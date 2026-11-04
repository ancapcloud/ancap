"""Explicit queued tasks only. A failure quarantines one worker, never its peer."""
import concurrent.futures
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import uuid
from scoped_files import FilePolicy

ROOT = Path(__file__).resolve().parent
WORK = Path.home() / 'Desktop/ANCAP-agents'
PYTHON = Path.home() / 'AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe'
NODE = 'C:/Program Files/nodejs/node.exe'
CLAW = Path.home() / 'AppData/Roaming/npm/node_modules/openclaw/openclaw.mjs'
FLAGS = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

def now(): return datetime.now(timezone.utc).isoformat()

def load(name):
    try: return json.loads((ROOT / 'status' / (name + '.json')).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError): return {}

def save(name, value):
    target = ROOT / 'status' / (name + '.json')
    target.parent.mkdir(exist_ok=True)
    tmp = target.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    for attempt in range(5):
        try:
            tmp.replace(target)
            return
        except PermissionError:
            if attempt==4:raise
            time.sleep(0.1*(attempt+1))

def git(cwd, *args):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True, encoding='utf-8', errors='replace', creationflags=FLAGS).strip()

def changes(cwd, baseline='HEAD'):
    return sorted(set(filter(None, git(cwd, 'diff', '--name-only', baseline).splitlines() + git(cwd, 'ls-files', '--others', '--exclude-standard').splitlines())))

def role_path(role, value):
    path=PurePosixPath(value.replace('\\','/'))
    if not value or not path.parts or path.is_absolute() or '..' in path.parts or ':' in value:
        raise ValueError('Task paths must be unambiguous project-relative paths')
    if role=='openclaw' and path.parts[0]!='frontend-app':raise ValueError('OpenClaw owns frontend-app only')
    if role=='hermes' and (path.parts[0] in ('frontend-app','agent-bridge') or str(path) in ('AGENTS.md','CLAUDE.md')):
        raise ValueError('Hermes task crosses ownership')

def task_for(role):
    try: task = json.loads((ROOT / 'queue' / (role + '.json')).read_text(encoding='utf-8'))
    except (OSError, ValueError): return None
    if task.get('enabled') is not True: return None
    if load(role + '-queue-result').get('task_id') == task.get('task_id'): return None
    if not task.get('task_id') or not task.get('allowed_files'): raise ValueError('Task needs an ID and explicit output files')
    policy=FilePolicy(WORK / ('wt-' + role), task.get('sources', []), task['allowed_files'])
    for path in task['allowed_files'] + task.get('sources', []):
        role_path(role,path)
        role_path(role,policy.path(path).relative_to(policy.cwd).as_posix())
    return task

def quarantine(role, state, reason, paths=None):
    state.update(state='blocked', reason=reason, updated_at=now(), finished_at=now(), paths=paths or [])
    save(role + '-process', state)
    save(role + '-quarantine', state)
    return False

def execute(role, task):
    cwd = WORK / ('wt-' + role)
    baseline = git(cwd, 'rev-parse', 'HEAD')
    cycle = uuid.uuid4().hex
    state = dict(agent=role, cycle_id=cycle, task_id=task['task_id'], state='starting',
                 started_at=now(), updated_at=now(), workdir=str(cwd), branch=git(cwd,'branch','--show-current'))
    save(role + '-process', state)
    dirty = changes(cwd)
    if dirty: return quarantine(role, state, 'Existing changes require review before a new task', dirty)
    policy = FilePolicy(cwd, task.get('sources', []), task['allowed_files'])
    context = '\n\n'.join('FILE: '+p+'\n'+policy.path(p).read_text(encoding='utf-8')[:12000] for p in task.get('sources', []))
    front = cwd / 'frontend-app'
    outputs = [str(Path(p).relative_to('frontend-app')) for p in task['allowed_files']] if role == 'openclaw' else task['allowed_files']
    prompt = ('Execute this single bounded task using file tools now. Do not answer with a future plan. '
              'No terminal, network, messaging, Git, or database operations are permitted. '
              'The supervisor independently runs project checks and commits the result. '
              'Do not read inboxes or choose another task. Write ONLY: '+', '.join(outputs)+'.\n'
              +task['instructions']+'\nThe source context is already loaded below; no path discovery is needed.\n'+context)
    env = {**os.environ, 'PYTHONIOENCODING':'utf-8', 'PYTHONUNBUFFERED':'1', 'OMP_NUM_THREADS':'4',
           'HERMES_HOME':str(Path.home()/'AppData/Local/hermes'), 'HERMES_GIT_BASH_PATH':'C:/Program Files/Git/bin/bash.exe',
           'TERMINAL_CWD':str(cwd), 'ANCAP_FILE_POLICY':json.dumps(dict(cwd=str(cwd),sources=task.get('sources',[]),outputs=task['allowed_files']))}
    if role == 'openclaw':
        cmd = [NODE,str(CLAW),'--profile','ancap','agent','--local','--agent','ancap-site','--session-id','scoped-'+cycle,
               '--message',prompt,'--timeout','1200','--json']
        actor_cwd = front
    else:
        cmd = [str(PYTHON),'-u',str(ROOT/'hermes_scoped.py'),'chat','-t','file','--max-turns','6','-q',prompt]
        actor_cwd = cwd
    log = ROOT/'runtime'/f'{role}-{cycle}.log'
    deadline = time.monotonic()+1260
    with log.open('w',encoding='utf-8') as out:
        process = subprocess.Popen(cmd,cwd=actor_cwd,env=env,stdout=out,stderr=subprocess.STDOUT,creationflags=FLAGS)
        state.update(state='running',pid=process.pid,log=str(log))
        unexpected = []
        while process.poll() is None and time.monotonic()<deadline:
            state['updated_at']=now();save(role+'-process',state)
            unexpected = sorted(set(changes(cwd,baseline))-set(task['allowed_files']))
            if unexpected: break
            time.sleep(5)
        code = process.poll()
        if code is None:
            subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,creationflags=FLAGS)
            if unexpected: return quarantine(role,state,'Out-of-task changes preserved; only this worker blocked',unexpected)
            return quarantine(role,state,'Task timed out; no automatic retry of the same failed task')
    unexpected=sorted(set(changes(cwd,baseline))-set(task['allowed_files']))
    if unexpected: return quarantine(role,state,'Out-of-task changes preserved',unexpected)
    # Framework final-rendering failures do not erase a real artifact; acceptance
    # requires the output and an independent successful check, regardless of prose.
    missing=[p for p in task['allowed_files'] if not policy.path(p).is_file() or policy.path(p).stat().st_size<100]
    if missing: return quarantine(role,state,'Required result was not produced',missing)
    check_env={**env,'ANCAP_CHECK_EXECUTOR':'supervisor'}
    state.update(state='checking',updated_at=now(),agent_exit_code=code);save(role+'-process',state)
    result=subprocess.run([str(PYTHON),str(ROOT/'verify_worker.py'),role,cycle],cwd=cwd,env=check_env,
                          capture_output=True,timeout=540,creationflags=FLAGS)
    receipt=load(role+'-evidence')
    if result.returncode or receipt.get('cycle_id')!=cycle or receipt.get('test_passed') is not True:
        return quarantine(role,state,'Independent project check failed; changes preserved')
    dirty=changes(cwd)
    if set(dirty)-set(task['allowed_files']): return quarantine(role,state,'Changes appeared during verification',dirty)
    if dirty:
        subprocess.run(['git','add','--',*dirty],cwd=cwd,check=True,creationflags=FLAGS,capture_output=True)
        subprocess.run(['git','commit','-m',task['commit_message']],cwd=cwd,check=True,creationflags=FLAGS,capture_output=True)
    state.update(state='completed',updated_at=now(),finished_at=now(),verified=True,exit_code=0,commit=git(cwd,'rev-parse','HEAD'))
    save(role+'-process',state);save(role+'-last-result',dict(state=state,receipt=receipt))
    save(role+'-queue-result',state)
    return True

def loop(role, once=False):
    while not (ROOT/'runtime/STOP').exists():
        if load(role+'-quarantine'):
            if once: return False
            time.sleep(5);continue
        try:
            task=task_for(role)
            if task:
                ok=execute(role,task)
                if once:return ok
            else:
                save(role+'-process',dict(agent=role,state='idle',updated_at=now(),reason='Ready; no new explicit queued task'))
                if once:return True
        except Exception as exc:
            quarantine(role,dict(agent=role,state='error'),str(exc)[:300])
            if once:return False
        time.sleep(5)
    return True

def main():
    kernel=ctypes.windll.kernel32;kernel.CreateMutexW.restype=ctypes.c_void_p
    handle=kernel.CreateMutexW(None,False,'Local\\ANCAPParallelAgentsV1')
    if kernel.GetLastError()==183:return 0
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(loop,role,'--once' in sys.argv) for role in ('openclaw','hermes')]
            while not all(f.done() for f in futures):
                save('supervisor',dict(pid=os.getpid(),state='running',enabled=True,updated_at=now(),scheduler='explicit-scoped-queue-v3'))
                time.sleep(5)
            return int(not all(f.result() for f in futures))
    finally:
        save('supervisor',dict(pid=os.getpid(),state='stopped',enabled=False,updated_at=now(),scheduler='explicit-scoped-queue-v3'))
        kernel.CloseHandle(ctypes.c_void_p(handle))

if __name__=='__main__':raise SystemExit(main())

"""Local dual-agent supervisor. No publishing, messaging, or automatic merging."""
import concurrent.futures
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
USER = Path.home()
WORK = USER / 'Desktop/ANCAP-agents'
PYTHON = USER / 'AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe'
CLAW = USER / 'AppData/Roaming/npm/node_modules/openclaw/openclaw.mjs'
NODE = Path('C:/Program Files/nodejs/node.exe')
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

def write_state(name, data):
    folder = ROOT / 'status'
    folder.mkdir(exist_ok=True)
    target = folder / (name + '.json')
    tmp = target.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(target)

def run_agent(name, smoke=False):
    cwd = WORK / ('wt-' + name)
    baseline = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=cwd, creationflags=FLAGS, text=True).strip()
    prompt = ('Do not edit files or call external messaging tools. Read AGENTS.md and '
              f'{ROOT / "CONTRACT.md"}. Reply READY with your role and working directory.'
              if smoke else (ROOT / (name.upper() + '_CYCLE.md')).read_text(encoding='utf-8'))
    env = os.environ.copy()
    env.update(PYTHONIOENCODING='utf-8', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4',
               OPENBLAS_NUM_THREADS='4', CMAKE_BUILD_PARALLEL_LEVEL='4',
               CARGO_BUILD_JOBS='4', HERMES_HOME=str(USER / 'AppData/Local/hermes'))
    if name == 'openclaw':
        cmd = [str(NODE), str(CLAW), '--profile', 'ancap', 'agent', '--local', '--agent', 'ancap-site',
               '--session-id', f'ancap-site-{int(time.time())}', '--message', prompt,
               '--timeout', '900', '--json']
    else:
        cmd = [str(PYTHON), '-m', 'hermes_cli.main', '-z', prompt]
    logs = ROOT / 'runtime'
    logs.mkdir(exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    with (logs / (name + '.log')).open('a', encoding='utf-8') as out:
        out.write('\nSTART ' + started + '\n'); out.flush()
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=out, stderr=subprocess.STDOUT,
                             creationflags=FLAGS)
        write_state(name + '-process', dict(pid=p.pid, started_at=started, state='running', workdir=str(cwd)))
        try:
            code = p.wait(timeout=960)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True, creationflags=FLAGS)
            code = 124
        changed = subprocess.check_output(['git', 'diff', '--name-only', baseline], cwd=cwd, creationflags=FLAGS, text=True).splitlines()
        changed += subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=cwd, creationflags=FLAGS, text=True).splitlines()
        def allowed(path):
            if path in ('AGENTS.md', 'CLAUDE.md') or path.startswith('agent-bridge/'):
                return False
            return path.startswith('frontend-app/') if name == 'openclaw' else not path.startswith('frontend-app/')
        violations = sorted({path for path in changed if not allowed(path)})
        if violations:
            (logs / 'STOP').touch()
            write_state(name + '-scope-violation', dict(paths=violations, action='supervisor stopped; changes preserved for review'))
            code = 125
        write_state(name + '-process', dict(pid=p.pid, started_at=started, state='exited', exit_code=code, workdir=str(cwd)))
        return code

def main():
    # OS mutex prevents manual launches and login launches from overlapping.
    kernel = ctypes.windll.kernel32
    kernel.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel.CreateMutexW(None, False, 'Local\\ANCAPParallelAgentsV1')
    if kernel.GetLastError() == 183:
        return 0
    smoke = '--smoke' in sys.argv
    failures = 0
    try:
        while not (ROOT / 'runtime/STOP').exists():
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda name: run_agent(name, smoke), ['openclaw', 'hermes']))
            if smoke or '--once' in sys.argv:
                return int(any(results))
            failures = failures + 1 if any(results) else 0
            if failures >= 3:
                (ROOT / 'runtime/STOP').touch()
                write_state('supervisor', dict(state='stopped', reason='three consecutive failed rounds; inspect runtime logs'))
                return 1
            # Both agents start together; never two cycles of the same agent.
            for _ in range(60):
                if (ROOT / 'runtime/STOP').exists():
                    return 0
                time.sleep(1)
    finally:
        kernel.CloseHandle(ctypes.c_void_p(handle))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

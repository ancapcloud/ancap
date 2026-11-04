"""Independent workers. Success requires a fresh tool-produced test receipt."""
import concurrent.futures
import ctypes
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
USER = Path.home()
WORK = USER / 'Desktop/ANCAP-agents'
PYTHON = USER / 'AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe'
CLAW = USER / 'AppData/Roaming/npm/node_modules/openclaw/openclaw.mjs'
NODE = Path('C:/Program Files/nodejs/node.exe')
FLAGS = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
MAX_CYCLE_SECONDS = 1800

def now():
    return datetime.now(timezone.utc).isoformat()

def read_state(name):
    try:
        return json.loads((ROOT / 'status' / (name + '.json')).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return {}

def write_state(name, data):
    folder = ROOT / 'status'
    folder.mkdir(exist_ok=True)
    target = folder / (name + '.json')
    tmp = target.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(target)

def git(cwd, *args):
    return subprocess.check_output(['git', *args], cwd=cwd, creationflags=FLAGS,
                                   text=True, encoding='utf-8', errors='replace').strip()

def allowed(name, path):
    if path in ('AGENTS.md', 'CLAUDE.md', 'SOUL.md', 'USER.md', 'IDENTITY.md') or path.startswith('agent-bridge/'):
        return False
    return path.startswith('frontend-app/') if name == 'openclaw' else not path.startswith('frontend-app/')

def valid_evidence(receipt, name, cycle):
    return (receipt.get('agent') == name and receipt.get('cycle_id') == cycle
            and receipt.get('exit_code') == 0 and receipt.get('test_passed') is True
            and bool(receipt.get('command')))

def selected_task(name):
    try:
        task = json.loads((ROOT / 'tasks' / (name + '.json')).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    previous = read_state(name + '-task-result')
    return {} if previous.get('task_id') == task.get('task_id') and previous.get('completed') else task

def source_context(name, task):
    cwd = (WORK / ('wt-' + name)).resolve()
    parts = []
    for relative in task.get('sources', []):
        path = (cwd / relative).resolve()
        if not path.is_relative_to(cwd) or any(part.startswith('.env') or part.lower() == 'sicret' for part in path.parts):
            raise ValueError('Task source must be a non-secret file inside the assigned worktree')
        limit = 9000 if relative.endswith('/api.ts') else 24000
        parts.append(f'FILE: {relative}\n' + path.read_text(encoding='utf-8')[:limit])
    return '\n\n'.join(parts)

def build_prompt(name, cycle, acceptance):
    command = f'{PYTHON.as_posix()} {(ROOT / "verify_worker.py").as_posix()} {name} {cycle}'
    assigned = {} if acceptance else selected_task(name)
    task = ('This is a real tool-execution acceptance task. Run the command below using '
            'your terminal/exec tool NOW. It runs a targeted existing project test and '
            'writes the machine receipt. Do not edit code in this acceptance task.' if acceptance else
            'Complete ONE small task in your owned area from the inbox below. Inspect '
            'the current code first; do not invent missing roadmap tasks or dependencies. '
            'If a dependency is missing, report it honestly and do an independent scoped check. '
            'After any change run applicable targeted checks and commit only owned paths. '
            'You must ALSO run the command below using your terminal/exec tool before finishing.')
    if assigned:
        task = assigned['instructions']
    prompt = (f'You are the {name} worker. CWD is {WORK / ("wt-" + name)}. '
              'You have terminal and file tools. An acknowledgement is NOT a result. '
              'Do not end with "starting"; EXECUTE tools, then report actual results. '
              'No push, deploy, external messages, reset, clean, rebase, or merge. '
              'Do not inspect secrets, .env files, credentials, wallets, or passwords.\n'
              f'{task}\nCOMMAND (Windows cmd syntax; use cmd /d /s /c if your shell is PowerShell):\n{command}\n'
              'If a tool call fails, correct it and retry. Final reply: performed action, actual test result, remaining issue.\n')
    if assigned:
        prompt += '\nSOURCE CONTEXT (already read from your exact worktree; edit these relative paths):\n'
        prompt += source_context(name, assigned)
    elif not acceptance:
        scope = 'frontend-app/ only' if name == 'openclaw' else 'backend, tests, mobile, chain, infrastructure and non-UI docs; never frontend-app/'
        prompt += f'\nYour ownership: {scope}. Never edit shared AGENTS.md, CLAUDE.md, or agent-bridge control code. '
        prompt += f'Use relative source paths from CWD. Shared coordination directory: {ROOT.as_posix()}. '
        prompt += 'Discover exact filenames with git ls-files before reading. Missing dependency: report blocked, do not repeatedly guess paths. '
        prompt += 'Do not alter databases or run DB tests without a dedicated test DB. Commit only owned paths. '
        prompt += '\nYOUR INBOX (already loaded; use absolute bridge paths for writes):\n'
        prompt += (ROOT / 'inbox' / ('to-' + name + '.md')).read_text(encoding='utf-8')
    return prompt

def run_agent(name, acceptance=False):
    cwd = WORK / ('wt-' + name)
    baseline = git(cwd, 'rev-parse', 'HEAD')
    before = set(git(cwd, 'ls-files', '--others', '--exclude-standard').splitlines())
    assigned = {} if acceptance else selected_task(name)
    cycle = uuid.uuid4().hex
    state = dict(agent=name, cycle_id=cycle, started_at=now(), updated_at=now(), state='starting',
                 mode='acceptance' if acceptance else 'development', workdir=str(cwd),
                 branch=git(cwd, 'branch', '--show-current'), baseline=baseline)
    state['task_id'] = assigned.get('task_id', '')
    env = os.environ.copy()
    env.update(PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4',
               OPENBLAS_NUM_THREADS='4', CMAKE_BUILD_PARALLEL_LEVEL='4', CARGO_BUILD_JOBS='4',
               HERMES_HOME=str(USER / 'AppData/Local/hermes'))
    # The Windows system32 bash shim launches WSL, which cannot cd to C:\\ paths.
    # Pin the installed Git Bash for Hermes' native local terminal backend.
    env['HERMES_GIT_BASH_PATH'] = 'C:/Program Files/Git/bin/bash.exe'
    prompt = build_prompt(name, cycle, acceptance)
    if name == 'openclaw':
        cmd = [str(NODE), str(CLAW), '--profile', 'ancap', 'agent', '--local', '--agent', 'ancap-site',
               '--session-id', 'ancap-site-' + cycle, '--message', prompt, '--timeout', '1500', '--json']
    else:
        cmd = [str(PYTHON), '-u', str(ROOT / 'hermes_headless.py'), 'chat', '-t', 'terminal,file',
               '--max-turns', '12', '-q', prompt]
    logs = ROOT / 'runtime'
    logs.mkdir(exist_ok=True)
    with (logs / (name + '.log')).open('a', encoding='utf-8') as out:
        out.write(f'\nSTART {state["started_at"]} CYCLE {cycle} MODE {state["mode"]}\n'); out.flush()
        deadline = time.monotonic() + MAX_CYCLE_SECONDS
        for attempt in range(3):
            offset = (logs / (name + '.log')).stat().st_size
            p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=out, stderr=subprocess.STDOUT, creationflags=FLAGS)
            state.update(pid=p.pid, state='running', attempt=attempt + 1)
            write_state(name + '-process', state)
            while p.poll() is None and time.monotonic() < deadline:
                state['updated_at'] = now()
                state['elapsed_seconds'] = int(MAX_CYCLE_SECONDS - (deadline - time.monotonic()))
                write_state(name + '-process', state)
                time.sleep(5)
            code = p.poll()
            if code is None:
                subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True, creationflags=FLAGS)
                code = 124
            if code or valid_evidence(read_state(name + '-evidence'), name, cycle) or attempt == 2 or deadline - time.monotonic() < 60:
                break
            # A final promise is not task completion. Continue the same conversation,
            # preserving its context instead of discarding it in a new scheduled cycle.
            followup = ('Your last response ended before executing the task. Continue NOW with actual tools. '
                        'First call terminal/exec to run git status --short in your assigned worktree, '
                        'then inspect the relevant source and perform the scoped task already assigned. '
                        'Do not respond with plans. Before finishing, run this exact verification command: '
                        f'{PYTHON.as_posix()} {(ROOT / "verify_worker.py").as_posix()} {name} {cycle}')
            if name == 'hermes':
                with (logs / (name + '.log')).open('rb') as source:
                    source.seek(offset)
                    output = source.read().decode('utf-8', errors='replace')
                matches = re.findall(r'(?:Session:\s+|--resume\s+)([a-zA-Z0-9_-]+)', output)
                if not matches:
                    break
                cmd = [str(PYTHON), '-u', str(ROOT / 'hermes_headless.py'), 'chat', '-t', 'terminal,file',
                       '--max-turns', '12', '--resume', matches[-1], '-q', followup]
            else:
                cmd[cmd.index('--message') + 1] = followup
            out.write(f'\nCONTINUE {cycle} after response without tool receipt\n'); out.flush()
        changed = git(cwd, 'diff', '--name-only', baseline).splitlines()
        changed += sorted(set(git(cwd, 'ls-files', '--others', '--exclude-standard').splitlines()) - before)
        violations = sorted({path for path in changed if not allowed(name, path)})
        if assigned:
            violations += sorted(set(changed) - set(assigned.get('allowed_files', [])))
        receipt = read_state(name + '-evidence')
        verified = valid_evidence(receipt, name, cycle)
        head = git(cwd, 'rev-parse', 'HEAD')
        reason = ''
        if violations:
            (logs / 'STOP').touch()
            write_state(name + '-scope-violation', dict(paths=violations, cycle_id=cycle,
                        action='supervisor stopped; changes preserved for review'))
            code, reason = 125, 'scope violation'
        elif code == 0 and not verified:
            code, reason = 126, 'agent exited without a passing tool-produced test receipt'
        elif code:
            reason = 'timeout' if code == 124 else 'agent or check failed'
        state.update(updated_at=now(), finished_at=now(), state='exited', exit_code=code,
                     verified=verified, head=head, commit=head if head != baseline else '', reason=reason)
        write_state(name + '-process', state)
        if code == 0:
            write_state(name + '-last-result', dict(state=state, receipt=receipt))
        write_state(name, dict(agent=name, role='site' if name == 'openclaw' else 'project',
                    branch=state['branch'], updated_at=now(), cycle_id=cycle,
                    status='completed' if code == 0 else 'blocked', task=state['mode'], commit=state['commit'],
                    done=('Agent executed targeted project test' if acceptance else
                          ('Scoped code commit with test receipt' if head != baseline else 'Project checks; no new code commit')) if code == 0 else reason,
                    checked=(receipt.get('command', '') + ': PASS') if verified else 'No passing test receipt for this cycle',
                    next='One scoped inbox task' if code == 0 else 'Retry execution; inspect worker log', needs_from_other=''))
        if acceptance and code == 0:
            write_state(name + '-acceptance', dict(cycle_id=cycle, completed_at=now(), verified=True))
        if assigned and code == 0 and head != baseline:
            write_state(name + '-task-result', dict(task_id=assigned['task_id'], completed=True,
                        cycle_id=cycle, commit=head, finished_at=now()))
        return code

def worker_loop(name, once=False, force_acceptance=False):
    while not (ROOT / 'runtime/STOP').exists():
        try:
            acceptance = force_acceptance or not read_state(name + '-acceptance').get('verified')
            code = run_agent(name, acceptance)
        except Exception as exc:
            write_state(name + '-process', dict(agent=name, state='error', updated_at=now(), reason=str(exc)[:300]))
            code = 1
        if once:
            return code
        for _ in range(60 if code == 0 else 180):
            if (ROOT / 'runtime/STOP').exists():
                return code
            time.sleep(1)
    return 0

def main():
    kernel = ctypes.windll.kernel32
    kernel.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel.CreateMutexW(None, False, 'Local\\ANCAPParallelAgentsV1')
    if kernel.GetLastError() == 183:
        return 0
    try:
        write_state('supervisor', dict(pid=os.getpid(), state='running', updated_at=now(),
                    scheduler='independent-workers-v2', enabled=True))
        once = '--once' in sys.argv or '--acceptance' in sys.argv
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda name: worker_loop(name, once, '--acceptance' in sys.argv), ['openclaw', 'hermes']))
        return int(any(results))
    finally:
        write_state('supervisor', dict(pid=os.getpid(), state='stopped', updated_at=now(),
                    scheduler='independent-workers-v2', enabled=False))
        kernel.CloseHandle(ctypes.c_void_p(handle))

if __name__ == '__main__':
    raise SystemExit(main())

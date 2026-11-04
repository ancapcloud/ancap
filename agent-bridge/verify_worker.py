"""Run by an agent tool: existing targeted tests produce a cycle-bound receipt."""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent

def main():
    name, cycle = sys.argv[1:]
    if name not in ('openclaw', 'hermes') or len(cycle) != 32 or not all(c in '0123456789abcdef' for c in cycle):
        raise ValueError('Invalid role or cycle')
    cwd = Path.home() / 'Desktop/ANCAP-agents' / ('wt-' + name)
    if Path.cwd().resolve() != cwd.resolve():
        raise ValueError('Run from your own worktree root')
    if name == 'openclaw':
        cmd = ['C:/Program Files/nodejs/node.exe', str(cwd / 'frontend-app/node_modules/vitest/vitest.mjs'),
               'run', 'src/lib/racpDisplay.test.ts']
        test_cwd = cwd / 'frontend-app'
    else:
        cmd = [str(Path.home() / 'Desktop/ANCAP/.venv/Scripts/python.exe'), '-m', 'pytest',
               '--noconftest', 'tests/test_acp_rpc_headers.py', '-q']
        test_cwd = cwd
    result = subprocess.run(cmd, cwd=test_cwd, capture_output=True, text=True, encoding='utf-8',
                            errors='replace', timeout=120, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    output = result.stdout + result.stderr
    folder = ROOT / 'runtime'
    folder.mkdir(exist_ok=True)
    logfile = folder / f'{name}-tests-{cycle}.log'
    logfile.write_text(output, encoding='utf-8')
    receipt = dict(agent=name, cycle_id=cycle, updated_at=datetime.now(timezone.utc).isoformat(),
                   workdir=str(cwd), command=subprocess.list2cmdline(cmd), exit_code=result.returncode,
                   test_passed=result.returncode == 0, output_log=str(logfile))
    dest = ROOT / 'status' / (name + '-evidence.json')
    tmp = dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(receipt, indent=2), encoding='utf-8'); tmp.replace(dest)
    print(output[-3000:])
    print('Tool receipt saved:', dest)
    return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())

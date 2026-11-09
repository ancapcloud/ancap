"""Require an actual failing regression against unchanged baseline production code."""
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile


def run(command, cwd, flags):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=300,
                          creationflags=flags,
                          env={**os.environ, 'PYTHONPATH': str(cwd)})


def assertion_failure(result):
    output=result.stdout+'\n'+result.stderr
    return (result.returncode == 1
            and re.search(r'AssertionError|\bexpected\b',output) is not None
            and re.search(r'ImportError|ModuleNotFoundError|SyntaxError|NameError|ReferenceError|Error collecting|ERROR collecting',output) is None)


def prove_regression(runtime, role, task, log):
    cwd=runtime.WORK/('wt-'+role)
    tests=task.get('tests',[])
    if not tests:
        raise ValueError('A task-specific regression suite is required')
    # Export tracked source only: no secrets, user files or Git metadata.
    paths=['app','tests','pytest.ini','pyproject.toml'] if role=='hermes' else ['frontend-app']
    archive=subprocess.check_output(['git','archive',task['baseline'],*paths],cwd=cwd,
                                    creationflags=runtime.FLAGS,timeout=60)
    with tempfile.TemporaryDirectory(prefix='ancap-regression-') as temporary:
        root=Path(temporary)
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(root,filter='data')
        if role=='hermes':
            python=getattr(runtime,'PROJECT_PYTHON',sys.executable)
            command=[str(python),'-m','pytest','--noconftest',*tests,'-q']
            work=root
        else:
            work=root/'frontend-app'
            modules=cwd/'frontend-app/node_modules'
            target=work/'node_modules'
            if os.name=='nt':
                # Fixed arguments; paths stay in this freshly-created temporary root.
                subprocess.run(['cmd','/c','mklink','/J',str(target),str(modules)],
                               check=True,capture_output=True,creationflags=runtime.FLAGS)
            else:
                target.symlink_to(modules,target_is_directory=True)
            command=[runtime.NODE,str(target/'vitest/vitest.mjs'),'run',
                     *[p.removeprefix('frontend-app/') for p in tests]]
        original=run(command,work,runtime.FLAGS)
        log.write('BASELINE ORIGINAL:\n'+original.stdout+original.stderr+'\n');log.flush()
        if original.returncode:
            raise ValueError('Baseline tests already fail; repair the baseline before planning')
        for name in tests:
            (root/name).write_bytes((cwd/name).read_bytes())
        regression=run(command,work,runtime.FLAGS)
        log.write('BASELINE WITH NEW TESTS:\n'+regression.stdout+regression.stderr+'\n');log.flush()
        if not assertion_failure(regression):
            raise ValueError('New regression must fail by assertion on baseline production code')

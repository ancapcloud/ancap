"""Require an actual failing regression against unchanged baseline production code."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET


PYTEST_REPORTER = '''import json
from pathlib import Path
import pytest
failures = []
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed:
        failures.append({"phase": report.when, "assertion": bool(call.excinfo and issubclass(call.excinfo.type, AssertionError))})
def pytest_sessionfinish(session, exitstatus):
    Path(__file__).with_suffix(".json").write_text(json.dumps(failures))
'''


def run(command, cwd, flags):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=300,
                          creationflags=flags,
                          env={**os.environ, 'PYTHONPATH': str(cwd)})


def assertion_failure(result, failures):
    return (result.returncode == 1 and bool(failures)
            and all(f.get('phase') == 'call' and f.get('assertion') is True for f in failures))


def read_failures(role, root):
    try:
        if role == 'hermes':
            return json.loads((root/'ancap_regression_reporter.json').read_text())
        tree=ET.parse(root/'vitest-regression.xml')
        if tree.findall('.//error'):
            return []
        return [dict(phase='call',assertion=f.get('type') == 'AssertionError')
                for f in tree.findall('.//failure')]
    except (OSError, ValueError, ET.ParseError):
        return []


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
            (root/'ancap_regression_reporter.py').write_text(PYTEST_REPORTER)
            python=getattr(runtime,'PROJECT_PYTHON',sys.executable)
            command=[str(python),'-m','pytest','--noconftest','-p','ancap_regression_reporter',*tests,'-q']
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
            command=[runtime.NODE,str(target/'vitest/vitest.mjs'),'run','--reporter=default',
                     '--reporter=junit','--outputFile='+str(root/'vitest-regression.xml'),
                     *[p.removeprefix('frontend-app/') for p in tests]]
        original=run(command,work,runtime.FLAGS)
        log.write('BASELINE ORIGINAL:\n'+original.stdout+original.stderr+'\n');log.flush()
        if original.returncode:
            raise ValueError('Baseline tests already fail; repair the baseline before planning')
        for name in tests:
            (root/name).write_bytes((cwd/name).read_bytes())
        regression=run(command,work,runtime.FLAGS)
        log.write('BASELINE WITH NEW TESTS:\n'+regression.stdout+regression.stderr+'\n');log.flush()
        if not assertion_failure(regression,read_failures(role,root)):
            raise ValueError('New regression must fail by assertion on baseline production code')

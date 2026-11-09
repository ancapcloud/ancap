import unittest
import io
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from regression_probe import assertion_failure, prove_regression


class RegressionProbeTests(unittest.TestCase):
    def test_only_real_assertion_failure_is_accepted(self):
        def result(code,text):
            return SimpleNamespace(returncode=code,stdout=text,stderr='')
        assertion=[dict(phase='call',assertion=True)]
        self.assertTrue(assertion_failure(result(1,'FAILED test_new'),assertion))
        for code,text in [(0,'1 passed'),(1,'1 failed'),(2,'AssertionError'),
                          (1,'AssertionError\nNameError: undefined'),
                          (1,'expected value\nModuleNotFoundError: package')]:
            self.assertFalse(assertion_failure(result(code,text),[]))
        for failures in [[dict(phase='setup',assertion=True)],
                         [dict(phase='call',assertion=False)],
                         assertion+[dict(phase='call',assertion=False)]]:
            self.assertFalse(assertion_failure(result(1,'AssertionError: expected value'),failures))

    def test_probe_requires_new_test_to_fail_on_unchanged_production(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary);cwd=base/'wt-hermes';cwd.mkdir()
            def git(*args):
                return subprocess.check_output(['git',*args],cwd=cwd,stderr=subprocess.DEVNULL,text=True).strip()
            git('init');git('config','user.email','test@example.invalid');git('config','user.name','Test')
            (cwd/'app').mkdir();(cwd/'tests').mkdir()
            (cwd/'app/__init__.py').write_text('')
            (cwd/'app/sample.py').write_text('def value(): return 1\n')
            (cwd/'tests/test_sample.py').write_text('from app.sample import value\ndef test_old(): assert value() > 0\n')
            (cwd/'pytest.ini').write_text('[pytest]\n');(cwd/'pyproject.toml').write_text('')
            git('add','.');git('commit','-m','baseline')
            task=dict(baseline=git('rev-parse','HEAD'),tests=['tests/test_sample.py'])
            runtime=SimpleNamespace(WORK=base,FLAGS=0)
            (cwd/'tests/test_sample.py').write_text('from app.sample import value\ndef test_old(): assert value() > 0\ndef test_new(): assert value() == 2\n')
            (cwd/'app/sample.py').write_text('def value(): return 2\n')
            prove_regression(runtime,'hermes',task,io.StringIO())
            (cwd/'tests/test_sample.py').write_text('from app.sample import value\ndef test_old(): assert value() > 0\ndef test_new(): assert value() == 1\n')
            with self.assertRaisesRegex(ValueError,'must fail by assertion'):
                prove_regression(runtime,'hermes',task,io.StringIO())
            (cwd/'tests/test_sample.py').write_text('from app.sample import value\ndef test_old(): assert value() > 0\ndef test_new():\n import re\n re.match("x", 42)\n')
            with self.assertRaisesRegex(ValueError,'must fail by assertion'):
                prove_regression(runtime,'hermes',task,io.StringIO())

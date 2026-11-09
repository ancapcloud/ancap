import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import coordinator as runtime
import continuous


class ContinuousTests(unittest.TestCase):
    def test_duplicate_tests_cannot_mask_a_broken_test(self):
        import ast
        with self.assertRaisesRegex(ValueError,'Duplicate test'):
            continuous.test_definitions(ast.parse('def test_new():\n    undefined_variable()\ndef test_new():\n    assert True\n'))
        self.assertEqual(len(continuous.test_definitions(ast.parse('class TestA:\n    def test_ok(self): pass\nclass TestB:\n    def test_ok(self): pass\n'))),2)
    def test_planner_requires_actual_evidence_and_rejects_token_banner_churn(self):
        source='def normalize(value): return value.strip()'
        proposal=dict(title='Handle blank values safely',instructions='Reject an absent input before calling value.strip()',reason='The current code assumes a string value',evidence=source)
        continuous.validate_proposal(proposal,source)
        with self.assertRaisesRegex(ValueError,'evidence'):
            continuous.validate_proposal({**proposal,'evidence':'nonexistent_function()'},source)
        with self.assertRaisesRegex(ValueError,'financial identifiers'):
            continuous.validate_proposal({**proposal,'instructions':'Add contract address 0x'+'1'*40+' to this page'},source)

    def test_comment_only_production_churn_is_rejected(self):
        (self.cwd/'app/services/sample.py').write_text('# imaginary improvement\ndef value():\n    return 1\n')
        with self.assertRaisesRegex(ValueError,'comment-only'):
            continuous.validate(runtime,'hermes',self.task,self.baseline)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        base=Path(self.tmp.name)
        self.root=base/'bridge';(self.root/'runtime').mkdir(parents=True)
        self.work=base/'work';self.cwd=self.work/'wt-hermes';self.cwd.mkdir(parents=True)
        self.patches=[patch.object(runtime,'ROOT',self.root),patch.object(runtime,'WORK',self.work)]
        for p in self.patches:p.start()
        self.git('init')
        self.git('config','user.email','test@example.invalid');self.git('config','user.name','Test')
        (self.cwd/'app/services').mkdir(parents=True);(self.cwd/'tests').mkdir()
        (self.cwd/'app/services/sample.py').write_text('def value():\n    return 1\n')
        (self.cwd/'tests/test_sample.py').write_text('def test_existing():\n    assert True\n')
        self.git('add','.');self.git('commit','-m','initial')
        self.baseline=self.git('rev-parse','HEAD')
        self.task=dict(task_id='auto-test',continuous=True,baseline=self.baseline,
                       sources=['app/services/sample.py','tests/test_sample.py'],
                       allowed_files=['app/services/sample.py','tests/test_sample.py'],
                       production_files=['app/services/sample.py'],unit='sample')

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()

    def git(self,*args):
        return subprocess.check_output(['git',*args],cwd=self.cwd,text=True,stderr=subprocess.DEVNULL).strip()

    def test_failed_task_is_stashed_and_next_task_can_run(self):
        self.task['repair_attempt']=1
        (self.cwd/'app/services/sample.py').write_text('def value():\n    return 2\n')
        runtime.quarantine('hermes',dict(agent='hermes'),'failed test')
        continuous.finish(runtime,'hermes',self.task,False)
        self.assertFalse(runtime.load('hermes-quarantine'))
        self.assertEqual(self.git('status','--porcelain'),'')
        self.assertIn('return 2',self.git('stash','show','-p'))
        self.assertEqual([e['outcome'] for e in continuous.history(runtime,'hermes')],['failed','preserved'])

    def test_first_owned_failure_gets_one_repair_with_preserved_output(self):
        (self.root/'continuous.json').write_text('{"enabled":true}')
        self.task['instructions']='Fix the real defect'
        p=self.cwd/'app/services/sample.py';p.write_text('def value():\n    return 2\n')
        runtime.quarantine('hermes',dict(agent='hermes'),'missing argument')
        continuous.finish(runtime,'hermes',self.task,False)
        repair=continuous.next_task(runtime,'hermes')
        self.assertEqual(repair['repair_attempt'],1)
        self.assertIn('missing argument',repair['instructions'])
        self.assertEqual(p.read_text(),'def value():\n    return 2\n')
        self.assertFalse(runtime.load('hermes-quarantine'))
        self.assertTrue((self.root/'runtime/repair-auto-test/changes.patch').is_file())

    def test_unexpected_changes_remain_quarantined_and_untouched(self):
        p=self.cwd/'unrelated.txt';p.write_text('user work')
        runtime.quarantine('hermes',dict(agent='hermes'),'scope')
        continuous.finish(runtime,'hermes',self.task,False)
        self.assertTrue(runtime.load('hermes-quarantine'))
        self.assertEqual(p.read_text(),'user work')

    def test_existing_tests_cannot_be_weakened_or_removed(self):
        (self.cwd/'app/services/sample.py').write_text('def value():\n    return 2\n')
        (self.cwd/'tests/test_sample.py').write_text('def test_existing():\n    pass\n')
        with self.assertRaisesRegex(ValueError,'weakened'):
            continuous.validate(runtime,'hermes',self.task,self.baseline)

    def test_test_only_churn_is_not_accepted(self):
        (self.cwd/'tests/test_sample.py').write_text('def test_existing():\n    assert True\n\ndef test_new(): pass\n')
        with self.assertRaisesRegex(ValueError,'production-code'):
            continuous.validate(runtime,'hermes',self.task,self.baseline)

    def test_new_tests_cannot_write_extra_files(self):
        (self.cwd/'app/services/sample.py').write_text('def value():\n    return 2\n')
        p=self.cwd/'tests/test_sample.py'
        p.write_text(p.read_text()+'\ndef test_new():\n    open("extra", "w")\n')
        with self.assertRaisesRegex(ValueError,'Unsafe'):
            continuous.validate(runtime,'hermes',self.task,self.baseline)

    def test_seed_runs_once_and_then_planner_is_used(self):
        seed={**self.task,'instructions':'Small real change','commit_message':'fix: sample'}
        (self.root/'continuous.json').write_text(json.dumps(dict(enabled=True,seeds={'hermes':seed})))
        first=continuous.next_task(runtime,'hermes')
        self.assertTrue(first['continuous'])
        with patch.object(continuous,'units',return_value=[dict(source='app/services/sample.py',tests=['tests/test_sample.py'])]), \
             patch.object(continuous,'pulse',return_value=dict(actionable=False,reason='Already correct')):
            for name in ['MASTER_ROADMAP.md','PRODUCTION_ROADMAP.md']:
                (self.root.parent/name).write_text('roadmap')
            (self.root.parent/'docs').mkdir();(self.root.parent/'docs/RACP_CURRENT_POLICY.md').write_text('policy')
            self.assertIsNone(continuous.next_task(runtime,'hermes'))
        self.assertEqual(runtime.load('hermes-planner')['cursor'],1)

    def test_planner_cannot_assign_other_role_or_control_files(self):
        for path in ['frontend-app/page.tsx','agent-bridge/continuous.json','../outside.py']:
            with self.subTest(path=path),self.assertRaises(ValueError):
                continuous.prepare(runtime,'hermes',dict(sources=[],allowed_files=[path],instructions='change it'))

    def test_success_does_not_overwrite_explicit_queue_receipt(self):
        runtime.save('hermes-queue-result',dict(task_id='manual-completed'))
        runtime.save('hermes-process',dict(commit='verified'))
        continuous.finish(runtime,'hermes',self.task,True)
        self.assertEqual(runtime.load('hermes-queue-result')['task_id'],'manual-completed')

    def test_completed_cycle_automatically_starts_the_next_without_manual_queue(self):
        count=[]
        def execute(role,task):
            count.append(task['task_id'])
            if len(count)==2:(self.root/'runtime/STOP').write_text('test stop')
            return True
        tasks=[dict(task_id='first',continuous=True),dict(task_id='second',continuous=True)]
        with patch.object(runtime,'task_for',return_value=None), \
             patch.object(continuous,'resume_interrupted'), \
             patch.object(continuous,'next_task',side_effect=tasks), \
             patch.object(continuous,'finish') as finish, \
             patch.object(continuous,'config',return_value=dict(enabled=True,cooldown_seconds=30)), \
             patch.object(runtime,'execute',side_effect=execute),patch.object(runtime.time,'sleep'):
            runtime.loop('hermes')
        self.assertEqual(count,['first','second'])
        self.assertEqual(finish.call_count,2)


if __name__=='__main__':unittest.main()

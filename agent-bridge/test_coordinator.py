import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import coordinator as runtime
import coordinator_report as report
from scoped_files import FilePolicy, install_guard

class CoordinatorTests(unittest.TestCase):
    def test_completed_queue_has_no_freeform_fallback(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'ROOT',Path(tmp)):
            queue=Path(tmp)/'queue';queue.mkdir()
            (queue/'openclaw.json').write_text(json.dumps(dict(enabled=True,task_id='done',allowed_files=['frontend-app/a.md'])))
            runtime.save('openclaw-queue-result',dict(task_id='done'))
            self.assertIsNone(runtime.task_for('openclaw'))
            self.assertIsNone(runtime.task_for('hermes'))

    def test_guard_denies_cross_role_and_secret_before_original_handler(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy=FilePolicy(tmp,['app/a.py'],['docs/result.md']);calls=[]
            registry=SimpleNamespace(dispatch=lambda name,args,**kw:calls.append((name,args)) or 'original')
            with patch.dict(sys.modules,{'tools.registry':SimpleNamespace(registry=registry)}):
                install_guard(policy)
                for args in [dict(path='frontend-app/page.tsx'),dict(path='../outside.py'),dict(path='.env')]:
                    self.assertIn('error',json.loads(registry.dispatch('write_file',args)))
                self.assertIn('error',json.loads(registry.dispatch('terminal',{'command':'echo x'})))
                self.assertFalse(calls)
                self.assertEqual(registry.dispatch('write_file',dict(path='docs/result.md',content='ok')),'original')
                self.assertEqual(len(calls),1)

    def test_multifile_patch_cannot_hide_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy=FilePolicy(tmp,[],['docs/result.md'])
            with self.assertRaises(ValueError):
                policy.check('patch',dict(mode='patch',patch='*** Update File: docs/result.md\n*** Add File: ../bad.py\n'))

    def test_one_quarantine_does_not_create_global_stop(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'ROOT',Path(tmp)):
            runtime.quarantine('openclaw',dict(agent='openclaw'),'scope failure',['app/a.py'])
            self.assertTrue(runtime.load('openclaw-quarantine'))
            self.assertFalse(runtime.load('hermes-quarantine'))
            self.assertFalse((Path(tmp)/'runtime/STOP').exists())

    def test_idle_workers_are_ready_without_fake_pid(self):
        def state(name):
            return dict(enabled=True,pid=1) if name=='supervisor' else dict(state='idle') if name.endswith('-process') else {}
        with patch.object(report,'load',side_effect=state),patch.object(report,'fresh',return_value=True),patch.object(report,'alive',return_value=True):
            text=report.render_report()
        self.assertEqual(text.count('Готов;'),2)
        self.assertNotIn('PID ',text)
        self.assertNotIn('PASS',text)

    def test_queue_paths_cannot_disguise_other_role_or_absolute_targets(self):
        for role,path in [('openclaw','frontend-app/../app/a.py'),('hermes','docs/../frontend-app/a.ts'),
                          ('hermes','C:/Users/x/frontend-app/a.ts'),('openclaw','app/a.py'),('hermes','frontend-app/a.ts'),('hermes','.')]:
            with self.subTest(role=role,path=path),self.assertRaises(ValueError):runtime.role_path(role,path)
        runtime.role_path('openclaw','frontend-app/src/a.ts')
        runtime.role_path('hermes','app/services/a.py')

    def test_status_write_retries_transient_windows_lock(self):
        original=Path.replace;attempts=[]
        def replace(path,target):
            attempts.append(1)
            if len(attempts)==1:raise PermissionError('temporary reader lock')
            return original(path,target)
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'ROOT',Path(tmp)),patch.object(Path,'replace',replace),patch.object(runtime.time,'sleep'):
            runtime.save('supervisor',dict(state='running'))
            self.assertEqual(runtime.load('supervisor')['state'],'running')
        self.assertEqual(len(attempts),2)

if __name__=='__main__':unittest.main()

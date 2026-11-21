from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from ensure_workspaces import restore, isolate_bridge
import os


class WorkspaceTests(unittest.TestCase):
    def test_stale_git_pointer_preserves_dirty_work_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();repo=root/'repo';repo.mkdir()
            def git(*args):
                return subprocess.check_output(['git',*args],cwd=repo,text=True,stderr=subprocess.DEVNULL).strip()
            git('init');git('config','user.email','test@example.invalid');git('config','user.name','Test')
            (repo/'source.py').write_text('value = 1\n')
            git('add','.');git('commit','-m','initial');git('branch','codex/worker')
            target=root/'worker';backup=root/'backup'
            restore(repo,target,'codex/worker',backup)
            (target/'source.py').write_text('valuable unfinished work\n')
            with (target/'.git').open('r+') as pointer:
                pointer.write('gitdir: '+(root/'missing').as_posix()+'\n');pointer.truncate()
            self.assertFalse(restore(repo,target,'codex/worker',backup))
            self.assertEqual((target/'source.py').read_text(),'valuable unfinished work\n')
            self.assertTrue((backup/'workspace.git').is_file())
            self.assertTrue((backup/'metadata/index').is_file())
            with self.assertRaisesRegex(RuntimeError,'different root/branch'):
                restore(repo,target,'codex/wrong',backup)

    def test_checkout_cannot_overwrite_shared_controller_through_junction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();repo=root/'repo';repo.mkdir()
            def git(*args):
                return subprocess.check_output(['git',*args],cwd=repo,text=True,stderr=subprocess.DEVNULL).strip()
            git('init');git('config','user.email','test@example.invalid');git('config','user.name','Test')
            shared=repo/'agent-bridge';shared.mkdir();(shared/'control.py').write_text('tracked baseline\n')
            git('add','.');git('commit','-m','initial');git('branch','codex/worker')
            target=root/'worker';restore(repo,target,'codex/worker',root/'backup')
            bridge=target/'agent-bridge';shutil.rmtree(bridge)
            if os.name=='nt':
                subprocess.run(['cmd','/c','mklink','/J',str(bridge),str(shared)],check=True,capture_output=True)
            else:bridge.symlink_to(shared,target_is_directory=True)
            (shared/'control.py').write_text('valuable controller correction\n')
            isolate_bridge(target,shared)
            self.assertNotEqual(bridge.resolve(),shared.resolve())
            self.assertEqual((bridge/'control.py').read_text(),'tracked baseline\n')
            subprocess.run(['git','-C',str(target),'restore','--worktree','--','agent-bridge'],check=True)
            self.assertEqual((shared/'control.py').read_text(),'valuable controller correction\n')

    def test_missing_registered_worktree_is_recreated_and_metadata_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();repo=root/'repo';repo.mkdir()
            def git(*args):
                return subprocess.check_output(['git',*args],cwd=repo,text=True,stderr=subprocess.DEVNULL).strip()
            git('init');git('config','user.email','test@example.invalid');git('config','user.name','Test')
            (repo/'source.py').write_text('value = 1\n')
            git('add','.');git('commit','-m','initial');git('branch','codex/worker')
            target=root/'worker';backup=root/'backup'
            self.assertTrue(restore(repo,target,'codex/worker',backup))
            self.assertFalse(restore(repo,target,'codex/worker',backup))
            self.assertTrue(target.resolve().is_relative_to(root))
            shutil.rmtree(target)
            self.assertTrue(restore(repo,target,'codex/worker',backup))
            self.assertTrue((target/'source.py').is_file())
            self.assertTrue(any(backup.glob('*/index')))
            self.assertEqual((repo/'source.py').read_text(),'value = 1\n')


if __name__=='__main__':unittest.main()

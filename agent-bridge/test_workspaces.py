from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from ensure_workspaces import restore


class WorkspaceTests(unittest.TestCase):
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

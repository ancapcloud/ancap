import datetime as dt
import unittest
import tempfile
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import run_workers as workers
import worker_report as report

class SupervisionTests(unittest.TestCase):
    def test_noop_or_stale_receipt_cannot_pass(self):
        receipt = dict(agent='hermes', cycle_id='new', exit_code=0, test_passed=True, command='pytest')
        self.assertTrue(workers.valid_evidence(receipt, 'hermes', 'new'))
        self.assertFalse(workers.valid_evidence({}, 'hermes', 'new'))
        self.assertFalse(workers.valid_evidence(receipt, 'hermes', 'old'))
        self.assertFalse(workers.valid_evidence(receipt, 'openclaw', 'new'))
        self.assertFalse(workers.valid_evidence({**receipt, 'exit_code': 1}, 'hermes', 'new'))

    def test_running_requires_live_pid_and_fresh_heartbeat(self):
        current = dt.datetime.now(dt.timezone.utc)
        state = dict(state='running', pid=123, updated_at=current.isoformat())
        with patch.object(report, 'pid_alive', return_value=True):
            self.assertTrue(report.live_worker(state, current))
            self.assertFalse(report.live_worker(state, current + dt.timedelta(minutes=2)))
        with patch.object(report, 'pid_alive', return_value=False):
            self.assertFalse(report.live_worker(state, current))

    def test_scope_roles(self):
        self.assertTrue(workers.allowed('openclaw', 'frontend-app/src/a.ts'))
        self.assertFalse(workers.allowed('openclaw', 'app/main.py'))
        self.assertFalse(workers.allowed('hermes', 'frontend-app/src/a.ts'))
        self.assertTrue(workers.allowed('hermes', 'tests/test_api.py'))
        self.assertFalse(workers.allowed('hermes', 'AGENTS.md'))

    def test_report_does_not_infer_failure_from_disabled_legacy_cron(self):
        current = dt.datetime.now(dt.timezone.utc)
        def data(name):
            if name == 'supervisor':
                return dict(enabled=True, pid=1)
            if name.endswith('-process'):
                return dict(state='running', pid=2, updated_at=current.isoformat())
            return {}
        with patch.object(report, 'load', side_effect=data), patch.object(report, 'pid_alive', return_value=True):
            text = report.render_report(current)
        self.assertEqual(text.count('Работает:'), 2)
        self.assertNotIn('расписании', text)
        self.assertNotIn('PASS', text)

    def test_report_never_uses_old_result_for_new_cycle(self):
        state = dict(agent='hermes', cycle_id='new', verified=True)
        receipt = dict(agent='hermes', cycle_id='old', test_passed=True, exit_code=0)
        self.assertFalse(report.checked_receipt(state, receipt))

    def test_report_keeps_accepted_tool_check_visible_during_next_cycle(self):
        current = dt.datetime.now(dt.timezone.utc)
        def data(name):
            if name == 'supervisor':
                return dict(enabled=True, pid=1)
            role = name.split('-')[0]
            if name.endswith('-process'):
                return dict(agent=role, state='running', pid=2, cycle_id='new', updated_at=current.isoformat())
            if name.endswith('-acceptance'):
                return dict(verified=True, cycle_id='accepted', completed_at=current.isoformat())
            if name.endswith('-evidence'):
                return dict(agent=role, cycle_id='accepted', test_passed=True, exit_code=0)
            return {}
        with patch.object(report, 'load', side_effect=data), patch.object(report, 'pid_alive', return_value=True):
            text = report.render_report(current)
        self.assertEqual(text.count('Работает:'), 2)
        self.assertEqual(text.count('PASS'), 2)
        self.assertEqual(text.count('Последний подтверждённый цикл:'), 2)

    def test_promise_continues_same_session_until_actual_test_receipt(self):
        commands = []
        cycle = 'a' * 32
        class Child:
            pid = 123
            def poll(self):
                return 0
        def spawn(cmd, **kwargs):
            commands.append(cmd)
            kwargs['stdout'].write('Session: test_session\n')
            kwargs['stdout'].flush()
            if len(commands) == 2:
                workers.write_state('hermes-evidence', dict(agent='hermes', cycle_id=cycle,
                                    test_passed=True, exit_code=0, command='pytest'))
            return Child()
        def git(cwd, *args):
            return 'h' * 40 if args[0] == 'rev-parse' else 'codex/hermes-parallel' if args[0] == 'branch' else ''
        with tempfile.TemporaryDirectory() as folder, patch.object(workers, 'ROOT', Path(folder)), \
             patch.object(workers, 'git', side_effect=git), \
             patch.object(workers, 'build_prompt', return_value='Perform task'), \
             patch.object(workers.uuid, 'uuid4', return_value=SimpleNamespace(hex=cycle)), \
             patch.object(workers.subprocess, 'Popen', side_effect=spawn):
            self.assertEqual(workers.run_agent('hermes'), 0)
            self.assertTrue(workers.read_state('hermes-process')['verified'])
        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[1][commands[1].index('--resume') + 1], 'test_session')

    def test_task_context_refuses_paths_outside_worktree_and_secret_files(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(workers, 'WORK', Path(folder)):
            cwd = Path(folder) / 'wt-hermes'
            cwd.mkdir()
            (cwd / 'safe.py').write_text('print(1)', encoding='utf-8')
            self.assertIn('print(1)', workers.source_context('hermes', {'sources': ['safe.py']}))
            for path in ('../outside.py', '.env', 'Sicret/key.txt'):
                with self.assertRaises(ValueError):
                    workers.source_context('hermes', {'sources': [path]})

    def test_assigned_prompt_has_exact_sources_without_double_absolute_paths(self):
        # Use a temporary worktree so the test does not depend on the operator's
        # Windows Desktop layout (CI and other machines have no wt-hermes).
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(__file__).resolve().parent.parent
            worktree = Path(tmp) / 'wt-hermes'
            for rel in workers.selected_task('hermes').get('sources', []):
                target = worktree / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text((repo / rel).read_text(encoding='utf-8'), encoding='utf-8')
            with patch.object(workers, 'WORK', Path(tmp)):
                prompt = workers.build_prompt('hermes', 'b' * 32, False)
        self.assertIn('FILE: app/services/acp_rpc.py', prompt)
        self.assertIn('FILE: tests/test_acp_rpc_headers.py', prompt)
        self.assertNotIn('agent-bridge\\C:', prompt)
        self.assertNotIn('agent-bridge/C:', prompt)
        self.assertNotIn('YOUR INBOX', prompt)

    def test_failed_independent_check_resumes_and_commits_only_after_pass(self):
        commands, commits, checks = [], [], []
        cycle = 'c' * 32
        class Child:
            pid = 123
            def poll(self):
                return 0
        def spawn(cmd, **kwargs):
            commands.append(cmd)
            kwargs['stdout'].write('Session: repair_session\n'); kwargs['stdout'].flush()
            return Child()
        def git(cwd, *args):
            if args[0] == 'rev-parse':
                return ('n' if commits else 'h') * 40
            if args[0] == 'branch':
                return 'codex/hermes-parallel'
            if args[0] == 'diff':
                return 'tests/t.py' if commands else ''
            return ''
        def check(name, token, cwd, env):
            passed = len(commands) == 2
            checks.append(passed)
            self.assertFalse(commits)
            receipt = dict(agent=name, cycle_id=token, command='pytest', executor='supervisor',
                           exit_code=0 if passed else 1, test_passed=passed)
            workers.write_state(name + '-evidence', receipt)
            return receipt, '' if passed else 'NameError: pytest is not defined'
        def run(cmd, **kwargs):
            if cmd[:2] == ['git', 'add']:
                self.assertEqual(cmd[3:], ['tests/t.py'])
            elif cmd[:2] == ['git', 'commit']:
                commits.append(cmd)
            return SimpleNamespace(returncode=0)
        with tempfile.TemporaryDirectory() as folder, patch.object(workers, 'ROOT', Path(folder)), \
             patch.object(workers, 'git', side_effect=git), \
             patch.object(workers, 'build_prompt', return_value='Make scoped change'), \
             patch.object(workers, 'controlled_check', side_effect=check), \
             patch.object(workers.uuid, 'uuid4', return_value=SimpleNamespace(hex=cycle)), \
             patch.object(workers.subprocess, 'Popen', side_effect=spawn), \
             patch.object(workers.subprocess, 'run', side_effect=run):
            tasks = Path(folder) / 'tasks'; tasks.mkdir()
            (tasks / 'hermes.json').write_text(json.dumps(dict(task_id='repair', allowed_files=['tests/t.py'])), encoding='utf-8')
            self.assertEqual(workers.run_agent('hermes'), 0)
            self.assertTrue(workers.read_state('hermes-task-result')['completed'])
        self.assertEqual(checks, [False, True])
        self.assertEqual(len(commits), 1)
        self.assertIn('NameError', commands[1][-1])

if __name__ == '__main__':
    unittest.main()

import datetime as dt
import unittest
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

if __name__ == '__main__':
    unittest.main()

from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from inference_lane import InferenceLane, StopRequested


class Runtime:
    def __init__(self, root):
        self.ROOT=root;self.states={};self.waiting={name:threading.Event() for name in ('second','third')}
    def now(self):return 'test-heartbeat'
    def load(self,name):return dict(self.states.get(name,{}))
    def save(self,name,state):
        self.states[name]=dict(state)
        role=state.get('agent')
        if state.get('state')=='waiting-model' and role in self.waiting:self.waiting[role].set()


class LaneTests(unittest.TestCase):
    def test_operator_stop_does_not_quarantine_the_worker_loop(self):
        import coordinator as runtime
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'ROOT',Path(tmp)), \
             patch.object(runtime.continuous,'resume_interrupted'), \
             patch.object(runtime,'task_for',return_value=None), \
             patch.object(runtime.continuous,'next_task',side_effect=StopRequested()), \
             patch.object(runtime,'quarantine') as quarantine:
            self.assertTrue(runtime.loop('openclaw'))
            quarantine.assert_not_called()
    def test_fifo_waiters_have_heartbeat_and_no_parallel_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'runtime').mkdir();runtime=Runtime(root);lane=InferenceLane()
            entered=threading.Event();release=threading.Event();order=[];errors=[]
            def worker(role):
                try:
                    with lane.acquire(runtime,role):
                        order.append(role)
                        if role=='first':
                            entered.set()
                            if not release.wait(10):raise TimeoutError('test release missing')
                except Exception as exc:errors.append(exc)
            threads=[threading.Thread(target=worker,args=(role,)) for role in ('first','second','third')]
            threads[0].start();self.assertTrue(entered.wait(5))
            threads[1].start();self.assertTrue(runtime.waiting['second'].wait(5))
            threads[2].start();self.assertTrue(runtime.waiting['third'].wait(5))
            self.assertEqual(order,['first'])
            self.assertEqual(runtime.states['second-process']['updated_at'],'test-heartbeat')
            release.set()
            for thread in threads:thread.join(10)
            self.assertFalse(any(thread.is_alive() for thread in threads));self.assertFalse(errors)
            self.assertEqual(order,['first','second','third'])

    def test_operator_stop_removes_waiter_without_leaking_the_lane(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'runtime').mkdir();runtime=Runtime(root);lane=InferenceLane()
            with lane.acquire(runtime,'owner'):
                stop=root/'runtime/STOP';stop.write_text('operator')
                with self.assertRaises(StopRequested):
                    with lane.acquire(runtime,'second'):self.fail('must not enter')
                self.assertFalse(lane.queue);self.assertTrue(lane.busy);stop.unlink()
            with lane.acquire(runtime,'third'):self.assertTrue(lane.busy)
            self.assertFalse(lane.busy)

    def test_exception_releases_model_for_the_other_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'runtime').mkdir();runtime=Runtime(root);lane=InferenceLane()
            def fail_model():
                with lane.acquire(runtime,'first'):raise ValueError('model error')
            self.assertRaises(ValueError,fail_model)
            with lane.acquire(runtime,'second'):self.assertTrue(lane.busy)


if __name__=='__main__':unittest.main()

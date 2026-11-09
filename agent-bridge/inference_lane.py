"""Fair access to the single local inference runner; checks never hold this lane."""
from collections import deque
from contextlib import contextmanager
import threading


class StopRequested(Exception):
    pass


class InferenceLane:
    def __init__(self):
        self.condition=threading.Condition()
        self.queue=deque()
        self.busy=False

    @contextmanager
    def acquire(self, runtime, role):
        ticket=object()
        acquired=False
        with self.condition:
            self.queue.append(ticket)
        try:
            while not acquired:
                with self.condition:
                    if (runtime.ROOT/'runtime/STOP').exists():raise StopRequested()
                    if self.queue[0] is ticket and not self.busy:
                        self.queue.popleft();self.busy=True;acquired=True
                    else:
                        state=runtime.load(role+'-process')
                        state.update(agent=role,state='waiting-model',updated_at=runtime.now(),
                                     reason='Waiting for the shared local model; no task timeout is consumed')
                        runtime.save(role+'-process',state)
                        self.condition.wait(timeout=5)
            yield
        finally:
            with self.condition:
                if acquired:self.busy=False
                elif ticket in self.queue:self.queue.remove(ticket)
                self.condition.notify_all()


LANE=InferenceLane()

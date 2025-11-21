from typing import List, Optional
from .storage import StoreSlot
from .handler import UnitHandler
from .calls import IncomingCall
from ..stats.statebox import StatBox

class FlowArbiter:

    def __init__(self, store: StoreSlot, workers: List[UnitHandler], log: StatBox):
        self.store = store
        self.workers = workers
        self.log = log
        self.active_src: Optional[int] = None
        self.batch: List[IncomingCall] = []
        self.busy_cnt = 0

    def push_call(self, call: IncomingCall, now: float):
        self.log.reg_call(call, now)

        if self.store.filled():
            if call.emergency:
                drop = self.store.drop_low()
                if drop:
                    self.log.reg_reject(drop, now, "evict")
                    if self.store.put(call):
                        self.log.reg_store("put", call, now)
                else:
                    self.log.reg_reject(call, now, "all_high")
            else:
                self.log.reg_reject(call, now, "full_normal")
        else:
            if self.store.put(call):
                self.log.reg_store("put", call, now)
            else:
                self.log.reg_reject(call, now, "fail_put")

        self.distribute(now)

    def _free_workers(self, now: float) -> List[UnitHandler]:
        return [w for w in self.workers if w.free(now)]

    def _begin_batch(self, now: float) -> bool:
        head = self.store.take()
        if not head:
            return False
        self.log.reg_store("take", head, now)
        group = [head] + self.store.grab_same_origin(head.origin)
        self.batch = group
        self.busy_cnt = 0
        self.active_src = head.origin
        self.log.reg_event("new_group", now, src=head.origin, size=len(group))
        return True

    def _assign(self, worker: UnitHandler, call: IncomingCall, now: float):
        worker.assign(call, now)
        self.log.reg_start(call, now, worker.uid)

    def distribute(self, now: float):
        idle = self._free_workers(now)
        while idle:
            if self.active_src is None:
                if self.store.empty():
                    break
                if not self._begin_batch(now):
                    break

            if not self.batch:
                break

            worker = sorted(idle, key=lambda h: h.uid)[0]
            idle.remove(worker)
            call = self.batch.pop(0)
            self.log.reg_event("pick", now, id=call.cid)
            self._assign(worker, call, now)
            self.busy_cnt += 1

    def update(self, now: float):
        for w in self.workers:
            if w.free(now) and w.current:
                done = w.done(now)
                self.log.reg_finish(done, now)
                if done.origin == self.active_src:
                    self.busy_cnt -= 1
                    if self.busy_cnt == 0 and not self.batch:
                        self.log.reg_event("group_done", now, src=done.origin)
                        self.active_src = None
        self.distribute(now)

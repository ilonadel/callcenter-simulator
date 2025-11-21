from .intake import SourceFlux
from .storage import StoreSlot
from .handler import UnitHandler
from .arbiter import FlowArbiter
from ..stats.statebox import StatBox

class RuntimeLoop:

    def __init__(self, rates, buf_size, workers):
        self.t = 0.0
        self.dt = 0.1

        self.stats = StatBox()
        self.source = SourceFlux(rates)
        self.store = StoreSlot(buf_size)
        self.units = [UnitHandler(i+1) for i in range(workers)]
        self.ctrl = FlowArbiter(self.store, self.units, self.stats)

    def step(self):
        self.t += self.dt
        born = self.source.emit(self.t)
        for c in born:
            self.ctrl.push_call(c, self.t)
        self.ctrl.update(self.t)

    def run_steps(self, n):
        for _ in range(n):
            self.step()
            self.stats.snap(self.t, self.store, self.units)
        return self.stats.snaps

    def run_auto(self, duration, folder):
        while self.t < duration:
            self.step()
            self.stats.snap(self.t, self.store, self.units)

        while True:
            any_busy = any(not u.free(self.t) for u in self.units)
            if not any_busy and self.store.empty():
                break
            self.t += self.dt
            self.ctrl.update(self.t)
            self.stats.snap(self.t, self.store, self.units)

        util = {u.uid: u.utilization(self.t) for u in self.units}
        self.stats.util = util
        plot = self.stats.draw(self.t, folder)

        return dict(
            total=self.t,
            generated=self.stats.gen,
            done=self.stats.done,
            rejected=self.stats.rej,
            rej_percent=self.stats.summary_rej(),
            avg_wait=sum(self.stats.wait)/len(self.stats.wait) if self.stats.wait else 0,
            avg_serv=sum(self.stats.serv)/len(self.stats.serv) if self.stats.serv else 0,
            graph=str(plot)
        )

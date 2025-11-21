import matplotlib.pyplot as plt
from pathlib import Path

class StatBox:

    def __init__(self):
        self.events = []
        self.snaps = []

        self.gen = {}
        self.rej = {}
        self.done = {}

        self.wait = []
        self.serv = []
        self.start_at = {}

        self.qhist = []
        self.rejhist = []
        self.util = {}

    def reg_event(self, kind, t, **kw):
        self.events.append(dict(kind=kind, t=t, **kw))

    def reg_call(self, call, t):
        self.gen[call.origin] = self.gen.get(call.origin, 0) + 1
        self.reg_event("in", t, id=call.cid, src=call.origin)

    def reg_store(self, act, call, t):
        self.reg_event(f"store_{act}", t, id=call.cid, src=call.origin)

    def reg_reject(self, call, t, why):
        self.rej[call.origin] = self.rej.get(call.origin, 0) + 1
        self.reg_event("reject", t, id=call.cid, why=why, src=call.origin)

    def reg_start(self, call, t, wid):
        self.start_at[call.cid] = t
        self.wait.append(t - call.born_at)
        self.reg_event("start", t, id=call.cid, src=call.origin, worker=wid)

    def reg_finish(self, call, t):
        self.done[call.origin] = self.done.get(call.origin, 0) + 1
        st = self.start_at.get(call.cid, t)
        self.serv.append(t - st)
        self.reg_event("finish", t, id=call.cid, src=call.origin)

    def summary_rej(self):
        total_g = sum(self.gen.values())
        total_r = sum(self.rej.values())
        return 0 if (total_g + total_r) == 0 else round(total_r/(total_g+total_r)*100, 2)

    def snap(self, t, pool, workers):
        ev = self.events[:]  
        self.events.clear()  
        self.snaps.append(dict(
            t=round(t,2),
            events=ev,
            pool=pool.info(),
            ptrs=pool.pointers(),
            ops=[w.describe(t) for w in workers],
            rej=self.summary_rej(),
        ))
        self.qhist.append((t, pool.info()['count']))
        self.rejhist.append((t, self.summary_rej()))

    def draw(self, total, folder):
        folder = Path(folder)
        folder.mkdir(exist_ok=True, parents=True)
        f = folder/"plots.png"

        fig, ax = plt.subplots(3,1,figsize=(10,12))
        t1, q1 = zip(*self.qhist)
        ax[0].plot(t1, q1)
        ax[0].set_title("Очередь")

        t2, r2 = zip(*self.rejhist)
        ax[1].plot(t2, r2)
        ax[1].set_title("Отказы")

        if self.util:
            ids = list(self.util)
            vals = [self.util[x]*100 for x in ids]
            ax[2].bar([str(x) for x in ids], vals)

        fig.tight_layout()
        fig.savefig(f, dpi=200)
        plt.close(fig)
        return f

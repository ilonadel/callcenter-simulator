from typing import Optional, Dict
from .calls import IncomingCall


class UnitHandler:
    def __init__(self, uid: int):
        self.uid = uid
        self.busy_till: float = 0.0
        self.current: Optional[IncomingCall] = None
        self.load_sum: float = 0.0

    # проверка, свободен ли оператор
    def free(self, t: float) -> bool:
        return (self.current is None) or (t >= self.busy_till)

    # назначение новой заявки
    def assign(self, call: IncomingCall, now: float):
        self.current = call
        self.busy_till = now + call.duration

    # завершение обслуживания
    def done(self, now: float) -> Optional[IncomingCall]:
        finished = self.current
        if finished is not None:
            self.load_sum += finished.duration
        self.current = None
        return finished

    # состояние оператора для таблицы
    def describe(self, t: float) -> Dict:
        if self.free(t):
            return {
                "id": self.uid,
                "mode": "idle",
                "task": None,
                "until": t
            }
        return {
            "id": self.uid,
            "mode": "busy",
            "task": self.current.cid if self.current else None,
            "until": self.busy_till
        }

    # загрузка оператора
    def utilization(self, total: float):
        if total == 0:
            return 0.0
        return min(1.0, self.load_sum / total)


# буфер заявок (кольцевой), вариант 15

from typing import List, Optional
from .calls import IncomingCall


class StoreSlot:

    def __init__(self, limit: int):
        self.capacity = limit
        self.data: List[IncomingCall] = []   # сами заявки
        self.pos_in = 0
        self.pos_out = 0

    def filled(self) -> bool:
        return len(self.data) >= self.capacity

    def empty(self) -> bool:
        return not self.data

    def put(self, item: IncomingCall) -> bool:
        if self.filled():
            return False
        self.data.append(item)
        self.pos_in = (self.pos_in + 1) % self.capacity
        return True

    def take(self) -> Optional[IncomingCall]:
        if self.empty():
            return None
        obj = self.data.pop(0)
        self.pos_out = (self.pos_out + 1) % self.capacity
        return obj

    # удаляем обычную заявку при переполнении (приоритет)
    def drop_low(self) -> Optional[IncomingCall]:
        for x in self.data:
            if not x.emergency:
                self.data.remove(x)
                self.pos_out = (self.pos_out + 1) % self.capacity
                return x
        return None

    # забрать подряд заявки одного источника
    def grab_same_origin(self, src: int) -> List[IncomingCall]:
        pack = []
        remain = []
        for x in self.data:
            (pack if x.origin == src else remain).append(x)
        if pack:
            self.pos_out = (self.pos_out + len(pack)) % self.capacity
        self.data = remain
        return pack

    def info(self):
        return dict(
            count=len(self.data),
            ids=[c.cid for c in self.data]
        )

    def pointers(self):
        return dict(inp=self.pos_in, out=self.pos_out)


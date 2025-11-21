# Источники заявок (ИБ и ИЗ1). Генерируют новые звонки.

import numpy as np
from typing import List
from .calls import IncomingCall


class SourceFlux:
    def __init__(self, intensities: List[float]):
        self.rates = intensities
        # будущие моменты прихода для каждого источника
        self.future = {i + 1: None for i in range(len(intensities))}
        self.count = 0

    # пересчёт следующего прихода
    def _next(self, idx: int, now: float):
        rate = self.rates[idx - 1]
        self.future[idx] = now + np.random.exponential(1.0 / rate)

    # генерация новых заявок
    def emit(self, now: float) -> List[IncomingCall]:
        events = []

        for src_id in self.future:
            # если ещё не задано время — задаём
            if self.future[src_id] is None:
                self._next(src_id, now)

            # проверяем, настал ли момент генерации
            if now >= self.future[src_id]:
                duration = float(np.random.uniform(3, 7))
                is_emerg = (src_id == 1)

                call = IncomingCall(
                    ident=self.count,
                    origin=src_id,
                    emergency=is_emerg,
                    born_at=self.future[src_id],
                    duration=duration
                )

                events.append(call)
                self.count += 1

                # назначаем следующее событие для этого источника
                self._next(src_id, now)

        return events


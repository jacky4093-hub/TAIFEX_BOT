import random
import time
from dataclasses import dataclass
from typing import Iterator
import config

@dataclass
class Tick:
    index: int
    price: float

class SimulatedMarketData:
    def __init__(self, start_price: float = config.START_PRICE):
        self.price = start_price

    def stream(self) -> Iterator[Tick]:
        for i in range(config.TICKS):
            # 模擬每次跳動 -8 到 +8 點
            self.price += random.randint(-8, 8)
            yield Tick(index=i, price=round(self.price, 2))
            time.sleep(config.TICK_INTERVAL_SECONDS)

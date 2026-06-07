import random
from dataclasses import dataclass

@dataclass
class Tick:
    index: int
    price: float

class SimulatedMarketData:
    def __init__(self, start_price: float):
        self.price = start_price
        self.index = 0

    def next_tick(self) -> Tick:
        self.price += random.randint(-8, 8)
        self.index += 1
        return Tick(index=self.index, price=round(self.price, 2))

from abc import ABC, abstractmethod
import random
from dataclasses import dataclass

@dataclass
class Tick:
    index: int
    price: float

class MarketSource(ABC):
    @abstractmethod
    def next_tick(self) -> Tick:
        pass

class SimulatedMarketSource(MarketSource):
    def __init__(self, start_price: float):
        self.price = start_price
        self.index = 0

    def next_tick(self) -> Tick:
        self.price += random.randint(-8, 8)
        self.index += 1
        return Tick(index=self.index, price=round(self.price, 2))

class ShioajiMarketSource(MarketSource):
    """
    Shioaji 真實行情預留類別。

    等你申請好永豐 Shioaji API 後，這裡會改成：
    1. 登入 Shioaji
    2. 訂閱 TX / MTX / TMF 近月合約
    3. 收到 tick 後回傳 Tick
    4. 丟給策略引擎做模擬交易

    目前故意不實作，避免沒有 API Key 時誤用。
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Shioaji 真實行情尚未啟用，請先申請 API Key。")

    def next_tick(self) -> Tick:
        raise NotImplementedError("Shioaji 真實行情尚未啟用。")

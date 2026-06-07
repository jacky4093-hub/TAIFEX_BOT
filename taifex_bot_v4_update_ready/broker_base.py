"""
交易介面抽象層。

V5-0 先把交易介面拆出來，之後 V8 接 Shioaji 真實下單時，
GUI 與策略層不需要大幅改寫。
"""
from abc import ABC, abstractmethod


class BrokerBase(ABC):
    @abstractmethod
    def on_signal(self, action: str, price: float, reason: str, settings: dict):
        pass

    @abstractmethod
    def check_stop(self, price: float, settings: dict):
        pass

    @abstractmethod
    def export_trades(self, filename: str = "trades.csv") -> bool:
        pass

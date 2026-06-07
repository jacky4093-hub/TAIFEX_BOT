from abc import ABC, abstractmethod

class BrokerBase(ABC):
    """
    交易介面基底類別。

    目前 V5-0 只允許模擬交易。
    未來 V8 才會新增 ShioajiBroker 真實下單。
    """

    @abstractmethod
    def on_signal(self, action: str, price: float, reason: str, settings: dict):
        pass

    @abstractmethod
    def check_stop(self, price: float, settings: dict):
        pass

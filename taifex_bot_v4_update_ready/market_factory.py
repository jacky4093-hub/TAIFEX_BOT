"""
行情來源工廠。

目的：
- GUI 不直接知道行情來源實作細節
- 目前可用：sim 模擬行情
- 未來擴充：shioaji 永豐真實行情
"""
from market_source import SimulatedMarketSource, ShioajiMarketSource, MarketSource


class MarketFactory:
    SIM = "sim"
    SHIOAJI = "shioaji"

    @staticmethod
    def create(mode: str, start_price: float, **kwargs) -> MarketSource:
        mode = (mode or MarketFactory.SIM).lower()

        if mode == MarketFactory.SIM:
            return SimulatedMarketSource(start_price=start_price)

        if mode == MarketFactory.SHIOAJI:
            return ShioajiMarketSource(**kwargs)

        raise ValueError(f"未知行情模式：{mode}")

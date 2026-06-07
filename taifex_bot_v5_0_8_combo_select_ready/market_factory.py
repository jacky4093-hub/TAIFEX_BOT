from sim_market import SimulatedMarketSource
from shioaji_market import ShioajiMarketSource

class MarketFactory:
    @staticmethod
    def create(mode: str, start_price: float):
        if mode == "sim":
            return SimulatedMarketSource(start_price)
        if mode == "shioaji":
            return ShioajiMarketSource(start_price=start_price)
        raise ValueError(f"未知行情模式：{mode}")

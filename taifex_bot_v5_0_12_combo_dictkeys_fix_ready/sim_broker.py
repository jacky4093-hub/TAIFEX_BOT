from trader import SimulatedTrader

class SimBroker(SimulatedTrader):
    """
    模擬交易 Broker。

    先繼承原本 V4 的 SimulatedTrader，保持 GUI 和交易邏輯穩定。
    未來要接真實下單時，只要新增 ShioajiBroker，不需要大改策略與 GUI。
    """
    pass

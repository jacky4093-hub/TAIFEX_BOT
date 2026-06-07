from market_source import MarketSource, Tick

class ShioajiMarketSource(MarketSource):
    """
    Shioaji 真實行情骨架。

    V5-0 先完成架構拆分，不會真的連線。
    V5-1 會加入 API Key / Secret Key / 憑證設定畫面。
    V5-2 再訂閱 TX / MTX / TMF 即時行情。
    """

    def __init__(self, *args, **kwargs):
        self.connected = False
        raise NotImplementedError("Shioaji 真實行情尚未啟用，請等 V5-1/V5-2。")

    def next_tick(self) -> Tick:
        raise NotImplementedError("Shioaji 真實行情尚未啟用。")

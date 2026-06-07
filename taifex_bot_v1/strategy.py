from collections import deque
from dataclasses import dataclass
import config

@dataclass
class Signal:
    action: str  # BUY, SELL, HOLD
    reason: str

class StrategyEngine:
    def __init__(self):
        self.prices = deque(maxlen=max(config.MA_LONG + 2, 100))
        self.last_grid_level = None

    def on_price(self, price: float) -> list[Signal]:
        self.prices.append(price)
        signals = []

        if config.ENABLE_BREAKOUT:
            signals.append(self.breakout(price))

        if config.ENABLE_RANGE:
            signals.append(self.range_strategy(price))

        if config.ENABLE_MA:
            signals.append(self.ma_strategy())

        if config.ENABLE_GRID:
            signals.append(self.grid_strategy(price))

        return [s for s in signals if s.action != "HOLD"]

    def breakout(self, price: float) -> Signal:
        if price >= config.BREAKOUT_UPPER:
            return Signal("BUY", f"突破上限 {config.BREAKOUT_UPPER}")
        if price <= config.BREAKOUT_LOWER:
            return Signal("SELL", f"跌破下限 {config.BREAKOUT_LOWER}")
        return Signal("HOLD", "突破策略無訊號")

    def range_strategy(self, price: float) -> Signal:
        if price <= config.RANGE_BUY_LEVEL:
            return Signal("BUY", f"區間低點買進 {config.RANGE_BUY_LEVEL}")
        if price >= config.RANGE_SELL_LEVEL:
            return Signal("SELL", f"區間高點賣出 {config.RANGE_SELL_LEVEL}")
        return Signal("HOLD", "區間策略無訊號")

    def ma_strategy(self) -> Signal:
        if len(self.prices) < config.MA_LONG + 1:
            return Signal("HOLD", "均線資料不足")

        prices = list(self.prices)
        short_ma_now = sum(prices[-config.MA_SHORT:]) / config.MA_SHORT
        long_ma_now = sum(prices[-config.MA_LONG:]) / config.MA_LONG

        short_ma_prev = sum(prices[-config.MA_SHORT-1:-1]) / config.MA_SHORT
        long_ma_prev = sum(prices[-config.MA_LONG-1:-1]) / config.MA_LONG

        if short_ma_prev <= long_ma_prev and short_ma_now > long_ma_now:
            return Signal("BUY", f"短均線上穿長均線 MA{config.MA_SHORT}/MA{config.MA_LONG}")

        if short_ma_prev >= long_ma_prev and short_ma_now < long_ma_now:
            return Signal("SELL", f"短均線下穿長均線 MA{config.MA_SHORT}/MA{config.MA_LONG}")

        return Signal("HOLD", "均線策略無訊號")

    def grid_strategy(self, price: float) -> Signal:
        level = round((price - config.GRID_BASE_PRICE) / config.GRID_SIZE)

        if self.last_grid_level is None:
            self.last_grid_level = level
            return Signal("HOLD", "初始化網格")

        if level < self.last_grid_level:
            self.last_grid_level = level
            return Signal("BUY", f"網格下跌買進 level={level}")

        if level > self.last_grid_level:
            self.last_grid_level = level
            return Signal("SELL", f"網格上漲賣出 level={level}")

        return Signal("HOLD", "網格策略無訊號")

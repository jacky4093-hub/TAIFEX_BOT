from collections import deque
from dataclasses import dataclass

@dataclass
class Signal:
    action: str
    reason: str

class StrategyEngine:
    def __init__(self):
        self.prices = deque(maxlen=300)

    def reset(self):
        self.prices.clear()

    def on_price(self, price: float, settings: dict) -> list[Signal]:
        self.prices.append(price)
        signals = []

        if settings["enable_breakout"]:
            signals.append(self.breakout(price, settings))
        if settings["enable_range"]:
            signals.append(self.range_strategy(price, settings))
        if settings["enable_ma"]:
            signals.append(self.ma_strategy(settings))
        return [s for s in signals if s.action != "HOLD"]

    def breakout(self, price: float, settings: dict) -> Signal:
        if price >= settings["breakout_upper"]:
            return self._breakout_signal(
                settings.get("breakout_upper_action", "做多"),
                f"突破上限 {settings['breakout_upper']}"
            )
        if price <= settings["breakout_lower"]:
            return self._breakout_signal(
                settings.get("breakout_lower_action", "做空"),
                f"跌破下限 {settings['breakout_lower']}"
            )
        return Signal("HOLD", "")

    def _breakout_signal(self, action_text: str, reason: str) -> Signal:
        if action_text == "做多":
            return Signal("BUY", f"{reason}，動作：做多")
        if action_text == "做空":
            return Signal("SELL", f"{reason}，動作：做空")
        return Signal("HOLD", "")

    def range_strategy(self, price: float, settings: dict) -> Signal:
        if price <= settings["range_buy"]:
            return Signal("BUY", f"區間低點買進 {settings['range_buy']}")
        if price >= settings["range_sell"]:
            return Signal("SELL", f"區間高點賣出 {settings['range_sell']}")
        return Signal("HOLD", "")

    def ma_strategy(self, settings: dict) -> Signal:
        short = settings["ma_short"]
        long = settings["ma_long"]
        if len(self.prices) < long + 1:
            return Signal("HOLD", "")

        prices = list(self.prices)
        short_now = sum(prices[-short:]) / short
        long_now = sum(prices[-long:]) / long
        short_prev = sum(prices[-short-1:-1]) / short
        long_prev = sum(prices[-long-1:-1]) / long

        if short_prev <= long_prev and short_now > long_now:
            return Signal("BUY", f"短均線上穿長均線 MA{short}/MA{long}")
        if short_prev >= long_prev and short_now < long_now:
            return Signal("SELL", f"短均線下穿長均線 MA{short}/MA{long}")
        return Signal("HOLD", "")

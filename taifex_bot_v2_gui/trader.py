from dataclasses import dataclass
from datetime import datetime
import csv

@dataclass
class Position:
    side: str
    entry_price: float
    entry_time: str
    reason: str

class SimulatedTrader:
    def __init__(self, initial_capital: float, point_value: int, contracts: int):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.point_value = point_value
        self.contracts = contracts
        self.position: Position | None = None
        self.trades = []
        self.open_count = 0
        self.daily_loss = 0

    def reset(self, initial_capital: float, point_value: int, contracts: int):
        self.__init__(initial_capital, point_value, contracts)

    def set_contract(self, point_value: int, contracts: int):
        self.point_value = point_value
        self.contracts = contracts

    def can_trade(self, settings: dict) -> bool:
        if self.open_count >= settings["max_trades"]:
            return False
        if self.daily_loss <= -abs(settings["max_loss"]):
            return False
        return True

    def on_signal(self, action: str, price: float, reason: str, settings: dict):
        if not self.can_trade(settings):
            return "風控停止交易"

        if self.position is None:
            if action == "BUY":
                self.open_position("LONG", price, reason)
                return f"開多單 @ {price}，原因：{reason}"
            if action == "SELL":
                self.open_position("SHORT", price, reason)
                return f"開空單 @ {price}，原因：{reason}"

        if self.position.side == "LONG" and action == "SELL":
            pnl = self.close_position(price, f"反向訊號平多：{reason}")
            return f"平多單 @ {price}，損益 {pnl:.0f} 元"

        if self.position.side == "SHORT" and action == "BUY":
            pnl = self.close_position(price, f"反向訊號平空：{reason}")
            return f"平空單 @ {price}，損益 {pnl:.0f} 元"

        return "已有同方向持倉，忽略訊號"

    def check_stop(self, price: float, settings: dict):
        if self.position is None:
            return None

        if self.position.side == "LONG":
            diff = price - self.position.entry_price
        else:
            diff = self.position.entry_price - price

        if diff >= settings["take_profit"]:
            pnl = self.close_position(price, "達到停利")
            return f"停利平倉 @ {price}，損益 {pnl:.0f} 元"

        if diff <= -settings["stop_loss"]:
            pnl = self.close_position(price, "達到停損")
            return f"停損平倉 @ {price}，損益 {pnl:.0f} 元"

        return None

    def open_position(self, side: str, price: float, reason: str):
        self.position = Position(
            side=side,
            entry_price=price,
            entry_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            reason=reason,
        )
        self.open_count += 1

    def close_position(self, price: float, reason: str):
        if self.position is None:
            return 0

        if self.position.side == "LONG":
            pnl_points = price - self.position.entry_price
        else:
            pnl_points = self.position.entry_price - price

        pnl_money = pnl_points * self.point_value * self.contracts
        self.capital += pnl_money

        if pnl_money < 0:
            self.daily_loss += pnl_money

        record = {
            "entry_time": self.position.entry_time,
            "exit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "side": self.position.side,
            "entry_price": self.position.entry_price,
            "exit_price": price,
            "pnl_points": pnl_points,
            "pnl_money": pnl_money,
            "capital": self.capital,
            "entry_reason": self.position.reason,
            "exit_reason": reason,
        }
        self.trades.append(record)
        self.position = None
        return pnl_money

    def force_close(self, price: float):
        if self.position:
            return self.close_position(price, "手動/停止監控平倉")
        return 0

    def export_trades(self, filename="trades.csv"):
        if not self.trades:
            return False

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.trades[0].keys())
            writer.writeheader()
            writer.writerows(self.trades)
        return True

    def position_text(self):
        if self.position is None:
            return "無持倉"
        side = "多單" if self.position.side == "LONG" else "空單"
        return f"{side} @ {self.position.entry_price}"

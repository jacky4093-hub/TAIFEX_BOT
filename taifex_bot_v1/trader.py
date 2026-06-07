from dataclasses import dataclass
from datetime import datetime
import csv
import config

@dataclass
class Position:
    side: str  # LONG or SHORT
    entry_price: float
    entry_time: str
    reason: str

class SimulatedTrader:
    def __init__(self):
        self.capital = config.INITIAL_CAPITAL
        self.position: Position | None = None
        self.trades = []
        self.trade_count = 0
        self.daily_loss = 0

    def can_trade(self) -> bool:
        if self.trade_count >= config.MAX_DAILY_TRADES:
            return False
        if self.daily_loss <= -abs(config.MAX_DAILY_LOSS):
            return False
        return True

    def on_signal(self, action: str, price: float, reason: str):
        if not self.can_trade():
            return "風控停止交易"

        if self.position is None:
            if action == "BUY":
                self.open_position("LONG", price, reason)
                return f"開多單 @ {price}，原因：{reason}"
            elif action == "SELL":
                self.open_position("SHORT", price, reason)
                return f"開空單 @ {price}，原因：{reason}"

        else:
            # 有持倉時，反向訊號就平倉
            if self.position.side == "LONG" and action == "SELL":
                pnl = self.close_position(price, f"反向訊號平多：{reason}")
                return f"平多單 @ {price}，損益 {pnl} 元"
            elif self.position.side == "SHORT" and action == "BUY":
                pnl = self.close_position(price, f"反向訊號平空：{reason}")
                return f"平空單 @ {price}，損益 {pnl} 元"

        return "已有同方向持倉，忽略訊號"

    def check_stop(self, price: float):
        if self.position is None:
            return None

        if self.position.side == "LONG":
            diff = price - self.position.entry_price
        else:
            diff = self.position.entry_price - price

        if diff >= config.TAKE_PROFIT_POINTS:
            pnl = self.close_position(price, "達到停利")
            return f"停利平倉 @ {price}，損益 {pnl} 元"

        if diff <= -config.STOP_LOSS_POINTS:
            pnl = self.close_position(price, "達到停損")
            return f"停損平倉 @ {price}，損益 {pnl} 元"

        return None

    def open_position(self, side: str, price: float, reason: str):
        self.position = Position(
            side=side,
            entry_price=price,
            entry_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            reason=reason,
        )
        self.trade_count += 1

    def close_position(self, price: float, reason: str):
        if self.position is None:
            return 0

        if self.position.side == "LONG":
            pnl_points = price - self.position.entry_price
        else:
            pnl_points = self.position.entry_price - price

        pnl_money = pnl_points * config.POINT_VALUE * config.CONTRACTS
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

    def export_trades(self, filename="trades.csv"):
        if not self.trades:
            return

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.trades[0].keys())
            writer.writeheader()
            writer.writerows(self.trades)

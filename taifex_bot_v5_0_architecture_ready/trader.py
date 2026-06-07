from dataclasses import dataclass
from datetime import datetime
import csv

@dataclass
class Position:
    side: str
    entry_price: float
    entry_time: str
    reason: str
    contracts: int

class SimulatedTrader:
    def __init__(self, initial_equity: float, point_value: int, margin_per_contract: int, contracts: int):
        self.initial_equity = initial_equity
        self.realized_pnl = 0
        self.point_value = point_value
        self.margin_per_contract = margin_per_contract
        self.contracts = contracts
        self.position: Position | None = None
        self.trades = []
        self.open_count = 0
        self.daily_loss = 0

    def set_contract(self, point_value: int, margin_per_contract: int, contracts: int):
        self.point_value = point_value
        self.margin_per_contract = margin_per_contract
        self.contracts = contracts

    def floating_pnl(self, current_price: float) -> float:
        if self.position is None:
            return 0
        if self.position.side == "LONG":
            pnl_points = current_price - self.position.entry_price
        else:
            pnl_points = self.position.entry_price - current_price
        return pnl_points * self.point_value * self.position.contracts

    def equity(self, current_price: float) -> float:
        return self.initial_equity + self.realized_pnl + self.floating_pnl(current_price)

    def used_margin(self) -> float:
        if self.position is None:
            return 0
        return self.margin_per_contract * self.position.contracts

    def available_funds(self, current_price: float) -> float:
        return self.equity(current_price) - self.used_margin()

    def risk_ratio(self, current_price: float) -> float:
        eq = self.equity(current_price)
        if eq <= 0:
            return 999
        return self.used_margin() / eq * 100

    def required_margin_for_new_position(self) -> float:
        return self.margin_per_contract * self.contracts

    def can_trade(self, settings: dict, current_price: float) -> tuple[bool, str]:
        if self.open_count >= settings["max_trades"]:
            return False, "已達每日最大交易次數"
        if self.daily_loss <= -abs(settings["max_loss"]):
            return False, "已達每日最大虧損限制"
        if self.position is None:
            required = self.required_margin_for_new_position()
            available = self.available_funds(current_price)
            if available < required:
                return False, f"資金不足，需要保證金 {required:,.0f}，可用資金 {available:,.0f}"
        return True, ""

    def on_signal(self, action: str, price: float, reason: str, settings: dict):
        ok, msg = self.can_trade(settings, price)
        if not ok:
            return msg

        if self.position is None:
            if action == "BUY":
                self.open_position("LONG", price, reason)
                return f"開多單 {self.contracts}口 @ {price}，原因：{reason}"
            if action == "SELL":
                self.open_position("SHORT", price, reason)
                return f"開空單 {self.contracts}口 @ {price}，原因：{reason}"

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
            contracts=self.contracts,
        )
        self.open_count += 1

    def close_position(self, price: float, reason: str):
        if self.position is None:
            return 0
        if self.position.side == "LONG":
            pnl_points = price - self.position.entry_price
        else:
            pnl_points = self.position.entry_price - price
        pnl_money = pnl_points * self.point_value * self.position.contracts
        self.realized_pnl += pnl_money
        if pnl_money < 0:
            self.daily_loss += pnl_money
        record = {
            "entry_time": self.position.entry_time,
            "exit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "side": self.position.side,
            "contracts": self.position.contracts,
            "entry_price": self.position.entry_price,
            "exit_price": price,
            "pnl_points": pnl_points,
            "pnl_money": pnl_money,
            "equity_after": self.initial_equity + self.realized_pnl,
            "entry_reason": self.position.reason,
            "exit_reason": reason,
        }
        self.trades.append(record)
        self.position = None
        return pnl_money

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
        return f"{side} {self.position.contracts}口 @ {self.position.entry_price}"

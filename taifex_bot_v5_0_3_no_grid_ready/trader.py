from dataclasses import dataclass
from datetime import datetime, date
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

        # Daily risk baseline: use today's starting capital as the reference.
        # This replaces the old "sum of losing trades" logic.
        self.trade_date = date.today()
        self.day_start_equity = float(initial_equity)
        self.day_start_realized_pnl = 0.0
        self.daily_risk_locked = False

    def reset_daily_baseline_if_needed(self, current_price: float):
        today = date.today()
        if today != self.trade_date:
            self.trade_date = today
            self.day_start_equity = self.equity(current_price)
            self.day_start_realized_pnl = self.realized_pnl
            self.open_count = 0
            self.daily_risk_locked = False

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

    def daily_pnl(self, current_price: float) -> float:
        """Today's P/L, based on today's starting equity, including floating P/L."""
        return self.equity(current_price) - self.day_start_equity

    def daily_pnl_percent(self, current_price: float) -> float:
        if self.day_start_equity == 0:
            return 0
        return self.daily_pnl(current_price) / self.day_start_equity * 100

    def max_daily_loss_amount(self, settings: dict) -> float:
        unit = settings.get("max_loss_unit", "元")
        value = abs(float(settings.get("max_loss", 0)))
        if unit == "%":
            return self.day_start_equity * value / 100
        return value

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

    def is_daily_loss_reached(self, settings: dict, current_price: float) -> bool:
        self.reset_daily_baseline_if_needed(current_price)
        return self.daily_pnl(current_price) <= -self.max_daily_loss_amount(settings)

    def can_trade(self, settings: dict, current_price: float) -> tuple[bool, str]:
        self.reset_daily_baseline_if_needed(current_price)
        if self.daily_risk_locked or self.is_daily_loss_reached(settings, current_price):
            self.daily_risk_locked = True
            return False, (
                f"已達每日最大虧損限制：日損益 {self.daily_pnl(current_price):,.0f} 元，"
                f"限制 {self.max_daily_loss_amount(settings):,.0f} 元。"
            )
        if self.open_count >= settings["max_trades"]:
            return False, "已達每日最大交易次數"
        if self.position is None:
            required = self.required_margin_for_new_position()
            available = self.available_funds(current_price)
            if available < required:
                return False, f"資金不足，需要保證金 {required:,.0f}，可用資金 {available:,.0f}"
        return True, ""

    def check_daily_risk(self, price: float, settings: dict):
        """Lock trading when today's equity loss reaches the limit. If holding a position, flatten it."""
        if self.daily_risk_locked and self.position is None:
            return None
        if self.is_daily_loss_reached(settings, price):
            self.daily_risk_locked = True
            if self.position is not None:
                pnl = self.close_position(price, "達到每日最大虧損，自動平倉")
                return f"達到每日最大虧損，已自動平倉 @ {price}，本筆損益 {pnl:.0f} 元"
            return "已達每日最大虧損限制，今日停止開新倉"
        return None

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
            "daily_pnl_after": self.realized_pnl - self.day_start_realized_pnl,
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

import sys
import time
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QSpinBox, QCheckBox, QTextEdit, QGroupBox,
    QMessageBox, QMenu
)
from PyQt6.QtCore import QTimer, pyqtSignal

from contract import CONTRACTS
from market_factory import MarketFactory
from broker_factory import BrokerFactory
from strategy import StrategyEngine
from updater import check_update, load_local_version

APP_VERSION = load_local_version().get("version", "5.1.2")
SETTINGS_FILE = Path("settings.json")


class FixedComboBox(QPushButton):
    currentTextChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._current_text = ""
        self._menu = QMenu(self)
        self.clicked.connect(self.show_menu)
        self.setMinimumWidth(120)
        self.setStyleSheet("text-align: left; padding-left: 6px;")

    def addItems(self, items):
        items = list(items)
        for item in items:
            self.addItem(item)
        if items and not self._current_text:
            self.setCurrentText(items[0])

    def addItem(self, text):
        text = str(text)
        self._items.append(text)
        action = self._menu.addAction(text)
        action.triggered.connect(lambda checked=False, value=text: self.setCurrentText(value))

    def setCurrentText(self, text):
        text = str(text)
        if text not in self._items:
            return
        old = self._current_text
        self._current_text = text
        self.setText(text + "  ▾")
        self._menu.close()
        if old != text:
            self.currentTextChanged.emit(text)

    def currentText(self):
        return self._current_text

    def show_menu(self):
        self._menu.close()
        self._menu.popup(self.mapToGlobal(self.rect().bottomLeft()))


class TaifexBotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"TAIFEX Bot V5.1.2 - 監測與交易分離版")
        self.resize(1150, 850)

        self.market = None
        self.strategy = StrategyEngine()
        self.trader = None
        self.current_price = 22000
        self._last_log_time = {}
        self.log_cooldown_seconds = 5
        self.trading_enabled = False
        self.trading_pause_reason = "尚未啟用交易"
        self._settings_loaded = False
        self._loading_settings = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_tick)

        self.build_ui()
        self.load_settings()
        self.reset_system()
        self.setup_auto_save_connections()

    def build_ui(self):
        main = QVBoxLayout()

        title = QLabel(f"台指期多商品多策略模擬交易機器人 V5.1.2  版本：{APP_VERSION}")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main.addWidget(title)

        account_group = QGroupBox("商品與帳戶")
        account = QGridLayout()

        self.contract_box = FixedComboBox()
        self.contract_box.addItems(CONTRACTS.keys())
        self.contract_box.currentTextChanged.connect(self.on_contract_changed)

        self.market_source_box = FixedComboBox()
        self.market_source_box.addItems(["模擬行情", "Shioaji真實行情（預留，尚未啟用）"])

        self.initial_equity_spin = QSpinBox()
        self.initial_equity_spin.setRange(10000, 100000000)
        self.initial_equity_spin.setSingleStep(10000)
        self.initial_equity_spin.setValue(1000000)

        self.contracts_spin = QSpinBox()
        self.contracts_spin.setRange(1, 100)
        self.contracts_spin.setValue(1)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(1000, 10000000)
        self.margin_spin.setSingleStep(1000)

        self.maintenance_margin_spin = QSpinBox()
        self.maintenance_margin_spin.setRange(1000, 10000000)
        self.maintenance_margin_spin.setSingleStep(1000)

        self.price_label = QLabel("台指期：-")
        self.price_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.equity_label = QLabel("帳戶權益：-")
        self.available_label = QLabel("可用資金：-")
        self.used_margin_label = QLabel("已用保證金：-")
        self.float_pnl_label = QLabel("浮動損益：-")
        self.realized_pnl_label = QLabel("已實現損益：-")
        self.risk_ratio_label = QLabel("風險率：-")
        self.daily_pnl_label = QLabel("今日損益：-")
        self.position_label = QLabel("持倉：-")
        self.point_value_label = QLabel("點值：-")
        self.monitor_status_label = QLabel("監測狀態：停止")
        self.trade_status_label = QLabel("交易狀態：暫停")
        self.trade_status_label.setStyleSheet("font-weight: bold;")

        account.addWidget(QLabel("商品"), 0, 0)
        account.addWidget(self.contract_box, 0, 1)
        account.addWidget(QLabel("行情來源"), 0, 2)
        account.addWidget(self.market_source_box, 0, 3)
        account.addWidget(QLabel("帳戶權益數"), 0, 4)
        account.addWidget(self.initial_equity_spin, 0, 5)
        account.addWidget(QLabel("每次下單口數"), 0, 6)
        account.addWidget(self.contracts_spin, 0, 7)
        account.addWidget(QLabel("單口原始保證金"), 0, 8)
        account.addWidget(self.margin_spin, 0, 9)
        account.addWidget(QLabel("單口維持保證金"), 0, 10)
        account.addWidget(self.maintenance_margin_spin, 0, 11)

        account.addWidget(self.price_label, 1, 0, 1, 2)
        account.addWidget(self.point_value_label, 1, 2)
        account.addWidget(self.position_label, 1, 3, 1, 2)
        account.addWidget(self.monitor_status_label, 1, 5, 1, 2)
        account.addWidget(self.trade_status_label, 1, 7, 1, 3)

        account.addWidget(self.equity_label, 2, 0)
        account.addWidget(self.available_label, 2, 1)
        account.addWidget(self.used_margin_label, 2, 2)
        account.addWidget(self.float_pnl_label, 2, 3)
        account.addWidget(self.realized_pnl_label, 2, 4)
        account.addWidget(self.risk_ratio_label, 2, 5)
        account.addWidget(self.daily_pnl_label, 2, 6, 1, 2)

        account_group.setLayout(account)
        main.addWidget(account_group)

        strategy_group = QGroupBox("策略設定")
        grid = QGridLayout()

        self.enable_breakout = QCheckBox("突破策略")
        self.enable_range = QCheckBox("區間策略")
        self.enable_ma = QCheckBox("均線策略")
        for cb in [self.enable_breakout, self.enable_range, self.enable_ma]:
            cb.setChecked(True)

        self.breakout_upper = self.spin(22080)
        self.breakout_lower = self.spin(21920)

        self.breakout_upper_action = FixedComboBox()
        self.breakout_upper_action.addItems(["做多", "做空", "不動作"])
        self.breakout_upper_action.setCurrentText("做多")

        self.breakout_lower_action = FixedComboBox()
        self.breakout_lower_action.addItems(["做空", "做多", "不動作"])
        self.breakout_lower_action.setCurrentText("做空")

        self.range_buy = self.spin(21950)
        self.range_sell = self.spin(22050)
        self.ma_short = self.spin(5, 1, 100)
        self.ma_long = self.spin(20, 2, 300)

        grid.addWidget(self.enable_breakout, 0, 0)
        grid.addWidget(QLabel("突破上限"), 0, 1)
        grid.addWidget(self.breakout_upper, 0, 2)
        grid.addWidget(QLabel("上限動作"), 0, 3)
        grid.addWidget(self.breakout_upper_action, 0, 4)
        grid.addWidget(QLabel("跌破下限"), 1, 1)
        grid.addWidget(self.breakout_lower, 1, 2)
        grid.addWidget(QLabel("下限動作"), 1, 3)
        grid.addWidget(self.breakout_lower_action, 1, 4)
        grid.addWidget(self.enable_range, 2, 0)
        grid.addWidget(QLabel("區間買進"), 2, 1)
        grid.addWidget(self.range_buy, 2, 2)
        grid.addWidget(QLabel("區間賣出"), 2, 3)
        grid.addWidget(self.range_sell, 2, 4)
        grid.addWidget(self.enable_ma, 3, 0)
        grid.addWidget(QLabel("短均線"), 3, 1)
        grid.addWidget(self.ma_short, 3, 2)
        grid.addWidget(QLabel("長均線"), 3, 3)
        grid.addWidget(self.ma_long, 3, 4)

        strategy_group.setLayout(grid)
        main.addWidget(strategy_group)

        risk_group = QGroupBox("風控設定")
        risk = QGridLayout()

        self.take_profit = self.spin(40, 1, 10000)
        self.stop_loss = self.spin(25, 1, 10000)
        self.max_loss = self.spin(10000, 0, 10000000)
        self.max_loss_unit_box = FixedComboBox()
        self.max_loss_unit_box.addItems(["元", "%"])
        self.max_trades = self.spin(20, 0, 1000)
        self.tick_interval = self.spin(200, 50, 5000)
        self.open_cooldown = self.spin(30, 0, 3600)
        self.stop_loss_reentry_cooldown = self.spin(300, 0, 86400)

        self.enable_time_filter = QCheckBox("啟用交易時段限制")
        self.enable_time_filter.setChecked(False)
        self.trade_start_hour = self.spin(8, 0, 23)
        self.trade_start_minute = self.spin(45, 0, 59)
        self.stop_open_hour = self.spin(13, 0, 23)
        self.stop_open_minute = self.spin(30, 0, 59)
        self.enable_force_close = QCheckBox("啟用強制平倉時間")
        self.enable_force_close.setChecked(False)
        self.force_close_hour = self.spin(13, 0, 23)
        self.force_close_minute = self.spin(44, 0, 59)

        risk.addWidget(QLabel("停利點數"), 0, 0)
        risk.addWidget(self.take_profit, 0, 1)
        risk.addWidget(QLabel("停損點數"), 0, 2)
        risk.addWidget(self.stop_loss, 0, 3)
        risk.addWidget(QLabel("每日最大虧損(0=不限制)"), 1, 0)
        risk.addWidget(self.max_loss, 1, 1)
        risk.addWidget(QLabel("單位"), 1, 2)
        risk.addWidget(self.max_loss_unit_box, 1, 3)
        risk.addWidget(QLabel("每日最大交易次數(0=不限制)"), 1, 4)
        risk.addWidget(self.max_trades, 1, 5)
        risk.addWidget(QLabel("模擬行情速度ms"), 2, 0)
        risk.addWidget(self.tick_interval, 2, 1)
        risk.addWidget(QLabel("開倉冷卻秒數(0秒=關閉)"), 2, 2)
        risk.addWidget(self.open_cooldown, 2, 3)
        risk.addWidget(QLabel("停損後重新進場冷卻秒數(0秒=關閉)"), 2, 4)
        risk.addWidget(self.stop_loss_reentry_cooldown, 2, 5)
        risk.addWidget(self.enable_time_filter, 3, 0, 1, 2)
        risk.addWidget(QLabel("開始交易"), 3, 2)
        risk.addWidget(self.trade_start_hour, 3, 3)
        risk.addWidget(QLabel(":"), 3, 4)
        risk.addWidget(self.trade_start_minute, 3, 5)
        risk.addWidget(QLabel("停止開倉"), 4, 2)
        risk.addWidget(self.stop_open_hour, 4, 3)
        risk.addWidget(QLabel(":"), 4, 4)
        risk.addWidget(self.stop_open_minute, 4, 5)
        risk.addWidget(self.enable_force_close, 5, 0, 1, 2)
        risk.addWidget(QLabel("強制平倉"), 5, 2)
        risk.addWidget(self.force_close_hour, 5, 3)
        risk.addWidget(QLabel(":"), 5, 4)
        risk.addWidget(self.force_close_minute, 5, 5)

        risk_group.setLayout(risk)
        main.addWidget(risk_group)

        stats_group = QGroupBox("交易統計")
        stats = QGridLayout()
        self.today_trade_count_label = QLabel("今日開倉次數：0")
        self.closed_trade_count_label = QLabel("已完成交易：0")
        self.win_rate_label = QLabel("勝率：0.0%")
        self.avg_win_label = QLabel("平均獲利：0")
        self.avg_loss_label = QLabel("平均虧損：0")
        self.profit_factor_label = QLabel("獲利因子：0.00")
        stats.addWidget(self.today_trade_count_label, 0, 0)
        stats.addWidget(self.closed_trade_count_label, 0, 1)
        stats.addWidget(self.win_rate_label, 0, 2)
        stats.addWidget(self.avg_win_label, 1, 0)
        stats.addWidget(self.avg_loss_label, 1, 1)
        stats.addWidget(self.profit_factor_label, 1, 2)
        stats_group.setLayout(stats)
        main.addWidget(stats_group)

        buttons = QHBoxLayout()
        self.start_monitor_btn = QPushButton("開始監測")
        self.stop_monitor_btn = QPushButton("停止監測")
        self.enable_trade_btn = QPushButton("啟用交易")
        self.pause_trade_btn = QPushButton("暫停交易")
        self.reset_btn = QPushButton("重置")
        self.save_settings_btn = QPushButton("儲存設定")
        self.update_btn = QPushButton("檢查更新")
        self.export_btn = QPushButton("匯出CSV")
        self.export_excel_btn = QPushButton("匯出Excel")

        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.enable_trade_btn.clicked.connect(self.enable_trading)
        self.pause_trade_btn.clicked.connect(lambda: self.pause_trading("手動暫停交易"))
        self.reset_btn.clicked.connect(self.reset_system)
        self.save_settings_btn.clicked.connect(lambda: self.save_settings(show_message=True))
        self.update_btn.clicked.connect(self.check_for_updates)
        self.export_btn.clicked.connect(self.export_trades)
        self.export_excel_btn.clicked.connect(self.export_trades_excel)

        for btn in [self.start_monitor_btn, self.stop_monitor_btn, self.enable_trade_btn, self.pause_trade_btn,
                    self.reset_btn, self.save_settings_btn, self.update_btn, self.export_btn, self.export_excel_btn]:
            buttons.addWidget(btn)
        main.addLayout(buttons)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        main.addWidget(self.log)
        self.setLayout(main)

    def spin(self, value, min_v=1, max_v=1000000):
        s = QSpinBox()
        s.setRange(min_v, max_v)
        s.setValue(value)
        return s

    def get_contract_info(self):
        return CONTRACTS[self.contract_box.currentText()]

    def get_settings(self):
        return {
            "contract": self.contract_box.currentText(),
            "market_source": self.market_source_box.currentText(),
            "initial_equity": self.initial_equity_spin.value(),
            "contracts": self.contracts_spin.value(),
            "margin": self.margin_spin.value(),
            "maintenance_margin": self.maintenance_margin_spin.value(),
            "enable_breakout": self.enable_breakout.isChecked(),
            "enable_range": self.enable_range.isChecked(),
            "enable_ma": self.enable_ma.isChecked(),
            "breakout_upper": self.breakout_upper.value(),
            "breakout_lower": self.breakout_lower.value(),
            "breakout_upper_action": self.breakout_upper_action.currentText(),
            "breakout_lower_action": self.breakout_lower_action.currentText(),
            "range_buy": self.range_buy.value(),
            "range_sell": self.range_sell.value(),
            "ma_short": self.ma_short.value(),
            "ma_long": self.ma_long.value(),
            "take_profit": self.take_profit.value(),
            "stop_loss": self.stop_loss.value(),
            "max_loss": self.max_loss.value(),
            "max_loss_unit": self.max_loss_unit_box.currentText(),
            "max_trades": self.max_trades.value(),
            "open_cooldown_seconds": self.open_cooldown.value(),
            "stop_loss_reentry_cooldown_seconds": self.stop_loss_reentry_cooldown.value(),
            "enable_time_filter": self.enable_time_filter.isChecked(),
            "trade_start_hour": self.trade_start_hour.value(),
            "trade_start_minute": self.trade_start_minute.value(),
            "stop_open_hour": self.stop_open_hour.value(),
            "stop_open_minute": self.stop_open_minute.value(),
            "enable_force_close": self.enable_force_close.isChecked(),
            "force_close_hour": self.force_close_hour.value(),
            "force_close_minute": self.force_close_minute.value(),
        }

    def apply_settings(self, data: dict):
        combo_map = {
            "contract": self.contract_box,
            "market_source": self.market_source_box,
            "breakout_upper_action": self.breakout_upper_action,
            "breakout_lower_action": self.breakout_lower_action,
            "max_loss_unit": self.max_loss_unit_box,
        }
        spin_map = {
            "initial_equity": self.initial_equity_spin,
            "contracts": self.contracts_spin,
            "margin": self.margin_spin,
            "maintenance_margin": self.maintenance_margin_spin,
            "breakout_upper": self.breakout_upper,
            "breakout_lower": self.breakout_lower,
            "range_buy": self.range_buy,
            "range_sell": self.range_sell,
            "ma_short": self.ma_short,
            "ma_long": self.ma_long,
            "take_profit": self.take_profit,
            "stop_loss": self.stop_loss,
            "max_loss": self.max_loss,
            "max_trades": self.max_trades,
            "open_cooldown_seconds": self.open_cooldown,
            "stop_loss_reentry_cooldown_seconds": self.stop_loss_reentry_cooldown,
            "trade_start_hour": self.trade_start_hour,
            "trade_start_minute": self.trade_start_minute,
            "stop_open_hour": self.stop_open_hour,
            "stop_open_minute": self.stop_open_minute,
            "force_close_hour": self.force_close_hour,
            "force_close_minute": self.force_close_minute,
        }
        check_map = {
            "enable_breakout": self.enable_breakout,
            "enable_range": self.enable_range,
            "enable_ma": self.enable_ma,
            "enable_time_filter": self.enable_time_filter,
            "enable_force_close": self.enable_force_close,
        }
        for key, widget in combo_map.items():
            if key in data:
                widget.setCurrentText(data[key])
        for key, widget in spin_map.items():
            if key in data:
                widget.setValue(int(data[key]))
        for key, widget in check_map.items():
            if key in data:
                widget.setChecked(bool(data[key]))


    def setup_auto_save_connections(self):
        widgets = [
            self.initial_equity_spin, self.contracts_spin, self.margin_spin, self.maintenance_margin_spin,
            self.breakout_upper, self.breakout_lower, self.range_buy, self.range_sell,
            self.ma_short, self.ma_long, self.take_profit, self.stop_loss, self.max_loss,
            self.max_trades, self.tick_interval, self.open_cooldown, self.stop_loss_reentry_cooldown,
            self.trade_start_hour, self.trade_start_minute, self.stop_open_hour, self.stop_open_minute,
            self.force_close_hour, self.force_close_minute,
        ]
        for widget in widgets:
            widget.valueChanged.connect(self.auto_save_settings)

        checks = [
            self.enable_breakout, self.enable_range, self.enable_ma,
            self.enable_time_filter, self.enable_force_close,
        ]
        for widget in checks:
            widget.toggled.connect(self.auto_save_settings)

        combos = [
            self.contract_box, self.market_source_box, self.breakout_upper_action,
            self.breakout_lower_action, self.max_loss_unit_box,
        ]
        for widget in combos:
            widget.currentTextChanged.connect(self.auto_save_settings)

    def auto_save_settings(self, *_):
        if self._loading_settings or self.trader is None:
            return
        self.save_settings(show_message=False)

    def save_settings(self, show_message=False):
        SETTINGS_FILE.write_text(json.dumps(self.get_settings(), ensure_ascii=False, indent=2), encoding="utf-8")
        if show_message:
            QMessageBox.information(self, "完成", "設定已儲存到 settings.json")

    def load_settings(self):
        if not SETTINGS_FILE.exists():
            return
        try:
            self._loading_settings = True
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            self.apply_settings(data)
            self._settings_loaded = True
        except Exception as exc:
            QMessageBox.warning(self, "設定讀取失敗", f"settings.json 讀取失敗：{exc}")
        finally:
            self._loading_settings = False

    def reset_system(self):
        info = self.get_contract_info()
        if not self._settings_loaded:
            self.margin_spin.setValue(info["margin"])
            self.maintenance_margin_spin.setValue(info.get("maintenance_margin", int(info["margin"] * 0.8)))
        self.current_price = info["default_price"]
        self.market = MarketFactory.create("sim", self.current_price)
        self.strategy.reset()
        self.trader = BrokerFactory.create(
            "sim",
            self.initial_equity_spin.value(),
            info["point_value"],
            self.margin_spin.value(),
            self.contracts_spin.value(),
            self.maintenance_margin_spin.value()
        )
        self.trading_enabled = False
        self.trading_pause_reason = "重置後交易暫停"
        self.log.clear()
        self.append_log("系統已重置，目前使用模擬行情 + 模擬交易，不會真實下單")
        self.append_log("V5.1.2：監測行情與機器人交易已拆成兩個按鈕")
        self.append_log("達每日最大交易次數或每日最大虧損時，只會暫停機器人交易，監測行情會繼續")
        self.append_log("平倉冷卻已移除，避免妨礙停損、停利、強制平倉等風控")
        self.append_log("新增停損後重新進場冷卻，可降低連續停損來回打臉；0秒代表關閉")
        self.append_log("開倉冷卻與停損後重新進場冷卻都支援 0秒=關閉")
        self.append_log("每日最大交易次數與每日最大虧損都支援 0=不限制")
        self.append_log("目前口數代表每次下單口數；金字塔加碼的最大總持倉口數保留到未來版本")
        self.append_log("新增維持保證金監控：權益數低於維持保證金時，暫停交易但不中斷監測")
        self.append_log("設定已支援自動保存，關閉程式前也會再保存一次")
        self.update_labels()

    def on_contract_changed(self, *_):
        if self._loading_settings:
            return
        if self.timer.isActive():
            self.stop_monitoring()
        info = self.get_contract_info()
        self.margin_spin.setValue(info["margin"])
        self.maintenance_margin_spin.setValue(info.get("maintenance_margin", int(info["margin"] * 0.8)))
        self.reset_system()

    def start_monitoring(self):
        if self.market_source_box.currentText().startswith("Shioaji"):
            QMessageBox.information(
                self,
                "尚未啟用",
                "Shioaji 真實行情目前只是預留。\n目前版本仍使用模擬行情。"
            )
            return
        self.timer.start(self.tick_interval.value())
        self.append_log("開始監測行情")
        self.update_labels()

    def stop_monitoring(self):
        self.timer.stop()
        self.pause_trading("停止監測，交易同步暫停")
        self.append_log("停止監測行情")
        self.update_labels()

    def enable_trading(self):
        required = self.margin_spin.value() * self.contracts_spin.value()
        maintenance_required = self.maintenance_margin_spin.value() * self.contracts_spin.value()
        if self.initial_equity_spin.value() < required:
            QMessageBox.warning(
                self,
                "資金不足",
                f"目前帳戶權益數 {self.initial_equity_spin.value():,} 元\n"
                f"需要原始保證金 {required:,} 元\n"
                f"維持保證金參考 {maintenance_required:,} 元\n"
                f"請降低口數、改交易較小商品，或提高帳戶權益數。"
            )
            return
        if not self.timer.isActive():
            self.start_monitoring()
            if not self.timer.isActive():
                return
        if self.trader.daily_risk_locked:
            QMessageBox.warning(self, "無法啟用交易", "今日已達每日最大虧損限制，請重置或隔日再啟用。")
            return
        if self.trader.is_max_trades_reached(self.get_settings()):
            QMessageBox.warning(self, "無法啟用交易", "今日已達每日最大交易次數。")
            return
        self.trading_enabled = True
        self.trading_pause_reason = ""
        self.append_log("機器人交易已啟用")
        self.update_labels()

    def pause_trading(self, reason="手動暫停交易"):
        was_enabled = self.trading_enabled
        self.trading_enabled = False
        self.trading_pause_reason = reason
        if was_enabled:
            self.append_log(reason)
        self.update_labels()

    def on_tick(self):
        tick = self.market.next_tick()
        self.current_price = tick.price

        info = self.get_contract_info()
        self.trader.set_contract(info["point_value"], self.margin_spin.value(), self.contracts_spin.value(), self.maintenance_margin_spin.value())
        settings = self.get_settings()

        force_close_msg = self.trader.check_force_close_time(self.current_price, settings)
        if force_close_msg:
            self.append_log(force_close_msg)

        daily_risk_msg = self.trader.check_daily_risk(self.current_price, settings)
        if daily_risk_msg:
            self.append_log(daily_risk_msg)
            if self.trader.daily_risk_locked and self.trader.position is None:
                self.pause_trading("已達每日最大虧損限制，機器人交易已暫停，監測行情繼續")

        stop_msg = self.trader.check_stop(self.current_price, settings)
        if stop_msg:
            self.append_log(stop_msg)

        daily_risk_msg = self.trader.check_daily_risk(self.current_price, settings)
        if daily_risk_msg:
            self.append_log(daily_risk_msg)
            if self.trader.daily_risk_locked and self.trader.position is None:
                self.pause_trading("已達每日最大虧損限制，機器人交易已暫停，監測行情繼續")

        margin_risk_msg = self.trader.check_maintenance_margin_risk(self.current_price)
        if margin_risk_msg:
            self.append_log(margin_risk_msg)
            self.pause_trading("權益數低於維持保證金，機器人交易已暫停，監測行情繼續")

        if self.trading_enabled and self.trader.is_max_trades_reached(settings) and self.trader.position is None:
            self.pause_trading("已達每日最大交易次數，機器人交易已暫停，監測行情繼續")

        signals = self.strategy.on_price(self.current_price, settings)
        if self.trading_enabled:
            for signal in signals:
                msg = self.trader.on_signal(signal.action, self.current_price, signal.reason, settings)
                if msg:
                    self.append_log(msg)
                    if "已達每日最大交易次數" in msg:
                        self.pause_trading("已達每日最大交易次數，機器人交易已暫停，監測行情繼續")
        elif signals:
            self.append_log(f"交易暫停中，僅監測訊號：{signals[0].action} / {signals[0].reason}")

        self.update_labels()

    def update_labels(self):
        info = self.get_contract_info()
        if self.trader:
            self.trader.set_contract(info["point_value"], self.margin_spin.value(), self.contracts_spin.value(), self.maintenance_margin_spin.value())

        equity = self.trader.equity(self.current_price)
        available = self.trader.available_funds(self.current_price)
        used = self.trader.used_margin()
        floating = self.trader.floating_pnl(self.current_price)
        realized = self.trader.realized_pnl
        risk = self.trader.risk_ratio(self.current_price)
        daily_pnl = self.trader.daily_pnl(self.current_price)
        daily_pnl_pct = self.trader.daily_pnl_percent(self.current_price)
        stats = self.trader.stats()

        self.price_label.setText(f"台指期：{self.current_price}")
        self.point_value_label.setText(f"點值：{info['point_value']} 元 / 點")
        self.position_label.setText(f"持倉：{self.trader.position_text()}")
        self.equity_label.setText(f"帳戶權益：{equity:,.0f}")
        self.available_label.setText(f"可用資金：{available:,.0f}")
        self.used_margin_label.setText(f"已用保證金：{used:,.0f}")
        self.float_pnl_label.setText(f"浮動損益：{floating:,.0f}")
        self.realized_pnl_label.setText(f"已實現損益：{realized:,.0f}")
        self.risk_ratio_label.setText(f"風險率：{risk:.1f}%")
        self.daily_pnl_label.setText(f"今日損益：{daily_pnl:,.0f} / {daily_pnl_pct:.2f}%")
        self.monitor_status_label.setText("監測狀態：運行中" if self.timer.isActive() else "監測狀態：停止")
        if self.trading_enabled:
            self.trade_status_label.setText("交易狀態：啟用")
        else:
            self.trade_status_label.setText(f"交易狀態：暫停（{self.trading_pause_reason}）")
        max_trades_text = "不限制" if self.max_trades.value() <= 0 else str(self.max_trades.value())
        self.today_trade_count_label.setText(f"今日開倉次數：{stats['open_count']} / {max_trades_text}")
        self.closed_trade_count_label.setText(f"已完成交易：{stats['closed_trades']}")
        self.win_rate_label.setText(f"勝率：{stats['win_rate']:.1f}%")
        self.avg_win_label.setText(f"平均獲利：{stats['avg_win']:,.0f}")
        self.avg_loss_label.setText(f"平均虧損：{stats['avg_loss']:,.0f}")
        self.profit_factor_label.setText(f"獲利因子：{stats['profit_factor']:.2f}")

    def check_for_updates(self):
        info = check_update()
        if info.has_update:
            QMessageBox.information(
                self,
                "發現新版本",
                f"目前版本：{info.current_version}\n"
                f"最新版本：{info.latest_version}\n\n"
                f"更新內容：\n{info.notes}\n\n"
                f"下載網址：\n{info.download_url}\n\n"
                f"目前版本先提供檢查與提示，下一版可加入自動下載覆蓋。"
            )
        else:
            QMessageBox.information(self, "檢查更新", f"目前版本：{info.current_version}\n{info.message}")

    def append_log(self, text):
        if not text:
            return
        now = time.time()
        last = self._last_log_time.get(text, 0)
        if now - last < self.log_cooldown_seconds:
            return
        self._last_log_time[text] = now
        self.log.append(text)

    def export_trades(self):
        ok = self.trader.export_trades("trades_v5_1_2.csv")
        if ok:
            QMessageBox.information(self, "完成", "已匯出 trades_v5_1_2.csv")
        else:
            QMessageBox.warning(self, "沒有資料", "目前沒有交易紀錄可以匯出")

    def export_trades_excel(self):
        ok = self.trader.export_trades_excel("trades_v5_1_2.xlsx")
        if ok:
            QMessageBox.information(self, "完成", "已匯出 trades_v5_1_2.xlsx")
        else:
            QMessageBox.warning(self, "沒有資料", "目前沒有交易紀錄可以匯出")

    def closeEvent(self, event):
        self.save_settings(show_message=False)
        event.accept()


def main():
    app = QApplication(sys.argv)
    gui = TaifexBotGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

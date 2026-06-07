import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QComboBox, QSpinBox, QCheckBox, QTextEdit, QGroupBox,
    QMessageBox, QListView, QApplication
)
from PyQt6.QtCore import QTimer, QEvent

from contract import CONTRACTS
from market_factory import MarketFactory
from broker_factory import BrokerFactory
from strategy import StrategyEngine
from updater import check_update, load_local_version

APP_VERSION = load_local_version().get("version", "5.0.9")


class FixedComboBox(QComboBox):
    """
    修正 WSL/Linux/PyQt6 下拉選單點選後不自動收合的問題。

    重點不是只呼叫 hidePopup()，而是攔截 popup 的滑鼠放開事件，
    手動設定目前選項後，強制把 popup view/window 關掉。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setView(QListView())
        self.view().viewport().installEventFilter(self)
        self.activated.connect(lambda _index: QTimer.singleShot(20, self._force_close_popup))

    def eventFilter(self, obj, event):
        if obj is self.view().viewport() and event.type() == QEvent.Type.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                self.setCurrentIndex(index.row())
                self.activated.emit(index.row())
            QTimer.singleShot(20, self._force_close_popup)
            return True
        return super().eventFilter(obj, event)

    def _force_close_popup(self):
        self.hidePopup()
        self.view().hide()
        popup_window = self.view().window()
        if popup_window:
            popup_window.hide()
        self.clearFocus()
        if self.parentWidget():
            self.parentWidget().setFocus()
        QApplication.processEvents()


class TaifexBotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"TAIFEX Bot V5-0-9 - 下拉選單強制收合版")
        self.resize(1100, 800)

        self.market = None
        self.strategy = StrategyEngine()
        self.trader = None
        self.current_price = 22000
        self._last_log_time = {}
        self.log_cooldown_seconds = 5

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_tick)

        self.build_ui()
        self.reset_system()

    def build_ui(self):
        main = QVBoxLayout()

        title = QLabel(f"台指期多商品多策略模擬交易機器人 V5-0-9  版本：{APP_VERSION}")
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

        account.addWidget(QLabel("商品"), 0, 0)
        account.addWidget(self.contract_box, 0, 1)
        account.addWidget(QLabel("行情來源"), 0, 2)
        account.addWidget(self.market_source_box, 0, 3)
        account.addWidget(QLabel("帳戶權益數"), 0, 4)
        account.addWidget(self.initial_equity_spin, 0, 5)
        account.addWidget(QLabel("口數"), 0, 6)
        account.addWidget(self.contracts_spin, 0, 7)
        account.addWidget(QLabel("單口保證金"), 0, 8)
        account.addWidget(self.margin_spin, 0, 9)

        account.addWidget(self.price_label, 1, 0, 1, 2)
        account.addWidget(self.point_value_label, 1, 2)
        account.addWidget(self.position_label, 1, 3, 1, 2)

        account.addWidget(self.equity_label, 2, 0)
        account.addWidget(self.available_label, 2, 1)
        account.addWidget(self.used_margin_label, 2, 2)
        account.addWidget(self.float_pnl_label, 2, 3)
        account.addWidget(self.realized_pnl_label, 2, 4)
        account.addWidget(self.risk_ratio_label, 2, 5)
        account.addWidget(self.daily_pnl_label, 2, 6)

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
        self.max_loss = self.spin(10000, 1, 10000000)
        self.max_loss_unit_box = FixedComboBox()
        self.max_loss_unit_box.addItems(["元", "%"])
        self.max_trades = self.spin(20, 1, 1000)
        self.tick_interval = self.spin(200, 50, 5000)

        risk.addWidget(QLabel("停利點數"), 0, 0)
        risk.addWidget(self.take_profit, 0, 1)
        risk.addWidget(QLabel("停損點數"), 0, 2)
        risk.addWidget(self.stop_loss, 0, 3)
        risk.addWidget(QLabel("每日最大虧損"), 1, 0)
        risk.addWidget(self.max_loss, 1, 1)
        risk.addWidget(QLabel("單位"), 1, 2)
        risk.addWidget(self.max_loss_unit_box, 1, 3)
        risk.addWidget(QLabel("每日最大交易次數"), 1, 4)
        risk.addWidget(self.max_trades, 1, 5)
        risk.addWidget(QLabel("模擬行情速度ms"), 2, 0)
        risk.addWidget(self.tick_interval, 2, 1)

        risk_group.setLayout(risk)
        main.addWidget(risk_group)

        buttons = QHBoxLayout()
        self.start_btn = QPushButton("開始監控")
        self.stop_btn = QPushButton("停止監控")
        self.reset_btn = QPushButton("重置")
        self.update_btn = QPushButton("檢查更新")
        self.export_btn = QPushButton("匯出交易紀錄")

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.reset_btn.clicked.connect(self.reset_system)
        self.update_btn.clicked.connect(self.check_for_updates)
        self.export_btn.clicked.connect(self.export_trades)

        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addWidget(self.reset_btn)
        buttons.addWidget(self.update_btn)
        buttons.addWidget(self.export_btn)
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
        }

    def reset_system(self):
        info = self.get_contract_info()
        self.margin_spin.setValue(info["margin"])
        self.current_price = info["default_price"]
        self.market = MarketFactory.create("sim", self.current_price)
        self.strategy.reset()
        self.trader = BrokerFactory.create(
            "sim",
            self.initial_equity_spin.value(),
            info["point_value"],
            self.margin_spin.value(),
            self.contracts_spin.value()
        )
        self.log.clear()
        self.append_log("系統已重置，目前使用 MarketFactory + BrokerFactory 架構")
        self.append_log("目前只啟用模擬行情 + 模擬交易，不會真實下單")
        self.append_log("Shioaji 真實行情已預留，下一版 V5-1 會加入登入設定畫面")
        self.append_log("每日最大虧損已改為：以當日本金基準計算，不再用虧損交易加總")
        self.append_log("突破策略已新增方向選單：突破上限 / 跌破下限 可分別設定做多、做空或不動作")
        self.append_log("達每日最大虧損時會先檢查持倉，平倉完成後才停止監測與交易")
        self.append_log("日誌防洗版已啟用：同方向持倉提示只顯示一次，相同訊息 5 秒內不重複顯示")
        self.append_log("下拉選單已修正：點選後會立即套用並自動收合")
        self.update_labels()

    def on_contract_changed(self):
        if self.timer.isActive():
            self.stop()
        self.reset_system()

    def start(self):
        if self.market_source_box.currentText().startswith("Shioaji"):
            QMessageBox.information(
                self,
                "尚未啟用",
                "Shioaji 真實行情目前只是預留。\nV5-1 會加入登入設定畫面。\nV5-2 才會接 TX / MTX / TMF 即時行情。"
            )
            return

        required = self.margin_spin.value() * self.contracts_spin.value()
        if self.initial_equity_spin.value() < required:
            QMessageBox.warning(
                self,
                "資金不足",
                f"目前帳戶權益數 {self.initial_equity_spin.value():,} 元\n"
                f"需要保證金 {required:,} 元\n"
                f"請降低口數、改交易較小商品，或提高帳戶權益數。"
            )
            return

        self.timer.start(self.tick_interval.value())
        self.append_log("開始監控")

    def stop(self):
        self.timer.stop()
        self.append_log("停止監控")

    def on_tick(self):
        tick = self.market.next_tick()
        self.current_price = tick.price

        info = self.get_contract_info()
        self.trader.set_contract(info["point_value"], self.margin_spin.value(), self.contracts_spin.value())

        settings = self.get_settings()

        daily_risk_msg = self.trader.check_daily_risk(self.current_price, settings)
        if daily_risk_msg:
            self.append_log(daily_risk_msg)
            if self.trader.daily_risk_locked and self.trader.position is None:
                self.timer.stop()
                self.append_log("已達每日最大虧損限制，確認無持倉，停止監測與交易")
            self.update_labels()
            return

        stop_msg = self.trader.check_stop(self.current_price, settings)
        if stop_msg:
            self.append_log(stop_msg)

        daily_risk_msg = self.trader.check_daily_risk(self.current_price, settings)
        if daily_risk_msg:
            self.append_log(daily_risk_msg)
            if self.trader.daily_risk_locked and self.trader.position is None:
                self.timer.stop()
                self.append_log("已達每日最大虧損限制，確認無持倉，停止監測與交易")
            self.update_labels()
            return

        signals = self.strategy.on_price(self.current_price, settings)
        for signal in signals:
            msg = self.trader.on_signal(signal.action, self.current_price, signal.reason, settings)
            if msg:
                self.append_log(msg)

        self.update_labels()

    def update_labels(self):
        info = self.get_contract_info()
        if self.trader:
            self.trader.set_contract(info["point_value"], self.margin_spin.value(), self.contracts_spin.value())

        equity = self.trader.equity(self.current_price)
        available = self.trader.available_funds(self.current_price)
        used = self.trader.used_margin()
        floating = self.trader.floating_pnl(self.current_price)
        realized = self.trader.realized_pnl
        risk = self.trader.risk_ratio(self.current_price)
        daily_pnl = self.trader.daily_pnl(self.current_price)
        daily_pnl_pct = self.trader.daily_pnl_percent(self.current_price)

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
            QMessageBox.information(
                self,
                "檢查更新",
                f"目前版本：{info.current_version}\n"
                f"{info.message}"
            )

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
        ok = self.trader.export_trades("trades.csv")
        if ok:
            QMessageBox.information(self, "完成", "已匯出 trades.csv")
        else:
            QMessageBox.warning(self, "沒有資料", "目前沒有交易紀錄可以匯出")

def main():
    app = QApplication(sys.argv)
    gui = TaifexBotGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

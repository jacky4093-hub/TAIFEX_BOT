import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QComboBox, QSpinBox, QCheckBox, QTextEdit, QGroupBox,
    QMessageBox
)
from PyQt6.QtCore import QTimer

from contract import CONTRACTS
from market_data import SimulatedMarketData
from strategy import StrategyEngine
from trader import SimulatedTrader

class TaifexBotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TAIFEX Bot V2 - 台指期多策略模擬交易機器人")
        self.resize(980, 720)

        self.market = None
        self.strategy = StrategyEngine()
        self.trader = None
        self.current_price = 22000

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_tick)

        self.build_ui()
        self.reset_system()

    def build_ui(self):
        main = QVBoxLayout()

        title = QLabel("台指期多商品多策略模擬交易機器人 V2")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main.addWidget(title)

        top_group = QGroupBox("商品與帳戶")
        top = QGridLayout()

        self.contract_box = QComboBox()
        self.contract_box.addItems(CONTRACTS.keys())
        self.contract_box.currentTextChanged.connect(self.on_contract_changed)

        self.price_label = QLabel("價格：-")
        self.price_label.setStyleSheet("font-size: 28px; font-weight: bold;")

        self.capital_label = QLabel("資金：-")
        self.position_label = QLabel("持倉：-")
        self.point_value_label = QLabel("點值：-")

        self.initial_capital_spin = QSpinBox()
        self.initial_capital_spin.setRange(10000, 100000000)
        self.initial_capital_spin.setSingleStep(10000)
        self.initial_capital_spin.setValue(1000000)

        self.contracts_spin = QSpinBox()
        self.contracts_spin.setRange(1, 100)
        self.contracts_spin.setValue(1)

        top.addWidget(QLabel("商品"), 0, 0)
        top.addWidget(self.contract_box, 0, 1)
        top.addWidget(QLabel("模擬資金"), 0, 2)
        top.addWidget(self.initial_capital_spin, 0, 3)
        top.addWidget(QLabel("口數"), 0, 4)
        top.addWidget(self.contracts_spin, 0, 5)

        top.addWidget(self.price_label, 1, 0, 1, 2)
        top.addWidget(self.capital_label, 1, 2)
        top.addWidget(self.position_label, 1, 3)
        top.addWidget(self.point_value_label, 1, 4)

        top_group.setLayout(top)
        main.addWidget(top_group)

        strategy_group = QGroupBox("策略設定")
        grid = QGridLayout()

        self.enable_breakout = QCheckBox("突破策略")
        self.enable_range = QCheckBox("區間策略")
        self.enable_ma = QCheckBox("均線策略")
        self.enable_grid = QCheckBox("網格策略")
        for cb in [self.enable_breakout, self.enable_range, self.enable_ma, self.enable_grid]:
            cb.setChecked(True)

        self.breakout_upper = self.spin(22080)
        self.breakout_lower = self.spin(21920)
        self.range_buy = self.spin(21950)
        self.range_sell = self.spin(22050)
        self.ma_short = self.spin(5, 1, 100)
        self.ma_long = self.spin(20, 2, 300)
        self.grid_base = self.spin(22000)
        self.grid_size = self.spin(30, 1, 1000)

        grid.addWidget(self.enable_breakout, 0, 0)
        grid.addWidget(QLabel("突破上限"), 0, 1)
        grid.addWidget(self.breakout_upper, 0, 2)
        grid.addWidget(QLabel("跌破下限"), 0, 3)
        grid.addWidget(self.breakout_lower, 0, 4)

        grid.addWidget(self.enable_range, 1, 0)
        grid.addWidget(QLabel("區間買進"), 1, 1)
        grid.addWidget(self.range_buy, 1, 2)
        grid.addWidget(QLabel("區間賣出"), 1, 3)
        grid.addWidget(self.range_sell, 1, 4)

        grid.addWidget(self.enable_ma, 2, 0)
        grid.addWidget(QLabel("短均線"), 2, 1)
        grid.addWidget(self.ma_short, 2, 2)
        grid.addWidget(QLabel("長均線"), 2, 3)
        grid.addWidget(self.ma_long, 2, 4)

        grid.addWidget(self.enable_grid, 3, 0)
        grid.addWidget(QLabel("網格基準"), 3, 1)
        grid.addWidget(self.grid_base, 3, 2)
        grid.addWidget(QLabel("網格間距"), 3, 3)
        grid.addWidget(self.grid_size, 3, 4)

        strategy_group.setLayout(grid)
        main.addWidget(strategy_group)

        risk_group = QGroupBox("風控設定")
        risk = QGridLayout()

        self.take_profit = self.spin(40, 1, 10000)
        self.stop_loss = self.spin(25, 1, 10000)
        self.max_loss = self.spin(10000, 100, 10000000)
        self.max_trades = self.spin(20, 1, 1000)
        self.tick_interval = self.spin(200, 50, 5000)

        risk.addWidget(QLabel("停利點數"), 0, 0)
        risk.addWidget(self.take_profit, 0, 1)
        risk.addWidget(QLabel("停損點數"), 0, 2)
        risk.addWidget(self.stop_loss, 0, 3)
        risk.addWidget(QLabel("每日最大虧損"), 1, 0)
        risk.addWidget(self.max_loss, 1, 1)
        risk.addWidget(QLabel("每日最大交易次數"), 1, 2)
        risk.addWidget(self.max_trades, 1, 3)
        risk.addWidget(QLabel("模擬行情速度ms"), 2, 0)
        risk.addWidget(self.tick_interval, 2, 1)

        risk_group.setLayout(risk)
        main.addWidget(risk_group)

        buttons = QHBoxLayout()
        self.start_btn = QPushButton("開始監控")
        self.stop_btn = QPushButton("停止監控")
        self.reset_btn = QPushButton("重置")
        self.export_btn = QPushButton("匯出交易紀錄")

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.reset_btn.clicked.connect(self.reset_system)
        self.export_btn.clicked.connect(self.export_trades)

        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addWidget(self.reset_btn)
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
            "enable_grid": self.enable_grid.isChecked(),
            "breakout_upper": self.breakout_upper.value(),
            "breakout_lower": self.breakout_lower.value(),
            "range_buy": self.range_buy.value(),
            "range_sell": self.range_sell.value(),
            "ma_short": self.ma_short.value(),
            "ma_long": self.ma_long.value(),
            "grid_base": self.grid_base.value(),
            "grid_size": self.grid_size.value(),
            "take_profit": self.take_profit.value(),
            "stop_loss": self.stop_loss.value(),
            "max_loss": self.max_loss.value(),
            "max_trades": self.max_trades.value(),
        }

    def reset_system(self):
        info = self.get_contract_info()
        self.current_price = info["default_price"]
        self.market = SimulatedMarketData(self.current_price)
        self.strategy.reset()
        self.trader = SimulatedTrader(
            self.initial_capital_spin.value(),
            info["point_value"],
            self.contracts_spin.value()
        )
        self.log.clear()
        self.append_log("系統已重置，目前是模擬行情，不會真實下單")
        self.update_labels()

    def on_contract_changed(self):
        if self.timer.isActive():
            self.stop()
        self.reset_system()

    def start(self):
        self.timer.start(self.tick_interval.value())
        self.append_log("開始監控")

    def stop(self):
        self.timer.stop()
        self.append_log("停止監控")

    def on_tick(self):
        tick = self.market.next_tick()
        self.current_price = tick.price

        settings = self.get_settings()

        stop_msg = self.trader.check_stop(self.current_price, settings)
        if stop_msg:
            self.append_log(stop_msg)

        signals = self.strategy.on_price(self.current_price, settings)
        for signal in signals:
            msg = self.trader.on_signal(signal.action, self.current_price, signal.reason, settings)
            self.append_log(msg)

        self.update_labels()

    def update_labels(self):
        info = self.get_contract_info()
        self.trader.set_contract(info["point_value"], self.contracts_spin.value())

        self.price_label.setText(f"價格：{self.current_price}")
        self.capital_label.setText(f"資金：{self.trader.capital:,.0f}")
        self.position_label.setText(f"持倉：{self.trader.position_text()}")
        self.point_value_label.setText(f"點值：{info['point_value']} 元 / 點")

    def append_log(self, text):
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

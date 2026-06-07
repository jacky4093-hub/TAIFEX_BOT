from market_data import SimulatedMarketData
from strategy import StrategyEngine
from trader import SimulatedTrader

def main():
    market = SimulatedMarketData()
    strategy = StrategyEngine()
    trader = SimulatedTrader()

    print("=== 台指期多策略模擬交易機器人 V1 ===")
    print("目前版本：模擬行情 + 模擬交易，不會真實下單")
    print("-" * 50)

    for tick in market.stream():
        price = tick.price
        print(f"[{tick.index}] 價格：{price} | 資金：{trader.capital:.0f}")

        stop_msg = trader.check_stop(price)
        if stop_msg:
            print("  >>>", stop_msg)
            continue

        signals = strategy.on_price(price)
        for signal in signals:
            msg = trader.on_signal(signal.action, price, signal.reason)
            print("  >>>", msg)

    trader.export_trades("trades.csv")
    print("-" * 50)
    print(f"結束資金：{trader.capital:.0f}")
    print(f"交易次數：{len(trader.trades)}")
    print("交易紀錄已輸出 trades.csv")

if __name__ == "__main__":
    main()

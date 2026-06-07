# TAIFEX BOT V5.0.7

本版變更：
- 移除網格策略。
- 保留突破策略、區間策略、均線策略。
- 保留 V5.0.5 突破/跌破方向選單。
- 保留 V5.0.1 每日最大虧損單位與當日本金基準風控。

啟動：
```bash
python3 main_gui.py
```

# TAIFEX Bot V5-0-2 - 突破策略方向版

這版是從 V4 升級來的實際可執行版本。

## V5-0-2 完成內容

- 保留 V4 GUI
- 保留 TX / MTX / TMF
- 保留多策略開關
- 保留保證金、權益數、可用資金、風險率
- 保留檢查更新按鈕
- 新增 `MarketFactory`
- 新增 `BrokerFactory`
- 新增 `SimBroker`
- 新增 `ShioajiMarketSource` 骨架
- 真實下單仍安全鎖定
- 每日最大虧損支援「元 / %」，並以當日本金為基準
- 突破策略新增方向選單：突破上限 / 跌破下限可各自設定「做多 / 做空 / 不動作」

## 執行方式 WSL / Linux

```bash
cd /mnt/d/AI程式專案/TAIFEX_BOT
unzip taifex_bot_v5_0_2_breakout_direction_ready.zip
cd taifex_bot_v5_0_2_breakout_direction_ready
pip3 install --break-system-packages -r requirements.txt
python3 main_gui.py
```

## 執行方式 Windows CMD

```bat
cd /d D:\AI程式專案\TAIFEX_BOT\taifex_bot_v5_0_2_breakout_direction_ready
python -m pip install -r requirements.txt
python main_gui.py
```

## 下一步

V5-1：加入 Shioaji 登入設定畫面，但仍不下單。


## V5.0.5
- 修正主畫面「價格」欄位為「台指期」。


## V5.0.5
- 修正 QComboBox 下拉選單點選後畫面殘留/未收合問題。
- 點選後會自動套用、收合，焦點回到主視窗。


## V5.0.6
- 每日最大虧損觸發時，會先檢查是否有持倉。
- 若有持倉，先自動平倉。
- 確認無持倉後，才停止監測與交易。


## V5.0.7
- 同方向持倉提示只顯示一次，避免 Log 洗版。
- 平倉後會重置提示狀態，下次重新開倉後仍會提示一次。
- 新增相同訊息 5 秒防重複顯示。

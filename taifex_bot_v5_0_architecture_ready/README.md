# TAIFEX Bot V5-0 - 架構重構版

這版是從 V4 升級來的實際可執行版本。

## V5-0 完成內容

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

## 執行方式 WSL / Linux

```bash
cd /mnt/d/AI程式專案/TAIFEX_BOT
unzip taifex_bot_v5_0_architecture_ready.zip
cd taifex_bot_v5_0_architecture_ready
pip3 install --break-system-packages -r requirements.txt
python3 main_gui.py
```

## 執行方式 Windows CMD

```bat
cd /d D:\AI程式專案\TAIFEX_BOT\taifex_bot_v5_0_architecture_ready
python -m pip install -r requirements.txt
python main_gui.py
```

## 下一步

V5-1：加入 Shioaji 登入設定畫面，但仍不下單。

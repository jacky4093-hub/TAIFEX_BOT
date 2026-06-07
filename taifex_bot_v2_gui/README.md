# TAIFEX Bot V2 GUI - 台指期多商品多策略模擬交易機器人

這是 V2：加入 PyQt6 GUI 介面。

## 支援商品
- 大台 TX：1 點 = 200 元
- 小台 MTX：1 點 = 50 元
- 微台 TMF：1 點 = 10 元

## 功能
- 模擬資金
- 商品切換
- 突破策略
- 區間策略
- 均線策略
- 網格策略
- 停利停損
- 交易紀錄即時顯示
- 匯出 trades.csv
- 未來可接永豐 Shioaji 真實行情

## 安裝 PyQt6

```bash
pip3 install PyQt6
```

如果 Ubuntu 沒有 pip：

```bash
sudo apt install -y python3-pip
pip3 install PyQt6
```

## 執行

```bash
cd taifex_bot_v2_gui
python3 main_gui.py
```

## 注意
目前仍是模擬行情，不是真實台指期行情，也不會真實下單。

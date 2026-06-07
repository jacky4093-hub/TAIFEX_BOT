# 台指期多商品多策略模擬交易機器人 V5-0

## 本版重點

V5-0 是後續接 Shioaji 真實行情前的架構整理版。

已完成：

- 保留 V1~V4 功能
- 模擬行情
- 模擬交易
- CSV 交易紀錄
- PyQt6 GUI
- 大台 TX / 小台 MTX / 微台 TMF
- 策略開關
- 保證金、權益數、可用資金、已用保證金、浮動損益、已實現損益、風險率
- 檢查更新按鈕
- version.json
- Shioaji 預留

## V5-0 新增

- `market_factory.py`
  - 統一建立行情來源
  - 目前啟用 `sim`
  - 預留 `shioaji`

- `broker_factory.py`
  - 統一建立交易介面
  - 目前啟用 `sim`
  - 預留 `shioaji`

- `broker_base.py`
  - 交易介面抽象層

- `sim_market.py`
  - 模擬行情別名模組

- `shioaji_market.py`
  - Shioaji 行情預留模組

- `sim_broker.py`
  - 模擬交易別名模組

## 安全狀態

目前仍然不會真實下單。

Shioaji 真實行情尚未啟用。
Shioaji 真實下單尚未啟用。

## 執行方式

```bash
pip install PyQt6
python main_gui.py
```

## 下一版建議

V5-1：新增 Shioaji 登入設定畫面，但先只測試登入，不訂閱、不下單。

V5-2：接 Shioaji 真實行情，只收報價，不下單。

V6：K 線圖與技術指標。

V7：紙上交易回測。

V8：真實下單，並加入二次確認、最大口數限制與安全鎖。

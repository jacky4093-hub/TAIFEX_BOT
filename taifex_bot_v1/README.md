# TAIFEX Bot V1 - 台指期多策略模擬交易機器人

這是第一版：不接真實券商、不真下單，只做模擬行情 + 多策略交易 + 損益紀錄。

## 功能
- 模擬資金：100萬
- 支援策略：
  - 突破策略 Breakout
  - 區間策略 Range
  - 均線策略 Moving Average
  - 網格策略 Grid
- 支援停利、停損
- 每次最多一筆主要持倉
- 交易紀錄輸出 CSV
- 未來可接永豐 Shioaji API

## 執行方式

```bash
cd taifex_bot_v1
python3 main.py
```

## 設定檔
請修改 `config.py`

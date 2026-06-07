# TAIFEX Bot V3 Margin GUI

V3 新增：
- 帳戶權益數
- 商品保證金檢查
- 已使用保證金
- 可用資金
- 浮動損益
- 已實現損益
- 風險率
- 資金不足不允許開倉
- 仍然是模擬行情，不真實下單

## 支援商品
- 大台 TX
- 小台 MTX
- 微台 TMF

## 安裝中文字型

```bash
sudo apt install -y fonts-noto-cjk
```

## 安裝 PyQt6

```bash
pip3 install --break-system-packages PyQt6
```

## 執行

```bash
cd taifex_bot_v3_margin_gui
python3 main_gui.py
```

## 注意
保證金金額是可調整的預設值，不是即時官方數字。
正式交易前，請以期交所與券商公告為準。

# TAIFEX Bot V5.1.0

本版以 V5.0.12 穩定版為基礎，不再調整下拉選單，新增實戰風控功能。

## 新增功能

- 開倉冷卻秒數：平倉後等待指定秒數，避免馬上被雜訊重新開倉。
- 平倉冷卻秒數：開倉後等待指定秒數，避免剛進場就被反向雜訊洗掉。
- 交易時段限制：可選擇啟用。
  - 開始交易時間
  - 停止開倉時間
  - 強制平倉時間

## 啟動

```bash
cd /mnt/d/AI程式專案/TAIFEX_BOT
unzip taifex_bot_v5_1_0_cooldown_time_ready.zip
cd taifex_bot_v5_1_0_cooldown_time_ready
pip3 install --break-system-packages -r requirements.txt
python3 main_gui.py
```

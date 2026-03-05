# Stockmarket
# Stock Market Overview Dashboard (PyQt6)

A local desktop app that displays top stocks, real-time quote information, and interactive charts using the free **Alpha Vantage API**.

## Features

- Dashboard table for top 10–20 stocks
- Columns:
  - Symbol
  - Company Name
  - Current Price
  - Daily Change %
  - Volume
- Click a stock row to load a price graph
- Time ranges:
  - 1 Day (intraday)
  - 1 Week
  - 1 Month
- Auto-refresh every 60 seconds
- Search bar for ticker symbols
- Clean dark modern UI
- Separated API / UI / chart code

---

## Project Structure

```text
.
├── main.py
├── stock_api.py
├── chart_widget.py
├── ui_main.py
├── requirements.txt
└── README.md
```

---

## Install

```bash
pip install -r requirements.txt
```

---

## Run

```bash
python main.py
```

---

## Build Windows `.exe` (PyInstaller)

Install PyInstaller:

```bash
pip install pyinstaller
```

Build:

```bash
pyinstaller --noconfirm --onefile --windowed --name StockDashboard main.py
```

Output:

```text
dist/StockDashboard.exe
```

---

## Notes

- API key is currently embedded in `ui_main.py` as requested.
- Alpha Vantage free tier has strict rate limits; if data fails, wait and retry.

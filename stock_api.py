"""
stock_api.py

Handles Alpha Vantage API requests and response parsing.
Includes rate-limit and error handling for free-tier usage.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import requests


@dataclass
class Quote:
    """Represents a stock quote row for the dashboard table."""
    symbol: str
    company_name: str
    current_price: float
    daily_change_percent: float
    volume: int


class AlphaVantageClient:
    """Simple wrapper around Alpha Vantage API endpoints."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str, timeout: int = 15) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, params: Dict[str, str]) -> Dict:
        """Send GET request and return parsed JSON with validation."""
        merged = dict(params)
        merged["apikey"] = self.api_key

        try:
            resp = self.session.get(self.BASE_URL, params=merged, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"Network/API request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("API returned invalid JSON.") from exc

        if "Error Message" in data:
            raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")
        if "Note" in data:
            raise RuntimeError(f"Alpha Vantage rate limit: {data['Note']}")
        if not data:
            raise RuntimeError("Empty API response.")

        return data

    def get_quote(self, symbol: str) -> Quote:
        """Fetch real-time quote for one symbol."""
        data = self._get({"function": "GLOBAL_QUOTE", "symbol": symbol.upper().strip()})
        global_quote = data.get("Global Quote")
        if not global_quote:
            raise RuntimeError(f"No quote data available for symbol '{symbol}'.")

        try:
            price = float(global_quote.get("05. price", "0") or 0)
            change_percent_str = (global_quote.get("10. change percent", "0%") or "0%").replace("%", "")
            change_percent = float(change_percent_str)
            volume = int(float(global_quote.get("06. volume", "0") or 0))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Unexpected quote format for '{symbol}'.") from exc

        company_name = self._lookup_company_name(symbol)

        return Quote(
            symbol=symbol.upper(),
            company_name=company_name,
            current_price=price,
            daily_change_percent=change_percent,
            volume=volume,
        )

    def _lookup_company_name(self, symbol: str) -> str:
        """Best-effort company name lookup from SYMBOL_SEARCH."""
        try:
            data = self._get({"function": "SYMBOL_SEARCH", "keywords": symbol.upper().strip()})
            matches = data.get("bestMatches", [])
            for item in matches:
                if item.get("1. symbol", "").upper() == symbol.upper():
                    return item.get("2. name", symbol.upper())
            if matches:
                return matches[0].get("2. name", symbol.upper())
        except RuntimeError:
            pass
        return symbol.upper()

    def get_intraday_series(self, symbol: str, interval: str = "5min") -> List[Tuple[datetime, float]]:
        """Fetch intraday series for 1D chart."""
        data = self._get(
            {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol.upper().strip(),
                "interval": interval,
                "outputsize": "compact",
            }
        )
        key = f"Time Series ({interval})"
        series = data.get(key)
        if not series:
            raise RuntimeError(f"No intraday data available for '{symbol}'.")

        points: List[Tuple[datetime, float]] = []
        for ts_str, values in series.items():
            try:
                dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                close_price = float(values["4. close"])
                points.append((dt, close_price))
            except Exception:
                continue

        points.sort(key=lambda x: x[0])
        return points

    def get_daily_series(self, symbol: str) -> List[Tuple[datetime, float]]:
        """Fetch daily adjusted series for 1W/1M charts."""
        data = self._get(
            {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol.upper().strip(),
                "outputsize": "compact",
            }
        )
        series = data.get("Time Series (Daily)")
        if not series:
            raise RuntimeError(f"No daily data available for '{symbol}'.")

        points: List[Tuple[datetime, float]] = []
        for date_str, values in series.items():
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                close_price = float(values["4. close"])
                points.append((dt, close_price))
            except Exception:
                continue

        points.sort(key=lambda x: x[0])
        return points

    def get_history_for_range(self, symbol: str, range_key: str) -> List[Tuple[datetime, float]]:
        """Return points for selected range: 1D / 1W / 1M."""
        rk = range_key.upper().strip()

        if rk == "1D":
            return self.get_intraday_series(symbol, interval="5min")

        daily = self.get_daily_series(symbol)
        now = datetime.now()

        if rk == "1W":
            cutoff = now - timedelta(days=7)
        elif rk == "1M":
            cutoff = now - timedelta(days=30)
        else:
            raise RuntimeError(f"Unsupported range '{range_key}'. Use 1D, 1W, or 1M.")

        filtered = [(d, p) for d, p in daily if d >= cutoff]
        return filtered if filtered else daily[-30:]


def fetch_top_quotes(
    client: AlphaVantageClient,
    symbols: List[str],
    sleep_seconds: float = 12.0,
):
    """
    Fetch quotes for a list of symbols with spacing between calls
    to reduce free-tier rate-limit hits.
    """
    quotes = []
    errors = []

    for idx, symbol in enumerate(symbols):
        try:
            quotes.append(client.get_quote(symbol))
        except RuntimeError as exc:
            errors.append(f"{symbol}: {exc}")

        if idx < len(symbols) - 1:
            time.sleep(sleep_seconds)

    return quotes, errors

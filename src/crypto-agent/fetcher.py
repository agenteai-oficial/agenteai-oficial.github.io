import urllib.request
import json
from datetime import datetime


BASE = "https://api.binance.com"


def _get(path: str) -> dict | list:
    url = f"{BASE}{path}"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def get_klines(symbol: str, interval: str = "15m", limit: int = 100) -> list[dict]:
    raw = _get(f"/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}")
    return [
        {
            "time": datetime.fromtimestamp(k[0] / 1000).isoformat(),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        }
        for k in raw
    ]


def get_ticker(symbol: str) -> dict:
    return _get(f"/api/v3/ticker/24hr?symbol={symbol}")


def get_orderbook_depth(symbol: str) -> dict:
    data = _get(f"/api/v3/depth?symbol={symbol}&limit=5")
    best_bid = float(data["bids"][0][0])
    best_ask = float(data["asks"][0][0])
    return {
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread_pct": round((best_ask - best_bid) / best_bid * 100, 4),
    }

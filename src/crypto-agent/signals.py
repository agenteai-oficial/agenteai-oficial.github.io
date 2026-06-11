def _ema(prices: list[float], period: int) -> list[float]:
    k = 2 / (period + 1)
    result = [prices[0]]
    for p in prices[1:]:
        result.append(p * k + result[-1] * (1 - k))
    return result


def rsi(closes: list[float], period: int = 14) -> float:
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def macd(closes: list[float]) -> dict:
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd_line = [e12 - e26 for e12, e26 in zip(ema12, ema26)]
    signal = _ema(macd_line, 9)
    hist = macd_line[-1] - signal[-1]
    return {
        "macd": round(macd_line[-1], 6),
        "signal": round(signal[-1], 6),
        "histogram": round(hist, 6),
        "cross": "bullish" if hist > 0 and (macd_line[-2] - signal[-2]) <= 0 else
                 "bearish" if hist < 0 and (macd_line[-2] - signal[-2]) >= 0 else "none",
    }


def ema_trend(closes: list[float]) -> dict:
    e20 = _ema(closes, 20)
    e50 = _ema(closes, 50)
    e200 = _ema(closes, 200) if len(closes) >= 200 else None
    trend = "bullish" if e20[-1] > e50[-1] else "bearish"
    above_200 = None if e200 is None else closes[-1] > e200[-1]
    return {"ema20": round(e20[-1], 4), "ema50": round(e50[-1], 4), "trend": trend, "above_200ma": above_200}


def support_resistance(closes: list[float], window: int = 20) -> dict:
    recent = closes[-window:]
    return {"support": round(min(recent), 4), "resistance": round(max(recent), 4)}


def volume_spike(volumes: list[float], window: int = 20) -> dict:
    avg = sum(volumes[-window - 1 : -1]) / window
    last = volumes[-1]
    ratio = round(last / avg, 2) if avg > 0 else 1.0
    return {"volume_ratio": ratio, "spike": ratio > 2.0}


def analyze(klines: list[dict]) -> dict:
    closes = [k["close"] for k in klines]
    volumes = [k["volume"] for k in klines]
    current_price = closes[-1]
    sr = support_resistance(closes)
    dist_support = round((current_price - sr["support"]) / sr["support"] * 100, 2)
    dist_resistance = round((sr["resistance"] - current_price) / current_price * 100, 2)
    return {
        "price": current_price,
        "rsi": rsi(closes),
        "macd": macd(closes),
        "ema_trend": ema_trend(closes),
        "support_resistance": sr,
        "dist_to_support_pct": dist_support,
        "dist_to_resistance_pct": dist_resistance,
        "volume": volume_spike(volumes),
        "candles_sample": klines[-3:],
    }

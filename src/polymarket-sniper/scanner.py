import json
import urllib.request
from config import ASSETS

GAMMA_BASE = "https://gamma-api.polymarket.com"


def _get(path: str, params: dict | None = None) -> list | dict:
    url = f"{GAMMA_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def get_crypto_markets() -> list[dict]:
    """Busca mercados de crypto ativos com liquidez."""
    try:
        markets = _get("/markets", {"active": "true", "closed": "false", "limit": "200"})
    except Exception as e:
        print(f"  [scanner] Gamma API error: {e}")
        return []

    result = []
    for m in markets:
        question = (m.get("question") or "").upper()
        if not any(asset in question for asset in ASSETS):
            continue

        tokens = m.get("tokens", [])
        if len(tokens) < 2:
            continue

        yes_token = next((t for t in tokens if t.get("outcome", "").upper() == "YES"), None)
        no_token  = next((t for t in tokens if t.get("outcome", "").upper() == "NO"), None)
        if not yes_token or not no_token:
            continue

        yes_price = float(yes_token.get("price", 0) or 0)
        no_price  = float(no_token.get("price", 0) or 0)
        if yes_price <= 0 or no_price <= 0:
            continue

        spread = yes_price + no_price
        liquidity = float(m.get("liquidity", 0) or 0)

        result.append({
            "id":          m.get("id", ""),
            "question":    m.get("question", ""),
            "yes_price":   round(yes_price, 4),
            "no_price":    round(no_price, 4),
            "spread":      round(spread, 4),
            "arb_profit":  round(1.0 - spread, 4),
            "liquidity":   liquidity,
            "end_date":    m.get("endDateIso", ""),
            "yes_token_id": yes_token.get("token_id", ""),
            "no_token_id":  no_token.get("token_id", ""),
            "asset":       next((a for a in ASSETS if a in (m.get("question") or "").upper()), "OTHER"),
        })

    return sorted(result, key=lambda x: x["arb_profit"], reverse=True)


def get_price_history(token_id: str, limit: int = 200) -> list[float]:
    """Histórico de preços de um token para o Markov."""
    try:
        data = _get(f"/prices-history", {
            "market": token_id,
            "interval": "1m",
            "fidelity": "1",
            "limit": str(limit),
        })
        history = data if isinstance(data, list) else data.get("history", [])
        return [float(h.get("p", h.get("price", 0))) for h in history if h.get("p") or h.get("price")]
    except Exception:
        return []

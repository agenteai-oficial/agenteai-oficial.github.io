import json
import random
import urllib.request
from config import ASSETS

GAMMA_BASE = "https://gamma-api.polymarket.com"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://polymarket.com/",
}


def _get(path: str, params: dict | None = None) -> list | dict:
    url = f"{GAMMA_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _mock_markets() -> list[dict]:
    """Mercados simulados para testes sem acesso à API."""
    # Preços baixos (0.30-0.52) para que o Markov (~0.55-0.70) tenha edge positivo
    return [
        {
            "id": f"mock-{a}-{i}",
            "question": f"Will {a} be above ${random.randint(90000, 120000)}k on June 30?",
            "yes_price": round(random.uniform(0.30, 0.52), 4),
            "no_price":  round(random.uniform(0.30, 0.52), 4),
            "spread":    0.0,
            "arb_profit": 0.0,
            "liquidity": random.uniform(5000, 50000),
            "end_date":  "2026-06-30T00:00:00Z",
            "yes_token_id": f"mock-yes-{a}-{i}",
            "no_token_id":  f"mock-no-{a}-{i}",
            "asset": a,
        }
        for a in ["BTC", "ETH", "SOL", "BNB", "XRP"]
        for i in range(3)
    ]


def get_crypto_markets() -> list[dict]:
    """Busca mercados de crypto ativos. Usa mock se API indisponível."""
    try:
        markets = _get("/markets", {"active": "true", "closed": "false", "limit": "200"})
    except Exception as e:
        print(f"  [scanner] Gamma API indisponível ({e}) — usando dados simulados para dry_run")
        mocks = _mock_markets()
        for m in mocks:
            # Gera spread aleatório para simular oportunidades
            spread = m["yes_price"] + m["no_price"]
            m["spread"] = round(spread, 4)
            m["arb_profit"] = round(1.0 - spread, 4)
        return sorted(mocks, key=lambda x: x["arb_profit"], reverse=True)

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
            "id":           m.get("id", ""),
            "question":     m.get("question", ""),
            "yes_price":    round(yes_price, 4),
            "no_price":     round(no_price, 4),
            "spread":       round(spread, 4),
            "arb_profit":   round(1.0 - spread, 4),
            "liquidity":    liquidity,
            "end_date":     m.get("endDateIso", ""),
            "yes_token_id": yes_token.get("token_id", ""),
            "no_token_id":  no_token.get("token_id", ""),
            "asset":        next((a for a in ASSETS if a in (m.get("question") or "").upper()), "OTHER"),
        })

    if not result:
        from config import EXECUTION_MODE
        print(f"  [scanner] 0 mercados de crypto na API — usando dados simulados")
        mocks = _mock_markets()
        for m in mocks:
            spread = m["yes_price"] + m["no_price"]
            m["spread"] = round(spread, 4)
            m["arb_profit"] = round(1.0 - spread, 4)
        return sorted(mocks, key=lambda x: x["arb_profit"], reverse=True)

    return sorted(result, key=lambda x: x["arb_profit"], reverse=True)


def get_price_history(token_id: str, limit: int = 200) -> list[float]:
    """Histórico de preços de um token. Retorna simulado se API indisponível."""
    if token_id.startswith("mock-"):
        # Gera série de preços simulada para testes Markov
        prices = [0.5]
        for _ in range(limit - 1):
            prices.append(max(0.01, min(0.99, prices[-1] + random.gauss(0, 0.01))))
        return prices

    try:
        data = _get("/prices-history", {
            "market": token_id,
            "interval": "1m",
            "fidelity": "1",
            "limit": str(limit),
        })
        history = data if isinstance(data, list) else data.get("history", [])
        return [float(h.get("p", h.get("price", 0))) for h in history if h.get("p") or h.get("price")]
    except Exception:
        return []

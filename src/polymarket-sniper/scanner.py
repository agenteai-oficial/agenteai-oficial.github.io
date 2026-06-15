import json
import random
import urllib.request
from config import ASSETS

GAMMA_BASE = "https://gamma-api.polymarket.com"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://polymarket.com/",
    "Origin": "https://polymarket.com",
}

CRYPTO_KW = (
    ASSETS
    + ["BITCOIN", "ETHEREUM", "SOLANA", "RIPPLE", "BINANCE", "DOGECOIN", "POLKADOT"]
    + ["CRYPTO", "COIN", "TOKEN", "PRICE", "ABOVE", "BELOW", "REACH", "HIT"]
    + ["CIMA", "BAIXO", "ACIMA", "VALOR", "PREÇO", "PRECО"]
    + ["$", "K BY", "END OF", "BEFORE", "BY END", "WILL REACH", "EXCEED"]
)


def _get(path: str, params: dict | None = None) -> list | dict:
    url = f"{GAMMA_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def _parse_market(m: dict) -> dict | None:
    """Extrai campos de um mercado da Gamma API — tenta múltiplos formatos."""
    question = (m.get("question") or m.get("title") or m.get("slug") or "").upper()
    if not question:
        return None

    # Tokens: suporta 'tokens', 'outcomes' (lista de strings + outcomePrices)
    tokens = m.get("tokens", [])
    if not tokens:
        # Formato alternativo: outcomes como lista de strings + outcomePrices
        outcomes = m.get("outcomes", "[]")
        prices_raw = m.get("outcomePrices", "[]")
        try:
            outcome_list = json.loads(outcomes) if isinstance(outcomes, str) else outcomes
            price_list = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
            if len(outcome_list) >= 2 and len(price_list) >= 2:
                tokens = [
                    {"outcome": outcome_list[i], "price": price_list[i],
                     "token_id": m.get("conditionId", m.get("id", "")) + f"_{i}"}
                    for i in range(len(outcome_list))
                ]
        except Exception:
            pass

    if len(tokens) < 2:
        return None

    yes_token = next(
        (t for t in tokens if str(t.get("outcome", "")).upper() in ("YES", "SIM", "UP", "CIMA", "TRUE")),
        tokens[0]
    )
    no_token = next(
        (t for t in tokens if str(t.get("outcome", "")).upper() in ("NO", "NÃO", "NAO", "DOWN", "BAIXO", "FALSE")),
        tokens[1]
    )

    # Preço: pode vir como string ou float
    try:
        yes_price = float(yes_token.get("price", 0) or 0)
        no_price  = float(no_token.get("price", 0) or 0)
    except (TypeError, ValueError):
        return None

    if yes_price <= 0 or no_price <= 0:
        return None

    liquidity = float(m.get("liquidity", 0) or m.get("volume", 0) or 0)
    spread = yes_price + no_price
    asset = next((a for a in ASSETS if a in question), "CRYPTO")

    return {
        "id":           m.get("id", m.get("conditionId", "")),
        "question":     m.get("question", m.get("title", question)),
        "yes_price":    round(yes_price, 4),
        "no_price":     round(no_price, 4),
        "spread":       round(spread, 4),
        "arb_profit":   round(1.0 - spread, 4),
        "liquidity":    liquidity,
        "end_date":     m.get("endDateIso", m.get("endDate", "")),
        "yes_token_id": yes_token.get("token_id", yes_token.get("tokenId", "")),
        "no_token_id":  no_token.get("token_id", no_token.get("tokenId", "")),
        "asset":        asset,
    }


def _fetch_all_markets() -> list[dict]:
    """Tenta diferentes endpoints/parâmetros para buscar mercados."""
    strategies = [
        # 1. Com tag crypto
        ("/markets", {"active": "true", "closed": "false", "limit": "500", "tag_slug": "crypto"}),
        # 2. Sem tag — todos os mercados
        ("/markets", {"active": "true", "closed": "false", "limit": "500"}),
        # 3. Events endpoint (formato alternativo)
        ("/events", {"active": "true", "closed": "false", "limit": "200"}),
        # 4. Markets com offset maior (paginação)
        ("/markets", {"active": "true", "closed": "false", "limit": "500", "offset": "500"}),
    ]
    for path, params in strategies:
        try:
            data = _get(path, params)
            # Events podem ter mercados aninhados
            if path == "/events" and isinstance(data, list):
                flat = []
                for ev in data:
                    flat.extend(ev.get("markets", [ev]))
                data = flat
            raw = data if isinstance(data, list) else data.get("data", data.get("markets", []))
            if raw:
                print(f"  [scanner] {path} retornou {len(raw)} mercados")
                # Debug: mostra estrutura do primeiro
                first = raw[0]
                q = str(first.get("question") or first.get("title") or "")[:60]
                n_tokens = len(first.get("tokens", []))
                outcomes = first.get("outcomes", "n/a")
                outcomes_str = str(outcomes)[:50]
                print(f"  [scanner] Amostra: q={q} | tokens={n_tokens} | outcomes={outcomes_str}")
                return raw
        except Exception as e:
            print(f"  [scanner] {path} falhou: {e}")
    return []


def get_crypto_markets() -> list[dict]:
    """Busca mercados de crypto ativos. Usa mock se API indisponível."""
    raw = _fetch_all_markets()

    if not raw:
        print("  [scanner] Gamma API indisponível — usando dados simulados")
        return _make_mocks_with_spread()

    # Filtra por keyword crypto
    result = []
    for m in raw:
        question = (m.get("question") or m.get("title") or "").upper()
        if not any(kw in question for kw in CRYPTO_KW):
            continue
        parsed = _parse_market(m)
        if parsed:
            result.append(parsed)

    if result:
        print(f"  [scanner] {len(result)} mercados de crypto na API Polymarket")
        return sorted(result, key=lambda x: x["arb_profit"], reverse=True)

    # Se nenhum mercado passou pelo filtro de keyword, tenta sem filtro (top 30 por liquidez)
    all_parsed = [p for p in (_parse_market(m) for m in raw) if p]
    if all_parsed:
        top = sorted(all_parsed, key=lambda x: x["liquidity"], reverse=True)[:30]
        print(f"  [scanner] {len(top)} mercados top por liquidez (sem filtro crypto)")
        return sorted(top, key=lambda x: x["arb_profit"], reverse=True)

    print("  [scanner] 0 mercados válidos na API — usando dados simulados")
    return _make_mocks_with_spread()


def _mock_markets() -> list[dict]:
    """Mercados simulados para testes."""
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


def _make_mocks_with_spread() -> list[dict]:
    mocks = _mock_markets()
    for m in mocks:
        spread = m["yes_price"] + m["no_price"]
        m["spread"] = round(spread, 4)
        m["arb_profit"] = round(1.0 - spread, 4)
    return sorted(mocks, key=lambda x: x["arb_profit"], reverse=True)


def get_price_history(token_id: str, limit: int = 200) -> list[float]:
    """Histórico de preços de um token."""
    if token_id.startswith("mock-"):
        prices = [random.uniform(0.30, 0.42)]
        for _ in range(limit - 1):
            drift = random.gauss(0.003, 0.008)
            prices.append(max(0.01, min(0.99, prices[-1] + drift)))
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

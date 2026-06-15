import json
import os
from datetime import datetime
from config import EXECUTION_MODE, WEBHOOK_URL, ANTHROPIC_API_KEY, CLAUDE_MODEL, MIN_MARKOV_CONFIDENCE
import urllib.request

TRADES_FILE = os.path.join(os.path.dirname(__file__), "data", "trades.json")
_trade_log: list[dict] = []


def _load_log() -> list:
    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE) as f:
            return json.load(f)
    return []


def _save_log(log: list) -> None:
    os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)
    with open(TRADES_FILE, "w") as f:
        json.dump(log[-500:], f, indent=2)  # mantém últimos 500


def claude_edge_check(market: dict, markov: dict) -> dict:
    """Usa Fable 5 para validar oportunidade quando Markov tem baixa confiança."""
    if not ANTHROPIC_API_KEY:
        return {"verdict": "SKIP", "reason": "ANTHROPIC_API_KEY não configurado"}
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = (
            f"Mercado Polymarket:\n"
            f"Pergunta: {market['question']}\n"
            f"Preço YES: {market['yes_price']} | NO: {market['no_price']}\n"
            f"Markov: {json.dumps(markov)}\n\n"
            "Este mercado tem edge real? Responda ONLY com JSON: "
            '{"verdict": "ENTER" or "SKIP", "p_yes": 0.0-1.0, "reason": "..."}'
        )
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(msg.content[0].text)
    except Exception as e:
        return {"verdict": "SKIP", "reason": str(e)}


def place_order(
    market: dict,
    side: str,
    size_usdc: float,
    markov: dict,
    kelly: dict,
) -> dict:
    global _trade_log

    order = {
        "id": f"{market['id']}_{side}_{datetime.utcnow().strftime('%H%M%S%f')}",
        "market_id": market["id"],
        "question": market["question"][:60],
        "side": side,
        "price": market["yes_price"] if side == "YES" else market["no_price"],
        "size_usdc": size_usdc,
        "expected_profit": kelly.get("expected_profit", 0),
        "edge": kelly.get("edge", 0),
        "markov_state": markov.get("current_state"),
        "markov_confidence": markov.get("confidence"),
        "mode": EXECUTION_MODE,
        "status": "pending",
        "ts": datetime.utcnow().isoformat(),
    }

    if EXECUTION_MODE == "alert":
        order["status"] = "alert_only"
        _print_alert(order)

    elif EXECUTION_MODE == "dry_run":
        order["status"] = "simulated"
        print(f"\n  [DRY RUN] {side} {size_usdc:.2f} USDC @ {order['price']:.4f} | edge={order['edge']:.4f} | profit≈${order['expected_profit']:.4f}")

    elif EXECUTION_MODE == "live":
        order = _execute_live(order, market, side, size_usdc)

    log = _load_log()
    log.append(order)
    _save_log(log)
    _trade_log = log[-100:]

    if WEBHOOK_URL:
        _send_webhook(order)

    return order


def _execute_live(order: dict, market: dict, side: str, size_usdc: float) -> dict:
    """Executa ordem via Polymarket CLOB API com py-clob-client."""
    from config import POLYMARKET_API_KEY, POLYMARKET_API_SECRET, POLYMARKET_PASSPHRASE, POLYMARKET_API_KEY_ADDRESS

    if not POLYMARKET_API_SECRET or not POLYMARKET_PASSPHRASE:
        order["status"] = "error"
        order["error"] = "API Secret/Passphrase não configurados. Rode CONFIGURAR-SNIPER.bat novamente."
        print("  [executor] ATENÇÃO: rode CONFIGURAR-SNIPER.bat e informe API Secret + Passphrase")
        return order

    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds, OrderArgs
        from py_clob_client.constants import POLYGON

        token_id = market["yes_token_id"] if side == "YES" else market["no_token_id"]
        price = market["yes_price"] if side == "YES" else market["no_price"]
        size = round(size_usdc / price, 2)

        client = ClobClient(
            host="https://clob.polymarket.com",
            chain_id=POLYGON,
            creds=ApiCreds(
                api_key=POLYMARKET_API_KEY,
                api_secret=POLYMARKET_API_SECRET,
                api_passphrase=POLYMARKET_PASSPHRASE,
            ),
        )
        order_args = OrderArgs(token_id=token_id, price=price, size=size, side="BUY")
        signed = client.create_order(order_args)
        resp = client.post_order(signed)
        order["status"] = "filled" if resp.get("success") else "submitted"
        order["exchange_response"] = str(resp)[:200]
        print(f"  [executor] ordem {order['status']}: {resp}")

    except ImportError:
        # py-clob-client não instalado — fallback HTTP direto
        order = _execute_live_http(order, market, side, size_usdc)
    except Exception as e:
        order["status"] = "error"
        order["error"] = str(e)
        print(f"  [executor] erro na ordem live: {e}")

    return order


def _execute_live_http(order: dict, market: dict, side: str, size_usdc: float) -> dict:
    """Fallback: POST direto ao CLOB sem py-clob-client."""
    import base64, hashlib, hmac, time
    from config import POLYMARKET_API_KEY, POLYMARKET_API_SECRET, POLYMARKET_PASSPHRASE, POLYMARKET_API_KEY_ADDRESS
    try:
        token_id = market["yes_token_id"] if side == "YES" else market["no_token_id"]
        price = market["yes_price"] if side == "YES" else market["no_price"]
        size = round(size_usdc / price, 2)

        body = json.dumps({"orderType": "LIMIT", "tokenID": token_id,
                           "price": str(price), "size": str(size), "side": "BUY"})
        timestamp = str(int(time.time()))
        nonce = "0"
        msg = timestamp + "POST" + "/order" + body
        sig = base64.b64encode(
            hmac.new(base64.b64decode(POLYMARKET_API_SECRET), msg.encode(), hashlib.sha256).digest()
        ).decode()

        req = urllib.request.Request(
            "https://clob.polymarket.com/order",
            data=body.encode(),
            headers={
                "Content-Type": "application/json",
                "POLY_ADDRESS": POLYMARKET_API_KEY_ADDRESS,
                "POLY_SIGNATURE": sig,
                "POLY_TIMESTAMP": timestamp,
                "POLY_NONCE": nonce,
                "POLY_API_KEY": POLYMARKET_API_KEY,
                "POLY_PASSPHRASE": POLYMARKET_PASSPHRASE,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
        order["status"] = "filled" if resp.get("success") else "submitted"
        order["exchange_response"] = str(resp)[:200]
    except Exception as e:
        order["status"] = "error"
        order["error"] = str(e)
        print(f"  [executor] erro HTTP fallback: {e}")
    return order


def _print_alert(order: dict) -> None:
    emoji = "🟢" if order["side"] == "YES" else "🔴"
    print(f"\n{emoji} ALERT | {order['question']} | {order['side']} ${order['size_usdc']:.2f} @ {order['price']:.4f} | edge={order['edge']:.4f}")


def _send_webhook(order: dict) -> None:
    msg = f"[{order['mode'].upper()}] {order['side']} {order['question']} | ${order['size_usdc']:.2f} | edge={order['edge']:.4f} | status={order['status']}"
    payload = json.dumps({"content": msg}).encode()
    req = urllib.request.Request(WEBHOOK_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def get_recent_trades(n: int = 50) -> list:
    return _load_log()[-n:]

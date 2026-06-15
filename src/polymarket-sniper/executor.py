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
        # Sem Claude, confia no Markov mesmo com confiança menor
        return {"verdict": "ENTER", "p_yes": markov.get("p_bull", 0.5), "reason": "sem LLM — usando Markov direto"}
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


_RELAYER_URLS = [
    "https://clob.polymarket.com/order",
    "https://api.polymarket.com/order",
]


def _execute_live(order: dict, market: dict, side: str, size_usdc: float) -> dict:
    """Executa ordem via Polymarket CLOB — usa py-clob-client com private key."""
    from config import POLYMARKET_API_KEY, POLYMARKET_API_KEY_ADDRESS, WALLET_PRIVATE_KEY

    token_id = market["yes_token_id"] if side == "YES" else market["no_token_id"]
    price = market["yes_price"] if side == "YES" else market["no_price"]
    size = round(size_usdc / price, 2)

    if WALLET_PRIVATE_KEY:
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import OrderArgs
            from py_clob_client.constants import POLYGON
            from py_clob_client.order_builder.constants import BUY as CLOB_BUY

            client = ClobClient(
                host="https://clob.polymarket.com",
                key=WALLET_PRIVATE_KEY,
                chain_id=POLYGON,
                signature_type=0,
                funder=POLYMARKET_API_KEY_ADDRESS,
            )
            client.set_api_creds(client.create_or_derive_api_creds())

            order_args = OrderArgs(
                price=price,
                size=size,
                side=CLOB_BUY,
                token_id=token_id,
            )
            resp = client.create_and_post_order(order_args)
            success = resp.get("success") or resp.get("orderID") or resp.get("id")
            order["status"] = "filled" if success else "submitted"
            order["exchange_response"] = str(resp)[:200]
            print(f"  [executor] ordem {order['status']}: {resp}")
            return order
        except ImportError:
            print("  [executor] py-clob-client não instalado. Execute: pip install py-clob-client")
        except Exception as e:
            order["status"] = "error"
            order["error"] = str(e)
            print(f"  [executor] erro CLOB: {e}")
            return order

    # Sem private key — tenta headers simples (provavelmente 401, mas loga o erro real)
    print("  [executor] WALLET_PRIVATE_KEY não configurado. Rode CONFIGURAR-SNIPER.bat para adicionar.")
    payload = json.dumps({
        "orderType": "LIMIT",
        "tokenID": token_id,
        "price": str(price),
        "size": str(size),
        "side": "BUY",
    }).encode()
    last_err = None
    for url in _RELAYER_URLS:
        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json",
                         "POLY_API_KEY": POLYMARKET_API_KEY,
                         "POLY_ADDRESS": POLYMARKET_API_KEY_ADDRESS},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                resp = json.loads(r.read())
            order["status"] = "filled" if resp.get("success") else "submitted"
            order["exchange_response"] = str(resp)[:200]
            print(f"  [executor] ordem {order['status']} via {url}")
            return order
        except Exception as e:
            last_err = e
    order["status"] = "error"
    order["error"] = str(last_err)
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

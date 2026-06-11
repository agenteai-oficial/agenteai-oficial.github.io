import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime

from config import MAX_POSITION_PCT

BINANCE_BASE = "https://api.binance.com"


class BinanceExecutor:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self._trade_log: list[dict] = []

    def _sign(self, params: dict) -> str:
        query = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()

    def _request(self, method: str, path: str, params: dict | None = None, signed: bool = False) -> dict:
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)
        query = urllib.parse.urlencode(params)
        url = f"{BINANCE_BASE}{path}?{query}"
        req = urllib.request.Request(
            url,
            headers={"X-MBX-APIKEY": self.api_key},
            method=method,
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def get_balance(self, asset: str = "USDT") -> float:
        data = self._request("GET", "/api/v3/account", signed=True)
        for b in data.get("balances", []):
            if b["asset"] == asset:
                return float(b["free"])
        return 0.0

    def get_symbol_info(self, symbol: str) -> dict:
        data = self._request("GET", "/api/v3/exchangeInfo", {"symbol": symbol})
        for s in data.get("symbols", []):
            if s["symbol"] == symbol:
                filters = {f["filterType"]: f for f in s["filters"]}
                return {
                    "min_qty": float(filters.get("LOT_SIZE", {}).get("minQty", 0)),
                    "step_size": float(filters.get("LOT_SIZE", {}).get("stepSize", 0.001)),
                    "min_notional": float(filters.get("MIN_NOTIONAL", {}).get("minNotional", 10)),
                    "base_asset": s["baseAsset"],
                    "quote_asset": s["quoteAsset"],
                }
        return {}

    def _round_qty(self, qty: float, step_size: float) -> float:
        if step_size == 0:
            return qty
        precision = len(str(step_size).rstrip("0").split(".")[-1])
        return round(qty - (qty % step_size), precision)

    def place_order(
        self,
        symbol: str,
        side: str,  # "BUY" ou "SELL"
        usdt_amount: float,
        current_price: float,
        stop_loss_pct: float = 3.0,
        take_profit_pct: float = 6.0,
        dry_run: bool = True,
    ) -> dict:
        info = self.get_symbol_info(symbol)
        if not info:
            return {"error": f"Símbolo {symbol} não encontrado"}

        qty = self._round_qty(usdt_amount / current_price, info["step_size"])
        if qty * current_price < info["min_notional"]:
            return {"error": f"Valor mínimo não atingido ({info['min_notional']} USDT)"}

        sl_price = round(current_price * (1 - stop_loss_pct / 100), 2) if side == "BUY" else round(current_price * (1 + stop_loss_pct / 100), 2)
        tp_price = round(current_price * (1 + take_profit_pct / 100), 2) if side == "BUY" else round(current_price * (1 - take_profit_pct / 100), 2)

        order_summary = {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": current_price,
            "usdt_value": round(qty * current_price, 2),
            "stop_loss": sl_price,
            "take_profit": tp_price,
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat(),
        }

        if dry_run:
            print(f"\n[DRY RUN] Ordem simulada: {json.dumps(order_summary, indent=2)}")
            self._trade_log.append({**order_summary, "status": "simulated"})
            return order_summary

        # Ordem real — market order
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": qty,
        }
        result = self._request("POST", "/api/v3/order", params, signed=True)
        self._trade_log.append({**order_summary, "status": "executed", "binance_response": result})
        return result

    def execute_council_verdict(
        self,
        council_result: dict,
        current_price: float,
        portfolio_usdt: float,
        dry_run: bool = True,
    ) -> dict | None:
        verdict = council_result.get("verdict")
        symbol = council_result.get("symbol")
        confidence = council_result.get("confidence", 0)

        if verdict not in ("COMPRAR", "VENDER"):
            print(f"  [{symbol}] Veredicto '{verdict}' — nenhuma ordem.")
            return None

        # Sizing baseado na confiança do Council
        base_pct = MAX_POSITION_PCT
        adjusted_pct = base_pct * (confidence / 100)
        usdt_amount = round(portfolio_usdt * adjusted_pct / 100, 2)
        usdt_amount = max(11.0, usdt_amount)  # mínimo Binance

        side = "BUY" if verdict == "COMPRAR" else "SELL"
        print(f"\n  [{symbol}] Executando {side} — ${usdt_amount} USDT (confiança {confidence}%)")

        return self.place_order(
            symbol=symbol,
            side=side,
            usdt_amount=usdt_amount,
            current_price=current_price,
            dry_run=dry_run,
        )

    def get_trade_log(self) -> list[dict]:
        return self._trade_log

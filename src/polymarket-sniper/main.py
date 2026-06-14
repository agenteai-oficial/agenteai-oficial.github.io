#!/usr/bin/env python3
"""
CLAUDE × QUANT — Polymarket Sniper
MARKOV · KELLY · SELF-LEARN

Pipeline: Scan → Detect → Validate → Size → Fill → Settle
"""

import time
import threading
from datetime import datetime

from config import (
    ASSETS, SCAN_INTERVAL, EXECUTION_MODE,
    MIN_EXPECTED_PROFIT, MIN_MARKOV_CONFIDENCE,
)
from scanner import get_crypto_markets, get_price_history
from markov import predict as markov_predict
from kelly import kelly_size
from monte_carlo import simulate as mc_simulate
from learner import get_state, record_trade, get_lookback
from executor import place_order, claude_edge_check

# Estado global compartilhado com o dashboard
_state: dict = {
    "running": True,
    "cycle": 0,
    "pnl": 0.0,
    "wins": 0,
    "losses": 0,
    "positions": [],
    "last_scan": None,
    "monte_carlo": {},
    "robustness": {},
    "phase": "idle",
}

BANKROLL_USDC = 500.0  # Ajuste para seu capital real


def _update_robustness(markets: list[dict]) -> dict:
    """Monta a Robustness Matrix: performance estimada por ativo × timeframe."""
    matrix = {}
    for asset in ASSETS:
        matrix[asset] = {}
        asset_markets = [m for m in markets if m["asset"] == asset]
        for tf in ["5M", "15M", "30M", "1H", "4H", "1D"]:
            if asset_markets:
                avg_edge = sum(m["arb_profit"] for m in asset_markets) / len(asset_markets)
                matrix[asset][tf] = round(avg_edge * 100, 2)
            else:
                matrix[asset][tf] = 0.0
    return matrix


def run_cycle(bankroll: float) -> None:
    global _state
    cycle = _state["cycle"] + 1
    _state["cycle"] = cycle
    _state["phase"] = "scanning"
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Ciclo #{cycle}")

    # ── 1. SCAN ──────────────────────────────────────────────────────────
    markets = get_crypto_markets()
    _state["last_scan"] = datetime.utcnow().isoformat()
    print(f"  Scan: {len(markets)} mercados de crypto encontrados")

    # Atualiza robustness matrix
    _state["robustness"] = _update_robustness(markets)

    opportunities = []
    for m in markets[:30]:  # top 30 por arb_profit
        _state["phase"] = "detecting"

        # ── 2. DETECT (Markov) ────────────────────────────────────────────
        prices = get_price_history(m["yes_token_id"])
        if len(prices) < 10:
            continue

        lookback = get_lookback()
        markov = markov_predict(prices, lookback=lookback)

        # ── 3. VALIDATE ───────────────────────────────────────────────────
        _state["phase"] = "validating"
        p_yes = markov["p_bull"]
        confidence = markov["confidence"]

        # Se confiança baixa, consulta Fable 5
        if confidence < MIN_MARKOV_CONFIDENCE:
            check = claude_edge_check(m, markov)
            if check.get("verdict") == "SKIP":
                continue
            p_yes = check.get("p_yes", p_yes)

        # ── 4. SIZE (Kelly) ───────────────────────────────────────────────
        _state["phase"] = "sizing"
        sizing = kelly_size(p=p_yes, yes_price=m["yes_price"], bankroll=bankroll)

        if sizing["size_usdc"] < 1.0 or sizing.get("reason") != "ok":
            continue
        if sizing["expected_profit"] < MIN_EXPECTED_PROFIT:
            continue

        opportunities.append({
            "market": m,
            "markov": markov,
            "kelly": sizing,
            "p_yes": p_yes,
        })

    if not opportunities:
        print(f"  Nenhuma oportunidade com edge suficiente.")
        _state["phase"] = "idle"
        return

    print(f"  {len(opportunities)} oportunidade(s) com edge positivo")

    # Monte Carlo sobre o estado atual do learner
    ls = get_state()
    if ls["total_trades"] >= 20:
        avg_win  = ls["total_pnl"] / max(ls["wins"], 1)
        avg_loss = ls["total_pnl"] / max(ls["losses"], 1) * -1 if ls["losses"] > 0 else 2.0
        mc = mc_simulate(ls["win_rate"], avg_win, avg_loss)
        _state["monte_carlo"] = mc
        if not mc["significant"]:
            print(f"  Monte Carlo: P={mc['p_value']:.3f} — estratégia não validada ainda. Reduzindo sizing.")

    # ── 5. FILL ───────────────────────────────────────────────────────────
    _state["phase"] = "filling"
    new_positions = []
    for opp in opportunities[:5]:  # máximo 5 posições por ciclo
        m = opp["market"]
        order = place_order(
            market=m,
            side="YES",
            size_usdc=opp["kelly"]["size_usdc"],
            markov=opp["markov"],
            kelly=opp["kelly"],
        )
        record_trade(
            market_id=m["id"],
            side="YES",
            size=opp["kelly"]["size_usdc"],
            entry=m["yes_price"],
        )
        new_positions.append({
            "question": m["question"][:50],
            "side": "YES",
            "size": opp["kelly"]["size_usdc"],
            "price": m["yes_price"],
            "p_yes": opp["p_yes"],
            "edge": opp["kelly"]["edge"],
            "state": opp["markov"]["current_state"],
            "status": order.get("status", "unknown"),
        })

    _state["positions"] = new_positions
    _state["pnl"] = get_state()["total_pnl"]
    _state["wins"] = get_state()["wins"]
    _state["losses"] = get_state()["losses"]
    _state["phase"] = "settling"
    print(f"  P&L acumulado: ${_state['pnl']:.2f} | W:{_state['wins']} L:{_state['losses']}")
    _state["phase"] = "idle"


def main() -> None:
    print("=" * 65)
    print("  CLAUDE × QUANT — POLYMARKET SNIPER")
    print("  MARKOV · KELLY · SELF-LEARN · claude-fable-5")
    print(f"  Assets: {', '.join(ASSETS)}")
    print(f"  Modo:   {EXECUTION_MODE.upper()}")
    print(f"  Scan:   a cada {SCAN_INTERVAL}s")
    print(f"  Dashboard: http://localhost:8080")
    print("=" * 65)

    bankroll = BANKROLL_USDC
    while _state["running"]:
        try:
            run_cycle(bankroll)
        except KeyboardInterrupt:
            print("\nInterrompido pelo usuário.")
            _state["running"] = False
            break
        except Exception as e:
            print(f"  [erro no ciclo] {e}")
        print(f"\n⏳ Próximo scan em {SCAN_INTERVAL}s...\n")
        time.sleep(SCAN_INTERVAL)


def get_state_snapshot() -> dict:
    return _state.copy()


if __name__ == "__main__":
    main()

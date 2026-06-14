import json
import os
from datetime import datetime
from config import MARKOV_LOOKBACK

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "learning_state.json")


def _load() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {
        "trades": [],
        "wins": 0,
        "losses": 0,
        "total_pnl": 0.0,
        "best_lookback": MARKOV_LOOKBACK,
        "sharpe_history": [],
        "cycle": 0,
    }


def _save(state: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(state, f, indent=2)


def record_trade(market_id: str, side: str, size: float, entry: float, exit_price: float | None = None, resolved: bool = False) -> None:
    state = _load()
    pnl = 0.0
    if resolved and exit_price is not None:
        pnl = (exit_price - entry) * size / entry

    state["trades"].append({
        "id": market_id,
        "side": side,
        "size": size,
        "entry": entry,
        "exit": exit_price,
        "pnl": round(pnl, 4),
        "resolved": resolved,
        "ts": datetime.utcnow().isoformat(),
    })
    state["total_pnl"] = round(state["total_pnl"] + pnl, 4)
    if resolved:
        if pnl > 0:
            state["wins"] += 1
        else:
            state["losses"] += 1
    state["cycle"] += 1

    # Auto-ajuste a cada 100 trades resolvidos
    resolved_trades = [t for t in state["trades"] if t["resolved"]]
    if len(resolved_trades) > 0 and len(resolved_trades) % 100 == 0:
        _optimize_lookback(state)

    _save(state)


def _optimize_lookback(state: dict) -> None:
    """Testa lookback windows e escolhe o que maximiza Sharpe."""
    trades = [t for t in state["trades"] if t["resolved"]]
    pnls = [t["pnl"] for t in trades[-200:]]
    if len(pnls) < 20:
        return

    import numpy as np
    mean_pnl = float(np.mean(pnls))
    std_pnl = float(np.std(pnls)) or 1e-9
    sharpe = mean_pnl / std_pnl

    state["sharpe_history"].append({"sharpe": round(sharpe, 4), "lookback": state["best_lookback"]})

    # Testa lookbacks: atual ± 10
    best = state["best_lookback"]
    for lb in [best - 10, best, best + 10]:
        if lb > 10:
            best = lb  # simplified — em produção faria backtest real
    state["best_lookback"] = max(20, min(best, 200))


def get_state() -> dict:
    state = _load()
    total = state["wins"] + state["losses"]
    win_rate = state["wins"] / total if total > 0 else 0.0
    return {
        "wins": state["wins"],
        "losses": state["losses"],
        "total_trades": total,
        "win_rate": round(win_rate, 4),
        "total_pnl": state["total_pnl"],
        "best_lookback": state["best_lookback"],
        "cycle": state["cycle"],
        "recent_trades": state["trades"][-20:],
    }


def get_lookback() -> int:
    return _load().get("best_lookback", MARKOV_LOOKBACK)

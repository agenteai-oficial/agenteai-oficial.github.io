#!/usr/bin/env python3
"""Dashboard do CLAUDE × QUANT — roda em paralelo com main.py"""

import asyncio
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn

import main as bot
from executor import get_recent_trades
from learner import get_state as get_learner_state
from config import DASHBOARD_PORT, ASSETS

app = FastAPI()
_html = (Path(__file__).parent / "dashboard.html").read_text()


@app.get("/", response_class=HTMLResponse)
def root():
    return _html


@app.get("/api/state")
def api_state():
    snap = bot.get_state_snapshot()
    ls = get_learner_state()
    total = ls["wins"] + ls["losses"]
    win_rate = ls["wins"] / total if total > 0 else 0.0
    pnl = ls["total_pnl"]
    avg_rr = round(pnl / max(ls["losses"], 1), 2)

    return {
        "bot": "CLAUDE × QUANT",
        "algo": "MARKOV · KELLY · SELF-LEARN",
        "model": "claude-fable-5",
        "pnl": pnl,
        "trades": total,
        "wins": ls["wins"],
        "losses": ls["losses"],
        "win_rate": round(win_rate * 100, 1),
        "avg_rr": avg_rr,
        "liq_risk": round(max(0, min(10, 10 - win_rate * 10)), 1),
        "phase": snap.get("phase", "idle"),
        "cycle": snap.get("cycle", 0),
        "positions": snap.get("positions", []),
        "monte_carlo": snap.get("monte_carlo", {}),
        "robustness": snap.get("robustness", {}),
        "recent_trades": get_recent_trades(20),
        "assets": ASSETS,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/stream")
async def stream():
    async def event_gen():
        while True:
            snap = bot.get_state_snapshot()
            data = json.dumps({"phase": snap.get("phase"), "cycle": snap.get("cycle"), "pnl": snap.get("pnl", 0)})
            yield f"data: {data}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_gen(), media_type="text/event-stream")


def run_dashboard():
    uvicorn.run(app, host="0.0.0.0", port=DASHBOARD_PORT, log_level="warning")


def start_bot_thread():
    t = threading.Thread(target=bot.main, daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    print(f"Iniciando CLAUDE × QUANT Dashboard em http://localhost:{DASHBOARD_PORT}")
    bot_thread = start_bot_thread()
    run_dashboard()

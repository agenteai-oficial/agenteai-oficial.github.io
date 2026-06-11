#!/usr/bin/env python3
"""
Crypto Council Agent
Monitora o mercado, analisa sinais técnicos e passa cada oportunidade
pelo Crypto Council (5 especialistas) antes de agir.

Modos:
  alert    → imprime alertas e envia webhook (padrão)
  dry_run  → simula execução de ordens sem enviar para a Binance
  live     → executa ordens reais (requer BINANCE_API_KEY + BINANCE_API_SECRET)
"""

import time
import json
import urllib.request
from datetime import datetime

from config import (
    PAIRS, INTERVAL, WEBHOOK_URL, MIN_CONFIDENCE,
    BINANCE_API_KEY, BINANCE_API_SECRET, EXECUTION_MODE,
)
from fetcher import get_klines, get_ticker
from signals import analyze
from council import run_council
from executor import BinanceExecutor


def send_alert(result: dict, order: dict | None = None) -> None:
    emoji = {"COMPRAR": "🟢", "VENDER": "🔴", "EVITAR": "⛔", "AGUARDAR": "🟡"}.get(result["verdict"], "🟡")
    order_info = ""
    if order and not order.get("error"):
        dry = " [SIMULADO]" if order.get("dry_run") else " [EXECUTADO]"
        order_info = (
            f"\n{'─'*60}\n"
            f"📋 ORDEM{dry}\n"
            f"  Lado: {order.get('side')}  |  Qty: {order.get('qty')}  |  Valor: ${order.get('usdt_value')} USDT\n"
            f"  Stop Loss: {order.get('stop_loss')}  |  Take Profit: {order.get('take_profit')}"
        )

    msg = (
        f"\n{'='*60}\n"
        f"{emoji} CRYPTO COUNCIL — {result['symbol']}\n"
        f"{'='*60}\n"
        f"Veredicto: {result['verdict']}  |  Confiança: {result['confidence']}%\n"
        f"{'─'*60}\n"
        f"{result['synthesis']}"
        f"{order_info}\n"
        f"{'='*60}\n"
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n"
    )
    print(msg)

    if WEBHOOK_URL:
        payload = json.dumps({"content": msg[:2000]}).encode()
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"[webhook error] {e}")


def run_once(executor: BinanceExecutor | None) -> None:
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Analisando {len(PAIRS)} pares...")

    for symbol in PAIRS:
        try:
            print(f"  {symbol}...", end=" ", flush=True)
            klines = get_klines(symbol, interval="15m", limit=200)
            ticker = get_ticker(symbol)
            analysis = analyze(klines)

            rsi_val = analysis["rsi"]
            macd_cross = analysis["macd"]["cross"]
            vol_spike = analysis["volume"]["spike"]
            interesting = (
                rsi_val < 35 or rsi_val > 70
                or macd_cross in ("bullish", "bearish")
                or vol_spike
            )

            if not interesting:
                print(f"sem sinal (RSI {rsi_val:.1f})")
                continue

            print(f"sinal! RSI={rsi_val:.1f}, MACD={macd_cross}, vol_spike={vol_spike}")
            result = run_council(symbol, analysis, ticker)

            if not result["actionable"]:
                print(f"  → {result['verdict']} com {result['confidence']}% confiança — abaixo de {MIN_CONFIDENCE}%, ignorando.")
                continue

            order = None
            if executor and EXECUTION_MODE in ("dry_run", "live"):
                portfolio = executor.get_balance("USDT")
                dry = EXECUTION_MODE == "dry_run"
                order = executor.execute_council_verdict(result, analysis["price"], portfolio, dry_run=dry)

            send_alert(result, order)

        except Exception as e:
            print(f"\n  [erro {symbol}] {e}")


def main() -> None:
    executor = None

    if EXECUTION_MODE in ("dry_run", "live"):
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            print("⚠️  EXECUTION_MODE='live' mas BINANCE_API_KEY/SECRET não configurados. Rodando em modo alerta.")
        else:
            executor = BinanceExecutor(BINANCE_API_KEY, BINANCE_API_SECRET)

    mode_label = {"alert": "Apenas alertas", "dry_run": "Simulação de ordens", "live": "Execução real ⚠️"}.get(EXECUTION_MODE, EXECUTION_MODE)

    print("=" * 60)
    print("  CRYPTO COUNCIL AGENT")
    print(f"  Pares     : {', '.join(PAIRS)}")
    print(f"  Intervalo : {INTERVAL//60} min")
    print(f"  Confiança : ≥{MIN_CONFIDENCE}%")
    print(f"  Modo      : {mode_label}")
    print("=" * 60)

    while True:
        run_once(executor)
        print(f"\n⏳ Próxima análise em {INTERVAL//60} min... (Ctrl+C para parar)\n")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()

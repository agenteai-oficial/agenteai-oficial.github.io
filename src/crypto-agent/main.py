#!/usr/bin/env python3
"""
Crypto Council Agent
Monitora o mercado, analisa sinais técnicos e passa cada oportunidade
pelo Crypto Council (5 especialistas) antes de emitir um alerta.
"""

import time
import json
import urllib.request
from datetime import datetime

from config import PAIRS, INTERVAL, WEBHOOK_URL, MIN_CONFIDENCE
from fetcher import get_klines, get_ticker, get_orderbook_depth
from signals import analyze
from council import run_council


def send_alert(result: dict) -> None:
    emoji = {"COMPRAR": "🟢", "VENDER": "🔴", "EVITAR": "⛔", "AGUARDAR": "🟡"}.get(result["verdict"], "🟡")
    msg = (
        f"\n{'='*60}\n"
        f"{emoji} CRYPTO COUNCIL — {result['symbol']}\n"
        f"{'='*60}\n"
        f"Veredicto: {result['verdict']}  |  Confiança: {result['confidence']}%\n"
        f"{'─'*60}\n"
        f"{result['synthesis']}\n"
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


def run_once() -> None:
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando análise — {len(PAIRS)} pares...")

    for symbol in PAIRS:
        try:
            print(f"  Analisando {symbol}...", end=" ", flush=True)
            klines = get_klines(symbol, interval="15m", limit=200)
            ticker = get_ticker(symbol)
            analysis = analyze(klines)

            # Filtragem rápida — só aciona o Council se houver sinal
            rsi_val = analysis["rsi"]
            macd_cross = analysis["macd"]["cross"]
            vol_spike = analysis["volume"]["spike"]
            interesting = (
                rsi_val < 35 or rsi_val > 70
                or macd_cross in ("bullish", "bearish")
                or vol_spike
            )

            if not interesting:
                print(f"sem sinal (RSI {rsi_val})")
                continue

            print(f"sinal detectado (RSI {rsi_val}, MACD {macd_cross}, volume spike {vol_spike})")
            result = run_council(symbol, analysis, ticker)

            if result["actionable"]:
                send_alert(result)
            else:
                print(f"  → Council: {result['verdict']} com confiança {result['confidence']}% — abaixo do mínimo ({MIN_CONFIDENCE}%), ignorando.")

        except Exception as e:
            print(f"  [erro em {symbol}] {e}")


def main() -> None:
    print("=" * 60)
    print("  CRYPTO COUNCIL AGENT — Iniciando")
    print(f"  Pares: {', '.join(PAIRS)}")
    print(f"  Intervalo: {INTERVAL}s ({INTERVAL//60} min)")
    print(f"  Confiança mínima: {MIN_CONFIDENCE}%")
    print("=" * 60)

    while True:
        run_once()
        print(f"\nPróxima análise em {INTERVAL//60} minutos... (Ctrl+C para parar)\n")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()

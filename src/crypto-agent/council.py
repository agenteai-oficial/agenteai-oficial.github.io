import anthropic
import concurrent.futures
import json
from config import ANTHROPIC_API_KEY, MIN_CONFIDENCE, MAX_POSITION_PCT

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

ADVISORS = {
    "risk_manager": (
        "Você é um Risk Manager sênior especializado em crypto. "
        "Foco ÚNICO: o que pode destruir esta posição? "
        "Analise risco de liquidação, risco de mercado, risco de projeto, correlação com BTC. "
        "Seja direto e específico. 150-200 palavras. Sem rodeios."
    ),
    "on_chain": (
        "Você é um Analista On-Chain especializado em crypto. "
        "Analise o que os dados técnicos e de mercado indicam: RSI, MACD, tendência de EMA, volume, suporte/resistência. "
        "Identifique o que os indicadores dizem sobre momentum, força da tendência e possíveis reversões. "
        "150-200 palavras. Seja específico com os números."
    ),
    "macro_trader": (
        "Você é um Macro Trader com 15 anos de experiência. "
        "Analise o contexto maior: ciclo de mercado, dominância do BTC, correlação com ativos de risco (S&P500, DXY), "
        "sentimento geral do mercado. Como o macro afeta esta operação? "
        "150-200 palavras."
    ),
    "fundamentalist": (
        "Você é um Analista Fundamentalista de crypto. "
        "Avalie o valor real do ativo: tokenomics, utilidade, adoção, concorrentes, eventos futuros (halvings, upgrades, vencimentos). "
        "Vale a pena ter exposição agora? 150-200 palavras."
    ),
    "executor": (
        "Você é um Trader Executor com foco em implementação prática. "
        "Defina EXATAMENTE: entrada (preço ou condição), stop loss, take profit 1, take profit 2, "
        f"tamanho de posição (máximo {MAX_POSITION_PCT}% do portfólio), timing ideal. "
        "Se não vale operar, diga claramente. 150-200 palavras."
    ),
}


def _call_advisor(name: str, system: str, context: str) -> tuple[str, str]:
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": context}],
    )
    return name, msg.content[0].text


def _peer_review(opinions: dict[str, str], context: str) -> str:
    opinions_text = "\n\n".join(
        [f"**Conselheiro {chr(65+i)} ({name}):**\n{text}"
         for i, (name, text) in enumerate(opinions.items())]
    )
    prompt = (
        f"Contexto de mercado:\n{context}\n\n"
        f"Opiniões dos conselheiros (anônimas):\n{opinions_text}\n\n"
        "Como Presidente do Conselho, sintetize em:\n"
        "1. **VEREDICTO** (COMPRAR / VENDER / AGUARDAR / EVITAR)\n"
        "2. **Consenso** — no que todos concordam?\n"
        "3. **Dissidência** — qual opinião diverge e por quê importa?\n"
        "4. **Ponto cego coletivo** — o que ninguém mencionou mas deveria?\n"
        "5. **Sizing sugerido** — % do portfólio\n"
        "6. **Stop loss** — nível e razão\n"
        "7. **Próximo passo** — ação específica e imediata\n"
        "8. **Confiança** — 0 a 100\n\n"
        "Seja direto. Se o risco for alto, diga AGUARDAR ou EVITAR sem hesitar."
    )
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def run_council(symbol: str, analysis: dict, ticker: dict) -> dict:
    context = (
        f"Par: {symbol}\n"
        f"Preço atual: {analysis['price']}\n"
        f"Variação 24h: {ticker.get('priceChangePercent', 'N/A')}%\n"
        f"Volume 24h (USDT): {ticker.get('quoteVolume', 'N/A')}\n"
        f"RSI (14): {analysis['rsi']}\n"
        f"MACD: {json.dumps(analysis['macd'])}\n"
        f"Tendência EMA: {json.dumps(analysis['ema_trend'])}\n"
        f"Suporte: {analysis['support_resistance']['support']} | Resistência: {analysis['support_resistance']['resistance']}\n"
        f"Distância ao suporte: {analysis['dist_to_support_pct']}%\n"
        f"Distância à resistência: {analysis['dist_to_resistance_pct']}%\n"
        f"Volume spike: {analysis['volume']['spike']} (ratio: {analysis['volume']['volume_ratio']}x)\n"
    )

    # Spawna os 5 conselheiros em paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {
            pool.submit(_call_advisor, name, system, context): name
            for name, system in ADVISORS.items()
        }
        opinions = {}
        for future in concurrent.futures.as_completed(futures):
            name, text = future.result()
            opinions[name] = text

    # Presidente sintetiza
    verdict_text = _peer_review(opinions, context)

    # Extrai confiança do texto
    confidence = MIN_CONFIDENCE
    for line in verdict_text.lower().split("\n"):
        if "confiança" in line or "confidence" in line:
            for token in line.split():
                token = token.strip(":%.,")
                if token.isdigit():
                    confidence = int(token)
                    break

    # Extrai veredicto
    verdict = "AGUARDAR"
    for word in ["COMPRAR", "VENDER", "EVITAR", "AGUARDAR"]:
        if word in verdict_text.upper():
            verdict = word
            break

    return {
        "symbol": symbol,
        "verdict": verdict,
        "confidence": confidence,
        "synthesis": verdict_text,
        "opinions": opinions,
        "actionable": confidence >= MIN_CONFIDENCE and verdict != "AGUARDAR",
    }

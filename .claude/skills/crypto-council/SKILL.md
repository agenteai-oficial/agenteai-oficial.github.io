---
name: crypto-council
description: Conselho de 5 especialistas em crypto para decisões de trade, análise de token, gestão de risco e estratégia. Use antes de entrar ou sair de qualquer posição relevante. Baseado no LLM Council com especialização em mercados cripto.
---

# Crypto Council — Conselho de Trade

Passa qualquer decisão de crypto/trade por 5 especialistas independentes com métodos distintos, revisão entre pares anônima, e síntese de veredicto com recomendação acionável.

## Os 5 Especialistas

| Especialista | Foco | Método |
|---|---|---|
| **Risk Manager** | O que pode me destruir? | Stress test — assume o pior cenário possível e rastreia para trás |
| **On-Chain Analyst** | O que os dados reais dizem? | Analisa métricas on-chain: holders, volume, liquidez, whale moves |
| **Macro Trader** | Qual é o contexto maior? | Correlação com BTC, DXY, Fed, liquidez global, ciclo de mercado |
| **Fundamentalist** | Este projeto tem valor real? | Tokenomics, equipe, produto, adoção, concorrentes, vesting |
| **Executor** | Como executo isso? | Tamanho de posição, entrada escalonada, stop, alvo, timing |

## Como Usar

```
/crypto-council [sua pergunta ou situação]
```

**Exemplos:**
- `/crypto-council Devo comprar ETH agora com BTC dominance em 58%?`
- `/crypto-council Análise do token XYZ: preço $0.04, MC $2M, lançou há 3 meses`
- `/crypto-council Estou -40% em SOL, devo segurar ou cortar a perda?`
- `/crypto-council --quick Vale a pena fazer alavancagem 3x em BTC no suporte de 95k?`

**Flags:**
- `--quick` → Risk Manager + Macro Trader + Executor apenas (decisões rápidas)
- `--jury` → 3 sínteses independentes (decisões de capital alto, >10% do portfólio)
- `--risk` → Foco total em gestão de risco e sizing da posição

## Fluxo de Execução

**Passo 0:** Identificar: é entrada, saída, sizing, análise de projeto ou estratégia?

**Passo 1:** Coletar contexto relevante:
- Preço atual vs histórico
- Ciclo de mercado (bull/bear/lateral)
- Tamanho do portfólio e % alocada
- Timeframe pretendido (scalp/swing/hodl)

**Passo 2:** Spawnar os 5 especialistas em paralelo — cada um responde 150-250 palavras do seu ângulo sem ver os outros.

**Passo 3:** Peer review anônimo — cada especialista avalia todas as respostas (A-E), identifica:
- Raciocínio mais sólido
- Pontos cegos coletivos
- O que ninguém mencionou

**Passo 3.7:** Devil's Advocate ataca o consenso emergente — "se todos concordam em comprar, qual é o risco que estamos ignorando?"

**Passo 4:** Síntese do Presidente com:
- Veredicto: COMPRAR / VENDER / AGUARDAR / EVITAR
- Consenso vs dissidência
- Pontos cegos identificados
- Sizing sugerido (% do portfólio)
- Stop loss e take profit recomendados
- UM próximo passo acionável

**Passo 5:** Seção "O que você perde" — custos da recomendação se o cenário oposto se materializar.

## Princípios Críticos

- **Nunca alocar mais do que o stop loss comporta** — o Executor define isso
- **O Risk Manager tem veto** se identificar risco de ruína (>30% do portfólio)
- **Consenso de compra em alta euforia** = sinal de alerta automático
- **Anonimizar sempre** antes do peer review para evitar viés de autoridade
- **Presidente pode sobrepor maioria** se o raciocínio do dissidente for superior

## Regras de Gestão de Risco Embutidas

| Situação | Regra automática |
|---|---|
| Altcoin desconhecida | Máximo 2% do portfólio |
| Posição alavancada | Máximo 5x, stop obrigatório |
| Mercado em euforia extrema (Fear&Greed >85) | Reduzir posição, não aumentar |
| BTC dominance subindo | Cautela com altcoins |
| Notícia positiva recente | Verificar se já está no preço |

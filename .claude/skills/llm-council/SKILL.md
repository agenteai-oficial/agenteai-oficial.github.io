---
name: llm-council
description: Passa qualquer decisão complexa por 5 conselheiros independentes com revisão entre pares e síntese final. Use para decisões onde errar é caro. Baseado no DMAD (Diverse Multi-Agent Debate, ICLR 2025).
---

# LLM Council — Conselho de 5 Conselheiros

Executa qualquer pergunta, plano, código ou decisão por 5 conselheiros independentes que usam métodos distintos, revisam uns aos outros anonimamente, e sintetizam um veredicto confiável.

## Os 5 Conselheiros

| Conselheiro | Método | O que captura |
|---|---|---|
| **Contrarian** | Inversão (assume fracasso, rastreia para trás) | Pontos cegos quando empolgado |
| **First Principles** | Decomposição em afirmações atômicas | Variáveis erradas |
| **Expansionist** | Analogia com domínios adjacentes | Pensamento pequeno demais |
| **Outsider** | Questionamento ingênuo, zero contexto | Maldição do conhecimento |
| **Executor** | Grafo de dependências, caminho crítico | Planos sem próximos passos |

## Flags Disponíveis

- `--quick` → 3 conselheiros, sem peer review (5 chamadas vs 12)
- `--jury` → 3 presidentes independentes em vez de 1 (para decisões críticas)
- `--adaptive` → parada antecipada se consenso convergir (reduz custo em até 94.5%)

## Quando Usar

**Bom para:** decisões de arquitetura, estratégia de produto, análise de risco, pivôs, entradas/saídas de posição  
**Ruim para:** fatos simples, tarefas criativas diretas, perguntas com resposta óbvia

## Fluxo de Execução

**Passo 0:** Validar escopo e flags  
**Passo 1:** Coletar contexto dos arquivos do projeto; enquadrar neutralmente  
**Passo 2:** Spawnar 5 conselheiros em paralelo — cada um responde 150-300 palavras do seu ângulo sem ver os outros  
**Passo 3:** Peer review anônimo — cada conselheiro avalia todas as respostas (A-E)  
**Passo 3.7:** Devil's Advocate ataca o consenso emergente  
**Passo 4:** Presidente sintetiza: concordância, discordância, pontos cegos, e UM próximo passo acionável  
**Passo 5:** Apresentar veredicto estruturado em markdown  

## Princípios Críticos

- Sempre spawnar conselheiros em paralelo (evita contaminação sequencial)
- Sempre anonimizar antes do peer review
- Presidente pode sobrepor maioria se o raciocínio for superior
- Seção "O que você perde" mostra os custos da recomendação

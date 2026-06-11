import os

# Pares monitorados — adicione ou remova à vontade
PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# Intervalo entre análises (segundos)
INTERVAL = 900  # 15 minutos

# Anthropic API para o Crypto Council
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Webhook para receber alertas (Discord, Slack, Telegram bot, etc.)
# Deixe vazio para só imprimir no terminal
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Binance API — necessário apenas para execução de ordens
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# Modo execução:
#   "alert"   → só imprime/envia webhook (padrão seguro)
#   "dry_run" → simula ordens sem executar (para testar)
#   "live"    → executa ordens reais (requer chaves Binance)
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "alert")

# Confiança mínima do Council para emitir alerta ou executar ordem (0-100)
MIN_CONFIDENCE = 65

# Tamanho máximo de posição (% do portfólio) — o Council ajusta por confiança
MAX_POSITION_PCT = 10

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

# Modo execução automática — False = só alertas, True = executa ordens
AUTO_EXECUTE = False

# Confiança mínima do Council para emitir alerta (0-100)
MIN_CONFIDENCE = 65

# Tamanho máximo de posição (% do portfólio) — o Council respeita isso
MAX_POSITION_PCT = 10

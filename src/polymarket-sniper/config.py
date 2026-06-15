import os
from pathlib import Path

# Carrega .env local se existir (gerado pelo CONFIGURAR-SNIPER.bat)
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# Polymarket Relayer API (geradas em Settings → Chaves API do Relayer)
POLYMARKET_API_KEY         = os.getenv("POLYMARKET_API_KEY", "")
POLYMARKET_API_KEY_ADDRESS = os.getenv("POLYMARKET_API_KEY_ADDRESS", "")
# Mantidos para compatibilidade mas não obrigatórios no Relayer
POLYMARKET_API_SECRET = os.getenv("POLYMARKET_API_SECRET", "")
POLYMARKET_PASSPHRASE = os.getenv("POLYMARKET_PASSPHRASE", "")
WALLET_PRIVATE_KEY    = os.getenv("WALLET_PRIVATE_KEY", "")

# Modelo Claude para edge cases (só acionado quando Markov < MIN_MARKOV_CONFIDENCE)
CLAUDE_MODEL = "claude-fable-5"

# Assets e timeframes monitorados
ASSETS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOT", "DOGE"]
TIMEFRAMES = ["5M", "15M", "30M", "1H", "4H", "1D"]

# Scan interval em segundos
SCAN_INTERVAL = 5

# Probabilidade mínima do Markov para entrar sem LLM
MIN_MARKOV_CONFIDENCE = 0.65

# Kelly fracionário — 0.25 = usa 25% do Kelly ótimo (safety)
KELLY_FRACTION = 0.25

# Posição máxima por trade em USDC
MAX_POSITION_USDC = 100.0

# Lucro mínimo esperado por trade (USDC)
MIN_EXPECTED_PROFIT = 0.10

# Modo de execução: "alert" | "dry_run" | "live"
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "alert")

# Webhook para alertas (Discord/Slack/Telegram)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Anthropic API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Porta do dashboard
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))

# Número de caminhos Monte Carlo
MONTE_CARLO_PATHS = 8172

# Janela de lookback padrão para Markov (ajustada pelo learner)
MARKOV_LOOKBACK = 50

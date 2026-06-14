import numpy as np
from config import MONTE_CARLO_PATHS


def simulate(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    n_trades: int = 100,
    n_paths: int = MONTE_CARLO_PATHS,
    initial_bankroll: float = 1000.0,
) -> dict:
    """
    Simula N caminhos de trading para validar significância estatística.
    Retorna distribuição de retornos e P-value.
    """
    rng = np.random.default_rng()

    # Gera matriz de outcomes: 1 = ganhou, 0 = perdeu
    outcomes = rng.random((n_paths, n_trades)) < win_rate
    pnl = np.where(outcomes, avg_win, -avg_loss)
    final_pnl = pnl.sum(axis=1)

    final_bankroll = initial_bankroll + final_pnl
    total_return = final_pnl / initial_bankroll

    # P-value: proporção de caminhos que terminaram no negativo
    p_value = float((final_pnl < 0).mean())

    percentiles = np.percentile(total_return, [5, 25, 50, 75, 95])

    return {
        "n_paths": n_paths,
        "n_trades": n_trades,
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "expected_return": round(float(total_return.mean()), 4),
        "p5":  round(float(percentiles[0]), 4),
        "p25": round(float(percentiles[1]), 4),
        "p50": round(float(percentiles[2]), 4),
        "p75": round(float(percentiles[3]), 4),
        "p95": round(float(percentiles[4]), 4),
        "max_drawdown": round(float((final_bankroll.min() - initial_bankroll) / initial_bankroll), 4),
        "histogram": [round(x, 4) for x in np.histogram(total_return, bins=20)[0].tolist()],
        "histogram_edges": [round(x, 4) for x in np.histogram(total_return, bins=20)[1].tolist()],
    }

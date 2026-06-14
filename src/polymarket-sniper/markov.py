import numpy as np
from config import MARKOV_LOOKBACK

# Estados do mercado
BULL = 0
NEUTRAL = 1
BEAR = 2
STATE_NAMES = {BULL: "BULL", NEUTRAL: "NEUTRAL", BEAR: "BEAR"}


def _classify_return(r: float, threshold: float = 0.002) -> int:
    if r > threshold:
        return BULL
    if r < -threshold:
        return BEAR
    return NEUTRAL


def build_transition_matrix(prices: list[float], lookback: int = MARKOV_LOOKBACK) -> np.ndarray:
    prices = prices[-lookback:] if len(prices) > lookback else prices
    returns = [prices[i] / prices[i-1] - 1 for i in range(1, len(prices))]
    states = [_classify_return(r) for r in returns]

    matrix = np.ones((3, 3))  # Laplace smoothing
    for i in range(len(states) - 1):
        matrix[states[i]][states[i+1]] += 1

    row_sums = matrix.sum(axis=1, keepdims=True)
    return matrix / row_sums


def current_state(prices: list[float]) -> int:
    if len(prices) < 2:
        return NEUTRAL
    r = prices[-1] / prices[-2] - 1
    return _classify_return(r)


def predict(prices: list[float], steps: int = 3, lookback: int = MARKOV_LOOKBACK) -> dict:
    matrix = build_transition_matrix(prices, lookback)
    state = current_state(prices)

    # Distribuição de probabilidade após N steps
    dist = np.zeros(3)
    dist[state] = 1.0
    for _ in range(steps):
        dist = dist @ matrix

    # P(YES resolve) = probabilidade de continuar BULL
    p_yes = float(dist[BULL])
    p_bear = float(dist[BEAR])
    confidence = float(max(dist))

    return {
        "current_state": STATE_NAMES[state],
        "p_bull": round(p_yes, 4),
        "p_neutral": round(float(dist[NEUTRAL]), 4),
        "p_bear": round(p_bear, 4),
        "confidence": round(confidence, 4),
        "steps": steps,
    }

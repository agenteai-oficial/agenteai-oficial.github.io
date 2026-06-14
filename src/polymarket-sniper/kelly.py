from config import KELLY_FRACTION, MAX_POSITION_USDC


def kelly_size(
    p: float,        # probabilidade estimada de ganhar
    yes_price: float,  # preço do contrato YES (ex: 0.72 = $0.72)
    bankroll: float,   # capital disponível em USDC
) -> dict:
    """
    Kelly Criterion para mercados de predição binários.

    Retorno se ganhar: b = (1 - yes_price) / yes_price
    Retorno se perder: 1 (perde o que apostou)
    f* = (bp - q) / b
    """
    if yes_price <= 0 or yes_price >= 1:
        return {"size_usdc": 0.0, "kelly_f": 0.0, "edge": 0.0, "reason": "preço inválido"}

    b = (1.0 - yes_price) / yes_price  # odds de retorno
    q = 1.0 - p                         # probabilidade de perder
    edge = p - yes_price                # edge: quanto melhor que o mercado

    if edge <= 0:
        return {"size_usdc": 0.0, "kelly_f": 0.0, "edge": round(edge, 4), "reason": "sem edge"}

    kelly_f = (b * p - q) / b
    kelly_f = max(0.0, kelly_f)

    # Kelly fracionário (mais seguro)
    adjusted_f = kelly_f * KELLY_FRACTION
    size = min(bankroll * adjusted_f, MAX_POSITION_USDC)
    size = round(max(0.0, size), 2)

    return {
        "size_usdc": size,
        "kelly_f": round(kelly_f, 4),
        "adjusted_f": round(adjusted_f, 4),
        "edge": round(edge, 4),
        "expected_profit": round(size * edge, 4),
        "reason": "ok",
    }

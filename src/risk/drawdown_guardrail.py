"""CPPI trailing peak floor and risk multiplier. RISK-02. Source: CONTEXT.md D-04, D-05, D-06."""


def compute_cppi_floor(peak_value: float, max_drawdown_limit: float = 0.20) -> float:
    """Return floor = peak * (1 - limit). Per D-04."""
    return peak_value * (1.0 - max_drawdown_limit)


def compute_cppi_multiplier(portfolio_value: float, peak_value: float, max_drawdown_limit: float = 0.20) -> float:
    """Return risk multiplier in [0.0, 1.0]. Per D-05/D-06. Returns 1.0 when no peak established."""
    if peak_value <= 0.0:
        return 1.0
    if max_drawdown_limit <= 0.0:
        return 1.0
    floor = peak_value * (1.0 - max_drawdown_limit)
    cushion = portfolio_value - floor
    if cushion <= 0.0:
        return 0.0
    denominator = max_drawdown_limit * peak_value
    return min(cushion / denominator, 1.0)

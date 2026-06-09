"""Fractional Kelly position sizing helper. RISK-03. Source: CONTEXT.md D-08, D-09, D-10, D-11."""


def fractional_kelly(win_probability: float, win_loss_ratio: float, enabled: bool = False) -> float:
    """Return Quarter Kelly in [0.0, 0.25] when enabled, else 1.0 (neutral). Per D-08/D-09/D-10/D-11."""
    if not enabled:
        return 1.0
    q = 1.0 - win_probability
    full_kelly = (win_probability * win_loss_ratio - q) / win_loss_ratio
    quarter_kelly = full_kelly * 0.25
    quarter_kelly = max(quarter_kelly, 0.0)
    return min(quarter_kelly, 0.25)

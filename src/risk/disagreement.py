"""Deterministic signal disagreement score and multiplier. RISK-01. Source: CONTEXT.md D-01, D-02, D-03."""

from math import sqrt


def compute_disagreement_score(stances: list[int | None]) -> float:
    """Return normalized population std dev of stances, in [0.0, 1.0]. None imputed as 0."""
    values = [s if s is not None else 0 for s in stances]
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return min(sqrt(variance), 1.0)


def compute_disagreement_multiplier(stances: list[int | None]) -> float:
    """Return 1.0 - disagreement_score, in [0.0, 1.0]. Per D-02."""
    return 1.0 - compute_disagreement_score(stances)

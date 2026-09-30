"""Statistical utility functions for the her2rwd pipeline.

Provides reusable, tested helpers for proportions used across Q1 and Q2:
- wilson_ci       — Wilson score 95% CI for a proportion
- build_distribution — add pct, ci_lo, ci_hi, small_cell to a counts Series

All parameters (z, threshold) are passed from the caller so no values
are hard-coded here.

ADRs implemented: ADR-012 (Wilson CI, small-cell flagging)
"""

from __future__ import annotations

import math

import pandas as pd


def wilson_ci(n: int, N: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score confidence interval for proportion n/N.

    Returns (lower, upper) as fractions in [0, 1]. Returns (0, 0) when N=0.
    ADR-012.
    """
    if N == 0:
        return 0.0, 0.0
    p = n / N
    denom = 1 + z**2 / N
    centre = (p + z**2 / (2 * N)) / denom
    margin = z * math.sqrt(p * (1 - p) / N + z**2 / (4 * N**2)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def build_distribution(
    counts: pd.Series,
    total: int,
    threshold: int,
    z: float = 1.96,
) -> pd.DataFrame:
    """Turn a counts Series into a distribution DataFrame with CI and small-cell flag.

    Args:
        counts: Series indexed by category name, values are integer counts.
        total: denominator for percentage calculation.
        threshold: cells with n < threshold are flagged small_cell=True (ADR-012).
        z: z-score for CI (default 1.96 = 95%).

    Returns DataFrame with columns: [index name], n, pct, ci_lo, ci_hi, small_cell.
    """
    df = counts.rename("n").reset_index()
    df["pct"] = (df["n"] / total * 100).round(1) if total > 0 else 0.0
    df["ci_lo"] = df["n"].apply(lambda n: round(wilson_ci(int(n), total, z)[0] * 100, 1))
    df["ci_hi"] = df["n"].apply(lambda n: round(wilson_ci(int(n), total, z)[1] * 100, 1))
    df["small_cell"] = df["n"] < threshold
    return df

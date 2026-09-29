"""Statistical utility functions.

Responsibility:
    Provide reusable, tested statistical helpers used across Q1 and Q2:
    - wilson_ci(n_events, n_total, alpha) → (lower, upper) Wilson 95% CI
    - flag_small_cell(n, threshold) → bool — True if n < threshold
    - format_pct_ci(n, total) → str — "X.X% (n=N; 95% CI Y.Y–Z.Z%)"

    The small-cell threshold is read from config (stats.small_cell_threshold).
    All functions operate on scalars and are vectorised via apply() at call sites.

ADRs implemented: ADR-012 (statistics: Wilson CIs, small-cell flagging)
"""

"""Tests for src/her2rwd/statistics.py.

Covers: wilson_ci boundary conditions and symmetry; build_distribution output shape,
column values, and small-cell flag. ADR-012.
"""

import math

import pandas as pd
import pytest

from her2rwd.statistics import build_distribution, wilson_ci

# ── wilson_ci ─────────────────────────────────────────────────────────────────


class TestWilsonCi:
    def test_zero_denominator_returns_zero_zero(self):
        lo, hi = wilson_ci(0, 0)
        assert lo == 0.0
        assert hi == 0.0

    def test_zero_numerator_lower_bound_is_zero(self):
        lo, hi = wilson_ci(0, 100)
        assert lo == 0.0
        assert hi > 0.0

    def test_all_events_upper_bound_is_one(self):
        lo, hi = wilson_ci(100, 100)
        assert hi == pytest.approx(1.0, abs=1e-9)
        assert lo < 1.0

    def test_half_events_ci_contains_half(self):
        lo, hi = wilson_ci(50, 100)
        assert lo < 0.5 < hi

    def test_ci_lower_less_than_upper(self):
        for n, N in [(1, 10), (5, 20), (11, 103), (3, 41)]:
            lo, hi = wilson_ci(n, N)
            assert lo < hi, f"wilson_ci({n}, {N}) = ({lo}, {hi}): lo >= hi"

    def test_bounds_within_zero_one(self):
        for n, N in [(0, 1), (1, 1), (3, 103), (17, 41)]:
            lo, hi = wilson_ci(n, N)
            assert 0.0 <= lo <= 1.0
            assert 0.0 <= hi <= 1.0

    def test_small_n_no_nan(self):
        lo, hi = wilson_ci(1, 3)
        assert not math.isnan(lo)
        assert not math.isnan(hi)

    def test_custom_z_widens_ci(self):
        lo_95, hi_95 = wilson_ci(5, 20, z=1.96)
        lo_99, hi_99 = wilson_ci(5, 20, z=2.576)
        assert lo_99 < lo_95
        assert hi_99 > hi_95


# ── build_distribution ────────────────────────────────────────────────────────


@pytest.fixture
def sample_counts():
    return pd.Series(
        {"positive": 17, "low": 13, "ultralow": 3, "null": 8, "unknown": 62},
        name="n",
    )


class TestBuildDistribution:
    def test_output_columns(self, sample_counts):
        df = build_distribution(sample_counts, total=103, threshold=11)
        assert set(df.columns) >= {"n", "pct", "ci_lo", "ci_hi", "small_cell"}

    def test_row_count_matches_input(self, sample_counts):
        df = build_distribution(sample_counts, total=103, threshold=11)
        assert len(df) == len(sample_counts)

    def test_pct_sums_to_100(self, sample_counts):
        df = build_distribution(sample_counts, total=103, threshold=11)
        assert abs(df["pct"].sum() - 100.0) < 0.5

    def test_ci_lo_less_than_ci_hi(self, sample_counts):
        df = build_distribution(sample_counts, total=103, threshold=11)
        assert (df["ci_lo"] < df["ci_hi"]).all()

    def test_small_cell_flag_below_threshold(self, sample_counts):
        df = build_distribution(sample_counts, total=103, threshold=11)
        # ultralow=3, null=8 are < 11
        flagged = set(df[df["small_cell"]].iloc[:, 0].tolist())
        assert "ultralow" in flagged
        assert "null" in flagged

    def test_small_cell_flag_at_threshold_not_flagged(self):
        counts = pd.Series({"a": 11, "b": 10}, name="n")
        df = build_distribution(counts, total=21, threshold=11)
        assert not df[df.iloc[:, 0] == "a"]["small_cell"].iloc[0]
        assert df[df.iloc[:, 0] == "b"]["small_cell"].iloc[0]

    def test_zero_total_no_crash(self):
        counts = pd.Series({"a": 0}, name="n")
        df = build_distribution(counts, total=0, threshold=11)
        assert len(df) == 1

    def test_large_category_not_flagged(self, sample_counts):
        df = build_distribution(sample_counts, total=103, threshold=11)
        # unknown=62, positive=17, low=13 are all >= 11
        not_flagged = set(df[~df["small_cell"]].iloc[:, 0].tolist())
        assert "unknown" in not_flagged
        assert "positive" in not_flagged
        assert "low" in not_flagged

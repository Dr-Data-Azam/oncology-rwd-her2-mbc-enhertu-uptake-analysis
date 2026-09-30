"""Tests for src/her2rwd/q2_uptake.py.

One case per subindication assignment branch + key uptake / discordance assertions.
ADRs tested: ADR-011, ADR-012, ADR-013.
"""

from __future__ import annotations

import pandas as pd
import pytest

from her2rwd.q2_uptake import _assign_subindication, compute_q2

# ── cfg fixture ───────────────────────────────────────────────────────────────


@pytest.fixture
def cfg():
    return {
        "stats": {"ci_method": "wilson", "ci_z": 1.96, "small_cell_threshold": 11},
        "treatment": {"enhertu_generic_name": "trastuzumab deruxtecan"},
        "subindications": {
            "required": [
                "her2_positive",
                "hr_pos_her2_low",
                "hr_neg_her2_low",
                "hr_pos_her2_ultralow",
            ],
            "exploratory": ["her2_null", "her2_unknown"],
        },
        "discordance": {"definitions": ["enhertu_in_her2_unknown", "enhertu_in_line_1"]},
    }


# ── _assign_subindication ─────────────────────────────────────────────────────


class TestAssignSubindication:
    def test_her2_positive_any_hr(self):
        assert _assign_subindication("positive", "positive") == "her2_positive"
        assert _assign_subindication("positive", "negative") == "her2_positive"
        assert _assign_subindication("positive", "unknown") == "her2_positive"

    def test_her2_low_hr_positive(self):
        assert _assign_subindication("low", "positive") == "hr_pos_her2_low"

    def test_her2_low_hr_negative(self):
        assert _assign_subindication("low", "negative") == "hr_neg_her2_low"

    def test_her2_low_hr_unknown(self):
        assert _assign_subindication("low", "unknown") == "her2_low_hr_unknown"

    def test_her2_ultralow_hr_positive(self):
        assert _assign_subindication("ultralow", "positive") == "hr_pos_her2_ultralow"

    def test_her2_ultralow_hr_negative(self):
        assert _assign_subindication("ultralow", "negative") == "hr_neg_her2_ultralow"

    def test_her2_null(self):
        assert _assign_subindication("null", "positive") == "her2_null"
        assert _assign_subindication("null", "unknown") == "her2_null"

    def test_her2_unknown(self):
        assert _assign_subindication("unknown", "positive") == "her2_unknown"
        assert _assign_subindication("unknown", "unknown") == "her2_unknown"


# ── compute_q2 ────────────────────────────────────────────────────────────────


def _make_inputs():
    """6-patient minimal dataset covering key branches."""
    cohort = pd.DataFrame({"patient_id": [f"P{i}" for i in range(1, 7)]})

    her2 = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4", "P5", "P6"],
            "her2_category": ["positive", "low", "low", "ultralow", "null", "unknown"],
        }
    )
    hr = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4", "P5", "P6"],
            "hr_status": ["positive", "positive", "negative", "positive", "positive", "positive"],
        }
    )
    # Lines: P1 gets Enhertu in 2L, P2 in 1L, P6 gets Enhertu in 2L (discordance: unknown)
    lines = pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P6", "P6"],
            "line_number": [1, 2, 1, 1, 2],
            "line_start": pd.to_datetime(["2020-02-01", "2020-06-01", "2020-03-01", "2020-02-01", "2020-07-01"]),
            "regimen_drugs": [
                "paclitaxel",
                "trastuzumab deruxtecan",
                "trastuzumab deruxtecan",
                "anastrozole",
                "trastuzumab deruxtecan",
            ],
            "drug_classes": ["chemo", "her2_adc", "her2_adc", "endocrine", "her2_adc"],
            "contains_enhertu": [False, True, True, False, True],
            "days_from_index": [31, 152, 61, 31, 182],
            "n_drugs_in_line": [1, 1, 1, 1, 1],
        }
    )
    return cohort, her2, hr, lines


class TestComputeQ2:
    def test_assignment_csv_written(self, cfg, tmp_path):
        c, h, r, lines_df = _make_inputs()
        compute_q2(h, r, lines_df, c, cfg, out_dir=tmp_path)
        assert (tmp_path / "q2_subindication_assignment.csv").exists()

    def test_uptake_summary_has_required_rows(self, cfg, tmp_path):
        c, h, r, lines_df = _make_inputs()
        result = compute_q2(h, r, lines_df, c, cfg, out_dir=tmp_path)
        subinds = set(result["uptake_summary"]["subindication"])
        for req in ["her2_positive", "hr_pos_her2_low", "hr_neg_her2_low", "hr_pos_her2_ultralow"]:
            assert req in subinds, f"{req} missing from uptake_summary"

    def test_her2_positive_enhertu_count(self, cfg, tmp_path):
        c, h, r, lines_df = _make_inputs()
        result = compute_q2(h, r, lines_df, c, cfg, out_dir=tmp_path)
        row = result["uptake_summary"][result["uptake_summary"]["subindication"] == "her2_positive"]
        assert row.iloc[0]["n_enhertu"] == 1  # P1 got Enhertu in line 2

    def test_discordance_unknown_captures_p6(self, cfg, tmp_path):
        c, h, r, lines_df = _make_inputs()
        result = compute_q2(h, r, lines_df, c, cfg, out_dir=tmp_path)
        discord = result["discordance_unknown_her2"]
        assert "P6" in discord["patient_id"].values

    def test_discordance_1l_captures_p2(self, cfg, tmp_path):
        c, h, r, lines_df = _make_inputs()
        result = compute_q2(h, r, lines_df, c, cfg, out_dir=tmp_path)
        discord = result["discordance_1l"]
        # P2 (HER2-low HR+) got Enhertu in 1L
        assert "P2" in discord["patient_id"].values

    def test_discordance_1l_does_not_include_2l(self, cfg, tmp_path):
        c, h, r, lines_df = _make_inputs()
        result = compute_q2(h, r, lines_df, c, cfg, out_dir=tmp_path)
        discord = result["discordance_1l"]
        # P1 got Enhertu in 2L — should NOT be in 1L discordance
        assert "P1" not in discord["patient_id"].values

    def test_all_csvs_written(self, cfg, tmp_path):
        c, h, r, lines_df = _make_inputs()
        compute_q2(h, r, lines_df, c, cfg, out_dir=tmp_path)
        for fname in [
            "q2_subindication_assignment.csv",
            "q2_uptake_summary.csv",
            "q2_enhertu_by_line.csv",
            "q2_competitor_map.csv",
            "q2_discordance_unknown_her2.csv",
            "q2_discordance_1l.csv",
        ]:
            assert (tmp_path / fname).exists(), f"{fname} not written"

    def test_small_cell_flagged_for_small_subindications(self, cfg, tmp_path):
        c, h, r, lines_df = _make_inputs()
        result = compute_q2(h, r, lines_df, c, cfg, out_dir=tmp_path)
        # All subindications in this 6-patient set have n<11
        assert result["uptake_summary"]["small_cell"].all()

    def test_by_line_has_three_label_rows_per_subind(self, cfg, tmp_path):
        c, h, r, lines_df = _make_inputs()
        result = compute_q2(h, r, lines_df, c, cfg, out_dir=tmp_path)
        # Each of the 6 subindications should have 3 line-label rows (1L, 2L, 3L+)
        counts = result["by_line"].groupby("subindication")["line_label"].count()
        assert (counts == 3).all()

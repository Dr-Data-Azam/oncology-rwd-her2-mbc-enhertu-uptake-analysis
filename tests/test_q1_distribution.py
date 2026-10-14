"""Tests for src/her2rwd/q1_distribution.py.

Uses minimal in-memory DataFrames — no DuckDB, no file I/O beyond temp dir.
ADRs tested: ADR-012, ADR-014.
"""

import pandas as pd
import pytest

from her2rwd.q1_distribution import compute_q1


@pytest.fixture
def minimal_cfg():
    return {
        "stats": {
            "ci_method": "wilson",
            "ci_z": 1.96,
            "small_cell_threshold": 11,
        },
        "benchmarks": {
            "her2_positive_pct_range": [15, 20],
            "her2_low_pct_range": [45, 55],
            "her2_zero_pct_range": [25, 35],
            "hr_positive_pct_range": [65, 75],
            "her2_ultralow_of_zero_pct": [35, 50],
            "source_citation": "VERIFY: test",
        },
    }


def _make_patients(
    n_pos=17,
    n_low=13,
    n_ultra=3,
    n_null=8,
    n_unk=62,
    n_hr_pos=74,
    n_hr_neg=2,
    n_hr_unk=27,
    n_denovo=61,
    n_recur=42,
):
    """Build minimal her2_df, hr_df, cohort_df with exact counts."""
    total = n_pos + n_low + n_ultra + n_null + n_unk
    pids = list(range(1, total + 1))
    cats = ["positive"] * n_pos + ["low"] * n_low + ["ultralow"] * n_ultra + ["null"] * n_null + ["unknown"] * n_unk
    # Alternate curated (1) / EHR (0) flags so both strata are represented
    curation_flags = [i % 2 for i in range(total)]
    her2_df = pd.DataFrame({"patient_id": pids, "her2_category": cats, "her2_curation_flag": curation_flags})

    hr_statuses = ["positive"] * n_hr_pos + ["negative"] * n_hr_neg + ["unknown"] * n_hr_unk
    hr_df = pd.DataFrame({"patient_id": pids, "hr_status": hr_statuses})

    disease_types = ["de_novo"] * n_denovo + ["recurrent"] * n_recur
    cohort_df = pd.DataFrame({"patient_id": pids, "disease_type": disease_types})

    return her2_df, hr_df, cohort_df


class TestComputeQ1:
    def test_overall_has_five_categories(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        assert len(result["overall"]) == 5

    def test_overall_n_sums_to_total(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        assert result["overall"]["n"].sum() == result["n_total"]

    def test_n_total_correct(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        assert result["n_total"] == 103

    def test_n_classifiable_excludes_unknown(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        # 17+13+3+8 = 41
        assert result["n_classifiable"] == 41

    def test_small_cell_flagged_for_ultralow(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        overall = result["overall"]
        ultra_row = overall[overall["her2_category"] == "ultralow"]
        assert ultra_row["small_cell"].iloc[0]

    def test_large_cells_not_flagged(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        overall = result["overall"]
        unk_row = overall[overall["her2_category"] == "unknown"]
        assert not unk_row["small_cell"].iloc[0]

    def test_by_hr_has_three_groups(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        assert result["by_hr"]["hr_status"].nunique() == 3

    def test_by_disease_type_has_two_groups(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        assert result["by_disease_type"]["disease_type"].nunique() == 2

    def test_benchmark_has_four_rows(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        assert len(result["benchmark"]) == 4

    def test_csv_files_written(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        expected = [
            "q1_overall.csv",
            "q1_by_hr.csv",
            "q1_by_disease_type.csv",
            "q1_by_source.csv",
            "q1_benchmark.csv",
        ]
        for fname in expected:
            assert (tmp_path / fname).exists(), f"{fname} not written"

    def test_benchmark_in_range_column_present(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        assert "in_benchmark_range" in result["benchmark"].columns

    def test_ci_lo_less_than_ci_hi_overall(self, minimal_cfg, tmp_path):
        h, r, c = _make_patients()
        result = compute_q1(h, r, c, minimal_cfg, out_dir=tmp_path)
        df = result["overall"]
        # Only check rows where n > 0 (ci undefined for n=N=0 edge case)
        nonzero = df[df["n"] > 0]
        assert (nonzero["ci_lo"] < nonzero["ci_hi"]).all()

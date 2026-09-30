"""Tests for sensitivity.py — alternative rule set re-runs.

Each test verifies that sensitivity scenarios produce valid output DataFrames
with expected structural properties, using minimal in-memory patient fixtures.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from her2rwd.sensitivity import _CAT_ORDER, _cfg_s1, _cfg_s2, _cfg_s3, run_sensitivity

# ── Shared fixture ────────────────────────────────────────────────────────────


@pytest.fixture
def base_cfg():
    return {
        "her2": {
            "window_days": {"pre_index": 365, "post_index": 90},
            "variant_to_category": {
                "IHC 3+": "positive",
                "IHC 2+; ISH amplified": "positive",
                "IHC 1+": "low",
                "IHC 2+; ISH negative": "low",
                "IHC 0 with faint membrane staining in <=10% cells": "ultralow",
                "IHC 0 absent membrane staining": "null",
                "IHC 0": "null",
                "IHC 0 with membrane staining": "unknown",
                "IHC equivocal": "unknown",
                "Pending": "unknown",
            },
            "tiebreak_order": ["curation_flag", "variant_specificity", "closest_to_index"],
            "conflict_resolution": "variant_beats_result_text",
        },
        "hr": {
            "positive_threshold_pct": 1,
            "er_low_max_pct": 10,
            "pct_beats_result_text": True,
            "null_variant_fallback": "result_text",
        },
        "treatment": {
            "regimen_window_days": 28,
            "new_line_gap_days": 90,
            "enhertu_generic_name": "trastuzumab deruxtecan",
            "drug_class_map": {
                "trastuzumab deruxtecan": "her2_adc",
                "paclitaxel": "chemo",
            },
        },
        "stats": {
            "ci_z": 1.96,
            "small_cell_threshold": 11,
        },
        "subindications": {
            "required": [
                "her2_positive",
                "hr_pos_her2_low",
                "hr_neg_her2_low",
                "hr_pos_her2_ultralow",
            ],
            "exploratory": ["her2_null", "her2_unknown"],
        },
        "discordance": {
            "definitions": ["enhertu_in_her2_unknown", "enhertu_in_line_1"],
        },
        "dq": {
            "post_death_grace_days": 30,
            "curation_priority": "curated_first",
        },
        "benchmarks": {
            "her2_positive_pct_range": [15, 20],
            "her2_low_pct_range": [45, 55],
            "her2_zero_pct_range": [25, 35],
            "hr_positive_pct_range": [65, 75],
            "her2_ultralow_of_zero_pct": [35, 50],
            "source_citation": "Test citation",
        },
    }


@pytest.fixture
def minimal_con_cohort(base_cfg):
    """In-memory DuckDB with 4 patients covering multiple HER2 categories."""
    con = duckdb.connect(":memory:")

    patients = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4"],
            "date_of_birth": ["1960-01-01"] * 4,
            "date_of_death": [None] * 4,
            "sex": ["Female"] * 4,
        }
    )
    con.register("patient", patients)

    # Biomarker — tests within window of 2020-06-01 index
    biomarker = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4"],
            "biomarker_name": ["HER2"] * 4,
            "biomarker_variant": ["IHC 3+", "IHC 1+", "IHC 0", "Pending"],
            "biomarker_result": ["Positive", "Positive", "Negative", "Unknown"],
            "report_date": ["2020-05-01"] * 4,
            "curation_flag": [1, 1, 0, 0],
        }
    )
    con.register("biomarker", biomarker)

    # HR biomarker (ER)
    er_bio = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4"],
            "biomarker_name": ["ER"] * 4,
            "biomarker_variant": ["80%", "2%", None, None],
            "biomarker_result": ["Positive", "Positive", "Negative", "Unknown"],
            "report_date": ["2020-05-01"] * 4,
            "curation_flag": [1, 1, 0, 0],
        }
    )
    pr_bio = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4"],
            "biomarker_name": ["PR"] * 4,
            "biomarker_variant": [None] * 4,
            "biomarker_result": ["Positive", "Negative", "Negative", "Unknown"],
            "report_date": ["2020-05-01"] * 4,
            "curation_flag": [1, 1, 0, 0],
        }
    )
    all_bio = pd.concat([biomarker, er_bio, pr_bio], ignore_index=True)
    con.register("biomarker", all_bio)

    # Minimal other tables
    con.register(
        "diagnosis",
        pd.DataFrame(columns=["patient_id", "diagnosis_date", "diagnosis_code", "diagnosis_type"]),
    )
    con.register("staging", pd.DataFrame(columns=["patient_id", "stage_date", "stage_group", "m_stage"]))
    medication = pd.DataFrame(
        {
            "patient_id": ["P1"],
            "med_generic_name": ["trastuzumab deruxtecan"],
            "med_brand_name": ["Enhertu"],
            "med_date": pd.to_datetime(["2020-07-01"]),
            "med_status": ["active"],
            "curation_flag": [1],
        }
    )
    con.register("medication", medication)

    cohort = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4"],
            "index_date": pd.to_datetime(["2020-06-01"] * 4),
            "disease_type": ["de_novo"] * 4,
            "date_of_birth": pd.to_datetime(["1960-01-01"] * 4),
            "date_of_death": [None] * 4,
            "age_at_index": [60] * 4,
        }
    )

    return con, cohort


# ── Config modifier tests ─────────────────────────────────────────────────────


def test_cfg_s1_narrows_window(base_cfg):
    c = _cfg_s1(base_cfg)
    assert c["her2"]["window_days"]["pre_index"] == 180
    assert base_cfg["her2"]["window_days"]["pre_index"] == 365  # original unchanged


def test_cfg_s2_sets_curated_only(base_cfg):
    c = _cfg_s2(base_cfg)
    assert c["her2"].get("curated_only") is True
    assert "curated_only" not in base_cfg["her2"]  # original unchanged


def test_cfg_s3_maps_ihc0_to_unknown(base_cfg):
    c = _cfg_s3(base_cfg)
    assert c["her2"]["variant_to_category"]["IHC 0"] == "unknown"
    assert base_cfg["her2"]["variant_to_category"]["IHC 0"] == "null"  # original unchanged


# ── Full sensitivity run tests ─────────────────────────────────────────────────


def test_sensitivity_returns_dict(minimal_con_cohort, base_cfg, tmp_path):
    con, cohort = minimal_con_cohort
    result = run_sensitivity(con, cohort, base_cfg, out_dir=str(tmp_path))
    assert isinstance(result, dict)
    assert "her2_distribution" in result
    assert "uptake" in result


def test_her2_distribution_has_all_categories(minimal_con_cohort, base_cfg, tmp_path):
    con, cohort = minimal_con_cohort
    result = run_sensitivity(con, cohort, base_cfg, out_dir=str(tmp_path))
    df = result["her2_distribution"]
    assert set(df["her2_category"]) == set(_CAT_ORDER)


def test_her2_distribution_has_all_columns(minimal_con_cohort, base_cfg, tmp_path):
    con, cohort = minimal_con_cohort
    result = run_sensitivity(con, cohort, base_cfg, out_dir=str(tmp_path))
    df = result["her2_distribution"]
    expected_cols = {
        "her2_category",
        "n_baseline",
        "pct_baseline",
        "n_s1_narrow_window",
        "pct_s1_narrow_window",
        "n_s2_curated_only",
        "pct_s2_curated_only",
        "n_s3_conservative_ihc0",
        "pct_s3_conservative_ihc0",
    }
    assert expected_cols.issubset(set(df.columns))


def test_sensitivity_csvs_written(minimal_con_cohort, base_cfg, tmp_path):
    con, cohort = minimal_con_cohort
    run_sensitivity(con, cohort, base_cfg, out_dir=str(tmp_path))
    assert (tmp_path / "sensitivity_her2_distribution.csv").exists()
    assert (tmp_path / "sensitivity_uptake.csv").exists()


def test_s3_conservative_increases_unknown(minimal_con_cohort, base_cfg, tmp_path):
    """S3 maps IHC 0 → unknown; patient P3 has IHC 0, so unknown count should increase."""
    con, cohort = minimal_con_cohort
    result = run_sensitivity(con, cohort, base_cfg, out_dir=str(tmp_path))
    df = result["her2_distribution"]
    row_unk = df[df["her2_category"] == "unknown"].iloc[0]
    # S3 should have >= baseline unknown count (P3's IHC 0 moves from null → unknown)
    assert row_unk["n_s3_conservative_ihc0"] >= row_unk["n_baseline"]


def test_baseline_n_sums_to_cohort(minimal_con_cohort, base_cfg, tmp_path):
    con, cohort = minimal_con_cohort
    result = run_sensitivity(con, cohort, base_cfg, out_dir=str(tmp_path))
    df = result["her2_distribution"]
    assert df["n_baseline"].sum() == len(cohort)


def test_s1_n_sums_to_cohort(minimal_con_cohort, base_cfg, tmp_path):
    con, cohort = minimal_con_cohort
    result = run_sensitivity(con, cohort, base_cfg, out_dir=str(tmp_path))
    df = result["her2_distribution"]
    assert df["n_s1_narrow_window"].sum() == len(cohort)


def test_uptake_has_subindication_column(minimal_con_cohort, base_cfg, tmp_path):
    con, cohort = minimal_con_cohort
    result = run_sensitivity(con, cohort, base_cfg, out_dir=str(tmp_path))
    assert "subindication" in result["uptake"].columns

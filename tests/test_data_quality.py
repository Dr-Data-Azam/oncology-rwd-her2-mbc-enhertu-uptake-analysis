"""Tests for data_quality.py — DQ check suite.

Each test builds a minimal in-memory DuckDB fixture and verifies that the
relevant check fires (or does not fire) as expected. No files on disk are
touched; fixtures use tmp_path only where CSV output must be checked.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from her2rwd.data_quality import run_dq_checks

# ── minimal config matching analysis_rules.yaml ADR-003 values ───────────────
_CFG = {
    "dq": {
        "future_date_action": "flag",
        "post_death_action": "flag",
        "pre_birth_action": "flag",
        "post_death_grace_days": 30,
    }
}


def _empty_con() -> duckdb.DuckDBPyConnection:
    """Return a connection with all five raw tables, all empty."""
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE patient (
            patient_id VARCHAR, date_of_birth DATE, date_of_death DATE,
            org_id VARCHAR, org_type VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE diagnosis (
            patient_id VARCHAR, diagnosis_date DATE,
            diagnosis_code VARCHAR, diagnosis_type VARCHAR, curation_flag INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE staging (
            patient_id VARCHAR, stage_date DATE, stage_group VARCHAR,
            t_stage VARCHAR, n_stage VARCHAR, m_stage VARCHAR, curation_flag INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE biomarker (
            patient_id VARCHAR, report_date DATE, biomarker_name VARCHAR,
            biomarker_test_type VARCHAR, biomarker_result VARCHAR,
            biomarker_variant VARCHAR, curation_flag INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE medication (
            patient_id VARCHAR, med_date DATE, med_brand_name VARCHAR,
            med_generic_name VARCHAR, med_status VARCHAR, curation_flag INTEGER
        )
    """)
    return con


# ── helpers ───────────────────────────────────────────────────────────────────


def _insert_patient(con, pid, dob="1970-01-01", dod=None):
    dod_val = f"'{dod}'" if dod else "NULL"
    con.execute(
        f"INSERT INTO patient VALUES ('{pid}', '{dob}', {dod_val}, 'ORG_001', 'academic')"
    )


def _insert_biomarker(con, pid, name, variant, report_date="2024-01-01"):
    variant_sql = "NULL" if variant is None else f"'{variant}'"
    con.execute(
        f"INSERT INTO biomarker VALUES ('{pid}', '{report_date}', '{name}', "
        f"'IHC', 'Positive', {variant_sql}, 1)"
    )


# ── tests ─────────────────────────────────────────────────────────────────────


def test_clean_data_produces_no_errors(tmp_path):
    """All checks return 0 flagged when data is clean."""
    con = _empty_con()
    _insert_patient(con, "PAT_001", dob="1970-01-01", dod="2023-06-01")
    con.execute(
        "INSERT INTO diagnosis VALUES ('PAT_001', '2022-01-01', 'C50.8', 'metastatic', 1)"
    )
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    errors = summary[summary["severity"] == "error"]["n_flagged"].sum()
    assert errors == 0, f"Expected no errors on clean data, got:\n{summary}"


def test_death_before_birth_is_flagged(tmp_path):
    """Patient whose death date precedes birth date triggers death_before_birth check."""
    con = _empty_con()
    _insert_patient(con, "PAT_BAD", dob="1980-06-15", dod="1979-12-01")
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    row = summary[summary["check_name"] == "death_before_birth"].iloc[0]
    assert row["n_flagged"] == 1


def test_null_her2_variant_flagged(tmp_path):
    """HER2 records with NULL variant trigger null_her2_variant check."""
    con = _empty_con()
    _insert_patient(con, "PAT_001")
    _insert_biomarker(con, "PAT_001", "HER2", None)
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    row = summary[summary["check_name"] == "null_her2_variant"].iloc[0]
    assert row["n_flagged"] == 1
    assert row["action"] == "classify_as_unknown"


def test_pending_her2_variant_flagged(tmp_path):
    """HER2 records with 'Pending' variant trigger unclassifiable_her2_variant check."""
    con = _empty_con()
    _insert_patient(con, "PAT_001")
    _insert_biomarker(con, "PAT_001", "HER2", "Pending")
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    row = summary[summary["check_name"] == "unclassifiable_her2_variant"].iloc[0]
    assert row["n_flagged"] == 1


def test_post_death_biomarker_within_grace_not_flagged(tmp_path):
    """Biomarker within grace window (30 days) after death is NOT flagged."""
    con = _empty_con()
    _insert_patient(con, "PAT_001", dob="1960-01-01", dod="2023-06-01")
    _insert_biomarker(con, "PAT_001", "HER2", "IHC 3+", report_date="2023-06-20")
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    row = summary[summary["check_name"] == "post_death_biomarker"].iloc[0]
    assert row["n_flagged"] == 0


def test_post_death_biomarker_beyond_grace_flagged(tmp_path):
    """Biomarker beyond grace window (>30 days) after death IS flagged."""
    con = _empty_con()
    _insert_patient(con, "PAT_001", dob="1960-01-01", dod="2023-06-01")
    _insert_biomarker(con, "PAT_001", "HER2", "IHC 3+", report_date="2023-08-01")
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    row = summary[summary["check_name"] == "post_death_biomarker"].iloc[0]
    assert row["n_flagged"] == 1


def test_dq_log_csv_written(tmp_path):
    """run_dq_checks writes dq_log.csv and dq_summary.csv to out_dir."""
    con = _empty_con()
    run_dq_checks(con, _CFG, out_dir=tmp_path)
    assert (tmp_path / "dq_log.csv").exists()
    assert (tmp_path / "dq_summary.csv").exists()


def test_summary_has_all_checks(tmp_path):
    """Summary DataFrame has one row per defined check."""
    con = _empty_con()
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    assert len(summary) >= 19
    assert set(["check_name", "n_flagged", "severity", "action"]).issubset(summary.columns)


def test_her2_result_variant_conflict_flagged(tmp_path):
    """HER2 result='Negative' + variant='IHC 1+' triggers her2_result_variant_conflict."""
    con = _empty_con()
    _insert_patient(con, "PAT_001")
    _insert_biomarker(con, "PAT_001", "HER2", "IHC 1+", report_date="2024-01-01")
    # Manually update result to Negative (helper always sets Positive)
    con.execute("UPDATE biomarker SET biomarker_result = 'Negative' WHERE biomarker_variant = 'IHC 1+'")
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    row = summary[summary["check_name"] == "her2_result_variant_conflict"].iloc[0]
    assert row["n_flagged"] == 1
    assert row["action"] == "variant_beats_result_text"


def test_er_pr_null_variant_fallback_flagged(tmp_path):
    """ER record with NULL variant triggers er_pr_null_variant_fallback."""
    con = _empty_con()
    _insert_patient(con, "PAT_001")
    _insert_biomarker(con, "PAT_001", "ER", None)
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    row = summary[summary["check_name"] == "er_pr_null_variant_fallback"].iloc[0]
    assert row["n_flagged"] == 1
    assert row["action"] == "use_result_text_fallback"


def test_duplicate_biomarker_same_date_flagged(tmp_path):
    """Two HER2 records for same patient on same date triggers duplicate_biomarker_same_date."""
    con = _empty_con()
    _insert_patient(con, "PAT_001")
    _insert_biomarker(con, "PAT_001", "HER2", "IHC 3+", report_date="2024-01-01")
    _insert_biomarker(con, "PAT_001", "HER2", "IHC 2+; ISH amplified", report_date="2024-01-01")
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    row = summary[summary["check_name"] == "duplicate_biomarker_same_date"].iloc[0]
    assert row["n_flagged"] == 1


def test_non_breast_metastatic_code_flagged(tmp_path):
    """Metastatic diagnosis with non-C50 code triggers non_breast_metastatic_code."""
    con = _empty_con()
    _insert_patient(con, "PAT_001")
    con.execute("INSERT INTO diagnosis VALUES ('PAT_001', '2023-01-01', 'C34.9', 'metastatic', 1)")
    summary = run_dq_checks(con, _CFG, out_dir=tmp_path)
    row = summary[summary["check_name"] == "non_breast_metastatic_code"].iloc[0]
    assert row["n_flagged"] == 1
    assert row["action"] == "exclude_from_index_date"

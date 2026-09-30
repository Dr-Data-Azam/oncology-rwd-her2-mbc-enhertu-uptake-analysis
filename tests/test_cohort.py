"""Tests for cohort.py — cohort construction and attrition.

Each test builds a minimal in-memory DuckDB fixture with one hand-crafted
patient that exercises exactly one decision branch. Uses tmp_path for CSV output.

ADRs covered: ADR-002, ADR-004, ADR-005
"""

from __future__ import annotations

import duckdb

from her2rwd.cohort import build_cohort

# ── minimal config matching analysis_rules.yaml ADR-002/004/005 values ────────
_CFG = {
    "eligibility": {"min_age_at_index_years": 18},
    "cohort": {"de_novo_primary_gap_days": 180},
}


# ── fixtures ──────────────────────────────────────────────────────────────────


def _empty_con() -> duckdb.DuckDBPyConnection:
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


def _add_patient(con, pid, dob="1970-01-01", dod=None):
    dod_val = f"'{dod}'" if dod else "NULL"
    con.execute(f"INSERT INTO patient VALUES ('{pid}', '{dob}', {dod_val}, 'ORG_001', 'academic')")


def _add_diagnosis(con, pid, code, dtype, ddate):
    con.execute(f"INSERT INTO diagnosis VALUES ('{pid}', '{ddate}', '{code}', '{dtype}', 1)")


def _add_staging(con, pid, stage_date, stage_group=None, m_stage=None):
    sg = f"'{stage_group}'" if stage_group else "NULL"
    ms = f"'{m_stage}'" if m_stage else "NULL"
    con.execute(f"INSERT INTO staging VALUES ('{pid}', '{stage_date}', {sg}, NULL, NULL, {ms}, 1)")


# ── tests ─────────────────────────────────────────────────────────────────────


def test_staging_only_patient_included(tmp_path):
    """Patient with M1 staging but no C50 metastatic dx is included (index_source=staging_only)."""
    con = _empty_con()
    _add_patient(con, "P1")
    _add_staging(con, "P1", "2020-01-01", m_stage="M1")

    cohort, _ = build_cohort(con, _CFG, out_dir=tmp_path)

    assert len(cohort) == 1
    assert cohort.iloc[0]["index_source"] == "staging_only"


def test_earliest_date_wins_staging(tmp_path):
    """When staging precedes metastatic dx, index_date = staging date."""
    con = _empty_con()
    _add_patient(con, "P1")
    _add_diagnosis(con, "P1", "C50.1", "metastatic", "2020-06-01")
    _add_staging(con, "P1", "2020-01-01", m_stage="M1")  # earlier

    cohort, _ = build_cohort(con, _CFG, out_dir=tmp_path)

    assert cohort.iloc[0]["index_date"].strftime("%Y-%m-%d") == "2020-01-01"
    assert cohort.iloc[0]["index_source"] == "staging_first"


def test_earliest_date_wins_diagnosis(tmp_path):
    """When metastatic dx precedes staging, index_date = diagnosis date."""
    con = _empty_con()
    _add_patient(con, "P1")
    _add_diagnosis(con, "P1", "C50.1", "metastatic", "2020-01-01")  # earlier
    _add_staging(con, "P1", "2020-06-01", m_stage="M1")

    cohort, _ = build_cohort(con, _CFG, out_dir=tmp_path)

    assert cohort.iloc[0]["index_date"].strftime("%Y-%m-%d") == "2020-01-01"
    assert cohort.iloc[0]["index_source"] == "diagnosis_first"


def test_non_c50_metastatic_code_excluded_from_index(tmp_path):
    """Non-C50 metastatic diagnosis code (e.g. C34.9) does not count toward index date."""
    con = _empty_con()
    _add_patient(con, "P1")
    _add_diagnosis(con, "P1", "C34.9", "metastatic", "2020-01-01")  # lung — not C50

    cohort, _ = build_cohort(con, _CFG, out_dir=tmp_path)

    assert len(cohort) == 0


def test_death_before_birth_excluded(tmp_path):
    """Patient with date_of_death < date_of_birth is excluded with attrition entry."""
    con = _empty_con()
    _add_patient(con, "P1", dob="1970-01-01", dod="1960-01-01")  # impossible
    _add_diagnosis(con, "P1", "C50.1", "metastatic", "2020-01-01")

    cohort, attrition = build_cohort(con, _CFG, out_dir=tmp_path)

    assert len(cohort) == 0
    row = attrition[attrition["step_label"].str.contains("birth")].iloc[0]
    assert row["n_excluded"] == 1


def test_age_under_18_excluded(tmp_path):
    """Patient aged 10 at index date is excluded; attrition step records exclusion."""
    con = _empty_con()
    _add_patient(con, "P1", dob="2010-01-01")  # age 10 at 2020 index
    _add_diagnosis(con, "P1", "C50.1", "metastatic", "2020-01-01")

    cohort, attrition = build_cohort(con, _CFG, out_dir=tmp_path)

    assert len(cohort) == 0
    row = attrition[attrition["step_label"].str.contains("age")].iloc[0]
    assert row["n_excluded"] == 1


def test_de_novo_no_prior_primary(tmp_path):
    """Patient with no prior primary C50 diagnosis is classified as de_novo."""
    con = _empty_con()
    _add_patient(con, "P1")
    _add_diagnosis(con, "P1", "C50.1", "metastatic", "2020-01-01")

    cohort, _ = build_cohort(con, _CFG, out_dir=tmp_path)

    assert cohort.iloc[0]["disease_type"] == "de_novo"


def test_de_novo_short_gap(tmp_path):
    """Primary to metastatic gap of 90 days (<=180) classifies patient as de_novo."""
    con = _empty_con()
    _add_patient(con, "P1")
    _add_diagnosis(con, "P1", "C50.1", "primary", "2020-01-01")
    _add_diagnosis(con, "P1", "C50.1", "metastatic", "2020-04-10")  # 100 days later

    cohort, _ = build_cohort(con, _CFG, out_dir=tmp_path)

    assert cohort.iloc[0]["disease_type"] == "de_novo"


def test_recurrent_long_gap(tmp_path):
    """Primary to metastatic gap of 5 years (>180 days) classifies patient as recurrent."""
    con = _empty_con()
    _add_patient(con, "P1")
    _add_diagnosis(con, "P1", "C50.1", "primary", "2015-01-01")
    _add_diagnosis(con, "P1", "C50.1", "metastatic", "2020-01-01")  # 5 years later

    cohort, _ = build_cohort(con, _CFG, out_dir=tmp_path)

    assert cohort.iloc[0]["disease_type"] == "recurrent"


def test_attrition_sums_correctly(tmp_path):
    """Sum of all n_excluded plus final n_remaining equals total patients at step 1."""
    con = _empty_con()
    # P1: eligible
    _add_patient(con, "P1", dob="1970-01-01")
    _add_diagnosis(con, "P1", "C50.1", "metastatic", "2020-01-01")
    # P2: no metastatic signal -> excluded at step 2
    _add_patient(con, "P2", dob="1970-01-01")
    # P3: death before birth -> excluded at step 3
    _add_patient(con, "P3", dob="1970-01-01", dod="1960-01-01")
    _add_diagnosis(con, "P3", "C50.1", "metastatic", "2020-01-01")

    _, attrition = build_cohort(con, _CFG, out_dir=tmp_path)

    total_start = attrition.iloc[0]["n_remaining"]
    total_excluded = attrition["n_excluded"].sum()
    final_remaining = attrition.iloc[-1]["n_remaining"]
    assert total_excluded + final_remaining == total_start


def test_outputs_written_to_csv(tmp_path):
    """build_cohort writes cohort.csv and attrition.csv to out_dir."""
    con = _empty_con()
    _add_patient(con, "P1")
    _add_diagnosis(con, "P1", "C50.1", "metastatic", "2020-01-01")

    build_cohort(con, _CFG, out_dir=tmp_path)

    assert (tmp_path / "cohort.csv").exists()
    assert (tmp_path / "attrition.csv").exists()

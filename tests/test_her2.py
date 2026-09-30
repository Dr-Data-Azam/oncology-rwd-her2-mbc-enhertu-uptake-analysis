"""Tests for her2.py — HER2 category derivation.

Each test builds a minimal in-memory DuckDB fixture with one hand-crafted
patient that exercises exactly one decision branch.

ADRs covered: ADR-006 (mapping), ADR-007 (window), ADR-008 (tie-break)
"""

from __future__ import annotations

import duckdb
import pandas as pd

from her2rwd.her2 import derive_her2

_CFG = {
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
    }
}


def _empty_con() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE biomarker (
            patient_id VARCHAR, report_date DATE, biomarker_name VARCHAR,
            biomarker_test_type VARCHAR, biomarker_result VARCHAR,
            biomarker_variant VARCHAR, curation_flag INTEGER
        )
    """)
    return con


def _cohort(pid, index_date="2020-06-01") -> pd.DataFrame:
    return pd.DataFrame({"patient_id": [pid], "index_date": [pd.Timestamp(index_date)]})


def _add_her2(con, pid, variant, result="Positive", report_date="2020-04-01", flag=1):
    v = "NULL" if variant is None else f"'{variant}'"
    con.execute(f"INSERT INTO biomarker VALUES ('{pid}', '{report_date}', 'HER2', " f"'IHC', '{result}', {v}, {flag})")


# ── category mapping tests (ADR-006) ─────────────────────────────────────────


def test_ihc3plus_maps_to_positive(tmp_path):
    con = _empty_con()
    _add_her2(con, "P1", "IHC 3+")
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "positive"


def test_ihc2plus_ish_amplified_maps_to_positive(tmp_path):
    con = _empty_con()
    _add_her2(con, "P1", "IHC 2+; ISH amplified")
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "positive"


def test_ihc1plus_maps_to_low(tmp_path):
    con = _empty_con()
    _add_her2(con, "P1", "IHC 1+", result="Negative")  # result conflicts — variant wins
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "low"


def test_ihc0_faint_maps_to_ultralow(tmp_path):
    con = _empty_con()
    _add_her2(con, "P1", "IHC 0 with faint membrane staining in <=10% cells")
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "ultralow"


def test_ihc0_absent_maps_to_null(tmp_path):
    con = _empty_con()
    _add_her2(con, "P1", "IHC 0 absent membrane staining")
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "null"


def test_ihc0_no_detail_maps_to_null(tmp_path):
    con = _empty_con()
    _add_her2(con, "P1", "IHC 0")
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "null"


def test_ihc0_membrane_staining_maps_to_unknown(tmp_path):
    con = _empty_con()
    _add_her2(con, "P1", "IHC 0 with membrane staining")
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "unknown"


def test_null_variant_maps_to_unknown(tmp_path):
    con = _empty_con()
    _add_her2(con, "P1", None)
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "unknown"


# ── window tests (ADR-007) ────────────────────────────────────────────────────


def test_record_outside_window_excluded(tmp_path):
    """HER2 record more than 365 days before index date is outside window -> unknown."""
    con = _empty_con()
    _add_her2(con, "P1", "IHC 3+", report_date="2018-01-01")  # >365d before 2020-06-01
    result = derive_her2(con, _cohort("P1", "2020-06-01"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "unknown"
    assert result.iloc[0]["n_her2_in_window"] == 0


def test_record_at_window_edge_included(tmp_path):
    """HER2 record exactly 365 days before index date is inside window (BETWEEN is inclusive)."""
    con = _empty_con()
    # 2019-01-01 to 2020-01-01 = exactly 365 days (2019 is not a leap year)
    _add_her2(con, "P1", "IHC 3+", report_date="2019-01-01")
    result = derive_her2(con, _cohort("P1", "2020-01-01"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "positive"


# ── tie-break tests (ADR-008) ─────────────────────────────────────────────────


def test_curated_beats_uncurated(tmp_path):
    """Curated (flag=1) IHC 1+ beats uncurated (flag=0) IHC 3+."""
    con = _empty_con()
    _add_her2(con, "P1", "IHC 3+", report_date="2020-05-01", flag=0)  # uncurated
    _add_her2(con, "P1", "IHC 1+", report_date="2020-05-01", flag=1)  # curated
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "low"


def test_specific_variant_beats_null_variant(tmp_path):
    """Non-NULL variant (IHC 3+) beats NULL variant when curation flags tie."""
    con = _empty_con()
    _add_her2(con, "P1", None, report_date="2020-05-01", flag=1)  # NULL variant
    _add_her2(con, "P1", "IHC 3+", report_date="2020-05-01", flag=1)  # specific
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "positive"


def test_no_her2_in_window_returns_unknown(tmp_path):
    """Patient with no HER2 record in window gets her2_category = unknown."""
    con = _empty_con()
    result = derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["her2_category"] == "unknown"
    assert result.iloc[0]["n_her2_in_window"] == 0


def test_output_written_to_csv(tmp_path):
    con = _empty_con()
    _add_her2(con, "P1", "IHC 3+")
    derive_her2(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert (tmp_path / "patient_her2.csv").exists()

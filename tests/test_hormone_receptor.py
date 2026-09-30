"""Tests for hormone_receptor.py — HR status derivation.

Each test builds a minimal in-memory DuckDB fixture with one hand-crafted
patient per decision branch.

ADRs covered: ADR-009 (HR derivation)
"""

from __future__ import annotations

import duckdb
import pandas as pd

from her2rwd.hormone_receptor import derive_hr

_CFG = {
    "hr": {
        "positive_threshold_pct": 1,
        "er_low_max_pct": 10,
        "pct_beats_result_text": True,
        "null_variant_fallback": "result_text",
    },
    "her2": {
        "window_days": {"pre_index": 365, "post_index": 90},
    },
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


def _add_bm(con, pid, name, variant, result="Positive", report_date="2020-04-01", flag=1):
    v = "NULL" if variant is None else f"'{variant}'"
    con.execute(
        f"INSERT INTO biomarker VALUES ('{pid}', '{report_date}', '{name}', " f"'IHC', '{result}', {v}, {flag})"
    )


# ── HR+ from numeric % ────────────────────────────────────────────────────────


def test_er_pct_above_threshold_is_positive(tmp_path):
    con = _empty_con()
    _add_bm(con, "P1", "ER", "52% positive cells", result="Positive")
    result = derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["hr_status"] == "positive"
    assert result.iloc[0]["er_pct"] == 52


def test_pr_pct_above_threshold_drives_hr_positive(tmp_path):
    """HR+ if PR >= 1% even when ER = 0%."""
    con = _empty_con()
    _add_bm(con, "P1", "ER", "0% positive cells", result="Negative")
    _add_bm(con, "P1", "PR", "5% positive cells", result="Positive")
    result = derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["hr_status"] == "positive"


def test_both_zero_pct_is_negative(tmp_path):
    con = _empty_con()
    _add_bm(con, "P1", "ER", "0% positive cells", result="Negative")
    _add_bm(con, "P1", "PR", "0% positive cells", result="Negative")
    result = derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["hr_status"] == "negative"


# ── HR from result text fallback (ADR-009) ────────────────────────────────────


def test_null_variant_positive_result_is_hr_positive(tmp_path):
    """No ER %; result = 'Positive' → HR+ via text fallback."""
    con = _empty_con()
    _add_bm(con, "P1", "ER", None, result="Positive")
    result = derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["hr_status"] == "positive"
    assert result.iloc[0]["hr_source"] == "result_text"


def test_null_variant_negative_result_is_hr_negative(tmp_path):
    con = _empty_con()
    _add_bm(con, "P1", "ER", None, result="Negative")
    _add_bm(con, "P1", "PR", None, result="Negative")
    result = derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["hr_status"] == "negative"
    assert result.iloc[0]["hr_source"] == "result_text"


# ── ER-low flag (ADR-009) ─────────────────────────────────────────────────────


def test_er_1pct_is_er_low(tmp_path):
    """ER = 1% is HR+ and ER-low."""
    con = _empty_con()
    _add_bm(con, "P1", "ER", "1% positive cells", result="Positive")
    result = derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["hr_status"] == "positive"
    assert result.iloc[0]["er_low"]


def test_er_10pct_is_er_low(tmp_path):
    """ER = 10% is within ER-low range."""
    con = _empty_con()
    _add_bm(con, "P1", "ER", "10% positive cells", result="Positive")
    result = derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["er_low"]


def test_er_11pct_is_not_er_low(tmp_path):
    """ER = 11% is HR+ but not ER-low."""
    con = _empty_con()
    _add_bm(con, "P1", "ER", "11% positive cells", result="Positive")
    result = derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["hr_status"] == "positive"
    assert not result.iloc[0]["er_low"]


def test_no_hr_record_is_unknown(tmp_path):
    """Patient with no ER/PR record in window gets hr_status = unknown."""
    con = _empty_con()
    result = derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert result.iloc[0]["hr_status"] == "unknown"


def test_output_written_to_csv(tmp_path):
    con = _empty_con()
    _add_bm(con, "P1", "ER", "50% positive cells")
    derive_hr(con, _cohort("P1"), _CFG, out_dir=tmp_path)
    assert (tmp_path / "patient_hr.csv").exists()

"""Tests for src/her2rwd/treatment.py.

One tiny hand-made patient case per decision branch.
Uses in-memory DuckDB — no mocks, no file I/O beyond tmp_path.
ADR-010.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from her2rwd.treatment import build_treatment_lines

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def cfg():
    return {
        "treatment": {
            "regimen_window_days": 28,
            "new_line_gap_days": 90,
            "enhertu_generic_name": "trastuzumab deruxtecan",
            "drug_class_map": {
                "trastuzumab deruxtecan": "her2_adc",
                "trastuzumab": "her2_mab",
                "pertuzumab": "her2_mab",
                "palbociclib": "cdk46i",
                "anastrozole": "endocrine",
                "paclitaxel": "chemo",
            },
        }
    }


_MED_COLS = [
    "patient_id",
    "med_generic_name",
    "med_brand_name",
    "med_date",
    "med_status",
    "curation_flag",
]


def _make_con(med_rows: list[dict], cohort_rows: list[dict]) -> duckdb.DuckDBPyConnection:
    """Build an in-memory DuckDB with medication and cohort tables."""
    con = duckdb.connect()
    if med_rows:
        med_df = pd.DataFrame(med_rows)
    else:
        med_df = pd.DataFrame(columns=_MED_COLS).astype({"med_date": "datetime64[ns]", "curation_flag": int})
    cohort_df = pd.DataFrame(cohort_rows)
    con.register("medication", med_df)
    return con, cohort_df


def _cohort(pid="P1", index_date="2020-01-01"):
    return {"patient_id": pid, "index_date": pd.Timestamp(index_date)}


def _med(pid="P1", drug="paclitaxel", date_str="2020-01-15", flag=1):
    return {
        "patient_id": pid,
        "med_generic_name": drug,
        "med_brand_name": drug,
        "med_date": pd.Timestamp(date_str),
        "med_status": "completed",
        "curation_flag": flag,
    }


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestSingleDrug:
    def test_single_drug_is_line_1(self, cfg, tmp_path):
        con, cohort = _make_con([_med()], [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert len(df) == 1
        assert df.iloc[0]["line_number"] == 1

    def test_days_from_index_computed(self, cfg, tmp_path):
        con, cohort = _make_con([_med(date_str="2020-02-01")], [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert df.iloc[0]["days_from_index"] == 31

    def test_pre_index_drug_excluded(self, cfg, tmp_path):
        """Drug before index date must not appear in output."""
        con, cohort = _make_con(
            [_med(date_str="2019-12-01")],  # before index 2020-01-01
            [_cohort()],
        )
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert len(df) == 0


class TestRegimenGrouping:
    def test_two_drugs_within_28d_same_regimen_same_line(self, cfg, tmp_path):
        meds = [
            _med(drug="paclitaxel", date_str="2020-01-15"),
            _med(drug="trastuzumab", date_str="2020-02-01"),
        ]  # 17d gap
        con, cohort = _make_con(meds, [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert len(df) == 1
        assert df.iloc[0]["line_number"] == 1
        assert "paclitaxel" in df.iloc[0]["regimen_drugs"]
        assert "trastuzumab" in df.iloc[0]["regimen_drugs"]

    def test_two_drugs_beyond_28d_different_regimens(self, cfg, tmp_path):
        meds = [
            _med(drug="paclitaxel", date_str="2020-01-15"),
            _med(drug="trastuzumab", date_str="2020-02-20"),
        ]  # 36d gap
        con, cohort = _make_con(meds, [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        # Two regimens but gap = 36d < 90d → same line
        assert len(df) == 1
        assert df.iloc[0]["line_number"] == 1

    def test_exact_window_boundary_inclusive(self, cfg, tmp_path):
        """Gap exactly == window (28d) → same regimen."""
        meds = [
            _med(drug="paclitaxel", date_str="2020-01-01"),
            _med(drug="trastuzumab", date_str="2020-01-29"),
        ]  # exactly 28d
        con, cohort = _make_con(meds, [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert len(df) == 1
        assert "paclitaxel" in df.iloc[0]["regimen_drugs"]
        assert "trastuzumab" in df.iloc[0]["regimen_drugs"]


class TestLineAssignment:
    def test_gap_less_than_90d_same_line(self, cfg, tmp_path):
        meds = [
            _med(drug="paclitaxel", date_str="2020-01-15"),
            _med(drug="trastuzumab", date_str="2020-04-01"),
        ]  # 77d gap
        con, cohort = _make_con(meds, [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert len(df) == 1
        assert df.iloc[0]["line_number"] == 1

    def test_gap_greater_than_90d_new_line(self, cfg, tmp_path):
        meds = [
            _med(drug="paclitaxel", date_str="2020-01-15"),
            _med(drug="trastuzumab deruxtecan", date_str="2020-05-01"),
        ]  # 107d gap
        con, cohort = _make_con(meds, [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert len(df) == 2
        assert df.iloc[0]["line_number"] == 1
        assert df.iloc[1]["line_number"] == 2

    def test_three_lines_sequential(self, cfg, tmp_path):
        meds = [
            _med(drug="paclitaxel", date_str="2020-01-15"),
            _med(drug="trastuzumab deruxtecan", date_str="2020-05-01"),  # +107d → line 2
            _med(drug="anastrozole", date_str="2020-09-01"),  # +123d → line 3
        ]
        con, cohort = _make_con(meds, [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert len(df) == 3
        assert list(df["line_number"]) == [1, 2, 3]


class TestEnhertu:
    def test_enhertu_flagged(self, cfg, tmp_path):
        con, cohort = _make_con(
            [_med(drug="trastuzumab deruxtecan", date_str="2020-03-01")],
            [_cohort()],
        )
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert df.iloc[0]["contains_enhertu"]

    def test_non_enhertu_not_flagged(self, cfg, tmp_path):
        con, cohort = _make_con([_med(drug="paclitaxel")], [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert not df.iloc[0]["contains_enhertu"]

    def test_enhertu_in_line_2_contains_enhertu_true(self, cfg, tmp_path):
        meds = [
            _med(drug="paclitaxel", date_str="2020-01-15"),
            _med(drug="trastuzumab deruxtecan", date_str="2020-05-01"),
        ]
        con, cohort = _make_con(meds, [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        line2 = df[df["line_number"] == 2]
        assert line2.iloc[0]["contains_enhertu"]


class TestDeduplication:
    def test_duplicate_drug_same_date_collapsed(self, cfg, tmp_path):
        meds = [
            _med(drug="paclitaxel", date_str="2020-01-15", flag=0),
            _med(drug="paclitaxel", date_str="2020-01-15", flag=1),
        ]
        con, cohort = _make_con(meds, [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert len(df) == 1
        assert df.iloc[0]["n_drugs_in_line"] == 1  # paclitaxel only once


class TestOutput:
    def test_csv_written(self, cfg, tmp_path):
        con, cohort = _make_con([_med()], [_cohort()])
        build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert (tmp_path / "patient_lines.csv").exists()

    def test_no_meds_returns_empty_df(self, cfg, tmp_path):
        con, cohort = _make_con([], [_cohort()])
        df = build_treatment_lines(con, cohort, cfg, out_dir=tmp_path)
        assert len(df) == 0
        assert (tmp_path / "patient_lines.csv").exists()

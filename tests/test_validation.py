"""Tests for validation.py — pipeline invariant checks.

Each test sets up minimal CSV outputs to drive one specific PASS or FAIL branch.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from her2rwd.validation import run_validation

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _write_valid_outputs(tmp_path: Path) -> dict[str, Path]:
    """Write minimal valid pipeline outputs to tmp_path and return paths."""
    tbl = tmp_path / "tables"
    tbl.mkdir(parents=True)
    dq = tmp_path / "dq"
    dq.mkdir()

    # cohort — 5 patients, index_date after dob
    cohort = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4", "P5"],
            "index_date": ["2020-01-01"] * 5,
            "date_of_birth": ["1960-01-01"] * 5,
            "disease_type": ["de_novo"] * 5,
        }
    )
    cohort.to_csv(tbl / "cohort.csv", index=False)

    # attrition — starts at 150, ends at 5
    attrition = pd.DataFrame(
        {
            "step": [1, 2],
            "step_label": ["All patients", "Eligible"],
            "n_in": [150, 150],
            "n_excluded": [0, 145],
            "n_remaining": [150, 5],
        }
    )
    attrition.to_csv(tbl / "attrition.csv", index=False)

    # patient_her2 — all valid categories
    her2 = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4", "P5"],
            "her2_category": ["positive", "low", "ultralow", "null", "unknown"],
            "her2_variant": [
                "IHC 3+",
                "IHC 1+",
                "IHC 0 with faint membrane staining in <=10% cells",
                "IHC 0",
                "Pending",
            ],
            "her2_curation_flag": [1, 0, 1, 0, 0],
        }
    )
    her2.to_csv(tbl / "patient_her2.csv", index=False)

    # patient_hr
    hr = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4", "P5"],
            "hr_status": ["positive", "negative", "unknown", "positive", "unknown"],
        }
    )
    hr.to_csv(tbl / "patient_hr.csv", index=False)

    # q1_overall — pcts sum to 100
    q1 = pd.DataFrame(
        {
            "her2_category": ["positive", "low", "ultralow", "null", "unknown"],
            "n": [1, 1, 1, 1, 1],
            "pct": [20.0, 20.0, 20.0, 20.0, 20.0],
            "ci_lo": [5.0] * 5,
            "ci_hi": [50.0] * 5,
            "small_cell": [True, True, True, True, True],
        }
    )
    q1.to_csv(tbl / "q1_overall.csv", index=False)

    # q2_subindication_assignment — one row per cohort patient
    q2 = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4", "P5"],
            "subindication": [
                "her2_positive",
                "hr_neg_her2_low",
                "hr_pos_her2_ultralow",
                "her2_null",
                "her2_unknown",
            ],
        }
    )
    q2.to_csv(tbl / "q2_subindication_assignment.csv", index=False)

    # patient_lines — only P1 has enhertu
    lines = pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2"],
            "line_number": [1, 2, 1],
            "contains_enhertu": [True, False, False],
            "regimen_drugs": ["trastuzumab deruxtecan", "paclitaxel", "paclitaxel"],
        }
    )
    lines.to_csv(tbl / "patient_lines.csv", index=False)

    # discordance tables — P1 has enhertu
    disc_unk = pd.DataFrame(
        {
            "patient_id": ["P1"],
            "subindication": ["her2_unknown"],
            "hr_status": ["positive"],
            "enhertu_line": [1.0],
        }
    )
    disc_unk.to_csv(tbl / "q2_discordance_unknown_her2.csv", index=False)

    disc_1l = pd.DataFrame(columns=["patient_id", "subindication", "hr_status", "enhertu_line"])
    disc_1l.to_csv(tbl / "q2_discordance_1l.csv", index=False)

    return {"tbl": tbl, "dq": dq}


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_all_pass_on_valid_outputs(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    audit = tmp_path / "audit"
    df = run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))
    assert (df["result"] == "PASS").all(), df[df["result"] == "FAIL"][["check", "detail"]].to_string()


def test_validation_report_written(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    audit = tmp_path / "audit"
    run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))
    assert (audit / "validation_report.md").exists()
    content = (audit / "validation_report.md").read_text()
    assert "ALL PASS" in content


def test_attrition_wrong_start_fails(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    # Overwrite attrition with wrong starting n_in
    atr = pd.read_csv(paths["tbl"] / "attrition.csv")
    atr.loc[0, "n_in"] = 100  # should be 150
    atr.to_csv(paths["tbl"] / "attrition.csv", index=False)
    audit = tmp_path / "audit"
    with pytest.raises(RuntimeError, match="attrition_starts_at_150"):
        run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))


def test_attrition_final_mismatch_fails(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    # Add extra patient to cohort so sizes mismatch
    cohort = pd.read_csv(paths["tbl"] / "cohort.csv")
    extra = pd.DataFrame(
        {
            "patient_id": ["P6"],
            "index_date": ["2020-01-01"],
            "date_of_birth": ["1960-01-01"],
            "disease_type": ["de_novo"],
        }
    )
    pd.concat([cohort, extra]).to_csv(paths["tbl"] / "cohort.csv", index=False)
    audit = tmp_path / "audit"
    with pytest.raises(RuntimeError, match="attrition_final_matches_cohort"):
        run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))


def test_duplicate_patient_ids_fails(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    cohort = pd.read_csv(paths["tbl"] / "cohort.csv")
    dup = pd.concat([cohort, cohort.iloc[[0]]])  # duplicate P1
    dup.to_csv(paths["tbl"] / "cohort.csv", index=False)
    # fix attrition to match new count
    atr = pd.read_csv(paths["tbl"] / "attrition.csv")
    atr.loc[atr.index[-1], "n_remaining"] = 6
    atr.to_csv(paths["tbl"] / "attrition.csv", index=False)
    audit = tmp_path / "audit"
    with pytest.raises(RuntimeError, match="cohort_no_duplicate_ids"):
        run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))


def test_invalid_her2_category_fails(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    her2 = pd.read_csv(paths["tbl"] / "patient_her2.csv")
    her2.loc[0, "her2_category"] = "invalid_cat"
    her2.to_csv(paths["tbl"] / "patient_her2.csv", index=False)
    audit = tmp_path / "audit"
    with pytest.raises(RuntimeError, match="her2_categories_valid"):
        run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))


def test_q1_pcts_not_summing_to_100_fails(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    q1 = pd.read_csv(paths["tbl"] / "q1_overall.csv")
    q1.loc[0, "pct"] = 99.9  # sum will be 119.9
    q1.to_csv(paths["tbl"] / "q1_overall.csv", index=False)
    audit = tmp_path / "audit"
    with pytest.raises(RuntimeError, match="q1_pcts_sum_to_100"):
        run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))


def test_index_date_before_dob_fails(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    cohort = pd.read_csv(paths["tbl"] / "cohort.csv")
    cohort.loc[0, "index_date"] = "1950-01-01"  # before dob 1960
    cohort.to_csv(paths["tbl"] / "cohort.csv", index=False)
    audit = tmp_path / "audit"
    with pytest.raises(RuntimeError, match="index_date_after_dob"):
        run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))


def test_discordance_not_in_cohort_fails(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    disc = pd.read_csv(paths["tbl"] / "q2_discordance_unknown_her2.csv")
    disc.loc[0, "patient_id"] = "GHOST"  # not in cohort
    disc.to_csv(paths["tbl"] / "q2_discordance_unknown_her2.csv", index=False)
    # Make GHOST appear to have enhertu
    lines = pd.read_csv(paths["tbl"] / "patient_lines.csv")
    ghost = pd.DataFrame(
        {
            "patient_id": ["GHOST"],
            "line_number": [1],
            "contains_enhertu": [True],
            "regimen_drugs": ["trastuzumab deruxtecan"],
        }
    )
    pd.concat([lines, ghost]).to_csv(paths["tbl"] / "patient_lines.csv", index=False)
    audit = tmp_path / "audit"
    with pytest.raises(RuntimeError, match="discordance_ids_in_cohort"):
        run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))


def test_discordance_without_enhertu_fails(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    # P2 is in cohort but did not receive enhertu
    disc = pd.read_csv(paths["tbl"] / "q2_discordance_unknown_her2.csv")
    disc.loc[0, "patient_id"] = "P2"
    disc.to_csv(paths["tbl"] / "q2_discordance_unknown_her2.csv", index=False)
    audit = tmp_path / "audit"
    with pytest.raises(RuntimeError, match="discordance_received_enhertu"):
        run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))


def test_her2_count_mismatch_fails(tmp_path):
    paths = _write_valid_outputs(tmp_path)
    her2 = pd.read_csv(paths["tbl"] / "patient_her2.csv")
    her2.iloc[:-1].to_csv(paths["tbl"] / "patient_her2.csv", index=False)
    audit = tmp_path / "audit"
    with pytest.raises(RuntimeError, match="her2_count_matches_cohort"):
        run_validation(out_dir=str(paths["tbl"]), audit_dir=str(audit))

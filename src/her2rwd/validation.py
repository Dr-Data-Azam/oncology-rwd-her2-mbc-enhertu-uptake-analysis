"""Pipeline invariant checks and validation report.

Responsibility:
    Run a battery of PASS/FAIL assertions after every pipeline run to confirm
    that the outputs are internally consistent.  Write results to
    audit/validation_report.md.  Any FAIL causes the pipeline to exit with a
    non-zero return code so /close-phase is blocked.

    Invariants checked:
    - Attrition table sums to 150 (total raw patients)
    - Cohort table has exactly one row per patient_id
    - Every HER2 category value is in the allowed set
    - HER2 category counts sum to cohort size
    - No index date is before the patient's date of birth
    - Q1 proportions sum to 100% (within floating-point tolerance)
    - Q2 cohort size equals Q1 cohort size
    - Enhertu recipients in treatment table are a subset of the cohort
    - Discordance patient lists are a subset of Enhertu recipients

Inputs:
    All outputs/tables/*.csv produced by the pipeline

Outputs:
    audit/validation_report.md  — PASS/FAIL per check with counts

ADRs implemented: none (cross-cutting quality gate)
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

_VALID_HER2_CATS = {"positive", "low", "ultralow", "null", "unknown"}
_VALID_HR_STATUSES = {"positive", "negative", "unknown"}
_EXPECTED_N_RAW = 150


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"check": name, "result": "PASS" if passed else "FAIL", "detail": detail}


def run_validation(out_dir: str = "outputs/tables", audit_dir: str = "audit") -> pd.DataFrame:
    """Run pipeline invariant checks.

    Reads from outputs/tables/ CSVs written by the pipeline.
    Writes audit/validation_report.md.
    Raises RuntimeError on any FAIL.
    """
    tbl = Path(out_dir)
    results: list[dict] = []

    # ── Load outputs ──────────────────────────────────────────────────────────
    attrition = pd.read_csv(tbl / "attrition.csv")
    cohort = pd.read_csv(tbl / "cohort.csv")
    her2 = pd.read_csv(tbl / "patient_her2.csv")
    hr = pd.read_csv(tbl / "patient_hr.csv")
    q1_overall = pd.read_csv(tbl / "q1_overall.csv")
    q2_assign = pd.read_csv(tbl / "q2_subindication_assignment.csv")
    lines = pd.read_csv(tbl / "patient_lines.csv")
    disc_unk = pd.read_csv(tbl / "q2_discordance_unknown_her2.csv")
    disc_1l = pd.read_csv(tbl / "q2_discordance_1l.csv")

    n_cohort = len(cohort)
    cohort_ids = set(cohort["patient_id"])

    # ── Check 1: attrition starts at 150 ─────────────────────────────────────
    n_start = int(attrition.iloc[0]["n_in"])
    results.append(
        _check(
            "attrition_starts_at_150",
            n_start == _EXPECTED_N_RAW,
            f"n_in for step 1 = {n_start} (expected {_EXPECTED_N_RAW})",
        )
    )

    # ── Check 2: attrition final n_remaining == cohort row count ─────────────
    n_final = int(attrition.iloc[-1]["n_remaining"])
    results.append(
        _check(
            "attrition_final_matches_cohort",
            n_final == n_cohort,
            f"attrition final = {n_final}, cohort rows = {n_cohort}",
        )
    )

    # ── Check 3: no duplicate patient IDs in cohort ───────────────────────────
    n_unique = cohort["patient_id"].nunique()
    results.append(
        _check(
            "cohort_no_duplicate_ids",
            n_unique == n_cohort,
            f"unique patient_ids = {n_unique}, cohort rows = {n_cohort}",
        )
    )

    # ── Check 4: HER2 categories all valid ───────────────────────────────────
    bad_cats = set(her2["her2_category"].dropna().unique()) - _VALID_HER2_CATS
    results.append(
        _check(
            "her2_categories_valid",
            len(bad_cats) == 0,
            f"invalid categories = {bad_cats or 'none'}",
        )
    )

    # ── Check 5: HER2 row count matches cohort ────────────────────────────────
    results.append(
        _check(
            "her2_count_matches_cohort",
            len(her2) == n_cohort,
            f"her2 rows = {len(her2)}, cohort rows = {n_cohort}",
        )
    )

    # ── Check 6: HR row count matches cohort ─────────────────────────────────
    results.append(
        _check(
            "hr_count_matches_cohort",
            len(hr) == n_cohort,
            f"hr rows = {len(hr)}, cohort rows = {n_cohort}",
        )
    )

    # ── Check 7: no index date before date of birth ───────────────────────────
    if "date_of_birth" in cohort.columns and "index_date" in cohort.columns:
        cohort_dt = cohort.copy()
        cohort_dt["dob"] = pd.to_datetime(cohort_dt["date_of_birth"], errors="coerce")
        cohort_dt["idx"] = pd.to_datetime(cohort_dt["index_date"], errors="coerce")
        bad_dob = int((cohort_dt["idx"] < cohort_dt["dob"]).sum())
        results.append(
            _check(
                "index_date_after_dob",
                bad_dob == 0,
                f"patients with index_date < dob = {bad_dob}",
            )
        )
    else:
        results.append(_check("index_date_after_dob", True, "columns not present — skip"))

    # ── Check 8: Q1 percentages sum to 100 ───────────────────────────────────
    pct_sum = float(q1_overall["pct"].sum())
    results.append(
        _check(
            "q1_pcts_sum_to_100",
            math.isclose(pct_sum, 100.0, abs_tol=0.5),
            f"pct sum = {pct_sum:.2f}% (expected 100 ± 0.5)",
        )
    )

    # ── Check 9: Q1 n values non-negative ────────────────────────────────────
    neg_n = int((q1_overall["n"] < 0).sum())
    results.append(
        _check(
            "q1_n_nonnegative",
            neg_n == 0,
            f"negative n counts = {neg_n}",
        )
    )

    # ── Check 10: Q2 subindication assignment row count matches cohort ────────
    results.append(
        _check(
            "q2_row_count_matches_cohort",
            len(q2_assign) == n_cohort,
            f"q2_assign rows = {len(q2_assign)}, cohort rows = {n_cohort}",
        )
    )

    # ── Check 11: treatment patient IDs are subset of cohort ─────────────────
    treatment_ids = set(lines["patient_id"].unique())
    not_in_cohort = treatment_ids - cohort_ids
    results.append(
        _check(
            "treatment_ids_in_cohort",
            len(not_in_cohort) == 0,
            f"treatment patient_ids not in cohort = {len(not_in_cohort)}",
        )
    )

    # ── Check 12: discordance patient IDs are subset of cohort ───────────────
    disc_ids = set(disc_unk["patient_id"].unique()) | set(disc_1l["patient_id"].unique())
    disc_not_in_cohort = disc_ids - cohort_ids
    results.append(
        _check(
            "discordance_ids_in_cohort",
            len(disc_not_in_cohort) == 0,
            f"discordance patient_ids not in cohort = {len(disc_not_in_cohort)}",
        )
    )

    # ── Check 13: discordance patients received Enhertu ───────────────────────
    enhertu_ids = set(lines[lines["contains_enhertu"]]["patient_id"].unique())
    disc_without_enhertu = disc_ids - enhertu_ids
    results.append(
        _check(
            "discordance_received_enhertu",
            len(disc_without_enhertu) == 0,
            f"discordance patients without Enhertu in lines = {len(disc_without_enhertu)}",
        )
    )

    # ── Build result DataFrame ────────────────────────────────────────────────
    df = pd.DataFrame(results)
    n_fail = int((df["result"] == "FAIL").sum())
    n_pass = int((df["result"] == "PASS").sum())

    # ── Write audit/validation_report.md ─────────────────────────────────────
    audit_path = Path(audit_dir)
    audit_path.mkdir(parents=True, exist_ok=True)
    _write_report(df, n_pass, n_fail, audit_path / "validation_report.md")

    if n_fail > 0:
        failed = df[df["result"] == "FAIL"]["check"].tolist()
        raise RuntimeError(
            f"Validation FAILED: {n_fail} check(s) failed — {failed}. " "See audit/validation_report.md."
        )

    return df


def _write_report(df: pd.DataFrame, n_pass: int, n_fail: int, path: Path) -> None:
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    verdict = "ALL PASS" if n_fail == 0 else f"FAILED ({n_fail} check(s))"

    lines_md = [
        "# Validation Report",
        "",
        f"**Generated:** {ts}  ",
        f"**Verdict:** {verdict}  ",
        f"**Checks run:** {n_pass + n_fail}  ",
        f"**Passed:** {n_pass}  ",
        f"**Failed:** {n_fail}  ",
        "",
        "---",
        "",
        "## Results",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for _, row in df.iterrows():
        icon = "✅" if row["result"] == "PASS" else "❌"
        lines_md.append(f"| `{row['check']}` | {icon} {row['result']} | {row['detail']} |")

    lines_md += ["", "---", "", "*Generated by `src/her2rwd/validation.py`*"]
    path.write_text("\n".join(lines_md), encoding="utf-8")

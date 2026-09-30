"""Question 2: Enhertu uptake vs competitors by HER2-defined subindication.

Responsibility:
    Assign each cohort patient to a subindication (HER2+, HR+/HER2-low,
    HR-/HER2-low, HR+/HER2-ultralow, and exploratory groups) using the
    framework in ADR-011. For each subindication report: n, % receiving
    Enhertu with Wilson CI, line of therapy at first Enhertu, top competing
    drug classes. Identify discordant cases per ADR-013.

Subindication assignment logic (ADR-011):
    her2_positive (any HR)              → her2_positive
    her2_low + HR-positive              → hr_pos_her2_low
    her2_low + HR-negative              → hr_neg_her2_low
    her2_low + HR-unknown               → her2_low_hr_unknown
    her2_ultralow + HR-positive         → hr_pos_her2_ultralow
    her2_ultralow + HR-negative         → hr_neg_her2_ultralow
    her2_ultralow + HR-unknown          → her2_ultralow_hr_unknown
    her2_null                           → her2_null
    her2_unknown                        → her2_unknown

Discordance definitions (ADR-013):
    enhertu_in_her2_unknown: Enhertu given to patient with no HER2 test in window
    enhertu_in_line_1: Enhertu given as 1L therapy (investigational; not yet SoC)

Outputs:
    q2_subindication_assignment.csv  — patient_id, subindication
    q2_uptake_summary.csv            — subindication × uptake metrics + Wilson CI
    q2_enhertu_by_line.csv           — subindication × line_number × n_patients
    q2_competitor_map.csv            — subindication × drug_class × n_patients
    q2_discordance_unknown_her2.csv  — patients: Enhertu + no HER2 test
    q2_discordance_1l.csv            — patients: Enhertu in Line 1

ADRs implemented: ADR-011, ADR-012 (statistics), ADR-013
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from her2rwd.statistics import wilson_ci

# Canonical order for display
_REQUIRED_SUBIND = [
    "her2_positive",
    "hr_pos_her2_low",
    "hr_neg_her2_low",
    "hr_pos_her2_ultralow",
]
_EXPLORATORY_SUBIND = [
    "her2_null",
    "her2_unknown",
]


def _assign_subindication(her2_cat: str, hr_status: str) -> str:
    """Map (her2_category, hr_status) → named clinical subindication. ADR-011."""
    if her2_cat == "positive":
        return "her2_positive"
    if her2_cat == "low":
        if hr_status == "positive":
            return "hr_pos_her2_low"
        if hr_status == "negative":
            return "hr_neg_her2_low"
        return "her2_low_hr_unknown"
    if her2_cat == "ultralow":
        if hr_status == "positive":
            return "hr_pos_her2_ultralow"
        if hr_status == "negative":
            return "hr_neg_her2_ultralow"
        return "her2_ultralow_hr_unknown"
    if her2_cat == "null":
        return "her2_null"
    return "her2_unknown"


def compute_q2(
    her2_df: pd.DataFrame,
    hr_df: pd.DataFrame,
    lines_df: pd.DataFrame,
    cohort_df: pd.DataFrame,
    cfg: dict,
    out_dir: str | Path = "outputs/tables",
) -> dict[str, pd.DataFrame]:
    """Compute Q2 Enhertu uptake and discordance tables.

    ADRs implemented: ADR-011, ADR-012, ADR-013.
    """
    threshold = cfg["stats"]["small_cell_threshold"]
    z = cfg["stats"].get("ci_z", 1.96)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # ── Build patient-level base table ────────────────────────────────────────
    base = (
        cohort_df[["patient_id"]]
        .merge(her2_df[["patient_id", "her2_category"]], on="patient_id", how="left")
        .merge(hr_df[["patient_id", "hr_status"]], on="patient_id", how="left")
    )
    base["subindication"] = base.apply(
        lambda r: _assign_subindication(
            str(r["her2_category"]) if pd.notna(r["her2_category"]) else "unknown",
            str(r["hr_status"]) if pd.notna(r["hr_status"]) else "unknown",
        ),
        axis=1,
    )

    # First Enhertu line per patient
    if len(lines_df) > 0 and "contains_enhertu" in lines_df.columns:
        enhertu_first = (
            lines_df[lines_df["contains_enhertu"]]
            .groupby("patient_id")["line_number"]
            .min()
            .reset_index()
            .rename(columns={"line_number": "enhertu_line"})
        )
    else:
        enhertu_first = pd.DataFrame(columns=["patient_id", "enhertu_line"])

    base = base.merge(enhertu_first, on="patient_id", how="left")
    base["got_enhertu"] = base["enhertu_line"].notna()
    base["days_from_index_to_enhertu"] = None  # populated below if timing data available

    # ── Subindication assignment CSV ──────────────────────────────────────────
    assign_df = base[["patient_id", "subindication", "got_enhertu", "enhertu_line"]].copy()
    assign_df.to_csv(out_path / "q2_subindication_assignment.csv", index=False)

    # ── Uptake summary per subindication ──────────────────────────────────────
    all_subind = _REQUIRED_SUBIND + _EXPLORATORY_SUBIND
    uptake_rows = []
    for subind in all_subind:
        grp = base[base["subindication"] == subind]
        n_total = len(grp)
        n_enhertu = int(grp["got_enhertu"].sum())
        pct = round(n_enhertu / n_total * 100, 1) if n_total > 0 else 0.0
        lo, hi = wilson_ci(n_enhertu, n_total, z)
        uptake_rows.append(
            {
                "subindication": subind,
                "subindication_type": "required" if subind in _REQUIRED_SUBIND else "exploratory",
                "n_total": n_total,
                "n_enhertu": n_enhertu,
                "pct_enhertu": pct,
                "ci_lo": round(lo * 100, 1),
                "ci_hi": round(hi * 100, 1),
                "small_cell": n_total < threshold,
            }
        )
    uptake_df = pd.DataFrame(uptake_rows)
    uptake_df.to_csv(out_path / "q2_uptake_summary.csv", index=False)

    # ── Enhertu by line per subindication ─────────────────────────────────────
    enhertu_pts = base[base["got_enhertu"]].copy()
    enhertu_pts["line_label"] = enhertu_pts["enhertu_line"].apply(
        lambda x: "1L" if x == 1 else ("2L" if x == 2 else "3L+")
    )
    by_line_rows = []
    for subind in all_subind:
        for ll in ["1L", "2L", "3L+"]:
            n = int(((enhertu_pts["subindication"] == subind) & (enhertu_pts["line_label"] == ll)).sum())
            by_line_rows.append(
                {
                    "subindication": subind,
                    "line_label": ll,
                    "n_patients": n,
                    "small_cell": n < threshold,
                }
            )
    by_line_df = pd.DataFrame(by_line_rows)
    by_line_df.to_csv(out_path / "q2_enhertu_by_line.csv", index=False)

    # ── Competitor map (all drug classes per subindication) ───────────────────
    if len(lines_df) > 0:
        lines_w_subind = lines_df.merge(base[["patient_id", "subindication"]], on="patient_id", how="left")
        competitor_rows = []
        for subind in all_subind:
            grp = lines_w_subind[lines_w_subind["subindication"] == subind]
            if grp.empty:
                continue
            class_counts = (
                grp.assign(drug_class=grp["drug_classes"].str.split(", "))
                .explode("drug_class")
                .groupby("drug_class")["patient_id"]
                .nunique()
                .reset_index()
                .rename(columns={"patient_id": "n_patients"})
            )
            class_counts["subindication"] = subind
            class_counts["small_cell"] = class_counts["n_patients"] < threshold
            competitor_rows.append(class_counts)
        comp_df = pd.concat(competitor_rows, ignore_index=True) if competitor_rows else pd.DataFrame()
    else:
        comp_df = pd.DataFrame()
    comp_df.to_csv(out_path / "q2_competitor_map.csv", index=False)

    # ── Discordance: Enhertu in HER2-unknown (ADR-013) ────────────────────────
    discord_unknown = base[(base["got_enhertu"]) & (base["subindication"] == "her2_unknown")][
        ["patient_id", "subindication", "hr_status", "enhertu_line"]
    ].reset_index(drop=True)
    discord_unknown.to_csv(out_path / "q2_discordance_unknown_her2.csv", index=False)

    # ── Discordance: Enhertu in Line 1 (ADR-013) ─────────────────────────────
    discord_1l = base[(base["got_enhertu"]) & (base["enhertu_line"] == 1)][
        ["patient_id", "subindication", "hr_status", "enhertu_line"]
    ].reset_index(drop=True)
    discord_1l.to_csv(out_path / "q2_discordance_1l.csv", index=False)

    return {
        "assignment": assign_df,
        "uptake_summary": uptake_df,
        "by_line": by_line_df,
        "competitor_map": comp_df,
        "discordance_unknown_her2": discord_unknown,
        "discordance_1l": discord_1l,
    }

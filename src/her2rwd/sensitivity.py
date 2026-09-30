"""Sensitivity analyses — pipeline re-runs under alternative rule sets.

Responsibility:
    Re-run the HER2 classification and Q1/Q2 outputs under alternative
    rule configurations and produce side-by-side comparison tables.

    Three sensitivity scenarios (S1–S3):
        S1: Narrow biomarker window — pre_index reduced from 365 to 180 days
        S2: Curated-only records — only curation_flag=1 biomarker records used
        S3: Conservative IHC-0 — plain "IHC 0" mapped to unknown (not null)

    The baseline (primary run) is column 0.

Inputs:
    DuckDB connection (from load_raw)
    cohort_df (from build_cohort)
    cfg (from analysis_rules.yaml)

Outputs:
    outputs/tables/sensitivity_her2_distribution.csv  — Q1 under S1/S2/S3
    outputs/tables/sensitivity_uptake.csv             — Q2 Enhertu uptake counts

ADRs implemented: ADR-007 (window sensitivity), ADR-006 (IHC-0 sensitivity)
"""

from __future__ import annotations

import copy
from pathlib import Path

import pandas as pd

from her2rwd.her2 import derive_her2
from her2rwd.hormone_receptor import derive_hr
from her2rwd.q1_distribution import compute_q1
from her2rwd.q2_uptake import compute_q2
from her2rwd.treatment import build_treatment_lines

_CAT_ORDER = ["positive", "low", "ultralow", "null", "unknown"]


def _cfg_s1(cfg: dict) -> dict:
    """S1: narrow pre-index window 365 → 180 days."""
    c = copy.deepcopy(cfg)
    c["her2"]["window_days"]["pre_index"] = 180
    return c


def _cfg_s2(cfg: dict) -> dict:
    """S2: curated-only biomarker records (tiebreak_order still applies but pool is restricted)."""
    c = copy.deepcopy(cfg)
    c["her2"]["curated_only"] = True
    return c


def _cfg_s3(cfg: dict) -> dict:
    """S3: conservative IHC-0 — plain IHC 0 → unknown (not null)."""
    c = copy.deepcopy(cfg)
    c["her2"]["variant_to_category"]["IHC 0"] = "unknown"
    return c


def _distribution(her2_df: pd.DataFrame) -> dict[str, int]:
    counts = her2_df["her2_category"].value_counts().to_dict()
    return {cat: int(counts.get(cat, 0)) for cat in _CAT_ORDER}


def run_sensitivity(
    con,
    cohort_df: pd.DataFrame,
    cfg: dict,
    out_dir: str = "outputs/tables",
) -> dict:
    """Run three sensitivity analyses and write comparison tables.

    Returns dict with keys: 'her2_distribution', 'uptake'.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ── Baseline (primary run) ────────────────────────────────────────────────
    her2_base = derive_her2(con, cohort_df, cfg)
    hr_base = derive_hr(con, cohort_df, cfg)
    lines_base = build_treatment_lines(con, cohort_df, cfg)
    compute_q1(her2_base, hr_base, cohort_df, cfg)  # writes q1 CSVs; distribution taken directly below
    q2_base = compute_q2(her2_base, hr_base, lines_base, cohort_df, cfg)

    dist_base = _distribution(her2_base)
    uptake_base = _uptake_summary(q2_base["uptake_summary"])

    # ── S1: Narrow window ────────────────────────────────────────────────────
    cfg_s1 = _cfg_s1(cfg)
    her2_s1 = derive_her2(con, cohort_df, cfg_s1)
    hr_s1 = derive_hr(con, cohort_df, cfg_s1)
    lines_s1 = build_treatment_lines(con, cohort_df, cfg_s1)
    q2_s1 = compute_q2(her2_s1, hr_s1, lines_s1, cohort_df, cfg_s1)
    dist_s1 = _distribution(her2_s1)
    uptake_s1 = _uptake_summary(q2_s1["uptake_summary"])

    # ── S2: Curated-only ─────────────────────────────────────────────────────
    cfg_s2 = _cfg_s2(cfg)
    her2_s2 = derive_her2(con, cohort_df, cfg_s2)
    hr_s2 = derive_hr(con, cohort_df, cfg_s2)
    lines_s2 = build_treatment_lines(con, cohort_df, cfg_s2)
    q2_s2 = compute_q2(her2_s2, hr_s2, lines_s2, cohort_df, cfg_s2)
    dist_s2 = _distribution(her2_s2)
    uptake_s2 = _uptake_summary(q2_s2["uptake_summary"])

    # ── S3: Conservative IHC-0 ───────────────────────────────────────────────
    cfg_s3 = _cfg_s3(cfg)
    her2_s3 = derive_her2(con, cohort_df, cfg_s3)
    hr_s3 = derive_hr(con, cohort_df, cfg_s3)
    lines_s3 = build_treatment_lines(con, cohort_df, cfg_s3)
    q2_s3 = compute_q2(her2_s3, hr_s3, lines_s3, cohort_df, cfg_s3)
    dist_s3 = _distribution(her2_s3)
    uptake_s3 = _uptake_summary(q2_s3["uptake_summary"])

    # ── Build HER2 distribution comparison table ──────────────────────────────
    n_total = len(cohort_df)
    dist_rows = []
    for cat in _CAT_ORDER:
        dist_rows.append(
            {
                "her2_category": cat,
                "n_baseline": dist_base[cat],
                "pct_baseline": round(dist_base[cat] / n_total * 100, 1),
                "n_s1_narrow_window": dist_s1[cat],
                "pct_s1_narrow_window": round(dist_s1[cat] / n_total * 100, 1),
                "n_s2_curated_only": dist_s2[cat],
                "pct_s2_curated_only": round(dist_s2[cat] / n_total * 100, 1),
                "n_s3_conservative_ihc0": dist_s3[cat],
                "pct_s3_conservative_ihc0": round(dist_s3[cat] / n_total * 100, 1),
            }
        )

    dist_df = pd.DataFrame(dist_rows)
    dist_df.to_csv(out / "sensitivity_her2_distribution.csv", index=False)

    # ── Build uptake comparison table ────────────────────────────────────────
    all_subinds = set(uptake_base) | set(uptake_s1) | set(uptake_s2) | set(uptake_s3)
    uptake_rows = []
    for sub in sorted(all_subinds):
        uptake_rows.append(
            {
                "subindication": sub,
                "n_enhertu_baseline": uptake_base.get(sub, 0),
                "n_enhertu_s1_narrow_window": uptake_s1.get(sub, 0),
                "n_enhertu_s2_curated_only": uptake_s2.get(sub, 0),
                "n_enhertu_s3_conservative_ihc0": uptake_s3.get(sub, 0),
            }
        )

    uptake_df = pd.DataFrame(uptake_rows)
    uptake_df.to_csv(out / "sensitivity_uptake.csv", index=False)

    return {"her2_distribution": dist_df, "uptake": uptake_df}


def _uptake_summary(df: pd.DataFrame) -> dict[str, int]:
    return {row["subindication"]: int(row["n_enhertu"]) for _, row in df.iterrows()}

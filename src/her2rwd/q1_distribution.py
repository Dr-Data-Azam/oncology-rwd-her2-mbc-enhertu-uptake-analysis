"""Question 1: HER2 distribution at metastatic diagnosis.

Responsibility:
    Compute overall HER2 category distribution and stratify by HR status and
    de novo / recurrent disease type. Compare classifiable-patient proportions
    against literature benchmarks from config (all marked VERIFY). Apply Wilson
    95% CIs and small-cell (n < 11) flagging throughout.

Inputs:
    her2_df: DataFrame from derive_her2()
    hr_df: DataFrame from derive_hr()
    cohort_df: DataFrame from build_cohort()
    config dict loaded from config/analysis_rules.yaml

Outputs:
    outputs/tables/q1_overall.csv        — 5 HER2 categories, all 103 patients
    outputs/tables/q1_by_hr.csv          — HER2 x HR status
    outputs/tables/q1_by_disease_type.csv — HER2 x de novo / recurrent
    outputs/tables/q1_by_source.csv      — HER2 x curated vs EHR source
    outputs/tables/q1_benchmark.csv      — classifiable vs literature ranges
    Returns dict of DataFrames.

ADRs implemented: ADR-012 (statistics), ADR-014 (benchmarks)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from her2rwd.statistics import build_distribution, wilson_ci

_CAT_ORDER = ["positive", "low", "ultralow", "null", "unknown"]
_CLASSIFIABLE = ["positive", "low", "ultralow", "null"]


def compute_q1(
    her2_df: pd.DataFrame,
    hr_df: pd.DataFrame,
    cohort_df: pd.DataFrame,
    cfg: dict,
    out_dir: str | Path = "outputs/tables",
) -> dict[str, pd.DataFrame]:
    """Compute HER2 distribution tables for Q1.

    ADRs implemented: ADR-012, ADR-014
    """
    threshold = cfg["stats"]["small_cell_threshold"]
    z = cfg["stats"].get("ci_z", 1.96)
    benchmarks = cfg["benchmarks"]
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    merged = (
        her2_df[["patient_id", "her2_category", "her2_curation_flag"]]
        .merge(hr_df[["patient_id", "hr_status"]], on="patient_id", how="left")
        .merge(cohort_df[["patient_id", "disease_type"]], on="patient_id", how="left")
    )
    N = len(merged)

    # ── Overall distribution (all patients) ───────────────────────────────────
    counts_all = merged.groupby("her2_category", dropna=False).size().reindex(_CAT_ORDER, fill_value=0)
    overall = build_distribution(counts_all, N, threshold, z)
    overall.rename(columns={overall.columns[0]: "her2_category"}, inplace=True)
    overall.to_csv(out_path / "q1_overall.csv", index=False)

    # ── Classifiable only — denominator for benchmark comparison ──────────────
    classifiable = merged[merged["her2_category"].isin(_CLASSIFIABLE)]
    N_class = len(classifiable)
    counts_class = classifiable.groupby("her2_category").size().reindex(_CLASSIFIABLE, fill_value=0)

    # ── By HR status ──────────────────────────────────────────────────────────
    by_hr_frames = []
    for hr_val, grp in merged.groupby("hr_status", dropna=False):
        grp_counts = grp.groupby("her2_category", dropna=False).size().reindex(_CAT_ORDER, fill_value=0)
        dist = build_distribution(grp_counts, len(grp), threshold, z)
        dist.insert(0, "hr_status", str(hr_val))
        by_hr_frames.append(dist)
    by_hr = pd.concat(by_hr_frames, ignore_index=True)
    by_hr.rename(columns={by_hr.columns[1]: "her2_category"}, inplace=True)
    by_hr.to_csv(out_path / "q1_by_hr.csv", index=False)

    # ── By disease type ───────────────────────────────────────────────────────
    by_dt_frames = []
    for dt_val, grp in merged.groupby("disease_type", dropna=False):
        grp_counts = grp.groupby("her2_category", dropna=False).size().reindex(_CAT_ORDER, fill_value=0)
        dist = build_distribution(grp_counts, len(grp), threshold, z)
        dist.insert(0, "disease_type", str(dt_val))
        by_dt_frames.append(dist)
    by_dt = pd.concat(by_dt_frames, ignore_index=True)
    by_dt.rename(columns={by_dt.columns[1]: "her2_category"}, inplace=True)
    by_dt.to_csv(out_path / "q1_by_disease_type.csv", index=False)

    # ── By source (curated vs EHR) — ADR-008 ─────────────────────────────────
    by_src_frames = []
    merged["her2_curation_flag"] = pd.to_numeric(merged["her2_curation_flag"], errors="coerce").fillna(0).astype(int)
    for src_val, grp in merged.groupby("her2_curation_flag", dropna=True):
        label = "curated" if int(src_val) == 1 else "ehr"
        grp_counts = grp.groupby("her2_category", dropna=False).size().reindex(_CAT_ORDER, fill_value=0)
        dist = build_distribution(grp_counts, len(grp), threshold, z)
        dist.insert(0, "source", label)
        by_src_frames.append(dist)
    by_source = pd.concat(by_src_frames, ignore_index=True)
    by_source.rename(columns={by_source.columns[1]: "her2_category"}, inplace=True)
    by_source.to_csv(out_path / "q1_by_source.csv", index=False)

    # ── Benchmark comparison ───────────────────────────────────────────────────
    # Three comparisons (all VERIFY — do not state as fact without confirmed citations):
    #   1. positive and low as % of classifiable (denominator = N_class)
    #   2. HER2-zero (null+ultralow combined) as % of classifiable  — lit benchmark
    #      covers the IHC-0 total, not null-only; key renamed her2_zero_pct_range
    #   3. ultralow as % of HER2-zero — different denominator (n_zero), different key
    n_pos = int(counts_class.get("positive", 0))
    n_low = int(counts_class.get("low", 0))
    n_ultra = int(counts_class.get("ultralow", 0))
    n_null_only = int(counts_class.get("null", 0))
    n_zero = n_ultra + n_null_only  # HER2-zero = null + ultralow combined

    citation = benchmarks.get("source_citation", "VERIFY")
    bench_rows = []

    def _bench_row(label, n, denom, denom_label, bm_key):
        pct = round(n / denom * 100, 1) if denom > 0 else 0.0
        lo, hi = wilson_ci(n, denom, z)
        bm = benchmarks.get(bm_key, None)
        return {
            "her2_category": label,
            "n": n,
            "denominator": denom,
            "denominator_label": denom_label,
            "pct": pct,
            "ci_lo": round(lo * 100, 1),
            "ci_hi": round(hi * 100, 1),
            "benchmark_lo_pct": bm[0] if isinstance(bm, list) else None,
            "benchmark_hi_pct": bm[1] if isinstance(bm, list) else None,
            "in_benchmark_range": ((bm[0] <= pct <= bm[1]) if isinstance(bm, list) and bm[0] is not None else None),
            "source_VERIFY": citation,
        }

    bench_rows.append(_bench_row("positive", n_pos, N_class, "classifiable", "her2_positive_pct_range"))
    bench_rows.append(_bench_row("low", n_low, N_class, "classifiable", "her2_low_pct_range"))
    # null+ultralow combined vs classifiable (literature benchmarks IHC-0 as a whole)
    bench_rows.append(_bench_row("her2_zero (null+ultralow)", n_zero, N_class, "classifiable", "her2_zero_pct_range"))
    # ultralow as % of HER2-zero (different denominator)
    bench_rows.append(_bench_row("ultralow (of HER2-zero)", n_ultra, n_zero, "her2_zero", "her2_ultralow_of_zero_pct"))

    benchmark_df = pd.DataFrame(bench_rows)
    benchmark_df.to_csv(out_path / "q1_benchmark.csv", index=False)

    return {
        "overall": overall,
        "by_hr": by_hr,
        "by_disease_type": by_dt,
        "by_source": by_source,
        "benchmark": benchmark_df,
        "n_total": N,
        "n_classifiable": N_class,
    }

"""Hormone receptor (HR) status derivation.

Responsibility:
    Derive ER and PR status from the biomarker table using the same look-up
    window as HER2 (her2.window_days). When a numeric percentage is available
    in biomarker_variant, it takes precedence over biomarker_result text
    (ADR-009: pct_beats_result_text). NULL variant falls back to result text.
    ER-low patients (1–10%) are flagged separately.

Inputs:
    cohort_df: DataFrame with patient_id and index_date (from cohort.py)
    Open DuckDB connection with biomarker table.
    config dict loaded from config/analysis_rules.yaml.

Outputs:
    outputs/tables/patient_hr.csv — one row per cohort patient.
    Returns hr_df.

ADRs implemented: ADR-009 (HR derivation)
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def derive_hr(
    con: duckdb.DuckDBPyConnection,
    cohort_df: pd.DataFrame,
    cfg: dict,
    out_dir: str | Path = "outputs/tables",
) -> pd.DataFrame:
    """Derive HR status and ER-low flag per cohort patient.

    ADRs implemented: ADR-009
    """
    pos_thr = cfg["hr"]["positive_threshold_pct"]
    er_low_max = cfg["hr"]["er_low_max_pct"]
    pre_days = cfg["her2"]["window_days"]["pre_index"]
    post_days = cfg["her2"]["window_days"]["post_index"]

    con.register("_cohort_for_hr", cohort_df[["patient_id", "index_date"]])

    # Step 1: best ER / PR record per patient via tie-break (ADR-009 + ADR-008 order)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _hr_best AS
        WITH windowed AS (
            SELECT
                b.patient_id,
                b.biomarker_name,
                b.biomarker_result,
                b.biomarker_variant,
                b.curation_flag,
                -- extract numeric % from "52% positive cells" style variant
                TRY_CAST(
                    REGEXP_EXTRACT(b.biomarker_variant, '(\\d+)%', 1)
                AS INTEGER) AS pct,
                ROW_NUMBER() OVER (
                    PARTITION BY b.patient_id, b.biomarker_name
                    ORDER BY
                        b.curation_flag DESC,
                        CASE WHEN b.biomarker_variant IS NULL THEN 0 ELSE 1 END DESC,
                        ABS(DATEDIFF('day', CAST(b.report_date AS DATE), CAST(c.index_date AS DATE))) ASC
                ) AS rn
            FROM biomarker b
            JOIN _cohort_for_hr c ON b.patient_id = c.patient_id
            WHERE b.biomarker_name IN ('ER', 'PR')
              AND CAST(b.report_date AS DATE)
                  BETWEEN CAST(c.index_date AS DATE) - INTERVAL '{pre_days} days'
                      AND CAST(c.index_date AS DATE) + INTERVAL '{post_days} days'
        )
        SELECT patient_id, biomarker_name, biomarker_result, biomarker_variant, pct
        FROM windowed WHERE rn = 1
    """)

    # Step 2: pivot to one row per patient, then compute HR status
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _hr_per_patient AS
        WITH er AS (
            SELECT patient_id, pct AS er_pct, biomarker_result AS er_result
            FROM _hr_best WHERE biomarker_name = 'ER'
        ),
        pr AS (
            SELECT patient_id, pct AS pr_pct, biomarker_result AS pr_result
            FROM _hr_best WHERE biomarker_name = 'PR'
        )
        SELECT
            c.patient_id,
            e.er_pct,
            e.er_result,
            p.pr_pct,
            p.pr_result,
            -- HR status: positive if either ER or PR is positive (ADR-009)
            CASE
                WHEN e.er_pct IS NOT NULL AND e.er_pct >= {pos_thr}     THEN 'positive'
                WHEN p.pr_pct IS NOT NULL AND p.pr_pct >= {pos_thr}     THEN 'positive'
                WHEN e.er_pct IS NULL     AND e.er_result = 'Positive'  THEN 'positive'
                WHEN p.pr_pct IS NULL     AND p.pr_result = 'Positive'  THEN 'positive'
                WHEN e.er_pct IS NOT NULL AND e.er_pct < {pos_thr}
                 AND p.pr_pct IS NOT NULL AND p.pr_pct < {pos_thr}      THEN 'negative'
                WHEN e.er_pct IS NOT NULL AND e.er_pct < {pos_thr}
                 AND p.pr_pct IS NULL     AND p.pr_result = 'Negative'  THEN 'negative'
                WHEN p.pr_pct IS NOT NULL AND p.pr_pct < {pos_thr}
                 AND e.er_pct IS NULL     AND e.er_result = 'Negative'  THEN 'negative'
                WHEN e.er_pct IS NULL     AND e.er_result = 'Negative'
                 AND p.pr_pct IS NULL     AND p.pr_result = 'Negative'  THEN 'negative'
                WHEN e.er_pct IS NOT NULL AND e.er_pct < {pos_thr}
                 AND p.patient_id IS NULL                                THEN 'negative'
                WHEN e.er_pct IS NULL     AND e.er_result = 'Negative'
                 AND p.patient_id IS NULL                                THEN 'negative'
                ELSE 'unknown'
            END AS hr_status,
            -- ER-low: ER staining in [threshold, er_low_max] — distinct biology (ADR-009)
            CASE
                WHEN e.er_pct IS NOT NULL
                 AND e.er_pct >= {pos_thr}
                 AND e.er_pct <= {er_low_max} THEN true
                ELSE false
            END AS er_low,
            -- audit: was numeric % used or result-text fallback?
            CASE
                WHEN e.er_pct IS NOT NULL OR p.pr_pct IS NOT NULL THEN 'pct'
                WHEN e.er_result IS NOT NULL OR p.pr_result IS NOT NULL THEN 'result_text'
                ELSE 'no_record'
            END AS hr_source
        FROM _cohort_for_hr c
        LEFT JOIN er e ON c.patient_id = e.patient_id
        LEFT JOIN pr p ON c.patient_id = p.patient_id
    """)

    hr_df = con.execute("""
        SELECT patient_id, hr_status, er_pct, er_result, er_low,
               pr_pct, pr_result, hr_source
        FROM _hr_per_patient
        ORDER BY patient_id
    """).df()

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    hr_df.to_csv(out_path / "patient_hr.csv", index=False)

    return hr_df

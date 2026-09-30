"""HER2 classification from biomarker records.

Responsibility:
    Map every HER2 biomarker record's variant to one of five clinical
    categories: positive, low, ultralow, null, unknown. Apply the look-up
    window around the metastatic index date, resolve multiple records via the
    tie-break hierarchy, and produce one HER2 category per patient with full
    audit columns.

    All mappings, window bounds, and tie-break order are read from
    config/analysis_rules.yaml. No clinical thresholds are hard-coded here.

Inputs:
    cohort_df: DataFrame with patient_id and index_date (from cohort.py)
    Open DuckDB connection with biomarker table.
    config dict loaded from config/analysis_rules.yaml.

Outputs:
    outputs/tables/patient_her2.csv — one row per cohort patient.
    Returns her2_df.

ADRs implemented: ADR-006 (variant mapping), ADR-007 (window), ADR-008 (tie-break)
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def derive_her2(
    con: duckdb.DuckDBPyConnection,
    cohort_df: pd.DataFrame,
    cfg: dict,
    out_dir: str | Path = "outputs/tables",
) -> pd.DataFrame:
    """Derive HER2 category per cohort patient.

    ADRs implemented: ADR-006, ADR-007, ADR-008
    """
    pre_days = cfg["her2"]["window_days"]["pre_index"]
    post_days = cfg["her2"]["window_days"]["post_index"]
    variant_map = cfg["her2"]["variant_to_category"]
    curated_only = cfg["her2"].get("curated_only", False)
    curated_filter = "AND b.curation_flag = 1" if curated_only else ""

    # Build SQL CASE from config mapping — keeps variant strings out of code
    case_clauses = "\n                ".join(f"WHEN her2_variant = '{k}' THEN '{v}'" for k, v in variant_map.items())

    con.register("_cohort_for_her2", cohort_df[["patient_id", "index_date"]])

    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _her2_result AS
        WITH windowed AS (
            SELECT
                b.patient_id,
                b.report_date                                   AS her2_test_date,
                b.biomarker_variant                             AS her2_variant,
                b.curation_flag                                 AS her2_curation_flag,
                ABS(DATEDIFF('day', CAST(b.report_date AS DATE), CAST(c.index_date AS DATE))) AS days_from_index,
                -- variant_specificity: NULL=0, indeterminate=1, IHC score=2 (ADR-008)
                CASE
                    WHEN b.biomarker_variant IS NULL                         THEN 0
                    WHEN b.biomarker_variant IN ('Pending', 'IHC equivocal') THEN 1
                    ELSE                                                           2
                END AS variant_specificity,
                ROW_NUMBER() OVER (
                    PARTITION BY b.patient_id
                    ORDER BY
                        b.curation_flag DESC,
                        CASE WHEN b.biomarker_variant IS NULL THEN 0
                             WHEN b.biomarker_variant IN ('Pending', 'IHC equivocal') THEN 1
                             ELSE 2 END DESC,
                        ABS(DATEDIFF('day', CAST(b.report_date AS DATE), CAST(c.index_date AS DATE))) ASC
                ) AS rn
            FROM biomarker b
            JOIN _cohort_for_her2 c ON b.patient_id = c.patient_id
            WHERE b.biomarker_name = 'HER2'
              AND CAST(b.report_date AS DATE)
                  BETWEEN CAST(c.index_date AS DATE) - INTERVAL '{pre_days} days'
                      AND CAST(c.index_date AS DATE) + INTERVAL '{post_days} days'
              {curated_filter}
        ),
        selected AS (SELECT * FROM windowed WHERE rn = 1),
        counts AS (
            SELECT b.patient_id, COUNT(*) AS n_her2_in_window
            FROM biomarker b
            JOIN _cohort_for_her2 c ON b.patient_id = c.patient_id
            WHERE b.biomarker_name = 'HER2'
              AND CAST(b.report_date AS DATE)
                  BETWEEN CAST(c.index_date AS DATE) - INTERVAL '{pre_days} days'
                      AND CAST(c.index_date AS DATE) + INTERVAL '{post_days} days'
              {curated_filter}
            GROUP BY b.patient_id
        )
        SELECT
            c.patient_id,
            s.her2_test_date,
            s.her2_variant,
            s.her2_curation_flag,
            s.days_from_index,
            COALESCE(n.n_her2_in_window, 0) AS n_her2_in_window,
            CASE
                {case_clauses}
                ELSE 'unknown'
            END AS her2_category
        FROM _cohort_for_her2 c
        LEFT JOIN selected s ON c.patient_id = s.patient_id
        LEFT JOIN counts  n ON c.patient_id = n.patient_id
    """)

    her2_df = con.execute("""
        SELECT patient_id, her2_category, her2_variant, her2_test_date,
               her2_curation_flag, days_from_index, n_her2_in_window
        FROM _her2_result
        ORDER BY patient_id
    """).df()

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    her2_df.to_csv(out_path / "patient_her2.csv", index=False)

    return her2_df

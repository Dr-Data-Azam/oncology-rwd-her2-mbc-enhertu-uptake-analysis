"""Cohort construction for the her2rwd pipeline.

Responsibility:
    Build the analysis cohort from raw diagnosis and staging tables.
    Assign a metastatic index date per patient, apply eligibility filters,
    and classify each patient as de novo or recurrent mBC. Write attrition
    and cohort outputs to outputs/tables/.

Inputs:
    Open DuckDB connection with tables: patient, diagnosis, staging.
    config dict loaded from config/analysis_rules.yaml.

Outputs:
    outputs/tables/cohort.csv   — one row per eligible patient.
    outputs/tables/attrition.csv — one row per eligibility step.
    Returns (cohort_df, attrition_df).

ADRs implemented: ADR-002 (eligibility), ADR-004 (index date), ADR-005 (de novo/recurrent)
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def build_cohort(
    con: duckdb.DuckDBPyConnection,
    cfg: dict,
    out_dir: str | Path = "outputs/tables",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the mBC analysis cohort with attrition tracking.

    ADRs implemented: ADR-002, ADR-004, ADR-005
    """
    gap_days = cfg["cohort"]["de_novo_primary_gap_days"]
    min_age = cfg["eligibility"]["min_age_at_index_years"]
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    attrition: list[dict] = []

    # ── Step 1: all patients ──────────────────────────────────────────────────
    total = con.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
    attrition.append({
        "step": 1,
        "step_label": "All patients in dataset",
        "n_in": total,
        "n_excluded": 0,
        "n_remaining": total,
    })

    # ── Step 2: assign index date (ADR-004) ───────────────────────────────────
    # Index date = LEAST(earliest C50 metastatic diagnosis date,
    #                    earliest M1/IV staging date).
    # Patients with neither signal are excluded here.
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _index_raw AS
        WITH met_dx AS (
            SELECT patient_id, MIN(diagnosis_date) AS met_dx_date
            FROM diagnosis
            WHERE diagnosis_type = 'metastatic' AND diagnosis_code LIKE 'C50%'
            GROUP BY patient_id
        ),
        m1_stg AS (
            SELECT patient_id, MIN(stage_date) AS m1_stg_date
            FROM staging
            WHERE m_stage = 'M1' OR stage_group = 'IV'
            GROUP BY patient_id
        )
        SELECT
            COALESCE(d.patient_id, s.patient_id) AS patient_id,
            d.met_dx_date,
            s.m1_stg_date,
            LEAST(
                COALESCE(d.met_dx_date, s.m1_stg_date),
                COALESCE(s.m1_stg_date, d.met_dx_date)
            ) AS index_date,
            CASE
                WHEN d.met_dx_date IS NULL            THEN 'staging_only'
                WHEN s.m1_stg_date IS NULL            THEN 'diagnosis_only'
                WHEN s.m1_stg_date <= d.met_dx_date  THEN 'staging_first'
                ELSE                                       'diagnosis_first'
            END AS index_source
        FROM met_dx d FULL OUTER JOIN m1_stg s ON d.patient_id = s.patient_id
    """)

    n_with_signal = con.execute("SELECT COUNT(*) FROM _index_raw").fetchone()[0]
    attrition.append({
        "step": 2,
        "step_label": "Has metastatic signal (C50 dx or M1/IV staging)",
        "n_in": total,
        "n_excluded": total - n_with_signal,
        "n_remaining": n_with_signal,
    })

    # ── Step 3: join demographics; exclude death before birth (ADR-002) ───────
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _cohort_s3 AS
        SELECT
            i.patient_id,
            i.index_date,
            i.index_source,
            p.date_of_birth,
            p.date_of_death,
            DATEDIFF('year', p.date_of_birth, i.index_date) AS age_at_index
        FROM _index_raw i
        JOIN patient p ON i.patient_id = p.patient_id
        WHERE NOT (
            p.date_of_death IS NOT NULL
            AND p.date_of_birth IS NOT NULL
            AND p.date_of_death < p.date_of_birth
        )
    """)

    n_after_dob = con.execute("SELECT COUNT(*) FROM _cohort_s3").fetchone()[0]
    attrition.append({
        "step": 3,
        "step_label": "Exclude death before birth",
        "n_in": n_with_signal,
        "n_excluded": n_with_signal - n_after_dob,
        "n_remaining": n_after_dob,
    })

    # ── Step 4: exclude age < min at index date (ADR-002) ─────────────────────
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _cohort_s4 AS
        SELECT * FROM _cohort_s3
        WHERE age_at_index >= {min_age}
    """)

    n_after_age = con.execute("SELECT COUNT(*) FROM _cohort_s4").fetchone()[0]
    attrition.append({
        "step": 4,
        "step_label": f"Exclude age < {min_age} at index date",
        "n_in": n_after_dob,
        "n_excluded": n_after_dob - n_after_age,
        "n_remaining": n_after_age,
    })

    # ── Step 5: de novo / recurrent flag (ADR-005) ────────────────────────────
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _cohort_final AS
        WITH primary_dx AS (
            SELECT patient_id, MIN(diagnosis_date) AS primary_date
            FROM diagnosis
            WHERE diagnosis_type = 'primary' AND diagnosis_code LIKE 'C50%'
            GROUP BY patient_id
        )
        SELECT
            c.patient_id,
            c.index_date,
            c.index_source,
            c.age_at_index,
            c.date_of_birth,
            c.date_of_death,
            CASE
                WHEN p.patient_id IS NULL THEN 'de_novo'
                WHEN DATEDIFF('day', p.primary_date, c.index_date) <= {gap_days}
                    THEN 'de_novo'
                ELSE 'recurrent'
            END AS disease_type
        FROM _cohort_s4 c
        LEFT JOIN primary_dx p ON c.patient_id = p.patient_id
    """)

    # ── Collect and write outputs ─────────────────────────────────────────────
    cohort_df = con.execute("""
        SELECT patient_id, index_date, index_source, disease_type,
               age_at_index, date_of_birth, date_of_death
        FROM _cohort_final
        ORDER BY patient_id
    """).df()

    attrition_df = pd.DataFrame(attrition)

    cohort_df.to_csv(out_path / "cohort.csv", index=False)
    attrition_df.to_csv(out_path / "attrition.csv", index=False)

    return cohort_df, attrition_df

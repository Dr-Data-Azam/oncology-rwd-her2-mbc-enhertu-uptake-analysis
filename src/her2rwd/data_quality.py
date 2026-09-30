"""Data-quality checks for the her2rwd pipeline.

Responsibility:
    Run a fixed suite of SQL-based checks against the raw DuckDB tables.
    Every flagged record is logged to outputs/dq/dq_log.csv with its
    patient_id, check name, severity, and the action downstream modules
    should apply. Checks are non-destructive — they never modify tables.

Inputs:
    Open DuckDB connection with tables: patient, diagnosis, staging,
    biomarker, medication.
    config dict loaded from config/analysis_rules.yaml.

Outputs:
    outputs/dq/dq_log.csv     — one row per flagged patient per check.
    outputs/dq/dq_summary.csv — one row per check (counts + severity).
    Returns summary DataFrame to the caller.

ADRs implemented: ADR-003 (DQ handling)
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def run_dq_checks(
    con: duckdb.DuckDBPyConnection,
    cfg: dict,
    out_dir: str | Path = "outputs/dq",
) -> pd.DataFrame:
    """Run all DQ checks; write dq_log.csv and dq_summary.csv; return summary.

    ADRs implemented: ADR-003
    """
    checks = _define_checks(cfg)
    detail_rows: list[dict] = []
    summary_rows: list[dict] = []

    for chk in checks:
        patient_ids = con.execute(chk["sql"]).df()["patient_id"].tolist()
        n = len(patient_ids)
        for pid in patient_ids:
            detail_rows.append(
                {
                    "patient_id": pid,
                    "check_name": chk["name"],
                    "severity": chk["severity"],
                    "action": chk["action"],
                    "description": chk["description"],
                }
            )
        summary_rows.append(
            {
                "check_name": chk["name"],
                "table": chk["table"],
                "description": chk["description"],
                "n_flagged": n,
                "severity": chk["severity"],
                "action": chk["action"],
                "sample_ids": "|".join(str(p) for p in patient_ids[:3]),
            }
        )

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(detail_rows).to_csv(out_path / "dq_log.csv", index=False)
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(out_path / "dq_summary.csv", index=False)

    return summary_df


def _define_checks(cfg: dict) -> list[dict]:
    """Return check definitions. Each SQL must return a column named patient_id."""
    grace = cfg["dq"]["post_death_grace_days"]

    return [
        {
            "name": "death_before_birth",
            "table": "patient",
            "description": "date_of_death is earlier than date_of_birth",
            "severity": "error",
            "action": cfg["dq"]["pre_birth_action"],
            "sql": """
                SELECT patient_id FROM patient
                WHERE date_of_death IS NOT NULL
                  AND date_of_birth IS NOT NULL
                  AND date_of_death < date_of_birth
            """,
        },
        {
            "name": "future_date_of_death",
            "table": "patient",
            "description": "date_of_death is after today",
            "severity": "error",
            "action": cfg["dq"]["future_date_action"],
            "sql": "SELECT patient_id FROM patient WHERE date_of_death > CURRENT_DATE",
        },
        {
            "name": "future_diagnosis_date",
            "table": "diagnosis",
            "description": "diagnosis_date is after today",
            "severity": "error",
            "action": cfg["dq"]["future_date_action"],
            "sql": "SELECT patient_id FROM diagnosis WHERE diagnosis_date > CURRENT_DATE",
        },
        {
            "name": "future_biomarker_date",
            "table": "biomarker",
            "description": "biomarker report_date is after today",
            "severity": "error",
            "action": cfg["dq"]["future_date_action"],
            "sql": "SELECT patient_id FROM biomarker WHERE report_date > CURRENT_DATE",
        },
        {
            "name": "future_medication_date",
            "table": "medication",
            "description": "med_date is after today",
            "severity": "error",
            "action": cfg["dq"]["future_date_action"],
            "sql": "SELECT patient_id FROM medication WHERE med_date > CURRENT_DATE",
        },
        {
            "name": "future_stage_date",
            "table": "staging",
            "description": "stage_date is after today",
            "severity": "error",
            "action": cfg["dq"]["future_date_action"],
            "sql": "SELECT patient_id FROM staging WHERE stage_date > CURRENT_DATE",
        },
        {
            "name": "post_death_diagnosis",
            "table": "diagnosis",
            "description": f"diagnosis_date more than {grace} days after date_of_death",
            "severity": "warning",
            "action": cfg["dq"]["post_death_action"],
            "sql": f"""
                SELECT DISTINCT d.patient_id FROM diagnosis d
                JOIN patient p ON d.patient_id = p.patient_id
                WHERE p.date_of_death IS NOT NULL
                  AND d.diagnosis_date > p.date_of_death + INTERVAL '{grace} days'
            """,
        },
        {
            "name": "post_death_biomarker",
            "table": "biomarker",
            "description": f"report_date more than {grace} days after date_of_death",
            "severity": "warning",
            "action": cfg["dq"]["post_death_action"],
            "sql": f"""
                SELECT DISTINCT b.patient_id FROM biomarker b
                JOIN patient p ON b.patient_id = p.patient_id
                WHERE p.date_of_death IS NOT NULL
                  AND b.report_date > p.date_of_death + INTERVAL '{grace} days'
            """,
        },
        {
            "name": "post_death_medication",
            "table": "medication",
            "description": f"med_date more than {grace} days after date_of_death",
            "severity": "warning",
            "action": cfg["dq"]["post_death_action"],
            "sql": f"""
                SELECT DISTINCT m.patient_id FROM medication m
                JOIN patient p ON m.patient_id = p.patient_id
                WHERE p.date_of_death IS NOT NULL
                  AND m.med_date > p.date_of_death + INTERVAL '{grace} days'
            """,
        },
        {
            "name": "null_her2_variant",
            "table": "biomarker",
            "description": "HER2 record has NULL biomarker_variant — classified as unknown",
            "severity": "warning",
            "action": "classify_as_unknown",
            "sql": """
                SELECT DISTINCT patient_id FROM biomarker
                WHERE biomarker_name = 'HER2' AND biomarker_variant IS NULL
            """,
        },
        {
            "name": "unclassifiable_her2_variant",
            "table": "biomarker",
            "description": "HER2 variant is Pending or IHC equivocal — classified as unknown",
            "severity": "warning",
            "action": "classify_as_unknown",
            "sql": """
                SELECT DISTINCT patient_id FROM biomarker
                WHERE biomarker_name = 'HER2'
                  AND biomarker_variant IN ('Pending', 'IHC equivocal')
            """,
        },
        {
            "name": "null_stage_group",
            "table": "staging",
            "description": "stage_group is NULL — cohort.py falls back to m_stage = M1",
            "severity": "info",
            "action": "use_m_stage_fallback",
            "sql": "SELECT DISTINCT patient_id FROM staging WHERE stage_group IS NULL",
        },
        {
            "name": "no_metastatic_record",
            "table": "diagnosis+staging",
            "description": "No metastatic diagnosis_type and no M1/stage-IV staging record",
            "severity": "warning",
            "action": "exclude_from_cohort",
            "sql": """
                SELECT p.patient_id FROM patient p
                WHERE p.patient_id NOT IN (
                    SELECT DISTINCT patient_id FROM diagnosis
                    WHERE diagnosis_type = 'metastatic'
                )
                AND p.patient_id NOT IN (
                    SELECT DISTINCT patient_id FROM staging
                    WHERE m_stage = 'M1' OR stage_group = 'IV'
                )
            """,
        },
        {
            "name": "orphan_diagnosis",
            "table": "diagnosis",
            "description": "diagnosis.patient_id not in patient table",
            "severity": "error",
            "action": "exclude_record",
            "sql": """
                SELECT DISTINCT d.patient_id FROM diagnosis d
                LEFT JOIN patient p ON d.patient_id = p.patient_id
                WHERE p.patient_id IS NULL
            """,
        },
        {
            "name": "orphan_biomarker",
            "table": "biomarker",
            "description": "biomarker.patient_id not in patient table",
            "severity": "error",
            "action": "exclude_record",
            "sql": """
                SELECT DISTINCT b.patient_id FROM biomarker b
                LEFT JOIN patient p ON b.patient_id = p.patient_id
                WHERE p.patient_id IS NULL
            """,
        },
        {
            "name": "her2_result_variant_conflict",
            "table": "biomarker",
            "description": "HER2 result='Negative' but variant='IHC 1+' — variant wins (IHC 1+ = HER2-low)",
            "severity": "info",
            "action": "variant_beats_result_text",
            "sql": """
                SELECT DISTINCT patient_id FROM biomarker
                WHERE biomarker_name = 'HER2'
                  AND biomarker_result = 'Negative'
                  AND biomarker_variant = 'IHC 1+'
            """,
        },
        {
            "name": "er_pr_null_variant_fallback",
            "table": "biomarker",
            "description": "ER/PR record has NULL variant — HR status will fall back to biomarker_result text",
            "severity": "info",
            "action": "use_result_text_fallback",
            "sql": """
                SELECT DISTINCT patient_id FROM biomarker
                WHERE biomarker_name IN ('ER', 'PR')
                  AND biomarker_variant IS NULL
            """,
        },
        {
            "name": "duplicate_biomarker_same_date",
            "table": "biomarker",
            "description": "Same patient_id + report_date + biomarker_name appears more than once",
            "severity": "warning",
            "action": "apply_curation_tiebreak",
            "sql": """
                SELECT DISTINCT patient_id FROM (
                    SELECT patient_id, report_date, biomarker_name, COUNT(*) c
                    FROM biomarker GROUP BY 1, 2, 3 HAVING c > 1
                )
            """,
        },
        {
            "name": "non_breast_metastatic_code",
            "table": "diagnosis",
            "description": "diagnosis_type='metastatic' with non-C50 ICD code — excluded from index date",
            "severity": "warning",
            "action": "exclude_from_index_date",
            "sql": """
                SELECT DISTINCT patient_id FROM diagnosis
                WHERE diagnosis_type = 'metastatic'
                  AND diagnosis_code NOT LIKE 'C50%'
            """,
        },
    ]

"""Metastatic breast cancer cohort construction.

Responsibility:
    Apply eligibility criteria to define the analytic cohort, assign one
    metastatic index date per patient, and classify each patient as de novo
    or recurrent.  Produce a one-row-per-patient cohort table and a
    CONSORT-style attrition table that traces every exclusion step.

    All thresholds (minimum age, de-novo gap, source priority, etc.) are read
    from config/analysis_rules.yaml.  No parameters are hard-coded here.

Inputs:
    DuckDB connection with raw tables and dq_log applied
    config/analysis_rules.yaml (eligibility, index_date, cohort sections)

Outputs:
    outputs/tables/cohort.csv      — one row per eligible patient
    outputs/tables/attrition.csv   — CONSORT-style exclusion counts

ADRs implemented: ADR-002 (eligibility), ADR-004 (index date), ADR-005 (de novo vs recurrent)
"""

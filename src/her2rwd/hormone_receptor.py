"""Hormone receptor (HR) status derivation.

Responsibility:
    Derive ER and PR status for each cohort patient from the biomarker table,
    then compute the composite HR status (HR+ = ER+ or PR+).  When result
    text and the percentage-positive value conflict, the rule from ADR-009
    (percentage beats result text) applies.  Flag ER-low patients (1–10%)
    separately for stratification.

    All thresholds (positive_threshold_pct, er_low_max_pct) are read from
    config/analysis_rules.yaml (hr section).

Inputs:
    outputs/tables/cohort.csv
    DuckDB biomarker table
    config/analysis_rules.yaml (hr section)

Outputs:
    outputs/tables/patient_hr.csv  — one row per cohort patient:
        patient_id, er_status, er_pct, er_low_flag,
        pr_status, pr_pct, hr_status, hr_evidence_note

ADRs implemented: ADR-009 (HR derivation)
"""

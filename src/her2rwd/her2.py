"""HER2 classification from biomarker records.

Responsibility:
    Map every HER2 biomarker record's (result, variant) pair to one of the
    five clinical categories: HER2-positive, HER2-low, HER2-ultralow,
    HER2-0/null, or unknown/indeterminate.  Apply the look-up window around
    the metastatic index date, resolve multiple records using the tie-break
    hierarchy, and produce one HER2 category per patient with full audit
    columns explaining which record won and why.

    All category mappings, window bounds, and tie-break order are read from
    config/analysis_rules.yaml (her2 section).  No clinical thresholds are
    hard-coded here.

Inputs:
    outputs/tables/cohort.csv
    DuckDB biomarker table
    config/analysis_rules.yaml (her2 section)

Outputs:
    outputs/tables/patient_her2.csv  — one row per cohort patient:
        patient_id, her2_category, winning_record_id, rule_applied,
        candidates_considered, window_used, note

ADRs implemented: ADR-006 (variant mapping), ADR-007 (window), ADR-008 (tie-break hierarchy)
"""

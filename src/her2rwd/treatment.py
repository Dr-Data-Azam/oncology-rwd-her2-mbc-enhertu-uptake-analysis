"""Treatment regimen grouping and line-of-therapy approximation.

Responsibility:
    Group medication events into regimens (drugs starting within
    regimen_window_days of each other form one line) and assign an
    approximate line-of-therapy number relative to the metastatic index date.
    Identify the first treatment after metastatic diagnosis for each patient.
    Because the raw data has no end dates or explicit line fields, this module
    implements a date-proximity heuristic documented in ADR-010.

    All window parameters are read from config/analysis_rules.yaml
    (treatment section).

Inputs:
    outputs/tables/cohort.csv
    DuckDB medication table
    config/analysis_rules.yaml (treatment section)

Outputs:
    outputs/tables/patient_lines.csv  — one row per patient-line:
        patient_id, line_number, line_start_date, drugs, regimen_class,
        days_from_index, includes_enhertu

ADRs implemented: ADR-010 (regimen grouping and line-of-therapy approximation)
"""

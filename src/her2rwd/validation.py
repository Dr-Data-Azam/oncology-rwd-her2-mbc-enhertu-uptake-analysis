"""Pipeline invariant checks and validation report.

Responsibility:
    Run a battery of PASS/FAIL assertions after every pipeline run to confirm
    that the outputs are internally consistent.  Write results to
    audit/validation_report.md.  Any FAIL causes the pipeline to exit with a
    non-zero return code so /close-phase is blocked.

    Invariants checked:
    - Attrition table sums to 150 (total raw patients)
    - Cohort table has exactly one row per patient_id
    - Every HER2 category value is in the allowed set
    - HER2 category counts sum to cohort size
    - No index date is before the patient's date of birth
    - Q1 proportions sum to 100% (within floating-point tolerance)
    - Q2 cohort size equals Q1 cohort size
    - Validation report timestamp and git commit are recorded

Inputs:
    All outputs/tables/*.csv produced by the pipeline

Outputs:
    audit/validation_report.md  — PASS/FAIL per check with counts

ADRs implemented: none (cross-cutting quality gate)
"""

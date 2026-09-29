"""Data-quality checks for the her2rwd pipeline.

Responsibility:
    Run a comprehensive battery of DQ checks across all five raw tables and
    write every issue to outputs/dq/dq_log.csv.  Each row in the log records:
    check_id, table, rule_description, rows_affected, patients_affected,
    action (exclude | flag | retain), and the ADR that governs the decision.
    This log becomes the source for Appendix A of the submission deck.

Inputs:
    DuckDB connection containing the raw tables (from io.load_raw())

Outputs:
    outputs/dq/dq_log.csv
    Summary dict returned for pipeline logging

ADRs implemented: ADR-003 (handling future-dated, post-death and pre-birth records)
"""

"""Sensitivity analyses — pipeline re-runs under alternative rule sets.

Responsibility:
    Re-run the HER2 classification and Q1/Q2 outputs under alternative
    rule configurations (e.g. a narrower biomarker window, curated-only
    records, or a different IHC-0 classification) and produce side-by-side
    comparison tables.  Each alternative rule set is stored as a separate
    YAML file in config/ or as a named override block in analysis_rules.yaml.
    The primary run is always the baseline column.

Inputs:
    outputs/tables/cohort.csv
    DuckDB biomarker and medication tables
    config/analysis_rules.yaml + any alt-rules YAML files

Outputs:
    outputs/tables/sensitivity_her2_distribution.csv  — Q1 under S1/S2/S3
    outputs/tables/sensitivity_uptake.csv             — Q2 subindication counts

ADRs implemented: ADR-007 (window sensitivity), ADR-006 (IHC-0 sensitivity)
"""

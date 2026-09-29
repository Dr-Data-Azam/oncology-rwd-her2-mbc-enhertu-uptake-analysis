"""Question 2: Enhertu uptake vs competitors by HER2-defined subindication.

Responsibility:
    Assign each cohort patient to a subindication (HER2+, HR+/HER2-low,
    HR+/HER2-ultralow, and exploratory groups) using the framework in ADR-011.
    For each subindication report: n, % receiving Enhertu (with Wilson CI),
    median days from metastatic index date to first Enhertu, line of therapy
    at which Enhertu starts, top first-line regimens, and top regimens given
    before or instead of Enhertu.  Identify discordant cases per ADR-013.
    Close with a fit-for-purpose verdict for each subindication.

Inputs:
    outputs/tables/patient_her2.csv
    outputs/tables/patient_hr.csv
    outputs/tables/patient_lines.csv
    outputs/tables/cohort.csv
    config/analysis_rules.yaml (subindications, discordance, stats sections)

Outputs:
    outputs/tables/q2_subindication_summary.csv
    outputs/tables/q2_enhertu_timing.csv
    outputs/tables/q2_competitors.csv
    outputs/tables/q2_discordance.csv

ADRs implemented: ADR-011 (subindication framework), ADR-013 (discordance definitions)
"""

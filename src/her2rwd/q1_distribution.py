"""Question 1: HER2 distribution at metastatic diagnosis.

Responsibility:
    Compute the overall HER2 category distribution and stratify it by at least
    four factors: HR status, curation source (EHR vs curated), org type
    (community vs academic), and de novo vs recurrent.  Compare observed
    proportions against literature benchmarks from config.  Report Wilson 95%
    confidence intervals on every proportion and flag cells with n < 11.
    Quantify the unclassifiable share (unknown + subtype-unknown HER2-negative
    + HER2-0 unspecified) as the key feasibility finding.

Inputs:
    outputs/tables/patient_her2.csv
    outputs/tables/patient_hr.csv
    outputs/tables/cohort.csv
    config/analysis_rules.yaml (benchmarks, stats sections)

Outputs:
    outputs/tables/q1_overall.csv
    outputs/tables/q1_by_hr.csv
    outputs/tables/q1_by_curation.csv
    outputs/tables/q1_by_org_type.csv
    outputs/tables/q1_by_denovo_recurrent.csv
    outputs/tables/q1_unclassifiable.csv

ADRs implemented: ADR-012 (statistics), ADR-014 (literature benchmarks)
"""

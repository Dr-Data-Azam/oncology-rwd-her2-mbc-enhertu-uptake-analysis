# Data Dictionary

> Source: `data/raw/data_dictionary.xlsx` (copy of `external/data_dictionary.xlsx`, READ-ONLY original). Rendered to Markdown for readability; the xlsx is authoritative.

| table_name | column_name | data_type | definition | example_or_allowed_values |
|---|---|---|---|---|
| patient | patient_id | string | Synthetic patient identifier | PAT_001 |
| patient | date_of_birth | date | Patient date of birth; includes intentionally implausible edge cases | 1980-06-15 |
| patient | date_of_death | date | Patient date of death; null if alive/unknown; includes one impossible quality check row | 1979-12-01 |
| patient | org_id | string | Synthetic source organization identifier | ORG_001 |
| patient | org_type | string | Source organization type | community / academic |
| diagnosis | patient_id | string | Synthetic patient identifier | PAT_001 |
| diagnosis | diagnosis_date | date | Date of diagnosis record | 2023-07-01 |
| diagnosis | diagnosis_code | string | ICD-10 diagnosis code; breast dominant with some non-breast noise and comorbidities | C50.9 |
| diagnosis | diagnosis_type | string | Primary or metastatic diagnosis designation | primary / metastatic |
| diagnosis | curation_flag | integer | 0 = structured EHR; 1 = expert curated | 0 / 1 |
| staging | patient_id | string | Synthetic patient identifier | PAT_001 |
| staging | stage_date | date | Date of staging record | 2023-07-10 |
| staging | stage_group | string | Overall stage group; may be blank and derivable from TNM | I / II / III / IV |
| staging | t_stage | string | Tumor stage component | T1 / T2 / T3 / T4 |
| staging | n_stage | string | Node stage component | N0 / N1 / N2 / N3 |
| staging | m_stage | string | Metastasis stage component | M0 / M1 |
| staging | curation_flag | integer | 0 = structured EHR; 1 = expert curated | 0 / 1 |
| biomarker | patient_id | string | Synthetic patient identifier | PAT_001 |
| biomarker | report_date | date | Biomarker report date | 2023-07-12 |
| biomarker | biomarker_name | string | Biomarker evaluated | HER2 / ER / PR / Ki-67 |
| biomarker | biomarker_test_type | string | Test type description | IHC / protein expression |
| biomarker | biomarker_result | string | Structured result field | Positive / Negative / Unknown |
| biomarker | biomarker_variant | string | More granular result detail; curated data more likely to be populated | IHC 3+, IHC 2+; ISH negative, IHC 0 with membrane staining |
| biomarker | curation_flag | integer | 0 = structured EHR; 1 = expert curated | 0 / 1 |
| medication | patient_id | string | Synthetic patient identifier | PAT_001 |
| medication | med_date | date | Medication event date | 2023-08-01 |
| medication | med_brand_name | string | Brand name for therapy | Enhertu |
| medication | med_generic_name | string | Generic therapy name | trastuzumab deruxtecan |
| medication | med_status | string | Medication status | active / completed / discontinued |
| medication | curation_flag | integer | 0 = structured EHR; 1 = expert curated | 0 / 1 |
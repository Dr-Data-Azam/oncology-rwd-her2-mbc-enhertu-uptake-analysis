# ADR-002: Eligibility Criteria

**Status:** Accepted
**Phase:** 02 (cohort-index-date)
**Config keys:** `eligibility.*`

---

## Context

Before building the cohort, patients must meet a minimum set of inclusion criteria.
The diagnosis table contains non-breast-cancer ICD codes (comorbidities, other primaries)
and the patient table contains one record with an impossible date of birth.

## Decision

| Criterion | Rule | Config key |
|---|---|---|
| Breast cancer diagnosis | Must have ≥1 C50.x diagnosis record | `require_breast_code: true` |
| Adult patient | Age ≥ 18 at metastatic index date | `min_age_at_index_years: 18` |
| Valid date of birth | Exclude patients flagged `death_before_birth` | `valid_dob_required: true` |
| In patient table | Exclude orphan IDs not in patient table | `must_exist_in_patient: true` |

## Rationale

- **C50.x requirement:** The diagnosis table contains comorbidity codes (diabetes, COPD,
  vascular disease) and 2 non-breast metastatic codes (C34.9 lung, C61 prostate). Only
  breast cancer primaries and metastatic records are relevant for mBC eligibility.
- **Age ≥ 18:** Standard for adult oncology studies. 24 patients appear under 18 today;
  age at actual index date will be checked in cohort.py.
- **Valid DOB:** PAT_001 has death before birth — an impossible record that would cause
  errors in any age or survival calculation.
- **Orphan IDs:** 2 biomarker patient_ids are not in the patient table (flagged by
  `orphan_biomarker` DQ check). These cannot be linked to demographics.

## Consequences

- `cohort.py` filters using these 4 criteria before computing any index date.
- Exclusions are logged in `outputs/tables/attrition.csv` with reason codes.
- Non-C50 diagnosis records are retained in the DuckDB table for comorbidity context
  but never used for eligibility or index date computation.

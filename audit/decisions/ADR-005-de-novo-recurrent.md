# ADR-005: De Novo vs Recurrent mBC Definition

**Status:** Accepted
**Phase:** 02 (cohort-index-date)
**Config keys:** `cohort.de_novo_primary_gap_days`

---

## Context

Patients in the mBC cohort can arrive at metastatic disease in two ways:

- **De novo metastatic:** the patient presents with stage IV disease at initial
  breast cancer diagnosis (no prior early-stage disease).
- **Recurrent metastatic:** the patient had early-stage breast cancer, received
  treatment, and later developed metastatic recurrence.

HER2-low expression rates and treatment patterns differ between these subtypes,
so the flag is required for Q1 stratification and Q2 subindication analysis.

Two data signals distinguish them:
1. **No prior primary C50 diagnosis** — patient appears in the data only with a
   metastatic code → de novo.
2. **Gap from primary to metastatic index date** — a short gap suggests the
   metastatic disease was present at initial staging (de novo); a long gap
   suggests true recurrence.

## Decision

| Rule | Value | Config key |
|---|---|---|
| De novo threshold | Primary to metastatic index gap <= 180 days = de novo | `de_novo_primary_gap_days: 180` |
| No prior primary C50 | Automatically de novo regardless of gap | — |

## Classification Logic

```
1. LEFT JOIN patient to primary_dx (MIN C50 primary diagnosis date)
2. If no primary C50 record → de_novo
3. If DATEDIFF('day', primary_date, index_date) <= 180 → de_novo
4. Otherwise → recurrent
```

## Evidence from Data

| Group | n patients |
|---|---|
| No primary C50 diagnosis (direct mBC presentation) | 34 |
| Primary + metastatic C50, gap > 90 days | 70 |
| Primary + metastatic C50, gap <= 90 days | 0 |

All 70 patients with both primary and metastatic diagnoses have a gap > 90 days
(range 91–several years). The 180-day threshold does not change the classification
on this dataset but is set for analytical correctness and future-proofing.

## Rationale

- **180-day threshold:** Used in most breast cancer RWD studies (e.g., Howlader
  et al., BCIRG, SEER-based analyses). A 6-month window captures patients staged
  at initial presentation whose metastatic code was entered with a short lag,
  without misclassifying true early recurrences as de novo.
- **No primary = de novo:** Patients who appear only with a metastatic diagnosis
  code presented with stage IV disease. No prior early-stage record exists in the
  EHR.
- **34 de novo patients:** They have no primary C50 record. Their index date is
  their first metastatic signal.

## Consequences

- `cohort.py` computes `disease_type` using a LEFT JOIN to primary diagnoses.
- The `disease_type` column ('de_novo' | 'recurrent') is preserved in `cohort.csv`.
- Q1 analysis will report HER2 distribution stratified by de novo vs recurrent.

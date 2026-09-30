# ADR-004: Metastatic Index Date Definition

**Status:** Accepted
**Phase:** 02 (cohort-index-date)
**Config keys:** `index_date.source_priority`, `index_date.require_c50_for_diagnosis`

---

## Context

The metastatic index date anchors every downstream analysis: the HER2 biomarker
look-up window, the line-of-therapy count, the de novo/recurrent flag, and
treatment timelines all depend on it. Two sources in the data can signal metastatic
disease for a given patient:

1. **Metastatic diagnosis code** — `diagnosis.diagnosis_type = 'metastatic'` AND
   `diagnosis_code LIKE 'C50%'` (104 patients)
2. **M1/IV staging record** — `staging.m_stage = 'M1'` OR `staging.stage_group = 'IV'`
   (106 patients total; 104 overlap with source 1, 2 staging-only)

In 62 of 104 patients with both sources, the staging date precedes the metastatic
diagnosis date by an average of 135 days. This reflects standard clinical workflow:
imaging detects spread → patient is staged M1 → the formal diagnosis code is entered
later in the EHR.

## Decision

| Rule | Value | Config key |
|---|---|---|
| Index date source | Earliest of (C50 metastatic dx date, M1/IV staging date) | `source_priority: earliest_of_diagnosis_and_staging` |
| C50 required for diagnosis source | true — non-C50 metastatic codes excluded | `require_c50_for_diagnosis: true` |

**Index date = MIN(earliest C50 metastatic diagnosis date, earliest M1/IV staging date)**

For the 2 patients with M1/IV staging but no C50 metastatic diagnosis:
index date = staging date; `index_source = 'staging_only'`.

## Index Source Audit Column

| Value | Meaning |
|---|---|
| `staging_first` | M1/IV staging date <= C50 metastatic diagnosis date |
| `diagnosis_first` | C50 metastatic diagnosis date < M1/IV staging date |
| `staging_only` | No C50 metastatic diagnosis exists |
| `diagnosis_only` | No M1/IV staging record exists |

## Rationale

- **Earliest-of approach:** The first clinical evidence of metastatic disease is
  the true index date. Using the staging date when it precedes the diagnosis code
  avoids assigning an artificially late index that would exclude relevant biomarker
  records and under-estimate time-on-therapy.
- **C50 required for diagnosis source:** Non-C50 metastatic codes (C34.9 lung,
  C61 prostate — 2 patients) are comorbidities, not breast cancer metastases.
  These are flagged by the `non_breast_metastatic_code` DQ check.
- **Staging without C50 metastatic code:** 2 patients have M1/IV staging but no
  C50 metastatic diagnosis code. Including them avoids losing patients whose
  clinical record shows metastatic disease via staging only.

## Evidence from Data

| Metric | Value |
|---|---|
| Patients with C50 metastatic diagnosis | 104 |
| Patients with M1/IV staging | 106 |
| Patients with both sources | 104 |
| Patients with staging-only (no C50 met dx) | 2 |
| Cases where staging date < diagnosis date | 62 of 104 |
| Average gap (staging before diagnosis) | 135 days |

## Consequences

- `cohort.py` uses a FULL OUTER JOIN of the two index date sources.
- `index_source` audit column is preserved in `patient_cohort.csv`.
- Downstream modules (`her2.py`, `treatment.py`) receive `index_date` from
  the cohort table.

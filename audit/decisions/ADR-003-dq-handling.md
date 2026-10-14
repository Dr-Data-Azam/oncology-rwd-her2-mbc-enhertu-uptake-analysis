# ADR-003: Handling future-dated, post-death, and pre-birth records

**Status:** Accepted
**Phase:** 01 (ingest-and-dq)
**Config keys:** `dq.future_date_action`, `dq.post_death_action`, `dq.pre_birth_action`, `dq.post_death_grace_days`

---

## Context

The synthetic dataset contains data quality issues found in Phase 01:
- 1 patient (PAT_001) with `date_of_death` before `date_of_birth`
- 1 future-dated diagnosis, 15 future-dated biomarkers, 5 future-dated medications, 1 future stage
- 2 orphan biomarker patient_ids not in the patient table
- Post-death events that may be legitimate (lab results arriving after death)

A decision is needed on whether to **drop** these records silently or **flag** them and
handle explicitly in downstream modules.

## Decision

**Flag all anomalous records** in `dq_log.csv`; never drop silently. Downstream modules
(cohort.py, her2.py) apply exclusions based on the flagged patient_ids.

A **30-day grace period** applies to post-death events (admin lag for lab results).
Events within 30 days of death are retained; beyond 30 days are flagged for exclusion.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Drop silently | Clean tables immediately | Untraceable; hidden data loss |
| **Flag + handle downstream (chosen)** | Auditable; explicit in dq_log.csv | Slightly more code |
| Flag + drop in DQ step | One place for exclusions | Mixes DQ and cohort logic |

## Rationale

Flagging preserves auditability — every excluded record appears in `dq_log.csv` with its
reason. Any analyst can inspect exactly which patients were excluded
and why. Silent drops are a common RWD pitfall that causes reproducibility failures.

The 30-day grace period reflects standard practice for electronic health records where lab
results, pathology reports, and billing codes arrive days to weeks after the clinical event.

## Evidence from data

| Check | n_flagged |
|---|---|
| death_before_birth | 1 (PAT_001) |
| future_diagnosis_date | 1 |
| future_biomarker_date | 15 |
| future_medication_date | 5 |
| future_stage_date | 1 |
| orphan_biomarker | 2 |
| null_her2_variant | (counted separately — classify_as_unknown) |

## Consequences

- `outputs/dq/dq_log.csv` is the patient-level audit trail for all exclusions.
- `cohort.py` will join against dq_log to exclude flagged patients where `action = flag`.
- Future-dated records are excluded from all downstream analysis.
- Post-death events within 30 days are retained; beyond 30 days are excluded.

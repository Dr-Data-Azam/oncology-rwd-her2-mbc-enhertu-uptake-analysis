# ADR-008: HER2 Tie-break Hierarchy and Conflict Resolution

**Status:** Accepted
**Phase:** 03 (biomarker-derivation)
**Config keys:** `her2.tiebreak_order`, `her2.conflict_resolution`

---

## Context

Multiple HER2 records may fall within the look-up window for a single patient.
Two types of conflicts arise:
1. **Multiple records:** which record to use when a patient has >1 HER2 test in the window?
2. **Result vs variant conflict:** 58 records have `biomarker_result='Negative'` but
   `biomarker_variant='IHC 1+'`. The old binary paradigm called IHC 1+ "Negative"; the
   current HER2-low framework classifies IHC 1+ as HER2-low.

## Decision

### Tie-break order (for multiple records)
```
1. curation_flag        — curated (flag=1) beats uncurated (flag=0)
2. variant_specificity  — non-NULL variant beats NULL; more granular beats less
3. closest_to_index     — record closest to metastatic index date wins
```

### Conflict resolution
```
variant_beats_result_text — biomarker_variant IHC score always overrides biomarker_result label
```

## Evidence

| Conflict type | Count | Resolution |
|---|---|---|
| result='Negative', variant='IHC 1+' | 58 records | variant wins → HER2-low |
| result='Positive', variant=NULL | 20 records | classified as unknown (no IHC score) |
| Duplicate same-date (PAT_015: 2 HER2) | 1 patient | curation_flag → variant_specificity |

## Rationale

- **Curation first:** Curated records (flag=1) have been reviewed by a clinician or
  abstractor and are more reliable than raw EHR extracts.
- **Variant specificity:** A record with an IHC score (`IHC 3+`, `IHC 1+`) is more
  informative than one with only a result text (`Positive`). A granular variant like
  `IHC 0 with faint membrane staining in <=10% cells` beats a generic `IHC 0`.
- **Variant beats result text:** The IHC score is the objective assay measurement.
  The `Positive/Negative` label reflects the old binary paradigm that predates the
  HER2-low and ultralow classifications. Using the score rather than the label is
  clinically correct and consistent with ASCO/CAP 2023 guidelines.

## Consequences

- `her2.py` applies tie-break in a SQL window function ordered by the 3-step hierarchy.
- The chosen record's `curation_flag`, `biomarker_variant`, and `report_date` are
  preserved as audit columns in `patient_her2.csv`.
- The `winning_record_id` column allows any number in the final output to be traced
  back to its source row in the raw `biomarker` table.

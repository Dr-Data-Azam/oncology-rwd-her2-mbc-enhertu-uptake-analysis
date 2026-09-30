# ADR-009: HR Status Derivation

**Status:** Accepted
**Phase:** 03 (biomarker-derivation)
**Config keys:** `hr.*`

---

## Context

HR status (ER/PR positive or negative) is required to stratify the HER2 distribution
(Q1) and define subindications (Q2). The data has two formats for ER/PR values:
- `biomarker_variant`: `"52% positive cells"` (numeric percentage, 364/515 records)
- `biomarker_result`: `"Positive"` or `"Negative"` (text label, all 515 records)
- 151/515 records have NULL variant — no percentage available

## Decision

| Rule | Value | Config key |
|---|---|---|
| HR-positive threshold | ≥ 1% staining | `positive_threshold_pct: 1` |
| ER-low range | 1–10% | `er_low_max_pct: 10` |
| % beats result text | true | `pct_beats_result_text: true` |
| NULL variant fallback | use `biomarker_result` text | `null_variant_fallback: result_text` |

## Classification Logic (applied in `hormone_receptor.py`)

```
1. Extract numeric % from biomarker_variant using regex (\d+)%
2. If % available:
   - % >= 1  → HR-positive
   - % 1–10  → also flag er_low = true
   - % == 0  → HR-negative
3. If % not available (NULL variant):
   - biomarker_result = 'Positive' → HR-positive (er_low unknown, flagged)
   - biomarker_result = 'Negative' → HR-negative
4. HR-positive if EITHER ER ≥1% OR PR ≥1%
```

## Rationale

- **≥1% threshold:** ASCO/CAP 2020 guidelines define ER/PR positivity as ≥1% nuclear
  staining. This is the standard clinical threshold for adult breast cancer.
- **ER-low flag (1–10%):** Patients with ER 1–10% have distinct biology and outcomes
  from strongly ER-positive patients. The ER-low subgroup is clinically relevant for
  CDK4/6 inhibitor and endocrine therapy decisions.
- **% beats result text:** The numeric staining percentage is the objective assay
  measurement. The `Positive/Negative` text label may reflect local lab cutoffs that
  differ from ASCO/CAP 1%.
- **NULL variant fallback:** 151 records have no percentage. Discarding them would lose
  29% of ER/PR data. Falling back to result text is clinically accepted when quantitative
  % is absent (ASCO/CAP allows this). These patients are flagged in `dq_log.csv` as
  `er_pr_null_variant_fallback` and cannot be assessed for ER-low status.

## Evidence from Data

| Scenario | Count |
|---|---|
| ER/PR with numeric % in variant | 364 records |
| ER/PR with NULL variant (fallback to result text) | 151 records |
| ER/PR records total | 515 records |

## Consequences

- `hormone_receptor.py` extracts % with `regexp_extract(biomarker_variant, '(\d+)%', 1)`.
- Patients where fallback was used have `hr_source = 'result_text'` audit column.
- ER-low patients are flagged `er_low = true` in `patient_hr.csv`.

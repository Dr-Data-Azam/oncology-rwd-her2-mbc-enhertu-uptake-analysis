# ADR-006: HER2 Variant → Category Mapping

**Status:** Accepted
**Phase:** 03 (biomarker-derivation)
**Config keys:** `her2.variant_to_category.*`

---

## Context

The biomarker table contains a `biomarker_variant` field with IHC score strings.
These must be mapped to one of five clinical categories for Q1 and Q2 analysis:
**positive**, **low**, **ultralow**, **null**, **unknown**.

The standard changed significantly between 2018 and 2023 (ASCO/CAP guidelines):
- Pre-2023: binary HER2+ / HER2− (IHC 0 and IHC 1+ were both "negative")
- ASCO/CAP 2023: IHC 1+ and IHC 2+/ISH- reclassified as "HER2-low"
- DESTINY-Breast06 (2024): introduced "HER2-ultralow" (IHC 0 with faint staining ≤10%)

Variant strings found in the data and their counts (all biomarker records):

| Variant | Count | Category |
|---|---|---|
| IHC 3+ | 45 | positive |
| IHC 2+; ISH amplified | 21 | positive |
| IHC 2+; ISH negative | 23 | low |
| IHC 1+ | 60 | low |
| IHC 0 with faint membrane staining in <=10% cells | 14 | ultralow |
| IHC 0 absent membrane staining | 15 | null |
| IHC 0 | 30 | null |
| IHC 0 with membrane staining | 9 | unknown |
| IHC equivocal | 4 | unknown |
| Pending | 4 | unknown |
| NULL (no variant) | 64 | unknown |

## Decision

| Variant | Category | Rationale |
|---|---|---|
| IHC 3+ | positive | ASCO/CAP 2018/2023: strong complete membrane staining >10% cells |
| IHC 2+; ISH amplified | positive | Equivocal IHC confirmed by ISH amplification |
| IHC 1+ | low | ASCO/CAP 2023: faint/incomplete staining >10% cells |
| IHC 2+; ISH negative | low | IHC 2+ but ISH non-amplified — HER2-low per 2023 reclassification |
| IHC 0 with faint membrane staining in <=10% cells | ultralow | DESTINY-Breast06 screening criteria |
| IHC 0 absent membrane staining | null | Explicitly documented: no staining |
| IHC 0 (no staining detail) | null | No faint-staining qualifier documented → absent staining assumed |
| IHC 0 with membrane staining | unknown | Staining present but % not documented → cannot confirm ≤10% ultralow |
| IHC equivocal | unknown | Indeterminate — no category assignable |
| Pending | unknown | Result not yet available |
| NULL variant | unknown | No IHC score → cannot classify |

## Two Ambiguous Cases

**IHC 0 (plain, no detail) → null:** Under ASCO/CAP 2023, ultralow requires explicit
documentation of faint staining. Absence of the "faint staining" qualifier means no staining
is documented. Classified as null (conservative). 30 records, 9 patients in window affected.

**IHC 0 with membrane staining → unknown:** Staining is documented but no percentage is given.
Cannot confirm ≤10% threshold required for ultralow. Unknown is safer than over-assigning
ultralow. 9 records, 5 patients in window affected.

## Consequences

- `her2.py` builds the SQL CASE statement dynamically from `cfg['her2']['variant_to_category']`.
  Changing a mapping means editing config only — no code change required.
- Patients with `biomarker_result = 'Negative'` but `biomarker_variant = 'IHC 1+'` are
  classified as **low** (variant wins — ADR-008).
- The `her2_variant` audit column in `patient_her2.csv` records the exact variant string
  that drove the classification.

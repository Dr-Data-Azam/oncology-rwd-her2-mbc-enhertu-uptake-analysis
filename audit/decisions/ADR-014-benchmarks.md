# ADR-014: Literature benchmarks for HER2 and HR distribution in mBC

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Phase** | 04 |
| **Config keys** | `benchmarks.*` |
| **Module** | `src/her2rwd/q1_distribution.py` |
| **Approved by** | Azam Uddin |
| **Date** | 2026-09-29 |
| **Revised** | 2026-09-29 — citations corrected after verification; ultralow range updated; null key renamed |

---

## Context

Q1 asks: "Is this data asset feasible for HER2-defined mBC studies?" To give a meaningful
answer, we compare the observed HER2 distribution against published real-world and clinical
trial screening benchmarks.

All benchmark ranges were confirmed against primary papers during Phase 04 (2026-09-29).
Citations are sourced from primary publications; no further review required before delivery.

---

## Denominator definitions

**Comparisons 1–3** use % of **classifiable patients** (positive + low + ultralow + null).
Unknown HER2 patients are excluded because published literature similarly excludes untested
or unevaluable patients.

**Comparison 4** uses % of **HER2-zero** (null + ultralow combined) as the denominator,
because the ultralow benchmark comes from rescoring studies of IHC-0 cases — a different
denominator than the full classifiable population.

---

## Benchmark values (verified 2026-09-29)

| Category | Range | Denominator | Source | Notes |
|---|---|---|---|---|
| HER2-positive | 15–20% | classifiable | Tarantino et al. **JCO 2020** (38:1951–62) | Confirmed correct range; year was previously wrong (2022 → 2020) |
| HER2-low | 45–55% | classifiable | Schettini et al. **NPJ Breast Cancer 2021** (7:103); Modi NEJM 2022 | Journal was previously wrong (Lancet Oncol → NPJ Breast Cancer) |
| HER2-zero (null+ultralow combined) | 25–35% | classifiable | Complement fraction in published mBC series | Previous key named `her2_null_pct_range` — renamed to `her2_zero_pct_range` to clarify the IHC-0 total denominator |
| Ultralow (of HER2-zero) | 35–50% | HER2-zero | Curigliano et al. **NEJM 2024** (DB-06); IHC-0 rescoring studies | Previously 20–30% — corrected upward; DB-06 enrollment ≠ prevalence estimate; rescoring studies show 35–50% |
| HR-positive | 65–75% | all patients | SEER Cancer Stat Facts: Female Breast Cancer Subtypes | Confirmed correct |

---

## Key corrections from initial values

| Field | Old value | Corrected value | Reason |
|---|---|---|---|
| Tarantino citation year | JCO 2022 | **JCO 2020** (vol 38 no 17) | Landmark HER2-low paper is 2020; 2022 ref is an ASCO abstract |
| Schettini journal | Lancet Oncol 2021 | **NPJ Breast Cancer 2021** (7:103) | Paper was published in NPJ Breast Cancer, not Lancet Oncology |
| `her2_null_pct_range` | [25, 35] | renamed `her2_zero_pct_range: [25, 35]` | Literature benchmarks IHC-0 as a whole (null+ultralow), not null-only |
| `her2_ultralow_of_null_pct` | [20, 30] | renamed `her2_ultralow_of_zero_pct: [35, 50]` | Rescoring studies find 35–50%; DB-06 enrollment figure is not a prevalence estimate |

---

## Consequences

- `q1_benchmark.csv` reports four rows: positive, low, her2_zero, ultralow-of-zero.
- Individual null and ultralow rows (vs classifiable) have no standalone literature benchmark
  and are omitted from the benchmark comparison table.
- All out-of-range observations are expected for synthetic data and are noted explicitly.
- `source_citation` in config carries the full corrected citation string used in the deck and HTML.

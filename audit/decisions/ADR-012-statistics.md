# ADR-012: Statistics — Wilson CIs and small-cell flagging

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Phase** | 04 |
| **Config keys** | `stats.ci_method`, `stats.ci_z`, `stats.small_cell_threshold` |
| **Module** | `src/her2rwd/statistics.py` |
| **Approved by** | Azam Uddin |
| **Date** | 2026-09-29 |

---

## Context

The analysis reports proportions (HER2 category distributions, Enhertu uptake rates) for
a cohort of 103 patients, with some sub-cells containing fewer than 11 patients. Two
statistical choices are required:

1. **Confidence interval method** — which method to use for a proportion p = n/N.
2. **Small-cell threshold** — below what count should a cell be suppressed or flagged.

---

## Options considered

### CI method

| Method | Pros | Cons |
|---|---|---|
| Normal approximation (Wald) | Simple | Fails at p≈0 or p≈1; unreliable for n<30 |
| Wilson score | Handles p≈0/1; exact; well-behaved for small n | Slightly more complex formula |
| Clopper-Pearson (exact) | Conservative, exact | Overly wide; rarely used in RWD |
| Bootstrap | Non-parametric | Overkill for proportions; adds randomness |

### Small-cell threshold

- n<5: threshold used in some academic papers; too permissive for RWD privacy practice.
- n<11: standard in real-world oncology data (HealthVerity, Flatiron, NCDB); aligns with
  most state health data reporting rules.
- n<15: used in some payer databases; too conservative for 103-patient feasibility analysis.

---

## Decision

**CI method: Wilson score** with z=1.96 (95% two-sided).

**Small-cell threshold: n < 11** — display as `n<11`, do not publish exact count.

---

## Rationale

Wilson is the practical standard for proportions in RWD oncology publications. It handles
the cells near 0% (e.g., ultralow at 3/103) without inflating confidence bounds or
producing negative lower limits. The formula is closed-form and exact.

n<11 is the de facto RWD standard. With 103 patients total, several sub-strata will have
n<11; this threshold ensures we flag them without suppressing the majority of cells.

---

## Consequences

- `statistics.py` implements `wilson_ci(n, N, z)` and `build_distribution(counts, total, threshold)`.
- All tables produced by Q1, Q2, and sensitivity use these helpers.
- Any cell where n < 11 gets `small_cell = True` in the CSV; the deck and HTML show `n<11`.
- The denominator is always reported alongside every proportion.

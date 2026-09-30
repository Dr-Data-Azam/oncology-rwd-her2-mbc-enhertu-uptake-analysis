# ADR-007: HER2 Look-up Window

**Status:** Accepted
**Phase:** 03 (biomarker-derivation)
**Config keys:** `her2.window_days.pre_index`, `her2.window_days.post_index`

---

## Context

73 of 150 patients have HER2 biomarker records dated **before** their metastatic index date.
These are from primary disease workup (biopsy at initial breast cancer diagnosis). They are
valid HER2 results and should be included in the classification — but only within a
defensible look-back window.

## Decision

| Direction | Window | Config value |
|---|---|---|
| Pre-index (look-back) | 365 days before metastatic index date | `pre_index: 365` |
| Post-index (look-forward) | 90 days after metastatic index date | `post_index: 90` |

## Options Considered

| Window | Pros | Cons |
|---|---|---|
| No window (all records) | Simplest | Very old tests may not reflect metastatic biology |
| 180d pre / 90d post | Tighter | Misses ~30% of valid primary workup records |
| **365d pre / 90d post (chosen)** | Captures primary workup; limits very stale tests | Standard in HER2 mBC literature |

## Rationale

A 365-day pre-index window captures biomarkers from:
1. Initial primary diagnosis (often 6–12 months before metastatic staging)
2. Restaging at metastatic recurrence (within weeks of index)

90 days post-index captures confirmatory tests ordered at metastatic staging but
reported a few weeks later (common in academic centres).

Tests older than 12 months before metastatic diagnosis are considered too remote to
reliably reflect metastatic HER2 status and are excluded.

## Consequences

- `her2.py` filters `biomarker` to `report_date BETWEEN index_date - 365 AND index_date + 90`.
- Patients with no HER2 record in this window are classified as `unknown`.
- Window boundaries are sourced from config — changing them triggers a sensitivity run.

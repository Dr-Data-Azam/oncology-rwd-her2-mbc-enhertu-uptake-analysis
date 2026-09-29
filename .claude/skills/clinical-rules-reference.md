# clinical-rules-reference

Authoritative reference for clinical definitions used in this analysis.
All items marked VERIFY must be confirmed with a citation before being stated as fact in the
deck or in an ADR.

---

## HER2 Categories (ASCO/CAP 2018/2023 guidelines + DESTINY-Breast trial definitions)

| Category | Rule | Source |
|---|---|---|
| HER2-positive | IHC 3+, OR IHC 2+ with ISH amplified | ASCO/CAP 2018 |
| HER2-low | IHC 1+, OR IHC 2+ with ISH not amplified | DESTINY-Breast04 eligibility |
| HER2-ultralow | IHC 0 with faint/barely perceptible, incomplete membrane staining in >0 and ≤10% of cells | DESTINY-Breast06 eligibility (VERIFY exact wording) |
| HER2-0 / null | IHC 0 with absent membrane staining | ASCO/CAP |
| HER2-0 unspecified | IHC 0 with no staining detail — cannot be split into ultralow vs null | Data limitation |
| Unknown / indeterminate | Equivocal without ISH follow-up, Pending, blank variant + Unknown result, irresolvable conflicts | |

**Conflict rule (in this analysis):** granular variant beats coarse result; curated beats EHR.
State this as an explicit rule in ADR-008.

---

## HR Status (ASCO/CAP guidelines)

- HR+ = ER ≥1% OR PR ≥1%
- ER-low = ER 1–10% (flag separately; relevant for DB-06 eligibility) (VERIFY)
- When result text and percentage conflict: the percentage wins (per ASCO/CAP 2020 update) (VERIFY)

---

## Enhertu (trastuzumab deruxtecan, T-DXd) Approved Indications — mBC (VERIFY ALL)

| Trial | Indication | Line |
|---|---|---|
| DESTINY-Breast03 | HER2+ mBC after ≥1 prior anti-HER2 regimen | 2L+ |
| DESTINY-Breast09 | HER2+ mBC 1L with pertuzumab (check approval status) | 1L (VERIFY) |
| DESTINY-Breast04 | HR+ or HR− HER2-low mBC after ≥1 prior chemo in the metastatic setting | 2L+ |
| DESTINY-Breast06 | HR+ HER2-low or HER2-ultralow mBC after ≥1 endocrine therapy, chemo-naive in the metastatic setting | 1L chemo (VERIFY FDA approval date; reported January 2025) |

---

## Competitor Map by Subindication

| Subindication | Key competitors |
|---|---|
| HER2+ mBC | trastuzumab + pertuzumab + taxane (HP+T, 1L standard); T-DM1 (Kadcyla, 2L); tucatinib + trastuzumab + capecitabine (HER2CLIMB) |
| HR+/HER2-low | CDK4/6i + AI or fulvestrant (1L standard); capecitabine; sacituzumab govitecan (TNBC and HR+/HER2− later lines) |
| HR+/HER2-ultralow | Same as HR+/HER2-low (DB-06 expands Enhertu eligibility to this group) |

---

## Literature Benchmarks (approximate; VERIFY and cite before stating in deck)

| Measure | Approximate value | Notes |
|---|---|---|
| HER2+ share of mBC | ~15–20% | VERIFY citation |
| HER2-low share of mBC | ~45–55% | VERIFY citation (Schettini et al., or similar) |
| HER2-0 share of mBC | ~25–35% | VERIFY |
| HER2-ultralow share of former HER2-0 (HR+) | ~20–30% | VERIFY (DB-06 screening data) |
| HR+ share of mBC | ~65–75% | VERIFY |

Deviations from these benchmarks in the synthetic dataset should be explained through:
synthetic enrichment for Enhertu-eligible patients, EHR blank-variant rate (46%), and
window choice.

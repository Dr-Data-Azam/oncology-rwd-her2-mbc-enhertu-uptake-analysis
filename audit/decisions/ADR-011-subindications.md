# ADR-011: Subindication framework (required + exploratory groups)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Phase** | 06 |
| **Config keys** | `subindications.required`, `subindications.exploratory` |
| **Module** | `src/her2rwd/q2_uptake.py` |
| **Approved by** | Azam Uddin |
| **Date** | 2026-09-29 |

---

## Context

Q2 asks: "How does Enhertu uptake compare with competitors across HER2-defined subindications?
Is this asset fit for a commercial or feasibility question about Enhertu in mBC?"

The term "subindication" means the HER2 × HR-defined clinical subgroup corresponding to a
specific Enhertu indication or trial population. Defining them precisely allows the uptake
analysis to speak directly to the populations clients care about (feasibility buyers,
commercial teams, and clinical researchers).

---

## Subindication assignment

Each patient is assigned exactly one subindication based on (her2_category, hr_status):

| her2_category | hr_status | Subindication | Trial reference |
|---|---|---|---|
| positive | any | her2_positive | DB-03 (2L+); DB-09: T-DXd+pertuzumab 1L (approved Dec 15, 2025) |
| low | positive | hr_pos_her2_low | DB-04 (2L+); DB-06: after ≥1 ET metastatic (approved Jan 27, 2025) |
| low | negative | hr_neg_her2_low | DB-04 (2L+) |
| low | unknown | her2_low_hr_unknown | DB-04 (cannot assign arm) |
| ultralow | positive | hr_pos_her2_ultralow | DB-06: after ≥1 ET metastatic (approved Jan 27, 2025) |
| ultralow | negative | hr_neg_her2_ultralow | No approved indication |
| ultralow | unknown | her2_ultralow_hr_unknown | DB-06 (cannot assign arm) |
| null | any | her2_null | No Enhertu indication |
| unknown | any | her2_unknown | Cannot classify |

---

## Required vs exploratory

**Required** (report uptake + CI + competitor map + discordance):
- `her2_positive` — Enhertu approved 2L+ per DB-03
- `hr_pos_her2_low` — Enhertu approved 2L+ per DB-04 (primary population)
- `hr_neg_her2_low` — Enhertu approved 2L+ per DB-04 (secondary population)
- `hr_pos_her2_ultralow` — Enhertu emerging indication per DB-06 (2024)

**Exploratory** (report n and uptake only; flag all small cells):
- `her2_null` — no Enhertu label; useful for discordance completeness
- `her2_unknown` — HER2 not tested; 23 patients received Enhertu → primary discordance finding

---

## Rationale

Named clinical subindications (rather than HER2 category alone) are preferred because:
1. They map directly to DB-03/04/06 trial populations — language clients recognize.
2. HR status within HER2-low matters clinically (different prognosis, CDK4/6i use).
3. HER2-ultralow requires HR+ context for DB-06 relevance.
4. The deck can reference specific labeled indications without ambiguity.

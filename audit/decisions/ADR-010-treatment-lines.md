# ADR-010: Regimen grouping and line-of-therapy approximation

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Phase** | 05 |
| **Config keys** | `treatment.regimen_window_days`, `treatment.new_line_gap_days`, `treatment.drug_class_map` |
| **Module** | `src/her2rwd/treatment.py` |
| **Approved by** | Azam Uddin |
| **Date** | 2026-09-29 |

---

## Context

The medication table provides drug start dates but no explicit end dates, line-of-therapy
numbers, or regimen labels. Q2 requires knowing which line of therapy Enhertu was received
in (1L, 2L, 2L+) and what competing regimens patients received. Two parameters govern the
heuristic: how wide to group concurrent drugs (regimen window) and how long a gap signals
a new line of therapy (line gap).

---

## Algorithm (date-proximity heuristic)

1. **Anchor:** Treatment events are restricted to on/after each patient's metastatic index
   date. Pre-metastatic (adjuvant/neoadjuvant) treatments are excluded.
2. **De-duplication:** Per (patient_id, med_generic_name, med_date), keep curated record
   (curation_flag=1) first; otherwise any record. Prevents inflated regimen counts.
3. **Regimen grouping:** Sort drugs by date within patient. A new regimen starts when the
   gap from the previous drug's start date to the current drug's start date exceeds
   `regimen_window_days` (28). Drugs within 28 days of each other = concurrent = one regimen.
4. **Line assignment:** Sort regimens by start date. A new LINE starts when the gap from
   the previous regimen's start date to the current regimen's start date exceeds
   `new_line_gap_days` (90). Regimens within 90 days of the prior regimen's start are
   counted as the same line (concurrent or sequential within one line).
5. **Collapse:** Multiple regimens within the same line are merged into one row per patient
   per line.

---

## Parameter values and rationale

### Regimen window: 28 days

Represents one standard chemotherapy cycle. Drugs starting within 28 days of each other
are treated as concurrent (same regimen). This is the standard used by Flatiron Health and
the ASCO CancerLinQ real-world LOT algorithms.

Alternative considered: 21 days (three-week cycle). Rejected because some combination
regimens (e.g., pertuzumab + trastuzumab, monthly dosing) would be split incorrectly.

### New line gap: 90 days

A gap of more than 90 days between regimen starts signals disease progression and the
start of a new line of therapy. 90 days is the standard RWD gap used by Flatiron,
HealthVerity, and ASCO real-world LOT consensus guidelines.

Alternative considered: 60 days — rejected as too sensitive; would split continuous
oral therapies (endocrine therapy often continues across lines).
Alternative considered: 180 days — rejected as too conservative; would collapse true
sequential lines in rapidly progressing patients.

### Treatment anchor: first medication on/after index date

The metastatic index date is the clinical anchor for all LOT counting. Any medication
administered before the index date is excluded (may represent adjuvant or neoadjuvant
treatment). Line 1 = first treatment regimen on or after the metastatic index date.

---

## Drug class map

| Generic name | Class | Rationale |
|---|---|---|
| trastuzumab deruxtecan | her2_adc | Primary study drug (Enhertu) |
| ado-trastuzumab emtansine | her2_adc | HER2-targeted ADC (T-DM1 / Kadcyla) |
| trastuzumab | her2_mab | HER2-targeted monoclonal antibody |
| pertuzumab | her2_mab | HER2-targeted monoclonal antibody |
| tucatinib | her2_tki | HER2-targeted tyrosine kinase inhibitor |
| palbociclib, abemaciclib, ribociclib | cdk46i | CDK4/6 inhibitors |
| anastrozole, letrozole, fulvestrant | endocrine | Endocrine therapies |
| paclitaxel, nab-paclitaxel, capecitabine | chemo | Chemotherapy |
| sacituzumab govitecan | trop2_adc | TROP2-targeted ADC (Trodelvy) |

---

## Limitations

- No end dates in the data — gap heuristic approximates progression, not true LOT.
- Continuous therapies (e.g., endocrine) cannot be distinguished from maintenance vs
  new initiation without explicit discontinuation dates.
- Small cohort (103 patients): LOT sub-strata will have n<11 cells — flagged per ADR-012.
- Synthetic data — LOT patterns may not reflect real-world mBC treatment sequences.

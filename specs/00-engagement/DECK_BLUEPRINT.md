# Deck Blueprint: 5 Slides + Appendix

Source of truth for the `deck-builder` skill and Phase 07. `[X]` = filled from `outputs/tables/`; never type a number that isn't in a table.

## What the reviewer is really grading
The deck answers the evaluation criteria in the instructions. Map every slide to them:

| Criterion (from the instructions) | Where it is proven |
|---|---|
| Cohort construction and defensible event indexing | Slide 2 + Appendix B |
| Clinical logic for HER2 and HR derivation | Slide 2 (logic) + Slide 3 (results) + Appendix D |
| Reasoning through data quality and ambiguity | Slide 3 (unknowns, sensitivity) + Slide 5 + Appendix A |
| Analytical depth and clarity | Slides 3 and 4 |
| Communication and production-minded thinking | Slide 1 (answer first) + Slide 5 (productionize) + Appendix C |

The reviewer reads the deck **before** the call, so it must **stand alone without narration**. The frame is a **client feasibility readout**, not a homework report.

## Global rules
- **Action titles:** every title is the finding as a sentence ("HER2-low is the largest group, but a third of patients cannot be sub-classified"), not a topic ("HER2 Distribution").
- **Every % has n and a denominator.** Show 95% Wilson CIs where n is small; flag cells with n < 11.
- **Always show "Unknown" as its own bar.** Hiding it is the #1 red flag in feasibility work.
- **One consistent HER2 colour scheme** across all slides (positive / low / ultralow / 0-null / 0 NOS / unknown).
- **Footer on every slide:** "Fully synthetic data · Source: outputs/tables/<file>.csv · Rule set v1 (ADR-xxx)".
- **Density:** one main visual and a 3-bullet "so what" per slide. The depth goes in the HTML notebook.
- Clinical facts (labels, benchmarks) carry citations. Anything unverified is not shown.

---

## Slide 1: Executive summary (answer first)
**Title (example):** "The asset supports HER2+ vs HER2− feasibility today; HER2-low and ultralow uptake questions require curated IHC detail"

| Left: 3 key findings | Right: fit-for-purpose scorecard |
|---|---|
| **Q1:** Final cohort N = [X] mBC patients. HER2: positive [X]%, low [X]%, ultralow [X]%, 0/null [X]%, unknown or unresolved [X]%. Directionally consistent / inconsistent with the literature because [reason]. | Traffic-light table: mBC identification 🟢 · index date 🟢/🟡 · HER2+ vs − 🟢 · HER2-low 🟡 · HER2-ultralow 🔴/🟡 · HR status 🟢/🟡 · treatment timing 🟡 · line of therapy 🟡 · sample size 🔴 |
| **Q2:** Enhertu reaches [X]% of HER2+, [X]% of HR+/HER2-low, [X]% of HR+/ultralow; median [X] days from metastatic diagnosis, typically at line [X]. | |
| **Verdict:** Fit for [..], fit with caveats for [..], not fit for [..]. | |

**Bottom strip: 3 recommendations to the client** (e.g. prioritise curated records for HER2 sub-classification · add IHC staining detail abstraction · add line-of-therapy fields).
**Speaker note (1.5 min):** "If you remember one thing: …"

## Slide 2: Cohort and method (how I built it)
**Title:** "[N] of 150 patients form an analysis-ready mBC cohort, anchored on a breast-specific metastatic index date"
- **Left, attrition flow (CONSORT style):** 150 → excluded non-breast (22) → implausible demographics/DQ ([X]) → no metastatic evidence ([X]) → **final N**, split de novo [X] / recurrent [X].
- **Right, logic boxes:**
  1. **Index date** = earliest of C50 metastatic diagnosis or M1/stage IV staging (rule + source priority).
  2. **HER2 at index** = window [−X/+Y] days → hierarchy: detailed IHC variant > coarse result → curated > EHR → closest to index → conflict rule.
  3. **HER2 mapping** (ASCO/CAP 2023 + DESTINY-Breast06 ultralow definition).
  4. **HR+** = ER or PR ≥ 1% (percentage beats result text).
- **So what:** "Most HER2 tests fall after the metastatic date, so the window choice matters. Tested on Slide 5."
**Speaker note (3 min):** walk through the index date and why the window extends after the index date.

## Slide 3: Q1, HER2 distribution at metastatic diagnosis
**Title:** "HER2-low is the largest group, but [X]% cannot be sub-classified, driven almost entirely by EHR records lacking IHC detail"
- **Main visual:** 100% stacked horizontal bars, one row each for **Overall** · HR+ / HR− · curated / EHR · academic / community · de novo / recurrent. Every row labelled with n.
- **Side panel, literature check:** observed vs expected ranges (HER2+ ~15–20%, HER2-low ~45–55%, …, **cite**), marked ✓ directionally credible / ⚠ deviates, with the reason (synthetic enrichment, missingness, window).
- **Callout, uncertainty:** "[X] patients ([X]%) unresolved: [a] unknown/pending, [b] HER2− without IHC score, [c] IHC 0 without staining detail."
- **So what:** "Curation is the difference between a binary HER2 answer and a HER2-low/ultralow answer." This is the key commercial insight for Nexus Health Data's curated data.
**Speaker note (3 min).**

## Slide 4: Q2, Enhertu uptake by subindication
**Title:** "Enhertu reaches [X]% of HER2+ but [X]% of HR+/HER2-low patients, mostly as a 2nd-line therapy after CDK4/6 + endocrine therapy"
- **Main table:**

| Subindication | n | % Enhertu (95% CI) | Median days to Enhertu | Typical line | Top therapy before | Top therapy instead (never Enhertu) |
|---|---|---|---|---|---|---|
| HER2+ | | | | | e.g. trastuzumab + pertuzumab + taxane | e.g. T-DM1 / tucatinib |
| HR+/HER2-low | | | | | e.g. CDK4/6i + AI | e.g. capecitabine / sacituzumab |
| HR+/HER2-ultralow | | | | | | |
| Exploratory: HR−/HER2-low · HER2-0/null (control) · Unknown | | | | | | |

- **Small visual:** line-sequence bars (1L → 2L → 3L share by drug class) for the two largest subindications.
- **Discordance callout:** "[X] patients with treatment not aligned to the documented biomarker profile": Enhertu in HER2-0/null or unknown ([X]) · anti-HER2 therapy in HER2-negative ([X]) · endocrine/CDK4/6i in HR− ([X]) · Enhertu dispensed before the HER2 result date ([X]). Show one illustrative patient timeline.
- **So what:** a commercial reading (where the headroom is) plus the caveat that n is small.
**Speaker note (3 min).**

## Slide 5: Robustness, fitness and productionization
**Title:** "Conclusions hold under alternative rules except HER2-low vs ultralow; a production version needs curated IHC detail and a governed rules engine"
- **Left, sensitivity table:** rows = primary rule, −365/+90 window, curated-only, "highest HER2 ever", "IHC 0 with staining = null". Columns = % HER2+, % low, % ultralow, % unresolved, % Enhertu in HR+/low. Highlight what moves.
- **Middle, limitations:** synthetic data · small n · no line-of-therapy or end dates · diagnosis-based index date · EHR missingness.
- **Right, how I'd productionize:**
  - rules-as-config (versioned YAML plus decision records)
  - SQL/dbt models
  - unit tests per clinical rule
  - DQ monitors and drift alerts
  - per-patient audit trail
  - abstraction QA sampling
  - scale to the full network
- **Next steps for the client:** e.g. a 2-week pilot on curated records, and an HER2 IHC detail abstraction add-on.
**Speaker note (3 min).**

---

## Appendix (the required "data quality checks and key assumptions" section)

**A. Data quality checks.** Table: check · table · rows/patients affected · action (exclude/flag/fix) · ADR. Covers the 15 traps: orphans, pediatric and implausible DOBs, death before birth, post-death and future dates, non-breast metastatic codes, blank stage group derived from M, HER2 and ER/PR result conflicts, EHR blank variants, duplicates, and more.

**B. Assumptions and tie-break rules.** Table: decision · primary rule · alternative tested · impact · ADR ID. Covers eligibility, index date, de novo/recurrent, HER2 window, HER2 mapping, HER2 tie-break, HR rule, regimen/line rule, subindications, statistics.

**C. Reproducibility and repo map.** Pipeline diagram (raw → DQ → cohort → HER2/HR → lines → Q1/Q2 → report), the 7 audit layers, the rerun command, input hash check, validation report status (all PASS).

**D. (Optional) Definitions.** The HER2 category table with IHC criteria, subindication definitions, the drug class map, and literature sources.

**E. (Optional) Discordant case listing.** Patient-level table with the reason for each flag.

## 15-minute talk track
| Min | Slide |
|---|---|
| 0–1.5 | 1: the answer |
| 1.5–4.5 | 2: how the cohort and rules were built |
| 4.5–7.5 | 3: Q1 |
| 7.5–10.5 | 4: Q2 |
| 10.5–13 | 5: robustness + productionize |
| 13–15 | Appendix C: 2-minute repo walkthrough (one patient from raw row to slide) |

## Red flags to avoid
- Topic titles instead of findings.
- Percentages without n, and no "Unknown" category.
- Code screenshots in the deck.
- Stating Enhertu label facts or benchmarks without a citation.
- Treating synthetic results as real-world truth. Always frame as "if this were production data, this would mean…".
- Overcrowded slides. If it needs a zoom, move it to the notebook.

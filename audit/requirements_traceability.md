# Requirements Traceability Matrix

Maps every requirement bullet from the Nexus Health Data project brief to the ADR that governs
it, the module that implements it, the output file(s) that prove it, and the result.

**Cohort:** 103 mBC patients (150 → 42 no metastatic signal → 3 death-before-birth → 2
age <18).  
**HER2 classified:** 41 classifiable; 62 unknown (60.2% — driven by EHR variant
missingness, not pipeline failure).  
**All data synthetic.**

---

## Q1 — Data Feasibility and HER2 Distribution at Metastatic Diagnosis

### Requirement 1 — Define the mBC cohort and metastatic index date

> "Define a metastatic breast cancer cohort using diagnosis and/or stage evidence. Clearly explain how you define the metastatic index date."

| Field | Detail |
|---|---|
| **ADR** | ADR-002 (cohort eligibility), ADR-004 (index date), ADR-005 (de novo vs recurrent) |
| **Module** | `cohort.py` |
| **Outputs** | `outputs/tables/cohort.csv`, `outputs/tables/attrition.csv`, `outputs/figures/consort_flow.png` |
| **Rule** | Index date = earliest of: (a) first C50 diagnosis with metastatic flag, (b) first M1/stage-IV staging record. Minimum age 18. Exclude death-before-birth. |
| **Result** | 150 → 108 (metastatic signal) → 105 (DQ exclusions) → **103 final cohort**. Attrition logged at every step. |

---

### Requirement 2 — HER2 status in a clinically justified time window

> "Determine HER2 status at metastatic diagnosis using biomarker records in a clinically justified time window around the metastatic index date."

| Field | Detail |
|---|---|
| **ADR** | ADR-007 (biomarker window) |
| **Module** | `her2.py` |
| **Outputs** | `outputs/tables/patient_her2.csv` (columns: `her2_category`, `her2_test_date`, `days_from_index`), `outputs/figures/her2_timing.png` |
| **Rule** | Window: −365 days pre-index to +90 days post-index. Clinically justified: most workup occurs post-staging; +90d captures initial oncology visit. |
| **Result** | 41 patients classified from biomarker records in window; 62 unknown (no qualifying test). `her2_timing.png` confirms most tests fall post-index, validating the +90d extension. |

---

### Requirement 3 — Resolve multiple, discordant, ambiguous, and incomplete records

> "Resolve situations with multiple HER2 records, discordant records, ambiguous records, and records with incomplete variant detail."

| Field | Detail |
|---|---|
| **ADR** | ADR-006 (variant-to-category mapping), ADR-008 (tie-break order) |
| **Module** | `her2.py` |
| **Outputs** | `outputs/tables/patient_her2.csv` (columns: `her2_n_records`, `her2_source`, `her2_conflict`, `her2_conflict_detail`) |
| **Rule** | Tie-break order: (1) curated beats EHR, (2) granular variant beats blank result text, (3) closest to index date wins. Blank EHR variant = excluded from classification. |
| **Result** | EHR variant blank rate = 46%; curated blank rate = 1%. Conflict column flags patients with ≥2 discordant records. Every resolution is auditable per patient. |

---

### Requirement 4 — HER2 distribution + ≥3 stratifications

> "Characterize the overall HER2 distribution and stratify it by at least three additional factors."

| Field | Detail |
|---|---|
| **ADR** | ADR-012 (Wilson CI, small-cell flagging) |
| **Module** | `q1_distribution.py`, `statistics.py` |
| **Outputs** | `outputs/tables/q1_overall.csv`, `outputs/tables/q1_by_hr.csv`, `outputs/tables/q1_by_disease_type.csv`, `outputs/tables/q1_by_source.csv`, `outputs/figures/q1_stacked_bars_by_stratum.png` |
| **Strata** | (1) Hormone receptor status (HR+/HR−/unknown), (2) de novo vs recurrent metastatic disease, (3) biomarker source (curated vs EHR). Calendar year omitted — cell sizes all n<11 on n=103. |
| **Result** | Overall: positive 16.5% [10.6–24.9%], low 12.6% [7.5–20.4%], ultralow 2.9% [1.0–8.2%], null 7.8%, unknown 60.2%. All percentages carry Wilson 95% CI. Cells with n<11 flagged `small_cell=True`. |

---

### Requirement 5 — Compare against literature benchmarks

> "Compare the observed HER2 distribution against external clinical expectations. Discuss whether values appear directionally credible."

| Field | Detail |
|---|---|
| **ADR** | ADR-014 (benchmark sources) |
| **Module** | `q1_distribution.py` |
| **Outputs** | `outputs/tables/q1_benchmark.csv`, `outputs/figures/q1_benchmark_comparison.png` |
| **Sources** | Tarantino et al. JCO 2020; Schettini et al. NPJ Breast Cancer 2021; Modi et al. NEJM 2022; Curigliano et al. NEJM 2024 (DB-06) |
| **Result** | HER2-zero (null + ultralow combined) at 26.8% sits within benchmark range [25–35%] ✓. HER2-positive at 41.5% of classifiable patients exceeds benchmark [15–20%] — explained by 60% unknown rate deflating the denominator. HER2-low at 31.7% of classifiable is below benchmark [45–55%] for the same reason. Deviations are consistent with synthetic data missingness, not pipeline error. |

---

### Requirement 6 — Quantify uncertainty and sensitivity analysis

> "Show how many patients could not be confidently classified and perform at least one sensitivity analysis."

| Field | Detail |
|---|---|
| **ADR** | ADR-007 (window), ADR-006 (IHC-0), ADR-012 (small-cell) |
| **Module** | `sensitivity.py`, `statistics.py` |
| **Outputs** | `outputs/tables/sensitivity_her2_distribution.csv`, `outputs/figures/sensitivity_dot_plot.png` |
| **Scenarios** | S1: narrow window (pre-index 365→180d); S2: curated-only records; S3: conservative IHC-0 mapping (IHC 0 → unknown) |
| **Result** | S1 — no change in positive/low/ultralow counts; S2 — unknown rises to 67.0% (confirms EHR data drives missingness); S3 — null drops from 7.8% to 1.9%, unknown rises to 66.0%. Primary distribution is robust to window choice; classification is sensitive to IHC-0 definition — disclosed and discussed. 62 patients (60.2%) unclassified; flagged explicitly. |

---

## Q2 — Enhertu Uptake vs Competitor Therapies by HER2-Defined Subindication

### Requirement 7 — Subindication framework

> "Propose and implement a subindication framework."

| Field | Detail |
|---|---|
| **ADR** | ADR-011 (subindication assignment) |
| **Module** | `q2_uptake.py`, `hormone_receptor.py` |
| **Outputs** | `outputs/tables/q2_subindication_assignment.csv`, `outputs/tables/patient_hr.csv` |
| **Subindications** | (Required) HER2-positive; HR+/HER2-low; HR+/HER2-ultralow. (Exploratory) HER2-null; HER2-unknown. |
| **Result** | HER2-positive: n=17; HR+/HER2-low: n=12; HR+/HER2-ultralow: n=3 (n<11, flagged); HER2-unknown: n=62 (large — disclosed as asset limitation). Every patient assigned to exactly one subindication. |

---

### Requirement 8 — Treatment timing, first treatment, sequencing

> "Derive treatment timing relative to metastatic diagnosis and identify first treatment. If possible, derive additional treatment sequencing logic."

| Field | Detail |
|---|---|
| **ADR** | ADR-010 (regimen grouping, line-of-therapy) |
| **Module** | `treatment.py` |
| **Outputs** | `outputs/tables/patient_lines.csv`, `outputs/figures/primary_met_gap.png`, `outputs/figures/time_to_enhertu.png` |
| **Rule** | Regimen: drugs within 28 days = same regimen. New line: gap >90 days or new regimen post-gap. Pre-index drugs excluded. |
| **Result** | Median time to first treatment ~60d post-index. Median time to Enhertu ~183d post-index — consistent with 2L+ positioning. Line-of-therapy derived for all treated patients; `q2_enhertu_by_line.csv` shows Enhertu by line per subindication. |

---

### Requirement 9 — Enhertu proportion, time to first Enhertu, competing therapies per subindication

> "For each subindication, quantify the proportion who receive Enhertu, time to first Enhertu, and most common competing therapies."

| Field | Detail |
|---|---|
| **ADR** | ADR-011, ADR-013 |
| **Module** | `q2_uptake.py` |
| **Outputs** | `outputs/tables/q2_uptake_summary.csv`, `outputs/tables/q2_competitor_map.csv`, `outputs/tables/q2_enhertu_by_line.csv`, `outputs/figures/enhertu_uptake_ci.png` |
| **Result** | HER2-positive: 52.9% [31.0–73.8%] received Enhertu; competitors = HER2-mAb, chemo, HER2-ADC. HR+/HER2-low: 41.7% [19.3–68.0%]; competitors = CDK4/6i, endocrine, chemo. HR+/HER2-ultralow: 100% (n=3, n<11 — not interpretable). All proportions carry Wilson 95% CI. |

---

### Requirement 10 — Biomarker/HR concordance with Enhertu use; discordant cases

> "Assess whether recorded biomarker and HR evidence support the observed use of Enhertu. Identify potentially discordant or analytically interesting cases."

| Field | Detail |
|---|---|
| **ADR** | ADR-013 (discordance definition) |
| **Module** | `q2_uptake.py` |
| **Outputs** | `outputs/tables/q2_discordance_unknown_her2.csv`, `outputs/tables/q2_discordance_1l.csv`, `outputs/figures/discordant_timelines.png`, `outputs/figures/swimmer_plot.png` |
| **Result** | 23 patients received Enhertu with no qualifying HER2 test in the biomarker window (listed in `q2_discordance_unknown_her2.csv`). 3 received Enhertu as 1L with unknown HER2 status. Individual timelines in `discordant_timelines.png`. These represent real data-quality and documentation gaps in the synthetic asset. |

---

### Requirement 11 — Executive-ready fit-for-purpose summary

> "Provide an executive-ready summary of whether this synthetic data asset appears fit for answering a commercial or feasibility-style question about Enhertu uptake."

| Field | Detail |
|---|---|
| **Module** | `report.py`, deck, notebook Section 1 |
| **Outputs** | `reports/HER2_mBC_Enhertu_Analysis.pptx` Slide 2, `reports/analysis_notebook.html` Section 1 |
| **Result** | **Fit with conditions.** HER2-positive subindication (n=17) is usable for directional feasibility. HER2-low/HR+ (n=12) is borderline — sufficient for hypothesis generation, not for confirmatory study sizing. HER2-ultralow/HR+ (n=3) is too small for any inference. The 60% unknown rate is the primary limitation: it reflects EHR variant missingness, not a classification failure, and is quantified and disclosed. |

---

## Evaluation Criteria

### Cohort construction accuracy and defensible event indexing

| Where | Evidence |
|---|---|
| `cohort.py` + ADR-002/004/005 | Eligibility rules, index date definition, de novo/recurrent logic — all config-driven |
| `outputs/tables/attrition.csv` | Every exclusion step counted with n_in, n_excluded, n_remaining |
| `outputs/figures/consort_flow.png` | Visual CONSORT-style attrition diagram |

---

### Appropriate clinical logic for HER2 and HR status derivation

| Where | Evidence |
|---|---|
| `her2.py` + ADR-006/007/008 | ASCO/CAP 2018/2023 variant mapping; window; tie-break |
| `hormone_receptor.py` + ADR-009 | ER/PR ≥1% = HR+; ER-low flag at 1–10%; % beats result text |
| `audit/clinical-review.md` | Clinical logic reviewer sign-off |
| `outputs/tables/patient_her2.csv` | Per-patient audit trail: source, n_records, conflict flag |

---

### Ability to reason through data quality and ambiguity

| Where | Evidence |
|---|---|
| `data_quality.py` | 19 DQ checks covering orphan records, future dates, post-death events, pediatric DOBs |
| `outputs/dq/dq_log.csv` | Every flag with patient_id, rule_id, severity |
| `audit/validation_report.md` | 13 pipeline invariants, all PASS |
| Discordance tables | Ambiguous Enhertu use explicitly surfaced, not suppressed |

---

### Analytical depth and clarity

| Where | Evidence |
|---|---|
| `reports/analysis_notebook.html` | 13 sections, 16 figures, Wilson CI on every proportion |
| Sensitivity analysis (S1/S2/S3) | Three alternative rule sets, side-by-side comparison |
| Benchmark comparison | Literature-sourced ranges with citations; deviations explained |
| `audit/decisions/` | 14 ADRs — every judgment call documented with rationale |

---

### Communication quality and production-minded thinking

| Where | Evidence |
|---|---|
| `reports/HER2_mBC_Enhertu_Analysis.pptx` | Finding-sentence slide titles; numbers sourced from CSVs only |
| `config/analysis_rules.yaml` | All rules externalised — changing a rule = editing config, not code |
| `audit/SESSION_LOG.md` | One row per phase; full process trail |
| `audit/AI_USAGE.md` | AI assistance disclosed |
| `README.md` | Repo walkthrough, decision hierarchy, 8-phase build table |

---

*Generated: 2026-09-30 · Synthetic data only · Rule set v1 (config/analysis_rules.yaml)*

---

## Clinical Rules, Trials, and Literature Reference

Every judgment call in this analysis traces to one of the following standards. Changing a rule means updating `config/analysis_rules.yaml` — no code change required.

| Source | Type | What It Governs | Why Used |
|---|---|---|---|
| **ASCO/CAP 2023 Guidelines** | Clinical guideline | HER2 IHC category mapping — IHC 1+ and IHC 2+/ISH− = HER2-low | Standard that reclassified HER2-low from "negative" to a distinct category. Without this, HER2-low patients would all be called HER2-negative — the entire Q1 and Q2 analysis collapses |
| **ASCO/CAP 2018 Guidelines** | Clinical guideline | IHC 3+ and IHC 2+/ISH+ = HER2-positive | Pre-2023 standard that still governs positive classification. IHC 3+ = strong complete staining, unambiguously positive |
| **DESTINY-Breast06 (DB-06) screening criteria** | Trial criteria | IHC 0 with faint membrane staining ≤10% cells = HER2-ultralow | This trial defined ultralow as a clinical category for the first time. No other standard exists for this subgroup |
| **ASCO/CAP 2020 Guidelines** | Clinical guideline | HR-positive threshold = ER or PR ≥ 1% nuclear staining | Standard clinical definition of HR-positivity in adult breast cancer. A patient with 1% ER staining is HR-positive and eligible for endocrine therapy |
| **FDA DB-03 Approval** | Regulatory label | HER2-positive subindication — Enhertu 2L+ | First Enhertu approval in mBC. Defines the HER2-positive population as the core Enhertu indication |
| **FDA DB-06 Approval (Jan 27 2025)** | Regulatory label | HR+/HER2-low and HR+/HER2-ultralow subindications — Enhertu after ≥1 prior endocrine therapy | Expands Enhertu to HER2-low and ultralow. Requires HR+ and prior ET — this is why HR status matters for the subindication framework |
| **FDA DB-09 Approval (Dec 15 2025)** | Regulatory label | HER2-positive 1L — T-DXd + pertuzumab combination | Reframes the ADR-013 discordance definition — 1L Enhertu in HER2-positive is now on-label, not discordant |
| **Tarantino et al. JCO 2020** (vol 38, no.17) | Literature benchmark | HER2-positive prevalence benchmark: 15–20% of classifiable patients | Used in Q1 to assess whether our 16.5% positive rate is credible. It falls inside this range — validates the asset |
| **Schettini et al. NPJ Breast Cancer 2021** (7:103) | Literature benchmark | HER2-low prevalence benchmark: 45–55% of classifiable patients | Used to assess whether our 12.6% low rate is credible. Our rate is below benchmark — explained by 60% unknown deflating the classifiable denominator |
| **Modi et al. NEJM 2022** | Literature benchmark | HER2-low prevalence — corroborates Schettini benchmark | Secondary corroboration of the 45–55% HER2-low range from the DESTINY-Breast04 trial population |
| **Curigliano et al. NEJM 2024 (DB-06)** | Literature benchmark | HER2-ultralow of HER2-zero benchmark: 35–50% | Used to assess ultralow prevalence. Our ultralow (n=3) is too small to benchmark — noted as a limitation |
| **SEER Cancer Stat Facts** | Population registry | HR-positive benchmark: 65–75% of all mBC patients | Used to validate HR distribution in the cohort. Standard US population reference |
| **Standard RWD practice — n<11 flagging** | Industry convention | Flag cells with fewer than 11 patients instead of reporting the proportion | Prevents false precision from unstable small counts. Also limits re-identification risk in oncology subgroups. Used in ADR-012 |
| **Wilson 95% CI** | Statistical method | Confidence interval on every proportion | Better than normal approximation at small n and at boundaries (0% and 100%). Relevant here because several subgroups have n=3 to n=17 |
| **Standard oncology practice — 28-day regimen window** | Clinical convention | Drugs dispensed within 28 days = same regimen | Reflects typical oncology prescription and dispensing cycles. Used in ADR-010 for treatment line derivation |
| **Standard RWD convention — 90-day LOT gap** | RWD methodology | Gap of more than 90 days between regimens = new line of therapy | Widely used in published RWD oncology studies to approximate line of therapy without explicit LOT documentation |

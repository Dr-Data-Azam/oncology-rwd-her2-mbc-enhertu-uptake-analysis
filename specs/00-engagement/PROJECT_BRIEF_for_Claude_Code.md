# Project Brief: HER2 Metastatic Breast Cancer Feasibility & Enhertu Uptake (Synthetic Oncology RWD)

> ⛔ **HARD RULE: `../external/` (ConcertAI_Assesment/external) is STRICTLY READ-ONLY.**
> It is the original, unmodified attachment from Nexus Health Data. Never write, edit, rename, move, delete, unzip into, or create files inside it, and never run any command with it as the working directory that could write output there. Read from it only to verify inputs (e.g. hash checks). All work happens inside `her2-mbc-feasibility/`. Working copies of the data are in `data/raw/` (verified identical by SHA-256).


> **For Claude Code plan mode.** Read this whole brief, then produce an implementation plan before writing any code. Confirm open decisions (Section 10) with me before building.

---

## 1. Framing: how we are treating this work

- **Who I am in this exercise:** Associate Director, Solutions Consulting at Nexus Health Data. I lead feasibility and pre-sales analytics for pharma/biotech clients on oncology real-world data (RWD).
- **The client:** a pharma commercial / HEOR team focused on trastuzumab deruxtecan (Enhertu) in metastatic breast cancer (mBC).
- **The client's two questions:**
  1. *Feasibility:* Can this data asset support a HER2-defined mBC cohort? What is the HER2 distribution (positive / low / ultralow / 0-null / unknown) at metastatic diagnosis, and how confident are we?
  2. *Commercial:* How does Enhertu uptake compare with competitor therapies across HER2-defined mBC subindications? Is this asset fit for answering that question?
- **Tone of deliverable:** client-ready and executive-first. Lead with the answer, then the evidence, then the caveats. Show defensible clinical logic and data-quality reasoning; visuals should be clean and functional, not decorative.

**Actual context:** This is a portfolio project demonstrating oncology RWD analytical leadership for the Nexus Health Data **Associate Director, Solutions Consulting** role.

## 2. Timeline

| When | What |
|---|---|
| Tue Sep 29, 2026 | Materials received; start work |
| **Wed Sep 30 (evening, ET)** | **Submit deliverables** (ppt, html of ipynb output, etc — before the meeting) |
| **Thu Oct 1, 3:00–3:30 PM ET** | Review meeting on Teams (30-minute slot). The instructions say to be ready to present for 20–30 min, so plan roughly a 15-minute walkthrough and leave the rest for Q&A. |

## 3. Files

- Originals (READ-ONLY): `../external/candidate_facing_instructions.docx`, `../external/data_dictionary.xlsx`, `../external/synthetic_breast_her2_dataset_csv.zip`
- Working copies: `data/raw/{patient,diagnosis,staging,biomarker,medication}.csv` + `data/raw/data_dictionary.xlsx`
- `candidate_facing_instructions.docx`: the official task (summarized in Section 4)
- `data_dictionary.xlsx`: column definitions (summarized in Section 5)
- `synthetic_breast_her2_dataset_csv.zip` → `synthetic_breast_her2_dataset_csv/{patient,diagnosis,staging,biomarker,medication}.csv`

## 4. Official task (faithful summary of the instructions)

**Dataset context:** fully synthetic, multi-site provider network. It mixes structured EHR records (`curation_flag = 0`) with expert-curated records (`curation_flag = 1`). Some fields are deliberately incomplete or discordant. Clinical time windows matter because biomarker, diagnosis, stage and treatment dates do not align perfectly.

**Rules of engagement**
- SQL, Python or R are all allowed (DuckDB/SQLite are fine).
- State all assumptions. Document tie-break rules for multiple candidate records per patient and event.
- The work must be reproducible, with enough code and explanation for another analyst to rerun it.
- Priority order: analytical rigor, data-quality reasoning and defensible clinical logic come before cosmetic visuals.

**Submission requirements**
1. Source code
2. A concise slide deck or written summary (**at most 5 slides or 2 pages**)
3. **One appendix** section or slide covering data-quality checks and key assumptions
4. Supporting output tables or figures

**Presentation:** 20–30 min covering approach, assumptions, validation and conclusions. Expect follow-up questions on **tradeoffs, alternative definitions and how to productionize the analysis**.

### Question 1: Feasibility and HER2 distribution at metastatic diagnosis
1. Define a metastatic breast cancer (mBC) cohort from diagnosis and/or stage evidence, and **explain how the metastatic index date is defined**.
2. Determine HER2 status at metastatic diagnosis using biomarker records within a **clinically justified window** around the index date.
3. Resolve cases with multiple, discordant, ambiguous or incompletely detailed HER2 records.
4. Classify every patient as **HER2-positive, HER2-low, HER2-ultralow, HER2-0/null, or unknown/indeterminate**.
5. Report the overall distribution, then stratify it by **at least 3 factors**. Options: HR status, curation source, org type (academic/community), de novo vs recurrent metastatic disease, calendar year.
6. Compare the results against literature expectations. Are they directionally credible? Could deviations come from the synthetic design, missingness, capture bias or classification choices?
7. Quantify uncertainty: count the patients who could not be confidently classified, and run **at least one sensitivity analysis** (an alternate rule or an alternate window).

### Question 2: Enhertu uptake vs competitors by HER2-defined subindication
1. Build a subindication framework. At minimum include **HER2+ mBC, HR+/HER2-low mBC and HR+/HER2-ultralow mBC**. Additional exploratory groups are fine if justified (for example HR−/HER2-low, which approximates TNBC-low, or HER2-0/null as a control).
2. Derive treatment timing relative to the metastatic index date and identify the **first treatment after metastatic diagnosis**. Add sequencing logic (line-of-therapy approximation) if possible.
3. For each subindication, report the **% receiving Enhertu**, the **time from metastatic diagnosis to first Enhertu**, and the **most common competing therapies used instead of or before Enhertu**.
4. Check whether biomarker and HR evidence **support the observed Enhertu use**, and flag discordant or interesting cases (for example Enhertu given to a HER2-0/null patient, or an anti-HER2 regimen given to a HER2-low patient).
5. Close with an **executive summary**: is this asset fit for a commercial or feasibility question about Enhertu uptake by HER2 subindication?

**Evaluation criteria:** cohort construction and event indexing · HER2/HR clinical logic · reasoning about data quality and ambiguity · analytical depth and clarity · communication and production-minded thinking.

## 5. Data dictionary

| Table | Column | Type | Notes |
|---|---|---|---|
| patient | patient_id | string | PAT_001… |
| patient | date_of_birth | date | *includes intentionally implausible edge cases* |
| patient | date_of_death | date | null if alive/unknown; *includes one impossible row* |
| patient | org_id / org_type | string | ORG_001–010 / community, academic |
| diagnosis | patient_id, diagnosis_date | | |
| diagnosis | diagnosis_code | ICD-10 | breast-dominant, plus non-breast noise and comorbidities |
| diagnosis | diagnosis_type | | primary / metastatic |
| diagnosis | curation_flag | int | 0 = EHR, 1 = curated |
| staging | stage_date, stage_group | | stage_group may be blank; *derivable from TNM* |
| staging | t_stage, n_stage, m_stage | | T1–4, N0–3, M0/M1 |
| staging | curation_flag | int | |
| biomarker | report_date, biomarker_name | | HER2 / ER / PR / Ki-67 |
| biomarker | biomarker_test_type | | IHC / protein expression |
| biomarker | biomarker_result | | Positive / Negative / Unknown |
| biomarker | biomarker_variant | | granular detail; *curated records more likely to have it populated* |
| biomarker | curation_flag | int | |
| medication | med_date, med_brand_name, med_generic_name | | |
| medication | med_status | | active / completed / discontinued |
| medication | curation_flag | int | |

## 6. Initial data profile (quick scan; the build should re-verify these numbers)

**Row counts:** patient 150 · diagnosis 333 (150 pts) · staging 200 (130 pts) · biomarker 1,059 (138 pts) · medication 341 (104 pts).

**patient:** 83 community / 67 academic; 27 deaths recorded.

**diagnosis:** 227 primary / 106 metastatic rows. Codes: C50.x (breast) is dominant. Non-breast cancers: C34.9 lung, C61 prostate, C18.9 colon. Comorbidities: I73.9, E11.9, J44.1, N18.3, I50.9. **106 patients have a "metastatic" diagnosis row**, but two of those rows carry non-breast codes (C34.9, C61). **22 patients have no C50 code at all.** There are no secondary-malignancy codes (C77–C79), so metastatic evidence comes only from `diagnosis_type` and staging.

**staging:** stage_group IV = 113, III = 22, II = 18, I = 7, **blank = 40** (21 with M0, 19 with M1, so stage can be derived from M). There are no IV/M0 conflicts. 108 patients have M1 or stage IV.

**biomarker:** HER2 289 · ER 256 · PR 259 · Ki-67 255 rows. HER2 records per patient: 1 record (43 patients), 2 (40), 3 (54), 4 (1).

HER2 `result × variant` patterns, which drive the classifier:

| result | variant | n |
|---|---|---|
| Negative | IHC 1+ | 58 |
| Positive | IHC 3+ | 43 |
| Negative | *(blank)* | 39 |
| Negative | IHC 0 | 27 |
| Positive | IHC 2+; ISH amplified | 21 |
| Positive | *(blank)* | 20 |
| Negative | IHC 2+; ISH negative | 22 |
| Negative | IHC 0 absent membrane staining | 15 |
| Negative | IHC 0 with faint membrane staining in <=10% cells | 14 |
| Negative | IHC 0 with membrane staining | 9 |
| Unknown | IHC equivocal / blank / Pending | 13 |
| **Conflicts:** Positive + IHC 0 (2), Positive + IHC 1+ (2), Positive + IHC 2+;ISH neg (1), Unknown + IHC 3+ (2), Unknown + IHC 0 (1) | | |

- Test type is "IHC" or "protein expression" (the latter is probably an EHR synonym for IHC).
- **ER/PR:** variants are "% positive cells" (1–95%) or blank. **Result/variant conflicts are common**, e.g. ER "Negative" with 37–93% positive cells, and "Unknown" with a stated %. Low-positive values (1–10%, the ASCO/CAP "ER-low" range) are present.

**Deliberate data-quality traps found so far:**
- **Orphan patients** PAT_998 and PAT_999 appear in staging and biomarker but not in patient.
- **24 pediatric DOBs** (PAT_127–150, born 2009–2020) and 7 patients born before 1935 (up to about 99 years old).
- **PAT_001 has a death date before its birth date.**
- **Events recorded after the death date:** diagnosis 26 · staging 19 · biomarker 113 · medication 51 rows. (Re-check this; it may be concentrated in a few patients or in PAT_001.)
- **Future-dated records** (after today, 2026-09-29): biomarker 15, medication 5 (medication dates run to 2027-08), diagnosis 1, staging 1. There are also 2 biomarker rows dated before 2000 (one from 1955).
- 1 exact duplicate biomarker row.
- Medication has **no end date, dose or line of therapy**, only an event date and a status.
- Medication patients only go up to PAT_128, so the pediatric block mostly has no treatment data.

**Therapies present (generic, rows):** paclitaxel 44 · **trastuzumab deruxtecan 43** · capecitabine 35 · pertuzumab 32 · trastuzumab 32 · palbociclib 28 · anastrozole 23 · letrozole 20 · sacituzumab govitecan 18 · abemaciclib 17 · fulvestrant 11 · nab-paclitaxel 11 · tucatinib 10 · ribociclib 10 · T-DM1 7.

## 7. Clinical reference logic (verify and cite in the deck)

**HER2 categories** (ASCO/CAP 2018/2023 plus DESTINY-Breast04/06 definitions):

| Category | Rule |
|---|---|
| HER2-positive | IHC 3+, **or** IHC 2+ with ISH amplified |
| HER2-low | IHC 1+, **or** IHC 2+ with ISH not amplified |
| HER2-ultralow | IHC 0 with faint/barely perceptible, incomplete membrane staining in **>0 and ≤10%** of cells |
| HER2-0 / null | IHC 0 with **absent** membrane staining |
| HER2-0, not otherwise specified | IHC 0 with no staining detail. This cannot be split into ultralow vs null, so flag it and handle it in the sensitivity analysis. |
| Unknown / indeterminate | equivocal without ISH, pending, blank variant with Unknown result, conflicting records that cannot be resolved |

- "IHC 0 with membrane staining" (no % given) is ambiguous. Treat it as probable ultralow and test the alternative in sensitivity analysis.
- A result of Positive/Negative with a blank variant supports only a binary HER2+ vs HER2−. **HER2− with a blank variant cannot be placed as low, ultralow or null.** This is a key feasibility finding.
- When result and variant conflict, the variant (the granular IHC score) should usually win, preferring curated records. State this as a rule.

**HR status:** ER or PR ≥1% means HR+. ER 1–10% is "ER-low" (flag it). When the % and the result conflict, decide which one wins and document the choice.

**Metastatic index date (candidate rule):** the earliest of (a) a metastatic diagnosis row with a breast C50 code, and (b) a staging record with M1 or stage IV (including stage derived from M). Plan mode should consider whether curated records get priority and whether the two sources must agree within N days.

**De novo vs recurrent:** de novo means stage IV / M1 at or near the initial breast diagnosis (for example within 90 days of the first primary C50). Recurrent means a primary diagnosis more than 90 days before the metastatic index date.

**Biomarker window (candidate):** −365 to +90 days around the index date, choosing the record closest to the index date. Tie-breaks: curated > EHR, granular variant > blank, then most recent. Sensitivity options: ±30/60 days, "ever" (any time before the first metastatic treatment), "curated only", "highest HER2 ever".

**Enhertu label context (to confirm the current status before stating it):**
- HER2+ mBC after a prior anti-HER2 regimen (DESTINY-Breast03, 2L). Possible 1L use with pertuzumab (DESTINY-Breast09); check approval status.
- HER2-low mBC after prior chemo in the metastatic setting (DB-04, 2022).
- HR+ HER2-low or HER2-ultralow mBC after ≥1 endocrine therapy, chemo-naive in the metastatic setting (DB-06, FDA January 2025).

**Competitor map by subindication:**
- **HER2+:** trastuzumab + pertuzumab + taxane (1L standard); T-DM1 (Kadcyla); tucatinib + trastuzumab + capecitabine.
- **HR+/HER2-low and HR+/HER2-ultralow:** CDK4/6 inhibitors (palbociclib, ribociclib, abemaciclib) + an aromatase inhibitor or fulvestrant (1L); chemo (capecitabine, paclitaxel, nab-paclitaxel); sacituzumab govitecan (HR+/HER2− after endocrine therapy plus ≥2 chemo lines).
- **Discordance examples to look for:** Enhertu in HER2-0/null or unknown; trastuzumab/pertuzumab/T-DM1/tucatinib in HER2-negative patients; CDK4/6 inhibitors in HR− patients; Enhertu before any endocrine therapy in HR+ HER2-low (possible off-sequence use).

**Literature benchmarks (approximate; verify and cite):** HER2+ about 15–20% of breast cancer; HER2-low about 45–55%; HER2-0 about 25–35%, of which ultralow is roughly 20–30% of HR+ HER2-0 (per DB-06 screening). HR+ is about 65–75% of mBC. Expect this synthetic set to deviate. Explain the deviation through its design, the number of blank variants, and curation mix.

## 8. Expected deliverables (what I will deliver to the client)

1. **Reproducible code**: Python + DuckDB (SQL for cohort logic, pandas for the rest) in a Jupyter notebook plus a small modular package or SQL files. It should run end to end from the zip, with fixed seeds and no manual steps.
2. **Rendered notebook as HTML** (the reviewer explicitly mentioned "html of ipynb output").
3. **Slide deck, at most 5 slides plus 1 appendix** (.pptx):
   1. Executive summary: answer, fit-for-purpose verdict, top 3 caveats
   2. Cohort attrition (a CONSORT-style flow) and the index-date definition
   3. Q1 HER2 distribution: overall plus 3 stratifications, a literature comparison, and the unclassifiable count
   4. Q2 Enhertu uptake by subindication: % treated, time to Enhertu, competitors before or instead of it, discordant cases
   5. Sensitivity analysis results, recommendations, and next steps to productionize
   - Appendix: data-quality checks table, assumptions and tie-break rules
4. **Output tables** (CSV): cohort, per-patient HER2/HR derivation with an audit trail (which record won and why), subindication × therapy tables, DQ issue log.
5. A **short README** explaining how to rerun.

## 9. Things the reviewer will probably probe (build answers into the work)

- Why this index date and not another? What changes if only curated records are used?
- Why this biomarker window? Why prefer the closest record over the most recent one or the highest HER2?
- How do you split IHC 0 when there is no staining detail? What share of HER2-0 is unresolvable?
- EHR vs curated concordance: how often do they disagree, and which wins?
- How would you productionize this: a versioned rules engine, dbt/SQL models, unit tests per rule, DQ monitors, and an evidence-level score per patient?
- Commercial framing: is n small enough that the percentages are fragile? Report counts with confidence intervals (Wilson), and suppress or flag cells with n < 11 as good RWD practice.
- Line-of-therapy approximation with no end dates: how did you define a regimen window (e.g. drugs started within 28 days count as one line)?

## 10. Open decisions for plan mode to raise with me

1. Should patients with pediatric or implausible DOBs, orphans, or death-before-birth be excluded, or kept with a flag? (Suggestion: exclude from the analytic cohort but show them in the attrition diagram.)
2. How should records dated after death or in the future be handled? (Suggestion: drop them from analysis and log them in the DQ table.)
3. Does the index date require breast-specific evidence? (Suggestion: yes. Only count metastatic evidence for patients with a C50 code; a stage IV record counts only if the patient has breast cancer.)
4. What are the primary window and the sensitivity windows?
5. How should "IHC 0 with membrane staining" and "IHC 0" with no detail be classified?
6. When ER/PR result and % disagree, which wins? (Suggestion: the % value, per ASCO/CAP.)
7. What format should the deck be: .pptx (my default), or should I also export a PDF?

## 11. Constraints

- Keep the deck to 5 slides plus the appendix. The rendered notebook carries the depth.
- **`../external/` is strictly read-only**: no writes, edits, moves, deletes or unzipping into it. `data/raw/` is also treated as read-only. All outputs go to `outputs/`.
- Write no dashes in any email text (style preference).

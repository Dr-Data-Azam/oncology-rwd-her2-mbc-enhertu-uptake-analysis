# Nexus Health Data Feasibility Study: Understanding the Data, and How to Approach It

> ⛔ **HARD RULE: `../external/` (ConcertAI_Assesment/external) is STRICTLY READ-ONLY.**
> It is the original, unmodified attachment from Nexus Health Data. Never write, edit, rename, move, delete, unzip into, or create files inside it, and never run any command with it as the working directory that could write output there. Read from it only to verify inputs (e.g. hash checks). All work happens inside `her2-mbc-feasibility/`. Working copies of the data are in `data/raw/` (verified identical by SHA-256).


Working copies of the data are in `data/raw/`; the original attachment is in `../external/` (read-only). Every number below comes from the actual files.

---

# PART A: UNDERSTANDING THE DATA

## A1. The big picture in one paragraph

We have **150 synthetic patients** from **10 provider organizations** (community and academic). For each patient there are up to four kinds of clinical events, all in "long" format, meaning one row per event rather than one row per patient: **diagnoses, staging assessments, biomarker lab results and medication events**. Every clinical row carries a `curation_flag`:

- **0** means it was pulled automatically from the EHR. These records are messy and less detailed.
- **1** means a human abstractor reviewed the chart. These records are cleaner and more detailed.

This is how Nexus Health Data and similar RWD vendors deliver data. The whole task comes down to collapsing many event rows into **one analytic row per patient**, anchored on one date: the day the patient became metastatic.

## A2. The data model

```
patient (1 row per patient)  ← the spine
   │  patient_id
   ├── diagnosis  (1–4 rows/pt)   "what cancer, and when did it become metastatic?"
   ├── staging    (1–2 rows/pt)   "TNM / stage IV evidence, with dates"
   ├── biomarker  (1–11 rows/pt)  "HER2, ER, PR, Ki-67 test results over time"
   └── medication (1–7 rows/pt)   "what drug, on what date"
```

There are no encounter IDs, no line-of-therapy fields and no end dates. All linkage is through **patient_id + dates**, so timing logic does all the work.

| Table | Rows | Patients | Grain (one row =) | Curated share |
|---|---|---|---|---|
| patient | 150 | 150 | one patient | n/a |
| diagnosis | 333 | 150 | one diagnosis event | 40% |
| staging | 200 | 130 (+2 orphans) | one staging assessment | 46% |
| biomarker | 1,059 | 138 (+2 orphans) | one test result | 55% |
| medication | 341 | 104 | one drug event on a date | 43% |

## A3. Table by table

### patient
- `date_of_birth`: **24 patients (PAT_127–150) were born between 2009 and 2020**, so they would be children with breast cancer. These are planted bad records. Most of them carry non-breast codes (lung, colon, prostate, comorbidities), and 3 of them carry C50 codes.
- `date_of_death`: 27 patients have one. **PAT_001 died before she was born** (the "impossible row" the dictionary warns about). About 15 patients have biomarker, diagnosis or medication events recorded after their death date.
- `org_type`: 83 community, 67 academic. This is a ready-made stratification variable.

### diagnosis
- `diagnosis_code`: ICD-10. **C50.x = breast cancer** (C50.1 central, .2 upper-inner, .4 upper-outer, .5 lower-outer, .8 overlapping, .9 unspecified). There is also noise: C34.9 lung, C61 prostate, C18.9 colon. Comorbidities also appear: I73.9 PVD, E11.9 diabetes, J44.1 COPD, N18.3 CKD, I50.9 heart failure.
- `diagnosis_type`: primary vs metastatic.
- Key facts:
  - **128 patients have a breast code and 22 do not**, so those 22 drop out immediately.
  - **104 breast patients have exactly one "metastatic" row with a C50 code.** This is the cleanest anchor for the index date.
  - Two metastatic rows carry non-breast codes (PAT_134 lung, PAT_136 prostate). These are traps and should not count.
  - Among the 104, **70 also have an earlier primary breast diagnosis**, between 123 and 897 days earlier, which makes them **recurrent**. **34 have no primary row**, which makes them **possibly de novo** stage IV (or their primary record is simply missing; say so).

### staging
- stage_group I, II, III or IV, or **blank (40 rows)**. Every blank can be derived from `m_stage`: M1 means IV. Nothing conflicts: every IV row has M1, and every I–III row has M0.
- **106 breast patients have M1 or stage IV evidence.** 104 of them overlap with the metastatic diagnosis group, and **2 more (PAT_004, PAT_090) have stage IV but no metastatic diagnosis row**. These 2 are a definition choice to discuss.
- PAT_998 and PAT_999 exist only in staging and biomarker, not in patient. They are **orphans**; exclude them.
- Timing: the first M1 stage date is usually **about 6 days before** the metastatic diagnosis date (median). Occasionally it is years before. PAT_001, for example, has an M1 staging row at her *primary* diagnosis in 2023, which conflicts with a clean recurrence story.

### biomarker (the most important and messiest table)
- 4 markers: HER2 289 rows, ER 256, PR 259, Ki-67 255. The median patient has about 8 biomarker rows.
- `biomarker_result` is the coarse field (Positive / Negative / Unknown). `biomarker_variant` is the detailed field, and it is the one that matters.
- **HER2 variants and what each one maps to:**

| variant text | Clinical meaning | HER2 category |
|---|---|---|
| IHC 3+ | strong complete staining | **Positive** |
| IHC 2+; ISH amplified | equivocal IHC, confirmed by gene test | **Positive** |
| IHC 2+; ISH negative | equivocal IHC, not amplified | **Low** |
| IHC 1+ | faint partial staining | **Low** |
| IHC 0 with faint membrane staining in <=10% cells | barely-there staining | **Ultralow** |
| IHC 0 with membrane staining | some staining, % not stated | probably ultralow (ambiguous) |
| IHC 0 absent membrane staining | nothing at all | **0 / null** |
| IHC 0 | no detail | **HER2-0, unspecified** (can't split ultralow vs null) |
| IHC equivocal / Pending / blank + Unknown | incomplete | **Unknown** |
| *blank* + Negative | only "HER2 negative" | **HER2-negative, subtype unknown** |

- **Key insight: EHR HER2 rows leave the variant blank 46% of the time, while curated rows leave it blank only 1% of the time.** Without curation you can say "HER2-negative" but you can't say low vs ultralow vs null. That is exactly the feasibility story Nexus Health Data sells: curated data enables HER2-low and ultralow analyses.
- Conflicts are planted: Positive + IHC 0 (2 rows), Positive + IHC 1+ (2), Unknown + IHC 3+ (2), Positive + IHC 2+/ISH negative (1). Your rule is "the detailed variant beats the coarse result, and curated beats EHR". State it.
- Patients have 1 HER2 record (43 patients), 2 (40), 3 (54) or 4 (1). Only 4 patients have a true Positive-vs-Negative flip across records, but many have mixed levels, e.g. PAT_001 has 2+/ISH negative, then blank, then 1+ (all of which are HER2-low).
- **Timing is critical.** Relative to the metastatic diagnosis date, **most HER2 tests happen after it**: 31 rows before, 81 in days 0–90, 73 in days 91–180, 37 after 180 days. A standard window of −365 to +90 days finds HER2 for only **71 of 104** patients. Widening to +180 days finds **95 of 104**. This is your sensitivity analysis waiting to happen.
- **ER / PR:** variants are "NN% positive cells". **Result and percentage often disagree.** PAT_010 has PR "Negative" with 30% positive cells, and ER "Negative" with 26%. Under ASCO/CAP, ≥1% counts as positive, so the percentage should win. **HR+ = ER+ or PR+.** Flag ER 1–10% as "ER-low".
- **Ki-67:** a proliferation marker, not needed for the questions. Mention it only as available.
- There are bad dates: 1 row from 1955, 15 rows dated after today (up to 2027), 1 exact duplicate row.

### medication
- 15 drugs, 104 patients, 1 to 7 rows each. No end date and no dose; `med_status` is active, completed or discontinued.
- **The same drug given on the same day as another = a regimen.** 95 patient-dates have 2 or 3 drugs, e.g. Verzenio + Arimidex, or Herceptin + Perjeta + Taxol.
- Every medication patient has a metastatic diagnosis, and meds typically start **about 60 days after** the index date (median). Only 1 row falls before it.
- **Enhertu:** 42 patients (43 rows), typically **about 183 days after** metastatic diagnosis. So it is mostly *not* first-line, which fits the approved labels (2nd line and beyond).

| Class | Drugs in data | Typical use in metastatic breast cancer |
|---|---|---|
| HER2-targeted | Herceptin (trastuzumab), Perjeta (pertuzumab), Kadcyla (T-DM1), Tukysa (tucatinib) | HER2+ only |
| **ADCs** | **Enhertu (T-DXd)**, Trodelvy (sacituzumab govitecan) | Enhertu: HER2+, low, ultralow. Trodelvy: TNBC and HR+/HER2− (later line) |
| CDK4/6 inhibitors | Ibrance, Kisqali, Verzenio | HR+/HER2− first line, given with endocrine therapy |
| Endocrine | Arimidex, Femara, Faslodex | HR+ only |
| Chemo | Taxol, Abraxane, Xeloda | Any subtype |

## A4. One patient end to end (PAT_001), to make it concrete

- 2023-03-13: staging T3 N1 **M1**, stage blank, EHR. ← an M1 flag at primary diagnosis? (conflict)
- 2023-03-21: primary breast cancer C50.8 (curated)
- 2024-10-18/19: ER 52%, PR 81%, so **HR+**
- 2024-11-04: stage IV M1 (EHR)
- **2024-11-18: metastatic diagnosis C50.8 (curated) ← index date candidate**
- 2025-01-24: Verzenio + Arimidex ← **1st line: CDK4/6 inhibitor + aromatase inhibitor (textbook HR+ first line)**
- 2025-02-16: HER2 IHC 2+ ISH negative (EHR) → low
- 2025-04-13: HER2 Negative, blank (EHR)
- 2025-04-16: HER2 **IHC 1+** (curated) → low
- 2025-04-27: **Enhertu** ← 2nd line, about 5 months after metastatic diagnosis; **HR+/HER2-low, consistent with DESTINY-Breast04/06 use**
- …but the patient table says she died in 1979, before her 1980 birth. **Data quality flag.**

This one patient contains most of the lessons in the test: index date choice, a post-index HER2 window, EHR vs curated records, regimen grouping, a label-consistent sequence, and an impossible date.

## A5. Traps checklist (these become the appendix DQ slide)

1. 22 patients with no breast cancer code
2. 2 metastatic rows with non-breast codes (lung, prostate)
3. 24 pediatric-DOB patients plus 7 born before 1935 (ages up to about 99)
4. PAT_001 has a death date before her birth date
5. Events after death (about 15 patients)
6. Future-dated rows (biomarker 15, medication 5, diagnosis and staging 1 each), plus 2 very old biomarker rows (1955)
7. Orphan IDs PAT_998 and PAT_999
8. 40 blank stage groups (derivable from M)
9. HER2 result vs variant conflicts; ER/PR result vs % conflicts
10. EHR HER2 with blank variant (46%), so HER2-low can't be determined
11. "IHC 0" with no staining detail, so ultralow vs null can't be determined
12. HER2 mostly tested after the metastatic date, so the window drives the results
13. 2 patients with stage IV but no metastatic diagnosis row
14. 1 duplicate biomarker row
15. No line-of-therapy or end dates in medication

---

# PART B: HOW AN IDEAL DATA SCIENTIST APPROACHES THIS TEST

The reviewer is scoring **judgment**, not code volume. A strong candidate thinks like this: *"Every number I show, I can defend, I know how fragile it is, and I know what I'd do in production."*

## Step 0: Read like a consultant (30 min) ✅ you're here
- Restate the client question in one sentence per question.
- Write down what "done" looks like: 5 slides + appendix + code + HTML notebook, sent Wednesday.
- Note the evaluation criteria. That list is the rubric. Map each criterion to a slide.

## Step 1: Profile before you analyze (1–2 hrs) ✅ mostly done above
- Row counts, grain, keys, blanks, value distributions per table.
- Check referential integrity (orphans), date sanity (birth, death, future), duplicates.
- **Write every issue to a DQ log table as you find it:** issue, table, rows affected, decision. This log becomes your appendix almost for free.

## Step 2: Write the rules before the code (1 hr), the most important step
Make a small **assumptions and decisions table**. For each decision, record the primary rule, the alternative (which becomes a sensitivity analysis), and why you chose it. Decisions to make:
1. **Eligibility:** breast C50 code required; plausible age (18 or older at metastatic diagnosis); valid birth and death dates; exists in the patient table.
2. **Metastatic index date:** e.g. the earliest of (a) a C50 metastatic diagnosis and (b) an M1/IV staging record, with the M1 date counting only if it falls within ±30 days of a C50 metastatic diagnosis, or on its own for the 2 stage-only patients. Stage IV at the primary diagnosis is treated as de novo.
3. **De novo vs recurrent:** de novo if there is no primary more than 90 days before the index date, or stage IV at the initial diagnosis.
4. **HER2 window:** primary **−365 to +180 days**; sensitivity −90/+90, −365/+90 and "any before first metastatic treatment". Justify the post-index allowance: metastatic biopsies are often reported weeks to months after diagnosis, and in this data most tests fall after the index date.
5. **HER2 tie-break hierarchy** (write it as ordered rules):
   1. Drop invalid or "Pending" results.
   2. The detailed variant beats the coarse result.
   3. Curated beats EHR.
   4. The record closest to the index date wins.
   5. If records still conflict: take the **highest** category (for treatment eligibility, the clinical convention is that any HER2+ result counts) in a sensitivity run, and the **most recent** in the primary run. Or state the reverse; the key is to **pick one and test the other**.
6. **HR status:** the % value beats the result text; ≥1% = positive; HR+ = ER+ or PR+; flag ER-low.
7. **Treatment lines:** drugs starting within 28 days of each other = one regimen. Line 1 = the first regimen on or after the index date. A new line starts when a new drug class appears more than 28 days later.
8. **Exclusions:** future dates, dates after death, pre-birth dates.

## Step 3: Build the pipeline in layers (3–4 hrs)
Use Python + DuckDB (install it with `pip install duckdb`) or plain pandas, and structure it like production code:
```
01_load_and_dq.py      → raw tables + dq_log.csv
02_cohort.py           → attrition table (CONSORT) + index date per patient
03_biomarkers.py       → patient-level HER2 + HR with an audit column ("which row won and why")
04_q1_distribution.py  → overall + stratified tables + sensitivity
05_treatment.py        → regimens, lines, first treatment, Enhertu timing
06_q2_uptake.py        → subindication × drug tables + discordance list
notebook.ipynb         → calls the above, narrates, exports to HTML
```
- Each layer outputs one tidy table. **Keep an audit trail**: for every patient, record why they were included or excluded and which biomarker record won. Reviewers love this because it's what production RWD pipelines do.
- Add a handful of asserts as "unit tests": one row per patient, no index date before birth, every HER2 category in the allowed set.

## Step 4: Answer Q1 (2 hrs)
- **Attrition diagram:** 150 → 128 breast → valid demographics → metastatic evidence → **final cohort** (roughly 80–100).
- HER2 distribution: counts, %, and **Wilson 95% confidence intervals**. With n ≈ 90 the intervals are wide, so say so.
- Stratify by **HR status, curation source, org type, de novo vs recurrent** (4 factors, more than the required 3).
- **Unclassifiable count:** unknown + "HER2-negative subtype unknown" + "HER2-0 not otherwise specified". Present this as the feasibility headline.
- **Literature comparison:** HER2+ about 15–20%, HER2-low about 45–55%, ultralow a meaningful slice of the former HER2-0 group. Explain gaps through synthetic enrichment (the data is clearly enriched for Enhertu-relevant patients), EHR missingness and window choice.
- **Sensitivity table:** the same distribution under 3–4 alternative rules, side by side. Show which categories are stable and which move.

## Step 5: Answer Q2 (2–3 hrs)
- **Subindications:**
  - HER2+
  - HR+/HER2-low
  - HR+/HER2-ultralow
  - Exploratory: HR−/HER2-low ("TNBC-low"), HER2-0/null (a negative control where Enhertu should be about 0% except off-label use), and Unknown.
- Per subindication:
  - n
  - % who ever received Enhertu (with CI)
  - median days from metastatic diagnosis to first Enhertu
  - line of therapy at which Enhertu starts
  - top first-line regimens
  - top regimens given **before** Enhertu, and **instead of** it (among patients who never got it)
- **Discordance list:**
  - Enhertu in HER2-0/null or unknown patients
  - HER2-targeted drugs in HER2-negative patients
  - CDK4/6 inhibitors or endocrine therapy in HR− patients
  - Enhertu given before any endocrine therapy in HR+ patients
  - Enhertu given before the HER2 test date. This is a nice subtle one: **was treatment chosen before the biomarker was documented?**
- Keep the **commercial lens**: e.g. "Enhertu reaches X% of HER2+ but only Y% of HR+/HER2-low patients. Ultralow uptake can't be measured reliably because only Z patients are classifiable."

## Step 6: Fit-for-purpose verdict (30 min)
Answer like an AD would, in three buckets:
- **Fit for:** HER2+ vs HER2− and HR status in curated records, and treatment timing.
- **Fit with caveats:** HER2-low, where it depends on curation and the window.
- **Not fit for:** HER2-ultralow without curated IHC detail; small cells; lines of therapy without end dates.

Then give **recommendations**: curate the EHR HER2 records, abstract IHC staining detail, add line-of-therapy fields, and increase sample size.

## Step 7: Deck (2 hrs)
Five slides:
1. **Executive summary**: the answer first.
2. **Cohort and method**: attrition, index date, HER2 rules.
3. **Q1 results**: distribution, strata, literature comparison, uncertainty.
4. **Q2 results**: uptake by subindication, time to Enhertu, competitors, discordance.
5. **Fit for purpose and productionization**: rules engine, dbt/SQL models, tests, DQ monitoring, versioned definitions.

Plus the **appendix**: DQ log and assumptions table.

- Each slide title should be a **sentence that states the finding**, not a topic label.

## Step 8: Rehearse the defense (1 hr)
Prepare a 30-second answer for each of these:
- Why this index date? What if you used only curated records?
- Why +180 days post-index? Isn't that a treatment-influenced window? *(Answer: yes, it's a risk. The −365/+90 sensitivity analysis shows the effect.)*
- How did you split IHC 0?
- How would you scale this to 100k patients? *(SQL models, a rules config, unit tests, DQ dashboards, abstraction QA sampling.)*
- What would you tell the client tomorrow?

## Suggested schedule
| When | Do |
|---|---|
| Tue night | Steps 1–2 (profiling done; write the rules table) |
| Wed day | Steps 3–6 (build + results) |
| Wed evening | Step 7 deck + HTML export → **submit deliverables** |
| Thu morning | Step 8 rehearsal |
| Thu 3:00 PM ET | Present |

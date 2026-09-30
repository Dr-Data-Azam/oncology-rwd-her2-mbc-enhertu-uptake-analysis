# her2-mbc-feasibility

Analysis of HER2 distribution and Enhertu uptake in a synthetic metastatic breast cancer
cohort (150 patients, 10 provider organizations). Answers two client questions:

1. **Feasibility:** What is the HER2 distribution (positive / low / ultralow / 0-null /
   unknown) at metastatic diagnosis, and how confident can we be?
2. **Commercial:** How does Enhertu uptake compare with competitor therapies across
   HER2-defined mBC subindications? Is this data asset fit for purpose?

Built as a ConcertAI technical assessment (Associate Director, Solutions Consulting).
**All data are synthetic and for assessment purposes only.**

---

## Quickstart

```bash
uv sync                                          # install all dependencies (Python 3.12+)
uv run pytest tests/ -v                          # verify 134 tests pass
uv run python -m her2rwd.pipeline --reports      # run all 12 stages → outputs/ + reports/
```

Open `reports/analysis_notebook.html` in a browser, or open
`reports/HER2_mBC_Enhertu_Assessment.pptx` for the slide deck.

---

## Part 1 — From Brief to Build: What Existed, What Was Planned, What Was Executed

### 1a. Before Plan Mode — What We Started With

The starting point was a blank folder and the original ConcertAI email attachment:

```
external/                                ← READ-ONLY original files as received
├── candidate_facing_instructions.docx   ← the official assessment brief
├── data_dictionary.xlsx                 ← column definitions for all 5 tables
└── synthetic_breast_her2_dataset_csv.zip ← 150-patient synthetic oncology dataset
```

No code existed. No repo. No notebook. The only inputs were the brief, the data
dictionary, and five CSV files (patient, diagnosis, staging, biomarker, medication).

**Key data facts discovered during initial scan:**
- 150 patients, 10 provider organizations (83 community, 67 academic)
- 106 patients have a metastatic signal (C50 dx or M1/IV staging); 44 have none
- 289 HER2 biomarker rows for 138 patients — many patients have 2-4 records with
  conflicting variants, requiring a tie-break rule
- 24 pediatric DOBs, 1 death-before-birth, events logged after death, future-dated
  records — deliberate data-quality traps built into the synthetic dataset
- No treatment line or end-date fields — line-of-therapy must be approximated from
  event dates alone

**The two client questions (from the brief):**
- Q1: Define an mBC cohort, classify HER2 status with a clinically justified window,
  resolve conflicts, stratify by ≥3 factors, benchmark against literature, run
  sensitivity analyses
- Q2: Build a subindication framework, derive treatment timing, report Enhertu uptake
  and time-to-first-Enhertu per subindication, identify competitors and discordant cases

---

### 1b. What Was Planned — The Engagement Spec (Plan Mode)

Before any code was written, a full engagement spec was produced in plan mode and
approved by Azam. The plan established:

**Deliverables committed:**

| ID | Deliverable | Format | Recipient |
|----|-------------|--------|-----------|
| D1 | Reproducible source code | zipped repo | Brandon |
| D2 | Rendered analysis notebook | HTML | Brandon |
| D3 | Slide deck (5 slides + Appendix A/B/C) | .pptx | Brandon |
| D4 | Output tables and figures | CSV / PNG | Brandon (inside zip) |
| D5 | Audit pack | Markdown + CSV | Brandon (inside zip) |
| D6 | README + repo docs | Markdown | Brandon (inside zip) |
| D7 | Cover email (no dashes) | text | Brandon |
| D8 | Talk track + Q&A prep | Markdown | Internal only (_prep/) |

**Build phases planned:**

| Phase | Slug | Purpose | ADRs | Approx. effort |
|-------|------|---------|------|----------------|
| P00 | engagement | Repo scaffold, brief, data guide, this plan | — | setup |
| P01 | ingest-and-dq | Load CSVs into DuckDB, SHA-256 hashes, 15+ DQ checks | 001, 003 | 1.5 h |
| P02 | cohort-index-date | Eligibility, metastatic index date, de novo/recurrent | 002, 004, 005 | 2 h |
| P03 | biomarker-derivation | HER2 + HR classification with full audit trail | 006, 007, 008, 009 | 2.5 h |
| P04 | q1-her2-distribution | HER2 distribution, strata, benchmarks, statistics | 012, 014 | 2 h |
| P05 | treatment-lines | Regimen grouping, line-of-therapy approximation | 010 | 1.5 h |
| P06 | q2-enhertu-uptake | Subindications, uptake, time-to-Enhertu, discordance | 011, 013 | 2.5 h |
| P07 | deliverables | Validation, sensitivity, HTML, PPTX, zip, cover email | — | 2.5 h |

**Governance designed in the plan:**
- Every rule parameter lives in `config/analysis_rules.yaml` (never hard-coded)
- Every decision produces an ADR (Architectural Decision Record) before code is written
- Azam approves both the analysis spec and the tech spec per phase before any build starts
- `../external/` and `data/raw/` are permanently read-only; all outputs go to `outputs/`
- Every pipeline run produces `outputs/run_manifest.json` with input SHA-256 hashes,
  config hash, package versions, and row counts at every stage
- 7-layer audit framework: ADRs → config → row-level audit columns → DQ log →
  validation report → run manifest → process trail (specs + session log)

---

### 1c. What Was Executed — Phase-by-Phase Outcome

Every phase followed the same lifecycle:
`/create-spec` → analysis-spec.md → tech-spec.md (plan mode) → build → `/test` →
`/lint` → clinical-logic-reviewer + code-reviewer agents → `/close-phase` → local commit

| Phase | What was built | Tests added | ADRs written | Commit |
|-------|---------------|-------------|-------------|--------|
| **P00 scaffold** | Repo skeleton, CLAUDE.md, pyproject.toml, notebook stub, module stubs, `.claude/` commands/skills/agents, specs/00-engagement/ with full project brief and data guide | — | — | 8fe950d |
| **P00 follow-up** | `analysis.ipynb` section stubs, module file renames applied to match final names | — | — | b653026 |
| **P01 ingest-and-dq** | `data_loader.py` (DuckDB loader + SHA-256 hash check), `data_quality.py` (19 DQ checks across all 5 tables), `pipeline.py` orchestrator (Stages 1–3 wired), `outputs/dq/dq_log.csv` produced | 15 tests | ADR-001, ADR-003 | 683a713 |
| **P01 DQ augment** | +4 DQ checks (19 total); `config/analysis_rules.yaml` filled with ADR-002/007/008/009 config keys | — | ADR-002, ADR-007, ADR-008, ADR-009 | a762ba6 |
| **P01 notebook** | Notebook decisions panel and Appendix B assumptions register cells added | — | — | 00b0681 |
| **P02 cohort** | `cohort.py` (eligibility filters, index date = earliest of C50-metastatic dx and M1/IV staging, de novo vs recurrent, 4-step attrition table), pipeline Stage 4 wired, notebook Section 2 populated | 11 tests | ADR-004, ADR-005 | 54095f3 |
| **P03 biomarker** | `her2.py` (variant→category map, −365/+90 day window, curated>EHR tie-break, audit columns: `rule_applied`, `winning_record_id`), `hormone_receptor.py` (ER/PR % beats result text, ≥1%=HR+, ER-low flag), pipeline Stages 5–6 wired, notebook Sections 3–4 populated | 24 tests | ADR-006, ADR-007, ADR-008, ADR-009 | 3a6a2ba |
| **P04 q1-distribution** | `statistics.py` (Wilson 95% CI, n<11 small-cell flagging), `q1_distribution.py` (overall + by HR status + by disease type + by curation source, literature benchmark table, benchmark PNG, HER2 distribution PNG), pipeline Stage 8 wired, notebook Section 5 populated (5a–5f including sensitivity display) | 28 tests | ADR-012, ADR-014 | 3a6a2ba |
| **P05 treatment-lines** | `treatment.py` (drugs started within 28-day window = one regimen, LOT numbered by regimen sequence after index date, `contains_enhertu` flag per line), pipeline Stage 7 wired, notebook Section 6 populated | 15 tests | ADR-010 | 3a6a2ba |
| **P06 q2-uptake** | `q2_uptake.py` (subindication assignment: HER2+/HR+HER2-low/HR+HER2-ultralow/HR-HER2-low/HER2-null, Enhertu uptake % per subindication, time-to-first-Enhertu, competitor drug-class map, discordance lists: Enhertu in HER2-unknown and 1L anti-HER2 in HER2-negative), pipeline Stage 9 wired, notebook Sections 7–8 populated | 17 tests | ADR-011, ADR-013 | 3a6a2ba |
| **P07 deliverables** | `validation.py` (13 invariant checks → audit/validation_report.md), `sensitivity.py` (S1: 180-day window, S2: curated-only, S3: IHC-0→unknown; output isolated to `_sensitivity_tmp/` to protect baseline tables), `report.py` (figures via matplotlib, notebook→HTML via nbconvert, 8-slide PPTX via python-pptx with 5 content slides + Appendix A/B/C), `deliverables/cover_email.txt`, pipeline Stages 10–12 wired; all 14 ADRs accepted; submission zip built; 134/134 tests pass; 0 lint errors | 0 (all 134 existing) | — | 307040e |

**Final headline outputs (103 patients, all data synthetic):**
- HER2-positive: 17 (16.5%) — within published 15–20% range
- HER2-low: 13 (12.6% of all; 31.7% of 41 classifiable) — benchmark 45–55% of classifiable
- HER2-ultralow: 7 (6.8%) | HER2-null: 4 (3.9%) | HER2-unknown: 62 (60.2%)
- Primary finding: 60% unclassifiable — driven by blank IHC variants in EHR records
- Enhertu recipients: 41 total; 23 unknowns received Enhertu (off-label / data gap)
- Validation: 13/13 invariant checks PASS

---

## Part 2 — Detailed Execution Order: What Runs After What

### Phase-level execution order

Each phase runs after the previous phase is committed. Within a phase the lifecycle is
fixed: spec → plan → build → test → lint → review → commit.

```
P00 scaffold
  └─ Repo created, CLAUDE.md written, module stubs placed, notebook section stubs created
        │
P01 ingest-and-dq
  └─ Data loaded, integrity verified, DQ issues logged
        │
P02 cohort-index-date
  └─ 103 eligible patients identified, index dates assigned
        │
P03 biomarker-derivation  (runs parallel with P02 outputs)
  ├─ HER2 classified per patient (her2.py)
  └─ HR status derived per patient (hormone_receptor.py)
        │
P04 q1-her2-distribution  (needs P03 her2 + hr tables)
  └─ Distribution computed, strata built, benchmarks compared
        │
P05 treatment-lines  (needs P02 cohort, runs parallel with P04)
  └─ Regimens grouped, lines numbered, Enhertu flagged
        │
P06 q2-enhertu-uptake  (needs P03 her2 + hr, P05 lines)
  └─ Subindications assigned, uptake computed, discordance flagged
        │
P07 deliverables  (needs all prior outputs)
  ├─ Sensitivity analyses run (S1/S2/S3)
  ├─ 13 invariant checks run
  ├─ HTML notebook exported
  ├─ PPTX deck generated
  └─ Submission zip built
```

---

### Pipeline stage-by-stage execution (what `python -m her2rwd.pipeline --reports` does)

The pipeline orchestrator (`pipeline.py`) runs these 12 stages in order.
Every stage writes to disk; the next stage reads only from prior stage outputs.

#### Stage 1 — Input integrity check (`data_loader.py`)
Computes SHA-256 hashes of all 5 CSVs in `data/raw/` and compares them against
pre-recorded hashes to guarantee the working copies are byte-identical to `../external/`.

#### Stage 2 — Load raw data (`data_loader.py`)
Reads all 5 CSVs (patient, diagnosis, staging, biomarker, medication) into an in-memory
DuckDB connection; no files are modified and the connection lives only for the current run.

#### Stage 3 — Data quality checks (`data_quality.py`)
Runs 19 DQ checks (one per known issue: orphan patients, death-before-birth, future-dated
records, post-death events, duplicate rows, etc.) and writes `outputs/dq/dq_log.csv` with
check name, severity, rows affected, and action taken.

#### Stage 4 — Cohort construction (`cohort.py`)
Applies 4 eligibility filters in sequence (has breast C50 metastatic signal, valid
date of birth, age ≥18 at index date, exists in the patient table) and records every
exclusion in `outputs/tables/attrition.csv`; assigns the metastatic index date as the
earliest of C50-metastatic diagnosis date and M1/IV staging date (ADR-004); classifies
each patient as de novo (no prior primary C50, or gap ≤180 days) or recurrent (ADR-005);
writes `outputs/tables/cohort.csv` with 103 eligible patients.

#### Stage 5 — HER2 classification (`her2.py`)
For each eligible patient, selects biomarker records within the −365/+90 day window
around the index date (ADR-007), maps each `biomarker_variant` string to a HER2 category
using the variant-to-category lookup in `config/analysis_rules.yaml` (ADR-006), breaks
ties by: curated > EHR, then granular variant > blank result, then closest to index date
(ADR-008), and writes `outputs/tables/patient_her2.csv` with one row per patient including
`rule_applied`, `winning_record_id`, and `her2_category`.

#### Stage 6 — HR status derivation (`hormone_receptor.py`)
Selects the most recent pre-index ER and PR biomarker records, uses the numeric percentage
value when present (overriding conflicting result text per ASCO/CAP, ADR-009), classifies
each patient as HR+ (ER or PR ≥1%), HR− (both <1% or negative), or HR-unknown; flags
ER-low (ER 1–10%); writes `outputs/tables/patient_hr.csv`.

#### Stage 7 — Treatment line construction (`treatment.py`)
Groups medication records by patient; drugs with start dates within a 28-day window of
each other are placed in the same regimen (ADR-010); regimens are numbered in chronological
order after the index date to approximate lines of therapy; sets `contains_enhertu=True`
for any line containing trastuzumab deruxtecan; writes `outputs/tables/patient_lines.csv`.

#### Stage 8 — Q1 HER2 distribution (`q1_distribution.py`)
Computes the overall HER2 category distribution across all 103 patients; produces three
stratified cross-tabs (by HR status, by disease type de novo/recurrent, by curation source
curated/uncurated/no-test-in-window); computes Wilson 95% confidence intervals and flags
cells with n<11 per ADR-012; compares against published literature benchmarks per ADR-014;
writes `outputs/tables/q1_overall.csv`, `q1_by_hr.csv`, `q1_by_disease_type.csv`,
`q1_benchmark.csv`, and two PNG figures.

#### Stage 9 — Q2 Enhertu uptake (`q2_uptake.py`)
Assigns each patient to a subindication (HER2+, HR+/HER2-low, HR+/HER2-ultralow,
HR−/HER2-low exploratory, HER2-null/unknown) based on HER2 and HR outputs (ADR-011);
computes Enhertu uptake count and percentage per subindication; computes days from index
date to first Enhertu line; builds competitor drug-class map (CDK4/6 inhibitors,
anti-HER2 agents, taxanes, endocrine therapy, etc.); flags discordant cases: Enhertu in
HER2-unknown patients and 1L anti-HER2 therapy in HER2-negative patients (ADR-013);
writes `outputs/tables/q2_uptake_summary.csv`, `q2_subindication_assignment.csv`,
`q2_enhertu_by_line.csv`, `q2_competitor_map.csv`, `q2_discordance_unknown_her2.csv`,
`q2_discordance_1l.csv`, and one PNG figure.

#### Stage 10 — Sensitivity analyses (`sensitivity.py`)
Reruns Stages 5–9 under three alternative rule sets without overwriting baseline outputs
(all internal compute calls write to `outputs/tables/_sensitivity_tmp/`):
- **S1 narrow window:** pre-index window 365 → 180 days
- **S2 curated-only:** uses only `curation_flag=1` biomarker records
- **S3 conservative IHC-0:** maps plain "IHC 0" to unknown instead of null

Writes side-by-side comparison tables: `outputs/tables/sensitivity_her2_distribution.csv`
and `outputs/tables/sensitivity_uptake.csv`.

#### Stage 11 — Validation (`validation.py`)
Runs 13 invariant checks against the outputs on disk: attrition row counts sum correctly,
every cohort patient has exactly one HER2 category, HER2 distribution percentages sum to
100, no patient has an index date before their birth date, Q1 and Q2 cohorts are identical,
sensitivity row counts are consistent, and more; writes `audit/validation_report.md` with
PASS/FAIL per check; the pipeline aborts if any check FAILs.

#### Stage 12 — Report generation (`report.py`) — `--reports` flag only
Exports `notebooks/analysis.ipynb` to `reports/analysis_notebook.html` via nbconvert
(executes all cells top-to-bottom; no outputs are hard-coded); builds
`reports/HER2_mBC_Enhertu_Assessment.pptx` via python-pptx with 5 content slides
(executive summary, cohort flow, Q1 HER2 distribution, Q2 Enhertu uptake, sensitivity +
fit-for-purpose verdict) plus Appendix A (DQ checks), B (assumptions and tie-break rules),
and C (validation results); all numbers on slides are sourced directly from
`outputs/tables/*.csv` — nothing is typed by hand.

#### After all stages — Run manifest
Writes `outputs/run_manifest.json` recording: UTC timestamp, SHA-256 hash of every input
CSV, SHA-256 hash of `config/analysis_rules.yaml`, Python package versions (duckdb,
pandas, pyyaml, python-pptx, nbconvert), and row counts at every stage — the
reproducibility receipt for the entire run.

---

## Full Repo Tour

```
her2-mbc-feasibility/
│
├── README.md                    ← you are here
├── CLAUDE.md                    ← project constitution: hard rules, conventions, lifecycle, commands
├── pyproject.toml               ← package definition, dependencies (uv-managed)
├── uv.lock                      ← pinned dependency graph for exact reproducibility
├── .python-version              ← pins Python 3.12 for uv
├── .gitignore                   ← excludes outputs/, reports/, data/interim/, .venv/, caches
│
├── config/
│   └── analysis_rules.yaml      ← SINGLE source of truth for every rule, window, threshold,
│                                   code list, and tie-break order; every key cites its ADR ID
│
├── data/
│   ├── raw/                     ← READ-ONLY byte-identical copies of the original CSVs;
│   │   ├── patient.csv             SHA-256-verified against ../external/ at every pipeline run
│   │   ├── diagnosis.csv
│   │   ├── staging.csv
│   │   ├── biomarker.csv
│   │   ├── medication.csv
│   │   └── data_dictionary.xlsx
│   └── interim/                 ← git-ignored; DuckDB working files written here if needed
│
├── src/her2rwd/                 ← the pipeline package; ALL analytical logic lives here
│   ├── __init__.py
│   ├── data_loader.py           ← Stage 1+2: SHA-256 check + DuckDB loader
│   ├── data_quality.py          ← Stage 3: 19 DQ checks → dq_log.csv
│   ├── cohort.py                ← Stage 4: eligibility, index date, de novo/recurrent, attrition
│   ├── her2.py                  ← Stage 5: variant→category, window, tie-break, audit columns
│   ├── hormone_receptor.py      ← Stage 6: ER/PR % → HR status, ER-low flag
│   ├── treatment.py             ← Stage 7: regimen grouping, line-of-therapy, Enhertu flag
│   ├── q1_distribution.py       ← Stage 8: HER2 distribution, 3 strata, benchmarks
│   ├── q2_uptake.py             ← Stage 9: subindications, uptake, time-to-Enhertu, discordance
│   ├── sensitivity.py           ← Stage 10: S1/S2/S3 re-runs, comparison tables
│   ├── statistics.py            ← Wilson 95% CI and n<11 small-cell flagging (used by q1/q2)
│   ├── validation.py            ← Stage 11: 13 invariant checks → validation_report.md
│   ├── report.py                ← Stage 12: matplotlib figures, nbconvert HTML, python-pptx deck
│   └── pipeline.py              ← orchestrates Stages 1–12, writes run_manifest.json
│
├── notebooks/
│   └── analysis.ipynb           ← narrative notebook; imports src/; no logic of its own;
│                                   exported to reports/analysis_notebook.html by Stage 12
│
├── sql/                         ← DuckDB SQL helpers called by src/ modules
│
├── tests/                       ← 134 pytest unit tests; all use in-memory DuckDB fixtures;
│   ├── test_data_loader.py         no real patient data is ever read during test runs
│   ├── test_data_quality.py
│   ├── test_cohort.py
│   ├── test_her2.py
│   ├── test_hormone_receptor.py
│   ├── test_treatment.py
│   ├── test_q1_distribution.py
│   ├── test_q2_uptake.py
│   ├── test_sensitivity.py
│   ├── test_statistics.py
│   ├── test_validation.py
│   └── fixtures/               ← tiny hand-crafted patient cases, one per decision branch
│
├── outputs/                     ← GENERATED by the pipeline; never hand-edited; git-ignored
│   ├── run_manifest.json        ← reproducibility receipt (hashes, versions, row counts)
│   ├── dq/
│   │   ├── dq_log.csv           ← one row per DQ violation: check, table, rows affected, action
│   │   └── dq_summary.csv       ← aggregated DQ pass/fail counts
│   ├── figures/
│   │   ├── q1_her2_distribution.png      ← HER2 category bar chart
│   │   ├── q1_benchmark_comparison.png   ← our distribution vs literature
│   │   └── q2_enhertu_uptake.png         ← Enhertu % by subindication
│   └── tables/
│       ├── cohort.csv                    ← 103 patients with index_date, disease_type, age
│       ├── attrition.csv                 ← 4 exclusion steps with n_in / n_excluded / n_remaining
│       ├── patient_her2.csv              ← per-patient HER2 category + audit columns
│       ├── patient_hr.csv                ← per-patient HR status + ER-low flag
│       ├── patient_lines.csv             ← per-patient line-of-therapy with regimen and Enhertu flag
│       ├── q1_overall.csv                ← HER2 distribution across all 103 patients
│       ├── q1_by_hr.csv                  ← HER2 distribution stratified by HR status
│       ├── q1_by_disease_type.csv        ← HER2 distribution stratified by de novo vs recurrent
│       ├── q1_benchmark.csv              ← our counts vs published literature benchmarks
│       ├── q2_uptake_summary.csv         ← Enhertu uptake % by subindication
│       ├── q2_subindication_assignment.csv ← one row per patient: which subindication they map to
│       ├── q2_enhertu_by_line.csv        ← Enhertu use broken down by line of therapy
│       ├── q2_competitor_map.csv         ← drug class counts by subindication
│       ├── q2_discordance_unknown_her2.csv ← patients who received Enhertu despite unknown HER2
│       ├── q2_discordance_1l.csv         ← patients with anti-HER2 therapy but HER2-negative status
│       ├── sensitivity_her2_distribution.csv ← HER2 distribution baseline vs S1/S2/S3
│       └── sensitivity_uptake.csv        ← Enhertu uptake baseline vs S1/S2/S3
│
├── reports/                     ← GENERATED presentation layer; git-ignored
│   ├── analysis_notebook.html   ← full executed notebook rendered as HTML (D2)
│   └── HER2_mBC_Enhertu_Assessment.pptx ← 8-slide deck (5 content + Appendix A/B/C) (D3)
│
├── audit/                       ← the audit pack (D5); committed to git
│   ├── DECISION_INDEX.md        ← master table of all 14 ADRs with status, phase, config key
│   ├── AI_USAGE.md              ← transparent statement of how Claude Code was used
│   ├── SESSION_LOG.md           ← one row per build session: date, phase, outcome, commit hash
│   ├── validation_report.md     ← generated by Stage 11: 13 invariant checks, all PASS
│   └── decisions/
│       ├── ADR-TEMPLATE.md      ← template for new decisions
│       ├── ADR-001-tooling.md              ← Python + DuckDB + pandas + config-driven
│       ├── ADR-002-eligibility.md          ← C50 required, age ≥18, valid dates
│       ├── ADR-003-dq-handling.md          ← future-dated / post-death / pre-birth records
│       ├── ADR-004-index-date.md           ← earliest of C50-met dx and M1/IV staging
│       ├── ADR-005-de-novo-recurrent.md    ← de novo if gap ≤180 days; recurrent if >180
│       ├── ADR-006-her2-mapping.md         ← variant string → category lookup table
│       ├── ADR-007-her2-window.md          ← −365 to +90 days around index date
│       ├── ADR-008-her2-tiebreak.md        ← curated > EHR, granular variant > blank, closest
│       ├── ADR-009-hr-derivation.md        ← % beats result text; ≥1% = HR+
│       ├── ADR-010-treatment-lines.md      ← 28-day regimen window; LOT numbered from index
│       ├── ADR-011-subindications.md       ← required + exploratory subindication groups
│       ├── ADR-012-statistics.md           ← Wilson 95% CI; n<11 flagged as small cell
│       ├── ADR-013-discordance.md          ← what counts as a discordant Enhertu case
│       └── ADR-014-benchmarks.md           ← literature sources chosen for comparison
│
├── docs/                        ← long-form technical documentation (D6)
│   ├── ARCHITECTURE.md          ← pipeline diagram, module map, design principles
│   ├── DEVELOPMENT_PROCESS.md   ← spec-driven lifecycle, phase gates, agent/command list
│   ├── DATA_LINEAGE.md          ← table: each output → module → config keys → ADRs → raw source
│   └── DATA_DICTIONARY.md       ← readable render of data_dictionary.xlsx + derived-field notes
│
├── specs/                       ← spec-driven process trail (one folder per phase)
│   └── 00-engagement/
│       ├── README.md            ← phase index
│       ├── PROJECT_BRIEF_for_Claude_Code.md    ← full brief handed to Claude in plan mode
│       ├── ASSESSMENT_PLAN_and_Repo_Structure.md ← deliverables, phases, audit framework, folder plan
│       ├── DATA_GUIDE_and_Approach.md          ← data facts, clinical reference logic, open decisions
│       ├── HANDOVER_PROMPT.md                  ← session handover context
│       └── source/
│           ├── candidate_facing_instructions.docx ← original brief (copy; external/ is the master)
│           └── candidate_facing_instructions.md   ← plain-text extraction
│
├── deliverables/
│   └── cover_email.txt          ← D7: cover email draft for Brandon (no dashes per style preference)
│
└── .claude/                     ← Claude Code workspace configuration
    ├── settings.json            ← permission rules (deny list for external/ and data/raw/)
    ├── commands/                ← slash commands: /create-spec, /close-phase, /run-pipeline,
    │                               /validate, /log-decision, /build-report, /test, /lint, /fix
    ├── skills/                  ← reusable skill prompts: generate-analysis-spec,
    │                               generate-tech-spec, write-test, clinical-rules-reference,
    │                               decision-log, deck-builder
    └── agents/                  ← specialized agents: code-reviewer, clinical-logic-reviewer,
                                    test-writer, reviewer-simulator
```

---

## Where to Find X

| What you want to find | Where to look |
|-----------------------|---------------|
| A specific rule (e.g. HER2 window) | `config/analysis_rules.yaml` → find the key |
| Why that rule was chosen | `audit/DECISION_INDEX.md` → find the ADR → open `audit/decisions/ADR-NNN-*.md` |
| A number on slide 3 | Check the slide speaker note for the source CSV → `outputs/tables/<table>.csv` |
| Why a patient is in a given HER2 bucket | `outputs/tables/patient_her2.csv` → `rule_applied` + `winning_record_id` columns |
| Why a patient was excluded from the cohort | `outputs/tables/attrition.csv` → `step_label` + `n_excluded` |
| A data quality issue | `outputs/dq/dq_log.csv` → filter by `check_name` or `table` |
| Which session built what | `audit/SESSION_LOG.md` |
| The full pipeline run receipt | `outputs/run_manifest.json` |
| Why sensitivity S1/S2/S3 were chosen | `audit/decisions/ADR-007-her2-window.md` (S1) and `ADR-006-her2-mapping.md` (S3) |
| The competitor drug list by subindication | `outputs/tables/q2_competitor_map.csv` |
| Discordant Enhertu cases | `outputs/tables/q2_discordance_unknown_her2.csv` and `q2_discordance_1l.csv` |

---

## Audit Framework — 7 Layers

Every number in the deck can be traced back to a raw CSV row through these layers:

| Layer | Artifact | Answers |
|-------|----------|---------|
| 1. Decision log (ADRs) | `audit/decisions/ADR-NNN-*.md` + `audit/DECISION_INDEX.md` | *Why this rule?* |
| 2. Rules as config | `config/analysis_rules.yaml` | *What exactly is the rule?* |
| 3. Row-level audit trail | `outputs/tables/patient_her2.csv` (`rule_applied`, `winning_record_id`) | *Why is this patient in this bucket?* |
| 4. DQ log | `outputs/dq/dq_log.csv` | *What was wrong with the data and what did we do?* |
| 5. Validation report | `audit/validation_report.md` | *Can the numbers be trusted?* |
| 6. Run manifest | `outputs/run_manifest.json` | *Can it be reproduced?* |
| 7. Process trail | `specs/00-engagement/` + `audit/SESSION_LOG.md` + `audit/AI_USAGE.md` | *How was it built?* |

---

## Note on `../external/`

The folder `../external/` (one level above this repo) holds the original, unmodified
ConcertAI email attachment exactly as received. It is **STRICTLY READ-ONLY** — this repo
never writes, edits, or deletes anything there.

`data/raw/` contains byte-identical working copies, verified by SHA-256 at every pipeline
run (Stage 1). If the hashes do not match, the pipeline stops immediately.

---

## Rerunning from Scratch

```bash
# Install dependencies
uv sync

# Run tests (should show 134 passed, 0 failed)
uv run pytest tests/ -v --cov=src/her2rwd --cov-report=term-missing

# Lint check
uv run ruff check src/ tests/ && uv run black --check src/ tests/

# Full pipeline (Stages 1–11, no reports)
uv run python -m her2rwd.pipeline

# Full pipeline + generate HTML notebook and PPTX deck (Stages 1–12)
uv run python -m her2rwd.pipeline --reports

# Use an alternate rules file for a what-if run
uv run python -m her2rwd.pipeline --rules config/alt_rules.yaml
```

**Expected terminal output (abridged):**
```
Stage 1: input integrity check... 6 files verified OK
Stage 2: loading raw data... patient: 150 | diagnosis: 333 | ...
Stage 3: data quality checks... 19 checks: 0 errors, N warnings
Stage 4: building cohort... 103 eligible patients (XX de novo, YY recurrent)
Stage 5: deriving HER2 categories... positive: 17 | low: 13 | ultralow: 7 | null: 4 | unknown: 62
Stage 6: deriving HR status... positive: 56 | negative: 47 | ...
Stage 7: building treatment lines... N patients with treatment; Enhertu: 41
Stage 8: computing Q1 HER2 distribution...
Stage 9: computing Q2 Enhertu uptake...
Stage 10: running sensitivity analyses...
Stage 11: running validation checks... 13 PASS, 0 FAIL
Stage 12: building reports (HTML + pptx)...
Manifest written to outputs/run_manifest.json
```

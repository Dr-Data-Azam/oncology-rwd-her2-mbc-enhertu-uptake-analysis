# Nexus Health Data HER2 mBC Feasibility Study: Deliverables, Audit Framework & Repo Structure

> ⛔ **HARD RULE: `../external/` (ConcertAI_Assesment/external) is STRICTLY READ-ONLY.**
> It is the original, unmodified attachment from Nexus Health Data. Never write, edit, rename, move, delete, unzip into, or create files inside it, and never run any command with it as the working directory that could write output there. Read from it only to verify inputs (e.g. hash checks). All work happens inside `her2-mbc-feasibility/`. Working copies of the data are in `data/raw/` (verified identical by SHA-256).


This plan is adapted from the spec-driven setup in `Dr-Data-Azam/shafers-ai-pathology-assistant`. Hand it to Claude Code together with `PROJECT_BRIEF_for_Claude_Code.md` and `DATA_GUIDE_and_Approach.md`.

---

## 1. Deliverables (who, what, when)

**Owner:** Azam, who approves every spec and decision. **Builder:** Claude Code.
**Hard deadline:** submit deliverables **Wed Sep 30, evening ET**. The review is **Thu Oct 1, 3:00 PM ET**.

| # | Deliverable | Format | Client deliverable? | Content | Done when |
|---|---|---|---|---|---|
| **D1** | Source code | zipped repo (`her2-mbc-analysis.zip`) | ✅ | pipeline package, SQL, tests, `config/analysis_rules.yaml`, README | `uv sync && python -m her2rwd.pipeline` reproduces every output from the raw CSVs |
| **D2** | Rendered analysis notebook | `analysis_notebook.html` | ✅ | narrative + code + tables for Q1 and Q2 | runs top to bottom with no errors; exported with outputs |
| **D3** | Slide deck | `.pptx` (plus a PDF copy) | ✅ | 5 slides + 1–2 appendix slides (DQ checks, assumptions) | every number traces to a table in D4 |
| **D4** | Output tables & figures | CSV/XLSX + PNG | ✅ (inside the zip) | cohort, attrition, per-patient HER2/HR audit, Q1 and Q2 tables, sensitivity, discordance list | produced by the pipeline, never hand-edited |
| **D5** | Audit pack | Markdown + CSV | ✅ (inside the zip) | decision log (ADRs), assumptions register, DQ log, validation report, run manifest | every rule in the code has an ADR; every ADR has evidence |
| **D6** | README + repo docs | Markdown | ✅ | README (repo tour, rerun steps), `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT_PROCESS.md`, `docs/DATA_LINEAGE.md` (see Section 10) | a stranger can rerun it in under 5 minutes and find any rule in under 1 minute |
| **D7** | Cover email | text | ✅ | 4–5 line summary + attachments list (no dashes) | Azam approves |
| **D8** | Talk track + Q&A prep (in `../_prep/`) | Markdown | ❌ internal | 15-minute script, ~20 likely questions with 30-second answers | rehearsed Thu morning |

Deck outline (D3):
1. **Executive summary**: the answer, the fit-for-purpose verdict, the top 3 caveats
2. **Cohort and method**: attrition flow, index date, HER2 and HR rules
3. **Q1**: HER2 distribution, 4 stratifications, literature comparison, unclassifiable share
4. **Q2**: Enhertu uptake by subindication, time to first Enhertu, competitors, discordant cases
5. **Fit for purpose, sensitivity analyses and how to productionize**
- **Appendix A**: DQ checks · **Appendix B**: assumptions and tie-break rules · **Appendix C**: how the repo is organized (pipeline diagram, audit layers, spec-driven process)

---

## 2. What we keep, change and drop from the Shafer's repo

| Shafer's element | Decision | Why |
|---|---|---|
| `CLAUDE.md` as the project constitution | **Keep, rewrite** | same role: project overview, rules, permission boundaries, lifecycle |
| Spec-driven lifecycle (non-tech → tech spec → build → test → review → summary) | **Keep** | this becomes the audit backbone: every analytic step has a "why" and a "how" before any code exists |
| `specs/NN-slug/` with non-tech, tech, code-review and implementation-summary files | **Keep** | one spec per analysis phase (Section 4) |
| `/create-spec` | **Keep, simplified** | no `git pull` or remote; creates a local branch and the spec folder, then interviews Azam |
| `/ship-feature` (commit → push → PR → merge) | **Drop → replace with `/close-phase`** | no GitHub. Instead: tests → lint → run pipeline → validate → implementation summary → **local commit** |
| `/test`, `/lint`, `/fix` | **Keep** | unchanged (pytest, Black, Ruff) |
| `/eval` (RAG golden-question eval) | **Drop → replace with `/run-pipeline` + `/validate`** | our "eval" is reconciliation: counts add up, one HER2 category per patient, percentages sum to 100 |
| `generate-non-tech-spec` skill | **Adapt → `generate-analysis-spec`** | the questions change from "user story" to "client question, definitions, outputs, alternatives" |
| `generate-tech-spec` skill | **Keep, retarget** | same template; the architecture table points to the new modules |
| `write-test` skill | **Adapt** | table-driven tests for clinical rules on tiny hand-made fixtures, not API mocks |
| `rag-eval` skill | **Drop → `clinical-rules-reference` skill** | HER2 and HR definitions, Enhertu labels, competitor map, literature benchmarks with citations |
| — | **New `decision-log` skill + `/log-decision` command** | ADR template, the core of the audit |
| — | **New `deck-builder` skill + `/build-report` command** | 5-slide rules, finding-as-title, notebook → HTML export |
| `code-reviewer` agent | **Keep, adapt checklist** | adds reproducibility, no hard-coded parameters, SQL/pandas join correctness |
| `security-reviewer` agent | **Drop → `clinical-logic-reviewer` agent** | there are no secrets or user input here. The risk is **clinically wrong logic**, so review against ASCO/CAP and the labels |
| `test-writer` agent | **Keep** | retargeted through the adapted skill |
| — | **New `reviewer-simulator` agent** | plays the reviewer: reads the deck and audit pack, fires tough follow-up questions, and writes the D8 Q&A prep |
| `.github/workflows`, `Dockerfile`, `docker-compose`, `infrastructure/` | **Drop** | out of scope; mention them under "how I'd productionize" instead |
| `.env`, API keys, `chat_history`, vectorDB rules | **Drop** | not relevant |
| `pyproject.toml` + `uv.lock` + `.python-version` | **Keep** | pinned environment = reproducibility |
| Dated eval results kept as a baseline | **Adapt → `run_manifest.json`** | each run records input hashes, config hash, git commit and row counts at every step |

---

## 3. Audit framework (answering "why did you decide that?")

Seven layers. Together they let Azam, or the reviewer, trace any number back to raw rows and a written decision.

| Layer | Artifact | Answers |
|---|---|---|
| **1. Decision log (ADRs)** | `audit/decisions/ADR-NNN-slug.md` + `audit/DECISION_INDEX.md` | *Why this rule?* Context → options considered → choice → **data evidence** → impact → which sensitivity analysis tests the alternative |
| **2. Rules as config** | `config/analysis_rules.yaml` | *What exactly is the rule?* Every window, threshold, code list and tie-break order lives in one file, and the code reads from it. Each key references its ADR ID. Changing a rule means editing config, not code, which is the production-minded answer. |
| **3. Row-level audit trail** | `outputs/tables/patient_audit.csv` | *Why is this patient in this bucket?* One row per patient: included/excluded + reason, index date + source record, winning HER2 record + rule applied + candidates considered, HR evidence, subindication, first-line regimen |
| **4. DQ log** | `outputs/dq/dq_log.csv` | *What was wrong with the data and what did we do?* check_id, table, rule, rows/patients affected, action (exclude / flag / fix), ADR link |
| **5. Validation report** | `audit/validation_report.md` (auto-generated) | *Can the numbers be trusted?* Invariant checks with PASS/FAIL: attrition sums, one category per patient, no index date before birth, percentages sum to 100, Q1 cohort = Q2 cohort |
| **6. Run manifest** | `outputs/run_manifest.json` | *Can it be reproduced?* timestamp, git commit, SHA-256 of each input CSV, hash of the rules file, package versions, row counts per step |
| **7. Process trail** | `specs/NN-*/` files + local git history (one commit per phase) + `audit/AI_USAGE.md` | *How was it built?* spec → plan → build → review → summary for each phase. AI_USAGE states plainly that Claude Code was used, and that Azam wrote and approved the specs and validated the outputs. |

### ADR template (`decision-log` skill)
```markdown
# ADR-004: HER2 look-up window around the metastatic index date
Status: Accepted | Date: 2026-09-30 | Phase: 03-biomarker-derivation | Config key: her2.window_days
## Context        (the clinical and data problem, 2–3 lines)
## Options considered
| Option | Pros | Cons | Data impact |
| −365/+90 | common in RWE | misses post-index biopsies | HER2 found for 71/104 |
| −365/+180 | captures metastatic biopsy reporting lag | risk of post-treatment tests | 95/104 |
## Decision       (the chosen option, one sentence)
## Rationale      (clinical + data reasons; cite guideline or paper)
## Evidence       (numbers from the profiling or the pipeline run)
## Consequences   (what it biases, and in which direction)
## Sensitivity    (alternative tested in S2; result: see Table S2)
## Reviewer notes (clinical-logic-reviewer verdict)
```

### Starter ADR backlog (decisions we know we must make)
| ADR | Decision |
|---|---|
| 001 | Tooling: Python + DuckDB SQL + pandas; one package; config-driven |
| 002 | Eligibility: breast C50 required; plausible age; valid dates; must exist in the patient table |
| 003 | Handling of future-dated, post-death and pre-birth records |
| 004 | Metastatic index date definition and source priority (diagnosis vs stage; curated vs EHR) |
| 005 | De novo vs recurrent definition |
| 006 | HER2 variant → category mapping (incl. "IHC 0 with membrane staining", "IHC 0" not otherwise specified) |
| 007 | HER2 look-up window |
| 008 | HER2 tie-break hierarchy (variant > result; curated > EHR; closest; conflict rule) |
| 009 | HR derivation (percentage beats result text; ≥1%; ER-low flag) |
| 010 | Regimen grouping and line-of-therapy approximation |
| 011 | Subindication framework (required + exploratory groups) |
| 012 | Statistics: Wilson CIs; small-cell (n<11) flagging |
| 013 | Discordance definitions (treatment vs biomarker) |
| 014 | Literature benchmarks chosen and cited |

---

## 4. Phases = specs (the build order)

Each phase goes through the full lifecycle, `/create-spec` → analysis spec → tech spec (Plan Mode) → build → `/test` → reviewers → `/close-phase`, and each phase writes its ADRs.

| Spec | Phase | Main outputs | ADRs | Time |
|---|---|---|---|---|
| `00-engagement` | Context only (no code): brief, data guide, this plan | — | — | done |
| `01-ingest-and-dq` | Load raw CSVs into DuckDB, hash the inputs, run the DQ checks | `dq_log.csv`, `run_manifest.json` | 001, 003 | 1.5 h |
| `02-cohort-index-date` | Eligibility, metastatic index date, de novo/recurrent, attrition | `cohort.csv`, `attrition.csv` | 002, 004, 005 | 2 h |
| `03-biomarker-derivation` | HER2 and HR classification with the audit trail | `patient_her2.csv`, `patient_hr.csv` | 006–009 | 2.5 h |
| `04-q1-her2-distribution` | Overall + 4 strata + literature comparison + sensitivity analyses | `q1_*.csv`, figures | 012, 014 | 2 h |
| `05-treatment-lines` | Regimens, lines, first treatment after the metastatic date | `patient_lines.csv` | 010 | 1.5 h |
| `06-q2-enhertu-uptake` | Subindications, uptake, time to Enhertu, competitors, discordance | `q2_*.csv`, figures | 011, 013 | 2.5 h |
| `07-deliverables` | Notebook → HTML, deck, README, validation report, zip, email draft | D1–D7 | — | 2.5 h |
| `08-review-prep` | reviewer-simulator → Q&A + talk track | D8 | — | 1 h |

**Gate between phases:** Azam approves the analysis spec and the tech spec, and reads the new ADRs before `/close-phase`.

---

## 5. Folder structure

### 5a. Workspace (NOT a repo)
```
ConcertAI_Assesment/                              ← workspace folder, not under git
├── sr_ds_comm_analytics_tech_assessment_2026.zip ← email attachment as received (read-only)
├── external/                                     ← unzipped original (STRICTLY READ-ONLY)
├── her2-mbc-feasibility/                         ← ★ REPO ROOT: git init here, open Claude Code here
├── _submission/                                  ← outbox: exactly what gets emailed (built by /build-report)
└── _prep/                                        ← private: talk track, Q&A prep (NEVER sent)
```
`_submission/` and `_prep/` live **outside** the repo, so private notes can never be zipped by accident and the repo never contains a zip of itself.

### 5b. Repo root: `her2-mbc-feasibility/`
```
her2-mbc-feasibility/
├── README.md                        # entry point: summary, quickstart, repo tour, "where to find X"
├── CLAUDE.md                        # project constitution (read-only rule first)
├── pyproject.toml · uv.lock · .python-version · .gitignore
│
├── config/
│   └── analysis_rules.yaml          # SINGLE source of truth for every rule (keys cite ADR IDs)
│
├── data/
│   ├── raw/                         # working copies of the CSVs + dictionary (READ-ONLY; hash-checked vs ../external/)
│   └── interim/                     # her2rwd.duckdb (generated, git-ignored)
│
├── src/her2rwd/                     # the pipeline package; all logic lives here
│   ├── __init__.py
│   ├── io.py                        # load raw data, hash inputs, build the DuckDB file
│   ├── dq.py                        # data-quality checks → dq_log
│   ├── cohort.py                    # eligibility, index date, de novo/recurrent, attrition
│   ├── her2.py                      # variant mapping, window, tie-breaks, audit columns
│   ├── hr.py                        # ER/PR → HR status
│   ├── treatment.py                 # regimens, lines of therapy
│   ├── q1_distribution.py           # HER2 distribution, strata, benchmarks
│   ├── q2_uptake.py                 # subindications, uptake, time to Enhertu, competitors, discordance
│   ├── sensitivity.py               # reruns the pipeline under alternative rule sets
│   ├── stats.py                     # Wilson CI, small-cell flags
│   ├── validate.py                  # invariants → validation_report.md
│   ├── report.py                    # deck + notebook export → reports/
│   └── pipeline.py                  # runs everything end to end and writes run_manifest.json
│
├── sql/                             # DuckDB models called by src/ (01_stg_*.sql, 02_cohort.sql, ...)
├── notebooks/
│   └── analysis.ipynb               # narrative only; imports src/, contains no logic
│
├── tests/
│   ├── fixtures/                    # tiny hand-made patient cases
│   ├── test_her2.py · test_hr.py · test_cohort.py · test_treatment.py
│   └── test_invariants.py
│
├── outputs/                         # GENERATED by the pipeline; never hand-edited
│   ├── tables/                      # cohort, attrition, patient_audit, q1_*, q2_*, sensitivity_*
│   ├── figures/
│   ├── dq/dq_log.csv
│   └── run_manifest.json
│
├── reports/                         # GENERATED presentation layer
│   ├── HER2_mBC_Enhertu_Analysis.pptx (+ .pdf)
│   └── analysis_notebook.html
│
├── audit/                           # the audit pack (D5)
│   ├── DECISION_INDEX.md
│   ├── decisions/ADR-001-tooling.md … ADR-014-benchmarks.md
│   ├── assumptions_register.md      # rendered from analysis_rules.yaml
│   ├── validation_report.md         # generated
│   ├── git_log.txt                  # exported commit history
│   ├── SESSION_LOG.md               # one row per Claude Code session (name, date, phase, outcome, commit)
│   └── AI_USAGE.md
│
├── docs/                            # repo documentation for reviewers (D6)
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT_PROCESS.md
│   ├── DATA_LINEAGE.md
│   └── DATA_DICTIONARY.md           # readable render of data/raw/data_dictionary.xlsx (+ derived-field notes later)
│
├── specs/                           # spec-driven process trail
│   ├── 00-engagement/               # brief, data guide, this plan, index
│   │   └── source/                  # candidate_facing_instructions.docx (copy) + .md text extraction
│   └── 01-ingest-and-dq/ … 07-deliverables/
│        ├── analysis-spec.md · tech-spec.md
│        ├── code-review.md · clinical-review.md
│        └── implementation-summary.md
│
└── .claude/                         # Claude Code setup (settings with deny rules, commands, skills, agents)
```

### 5c. What is emailed (`../_submission/`)
| File | Built from |
|---|---|
| `HER2_mBC_Enhertu_Analysis.pptx` + `.pdf` | `reports/` |
| `analysis_notebook.html` | `reports/` |
| `her2-mbc-feasibility.zip` | the repo, **excluding** `.git/`, `data/interim/`, `.venv/`, caches |

`/build-report` builds this folder. Phase 08 (review prep) writes to `../_prep/`, not into the repo.

---

## 6. New and changed commands in brief

| Command | Does |
|---|---|
| `/create-spec <slug>` | check the working tree is clean → local branch `phase/<slug>` → create `specs/NN-slug/` → interview Azam with the analysis-spec questions → save `analysis-spec.md` |
| `/log-decision "<title>"` | create the next ADR from the template, fill it with evidence from the latest run, add it to DECISION_INDEX, and link it from the `analysis_rules.yaml` key |
| `/run-pipeline [--rules alt.yaml]` | `python -m her2rwd.pipeline`; writes outputs + manifest; prints attrition and headline counts |
| `/validate` | runs the invariants → `validation_report.md`; STOPs on any FAIL |
| `/close-phase "<msg>"` | `/test` → `/lint` → `/run-pipeline` → `/validate` → clinical-logic-reviewer + code-reviewer → write implementation-summary → check that every new rule has an ADR → **local** commit, merge into `main`, **no push** |
| `/build-report` | export the notebook to HTML, build the pptx through the deck-builder skill, render assumptions_register, zip `../_submission/her2-mbc-feasibility.zip` |

## 7. Analysis-spec questions (replacing the 5 non-tech questions)
1. **Client question:** what business or feasibility question does this phase answer?
2. **Definitions:** what exactly are we classifying or counting, and what is the clinical source (guideline or label)?
3. **Outputs:** which tables, figures and audit columns must exist when the phase is done?
4. **Alternatives:** what other reasonable definitions exist? Which becomes the sensitivity analysis?
5. **Constraints and risks:** what must not change, which DQ issues bite here, and what is still unresolved?

## 8. CLAUDE.md permission boundaries for this project
- **Never touch `../external/`**: strictly read-only (no write, edit, rename, move, delete, unzip into). Read it only for hash verification.
- Never modify `data/raw/`.
- Never hard-code a rule parameter; it goes in `config/analysis_rules.yaml` with an ADR reference.
- Never hand-edit `outputs/`, and never type a number into the deck that isn't in `outputs/tables/`.
- No `git push` and no remote operations.
- Report counts with denominators; flag cells with n < 11; state that all data is synthetic.
- Every clinical claim in the deck or ADRs must carry a citation. When unsure, mark it `VERIFY`.
- Emails drafted for Azam: no dashes.

## 9. Timeline
| When | Phases |
|---|---|
| Tue night | scaffold repo + `01` + `02` |
| Wed morning | `03` + `04` |
| Wed afternoon | `05` + `06` |
| Wed evening | `07` → **submit deliverables** |
| Thu morning | `08` rehearsal |

---

## 10. The repo itself as a showcase

The reviewer will look at **how** the work is organized, not only the answers. The repo must explain itself.

| Doc | Content | Why it matters to a reviewer |
|---|---|---|
| `README.md` | 1-paragraph summary · quickstart (3 commands) · **repo tour** (folder → purpose table) · "where to find X" (a rule, a decision, a number on slide 3) · the read-only note on `external/` | first impression; proves reproducibility |
| `docs/ARCHITECTURE.md` | pipeline diagram (raw → DQ → cohort → HER2/HR → lines → Q1/Q2 → deliverables) · one line per module · design principles: config-driven rules, layered tidy tables, audit columns, no logic in the notebook, generated (never hand-edited) outputs | shows production thinking |
| `docs/DEVELOPMENT_PROCESS.md` | spec-driven lifecycle (analysis spec → tech spec → build → test → clinical + code review → close-phase) · phase gates · agents and commands used · git log excerpt · AI-assisted, human-directed and human-validated | shows method and governance, and is honest about AI use |
| `docs/DATA_LINEAGE.md` | table: each output → module → config keys → ADRs → raw source tables | "where did this number come from?" answered in one lookup |
| `CLAUDE.md` + `.claude/` | kept in the submission | evidence of the engineered workflow (optional to mention; include if Azam wants to show the agentic process) |
| Docstrings | every public function: purpose, inputs, outputs, the ADR it implements | code reads like documentation |

**Where the structure shows up in the presentation:**
- Deck **Appendix C**: a one-slide repo map + pipeline diagram + the 7 audit layers.
- Talk track (D8): a **2-minute repo walkthrough** segment: README → `config/analysis_rules.yaml` → one ADR → `patient_audit.csv` row → validation report. This traces one patient from a raw row to a number on a slide.
- Cover email (D7): one line saying the repo is self-documenting, with the README as the entry point.

**Done when:** a reviewer can answer all four of these without asking Azam: *How do I rerun it? Where is rule X defined? Why was rule X chosen? How did patient Y end up in bucket Z?*

---

## 11. Session naming & session log

One Claude Code session per phase. Every session name follows one pattern:

`concertai-her2 | P<NN> <phase-slug>`

| Phase | Session name |
|---|---|
| 00 | `concertai-her2 \| P00 scaffold` |
| 01 | `concertai-her2 \| P01 ingest-and-dq` |
| 02 | `concertai-her2 \| P02 cohort-index-date` |
| 03 | `concertai-her2 \| P03 biomarker-derivation` |
| 04 | `concertai-her2 \| P04 q1-her2-distribution` |
| 05 | `concertai-her2 \| P05 treatment-lines` |
| 06 | `concertai-her2 \| P06 q2-enhertu-uptake` |
| 07 | `concertai-her2 \| P07 deliverables` |
| 08 | `concertai-her2 \| P08 review-prep` |

Fix-up sessions within a phase add a letter: `P03b biomarker-derivation-fixes`.

`audit/SESSION_LOG.md` gets one row per session, appended by `/close-phase` (or manually for an unfinished session):

| Session | Date | Phase / spec | Outcome | ADRs added | Commit |
|---|---|---|---|---|---|
| concertai-her2 \| P00 scaffold | 2026-09-29 | 00 | scaffold created | — | abc1234 |

This ties the conversation history, the spec folder, the ADRs and the git commit together: the process-trail layer of the audit.

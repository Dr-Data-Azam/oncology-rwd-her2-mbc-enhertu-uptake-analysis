# CLAUDE.md — Project Constitution: her2-mbc-feasibility

---

## ⛔ HARD RULES (read before anything else)

1. **`../external/` is STRICTLY READ-ONLY.** Never write, edit, rename, move, delete, or
   unzip into it. Never run any command whose output could land there. Read it only to
   verify SHA-256 hashes (via `src/her2rwd/data_loader.py`).

2. **`data/raw/` is also read-only.** These are byte-identical working copies of the
   originals. No pipeline step, script, or edit ever modifies them. All outputs go to
   `outputs/`.

3. **Local git only.** No remote, no `git push`, no GitHub operations of any kind.

---

## Project Overview

**What:** ConcertAI technical assessment — HER2 metastatic breast cancer feasibility and
Enhertu uptake analysis on 150 synthetic patients.

**Who:** Azam (Associate Director, Solutions Consulting, ConcertAI) as owner and approver;
Claude Code as builder.

**Deadline:** Email Brandon Nathasingh Wed Sep 30 evening ET. Review Thu Oct 1, 3:00 PM ET.

**Two client questions:**
- Q1: What is the HER2 distribution (positive / low / ultralow / 0-null / unknown) at
  metastatic diagnosis? Is this data asset feasible for HER2-defined mBC studies?
- Q2: How does Enhertu uptake compare with competitors across HER2-defined subindications?
  Is this asset fit for a commercial or feasibility question about Enhertu in mBC?

**Deliverables:**

| ID | Deliverable | Format | To Brandon? |
|---|---|---|---|
| D1 | Source code (reproducible) | zipped repo | ✅ |
| D2 | Rendered analysis notebook | HTML | ✅ |
| D3 | Slide deck (5 slides + Appendix A/B/C) | .pptx (pdf skipped — no LibreOffice) | ✅ |
| D4 | Output tables and figures | CSV/PNG | ✅ (inside zip) |
| D5 | Audit pack | Markdown + CSV | ✅ (inside zip) |
| D6 | README + repo docs | Markdown | ✅ |
| D7 | Cover email | text (no dashes) | ✅ |
| D8 | Talk track + Q&A prep | Markdown | ❌ internal (_prep/) |

---

## Architecture

```
data/raw/          ← READ-ONLY input (5 CSVs + data_dictionary.xlsx)
     │
     ▼
data_loader.py     load + SHA-256 integrity check → DuckDB
     │
     ▼
data_quality.py    DQ checks → outputs/dq/dq_log.csv
     │
     ▼
cohort.py          eligibility + index date + de novo/recurrent → outputs/tables/cohort.csv
     │             attrition.csv
     ▼
her2.py            variant mapping + window + tie-break → outputs/tables/patient_her2.csv
hormone_receptor.py  ER/PR % → outputs/tables/patient_hr.csv
     │
     ▼
treatment.py       regimens + lines → outputs/tables/patient_lines.csv
     │
     ├── q1_distribution.py  → outputs/tables/q1_*.csv
     ├── q2_uptake.py        → outputs/tables/q2_*.csv
     └── sensitivity.py      → outputs/tables/sensitivity_*.csv
     │
     ▼
validation.py      invariant checks → audit/validation_report.md
     │
     ▼
report.py          notebook → HTML; outputs → .pptx → reports/
     │
     ▼
pipeline.py        orchestrates all stages → outputs/run_manifest.json
```

**Module map:**

| Module | Responsibility |
|---|---|
| `data_loader.py` | Load raw CSVs into DuckDB; SHA-256 integrity check vs ../external/ |
| `data_quality.py` | Data-quality checks → outputs/dq/dq_log.csv |
| `cohort.py` | Eligibility, metastatic index date, de novo/recurrent, attrition |
| `her2.py` | HER2 variant → category, biomarker window, tie-break, audit columns |
| `hormone_receptor.py` | ER/PR % → HR status, ER-low flag |
| `treatment.py` | Regimen grouping, line-of-therapy approximation |
| `q1_distribution.py` | HER2 distribution, strata, literature benchmarks |
| `q2_uptake.py` | Subindications, Enhertu uptake, competitors, discordance list |
| `sensitivity.py` | Re-runs pipeline under alternative rule sets |
| `statistics.py` | Wilson 95% CI, small-cell (n<11) flagging |
| `validation.py` | Invariant checks → audit/validation_report.md |
| `report.py` | Notebook → HTML (nbconvert); outputs → .pptx (python-pptx) |
| `pipeline.py` | End-to-end orchestration → outputs/run_manifest.json |

---

## Conventions

- **No hard-coded parameters.** Every window, threshold, code list, and tie-break order
  lives in `config/analysis_rules.yaml`. Code reads from config; changing a rule means
  editing config, not code.
- **All outputs are generated.** Nothing in `outputs/` or `reports/` is ever hand-edited.
  Numbers flow from raw data → pipeline → tables → deck.
- **Docstrings cite ADR IDs.** Every public function docstring names the ADR that governs
  its behavior (e.g. `# ADR-007`).
- **Emails to Brandon have no dashes** (Azam's style preference). Draft them in D7 only.
- **VERIFY markers.** All VERIFY markers were resolved in Phase 04 with confirmed primary
  literature citations (FDA DB-06 approval Jan 27 2025; DB-09 Dec 15 2025; DESTINY-Breast
  benchmarks). Any new clinical claim added in future phases must carry a citation before
  it can be stated as fact.
- **Small-cell flagging.** Report counts with denominators; flag cells with n < 11 as
  `n<11` per ADR-012 and standard RWD practice.
- **State that all data is synthetic** in the deck and README.

---

## Permission Boundaries (ASSESSMENT_PLAN §8)

- Never touch `../external/` (see Hard Rule 1).
- Never modify `data/raw/` (see Hard Rule 2).
- Never hand-edit anything in `outputs/` or `reports/`.
- Never type a number into the deck that is not sourced from `outputs/tables/`.
- No `git push`, no remote operations, no GitHub calls.
- Every clinical claim in the deck or ADRs must carry a citation or a `VERIFY` marker.

---

## Feature Lifecycle (spec-driven)

```
/create-spec <slug>
      │
      ▼
 analysis-spec.md   ← Azam approves
      │
      ▼ (Plan Mode)
  tech-spec.md      ← Azam approves + reads new ADRs
      │
      ▼
   BUILD (code + tests)
      │
      ▼
 /test  /lint
      │
      ▼
 clinical-logic-reviewer  +  code-reviewer  (agents)
      │
      ▼
 /close-phase         ← appends row to audit/SESSION_LOG.md → local commit
```

**Phase gate:** Azam must approve the analysis spec AND the tech spec, and read any new
ADRs, before `/close-phase` is allowed to commit.

---

## Commands

| Command | What it does |
|---|---|
| `/create-spec <slug>` | Clean tree check → branch `phase/<slug>` → create `specs/NN-slug/` → interview Azam on 5 analysis-spec questions → save `analysis-spec.md` |
| `/close-phase "<msg>"` | test → lint → run-pipeline → validate → clinical-logic-reviewer + code-reviewer → implementation-summary → ADR check → append SESSION_LOG row → local commit → merge main |
| `/run-pipeline [--rules alt.yaml] [--reports]` | `uv run python -m her2rwd.pipeline`; prints attrition + headline counts. `--reports` also runs stages 10–12 (figures + HTML + pptx) |
| `/validate` | Run invariants; STOP on any FAIL; write `audit/validation_report.md` |
| `/log-decision "<title>"` | Create next ADR from template; fill from latest run; update DECISION_INDEX; link from analysis_rules.yaml |
| `/build-report` | Notebook → HTML; outputs → pptx; zip `../_submission/` |
| `/test` | `uv run pytest tests/ -v --cov=src/her2rwd --cov-report=term-missing` |
| `/lint` | `uv run ruff check src/ tests/ && uv run black --check src/ tests/` |
| `/fix` | `uv run ruff check --fix src/ tests/ && uv run black src/ tests/` |

---

## Skills

| Skill | What it does |
|---|---|
| `generate-analysis-spec` | Interviews Azam on 5 questions (client question, definitions, outputs, alternatives, constraints/risks); writes `analysis-spec.md` |
| `generate-tech-spec` | Turns analysis spec into `tech-spec.md` (architecture table, module changes, SQL models, tests, ADRs to write) |
| `write-test` | Writes table-driven pytest fixtures; one tiny hand-made patient case per decision branch |
| `clinical-rules-reference` | Provides HER2/HR rules (ASCO/CAP 2018/2023), Enhertu labels (DB-06/DB-09 confirmed), competitor map, literature benchmarks (citations confirmed Phase 04) |
| `decision-log` | Fills ADR template from `audit/decisions/ADR-TEMPLATE.md`; adds evidence from current run |
| `deck-builder` | Enforces 5-slide structure; titles = finding sentences; routes numbers to CSV sources; exports via python-pptx |

---

## Agents

| Agent | What it does |
|---|---|
| `code-reviewer` | Reviews diffs: reproducibility, no hard-coded params, SQL/pandas join correctness, config-sourced parameters, test coverage |
| `clinical-logic-reviewer` | Reviews HER2/HR logic vs ASCO/CAP and Enhertu labels; flags uncited claims; writes verdict in `code-review.md` + `clinical-review.md` |
| `test-writer` | Writes pytest file for a module; uses `write-test` skill; never mocks DuckDB — uses in-memory instances |
| `reviewer-simulator` | Plays Brandon Nathasingh: reads deck + audit pack; fires PROJECT_BRIEF §9 follow-up questions; writes D8 Q&A prep in `../_prep/` |

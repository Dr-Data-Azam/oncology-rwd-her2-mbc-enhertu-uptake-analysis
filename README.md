# her2-mbc-feasibility

Analysis of HER2 distribution and Enhertu uptake in a synthetic metastatic breast cancer
cohort (150 patients, 10 provider organizations). Answers two client questions:

1. **Feasibility:** What is the HER2 distribution (positive / low / ultralow / 0-null /
   unknown) at metastatic diagnosis, and how confident can we be?
2. **Commercial:** How does Enhertu uptake compare with competitors across HER2-defined
   subindications? Is this data asset fit for purpose?

Built as a ConcertAI technical assessment (Associate Director, Solutions Consulting).
**All data are synthetic and for assessment purposes only.**

---

## Quickstart

```bash
# 1. Install dependencies (Python 3.12+, uv required)
uv sync

# 2. Run the full pipeline
uv run python -m her2rwd.pipeline

# 3. View results
open reports/analysis_notebook.html   # or start reports/HER2_mBC_Enhertu_Assessment.pptx
```

The pipeline reads from `data/raw/`, writes to `outputs/` and `reports/`, and produces
`outputs/run_manifest.json` with input hashes and row counts for every stage.

---

## Repo Tour

| Path | Purpose |
|---|---|
| `data/raw/` | READ-ONLY working copies of the 5 CSVs and data dictionary |
| `src/her2rwd/` | Analysis pipeline package (all logic lives here) |
| `notebooks/analysis.ipynb` | Narrative notebook (imports src/; no logic of its own) |
| `config/analysis_rules.yaml` | Single source of truth for every rule, window, and threshold |
| `sql/` | DuckDB SQL models called by src/ |
| `tests/` | Pytest unit tests (in-memory fixtures; no real data) |
| `outputs/` | Generated tables and figures (git-ignored; rebuilt by pipeline) |
| `reports/` | Generated HTML notebook and .pptx deck (git-ignored; rebuilt by /build-report) |
| `audit/` | Decision log (ADRs), validation report, session log, AI usage statement |
| `docs/` | ARCHITECTURE, DEVELOPMENT_PROCESS, DATA_LINEAGE, DATA_DICTIONARY |
| `specs/` | Spec-driven process trail: one folder per phase, analysis + tech specs |
| `.claude/` | Claude Code setup: settings, commands, skills, agents |
| `CLAUDE.md` | Project constitution: hard rules, conventions, lifecycle |

---

## Where to Find X

| What you want to find | Where to look |
|---|---|
| A specific clinical rule (e.g. HER2 window) | `config/analysis_rules.yaml` → find the key |
| Why that rule was chosen | `audit/DECISION_INDEX.md` → find the ADR → open `audit/decisions/ADR-NNN-*.md` |
| A number on slide 3 | Check the speaker note for the source CSV → `outputs/tables/<table>.csv` |
| Why a patient is in a given HER2 bucket | `outputs/tables/patient_her2.csv` → `rule_applied` + `winning_record_id` columns |
| Why a patient was excluded from the cohort | `outputs/tables/attrition.csv` + `patient_audit.csv` → `exclusion_reason` column |
| A data quality issue | `outputs/dq/dq_log.csv` → filter by table or check_id |
| Which session built what | `audit/SESSION_LOG.md` |

---

## Note on `../external/`

The folder `../external/` (one level up from this repo) contains the original, unmodified
ConcertAI attachment exactly as received:

```
external/
├── candidate_facing_instructions.docx
├── data_dictionary.xlsx
└── synthetic_breast_her2_dataset_csv.zip
```

It is **STRICTLY READ-ONLY**. This repo never writes, edits, or deletes anything there.
`data/raw/` contains byte-identical working copies, verified by SHA-256 hash at every
pipeline run.

---

## Rerunning from Scratch

```bash
uv sync                                         # install deps
uv run python -m her2rwd.pipeline               # run analysis → outputs/
uv run pytest tests/ -v                         # verify tests pass
uv run python -m her2rwd.pipeline --reports     # also build HTML + pptx → reports/
```

To use an alternative rule set (sensitivity analysis):

```bash
uv run python -m her2rwd.pipeline --rules config/alt_narrow_window.yaml
```

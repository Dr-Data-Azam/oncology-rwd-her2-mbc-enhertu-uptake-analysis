# Architecture

> Stub — to be completed in Phase 01 (ingest-and-dq).

---

## Pipeline Overview

```
data/raw/                     ← READ-ONLY: 5 CSVs + data_dictionary.xlsx
     │
     ▼
data_loader.py  SHA-256 integrity check + load into DuckDB
     │
     ▼
data_quality.py DQ checks → outputs/dq/dq_log.csv
     │
     ▼
cohort.py       Eligibility + index date + de novo/recurrent
                → outputs/tables/cohort.csv
                → outputs/tables/attrition.csv
     │
     ├── her2.py             HER2 variant mapping + window + tie-break
     │                       → outputs/tables/patient_her2.csv
     │
     └── hormone_receptor.py HR status from ER/PR %
                             → outputs/tables/patient_hr.csv
     │
     ▼
treatment.py    Regimen grouping + line-of-therapy
                → outputs/tables/patient_lines.csv
     │
     ├── q1_distribution.py   → outputs/tables/q1_*.csv
     ├── q2_uptake.py         → outputs/tables/q2_*.csv
     └── sensitivity.py       → outputs/tables/sensitivity_*.csv
     │
     ▼
validation.py   Invariant checks → audit/validation_report.md
     │
     ▼
report.py       Notebook → HTML; outputs → .pptx → reports/
     │
     ▼
pipeline.py     Orchestration → outputs/run_manifest.json
```

---

## Module Map

| Module | Responsibility | Key ADRs |
|---|---|---|
| `data_loader.py` | Load raw CSVs into DuckDB; SHA-256 integrity check | ADR-001 |
| `data_quality.py` | Data-quality checks → outputs/dq/dq_log.csv | ADR-003 |
| `cohort.py` | Eligibility, metastatic index date, de novo/recurrent, attrition | ADR-002, ADR-004, ADR-005 |
| `her2.py` | HER2 variant → category, biomarker window, tie-break, audit columns | ADR-006, ADR-007, ADR-008 |
| `hormone_receptor.py` | ER/PR % → HR status, ER-low flag | ADR-009 |
| `treatment.py` | Regimen grouping, line-of-therapy approximation | ADR-010 |
| `q1_distribution.py` | HER2 distribution, strata, literature benchmarks | ADR-012, ADR-014 |
| `q2_uptake.py` | Subindications, Enhertu uptake, competitors, discordance | ADR-011, ADR-013 |
| `sensitivity.py` | Re-runs pipeline under alternative rule sets | ADR-006, ADR-007 |
| `statistics.py` | Wilson 95% CI, small-cell (n<11) flagging | ADR-012 |
| `validation.py` | Invariant checks → audit/validation_report.md | — |
| `report.py` | Notebook → HTML (nbconvert); outputs → .pptx (python-pptx) | — |
| `pipeline.py` | End-to-end orchestration → outputs/run_manifest.json | ADR-001 |

---

## Design Principles

1. **Config-driven rules.** Every threshold, window, code list, and tie-break order lives in
   `config/analysis_rules.yaml`. Changing a rule means editing config, not code. Each key
   cites its ADR.

2. **Layered tidy tables.** Each pipeline stage produces one clean, wide table (one row per
   patient or per patient-line). Later stages join these tables; they never re-derive upstream
   logic.

3. **Audit columns.** Every patient-level table includes columns that explain why the patient
   ended up in a given bucket (`rule_applied`, `winning_record_id`, `exclusion_reason`).

4. **No logic in the notebook.** `notebooks/analysis.ipynb` imports from `src/her2rwd/` and
   calls the pipeline. All analytical logic lives in Python modules that are unit-tested.

5. **Generated outputs, never hand-edited.** Nothing in `outputs/` or `reports/` is modified
   manually. All numbers flow from raw data → pipeline → tables → deck.

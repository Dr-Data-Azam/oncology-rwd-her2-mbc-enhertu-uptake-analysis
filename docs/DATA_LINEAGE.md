# Data Lineage

> Stub — rows are added as phases are completed.
> Each row answers: "Where did this output come from?"

---

## Lineage Table

| Output file | Produced by | Config keys used | ADRs | Raw source tables |
|---|---|---|---|---|
| `outputs/dq/dq_log.csv` | `data_quality.py` | `dq.*` | ADR-003 | patient, diagnosis, staging, biomarker, medication |
| `outputs/tables/cohort.csv` | `cohort.py` | `eligibility.*`, `index_date.*`, `cohort.*` | ADR-002, ADR-004, ADR-005 | patient, diagnosis, staging |
| `outputs/tables/attrition.csv` | `cohort.py` | `eligibility.*` | ADR-002 | patient, diagnosis, staging |
| `outputs/tables/patient_her2.csv` | `her2.py` | `her2.*` | ADR-006, ADR-007, ADR-008 | biomarker |
| `outputs/tables/patient_hr.csv` | `hormone_receptor.py` | `hr.*` | ADR-009 | biomarker |
| `outputs/tables/patient_lines.csv` | `treatment.py` | `treatment.*` | ADR-010 | medication |
| `outputs/tables/q1_overall.csv` | `q1_distribution.py` | `stats.*`, `benchmarks.*` | ADR-012, ADR-014 | patient_her2, patient_hr, cohort |
| `outputs/tables/q1_by_*.csv` | `q1_distribution.py` | `stats.*` | ADR-012 | patient_her2, patient_hr, cohort |
| `outputs/tables/q1_unclassifiable.csv` | `q1_distribution.py` | — | — | patient_her2 |
| `outputs/tables/q2_subindication_summary.csv` | `q2_uptake.py` | `subindications.*`, `stats.*` | ADR-011, ADR-012 | patient_her2, patient_hr, patient_lines |
| `outputs/tables/q2_enhertu_timing.csv` | `q2_uptake.py` | `subindications.*` | ADR-011 | patient_lines, cohort |
| `outputs/tables/q2_competitors.csv` | `q2_uptake.py` | `subindications.*` | ADR-011 | patient_lines |
| `outputs/tables/q2_discordance.csv` | `q2_uptake.py` | `discordance.*` | ADR-013 | patient_her2, patient_hr, patient_lines |
| `outputs/tables/sensitivity_*.csv` | `sensitivity.py` | alt config overrides | ADR-006, ADR-007 | biomarker, cohort |
| `outputs/run_manifest.json` | `pipeline.py` | all | all | all |
| `audit/validation_report.md` | `validation.py` | — | — | all outputs |
| `reports/analysis_notebook.html` | `report.py` (nbconvert) | — | — | notebooks/analysis.ipynb |
| `reports/HER2_mBC_Enhertu_Analysis.pptx` | `report.py` (python-pptx) | — | — | all q1/q2 outputs |

---

## How to trace a number from a slide back to a raw row

1. Note the table name from the deck (each number cites its source CSV in deck speaker notes).
2. Open `outputs/tables/<table>.csv` — find the row.
3. For patient-level rows: check `rule_applied` and `winning_record_id` columns.
4. For aggregate rows: the `winning_record_id` is per-patient; trace through `patient_her2.csv`.
5. Check `config/analysis_rules.yaml` for the rule that produced that classification.
6. Check `audit/DECISION_INDEX.md` for the ADR that governs that config key.

# Notebook / HTML Blueprint (`reports/analysis_notebook.html`)

The deck shows **what** was found. The HTML proves **how**, as the "show your work" layer. The reviewer uses it to check reproducibility and rigour, and to prepare questions. The instructions say to focus on "analytical rigor… rather than cosmetic visualization", so every plot must answer a question. None are decorative.

## Principles
- **Narrative first:** each section opens with a question and ends with a 2–3 line "Finding" box, with numbers and n.
- **Logic lives in `src/her2rwd/`.** The notebook calls functions and shows key rule snippets (e.g. the HER2 mapping), not 300-line cells.
- **Every section prints its validation checks** (e.g. "one HER2 category per patient ✅").
- **Static plots (matplotlib), embedded.** The HTML must open offline from an email attachment with no JavaScript dependencies and stay small (< 5 MB).
- The same HER2 colour scheme as the deck. Every plot has a title, axis labels, n, and "synthetic data" noted.
- A table of contents at the top. Export with outputs and without errors. A run timestamp, git commit and input hashes in the header.

## Sections and plots
| # | Section | Tables | Plots (purpose) |
|---|---|---|---|
| 0 | Header: purpose, how to rerun, run manifest, table of contents | manifest | — |
| 1 | Executive summary (mirrors deck slide 1) | scorecard | — |
| 2 | Data overview and profiling | row counts, grain, curation share per table | **Record timeline per table** (dates by year, highlights future/pre-birth dates) · **completeness heatmap** (field × table, EHR vs curated) |
| 3 | Data quality checks | full DQ log (the 15 checks) | bar chart of patients affected per check |
| 4 | Cohort construction | attrition table | **Attrition flow chart** · **gap from primary to metastatic diagnosis** histogram (de novo vs recurrent logic) |
| 5 | Index date | source of index date (diagnosis vs stage, curated vs EHR) | **Stage M1 date minus metastatic diagnosis date** histogram (justifies the rule) |
| 6 | HER2 and HR derivation | result × variant cross-tab · mapping table · tie-break examples (PAT_001) | **HER2 test timing relative to the index date** histogram with window bands (**key plot: justifies the window**) · candidate records per patient |
| 7 | Q1: HER2 distribution | overall + 4 stratifications with n, %, CI · literature comparison | **100% stacked bars** by stratum · **observed vs benchmark** dot-and-range plot |
| 8 | Q1: uncertainty and sensitivity | unresolved breakdown · sensitivity table | **Sensitivity dot plot** (category % under each rule set) |
| 9 | Treatment patterns | regimen and line definitions · first-line regimen by subindication | **Swimmer/timeline plot** for ~15 sample patients (index date, HER2 test, regimens, Enhertu) · days from index to 1st treatment |
| 10 | Q2: Enhertu uptake | per-subindication table (n, %, CI, median days, line, before/instead) | **Uptake % with CI** by subindication · **time to 1st Enhertu** (box/strip, or cumulative incidence if justified) · treatment sequence bars |
| 11 | Discordance | patient-level list with reasons | timeline of 2–3 illustrative discordant patients |
| 12 | Fit for purpose + limitations + productionization | scorecard | — |
| 13 | Appendix: assumptions register (rendered from YAML), ADR index, validation report, environment | | |

## Top 5 plots that matter most
1. HER2 test timing vs index date, with window bands (justifies a key decision)
2. 100% stacked HER2 distribution by stratum (answers Q1)
3. Sensitivity dot plot (quantifies uncertainty)
4. Swimmer plot of patient journeys (makes sequencing and discordance tangible)
5. Enhertu uptake with CIs by subindication (answers Q2)

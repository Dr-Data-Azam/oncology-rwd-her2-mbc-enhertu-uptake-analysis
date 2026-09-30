# Decision Index

All architectural and clinical decisions for the her2-mbc-feasibility analysis.
Each ADR records context, options considered, the chosen option, and its rationale.
Status transitions: Proposed → Accepted (after Azam approval) → Superseded (if replaced).

| ADR | Title | Status | Phase | Config key(s) | File |
|---|---|---|---|---|---|
| ADR-001 | Tooling: Python + DuckDB + pandas, config-driven | Accepted | 01 | tooling.engine | [ADR-001](decisions/ADR-001-tooling.md) |
| ADR-002 | Eligibility criteria | Accepted | 02 | eligibility.* | [ADR-002](decisions/ADR-002-eligibility.md) |
| ADR-003 | Handling future-dated, post-death, and pre-birth records | Accepted | 01 | dq.* | [ADR-003](decisions/ADR-003-dq-handling.md) |
| ADR-004 | Metastatic index date definition and source priority | Accepted | 02 | index_date.* | [ADR-004](decisions/ADR-004-index-date.md) |
| ADR-005 | De novo vs recurrent definition | Accepted | 02 | cohort.de_novo_primary_gap_days | [ADR-005](decisions/ADR-005-de-novo-recurrent.md) |
| ADR-006 | HER2 variant → category mapping | Proposed | 03 | her2.variant_to_category.* | [ADR-006](decisions/ADR-006-her2-mapping.md) |
| ADR-007 | HER2 look-up window | Accepted | 03 | her2.window_days.* | [ADR-007](decisions/ADR-007-her2-window.md) |
| ADR-008 | HER2 tie-break hierarchy | Accepted | 03 | her2.tiebreak_order, her2.conflict_resolution | [ADR-008](decisions/ADR-008-her2-tiebreak.md) |
| ADR-009 | HR derivation: percentage beats result text; ≥1% = positive | Accepted | 03 | hr.* | [ADR-009](decisions/ADR-009-hr-derivation.md) |
| ADR-010 | Regimen grouping and line-of-therapy approximation | Proposed | 05 | treatment.* | [ADR-010](decisions/ADR-010-treatment-lines.md) |
| ADR-011 | Subindication framework (required + exploratory groups) | Proposed | 06 | subindications.* | [ADR-011](decisions/ADR-011-subindications.md) |
| ADR-012 | Statistics: Wilson CIs and small-cell flagging | Proposed | 04 | stats.* | [ADR-012](decisions/ADR-012-statistics.md) |
| ADR-013 | Discordance definitions (treatment vs biomarker) | Proposed | 06 | discordance.definitions | [ADR-013](decisions/ADR-013-discordance.md) |
| ADR-014 | Literature benchmarks chosen and cited | Proposed | 04 | benchmarks.* | [ADR-014](decisions/ADR-014-benchmarks.md) |

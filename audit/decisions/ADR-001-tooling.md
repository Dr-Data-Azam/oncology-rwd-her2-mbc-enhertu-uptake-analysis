# ADR-001: Tooling — Python + DuckDB + pandas, config-driven

**Status:** Accepted
**Phase:** 01 (ingest-and-dq)
**Config key:** `tooling.engine`

---

## Context

The assessment requires a reproducible, production-minded pipeline on 150 synthetic patients.
The evaluator will inspect the code for clean separation of logic, testability, and
config-driven parameterization.

## Decision

Use **DuckDB** for all data transformations (joins, filters, aggregations, window functions)
and **pandas** only for output formatting (`.to_csv()`, display in notebook). All rule
parameters live in `config/analysis_rules.yaml`; no values are hard-coded.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Pure pandas | Familiar to most DS | Verbose for joins; harder SQL logic |
| Pure DuckDB SQL | Clean, set-based | Less flexible for Wilson CI math |
| **DuckDB + pandas (chosen)** | SQL for transforms; pandas for output | Two tools to learn |
| PySpark | Scales to large data | Massive overkill for 150 patients |

## Rationale

DuckDB SQL is more readable and auditable for the join-heavy operations in cohort,
biomarker, and treatment logic. pandas handles the final mile (CSV output, statistical
formatting) where DuckDB is verbose. The two-layer notebook architecture
(`src/her2rwd/*.py` = logic, `notebooks/analysis.ipynb` = narrative) makes the
clinical logic independently testable via pytest.

## Consequences

- All DuckDB queries are strings inside Python functions — no separate `.sql` files needed.
- `con.execute(...).df()` converts DuckDB result sets to pandas DataFrames at the boundary.
- Tests use in-memory DuckDB instances (`duckdb.connect()`) — no mocking required.

# code-reviewer

Review the code diff for the current phase against a production-minded checklist.

## Trigger

Called by `/close-phase` after tests and lint pass. Writes verdict to
`specs/<NN>-<slug>/code-review.md`.

## Checklist

### Reproducibility
- [ ] The pipeline runs end-to-end from `uv run python -m her2rwd.pipeline` with no manual steps.
- [ ] All random seeds are fixed (if any randomness is used).
- [ ] `outputs/run_manifest.json` records input hashes, config hash, git commit, and row counts.

### Config-driven rules
- [ ] No numeric threshold, window bound, code list, or tie-break order is hard-coded in Python or SQL.
- [ ] Every rule parameter is in `config/analysis_rules.yaml` and has an ADR comment.
- [ ] The pipeline raises a clear error if any config value is `TBD`.

### SQL/pandas correctness
- [ ] All joins specify the join key explicitly; no implicit index joins.
- [ ] Aggregations include a `GROUP BY` on all non-aggregated columns.
- [ ] Date arithmetic uses consistent types (no silent string/date mixing).
- [ ] No cartesian products (check every `CROSS JOIN` or missing `ON` clause).

### Test coverage
- [ ] Every clinical rule branch in `her2.py`, `hr.py`, and `cohort.py` has at least one test.
- [ ] Tests use in-memory DuckDB; no test reads from `data/raw/`.
- [ ] At least one test covers the unhappy path (missing data, conflict, edge case).

### Audit trail
- [ ] `patient_her2.csv` includes `winning_record_id`, `rule_applied`, and `candidates_considered`.
- [ ] `dq_log.csv` includes a row for every DQ issue handled.
- [ ] `attrition.csv` accounts for every patient excluded and gives a reason.

### Read-only safety
- [ ] No code writes to `../external/` or `data/raw/`.
- [ ] No `git push` or network call anywhere in the pipeline.

## Output format

```markdown
# Code Review: <phase-slug>

Reviewer: code-reviewer agent
Date: YYYY-MM-DD
Verdict: PASS | PASS WITH NOTES | FAIL

## Findings

| # | Severity | File:line | Issue | Recommendation |
|---|---|---|---|---|

## Summary
<one paragraph>
```

A FAIL verdict blocks `/close-phase`. Surface the finding to Azam before proceeding.

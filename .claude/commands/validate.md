# /validate

Run pipeline invariant checks and write the validation report.

## Command

```
uv run python -c "from her2rwd.validate import run_all; run_all()"
```

## What it does

Runs every PASS/FAIL check in `src/her2rwd/validate.py` against the current contents of
`outputs/tables/`. Writes results to `audit/validation_report.md`. Exits with code 1 if
any check fails, which causes `/close-phase` to stop.

## Invariants checked

- Attrition table total = 150 raw patients
- Cohort table: exactly one row per patient_id, no duplicates
- Every `her2_category` value is in the allowed set
- HER2 category counts sum to cohort size
- No `index_date` < `date_of_birth`
- Q1 HER2 proportions sum to 100% (±0.01 tolerance)
- Q2 cohort size = Q1 cohort size
- `run_manifest.json` exists and contains a git commit hash and input hashes

## Notes

- Run this independently to check outputs without running the full pipeline.
- Any FAIL is a blocking error. Do not proceed to `/close-phase` with failing invariants.

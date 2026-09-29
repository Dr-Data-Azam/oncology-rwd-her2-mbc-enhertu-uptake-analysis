# /close-phase

Gate-check, audit, and commit the completed phase. No push — local only.

## Steps (run in order; stop on any failure)

1. **`/test`** — `uv run pytest tests/ -v --cov=src/her2rwd`. All tests must pass.

2. **`/lint`** — `uv run ruff check src/ tests/ && uv run black --check src/ tests/`.
   Zero lint errors required.

3. **`/run-pipeline`** — `uv run python -m her2rwd.pipeline`. Pipeline must complete
   without errors. Prints attrition and headline counts.

4. **`/validate`** — Run invariants. All checks must be PASS. Writes
   `audit/validation_report.md`.

5. **clinical-logic-reviewer agent** — Review HER2/HR logic against ASCO/CAP and Enhertu
   labels. Verdict is written to `specs/<NN>-<slug>/clinical-review.md`.

6. **code-reviewer agent** — Review the diff for this phase: reproducibility, config-driven
   params, join correctness, test coverage. Verdict written to
   `specs/<NN>-<slug>/code-review.md`.

7. **Write implementation-summary** — Fill `specs/<NN>-<slug>/implementation-summary.md`:
   what was built, which ADRs were written, what changed from the analysis spec, and the
   validation report summary.

8. **ADR check** — Verify that every new rule parameter introduced in this phase has a
   corresponding ADR in `audit/decisions/` and is linked from `config/analysis_rules.yaml`.
   Stop if any rule is un-documented.

9. **Append SESSION_LOG row** — Add one row to `audit/SESSION_LOG.md`:
   | session name | date | phase/spec | outcome | ADRs added | commit |
   Leave the commit column as `TBD`; it will be updated after step 11.

10. **Local commit** — `git add -A && git commit -m "<msg>"`.
    Conventional commit format: `feat(<phase>): <summary>`.

11. **Merge into main** — `git checkout main && git merge phase/<slug> --no-ff`.
    No push.

12. **Update SESSION_LOG commit** — Edit the `TBD` in the commit column with the actual
    short hash from `git log --oneline -1`.

## Usage

```
/close-phase "feat(01-ingest-and-dq): load raw data, DQ checks, run manifest"
```

## Notes

- No step can be skipped.
- If any agent raises a blocking concern, stop and surface it to Azam before committing.
- The commit must be on the `phase/<slug>` branch before merging; never commit directly
  to `main`.

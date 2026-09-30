# /close-phase

Finish a phase: test, lint, then commit. Local only — no push, no branches.

## Steps

1. **`/test`** — `uv run pytest tests/ -v --cov=src/her2rwd`.
   All tests must pass before continuing.

2. **`/lint`** — `uv run ruff check src/ tests/ && uv run black --check src/ tests/`.
   Zero errors required. Run `/fix` first if needed.

3. **ADR check** — confirm every new config key introduced in this phase has a
   corresponding ADR in `audit/decisions/` and a non-`TBD` value in
   `config/analysis_rules.yaml`. One sentence per new rule is enough.

4. **Append SESSION_LOG row** — add one row to `audit/SESSION_LOG.md`:
   `| session | date | phase | outcome | ADRs added | commit |`
   Leave commit as `TBD`; update after step 5.

5. **Commit** — `git add <specific files> && git commit -m "feat(<phase>): <summary>"`.
   Update the SESSION_LOG commit column with the short hash from `git log --oneline -1`.

## Usage

```
/close-phase "feat(01-ingest-and-dq): load raw data, DQ checks, run manifest"
```

## Notes

- Commit directly to `main` — no phase branches.
- Use `clinical-logic-reviewer` agent only on Phase 03 (biomarker derivation).
- Use `code-reviewer` agent only on Phase 06 (Q2 uptake).
- Run `/run-pipeline` manually any time to check outputs; it is not a gate here.

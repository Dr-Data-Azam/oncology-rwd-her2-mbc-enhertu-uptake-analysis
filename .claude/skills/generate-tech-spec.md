# generate-tech-spec

Turn an approved `analysis-spec.md` into a detailed `tech-spec.md` for the phase.

## Inputs

- The approved `analysis-spec.md` for the current phase
- `CLAUDE.md` (conventions, permission boundaries)
- The current state of `src/her2rwd/` (which modules exist, which are stubs)
- `config/analysis_rules.yaml` (which keys are still TBD)

## Output format (tech-spec.md)

```markdown
# Tech Spec: <phase-slug>

| Field | Value |
|---|---|
| Phase | NN-<slug> |
| Date | YYYY-MM-DD |
| Status | Draft → Approved |
| Blocks | list of tasks that must complete first |

## Architecture changes
<table: file → what changes → why>

## SQL models (sql/ files to create or modify)
<list each .sql file with its purpose>

## Python changes (src/her2rwd/ files)
<for each module: function signatures (no implementation), inputs, outputs, ADR reference>

## Config changes (config/analysis_rules.yaml)
<list every key that moves from TBD to a real value, and the ADR that governs it>

## Tests to write
<table: test file → test name → what it exercises → fixture needed>

## ADRs to write before implementation
<list each ADR number, title, and the decision it records>

## Open questions
<anything that must be resolved before implementation begins>
```

## Notes

- The tech spec must be in Plan Mode (no code written until approved).
- Function signatures go in the tech spec; implementations go in the code.
- Every new rule parameter must have an ADR reference in the tech spec before implementation.

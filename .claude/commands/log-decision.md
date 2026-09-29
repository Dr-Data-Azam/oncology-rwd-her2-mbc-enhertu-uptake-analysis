# /log-decision

Create a new ADR, populate it from the latest pipeline run, and register it.

## Steps

1. Determine the next ADR number from `audit/DECISION_INDEX.md`.
2. Copy `audit/decisions/ADR-TEMPLATE.md` to
   `audit/decisions/ADR-<NNN>-<kebab-slug>.md`.
3. Fill every section using the `decision-log` skill:
   - Context: the clinical and data problem this decision addresses
   - Options considered: at least two; include data impact from the latest run
   - Decision: one sentence naming the chosen option
   - Rationale: clinical + data reasons; cite guideline or paper (VERIFY if uncertain)
   - Evidence: numbers from the profiling or the pipeline run
   - Consequences: what it biases and in which direction
   - Sensitivity: which alternative is tested in a sensitivity run, and where to find the result
   - Reviewer notes: filled later by clinical-logic-reviewer
4. Add a row to `audit/DECISION_INDEX.md` with status "Accepted".
5. Find the corresponding key(s) in `config/analysis_rules.yaml` and add a comment
   `# ADR-<NNN>` next to each relevant key.
6. Show Azam the completed ADR for approval.

## Usage

```
/log-decision "HER2 look-up window around the metastatic index date"
/log-decision "HR derivation: percentage beats result text"
```

## Notes

- Do not fill in `config/analysis_rules.yaml` values until Azam approves the ADR.
- The ADR number in the filename must match the DECISION_INDEX row.
- Use `VERIFY` on any clinical statement that needs a citation.

# decision-log

Fill an ADR from the template, using evidence from the latest pipeline run.

## Inputs needed before calling this skill

- The decision title (e.g. "HER2 look-up window around the metastatic index date")
- The relevant config key(s) from `config/analysis_rules.yaml`
- Numbers from the latest pipeline run or from the data profiling in PROJECT_BRIEF §6
- The clinical source or guideline, if applicable

## Steps

1. Read `audit/decisions/ADR-TEMPLATE.md`.
2. Determine the next ADR number from `audit/DECISION_INDEX.md`.
3. Fill every section:
   - **Context:** 2–3 lines on the clinical and data problem.
   - **Options considered:** at least two rows in the table, each with Pros, Cons, and
     Data impact (actual numbers from the pipeline or profiling).
   - **Decision:** one sentence.
   - **Rationale:** clinical + data reasons. Cite guideline or paper. Mark `VERIFY` if uncertain.
   - **Evidence:** the specific numbers that drove the decision.
   - **Consequences:** what the choice biases, and in which direction.
   - **Sensitivity:** which alternative is tested in a sensitivity run, and where to find the result.
   - **Reviewer notes:** leave as "Pending clinical-logic-reviewer".
4. Write the file to `audit/decisions/ADR-<NNN>-<kebab-slug>.md`.
5. Add a row to `audit/DECISION_INDEX.md`.
6. Add `# ADR-<NNN>` comment to the relevant key(s) in `config/analysis_rules.yaml`.

## Notes

- One ADR per decision, not per phase.
- Use the exact template structure so the clinical-logic-reviewer agent can parse it.
- Never fill in `config/analysis_rules.yaml` values until the ADR is approved by Azam.

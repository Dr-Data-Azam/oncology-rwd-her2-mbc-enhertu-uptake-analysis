# generate-analysis-spec

Interview Azam and produce a complete `analysis-spec.md` for the current phase.

## The five questions (ask one at a time; wait for each answer)

1. **Client question:** What business or feasibility question does this phase answer?
   What does "done" look like from the client's perspective?

2. **Definitions:** What exactly are we classifying, counting, or computing?
   What is the clinical source — which guideline, label, or study definition applies?
   List every key term that needs a precise definition before code is written.

3. **Outputs:** Which tables, figures, and audit columns must exist when the phase is done?
   Name them as they will appear in `outputs/tables/` or `outputs/figures/`.

4. **Alternatives:** What other reasonable definitions or approaches exist?
   Which one becomes the sensitivity analysis? Why is the primary choice preferred?

5. **Constraints and risks:** What must not change (hard constraints)?
   Which DQ issues from `outputs/dq/dq_log.csv` are most likely to bite here?
   What is still unresolved and needs an ADR before code is written?

## Output format (analysis-spec.md)

```markdown
# Analysis Spec: <phase-slug>

| Field | Value |
|---|---|
| Phase | NN-<slug> |
| Date | YYYY-MM-DD |
| Status | Draft → Approved |
| ADRs needed | ADR-XXX, ADR-YYY |

## Client question
<answer to Q1>

## Definitions
<answer to Q2>

## Outputs
<answer to Q3 — table listing each output file and its columns>

## Alternatives and sensitivity analysis
<answer to Q4>

## Constraints and risks
<answer to Q5>
```

## Notes

- Do not write any code before the analysis spec is approved.
- If an answer requires a clinical citation that is uncertain, mark it `VERIFY`.
- The spec is the contract between Azam and Claude Code for this phase.

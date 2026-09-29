# reviewer-simulator

Simulate Brandon Nathasingh reviewing the deck and audit pack.

## Background

Brandon Nathasingh is the current Associate Director at ConcertAI. He is a computational
biologist with a background in survival analysis, causal inference, and oncology RWE, and was
previously a Strategic Data Scientist at ConcertAI. He sent this assessment. He will review
for ~15 minutes, then spend ~15 minutes on Q&A.

## Trigger

Called during Phase 08 (review prep). Reads the completed deck and audit pack, fires tough
follow-up questions, and writes the D8 Q&A prep document to `../_prep/qa_prep.md`.

## Inputs

- `reports/HER2_mBC_Enhertu_Assessment.pptx` (or the HTML notebook as a proxy)
- `audit/DECISION_INDEX.md` + the ADR files
- `outputs/tables/attrition.csv`, `patient_her2.csv`, `q1_overall.csv`,
  `q2_subindication_summary.csv`, `q2_discordance.csv`

## Questions to ask (from PROJECT_BRIEF §9)

1. Why this index date and not the staging M1 date alone? What changes if only curated
   records are used to define the index date?
2. Why +180 days post-index for the biomarker window? Isn't that a treatment-influenced
   window? What does the −365/+90 sensitivity show?
3. How do you split IHC 0 when there is no staining detail? What share of HER2-0 is
   truly unresolvable?
4. EHR vs curated concordance: how often do they disagree on HER2 category, and which wins?
5. How would you productionize this: versioned rules engine, dbt/SQL models, unit tests per
   rule, DQ monitors, evidence-level score per patient?
6. Commercial framing: n is small and the intervals are wide. How fragile are these
   percentages? What sample size would you need for a reliable estimate?
7. Line-of-therapy approximation: you have no end dates. How did you define a new line?
   How does the 28-day window affect the Enhertu line-number distribution?
8. Discordant cases: walk me through one Enhertu-in-HER2-0 case. What happened there?
9. Fit-for-purpose verdict: what would it take to make this asset definitively fit for
   the HER2-ultralow subindication? What data would you go back and collect?

## Output format (`../_prep/qa_prep.md`)

For each question:
```markdown
## Q: <question text>

**30-second answer:**
<the answer Azam should give, in 2–4 sentences>

**If they push further:**
<one additional point or caveat to add>

**Evidence to point to:**
<which slide, table, or ADR has the supporting data>
```

## Notes

- `../_prep/` is outside the repo and never committed or sent to Brandon.
- The reviewer-simulator plays Brandon honestly — it should surface real weaknesses, not
  just softballs. That is the point of the exercise.

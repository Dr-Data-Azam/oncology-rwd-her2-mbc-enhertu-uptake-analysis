# /create-spec

Create a new phase spec folder and bootstrap the analysis spec via structured interview.

## Steps

1. **Pre-flight:** verify the working tree is clean (`git status --porcelain`). If there are
   uncommitted changes, stop and tell Azam to commit or stash them first.

2. **Determine the next phase number** by reading `specs/` and finding the highest `NN` prefix
   already present. The new phase number is NN+1, zero-padded to two digits.

3. **Create a local branch:** `git checkout -b phase/<slug>`

4. **Create the spec folder:** `specs/<NN>-<slug>/` with empty placeholder files:
   - `analysis-spec.md` (to be filled in step 5)
   - `tech-spec.md` (filled in Plan Mode, after analysis-spec is approved)
   - `code-review.md` (filled by code-reviewer agent at close)
   - `clinical-review.md` (filled by clinical-logic-reviewer agent at close)
   - `implementation-summary.md` (filled by /close-phase)

5. **Interview Azam** using the five analysis-spec questions (see `generate-analysis-spec` skill).
   Ask the questions one at a time, wait for answers, then write the completed `analysis-spec.md`.

6. **Show Azam the completed analysis-spec** and ask for approval before stopping.

## Usage

```
/create-spec 01-ingest-and-dq
/create-spec 03-biomarker-derivation
```

## Notes

- Never skip the clean-tree check.
- The `analysis-spec.md` must be approved by Azam before Plan Mode begins.
- Phase numbers are sequential; do not reuse or skip numbers.

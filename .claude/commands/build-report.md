# /build-report

Build all submission artifacts and populate `../_submission/`.

## Steps

1. **Execute and export the notebook:**
   ```
   uv run jupyter nbconvert --to html --execute notebooks/analysis.ipynb \
     --output reports/analysis_notebook.html
   ```

2. **Build the slide deck** using the `deck-builder` skill:
   - Reads numbers from `outputs/tables/*.csv`
   - Produces `reports/HER2_mBC_Enhertu_Assessment.pptx`
   - Attempts PDF export via LibreOffice headless; logs a warning if unavailable

3. **Render the assumptions register** from `config/analysis_rules.yaml` into
   `audit/assumptions_register.md` (one row per key: config key → value → ADR).

4. **Run `/validate`** one final time to confirm all invariants pass.

5. **Populate `../_submission/`:**
   ```
   ../_submission/
   ├── HER2_mBC_Enhertu_Assessment.pptx
   ├── HER2_mBC_Enhertu_Assessment.pdf   (if available)
   ├── analysis_notebook.html
   └── her2-mbc-feasibility.zip          (repo, excluding .git/, data/interim/, .venv/, caches)
   ```

6. **Print a checklist** of every file in `../_submission/` with its size.

## Notes

- This command must be run from the `main` branch after `/close-phase` for Phase 07.
- Never include `data/raw/`, `data/interim/`, `.venv/`, or `outputs/` in the zip
  (they are git-ignored or too large).
- Azam reviews the submission folder before emailing Brandon.

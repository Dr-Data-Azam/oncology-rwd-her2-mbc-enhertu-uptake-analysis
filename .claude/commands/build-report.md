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

3. **Run `/validate`** one final time to confirm all invariants pass.

4. **Copy artifacts to `../_submission/`** (individual files, not a zip):
   ```
   ../_submission/
   ├── analysis_notebook.html
   ├── HER2_mBC_Enhertu_Assessment.pptx
   ├── HER2_mBC_Enhertu_Assessment.pdf   (if available)
   └── her2-mbc-feasibility.zip          (source code + outputs + audit pack)
   ```

   The zip includes: `src/`, `tests/`, `config/`, `notebooks/`, `outputs/`,
   `audit/`, `docs/`, `README.md`, `pyproject.toml`.
   The zip excludes: `data/raw/`, `data/interim/`, `.venv/`, `.git/`, caches.

5. **Print a checklist** of every file in `../_submission/` with its size.

## What Brandon receives (email attachments)

- `analysis_notebook.html` — the rendered ipynb output
- `HER2_mBC_Enhertu_Assessment.pptx` — slide deck
- `HER2_mBC_Enhertu_Assessment.pdf` — PDF of deck
- `her2-mbc-feasibility.zip` — reproducible source code + all outputs

## Notes

- `../_prep/` (talk track, Q&A prep) is internal only — never sent to Brandon.
- Azam reviews `../_submission/` before emailing.

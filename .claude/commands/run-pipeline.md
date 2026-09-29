# /run-pipeline

Run the full analysis pipeline end to end.

## Command

```
uv run python -m her2rwd.pipeline [--rules config/alt.yaml] [--reports]
```

- `--rules <path>`: use an alternative rules YAML instead of `config/analysis_rules.yaml`
  (for sensitivity analyses).
- `--reports`: also run `report.py` to export the notebook to HTML and build the pptx.
  Omit this flag during development to skip the slow report step.

## What it does

Runs all pipeline stages in order (see `pipeline.py` docstring), writes all output tables,
updates `outputs/run_manifest.json`, and prints a summary:

```
Attrition:
  150  raw patients
  128  with breast cancer code (C50.x)
  ...
  N    final analytic cohort

HER2 distribution (primary window):
  HER2+       n=X  (XX.X%)
  HER2-low    n=X  (XX.X%)
  ...
```

## Notes

- `outputs/` must be writable. The pipeline never writes to `data/raw/` or `../external/`.
- If `config/analysis_rules.yaml` contains any `TBD` values the pipeline raises a
  `ValueError` and prints which keys need to be filled.
- Run this after every significant code change to confirm the pipeline still completes.

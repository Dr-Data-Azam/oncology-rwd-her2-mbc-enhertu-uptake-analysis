# /test

Run the full test suite with coverage.

## Command

```
uv run pytest tests/ -v --cov=src/her2rwd --cov-report=term-missing
```

## Notes

- All tests must pass before `/close-phase`.
- Coverage target: every clinical rule branch in `her2.py`, `hr.py`, and `cohort.py`
  must be exercised by at least one test.
- Tests use in-memory DuckDB instances and tiny hand-made patient fixtures in
  `tests/fixtures/`. Do not use real `data/raw/` files in tests.

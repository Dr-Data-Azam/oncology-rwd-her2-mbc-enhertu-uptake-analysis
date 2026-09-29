# test-writer

Write a complete pytest file for a module, given its tech spec.

## Trigger

Called during the build phase when a new module is ready for tests. Uses the `write-test`
skill to construct each test case. Output goes to `tests/test_<module>.py`.

## Inputs

- The approved `tech-spec.md` for the current phase (the "Tests to write" section)
- The module's docstring (specifying inputs, outputs, and ADR references)
- Any existing fixtures in `tests/fixtures/`

## Approach

1. Read the "Tests to write" table from the tech spec.
2. For each row, call `write-test` to produce a parametrized test or a focused single test.
3. Consolidate into one `tests/test_<module>.py` file.
4. Include a module-level docstring explaining what is tested and which ADRs are covered.
5. All fixtures are inline DataFrames or in-memory DuckDB tables — never `data/raw/` files.
6. Mark any test that depends on a `TBD` config value with
   `@pytest.mark.skip(reason="ADR pending: <key>")`.

## Coverage targets

- `her2.py`: one parametrized test covering every variant → category branch (≥9 cases).
- `hr.py`: pct-beats-result conflict, ER-low flag, HR+ = ER+ OR PR+.
- `cohort.py`: eligibility exclusions (no C50, pediatric DOB, orphan, future index date),
  de novo vs recurrent logic.
- `treatment.py`: regimen grouping boundary (27 days = same line, 29 days = new line).
- `stats.py`: Wilson CI for edge cases (n=0, n=total, small n).

## Notes

- Tests must be runnable with `uv run pytest tests/test_<module>.py -v` immediately after
  writing, even if the functions they test are still stubs.
- Use `pytest.raises` for error cases (e.g. TBD config value, mismatched hash).

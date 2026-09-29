# write-test

Write table-driven pytest tests for a clinical rule module.

## Approach

1. **One tiny fixture per decision branch.** Each test exercises exactly one rule path
   (e.g. "IHC 1+ maps to HER2-low", "curated beats EHR when both are present"). Fixtures
   are hand-crafted DataFrames or DuckDB in-memory tables — never loaded from `data/raw/`.

2. **Table-driven where multiple inputs share the same assertion logic.** Use
   `@pytest.mark.parametrize` to cover all variant → category mappings in one test function.

3. **Never mock DuckDB.** Use `duckdb.connect(':memory:')` and `CREATE TABLE AS SELECT`.
   This tests the actual SQL logic, not a mock.

4. **Assert on audit columns too.** For HER2 and HR modules, assert that the `rule_applied`
   and `winning_record_id` columns are populated correctly — not just the final category.

5. **One file per module.** Place tests in `tests/test_<module>.py`. Add fixtures to
   `tests/fixtures/` if they are reused across test files.

## Test file template

```python
"""Tests for <module>.py — <module responsibility in one line>."""
import pytest
import duckdb
import pandas as pd
from her2rwd.<module> import <function>


@pytest.fixture
def db():
    con = duckdb.connect(":memory:")
    # minimal schema setup
    return con


@pytest.mark.parametrize("variant,result,curation,expected_category", [
    ("IHC 3+",               "Positive",  1, "HER2-positive"),
    ("IHC 2+; ISH amplified","Positive",  0, "HER2-positive"),
    ("IHC 1+",               "Negative",  1, "HER2-low"),
    # ... all branches
])
def test_her2_variant_mapping(db, variant, result, curation, expected_category):
    # insert one biomarker row into db
    # call the function
    # assert category == expected_category
    pass
```

## Notes

- Keep fixtures tiny: 1–5 rows is almost always enough.
- The test should break if the rule changes; that is the point.
- Mark any test that depends on a `TBD` config value with `@pytest.mark.skip(reason="ADR pending")`.

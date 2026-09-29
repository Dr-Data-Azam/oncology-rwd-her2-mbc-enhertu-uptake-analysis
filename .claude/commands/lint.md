# /lint

Check code style without modifying files.

## Command

```
uv run ruff check src/ tests/ && uv run black --check src/ tests/
```

## Notes

- Run before `/close-phase` to confirm the working tree is clean.
- Zero errors required. Use `/fix` to auto-apply corrections.

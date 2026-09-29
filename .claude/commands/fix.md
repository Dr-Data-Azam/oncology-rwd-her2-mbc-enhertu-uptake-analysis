# /fix

Auto-apply ruff and black fixes to src/ and tests/.

## Command

```
uv run ruff check --fix src/ tests/ && uv run black src/ tests/
```

## Notes

- Run after writing new code to clean up formatting before committing.
- Always run `/lint` afterwards to confirm zero remaining errors.
- The black/ruff PostToolUse hook in `.claude/settings.json` runs automatically on
  each file edit, so `/fix` is typically only needed for a bulk cleanup.

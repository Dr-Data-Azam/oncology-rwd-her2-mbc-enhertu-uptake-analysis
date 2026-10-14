# AI Usage Statement

This project used **Claude Code** (model: claude-sonnet-4-6, Anthropic) as an AI pair-programmer
throughout the analysis.

## What Claude Code did

- Wrote boilerplate Python, SQL, and Markdown scaffolding under Azam's direction.
- Suggested clinical logic patterns for HER2 and HR classification.
- Drafted ADR templates and filled initial evidence sections from data profiling.
- Performed code reviews, lint checks, and test generation.
- Simulated reviewer questions (reviewer-simulator agent) to prepare the talk track.

## What Azam did

- Wrote and approved every analysis spec and tech spec before any code was built.
- Made every analytical decision (index date, HER2 window, tie-break rules, etc.).
- Validated all clinical logic against ASCO/CAP guidelines and Enhertu labels.
- Read and approved every ADR before the corresponding config values were set.
- Reviewed all pipeline outputs and confirmed the numbers before they appeared in the deck.
- Is solely responsible for all conclusions in the deliverables.

## Why this matters

The analysis was **AI-assisted, human-directed, and human-validated**. The code reflects
Azam's analytical judgment; Claude Code accelerated the implementation. This distinction is
important for reproducibility and accountability: any error in the logic is traceable to a
human decision documented in an ADR.

---

_Last updated: 2026-09-29 (Phase 00 scaffold)_

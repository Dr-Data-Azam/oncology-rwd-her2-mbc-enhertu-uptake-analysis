# Development Process

> Stub — to be completed as phases progress.

---

## Spec-Driven Lifecycle

Every phase of analysis goes through a fixed lifecycle before any code is written or committed:

```
/create-spec <slug>
      │
      ▼ (Azam approves)
 analysis-spec.md   ← client question, definitions, outputs, alternatives, constraints
      │
      ▼ (Plan Mode — Azam approves)
  tech-spec.md      ← architecture changes, function signatures, tests, ADRs to write
      │
      ▼ (Azam reads and approves new ADRs)
   BUILD
      │  - write code (modules, SQL, tests)
      │  - /log-decision for each new rule → fills config values
      ▼
 /test  /lint
      │
      ▼
 clinical-logic-reviewer agent   →  specs/<NN>/clinical-review.md
 code-reviewer agent             →  specs/<NN>/code-review.md
      │
      ▼
 /close-phase
      │  - run-pipeline → validate
      │  - implementation-summary
      │  - ADR completeness check
      │  - append SESSION_LOG row
      │  - local commit → merge main
```

---

## Phase Gates

| Gate | Condition |
|---|---|
| analysis-spec → tech-spec | Azam approves analysis-spec.md |
| tech-spec → build | Azam approves tech-spec.md AND reads all new ADRs |
| build → close | All tests pass, lint clean, pipeline runs, all invariants PASS, both agents pass |

---

## Commands, Skills, and Agents Used

See `CLAUDE.md` for the full tables.

---

## AI-Assisted, Human-Directed, Human-Validated

This project was built with Claude Code as an AI pair-programmer. Azam wrote and approved every
spec, made every analytical decision, read every ADR, and validated every output. See
`audit/AI_USAGE.md` for the full statement.

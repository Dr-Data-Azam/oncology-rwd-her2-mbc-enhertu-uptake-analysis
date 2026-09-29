⛔ HARD RULES (above everything else)
1. ../external/ is STRICTLY READ-ONLY. It is the original ConcertAI attachment. Never write,
   edit, rename, move, delete, unzip into, or create files inside it, and never run a command
   whose output could land there. You may only read it to verify input hashes.
2. data/raw/ is also read-only (byte-identical working copies of the originals).
3. Local git only. No remote, no push.
Put rules 1 to 3 at the top of CLAUDE.md, and add deny rules in .claude/settings.json that
block Edit and Write on ../external/** and data/raw/**.

CONTEXT
- Repo root = this folder (her2-mbc-feasibility/). Workspace layout:
    ConcertAI_Assesment/
    ├── external/              original attachment (READ-ONLY)
    ├── her2-mbc-feasibility/  ← you are here (repo root)
    ├── _submission/           outbox, built later by /build-report
    └── _prep/                 my private talk track and Q&A (never touch unless asked)
- This is a technical assessment for ConcertAI (Associate Director, Solutions Consulting).
  Results are due Wed Sep 30 evening ET; the review with Brandon Nathasingh is Thu Oct 1, 3 PM ET.
  The repo organization, documentation and audit trail are graded alongside the analysis.

READ FIRST, IN THIS ORDER
0. specs/00-engagement/README.md                          (index of everything)
1. specs/00-engagement/source/candidate_facing_instructions.md  (official task; the .docx wins if they conflict)
2. specs/00-engagement/PROJECT_BRIEF_for_Claude_Code.md    (what and why)
3. specs/00-engagement/DATA_GUIDE_and_Approach.md          (data facts and method)
4. specs/00-engagement/ASSESSMENT_PLAN_and_Repo_Structure.md (blueprint: sections 1 to 11)
5. docs/DATA_DICTIONARY.md                                  (the data/raw/data_dictionary.xlsx wins if they conflict)
Reference pattern for the Claude Code setup: my repo
https://github.com/Dr-Data-Azam/shafers-ai-pathology-assistant (.claude/ commands, skills,
agents, CLAUDE.md, specs/). Adapt it as described in ASSESSMENT_PLAN section 2. Do not copy
anything RAG, Docker, CI or GitHub-push related.

TASK FOR THIS SESSION: PHASE 00, SCAFFOLD ONLY (no analysis code)
Plan, then build after I approve:
1. git init; .gitignore (data/interim/, .venv/, caches, *.duckdb); pyproject.toml via uv
   (python 3.12+: pandas, duckdb, pyyaml, pytest, pytest-cov, black, ruff, jupyter,
   nbconvert, python-pptx, openpyxl, matplotlib).
2. The full folder tree from ASSESSMENT_PLAN section 5b, with empty modules in src/her2rwd/
   (docstrings only, stating each module's responsibility).
3. CLAUDE.md: hard rules, project overview, architecture, conventions, section 8 permission
   boundaries, feature lifecycle, command, skill and agent tables.
4. .claude/settings.json (deny rules + black/ruff hooks), then:
   (close-phase must append a row to audit/SESSION_LOG.md)
   commands: create-spec, close-phase, run-pipeline, validate, log-decision, build-report, test, lint, fix
   skills: generate-analysis-spec, generate-tech-spec, write-test, clinical-rules-reference,
           decision-log, deck-builder
   agents: code-reviewer, clinical-logic-reviewer, test-writer, reviewer-simulator
5. config/analysis_rules.yaml skeleton: keys only, with an ADR reference on each key and values
   marked TBD. Do not fill in values until I answer the open decisions.
6. audit/: DECISION_INDEX.md listing the 14 starter ADRs as "Proposed", an ADR template,
   an AI_USAGE.md stub, and SESSION_LOG.md (ASSESSMENT_PLAN section 11) with this session
   as the first row: "concertai-her2 | P00 scaffold".
7. docs/: ARCHITECTURE.md, DEVELOPMENT_PROCESS.md, DATA_LINEAGE.md stubs (keep the existing
   DATA_DICTIONARY.md).
8. README.md: summary, quickstart, repo tour, "where to find X", a note that external/ is the
   unmodified original attachment.
9. An input-integrity check (in src/her2rwd/io.py + a test) that SHA-256 hashes data/raw/ against
   ../external/ (read-only access) and fails loudly on any mismatch.
10. First local commit: "chore(scaffold): initialize repo structure and spec-driven workflow".

HOW TO WORK
- Show me the plan first (files to create, anything you would change from ASSESSMENT_PLAN,
  and why). Wait for my approval before writing files.
- Then ask me the 7 open decisions from PROJECT_BRIEF section 10, one block at a time,
  with your recommendation for each. Record my answers as ADRs.
- Flag anything marked VERIFY (Enhertu labels, literature benchmarks) as needing a citation.
  Never state it as fact.
- Do NOT start Phase 01 until I say "start phase 01".
- End by listing what was created and the next command to run (/create-spec 01-ingest-and-dq).

# 00-engagement: Index of Context Documents

> ⛔ `../../../external/` (ConcertAI_Assesment/external) is **STRICTLY READ-ONLY**. Never write, edit, move, delete or unzip into it.

Read the documents in this order:

| # | File | Role | One-line summary |
|---|---|---|---|
| 1 | `PROJECT_BRIEF_for_Claude_Code.md` | **What & why** (requirements) | Client framing, the official task, data dictionary, first data scan, clinical rules, likely reviewer questions, open decisions |
| 2 | `DATA_GUIDE_and_Approach.md` | **Data & method** (knowledge) | Part A: every table and trap explained. Part B: the ideal data scientist's 8-step playbook |
| 3 | `ASSESSMENT_PLAN_and_Repo_Structure.md` | **How we build & prove it** (blueprint) | Deliverables D1 to D8, Shafer's repo adaptation, the 7-layer audit framework, ADR backlog, phases, folder tree, commands, rules, the repo as a showcase |

## Source materials (copies of the read-only originals in `external/`)
| File | What | Use |
|---|---|---|
| `source/candidate_facing_instructions.docx` | the official task, byte-identical copy | authoritative if anything conflicts |
| `source/candidate_facing_instructions.md` | verbatim text extraction | what Claude Code reads (it can't parse .docx reliably) |
| `../../data/raw/data_dictionary.xlsx` | official data dictionary, byte-identical copy | authoritative |
| `../../docs/DATA_DICTIONARY.md` | Markdown render of the xlsx | readable reference; derived fields get added here later |

## Key points by file

### 1. PROJECT_BRIEF
- **Framing:** Azam as AD, Solutions Consulting delivering to a pharma Enhertu/HEOR client. The real context is the ConcertAI take-home ("Senior Data Scientist Technical Assessment"), reviewed by Brandon Nathasingh.
- **Timeline:** email the results Wed Sep 30 evening ET. Review Thu Oct 1, 3:00 to 3:30 PM ET (about a 15-minute presentation, the rest Q&A).
- **Task:**
  - Q1 = mBC cohort + index date + HER2 at metastatic diagnosis (positive/low/ultralow/0/unknown) + 3 or more stratifications + literature comparison + uncertainty + sensitivity analysis.
  - Q2 = Enhertu uptake vs competitors by subindication (HER2+, HR+/low, HR+/ultralow), first treatment, time to Enhertu, discordance, fit-for-purpose verdict.
- **Submission:** code + at most 5 slides (or 2 pages) + a DQ/assumptions appendix + tables.
- **Data scan:** 150 patients. Breast is dominant with some noise. HER2 variant patterns and conflicts. Planted traps (orphans, pediatric DOBs, death before birth, future and post-death dates).
- **Clinical rules:** ASCO/CAP HER2 categories incl. ultralow; HR ≥1%; Enhertu labels (DB-03/04/06/09, **VERIFY**); competitor map; literature benchmarks (**VERIFY**).
- **Reviewer probes** and **7 open decisions** for Azam.

### 2. DATA_GUIDE
- **Data model:** a patient spine + 4 long event tables linked only by patient_id + dates, so timing logic is everything.
- **Headline numbers:**
  - Cohort: 128 breast patients; 104 with a metastatic breast diagnosis; +2 stage-IV-only; 70 recurrent and 34 possibly de novo.
  - Biomarkers: **EHR HER2 variant blank 46% vs curated 1%**; **most HER2 tests fall after the metastatic date** (window −365/+90 → 71/104 patients; −365/+180 → 95/104).
  - Treatment: drugs start about 60 days post-index; Enhertu (42 patients) about 183 days post-index, i.e. later-line.
- **HER2 mapping table**, ER/PR result vs % conflicts, drug class table, **PAT_001 end-to-end example**, a **15-item traps checklist**.
- **Playbook:** profile → write rules first → build in layers → Q1 → Q2 → verdict → deck → rehearse, plus a suggested schedule.

### 3. ASSESSMENT_PLAN
- **Deliverables:**
  - D1 code zip · D2 HTML notebook · D3 deck (5 slides + Appendix A/B/C) · D4 tables · D5 audit pack · D6 README + docs · D7 email (no dashes).
  - D8 Q&A prep (internal).
- **From the Shafer's repo:**
  - Keep: CLAUDE.md, the spec lifecycle, /test /lint /fix, code-reviewer, test-writer.
  - Drop: ship-feature/push, RAG eval, security-reviewer, CI, Docker.
  - Add: /close-phase, /run-pipeline, /validate, /log-decision, /build-report, clinical-logic-reviewer, a "Brandon" reviewer-simulator.
- **7 audit layers:** ADR decision log · rules-as-config YAML · per-patient audit trail · DQ log · validation report · run manifest (hashes) · process trail (specs + git + AI_USAGE).
- **14 starter ADRs** and **8 phases** (01 ingest/DQ → 06 Q2 → 07 deliverables → 08 review prep).
- **Folder tree** incl. `docs/` (ARCHITECTURE, DEVELOPMENT_PROCESS, DATA_LINEAGE).
- **Section 10: the repo as a showcase.** Four questions a reviewer must be able to answer alone, a 2-minute repo walkthrough in the talk track, and deck Appendix C.

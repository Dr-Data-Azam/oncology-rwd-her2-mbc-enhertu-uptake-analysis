"""End-to-end pipeline orchestrator.

Responsibility:
    Run every stage of the analysis in the correct order, collect row counts
    and timing at each step, and write a run manifest to
    outputs/run_manifest.json.  The manifest records: timestamp, git commit
    hash, SHA-256 of each input file, hash of analysis_rules.yaml, package
    versions, and row counts per pipeline stage.

    Stages (in order):
        1. check_input_integrity  (io)
        2. load_raw               (io)
        3. run_dq_checks          (dq)
        4. build_cohort           (cohort)
        5. derive_her2            (her2)
        6. derive_hr              (hr)
        7. build_treatment_lines  (treatment)
        8. compute_q1             (q1_distribution)
        9. compute_q2             (q2_uptake)
       10. run_sensitivity        (sensitivity)
       11. validate               (validate)
       12. build_reports          (report)  — only when --reports flag is set

    Called via: uv run python -m her2rwd.pipeline [--rules config/alt.yaml] [--reports]

Inputs:
    All raw data and config files

Outputs:
    All outputs/tables/, outputs/figures/, outputs/dq/, and reports/ files
    outputs/run_manifest.json
"""

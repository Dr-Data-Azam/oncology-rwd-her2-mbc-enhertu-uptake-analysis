"""End-to-end pipeline orchestrator for the her2rwd analysis.

Responsibility:
    Run every stage in order, collect row counts and timing, and write
    outputs/run_manifest.json recording: timestamp, input SHA-256 hashes,
    config hash, package versions, and row counts per stage.

    Stages (in order):
        1. check_input_integrity  (data_loader)
        2. load_raw               (data_loader)
        3. run_dq_checks          (data_quality)
        4. build_cohort           (cohort)          — Phase 02
        5. derive_her2            (her2)             — Phase 03
        6. derive_hr              (hormone_receptor) — Phase 03
        7. build_treatment_lines  (treatment)        — Phase 05
        8. compute_q1             (q1_distribution)  — Phase 04
        9. compute_q2             (q2_uptake)        — Phase 06
       10. run_sensitivity        (sensitivity)      — Phase 06
       11. run_validation         (validation)       — Phase 07
       12. build_reports          (report)           — Phase 07, --reports flag only

    Called via: uv run python -m her2rwd.pipeline [--rules config/alt.yaml] [--reports]

ADRs implemented: ADR-001 (tooling)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

from her2rwd.cohort import build_cohort
from her2rwd.data_loader import check_input_integrity, load_raw
from her2rwd.data_quality import run_dq_checks
from her2rwd.her2 import derive_her2
from her2rwd.hormone_receptor import derive_hr
from her2rwd.q1_distribution import compute_q1
from her2rwd.q2_uptake import compute_q2
from her2rwd.report import build_reports
from her2rwd.sensitivity import run_sensitivity
from her2rwd.treatment import build_treatment_lines
from her2rwd.validation import run_validation


def _load_cfg(rules_path: str = "config/analysis_rules.yaml") -> dict:
    with open(rules_path) as f:
        return yaml.safe_load(f)


def _cfg_hash(rules_path: str) -> str:
    return hashlib.sha256(Path(rules_path).read_bytes()).hexdigest()


def _pkg_versions() -> dict[str, str]:
    pkgs = ["duckdb", "pandas", "pyyaml", "python-pptx", "nbconvert"]
    versions = {}
    for pkg in pkgs:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = "not installed"
    return versions


def run(rules_path: str = "config/analysis_rules.yaml", reports: bool = False) -> dict:
    """Run the full pipeline and return the manifest dict."""
    t0 = time.time()
    manifest: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "rules_file": rules_path,
        "config_sha256": _cfg_hash(rules_path),
        "package_versions": _pkg_versions(),
        "stages": {},
        "input_hashes": {},
    }

    cfg = _load_cfg(rules_path)

    # ── Stage 1: integrity check ──────────────────────────────────────────────
    print("Stage 1: input integrity check...")
    hashes = check_input_integrity()
    manifest["input_hashes"] = hashes
    print(f"  {len(hashes)} files verified OK")

    # ── Stage 2: load raw ─────────────────────────────────────────────────────
    print("Stage 2: loading raw data...")
    con = load_raw()
    counts = {
        tbl: con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        for tbl in ["patient", "diagnosis", "staging", "biomarker", "medication"]
    }
    manifest["stages"]["load_raw"] = {"row_counts": counts}
    for tbl, n in counts.items():
        print(f"  {tbl}: {n:,} rows")

    # ── Stage 3: DQ checks ────────────────────────────────────────────────────
    print("Stage 3: data quality checks...")
    dq_summary = run_dq_checks(con, cfg)
    errors = dq_summary[dq_summary["severity"] == "error"]["n_flagged"].sum()
    warnings = dq_summary[dq_summary["severity"] == "warning"]["n_flagged"].sum()
    manifest["stages"]["dq_checks"] = {
        "n_checks": len(dq_summary),
        "total_errors": int(errors),
        "total_warnings": int(warnings),
    }
    print(f"  {len(dq_summary)} checks: {int(errors)} errors, {int(warnings)} warnings")
    if errors > 0:
        flagged = dq_summary[dq_summary["severity"] == "error"][["check_name", "n_flagged"]]
        for _, row in flagged.iterrows():
            if row["n_flagged"] > 0:
                print(f"  [ERROR] {row['check_name']}: {row['n_flagged']} records")

    # ── Stage 4: cohort construction ──────────────────────────────────────────
    print("Stage 4: building cohort...")
    cohort_df, attrition_df = build_cohort(con, cfg)
    final_n = int(attrition_df.iloc[-1]["n_remaining"])
    de_novo = int((cohort_df["disease_type"] == "de_novo").sum())
    recurrent = int((cohort_df["disease_type"] == "recurrent").sum())
    manifest["stages"]["cohort"] = {
        "n_eligible": final_n,
        "n_de_novo": de_novo,
        "n_recurrent": recurrent,
    }
    print(f"  {final_n} eligible patients ({de_novo} de novo, {recurrent} recurrent)")
    for _, row in attrition_df.iterrows():
        if row["n_excluded"] > 0:
            print(f"  [-{int(row['n_excluded'])}] {row['step_label']}")

    # ── Stage 5: HER2 classification ─────────────────────────────────────────
    print("Stage 5: deriving HER2 categories...")
    her2_df = derive_her2(con, cohort_df, cfg)
    her2_counts = her2_df["her2_category"].value_counts().to_dict()
    manifest["stages"]["her2"] = {"category_counts": her2_counts}
    for cat, n in sorted(her2_counts.items()):
        print(f"  {cat}: {n}")

    # ── Stage 6: HR status ────────────────────────────────────────────────────
    print("Stage 6: deriving HR status...")
    hr_df = derive_hr(con, cohort_df, cfg)
    hr_counts = hr_df["hr_status"].value_counts().to_dict()
    er_low_n = int(hr_df["er_low"].sum())
    manifest["stages"]["hr"] = {"status_counts": hr_counts, "n_er_low": er_low_n}
    for status, n in sorted(hr_counts.items()):
        print(f"  {status}: {n}")
    print(f"  ER-low: {er_low_n}")

    # ── Stage 7: treatment lines ──────────────────────────────────────────────
    print("Stage 7: building treatment lines...")
    lines_df = build_treatment_lines(con, cohort_df, cfg)
    n_treated = lines_df["patient_id"].nunique()
    n_enhertu = int(lines_df[lines_df["contains_enhertu"]]["patient_id"].nunique())
    line_dist = lines_df.groupby("line_number")["patient_id"].nunique().to_dict()
    manifest["stages"]["treatment"] = {
        "n_patients_with_treatment": n_treated,
        "n_patients_enhertu": n_enhertu,
        "n_patients_per_line": {str(k): v for k, v in line_dist.items()},
    }
    print(f"  {n_treated} patients with treatment on/after index date")
    print(f"  Enhertu recipients: {n_enhertu}")
    for ln, n in sorted(line_dist.items()):
        print(f"  Line {ln}: {n} patients")

    # ── Stage 8: Q1 distribution ─────────────────────────────────────────────
    print("Stage 8: computing Q1 HER2 distribution...")
    q1_results = compute_q1(her2_df, hr_df, cohort_df, cfg)
    overall = q1_results["overall"]
    n_class = q1_results["n_classifiable"]
    cat_summary = {
        row["her2_category"]: {
            "n": int(row["n"]),
            "pct": float(row["pct"]),
            "small_cell": bool(row["small_cell"]),
        }
        for _, row in overall.iterrows()
    }
    manifest["stages"]["q1_distribution"] = {
        "n_total": q1_results["n_total"],
        "n_classifiable": n_class,
        "categories": cat_summary,
    }
    for _, row in overall.iterrows():
        flag = " [n<11]" if row["small_cell"] else ""
        print(f"  {row['her2_category']}: {int(row['n'])} ({row['pct']}%){flag}")

    # ── Stage 9: Q2 uptake ────────────────────────────────────────────────────
    print("Stage 9: computing Q2 Enhertu uptake...")
    q2_results = compute_q2(her2_df, hr_df, lines_df, cohort_df, cfg)
    uptake = q2_results["uptake_summary"]
    n_discord_unknown = len(q2_results["discordance_unknown_her2"])
    n_discord_1l = len(q2_results["discordance_1l"])
    manifest["stages"]["q2_uptake"] = {
        "n_discordance_unknown_her2": n_discord_unknown,
        "n_discordance_1l": n_discord_1l,
        "uptake_by_subindication": {
            row["subindication"]: {
                "n_total": int(row["n_total"]),
                "n_enhertu": int(row["n_enhertu"]),
                "pct_enhertu": float(row["pct_enhertu"]),
            }
            for _, row in uptake.iterrows()
        },
    }
    for _, row in uptake[uptake["subindication_type"] == "required"].iterrows():
        flag = " [n<11]" if row["small_cell"] else ""
        print(f"  {row['subindication']}: {int(row['n_enhertu'])}/{int(row['n_total'])} ({row['pct_enhertu']}%){flag}")
    print(f"  Discordance — unknown HER2: {n_discord_unknown} | 1L: {n_discord_1l}")

    # ── Stage 10: sensitivity analyses ───────────────────────────────────────
    print("Stage 10: running sensitivity analyses...")
    sens_results = run_sensitivity(con, cohort_df, cfg)
    sens_dist = sens_results["her2_distribution"]
    manifest["stages"]["sensitivity"] = {
        "scenarios": ["baseline", "s1_narrow_window", "s2_curated_only", "s3_conservative_ihc0"],
        "n_rows": len(sens_dist),
    }
    print(f"  Sensitivity tables written ({len(sens_dist)} category rows × 4 scenarios)")

    # ── Stage 11: validation ──────────────────────────────────────────────────
    print("Stage 11: running validation checks...")
    val_df = run_validation()
    n_val_pass = int((val_df["result"] == "PASS").sum())
    n_val_fail = int((val_df["result"] == "FAIL").sum())
    manifest["stages"]["validation"] = {
        "n_checks": len(val_df),
        "n_pass": n_val_pass,
        "n_fail": n_val_fail,
    }
    print(f"  {n_val_pass} PASS, {n_val_fail} FAIL — see audit/validation_report.md")

    # ── Stage 12: reports (--reports flag) ────────────────────────────────────
    if reports:
        print("Stage 12: building reports (HTML + pptx)...")
        report_results = build_reports(cfg)
        manifest["stages"]["reports"] = {
            "html": report_results.get("html"),
            "pptx": report_results.get("pptx"),
            "pdf": report_results.get("pdf"),
        }
        print(f"  HTML: {report_results.get('html')}")
        print(f"  PPTX: {report_results.get('pptx')}")

    # ── Write manifest ────────────────────────────────────────────────────────
    manifest["elapsed_seconds"] = round(time.time() - t0, 2)
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written to {manifest_path}")

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the her2rwd analysis pipeline.")
    parser.add_argument(
        "--rules",
        default="config/analysis_rules.yaml",
        help="Path to analysis_rules.yaml (default: config/analysis_rules.yaml)",
    )
    parser.add_argument(
        "--reports",
        action="store_true",
        help="Also build HTML notebook and pptx (Phase 07+)",
    )
    args = parser.parse_args()
    run(rules_path=args.rules, reports=args.reports)


if __name__ == "__main__":
    main()

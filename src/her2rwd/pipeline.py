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
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from her2rwd.data_loader import check_input_integrity, load_raw
from her2rwd.data_quality import run_dq_checks


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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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

    # ── Phases 02–07 are stubs until those phases are built ──────────────────
    # Each phase will add its stage block here.

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

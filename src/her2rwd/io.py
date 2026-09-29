"""Input/output and data integrity for the her2rwd pipeline.

Responsibility:
    Load the five raw CSVs and the data dictionary into an in-memory or
    file-backed DuckDB database.  Before loading, verify that every file in
    data/raw/ is byte-for-byte identical to the originals in ../external/ by
    comparing SHA-256 hashes.  The external/ folder is STRICTLY READ-ONLY;
    this module reads it only to compute hashes and never writes there.

Inputs:
    data/raw/{patient,diagnosis,staging,biomarker,medication}.csv
    data/raw/data_dictionary.xlsx
    ../external/data_dictionary.xlsx           (hash reference, read-only)
    ../external/synthetic_breast_her2_dataset_csv.zip  (hash reference, read-only)

Outputs:
    DuckDB connection with raw tables loaded
    dict[str, str] of {filename: sha256_hex} returned by check_input_integrity()
    RuntimeError raised loudly if any hash mismatches

ADRs implemented: ADR-001 (tooling)
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import duckdb

# Internal zip prefix for the five CSVs inside ../external/synthetic_breast_her2_dataset_csv.zip
_ZIP_PREFIX = "synthetic_breast_her2_dataset_csv"

_CSV_FILES = ["patient", "diagnosis", "staging", "biomarker", "medication"]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def check_input_integrity(
    raw_dir: Path | str = "data/raw",
    external_dir: Path | str = "../external",
) -> dict[str, str]:
    """Verify data/raw/ files are byte-identical to the originals in ../external/.

    Compares SHA-256 hashes for:
    - data/raw/data_dictionary.xlsx  vs  ../external/data_dictionary.xlsx  (direct)
    - data/raw/<name>.csv  vs  the corresponding entry inside
      ../external/synthetic_breast_her2_dataset_csv.zip  (read without extraction)

    Args:
        raw_dir: Path to data/raw/ (relative to cwd or absolute).
        external_dir: Path to ../external/ (relative to cwd or absolute).
            This directory is STRICTLY READ-ONLY; this function never writes there.

    Returns:
        dict mapping filename → sha256_hex for every verified file.

    Raises:
        RuntimeError: if any file is missing or its hash does not match the original.

    ADRs implemented: ADR-001 (tooling)
    """
    raw = Path(raw_dir)
    external = Path(external_dir)
    hashes: dict[str, str] = {}
    mismatches: list[str] = []

    # --- data_dictionary.xlsx: direct file vs file ---
    raw_dict = raw / "data_dictionary.xlsx"
    ext_dict = external / "data_dictionary.xlsx"
    for path, label in [(raw_dict, "raw"), (ext_dict, "external")]:
        if not path.exists():
            raise RuntimeError(f"Missing file: {path}")
    raw_hash = _sha256_file(raw_dict)
    ext_hash = _sha256_file(ext_dict)
    if raw_hash != ext_hash:
        mismatches.append(
            f"data_dictionary.xlsx: raw={raw_hash[:12]}… external={ext_hash[:12]}…"
        )
    hashes["data_dictionary.xlsx"] = raw_hash

    # --- five CSVs: raw file vs entry inside the zip ---
    zip_path = external / "synthetic_breast_her2_dataset_csv.zip"
    if not zip_path.exists():
        raise RuntimeError(f"Missing zip: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in _CSV_FILES:
            raw_csv = raw / f"{name}.csv"
            zip_entry = f"{_ZIP_PREFIX}/{name}.csv"
            if not raw_csv.exists():
                raise RuntimeError(f"Missing raw file: {raw_csv}")
            try:
                zip_bytes = zf.read(zip_entry)
            except KeyError:
                raise RuntimeError(f"Entry not found in zip: {zip_entry}")
            raw_hash = _sha256_file(raw_csv)
            zip_hash = _sha256_bytes(zip_bytes)
            if raw_hash != zip_hash:
                mismatches.append(
                    f"{name}.csv: raw={raw_hash[:12]}… zip={zip_hash[:12]}…"
                )
            hashes[f"{name}.csv"] = raw_hash

    if mismatches:
        lines = "\n  ".join(mismatches)
        raise RuntimeError(
            f"Input integrity check FAILED — {len(mismatches)} mismatch(es):\n  {lines}\n"
            "data/raw/ files must be byte-identical to ../external/ originals."
        )

    return hashes


def load_raw(
    raw_dir: Path | str = "data/raw",
    db_path: str = ":memory:",
) -> duckdb.DuckDBPyConnection:
    """Load all five raw CSVs into a DuckDB database and return the connection.

    Tables created: patient, diagnosis, staging, biomarker, medication.
    Schema is inferred from the CSV headers; no transformations are applied here.

    Args:
        raw_dir: Path to data/raw/.
        db_path: DuckDB connection string. Use ":memory:" for tests;
                 use "data/interim/her2rwd.duckdb" for the pipeline.

    Returns:
        Open DuckDB connection with all five tables loaded.

    ADRs implemented: ADR-001 (tooling)
    """
    raw = Path(raw_dir)
    con = duckdb.connect(db_path)
    for name in _CSV_FILES:
        csv_path = raw / f"{name}.csv"
        con.execute(
            f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_csv_auto('{csv_path}')"
        )
    return con


if __name__ == "__main__":
    print("Running input integrity check...")
    hashes = check_input_integrity()
    for fname, h in hashes.items():
        print(f"  {fname}: {h}")
    print("All files verified OK.")

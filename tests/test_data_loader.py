"""Tests for data_loader.py — input integrity check and raw data loading.

Covers:
- check_input_integrity() passes when data/raw/ files match ../external/ originals
- check_input_integrity() raises RuntimeError with both hashes on any mismatch
- check_input_integrity() raises RuntimeError if a file is missing
- load_raw() creates expected tables in DuckDB

Fixtures use a temporary directory with synthesised tiny CSVs and a matching zip;
they never touch data/raw/ or ../external/.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from her2rwd.data_loader import check_input_integrity, load_raw

_CSV_NAMES = ["patient", "diagnosis", "staging", "biomarker", "medication"]
_TINY_CSV = b"patient_id,date_of_birth\nPAT_001,1980-01-01\n"
_TINY_XLSX = b"PK\x03\x04"  # minimal XLSX magic bytes (enough for hash comparison)
_ZIP_PREFIX = "synthetic_breast_her2_dataset_csv"


def _make_external_zip(external_dir: Path, csv_bytes: bytes) -> None:
    """Create a zip in external_dir containing all five tiny CSVs."""
    zip_path = external_dir / "synthetic_breast_her2_dataset_csv.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name in _CSV_NAMES:
            zf.writestr(f"{_ZIP_PREFIX}/{name}.csv", csv_bytes)


def _make_raw_dir(raw_dir: Path, csv_bytes: bytes, xlsx_bytes: bytes) -> None:
    """Create raw_dir with five CSVs and a data_dictionary.xlsx."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name in _CSV_NAMES:
        (raw_dir / f"{name}.csv").write_bytes(csv_bytes)
    (raw_dir / "data_dictionary.xlsx").write_bytes(xlsx_bytes)


def _make_external_dir(external_dir: Path, zip_csv_bytes: bytes, xlsx_bytes: bytes) -> None:
    """Create external_dir with the zip and data_dictionary.xlsx."""
    external_dir.mkdir(parents=True, exist_ok=True)
    _make_external_zip(external_dir, zip_csv_bytes)
    (external_dir / "data_dictionary.xlsx").write_bytes(xlsx_bytes)


# ─────────────────────────────────────────────────────────────────────────────


def test_integrity_passes_with_matching_files(tmp_path):
    """check_input_integrity() returns a hash dict when all files match."""
    raw_dir = tmp_path / "raw"
    external_dir = tmp_path / "external"
    _make_raw_dir(raw_dir, _TINY_CSV, _TINY_XLSX)
    _make_external_dir(external_dir, _TINY_CSV, _TINY_XLSX)

    result = check_input_integrity(raw_dir=raw_dir, external_dir=external_dir)

    assert isinstance(result, dict)
    expected_keys = {f"{name}.csv" for name in _CSV_NAMES} | {"data_dictionary.xlsx"}
    assert set(result.keys()) == expected_keys
    # all hashes are 64-char hex strings
    for h in result.values():
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


def test_integrity_fails_on_csv_mismatch(tmp_path):
    """check_input_integrity() raises RuntimeError when a CSV has been modified."""
    raw_dir = tmp_path / "raw"
    external_dir = tmp_path / "external"
    # raw CSV is different from what is in the zip
    modified_csv = _TINY_CSV + b"PAT_002,1990-06-15\n"
    _make_raw_dir(raw_dir, modified_csv, _TINY_XLSX)
    _make_external_dir(external_dir, _TINY_CSV, _TINY_XLSX)

    with pytest.raises(RuntimeError, match="integrity check FAILED"):
        check_input_integrity(raw_dir=raw_dir, external_dir=external_dir)


def test_integrity_fails_on_xlsx_mismatch(tmp_path):
    """check_input_integrity() raises RuntimeError when data_dictionary.xlsx differs."""
    raw_dir = tmp_path / "raw"
    external_dir = tmp_path / "external"
    modified_xlsx = _TINY_XLSX + b"\x00extra"
    _make_raw_dir(raw_dir, _TINY_CSV, modified_xlsx)
    _make_external_dir(external_dir, _TINY_CSV, _TINY_XLSX)

    with pytest.raises(RuntimeError, match="integrity check FAILED"):
        check_input_integrity(raw_dir=raw_dir, external_dir=external_dir)


def test_integrity_fails_on_missing_raw_csv(tmp_path):
    """check_input_integrity() raises RuntimeError if a raw CSV is missing."""
    raw_dir = tmp_path / "raw"
    external_dir = tmp_path / "external"
    _make_raw_dir(raw_dir, _TINY_CSV, _TINY_XLSX)
    _make_external_dir(external_dir, _TINY_CSV, _TINY_XLSX)
    # remove one raw CSV
    (raw_dir / "patient.csv").unlink()

    with pytest.raises(RuntimeError, match="Missing"):
        check_input_integrity(raw_dir=raw_dir, external_dir=external_dir)


def test_load_raw_creates_expected_tables(tmp_path):
    """load_raw() creates all five tables in DuckDB with at least one row."""
    raw_dir = tmp_path / "raw"
    _make_raw_dir(raw_dir, _TINY_CSV, _TINY_XLSX)

    con = load_raw(raw_dir=raw_dir, db_path=":memory:")

    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    for name in _CSV_NAMES:
        assert name in tables, f"Table '{name}' not found in DuckDB"
    # patient table should have one row (from _TINY_CSV)
    count = con.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
    assert count == 1
    con.close()

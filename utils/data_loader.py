"""
Data loading utilities for the Kayako ticket analysis pipeline.

Consolidates all CSV/JSON loading logic from the various scripts.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Optional

from config import (
    FULL_TICKET_DATA_CSV,
    GROUND_TRUTH_CSV,
    POC_SAMPLE_CSV,
    RAW_DIR,
    CSV_CONTEXT_FIELDS,
    OUR_PATTERNS,
)


def clean_csv_value(v: Any) -> Optional[str]:
    """Clean a CSV value, returning None for empty/null values."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    return s


def load_csv_context(csv_file: Optional[Path] = None) -> dict[int, dict[str, Any]]:
    """
    Load a compact per-ticket context map from the authoritative CSV universe.

    Returns a dict mapping ticket_id -> {field: value} for CSV_CONTEXT_FIELDS.
    """
    csv_path = csv_file or FULL_TICKET_DATA_CSV
    if not csv_path.exists():
        return {}

    out: dict[int, dict[str, Any]] = {}
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return {}
        fields = set(reader.fieldnames)
        use_fields = [c for c in CSV_CONTEXT_FIELDS if c in fields]
        if "Ticket ID" not in fields:
            raise RuntimeError(f"{csv_path.name} is missing required 'Ticket ID' column")

        for row in reader:
            tid_raw = row.get("Ticket ID")
            if tid_raw is None:
                continue
            try:
                tid = int(str(tid_raw).strip())
            except (ValueError, TypeError):
                continue
            ctx: dict[str, Any] = {}
            for k in use_fields:
                v = clean_csv_value(row.get(k))
                if v is not None:
                    ctx[k] = v
            out[tid] = ctx
    return out


def load_expected_labels(gt_csv: Optional[Path] = None) -> dict[int, set[str]]:
    """
    Load expected labels from ground truth CSV.

    Returns a dict mapping ticket_id -> set of expected pattern labels.
    """
    csv_path = gt_csv or GROUND_TRUTH_CSV
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found")

    expected: dict[int, set[str]] = {}
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise RuntimeError("Empty ground truth CSV")
        if "Ticket ID" not in reader.fieldnames:
            raise RuntimeError("ground truth missing 'Ticket ID' column")
        if "Expected Labels" not in reader.fieldnames:
            raise RuntimeError("ground truth missing 'Expected Labels' column")

        for row in reader:
            tid_raw = row.get("Ticket ID")
            if not tid_raw:
                continue
            tid = int(str(tid_raw).strip())
            labels_raw = row.get("Expected Labels") or "[]"
            try:
                labels = set(json.loads(labels_raw))
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Bad Expected Labels JSON for ticket {tid}: {labels_raw}") from e
            expected[tid] = {x for x in labels if x in OUR_PATTERNS}
    return expected


def load_predicted_labels(result_file: Path) -> set[str]:
    """
    Load predicted labels from a single LLM result JSON file.

    Returns a set of pattern labels that were detected=true.
    """
    data = json.loads(result_file.read_text())
    pred: set[str] = set()
    for p in OUR_PATTERNS:
        block: Any = data.get(p)
        if isinstance(block, dict) and block.get("detected") is True:
            pred.add(p)
    return pred


def load_ground_truth_ticket_ids(gt_csv: Optional[Path] = None) -> list[int]:
    """
    Load list of ticket IDs from ground truth CSV.
    """
    csv_path = gt_csv or GROUND_TRUTH_CSV
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found. Run: python3 6_build_ground_truth.py")

    ids: list[int] = []
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if "Ticket ID" not in (reader.fieldnames or []):
            raise RuntimeError("ground_truth_expected.csv missing 'Ticket ID' column")
        for row in reader:
            tid_raw = row.get("Ticket ID")
            if not tid_raw:
                continue
            try:
                ids.append(int(str(tid_raw).strip()))
            except (ValueError, TypeError):
                continue
    return sorted(set(ids))


def load_poc_sample_ticket_ids(sample_csv: Optional[Path] = None) -> list[int]:
    """
    Load Phase 0 sample ticket IDs (built by 0_build_sample.py).
    """
    csv_path = sample_csv or POC_SAMPLE_CSV
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found. Run: python3 0_build_sample.py")

    ids: list[int] = []
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if "ticket_id" not in (reader.fieldnames or []):
            raise RuntimeError("poc_sample.csv missing 'ticket_id' column")
        for row in reader:
            tid_raw = row.get("ticket_id")
            if not tid_raw:
                continue
            try:
                ids.append(int(str(tid_raw).strip()))
            except (ValueError, TypeError):
                continue

    return sorted(set(ids))


def load_ticket_raw(ticket_id: int, raw_dir: Optional[Path] = None) -> Optional[dict]:
    """
    Load raw ticket JSON from the raw directory.

    Returns the parsed JSON or None if file doesn't exist.
    """
    dir_path = raw_dir or RAW_DIR
    raw_file = dir_path / f"ticket_{ticket_id}.json"
    if not raw_file.exists():
        return None

    with open(raw_file, "r") as f:
        return json.load(f)

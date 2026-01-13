#!/usr/bin/env python3
"""
Recall-first evaluation: we only care whether the model includes the ground-truth labels.
False positives (extra predicted labels) are NOT penalized.

Inputs:
- data/poc/ground_truth_expected.csv  (Ticket ID + expected labels)
- an LLM results directory containing ticket_<id>.json (e.g., data/poc/llm_results/gpt-5.2-v5-gt-rerun)

Outputs (printed):
- ticket-level full coverage rate (all expected labels hit)
- label-level recall (TP/expected) ignoring FP
- list of missed expected labels with ticket ids
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OUR_PATTERNS = [
    "AI_QUALITY_FAILURES",
    "AI_WALL_LOOPING",
    "IGNORING_CONTEXT",
    "RESPONSE_DELAYS",
    "PREMATURE_CLOSURE",
    "P1_SEV1_MISHANDLING",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Recall-first evaluation (ignore false positives).")
    p.add_argument(
        "--ground-truth",
        default="data/poc/ground_truth_expected.csv",
        help="Path to ground_truth_expected.csv",
    )
    p.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing ticket_<id>.json model outputs",
    )
    p.add_argument(
        "--show-misses",
        type=int,
        default=50,
        help="Max missed-label rows to print",
    )
    return p.parse_args()


def _load_expected(gt_csv: Path) -> dict[int, set[str]]:
    expected: dict[int, set[str]] = {}
    with gt_csv.open("r", newline="") as f:
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
            except Exception as e:  # noqa: BLE001
                raise RuntimeError(f"Bad Expected Labels JSON for ticket {tid}: {labels_raw}") from e
            expected[tid] = {x for x in labels if x in OUR_PATTERNS}
    return expected


def _load_predicted(result_file: Path) -> set[str]:
    data = json.loads(result_file.read_text())
    pred: set[str] = set()
    for p in OUR_PATTERNS:
        block: Any = data.get(p)
        if isinstance(block, dict) and block.get("detected") is True:
            pred.add(p)
    return pred


def main() -> None:
    args = parse_args()
    gt_csv = Path(args.ground_truth)
    results_dir = Path(args.results_dir)

    if not gt_csv.exists():
        raise FileNotFoundError(str(gt_csv))
    if not results_dir.exists():
        raise FileNotFoundError(str(results_dir))

    expected = _load_expected(gt_csv)
    missing_result_files = [tid for tid in expected.keys() if not (results_dir / f"ticket_{tid}.json").exists()]
    if missing_result_files:
        raise RuntimeError(f"Missing {len(missing_result_files)} result files, e.g. {missing_result_files[:5]}")

    expected_counts = Counter()
    hit_counts = Counter()
    missed_by_label: dict[str, list[int]] = defaultdict(list)

    tickets_full_covered = 0
    tickets_with_any_expected = 0

    for tid, exp in expected.items():
        exp = set(exp)
        if not exp:
            continue
        tickets_with_any_expected += 1

        pred = _load_predicted(results_dir / f"ticket_{tid}.json")
        for label in exp:
            expected_counts[label] += 1
            if label in pred:
                hit_counts[label] += 1
            else:
                missed_by_label[label].append(tid)

        if exp.issubset(pred):
            tickets_full_covered += 1

    print("Recall-first evaluation (ignore false positives)")
    print(f"- Ground truth file: {gt_csv}")
    print(f"- Results dir:       {results_dir}")
    print()
    print(f"Ticket-level full coverage: {tickets_full_covered}/{tickets_with_any_expected} = {tickets_full_covered / max(1, tickets_with_any_expected):.3f}")
    print()
    print("Label-level recall (TP/expected):")
    for p in OUR_PATTERNS:
        denom = expected_counts.get(p, 0)
        num = hit_counts.get(p, 0)
        if denom == 0:
            print(f"- {p}: n/a (0 expected)")
        else:
            print(f"- {p}: {num}/{denom} = {num / denom:.3f}")

    total_expected = sum(expected_counts.values())
    total_hit = sum(hit_counts.values())
    print()
    print(f"Overall label recall: {total_hit}/{total_expected} = {total_hit / max(1, total_expected):.3f}")

    misses = []
    for label, tids in missed_by_label.items():
        for tid in tids:
            misses.append((label, tid))
    misses.sort()

    if misses:
        print()
        print(f"Missed expected labels (showing up to {args.show_misses}):")
        for label, tid in misses[: args.show_misses]:
            print(f"- ticket {tid}: missed {label}")
        if len(misses) > args.show_misses:
            print(f"... ({len(misses) - args.show_misses} more)")


if __name__ == "__main__":
    main()



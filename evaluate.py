#!/usr/bin/env python3
"""
Evaluation script for multi-label pattern detection.

Computes:
- Recall-first metrics (ignores false positives)
- Standard precision/recall/F1 (micro and macro)
- Per-label breakdown

Usage:
    python evaluate.py --results-dir data/poc/llm_results/gpt-5.2-v6
    python evaluate.py --results-dir data/poc/llm_results/gpt-5.2-v6 --mode recall-only
    python evaluate.py --results-dir data/poc/llm_results/gpt-5.2-v6 --mode full
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from config import GROUND_TRUTH_CSV, OUR_PATTERNS
from utils import load_expected_labels, load_predicted_labels


def safe_div(num: int, den: int) -> float:
    """Safe division returning 0.0 if denominator is 0."""
    return num / den if den else 0.0


def evaluate_recall_only(
    expected: dict[int, set[str]],
    results_dir: Path,
    show_misses: int = 50,
) -> dict:
    """
    Recall-first evaluation: only care whether model includes ground-truth labels.
    False positives (extra predicted labels) are NOT penalized.

    IMPORTANT: Missing result files are treated as missed predictions (all labels missed),
    not skipped, to avoid artificially inflating recall metrics.
    """
    expected_counts: Counter[str] = Counter()
    hit_counts: Counter[str] = Counter()
    missed_by_label: dict[str, list[int]] = defaultdict(list)
    missing_result_files: list[int] = []

    tickets_full_covered = 0
    tickets_with_any_expected = 0

    for tid, exp in expected.items():
        exp = set(exp)
        if not exp:
            continue
        tickets_with_any_expected += 1

        result_file = results_dir / f"ticket_{tid}.json"
        if not result_file.exists():
            # Treat missing files as all labels missed (not skipped!)
            # This prevents artificially inflating recall
            missing_result_files.append(tid)
            for label in exp:
                expected_counts[label] += 1
                missed_by_label[label].append(tid)
            continue

        pred = load_predicted_labels(result_file)
        for label in exp:
            expected_counts[label] += 1
            if label in pred:
                hit_counts[label] += 1
            else:
                missed_by_label[label].append(tid)

        if exp.issubset(pred):
            tickets_full_covered += 1

    # Calculate metrics
    total_expected = sum(expected_counts.values())
    total_hit = sum(hit_counts.values())
    overall_recall = safe_div(total_hit, total_expected)
    ticket_coverage = safe_div(tickets_full_covered, tickets_with_any_expected)

    per_label_recall = {}
    for p in OUR_PATTERNS:
        denom = expected_counts.get(p, 0)
        num = hit_counts.get(p, 0)
        per_label_recall[p] = {
            "recall": safe_div(num, denom),
            "hit": num,
            "expected": denom,
        }

    return {
        "mode": "recall-only",
        "ticket_coverage": ticket_coverage,
        "tickets_full_covered": tickets_full_covered,
        "tickets_with_expected": tickets_with_any_expected,
        "overall_recall": overall_recall,
        "total_hit": total_hit,
        "total_expected": total_expected,
        "per_label": per_label_recall,
        "missed_by_label": dict(missed_by_label),
        "missing_result_files": missing_result_files,
    }


def evaluate_full(
    expected: dict[int, set[str]],
    results_dir: Path,
) -> dict:
    """
    Standard precision/recall/F1 evaluation for multi-label classification.

    IMPORTANT: Missing result files are treated as having NO predictions (empty set),
    which means all expected labels are counted as false negatives. This is consistent
    with evaluate_recall_only() and prevents artificially inflating recall by skipping
    difficult cases.
    """
    # Micro counts across all label instances
    micro_tp = 0
    micro_fp = 0
    micro_fn = 0

    # Per-label counts
    tp: Counter[str] = Counter()
    fp: Counter[str] = Counter()
    fn: Counter[str] = Counter()
    support: Counter[str] = Counter()

    missing_result_files: list[int] = []

    for tid, exp in expected.items():
        result_file = results_dir / f"ticket_{tid}.json"

        if not result_file.exists():
            # Treat missing files as empty predictions (no labels detected)
            # This means all expected labels become false negatives
            missing_result_files.append(tid)
            pred: set[str] = set()
        else:
            pred = load_predicted_labels(result_file)

        for label in OUR_PATTERNS:
            exp_has = label in exp
            pred_has = label in pred
            if exp_has:
                support[label] += 1
            if pred_has and exp_has:
                micro_tp += 1
                tp[label] += 1
            elif pred_has and not exp_has:
                micro_fp += 1
                fp[label] += 1
            elif (not pred_has) and exp_has:
                micro_fn += 1
                fn[label] += 1

    # Micro metrics
    micro_precision = safe_div(micro_tp, micro_tp + micro_fp)
    micro_recall = safe_div(micro_tp, micro_tp + micro_fn)
    micro_f1 = safe_div(2 * micro_precision * micro_recall, micro_precision + micro_recall)

    # Per-label and macro metrics
    per_label_metrics = {}
    macro_f1_sum = 0.0
    macro_n = 0

    for label in OUR_PATTERNS:
        p = safe_div(tp[label], tp[label] + fp[label])
        r = safe_div(tp[label], tp[label] + fn[label])
        f1 = safe_div(2 * p * r, p + r)
        per_label_metrics[label] = {
            "precision": p,
            "recall": r,
            "f1": f1,
            "tp": tp[label],
            "fp": fp[label],
            "fn": fn[label],
            "support": support[label],
        }
        if support[label] > 0:
            macro_f1_sum += f1
            macro_n += 1

    macro_f1 = macro_f1_sum / macro_n if macro_n else 0.0

    return {
        "mode": "full",
        "micro": {
            "precision": micro_precision,
            "recall": micro_recall,
            "f1": micro_f1,
            "tp": micro_tp,
            "fp": micro_fp,
            "fn": micro_fn,
        },
        "macro_f1": macro_f1,
        "per_label": per_label_metrics,
        "missing_result_files": missing_result_files,
    }


def print_recall_results(results: dict, show_misses: int = 50) -> None:
    """Print recall-only evaluation results."""
    print("=" * 72)
    print("RECALL-FIRST EVALUATION (ignores false positives)")
    print("=" * 72)
    print()

    # Show warning if there were missing result files
    missing_files = results.get("missing_result_files", [])
    if missing_files:
        print(f"WARNING: {len(missing_files)} result files missing (treated as all labels missed)")
        print(f"         Missing tickets: {missing_files[:10]}{'...' if len(missing_files) > 10 else ''}")
        print()

    print(f"Ticket-level full coverage: {results['tickets_full_covered']}/{results['tickets_with_expected']} = {results['ticket_coverage']:.3f}")
    print()
    print("Label-level recall (TP/expected):")
    for p in OUR_PATTERNS:
        m = results["per_label"][p]
        if m["expected"] == 0:
            print(f"  {p}: n/a (0 expected)")
        else:
            print(f"  {p}: {m['hit']}/{m['expected']} = {m['recall']:.3f}")

    print()
    print(f"Overall label recall: {results['total_hit']}/{results['total_expected']} = {results['overall_recall']:.3f}")

    # Show missed labels
    misses = []
    for label, tids in results["missed_by_label"].items():
        for tid in tids:
            misses.append((label, tid))
    misses.sort()

    if misses:
        print()
        print(f"Missed expected labels (showing up to {show_misses}):")
        for label, tid in misses[:show_misses]:
            print(f"  - ticket {tid}: missed {label}")
        if len(misses) > show_misses:
            print(f"  ... ({len(misses) - show_misses} more)")


def print_full_results(results: dict) -> None:
    """Print full precision/recall/F1 evaluation results."""
    print("=" * 72)
    print("PRECISION/RECALL/F1 EVALUATION")
    print("=" * 72)
    print()

    # Show warning if there were missing result files
    missing_files = results.get("missing_result_files", [])
    if missing_files:
        print(f"WARNING: {len(missing_files)} result files missing (treated as no predictions)")
        print(f"         Missing tickets: {missing_files[:10]}{'...' if len(missing_files) > 10 else ''}")
        print()

    m = results["micro"]
    print(f"Micro precision: {m['tp']}/{m['tp'] + m['fp']} = {m['precision']:.3f}")
    print(f"Micro recall:    {m['tp']}/{m['tp'] + m['fn']} = {m['recall']:.3f}")
    print(f"Micro F1:        {m['f1']:.3f}")
    print(f"Macro F1:        {results['macro_f1']:.3f}")
    print()
    print("Per-label (P / R / F1) with counts (TP, FP, FN, support):")
    for label in OUR_PATTERNS:
        lm = results["per_label"][label]
        print(f"  {label}:")
        print(f"    P={lm['precision']:.3f} R={lm['recall']:.3f} F1={lm['f1']:.3f}")
        print(f"    TP={lm['tp']}, FP={lm['fp']}, FN={lm['fn']}, support={lm['support']}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Evaluate LLM pattern detection results."
    )
    p.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing ticket_<id>.json model outputs",
    )
    p.add_argument(
        "--ground-truth",
        default=str(GROUND_TRUTH_CSV),
        help="Path to ground_truth_expected.csv",
    )
    p.add_argument(
        "--mode",
        choices=["recall-only", "full", "both"],
        default="both",
        help="Evaluation mode (default: both)",
    )
    p.add_argument(
        "--show-misses",
        type=int,
        default=50,
        help="Max missed-label rows to print in recall mode",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    gt_csv = Path(args.ground_truth)
    results_dir = Path(args.results_dir)

    if not gt_csv.exists():
        raise FileNotFoundError(f"Ground truth file not found: {gt_csv}")
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    print(f"Evaluation")
    print(f"- Ground truth: {gt_csv}")
    print(f"- Results dir:  {results_dir}")
    print()

    # Load expected labels
    expected = load_expected_labels(gt_csv)

    # Check for missing result files
    missing_files = [tid for tid in expected.keys() if not (results_dir / f"ticket_{tid}.json").exists()]
    if missing_files:
        print(f"Warning: Missing {len(missing_files)} result files (e.g., {missing_files[:5]})")
        print()

    # Run evaluations
    if args.mode in ("recall-only", "both"):
        recall_results = evaluate_recall_only(expected, results_dir, args.show_misses)
        print_recall_results(recall_results, args.show_misses)
        print()

    if args.mode in ("full", "both"):
        full_results = evaluate_full(expected, results_dir)
        print_full_results(full_results)


if __name__ == "__main__":
    main()

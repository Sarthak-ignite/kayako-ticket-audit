#!/usr/bin/env python3
"""
Summarize LLM results over the Phase 0 sample into a single CSV for easy review.

Inputs:
- results dir with ticket_<id>.json (e.g., data/poc/llm_results/gpt-5.2-v6-sample)
- data/poc/poc_sample.csv (ticket_id, vertical, pattern_vertical, source)
- optionally data/poc/poc_csv_metrics.csv (derived metrics from Full_Ticket_Data)

Outputs:
- a wide CSV containing per-ticket detections + reasoning + evidence, and a compact predicted_labels column.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from config import OUR_PATTERNS, POC_SAMPLE_CSV, POC_CSV_METRICS


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize ticket_<id>.json outputs into a single CSV.")
    p.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing ticket_<id>.json model outputs",
    )
    p.add_argument(
        "--sample-file",
        default=str(POC_SAMPLE_CSV),
        help="POC sample file (ticket_id, vertical, source, ...)",
    )
    p.add_argument(
        "--csv-metrics",
        default=str(POC_CSV_METRICS),
        help="Optional CSV metrics file to join (by Ticket ID)",
    )
    p.add_argument(
        "--out",
        default="data/poc/poc_llm_v6_sample_summary.csv",
        help="Output CSV path",
    )
    return p.parse_args()


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise RuntimeError(f"Empty CSV: {path}")
        return list(reader)


def _load_results(result_file: Path) -> dict[str, Any]:
    return json.loads(result_file.read_text())


def _as_bool(v: Any) -> bool:
    return v is True


def _join_evidence(ev: Any) -> str:
    if not isinstance(ev, list):
        return ""
    parts: list[str] = []
    for x in ev:
        s = str(x).strip()
        if s:
            parts.append(s.replace("\n", " ").strip())
    return " | ".join(parts)


def main() -> None:
    args = parse_args()
    results_dir = Path(args.results_dir)
    sample_file = Path(args.sample_file)
    csv_metrics_file = Path(args.csv_metrics)
    out_file = Path(args.out)

    if not results_dir.exists():
        raise FileNotFoundError(str(results_dir))
    if not sample_file.exists():
        raise FileNotFoundError(str(sample_file))

    sample_rows = _read_csv_rows(sample_file)
    sample_ticket_ids: list[int] = []
    for r in sample_rows:
        tid_raw = (r.get("ticket_id") or "").strip()
        if not tid_raw:
            continue
        sample_ticket_ids.append(int(tid_raw))

    metrics_by_tid: dict[int, dict[str, str]] = {}
    metrics_cols: list[str] = []
    if csv_metrics_file.exists():
        metrics_rows = _read_csv_rows(csv_metrics_file)
        if metrics_rows:
            metrics_cols = list(metrics_rows[0].keys())
        for r in metrics_rows:
            tid_raw = (r.get("Ticket ID") or "").strip()
            if not tid_raw:
                continue
            metrics_by_tid[int(tid_raw)] = r

    # Build output rows
    out_rows: list[dict[str, Any]] = []
    missing_results: list[int] = []
    label_counts = Counter()
    label_counts_by_vertical: dict[str, Counter] = defaultdict(Counter)

    for r in sample_rows:
        tid = int((r.get("ticket_id") or "0").strip() or "0")
        if tid == 0:
            continue
        rf = results_dir / f"ticket_{tid}.json"
        if not rf.exists():
            missing_results.append(tid)
            continue

        data = _load_results(rf)
        predicted: list[str] = []
        row_out: dict[str, Any] = {
            "ticket_id": tid,
            "vertical": r.get("vertical") or "",
            "source": r.get("source") or "",
            "pattern_vertical": r.get("pattern_vertical") or "",
            "_model": data.get("_model") or "",
        }

        for ptn in OUR_PATTERNS:
            block = data.get(ptn, {})
            detected = _as_bool(block.get("detected")) if isinstance(block, dict) else False
            reasoning = (block.get("reasoning") if isinstance(block, dict) else "") or ""
            evidence = _join_evidence(block.get("evidence") if isinstance(block, dict) else None)

            row_out[f"{ptn}__detected"] = "1" if detected else "0"
            row_out[f"{ptn}__reasoning"] = str(reasoning).replace("\n", " ").strip()
            row_out[f"{ptn}__evidence"] = evidence

            if detected:
                predicted.append(ptn)
                label_counts[ptn] += 1
                label_counts_by_vertical[row_out["vertical"]][ptn] += 1

        row_out["predicted_labels"] = json.dumps(predicted)

        # Optional join: CSV metrics
        if metrics_by_tid.get(tid):
            for k, v in metrics_by_tid[tid].items():
                # avoid collisions
                if k in row_out:
                    row_out[f"csv__{k}"] = v
                else:
                    row_out[k] = v

        out_rows.append(row_out)

    if missing_results:
        print(f"WARNING: Missing {len(missing_results)} result files (e.g. {missing_results[:10]}) in {results_dir}")
        print(f"         These tickets will be excluded from the summary.")

    # Write CSV
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Build stable columns:
    base_cols = ["ticket_id", "vertical", "source", "pattern_vertical", "_model", "predicted_labels"]
    pattern_cols: list[str] = []
    for ptn in OUR_PATTERNS:
        pattern_cols.extend([f"{ptn}__detected", f"{ptn}__reasoning", f"{ptn}__evidence"])
    extra_cols = [c for c in metrics_cols if c not in base_cols and c not in pattern_cols]
    csv_cols = base_cols + pattern_cols + extra_cols

    with out_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_cols, extrasaction="ignore")
        writer.writeheader()
        for row in out_rows:
            writer.writerow(row)

    # Print summary
    print("LLM results summary")
    print(f"- Results dir: {results_dir}")
    print(f"- Sample file: {sample_file} ({len(sample_ticket_ids)} tickets)")
    print(f"- Output CSV:  {out_file} ({len(out_rows)} rows)")
    print()
    print("Predicted label counts (tickets flagged):")
    for ptn in OUR_PATTERNS:
        print(f"- {ptn}: {label_counts[ptn]}")
    print()
    print("Predicted label counts by vertical:")
    for vertical in sorted(label_counts_by_vertical.keys()):
        c = label_counts_by_vertical[vertical]
        counts = ", ".join([f"{ptn}={c[ptn]}" for ptn in OUR_PATTERNS])
        print(f"- {vertical}: {counts}")


if __name__ == "__main__":
    main()



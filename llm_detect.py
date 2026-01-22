#!/usr/bin/env python3
"""
LLM Pattern Detection - Recall-first approach.

Goal: Maximize recall of expected ground-truth issues. False positives are acceptable.

Uses GPT-5.2 to analyze support tickets and detect 6 quality patterns:
- AI_QUALITY_FAILURES
- AI_WALL_LOOPING
- IGNORING_CONTEXT
- RESPONSE_DELAYS
- PREMATURE_CLOSURE
- P1_SEV1_MISHANDLING
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Optional

from config import (
    RAW_DIR,
    LLM_RESULTS_DIR,
    LLM_CONFIG,
    CSV_CONTEXT_FIELDS,
    OUR_PATTERNS,
    ensure_dirs,
    get_llm_output_dir,
)
from utils import (
    load_csv_context,
    load_ground_truth_ticket_ids,
    load_poc_sample_ticket_ids,
    format_interactions,
    format_csv_context,
    call_llm,
)


def get_all_raw_ticket_ids() -> list[int]:
    """
    Dynamically get all ticket IDs from the raw directory.
    This replaces the hardcoded ALL_TICKETS list.
    """
    raw_files = list(RAW_DIR.glob("ticket_*.json"))
    ticket_ids = []
    for f in raw_files:
        # Extract ticket ID from filename like "ticket_60005284.json"
        try:
            tid = int(f.stem.replace("ticket_", ""))
            ticket_ids.append(tid)
        except ValueError:
            continue
    return sorted(ticket_ids)


SYSTEM_PROMPT = """You are an expert support quality analyst evaluating Central Support performance.

This run is **recall-first**:
- We care primarily about NOT missing true issues that are present.
- False positives are acceptable for now.

Evidence rules:
- You may use customer-facing messages, private/internal notes, and the Structured CSV context.
- If evidence is weaker/indirect, you may still set detected=true but clearly state uncertainty.

Output requirements:
- Return JSON with all 6 patterns.
- For each: detected (boolean), reasoning (1-4 sentences), evidence (1-6 quotes).
- Evidence can include ticket quotes and/or CSV fields cited as: "CSV: <field>=<value>".
"""


USER_PROMPT_TEMPLATE = """# Support Ticket Analysis (Recall-first)

Ticket ID: {ticket_id}

## Structured CSV context (authoritative)
{csv_context}

## Interactions (chronological)
{interactions}

---

# How to decide (v6 recall-first)

For each pattern:
- Mark detected=true if there is **any reasonable evidence** that the pattern occurred.
- Do NOT require multiple independent signals.
- If you are unsure but suspect it happened, still mark detected=true and explain uncertainty.

Important: do not invent facts. Base decisions only on the text/notes and CSV context provided.

---

## 1) AI_QUALITY_FAILURES
AI (ATLAS/Hermes) quality is poor (wrong, misleading, filler, repetitive, not adapting, or promises not delivered).

## 2) AI_WALL_LOOPING
Customer experience suggests being stuck with AI / difficulty reaching a human / repetitive AI loop / customer asks for a human.

## 3) IGNORING_CONTEXT
Support ignores info already provided (within the ticket) or forces repetition / fails to acknowledge explicit prior context.

## 4) RESPONSE_DELAYS
Significant gaps in support response or customer complaints about waiting.
Concrete thresholds:
- Initial response time > 24 hours
- Gap between support responses > 48 hours (while customer is waiting)
- Total resolution time > 7 days (if customer actively engaged)
- Customer explicitly complains about waiting/delays
CSV fields: initialResponseTime, resolutionTime, timeSpentOpenL1, timeSpentOpenL2 (values in hours/days).

## 5) PREMATURE_CLOSURE
Ticket closed/auto-closed or closure-threat while customer still needs help (use text + CSV Status/Ticket Closed).

## 6) P1_SEV1_MISHANDLING
High-severity/outage treated like routine troubleshooting; missed escalation or slow handling.
P1/SEV1 indicators: outage, production down, critical/urgent, "sev1"/"p1", all users affected, business/revenue impact.
Mishandling criteria:
- P1/SEV1 ticket with initial response > 4 hours
- P1/SEV1 ticket taking > 24 hours to resolve
- Generic troubleshooting steps instead of immediate escalation
- No acknowledgment of severity/urgency
- Treating outage like routine support ticket

---

# Output format
Return JSON with keys:
AI_QUALITY_FAILURES, AI_WALL_LOOPING, IGNORING_CONTEXT, RESPONSE_DELAYS, PREMATURE_CLOSURE, P1_SEV1_MISHANDLING

Each key maps to:
{{
  "detected": true/false,
  "reasoning": "...",
  "evidence": ["quote 1", "quote 2"]
}}
"""


def analyze_ticket(
    ticket_id: int,
    csv_context_by_ticket: dict[int, dict[str, Any]],
    raw_dir: Path = RAW_DIR,
) -> Optional[dict]:
    """
    Analyze a single ticket using the LLM.

    Returns the LLM response dict with pattern detections, or None if failed.
    """
    raw_file = raw_dir / f"ticket_{ticket_id}.json"
    if not raw_file.exists():
        return None

    interactions_text = format_interactions(raw_file)
    csv_context = format_csv_context(ticket_id, csv_context_by_ticket)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticket_id=ticket_id,
        csv_context=csv_context,
        interactions=interactions_text,
    )

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run LLM pattern detection on support tickets."
    )
    p.add_argument(
        "--ticket-set",
        choices=["all", "ground_truth", "sample"],
        default="ground_truth",
        help="Which ticket IDs to run (default: ground_truth).",
    )
    p.add_argument(
        "--outdir",
        default=None,
        help="Output directory for results (default: data/poc/llm_results/gpt-5.2-v6).",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if output file already exists.",
    )
    p.add_argument(
        "--tickets",
        type=str,
        default=None,
        help="Comma-separated list of specific ticket IDs to process.",
    )
    return p.parse_args()


def main() -> None:
    ensure_dirs()
    args = parse_args()

    # Determine output directory
    if args.outdir:
        output_dir = Path(args.outdir)
    else:
        output_dir = get_llm_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load CSV context
    csv_context_by_ticket = load_csv_context()

    # Determine which tickets to process
    if args.tickets:
        ticket_ids = [int(x.strip()) for x in args.tickets.split(",")]
    elif args.ticket_set == "ground_truth":
        ticket_ids = load_ground_truth_ticket_ids()
    elif args.ticket_set == "sample":
        ticket_ids = load_poc_sample_ticket_ids()
    else:
        # "all" - dynamically get all tickets from raw directory
        ticket_ids = get_all_raw_ticket_ids()
        if not ticket_ids:
            print("ERROR: No raw ticket files found in", RAW_DIR)
            print("       Run 1_fetch_tickets.py first to fetch tickets.")
            return

    print(f"LLM Pattern Detection")
    print(f"- Model: {LLM_CONFIG['model']}")
    print(f"- Output: {output_dir}")
    print(f"- Tickets: {len(ticket_ids)}")
    print("=" * 72)

    # Filter to tickets that need processing
    to_process = []
    for tid in ticket_ids:
        out = output_dir / f"ticket_{tid}.json"
        if args.force or not out.exists():
            to_process.append(tid)

    print(f"Already done: {len(ticket_ids) - len(to_process)}")
    print(f"To process:   {len(to_process)}")
    print()

    ok = 0
    empty = 0
    malformed = 0
    for i, tid in enumerate(to_process):
        print(f"[{i+1}/{len(to_process)}] {tid}...", end=" ", flush=True)
        result = analyze_ticket(tid, csv_context_by_ticket)
        if result is None:
            # analyze_ticket returned None (raw file missing or LLM call failed)
            print("EMPTY (no result)")
            empty += 1
        elif not any(p in result for p in OUR_PATTERNS):
            # LLM returned a result but it doesn't have any pattern keys
            # This is malformed - don't save it
            print("MALFORMED (missing pattern keys)")
            malformed += 1
        else:
            result["_model"] = f"{LLM_CONFIG['model']}-v6"
            result["_ticket_id"] = tid
            (output_dir / f"ticket_{tid}.json").write_text(json.dumps(result, indent=2))
            print("OK")
            ok += 1
        time.sleep(LLM_CONFIG["call_delay"])

    print()
    print("=" * 72)
    print(f"Complete: {ok} success, {empty} failed, {malformed} malformed")
    print(f"Total results files: {len(list(output_dir.glob('ticket_*.json')))}")


if __name__ == "__main__":
    main()

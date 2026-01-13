#!/usr/bin/env python3
"""
LLM Pattern Detection v6 - Recall-first

Goal: maximize recall of the expected ground-truth issues. False positives are acceptable.

Key changes vs v5:
- Recall-first rubric: mark detected=true if there is any reasonable evidence (1+ signal),
  including private/internal notes and CSV context.
- Looser thresholds and less guarding against FP.
- Explicit instruction: "when in doubt, detect=true and explain uncertainty".
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
import openai

load_dotenv()


ALL_TICKETS = [
    60005284, 60005331, 60011782, 60018792, 60069509, 60073150, 60073892, 60078199, 60082637, 60094192,
    60098171, 60098583, 60100448, 60101543, 60144719, 60149875, 60163212, 60164071, 60166415, 60169826,
    60177804, 60185126, 60185905, 60186930, 60190547, 60193443, 60195349, 60196166, 60196360, 60198743,
    60201836, 60209095, 60209553, 60210541, 60211680, 60214613, 60218313, 60220499, 60220701, 60225231,
    60226631, 60227783, 60230003, 60230438, 60231299, 60231851, 60232130, 60234621, 60237327, 60238295,
    60238457, 60239883, 60240989, 60241392, 60241518, 60242814, 60247476, 60252140, 60252864, 60256173,
    60258400,
]

RAW_DIR = Path("data/poc/raw")
DEFAULT_OUTPUT_DIR = Path("data/poc/llm_results/gpt-5.2-v6-gt")

CSV_UNIVERSE_FILE = Path("Full_Ticket_Data_1767638152669.csv")
CSV_CONTEXT_FIELDS = [
    "Brand",
    "Product",
    "Status",
    "Level Solved",
    "Ticket Created",
    "Ticket Updated",
    "Ticket Solved",
    "Ticket Closed",
    "First_L1_Agent_ID",
    "firstL2AgentId",
    "timeSpentOpenL1",
    "timeSpentOpenL2",
    "initialResponseTime",
    "resolutionTime",
]

MODEL_NAME = "gpt-5.2"
MAX_COMPLETION_TOKENS = 1800
REASONING_EFFORT = "medium"
MAX_RETRIES = 2

CSV_CONTEXT_BY_TICKET: dict[int, dict[str, Any]] = {}


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
Meaningful response gaps or customer complaints about waiting; CSV long durations can support this.

## 5) PREMATURE_CLOSURE
Ticket closed/auto-closed or closure-threat while customer still needs help (use text + CSV Status/Ticket Closed).

## 6) P1_SEV1_MISHANDLING
High-severity/outage treated like routine troubleshooting; missed escalation or slow handling during urgent impact.

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


def _clean_csv_value(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    return s


def load_csv_context() -> dict[int, dict[str, Any]]:
    """Load a compact per-ticket context map from the authoritative CSV universe."""
    if not CSV_UNIVERSE_FILE.exists():
        return {}

    out: dict[int, dict[str, Any]] = {}
    with open(CSV_UNIVERSE_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return {}
        fields = set(reader.fieldnames)
        use_fields = [c for c in CSV_CONTEXT_FIELDS if c in fields]
        if "Ticket ID" not in fields:
            raise RuntimeError("Full_Ticket_Data_1767638152669.csv is missing required 'Ticket ID' column")

        for row in reader:
            tid_raw = row.get("Ticket ID")
            if tid_raw is None:
                continue
            try:
                tid = int(str(tid_raw).strip())
            except Exception:
                continue
            ctx: dict[str, Any] = {}
            for k in use_fields:
                v = _clean_csv_value(row.get(k))
                if v is not None:
                    ctx[k] = v
            out[tid] = ctx
    return out


def format_csv_context(ticket_id: int) -> str:
    ctx = CSV_CONTEXT_BY_TICKET.get(ticket_id) or {}
    if not ctx:
        return "(not found in CSV universe)"
    lines = []
    for k in CSV_CONTEXT_FIELDS:
        if k in ctx:
            lines.append(f"- {k}: {ctx[k]}")
    return "\n".join(lines) if lines else "(no non-empty CSV fields)"


def _client() -> openai.OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment")
    return openai.OpenAI(api_key=api_key)


def load_ground_truth_ticket_ids() -> list[int]:
    gt_file = Path("data/poc/ground_truth_expected.csv")
    if not gt_file.exists():
        raise FileNotFoundError(f"{gt_file} not found. Run: python3 6_build_ground_truth.py")

    ids: list[int] = []
    with gt_file.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if "Ticket ID" not in (reader.fieldnames or []):
            raise RuntimeError("ground_truth_expected.csv missing 'Ticket ID' column")
        for row in reader:
            tid_raw = row.get("Ticket ID")
            if not tid_raw:
                continue
            try:
                ids.append(int(str(tid_raw).strip()))
            except Exception:  # noqa: BLE001
                continue
    return sorted(set(ids))


def format_interactions(raw_file: Path, max_chars: int = 26000) -> str:
    with open(raw_file, "r") as f:
        ticket_data = json.load(f)

    ticket = (ticket_data.get("payload") or {}).get("ticket") or {}
    interactions = ticket.get("interactions") or []

    requester = (ticket.get("metadata") or {}).get("requester") or {}
    requester_name = requester.get("full_name") or "Unknown Customer"

    lines = [f"Customer: {requester_name}\n"]

    # Stored reverse-chronological; we want chronological.
    interactions = list(reversed(interactions))

    total = 0
    for inter in interactions:
        if not (isinstance(inter, list) and len(inter) >= 2):
            continue
        ts, text = inter[0], inter[1]
        if not isinstance(text, str):
            text = str(text)
        if len(text) > 2200:
            text = text[:2000] + "\n...[truncated]..."

        chunk = f"[{ts}]\n{text}\n\n---\n"
        if total + len(chunk) > max_chars:
            lines.append("\n...[earlier interactions truncated]...\n")
            break
        lines.append(chunk)
        total += len(chunk)

    return "".join(lines)


def call_gpt52(ticket_id: int) -> Optional[dict]:
    raw_file = RAW_DIR / f"ticket_{ticket_id}.json"
    if not raw_file.exists():
        return None

    interactions_text = format_interactions(raw_file)
    csv_context = format_csv_context(ticket_id)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticket_id=ticket_id,
        csv_context=csv_context,
        interactions=interactions_text,
    )

    last_err: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = _client().chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                reasoning_effort=REASONING_EFFORT,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            if not content or not content.strip():
                last_err = RuntimeError("empty_content")
                time.sleep(0.6 * (attempt + 1))
                continue
            try:
                return json.loads(content)
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(0.6 * (attempt + 1))
                continue
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.8 * (attempt + 1))
            continue

    _ = last_err
    return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run gpt-5.2 prompt v6 (recall-first) pattern detection.")
    p.add_argument(
        "--ticket-set",
        choices=["all", "ground_truth"],
        default="ground_truth",
        help="Which ticket IDs to run.",
    )
    p.add_argument(
        "--outdir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory for per-ticket JSON results.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if output file already exists.",
    )
    return p.parse_args()


def main() -> None:
    global CSV_CONTEXT_BY_TICKET  # noqa: PLW0603
    CSV_CONTEXT_BY_TICKET = load_csv_context()

    args = parse_args()
    output_dir = Path(args.outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.ticket_set == "ground_truth":
        ticket_ids = load_ground_truth_ticket_ids()
    else:
        ticket_ids = list(ALL_TICKETS)

    print(f"Processing {len(ticket_ids)} tickets with v6 prompt -> {output_dir}")
    print("=" * 72)

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
    for i, tid in enumerate(to_process):
        print(f"[{i+1}/{len(to_process)}] {tid}...", end=" ", flush=True)
        result = call_gpt52(tid)
        if result:
            result["_model"] = "gpt-5.2-v6"
            result["_ticket_id"] = tid
            (output_dir / f"ticket_{tid}.json").write_text(json.dumps(result, indent=2))
            print("OK")
            ok += 1
        else:
            print("EMPTY")
            empty += 1
        time.sleep(0.35)

    print()
    print("=" * 72)
    print(f"Complete: {ok} success, {empty} failed")
    print(f"Total results files: {len(list(output_dir.glob('ticket_*.json')))}")


if __name__ == "__main__":
    main()



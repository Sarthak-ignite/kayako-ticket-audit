#!/usr/bin/env python3
"""
LLM Pattern Detection v5 - Balanced for F1 (reduce FP without killing recall)

Key changes vs v4:
- Public-vs-private weighting: private/internal notes cannot be the ONLY evidence.
- Per-pattern decision thresholds: require either 1 "strong" signal or 2+ "weak" signals.
- Stronger guards against common FP modes:
  - AI_QUALITY_FAILURES: generic openers + doc links alone are NOT failures.
  - IGNORING_CONTEXT: lack of acknowledgement alone is NOT enough.
  - P1/SEV1: requires explicit severity/outage language OR multi-user impact + mishandling.
  - PREMATURE_CLOSURE: requires explicit closure/auto-closure event language AND unmet expectation.
- Retry logic for empty/invalid JSON responses.
"""

import json
import os
import time
import csv
import argparse
from pathlib import Path
from typing import Optional, Any

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
DEFAULT_OUTPUT_DIR = Path("data/poc/llm_results/gpt-5.2-v5")

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


SYSTEM_PROMPT = """You are an expert support quality analyst evaluating Central Support performance.

Be accurate and evidence-based. Do NOT assume facts not present in the ticket text.
Your output will be used to compute precision/recall, so avoid over-flagging.

Important:
- Prefer customer-facing messages (\"commented publicly\") over internal notes (\"commented privately\").
- A private/internal note can SUPPORT a finding, but should not be the ONLY evidence for detected=true.
- For each detected pattern, include quotes from the ticket as evidence.
- You may also use the provided \"Structured CSV context\" fields (if present) as authoritative structured signals (e.g., Status, Ticket Closed, timeSpentOpenL1/L2).
  When you use CSV context, cite it in evidence as: \"CSV: <field>=<value>\"."""


USER_PROMPT_TEMPLATE = """# Support Ticket Analysis

Ticket ID: {ticket_id}

## Structured CSV context (authoritative)
{csv_context}

## Interactions (chronological)
{interactions}

---

# How to decide (v5)

For each pattern, mark detected=true only if you have either:
- **1 STRONG signal**, OR
- **2+ WEAK signals** (from customer-facing content).

If evidence exists only in private/internal notes, keep detected=false (or add public evidence too).

When you mark detected=true, include **at least 2 evidence quotes**, unless a single quote is a STRONG signal by itself.

---

## 1) AI_QUALITY_FAILURES
AI (ATLAS/Hermes) quality is poor (wrong, broken, misleading, or empty filler).

**STRONG signals (any one is enough):**
- Broken template: AI addresses itself (e.g., \"Dear ATLAS\") or obviously garbled output.
- Customer explicitly says AI was wrong / useless / hallucinating.
- AI provides clearly incorrect guidance AND customer (or later messages) correct it.
- AI promises a specific follow-up (\"I will send X\", \"we will share patch/logs\") AND later context shows it was not delivered.

**WEAK signals (need 2+):**
- AI sends generic boilerplate repeatedly without progressing.
- AI response is mostly links + asks for info but does not engage with described symptoms at all.
- AI repeats the same generic troubleshooting despite customer saying it didn't help.

**Do NOT count as failure by itself:**
- AI asking clarifying questions.
- AI requesting logs/screenshots once.
- AI sharing relevant documentation links.
- Internal AI status sync notes.

---

## 2) AI_WALL_LOOPING
Customer stuck with AI / can't reach a human / repetitive AI loop.

**STRONG signals:**
- Customer asks for human/agent AND receives 2+ subsequent AI responses (no human) after that request.
- Customer says \"I already provided that\" / \"I already tried that\" and AI asks for the same thing again.

**WEAK signals (need 2+):**
- 3+ consecutive AI customer-facing messages with no human response.
- AI creates a new ticket while customer explicitly says they already have one (and keeps pushing the flow).
- Customer expresses frustration specifically about interacting with AI.

**Do NOT detect if:**
- Customer asks for a human and a human responds next.

---

## 3) IGNORING_CONTEXT
Support ignores info the customer already provided (within the ticket) or forces repetition.

**STRONG signals:**
- Customer explicitly says they already shared X (logs/screenshot/steps) AND support asks for X again.
- Customer references previous ticket/context AND support continues as if it’s new without acknowledging.
- Same exact troubleshooting request repeated after customer said it was already done.

**WEAK signals (need 2+):**
- Customer says \"as I mentioned\" / \"see above\" / \"already explained\".
- Customer shares files/logs and later asks why nobody reviewed them (and no acknowledgement appears).

**Do NOT count as ignoring by itself:**
- Support asking for additional/different info.
- Lack of acknowledgement alone (without a repeat request or explicit customer complaint).

---

## 4) RESPONSE_DELAYS
Meaningful response gaps.

**STRONG signals:**
- Customer says they’ve been waiting days / asks \"any update\" after a long silence.
- Support explicitly apologizes for delay.
- CSV shows very large response/resolution metrics (e.g., initialResponseTime/resolutionTime/timeSpentOpenL1/L2) AND there is at least one customer-facing sign of waiting/impact.

**WEAK signals (need 2+):**
- Two separate gaps of >= 3 calendar days between customer message and next staff reply.
- One gap >= 5 calendar days between customer message and next staff reply.
- CSV shows timeSpentOpenL1 or timeSpentOpenL2 >= 3 days (>= 72 hours) AND the interaction log shows at least one customer-facing follow-up.

**Do NOT detect if:**
- The gap is due to customer not responding.
- Only internal/private notes occur during the gap.

---

## 5) PREMATURE_CLOSURE
Ticket effectively closed/auto-closed while customer still waiting or before resolution.

Use either text evidence OR the Structured CSV context (Status/Ticket Closed) as closure signal.

**STRONG signals:**
- A message indicates the case is closed / will be closed / auto-closed AND customer had an unresolved pending request.
- \"This ticket will stay open for one week unless...\" followed by text indicating closure (or an explicit closure notice).
- CSV shows Status indicates closed/solved (or Ticket Closed is present) AND there is customer-facing evidence of an unresolved request or waiting.

**WEAK signals (need 2+):**
- Closure warning language + support promised a follow-up that never appears in later messages.
- Customer says they are still waiting for promised info and then closure warning/notice appears.
- CSV shows Ticket Closed is present + customer says keep it open / still waiting / unresolved.

**Do NOT detect if:**
- Customer requests closure.
- Closure/auto-closure is not mentioned anywhere in the text.

---

## 6) P1_SEV1_MISHANDLING
High-severity issue handled like normal troubleshooting.

**STRONG signals:**
- Explicit P1/SEV1/critical/outage/production-down language AND support responds with generic environment checks (browser/cache/VPN/firewall) without escalation.

**WEAK signals (need 2+):**
- Multi-user impact (\"all users\", \"entire team\", \"multiple customers\") + urgency language (\"urgent\", \"blocking business\") + support stays in generic troubleshooting for a long time.
- Customer says it’s recurring/systemic + support treats as isolated and does not escalate.

**Do NOT detect if:**
- Only single-user impact is described without outage/severity cues.
- Support quickly escalates / creates incident / engages engineering.

---

# Output format
Return JSON with all 6 patterns. For each:
- detected: boolean
- reasoning: 1–3 sentences, explicit about what you saw
- evidence: list of 1–4 quotes from the interactions (prefer public)
"""

CSV_CONTEXT_BY_TICKET: dict[int, dict[str, Any]] = {}


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


def load_ground_truth_ticket_ids() -> list[int]:
    """
    Ticket IDs for evaluation seeds, after universe-filtering + overrides.
    """
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run gpt-5.2 prompt v5 pattern detection.")
    p.add_argument(
        "--ticket-set",
        choices=["all", "ground_truth"],
        default="all",
        help="Which ticket IDs to run: hardcoded ALL_TICKETS, or ground truth set from data/poc/ground_truth_expected.csv",
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

    # Exhausted retries
    _ = last_err
    return None


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

    print(f"Processing {len(ticket_ids)} tickets with v5 prompt -> {output_dir}")
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
            result["_model"] = "gpt-5.2-v5"
            result["_ticket_id"] = tid
            (output_dir / f"ticket_{tid}.json").write_text(json.dumps(result, indent=2))
            print("OK")
            ok += 1
        else:
            print("EMPTY")
            empty += 1
        time.sleep(0.4)

    print()
    print("=" * 72)
    print(f"Complete: {ok} success, {empty} failed")
    print(f"Total results files: {len(list(output_dir.glob('ticket_*.json')))}")


if __name__ == "__main__":
    main()




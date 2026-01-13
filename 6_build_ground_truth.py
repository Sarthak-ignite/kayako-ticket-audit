#!/usr/bin/env python3
"""
Build a filtered / corrected ground-truth dataset for Phase 0 scoring.

Inputs:
- IgniteTech_Khoros_GFI - Central Support Issues we see in tickets - Patterns.csv
- Full_Ticket_Data_1767638152669.csv  (authoritative ticket universe)
- data/poc/ground_truth_overrides.json (manual exclusions + keep/remove/add)

Outputs:
- data/poc/ground_truth_expected.csv
- data/poc/ground_truth_expected.json
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent

PATTERNS_FILE = REPO_ROOT / "IgniteTech_Khoros_GFI - Central Support Issues we see in tickets - Patterns.csv"
UNIVERSE_FILE = REPO_ROOT / "Full_Ticket_Data_1767638152669.csv"
OVERRIDES_FILE = REPO_ROOT / "data/poc/ground_truth_overrides.json"

OUT_CSV = REPO_ROOT / "data/poc/ground_truth_expected.csv"
OUT_JSON = REPO_ROOT / "data/poc/ground_truth_expected.json"

OUR_PATTERNS = [
    "AI_QUALITY_FAILURES",
    "AI_WALL_LOOPING",
    "IGNORING_CONTEXT",
    "RESPONSE_DELAYS",
    "PREMATURE_CLOSURE",
    "P1_SEV1_MISHANDLING",
]

# Fuzzy map from pattern text in Patterns.csv -> consolidated label
PATTERN_MAPPING = {
    "hermes answers are just a filler": "AI_QUALITY_FAILURES",
    "ai (atlas/hermes) provides wrong information": "AI_QUALITY_FAILURES",
    "ai is promissing": "AI_QUALITY_FAILURES",
    "customer is expressing frustation": "AI_QUALITY_FAILURES",
    "support agents are not checking past similar tickets": "IGNORING_CONTEXT",
    "after customer provided all the information": "IGNORING_CONTEXT",
    "feedback on shared patch": "IGNORING_CONTEXT",
    "with multiple issue reported in single ticket": "IGNORING_CONTEXT",
    "support does not recognize recurring issue patterns": "IGNORING_CONTEXT",
    "customer get's locked in an \"ai wall\"": "AI_WALL_LOOPING",
    "ai is requesting same information": "AI_WALL_LOOPING",
    "tickets being closed  after 7 days": "PREMATURE_CLOSURE",
    "chat conversations are closed prematuraly": "PREMATURE_CLOSURE",
    "ai resolution is high because customer give up": "PREMATURE_CLOSURE",
    "slow ai/agent resposnes with gaps": "RESPONSE_DELAYS",
    "ticket automation malfunctioning": "RESPONSE_DELAYS",
    "ai/atlas responds to sev1/p1 outages with generic": "P1_SEV1_MISHANDLING",
    "support consistently begins with customer environment investigation": "P1_SEV1_MISHANDLING",
    "sev1/p1 platform issues spend multiple days": "P1_SEV1_MISHANDLING",
}

TICKET_ID_RE = re.compile(r"\b\d{6,9}\b")


def _clean(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    return s


def map_pattern_to_label(pattern_text: str) -> Optional[str]:
    p = (pattern_text or "").strip().lower()
    if not p:
        return None
    for needle, label in PATTERN_MAPPING.items():
        if needle in p:
            return label
    return None


def extract_ticket_ids(cell: Any) -> list[int]:
    s = _clean(cell)
    if not s:
        return []
    return [int(x) for x in TICKET_ID_RE.findall(s)]


def load_overrides() -> tuple[set[int], dict[int, dict[str, Any]]]:
    if not OVERRIDES_FILE.exists():
        return set(), {}
    data = json.loads(OVERRIDES_FILE.read_text())
    excluded = {int(x["ticket_id"]) for x in data.get("excluded_seed_tickets", [])}
    overrides = {int(x["ticket_id"]): x for x in data.get("overrides", [])}
    return excluded, overrides


def main() -> None:
    if not PATTERNS_FILE.exists():
        raise FileNotFoundError(str(PATTERNS_FILE))
    if not UNIVERSE_FILE.exists():
        raise FileNotFoundError(str(UNIVERSE_FILE))

    excluded, overrides = load_overrides()

    # Universe (authoritative)
    universe_cols = [
        "Ticket ID",
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
    universe_header = pd.read_csv(UNIVERSE_FILE, nrows=0).columns.tolist()
    universe_df = pd.read_csv(
        UNIVERSE_FILE,
        low_memory=False,
        usecols=[c for c in universe_cols if c in universe_header],
    )
    universe_df["Ticket ID"] = universe_df["Ticket ID"].astype(int)
    universe = set(universe_df["Ticket ID"].tolist())
    universe_by_tid = {int(r["Ticket ID"]): r for _, r in universe_df.iterrows()}

    # Patterns.csv (two-row header)
    patterns_df = pd.read_csv(PATTERNS_FILE, header=[0, 1])
    if patterns_df.shape[1] < 2:
        raise RuntimeError("Patterns.csv did not parse as expected (needs multi-row header).")

    expected: dict[int, set[str]] = defaultdict(set)
    unmapped_patterns: Counter[str] = Counter()

    for _, row in patterns_df.iterrows():
        pattern_text = _clean(row.iloc[0]) or ""
        label = map_pattern_to_label(pattern_text)
        if not label:
            if pattern_text.strip():
                unmapped_patterns[pattern_text.strip()] += 1
            continue

        for col in patterns_df.columns[1:]:
            for tid in extract_ticket_ids(row[col]):
                expected[tid].add(label)

    # Filter to universe + apply explicit exclusions
    expected = {tid: set(labels) for tid, labels in expected.items() if tid in universe and tid not in excluded}

    # Apply overrides (keep/remove/add). If an override references a ticket in-universe
    # that wasn't seeded by Patterns.csv, we'll still include it with an empty base.
    for tid, rule in overrides.items():
        if tid not in universe:
            continue
        if tid in excluded:
            continue
        expected.setdefault(tid, set())
        if "keep" in rule:
            expected[tid] = set(rule["keep"])
        if "remove" in rule:
            expected[tid] -= set(rule["remove"])
        if "add" in rule:
            expected[tid] |= set(rule["add"])

    # Build output
    rows = []
    for tid in sorted(expected.keys()):
        base = dict(universe_by_tid.get(tid, {}))
        out = {
            "Ticket ID": tid,
            "Expected Labels": json.dumps(sorted(expected[tid])),
        }
        # include a few universe fields if present
        for k in [
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
        ]:
            if k in base:
                out[k] = base[k]
        for p in OUR_PATTERNS:
            out[p] = 1 if p in expected[tid] else 0
        rows.append(out)

    out_df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)

    payload = {
        "notes": {
            "source_patterns_csv": str(PATTERNS_FILE.name),
            "source_universe_csv": str(UNIVERSE_FILE.name),
            "source_overrides_json": str(OVERRIDES_FILE.as_posix()),
            "excluded_seed_tickets_count": len(excluded),
            "tickets_after_filtering": len(expected),
            "our_patterns": OUR_PATTERNS,
        },
        "expected_by_ticket": {str(tid): sorted(list(labels)) for tid, labels in expected.items()},
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2))

    counts = Counter()
    for labels in expected.values():
        counts.update(labels)

    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Tickets in filtered ground truth: {len(expected)}")
    print("Counts by label:")
    for p in OUR_PATTERNS:
        print(f"- {p}: {counts.get(p, 0)}")

    if unmapped_patterns:
        print("\nWARNING: Unmapped Patterns.csv rows (ignored):")
        for k, v in unmapped_patterns.most_common(20):
            print(f"- ({v}x) {k}")

    # Helpful diagnostics: overrides/exclusions referring to tickets outside the universe.
    orphan_excluded = sorted([tid for tid in excluded if tid not in universe])
    orphan_overrides = sorted([tid for tid in overrides.keys() if tid not in universe])
    if orphan_excluded:
        print("\nWARNING: excluded_seed_tickets not in universe (already excluded by universe filter):")
        for tid in orphan_excluded[:50]:
            print(f"- {tid}")
        if len(orphan_excluded) > 50:
            print(f"... ({len(orphan_excluded) - 50} more)")

    if orphan_overrides:
        print("\nWARNING: overrides not in universe (won't affect scoring):")
        for tid in orphan_overrides[:50]:
            print(f"- {tid}")
        if len(orphan_overrides) > 50:
            print(f"... ({len(orphan_overrides) - 50} more)")


if __name__ == "__main__":
    main()



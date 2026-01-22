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
from typing import Any, Optional

import pandas as pd

from config import (
    PATTERNS_CSV as PATTERNS_FILE,
    FULL_TICKET_DATA_CSV as UNIVERSE_FILE,
    GROUND_TRUTH_OVERRIDES as OVERRIDES_FILE,
    GROUND_TRUTH_CSV as OUT_CSV,
    GROUND_TRUTH_JSON as OUT_JSON,
    OUR_PATTERNS,
    PATTERN_TEXT_MAPPING as PATTERN_MAPPING,
    ensure_dirs,
)

TICKET_ID_RE = re.compile(r"\b\d{6,9}\b")


def _clean(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    return s


def map_pattern_to_label(pattern_text: str) -> Optional[str]:
    """
    Map a pattern description text to a canonical label.

    Uses longest-match-first to avoid ambiguity when multiple needles
    could match (e.g., "ai" vs "ai wall"). Sorted by needle length
    descending ensures more specific patterns match first.

    Returns None if no match found.
    """
    p = (pattern_text or "").strip().lower()
    if not p:
        return None

    # Sort by needle length descending (longest match first) for determinism
    sorted_mappings = sorted(PATTERN_MAPPING.items(), key=lambda x: len(x[0]), reverse=True)

    for needle, label in sorted_mappings:
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
    #
    # Semantics:
    # - "keep": Replace entire label set (mutually exclusive with remove/add)
    # - "remove": Remove labels from current set
    # - "add": Add labels to current set
    #
    # Validation: "keep" cannot be combined with "remove" or "add"
    override_warnings: list[str] = []

    for tid, rule in overrides.items():
        if tid not in universe:
            continue
        if tid in excluded:
            continue

        has_keep = "keep" in rule
        has_remove = "remove" in rule
        has_add = "add" in rule

        # Validate: "keep" is mutually exclusive with "remove"/"add"
        if has_keep and (has_remove or has_add):
            override_warnings.append(
                f"Ticket {tid}: 'keep' combined with 'remove'/'add' - using 'keep' only"
            )
            has_remove = False
            has_add = False

        expected.setdefault(tid, set())

        if has_keep:
            # Validate labels in "keep"
            invalid_labels = set(rule["keep"]) - set(OUR_PATTERNS)
            if invalid_labels:
                override_warnings.append(
                    f"Ticket {tid}: invalid labels in 'keep': {invalid_labels}"
                )
            expected[tid] = set(rule["keep"]) & set(OUR_PATTERNS)
        else:
            if has_remove:
                expected[tid] -= set(rule["remove"])
            if has_add:
                # Validate labels in "add"
                invalid_labels = set(rule["add"]) - set(OUR_PATTERNS)
                if invalid_labels:
                    override_warnings.append(
                        f"Ticket {tid}: invalid labels in 'add': {invalid_labels}"
                    )
                expected[tid] |= set(rule["add"]) & set(OUR_PATTERNS)

    if override_warnings:
        print(f"\nWARNING: Override validation issues ({len(override_warnings)}):")
        for w in override_warnings[:20]:
            print(f"  - {w}")
        if len(override_warnings) > 20:
            print(f"  ... ({len(override_warnings) - 20} more)")

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



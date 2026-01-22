"""
Text formatting utilities for the Kayako ticket analysis pipeline.

Consolidates format_interactions() and format_csv_context() from v2-v6 scripts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config import CSV_CONTEXT_FIELDS, INTERACTION_LIMITS


def clean_csv_value(v: Any) -> Optional[str]:
    """Clean a CSV value, returning None for empty/null values."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    return s


def format_csv_context(
    ticket_id: int,
    csv_context_by_ticket: dict[int, dict[str, Any]],
    fields: Optional[list[str]] = None,
) -> str:
    """
    Format CSV context for a ticket into a string for LLM prompts.

    Args:
        ticket_id: The ticket ID to look up
        csv_context_by_ticket: Dict mapping ticket_id -> {field: value}
        fields: Optional list of fields to include (defaults to CSV_CONTEXT_FIELDS)

    Returns:
        Formatted string with CSV field values, or error message if not found.
    """
    ctx = csv_context_by_ticket.get(ticket_id) or {}
    if not ctx:
        return "(not found in CSV universe)"

    use_fields = fields or CSV_CONTEXT_FIELDS
    lines = []
    for k in use_fields:
        if k in ctx:
            lines.append(f"- {k}: {ctx[k]}")
    return "\n".join(lines) if lines else "(no non-empty CSV fields)"


def _format_single_interaction(
    inter: list,
    max_per: int,
    trunc_at: int,
) -> Optional[str]:
    """Format a single interaction, returning None if invalid."""
    if not (isinstance(inter, list) and len(inter) >= 2):
        return None
    ts, text = inter[0], inter[1]
    if not isinstance(text, str):
        text = str(text)
    if len(text) > max_per:
        text = text[:trunc_at] + "\n...[truncated]..."
    return f"[{ts}]\n{text}\n\n---\n"


def _smart_select_interactions(
    formatted: list[str],
    max_chars: int,
    first_pct: float = 0.20,
    last_pct: float = 0.60,
) -> tuple[list[str], bool]:
    """
    Smart selection of interactions to fit within budget.

    Strategy: Prioritize RECENT interactions (most important for pattern detection)
    while keeping some early context.

    Allocation:
    - First 20%: Early context (ticket opening, initial problem statement)
    - Last 60%: Recent interactions (closure, delays, resolution attempts)
    - Middle 20%: Sampled if space allows

    Returns:
        (selected_chunks, was_truncated)
    """
    if not formatted:
        return [], False

    # Calculate total size
    total_size = sum(len(c) for c in formatted)
    if total_size <= max_chars:
        return formatted, False

    n = len(formatted)

    # Calculate how many interactions for each section
    n_first = max(1, int(n * first_pct))
    n_last = max(1, int(n * last_pct))

    # Ensure we don't overlap (for small interaction counts)
    if n_first + n_last >= n:
        # Just take all if overlap
        n_first = n // 3
        n_last = n - n_first

    # Get first and last sections
    first_section = formatted[:n_first]
    last_section = formatted[n - n_last:] if n_last > 0 else []

    # Calculate sizes
    first_size = sum(len(c) for c in first_section)
    last_size = sum(len(c) for c in last_section)

    # If first + last already exceeds budget, prioritize last (recent)
    if first_size + last_size > max_chars:
        # Give 70% budget to last section, 30% to first
        last_budget = int(max_chars * 0.70)
        first_budget = max_chars - last_budget

        # Truncate first section to fit budget
        truncated_first = []
        first_used = 0
        for chunk in first_section:
            if first_used + len(chunk) <= first_budget:
                truncated_first.append(chunk)
                first_used += len(chunk)
            else:
                break

        # Truncate last section from the END (keep most recent)
        truncated_last = []
        last_used = 0
        for chunk in reversed(last_section):
            if last_used + len(chunk) <= last_budget:
                truncated_last.insert(0, chunk)
                last_used += len(chunk)
            else:
                break

        result = truncated_first + ["\n...[middle interactions omitted]...\n"] + truncated_last
        return result, True

    # We have room for first + last, try to add some middle
    middle_start = n_first
    middle_end = n - n_last
    middle_section = formatted[middle_start:middle_end] if middle_end > middle_start else []

    remaining_budget = max_chars - first_size - last_size
    middle_selected = []

    if middle_section and remaining_budget > 100:
        # Sample evenly from middle section
        middle_used = 0
        step = max(1, len(middle_section) // 5)  # Sample ~5 from middle
        for i in range(0, len(middle_section), step):
            chunk = middle_section[i]
            if middle_used + len(chunk) <= remaining_budget:
                middle_selected.append(chunk)
                middle_used += len(chunk)

    # Assemble result
    if middle_selected:
        result = first_section + ["\n...[some interactions omitted]...\n"] + middle_selected + ["\n...[some interactions omitted]...\n"] + last_section
    else:
        result = first_section + ["\n...[middle interactions omitted]...\n"] + last_section

    return result, True


def format_interactions(
    raw_file: Path,
    max_total_chars: Optional[int] = None,
    max_chars_per_interaction: Optional[int] = None,
    truncate_at: Optional[int] = None,
) -> str:
    """
    Format ticket interactions from raw JSON file for LLM prompts.

    Uses smart truncation that prioritizes RECENT interactions (important for
    detecting PREMATURE_CLOSURE, RESPONSE_DELAYS) while keeping early context.

    Budget allocation when truncation needed:
    - First 20%: Early context (problem statement)
    - Last 60%: Recent interactions (most important for pattern detection)
    - Middle 20%: Sampled if space allows

    Args:
        raw_file: Path to the raw ticket JSON file
        max_total_chars: Maximum total characters for all interactions
        max_chars_per_interaction: Maximum chars before truncating a single interaction
        truncate_at: Where to truncate within an interaction

    Returns:
        Formatted string with interactions (chronological order).
    """
    limits = INTERACTION_LIMITS
    max_chars = max_total_chars or limits["max_total_chars"]
    max_per = max_chars_per_interaction or limits["max_chars_per_interaction"]
    trunc_at = truncate_at or limits["truncate_at"]

    with open(raw_file, "r") as f:
        ticket_data = json.load(f)

    ticket = (ticket_data.get("payload") or {}).get("ticket") or {}
    interactions = ticket.get("interactions") or []

    requester = (ticket.get("metadata") or {}).get("requester") or {}
    requester_name = requester.get("full_name") or "Unknown Customer"

    header = f"Customer: {requester_name}\n"

    # Stored reverse-chronological; we want chronological
    interactions = list(reversed(interactions))

    # Format all interactions first
    formatted = []
    for inter in interactions:
        chunk = _format_single_interaction(inter, max_per, trunc_at)
        if chunk:
            formatted.append(chunk)

    # Smart selection to fit budget (minus header)
    selected, was_truncated = _smart_select_interactions(
        formatted, max_chars - len(header)
    )

    return header + "".join(selected)


def format_interactions_from_dict(
    ticket_data: dict,
    max_total_chars: Optional[int] = None,
    max_chars_per_interaction: Optional[int] = None,
    truncate_at: Optional[int] = None,
) -> str:
    """
    Format ticket interactions from already-loaded ticket data dict.

    Same as format_interactions but accepts pre-loaded data.
    Uses smart truncation that prioritizes recent interactions.
    """
    limits = INTERACTION_LIMITS
    max_chars = max_total_chars or limits["max_total_chars"]
    max_per = max_chars_per_interaction or limits["max_chars_per_interaction"]
    trunc_at = truncate_at or limits["truncate_at"]

    ticket = (ticket_data.get("payload") or {}).get("ticket") or {}
    interactions = ticket.get("interactions") or []

    requester = (ticket.get("metadata") or {}).get("requester") or {}
    requester_name = requester.get("full_name") or "Unknown Customer"

    header = f"Customer: {requester_name}\n"

    # Stored reverse-chronological; we want chronological
    interactions = list(reversed(interactions))

    # Format all interactions first
    formatted = []
    for inter in interactions:
        chunk = _format_single_interaction(inter, max_per, trunc_at)
        if chunk:
            formatted.append(chunk)

    # Smart selection to fit budget (minus header)
    selected, was_truncated = _smart_select_interactions(
        formatted, max_chars - len(header)
    )

    return header + "".join(selected)

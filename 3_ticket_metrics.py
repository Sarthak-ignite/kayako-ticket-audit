#!/usr/bin/env python3
"""
Phase 0.4: Extract metrics from ticket_360 content
- Parse raw JSON files
- Tag interactions (AI/Employee/Customer/General)
- Compute timeline-based metrics (gaps, AI streaks, time to first human, etc.)
- Output: poc_ticket_metrics.csv
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

from config import (
    RAW_DIR,
    POC_TICKET_METRICS as OUTPUT_FILE,
    TAGGED_DIR,
    ensure_dirs,
)

# AI bot names - two categories:
# 1. Exact match names (short names that could appear in human names, use word boundaries)
# 2. Substring match names (longer/unique names safe for substring matching)
AI_NAMES_EXACT = {
    "atlas",
    "hermes",
}

AI_NAMES_SUBSTRING = {
    "centralsupport-ai-acc",
    "ce maintenance bot",
    "trilogy-taro[bot]",
    "cu chulainn ai manager",
    "service sfit",
    "scriptrunner for jira",
    "atlas@trilogy.com",
    "hermes@trilogy.com",
    "saas portal",
    "kayako automations",
    "adn support",
}

# Pre-compiled regex patterns for exact AI name matching (word boundaries)
AI_NAME_PATTERNS = [re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE) for name in AI_NAMES_EXACT]

# Patterns to extract actor names from interaction text
ACTOR_PATTERNS = [
    re.compile(r"Kayako\s+-\s+ticket\s+id\s+\d+\s+//\s+([^/]+?)\s+commented\s+(privately|publicly):", re.IGNORECASE),
    re.compile(r"SaaS\s+Jira\s+-\s+issue\s+key\s+[A-Z]+-\d+\s+//\s+([^/]+?)\s+commented:", re.IGNORECASE),
    re.compile(r"GHI\s+Engineering\s+-\s+\d+\s+//\s+([^/]+?)\s+(commented|subscribed)", re.IGNORECASE),
]


def extract_actor_name(text: str) -> Optional[str]:
    """Extract the actor name from interaction text."""
    for pattern in ACTOR_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def classify_actor(name: Optional[str], requester_email: Optional[str] = None, requester_name: Optional[str] = None) -> str:
    """Classify an actor as AI, Employee, Customer, or General."""
    if not name:
        return "General"

    name_lower = name.lower().strip()

    # Check if AI first (highest priority)
    # 1. Check exact match names using word boundaries (prevents "Atlas Corp" -> AI)
    for pattern in AI_NAME_PATTERNS:
        if pattern.search(name_lower):
            return "AI"
    # 2. Check substring match names (longer/unique names safe for substring)
    for ai_name in AI_NAMES_SUBSTRING:
        if ai_name in name_lower:
            return "AI"

    # Check if customer (matches requester name or email)
    # Stricter matching to avoid false positives with common names
    if requester_name:
        req_name_lower = requester_name.lower().strip()
        req_words = set(req_name_lower.split())
        name_words = set(name_lower.split())

        # Case 1: Exact full name match (always accept)
        if req_name_lower == name_lower:
            return "Customer"

        # Case 2: Multi-word names with high overlap
        # Require BOTH names to have 2+ words to prevent "John" matching "John Smith"
        if len(req_words) >= 2 and len(name_words) >= 2:
            overlap = len(req_words & name_words)
            min_words = min(len(req_words), len(name_words))
            if overlap >= 2 and overlap / min_words >= 0.8:
                return "Customer"

    if requester_email:
        req_email_name = requester_email.split('@')[0].lower().replace('.', ' ')
        req_words = set(req_email_name.split())
        name_words = set(name_lower.split())

        # Case 1: Exact match of email prefix (e.g., "john.smith" == "john smith")
        if req_email_name == name_lower:
            return "Customer"

        # Case 2: Multi-word email prefix with high overlap
        # Require 2+ words overlap to prevent single common names matching
        if len(req_words) >= 2 and len(name_words) >= 2:
            overlap = len(req_words & name_words)
            min_words = min(len(req_words), len(name_words))
            if overlap >= 2 and overlap / min_words >= 0.8:
                return "Customer"

    # Default to Employee if has a real name pattern
    if len(name) > 2 and not name.startswith('['):
        return "Employee"

    return "General"


def get_ai_subtype(text: str) -> Optional[str]:
    """Determine AI subtype (Atlas vs Hermes).

    Uses word boundary matching to avoid false positives
    (e.g., "Atlas Corporation" shouldn't trigger Atlas detection).
    """
    text_lower = text.lower()
    # Use word boundaries to match AI names precisely
    if re.search(r'\batlas\b', text_lower):
        return 'Atlas'
    if re.search(r'\bhermes\b', text_lower):
        return 'Hermes'
    return None


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse timestamp string to datetime."""
    if not ts_str:
        return None
    try:
        # Remove timezone offset for parsing (we'll treat all as UTC)
        ts_clean = ts_str.strip()
        # Handle common timezone formats
        if ts_clean.endswith('+00:00'):
            ts_clean = ts_clean[:-6]
        elif ts_clean.endswith('+0000'):
            ts_clean = ts_clean[:-5]
        elif ts_clean.endswith('Z'):
            ts_clean = ts_clean[:-1]  # Remove exactly one trailing Z

        # Try common formats (without Z suffix since we stripped it)
        for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
            try:
                return datetime.strptime(ts_clean, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def process_ticket(ticket_path: Path) -> Dict:
    """Process a single ticket JSON and extract metrics."""
    
    with open(ticket_path, 'r') as f:
        data = json.load(f)
    
    # Extract ticket ID
    ticket_id = ticket_path.stem.replace('ticket_', '')
    
    # Get ticket metadata - structure is payload.ticket.metadata
    payload = data.get('payload', data)  # Handle both wrapped and unwrapped
    ticket_data = payload.get('ticket', {})
    metadata = ticket_data.get('metadata', {})
    
    # Requester can be a string email or an object
    requester = metadata.get('requester', '')
    if isinstance(requester, dict):
        requester_email = requester.get('emails', [{}])[0].get('email', '') if requester.get('emails') else ''
        requester_name = requester.get('full_name', '')
    else:
        requester_email = requester
        requester_name = ''
    
    # Get interactions - structure is payload.ticket.interactions as list of [timestamp, text]
    raw_interactions = ticket_data.get('interactions', [])
    
    # Tag each interaction - format is [timestamp, text] or just a list
    tagged_interactions = []
    for i, interaction in enumerate(raw_interactions):
        # Handle [timestamp, text] format
        if isinstance(interaction, list) and len(interaction) >= 2:
            timestamp_str = interaction[0]
            text = interaction[1]
        elif isinstance(interaction, dict):
            text = interaction.get('text', '') or interaction.get('content', '') or ''
            timestamp_str = interaction.get('timestamp', '') or interaction.get('created_at', '')
        else:
            continue
        
        # Extract actor
        actor_name = extract_actor_name(text)
        actor_type = classify_actor(actor_name, requester_email, requester_name)
        ai_subtype = get_ai_subtype(text) if actor_type == 'AI' else None
        
        # Parse timestamp
        timestamp = parse_timestamp(timestamp_str)
        
        tagged_interactions.append({
            'index': i,
            'actor_name': actor_name,
            'actor_type': actor_type,
            'ai_subtype': ai_subtype,
            'timestamp': timestamp,
            'timestamp_str': timestamp_str,
            'text_preview': text[:200] if text else '',
            'text_length': len(text) if text else 0,
        })
    
    # Compute metrics from tagged interactions
    metrics = compute_interaction_metrics(tagged_interactions)
    metrics['ticket_id'] = int(ticket_id)
    metrics['total_interactions'] = len(tagged_interactions)
    metrics['product_code'] = metadata.get('product', '')
    
    return metrics, tagged_interactions


def compute_interaction_metrics(interactions: List[Dict]) -> Dict:
    """Compute metrics from tagged interactions."""
    
    metrics = {
        # Counts by actor type
        'ai_count': 0,
        'employee_count': 0,
        'customer_count': 0,
        'general_count': 0,
        
        # AI subtypes
        'atlas_count': 0,
        'hermes_count': 0,
        
        # Timeline metrics
        'first_interaction_ts': None,
        'last_interaction_ts': None,
        'time_to_first_human_seconds': None,
        'time_to_first_ai_seconds': None,
        'max_gap_seconds': 0,
        'gaps_over_24h': 0,
        'gaps_over_48h': 0,
        
        # AI Wall indicators
        'max_consecutive_ai': 0,
        'ai_only_before_human': 0,  # How many AI messages before first human
        'ai_streak_at_start': False,  # Does ticket start with AI streak > 2?
        
        # Content indicators
        'has_customer_frustration_keywords': False,
        'has_previous_ticket_reference': False,
        'has_repeated_info_request': False,
    }
    
    if not interactions:
        return metrics
    
    # Count by actor type
    for inter in interactions:
        actor = inter['actor_type']
        if actor == 'AI':
            metrics['ai_count'] += 1
            if inter['ai_subtype'] == 'Atlas':
                metrics['atlas_count'] += 1
            elif inter['ai_subtype'] == 'Hermes':
                metrics['hermes_count'] += 1
        elif actor == 'Employee':
            metrics['employee_count'] += 1
        elif actor == 'Customer':
            metrics['customer_count'] += 1
        else:
            metrics['general_count'] += 1
    
    # Timeline analysis
    timestamped = [i for i in interactions if i['timestamp']]
    if timestamped:
        sorted_by_time = sorted(timestamped, key=lambda x: x['timestamp'])
        
        metrics['first_interaction_ts'] = sorted_by_time[0]['timestamp'].isoformat()
        metrics['last_interaction_ts'] = sorted_by_time[-1]['timestamp'].isoformat()
        
        # Time to first human response
        first_human = next((i for i in sorted_by_time if i['actor_type'] == 'Employee'), None)
        if first_human and sorted_by_time[0]['timestamp']:
            delta = first_human['timestamp'] - sorted_by_time[0]['timestamp']
            metrics['time_to_first_human_seconds'] = delta.total_seconds()
        
        # Time to first AI response
        first_ai = next((i for i in sorted_by_time if i['actor_type'] == 'AI'), None)
        if first_ai and sorted_by_time[0]['timestamp']:
            delta = first_ai['timestamp'] - sorted_by_time[0]['timestamp']
            metrics['time_to_first_ai_seconds'] = delta.total_seconds()
        
        # Gap analysis
        # Note: gaps_over_24h counts gaps BETWEEN 24h and 48h only
        # gaps_over_48h counts gaps OVER 48h only (mutually exclusive)
        for i in range(1, len(sorted_by_time)):
            gap = (sorted_by_time[i]['timestamp'] - sorted_by_time[i-1]['timestamp']).total_seconds()
            if gap > metrics['max_gap_seconds']:
                metrics['max_gap_seconds'] = gap
            if gap > 48 * 3600:
                metrics['gaps_over_48h'] += 1
            elif gap > 24 * 3600:
                metrics['gaps_over_24h'] += 1
        
        # AI before first human
        first_human_idx = next((i for i, x in enumerate(sorted_by_time) if x['actor_type'] == 'Employee'), len(sorted_by_time))
        metrics['ai_only_before_human'] = sum(1 for x in sorted_by_time[:first_human_idx] if x['actor_type'] == 'AI')
    
    # Max consecutive AI
    current_ai_streak = 0
    max_ai_streak = 0
    for inter in interactions:
        if inter['actor_type'] == 'AI':
            current_ai_streak += 1
            max_ai_streak = max(max_ai_streak, current_ai_streak)
        else:
            current_ai_streak = 0
    metrics['max_consecutive_ai'] = max_ai_streak
    
    # AI streak at start
    start_ai_count = 0
    for inter in interactions:
        if inter['actor_type'] == 'AI':
            start_ai_count += 1
        elif inter['actor_type'] in ('Employee', 'Customer'):
            break
    metrics['ai_streak_at_start'] = start_ai_count > 2
    
    # Content keyword detection (basic)
    all_text = ' '.join(i.get('text_preview', '') for i in interactions).lower()
    
    frustration_keywords = ['frustrated', 'frustrating', 'disappointed', 'unacceptable', 'terrible', 'awful', 'worst', 'ridiculous']
    metrics['has_customer_frustration_keywords'] = any(kw in all_text for kw in frustration_keywords)
    
    # Previous ticket reference
    prev_ticket_patterns = [r'ticket\s*#?\d+', r'previous ticket', r'earlier ticket', r'as i mentioned before', r'already told', r'already provided']
    metrics['has_previous_ticket_reference'] = any(re.search(p, all_text) for p in prev_ticket_patterns)
    
    # Repeated info requests
    repeated_patterns = [r'please provide.*again', r'can you share.*again', r'need.*logs', r'send.*har', r'attach.*screenshot']
    info_requests = sum(1 for p in repeated_patterns if re.search(p, all_text))
    metrics['has_repeated_info_request'] = info_requests > 1
    
    return metrics


def main():
    print("=" * 60)
    print("Phase 0.4: Extract Ticket_360 Metrics")
    print("=" * 60)

    # Create output directories
    ensure_dirs()
    
    # Get all raw ticket files
    raw_files = list(RAW_DIR.glob("ticket_*.json"))
    print(f"\nFound {len(raw_files)} raw ticket files")
    
    if not raw_files:
        print("No raw files found. Run 1_fetch_tickets.py first.")
        return
    
    # Process each ticket
    all_metrics = []
    for i, ticket_path in enumerate(raw_files):
        try:
            metrics, tagged = process_ticket(ticket_path)
            all_metrics.append(metrics)
            
            # Save tagged interactions
            tagged_file = TAGGED_DIR / f"{ticket_path.stem}_tagged.json"
            with open(tagged_file, 'w') as f:
                json.dump(tagged, f, indent=2, default=str)
            
            if (i + 1) % 20 == 0:
                print(f"  Processed {i + 1}/{len(raw_files)} tickets...")
                
        except Exception as e:
            print(f"Error processing {ticket_path.name}: {e}")
    
    # Create DataFrame
    metrics_df = pd.DataFrame(all_metrics)
    
    # Summary stats
    print("\n" + "=" * 60)
    print("TICKET_360 METRICS SUMMARY")
    print("=" * 60)
    
    print(f"\nTickets processed: {len(metrics_df)}")
    
    print(f"\nInteraction counts:")
    print(f"  Total interactions: {metrics_df['total_interactions'].sum()}")
    print(f"  AI interactions: {metrics_df['ai_count'].sum()} (Atlas: {metrics_df['atlas_count'].sum()}, Hermes: {metrics_df['hermes_count'].sum()})")
    print(f"  Employee interactions: {metrics_df['employee_count'].sum()}")
    print(f"  Customer interactions: {metrics_df['customer_count'].sum()}")
    
    print(f"\nTime to first human response (hours):")
    valid_ttfh = metrics_df['time_to_first_human_seconds'].dropna()
    if len(valid_ttfh) > 0:
        print(f"  Mean: {valid_ttfh.mean() / 3600:.1f}")
        print(f"  Median: {valid_ttfh.median() / 3600:.1f}")
        print(f"  P90: {valid_ttfh.quantile(0.9) / 3600:.1f}")
    
    print(f"\nMax gap between interactions (hours):")
    print(f"  Mean: {metrics_df['max_gap_seconds'].mean() / 3600:.1f}")
    print(f"  Tickets with gaps > 24h: {(metrics_df['gaps_over_24h'] > 0).sum()}")
    print(f"  Tickets with gaps > 48h: {(metrics_df['gaps_over_48h'] > 0).sum()}")
    
    print(f"\nAI Wall indicators:")
    print(f"  Max consecutive AI (mean): {metrics_df['max_consecutive_ai'].mean():.1f}")
    print(f"  Tickets with AI streak at start: {metrics_df['ai_streak_at_start'].sum()}")
    print(f"  Mean AI msgs before human: {metrics_df['ai_only_before_human'].mean():.1f}")
    
    print(f"\nContent indicators:")
    print(f"  Customer frustration keywords: {metrics_df['has_customer_frustration_keywords'].sum()}")
    print(f"  Previous ticket references: {metrics_df['has_previous_ticket_reference'].sum()}")
    print(f"  Repeated info requests: {metrics_df['has_repeated_info_request'].sum()}")
    
    # Save
    metrics_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✓ Ticket metrics saved to: {OUTPUT_FILE}")
    print(f"✓ Tagged interactions saved to: {TAGGED_DIR}/")
    
    return metrics_df


if __name__ == "__main__":
    metrics = main()


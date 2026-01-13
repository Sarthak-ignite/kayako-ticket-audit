#!/usr/bin/env python3
"""
Phase 0.1: Build POC sample of ~100 tickets
- Extract all validation seed ticket IDs from Patterns.csv
- Add random tickets per vertical to fill to ~100
- Output: poc_sample.csv with ticket_id, vertical, source (seed/random)
"""

import pandas as pd
import re
import random
from pathlib import Path

# Set random seed for reproducibility
random.seed(42)

# Paths
PATTERNS_CSV = Path("IgniteTech_Khoros_GFI - Central Support Issues we see in tickets - Patterns.csv")
FULL_DATA_CSV = Path("Full_Ticket_Data_1767638152669.csv")
OUTPUT_DIR = Path("data/poc")
OUTPUT_FILE = OUTPUT_DIR / "poc_sample.csv"

def extract_ticket_ids_from_patterns():
    """Parse Patterns.csv and extract all ticket IDs by vertical.
    
    The CSV has an unusual structure:
    - Row 0: "Pattern", "Examples (comma sep list of ticket Ids)", "", ""
    - Row 1: "", "IgniteTech", "Khoros", "GFI"
    - Row 2+: Pattern name, ticket IDs for each vertical
    """
    
    # Read raw to handle the two-row header
    with open(PATTERNS_CSV, 'r') as f:
        lines = f.readlines()
    
    seeds = {
        'IgniteTech': set(),
        'Khoros': set(),
        'GFI': set()
    }
    
    # Column indices based on the structure:
    # Col 0: Pattern name
    # Col 1: IgniteTech ticket IDs
    # Col 2: Khoros ticket IDs  
    # Col 3: GFI ticket IDs
    
    col_to_vertical = {
        1: 'IgniteTech',
        2: 'Khoros',
        3: 'GFI'
    }
    
    # Skip header rows (first 2), parse the rest
    # Use pandas to handle CSV parsing properly (quoted strings, etc.)
    patterns_df = pd.read_csv(PATTERNS_CSV, skiprows=1, header=None)
    
    print(f"Patterns CSV shape: {patterns_df.shape}")
    print(f"First row: {patterns_df.iloc[0].tolist()}")
    
    # Extract ticket IDs from columns 1, 2, 3
    for col_idx, vertical in col_to_vertical.items():
        if col_idx >= len(patterns_df.columns):
            print(f"Warning: Column {col_idx} not found for {vertical}")
            continue
            
        for cell in patterns_df[col_idx].dropna():
            # Extract all numbers that look like ticket IDs (8 digits starting with 60)
            ids = re.findall(r'60\d{6}', str(cell))
            seeds[vertical].update(ids)
    
    return seeds


def load_full_data():
    """Load the full ticket data CSV."""
    df = pd.read_csv(FULL_DATA_CSV)
    
    # Normalize Brand to vertical
    brand_map = {
        'Ignite': 'IgniteTech',
        'Khoros': 'Khoros', 
        'GFI': 'GFI'
    }
    df['vertical'] = df['Brand'].map(brand_map)
    
    return df


def build_sample(seed_tickets, full_df, target_total=100):
    """
    Build sample combining:
    - All seed tickets from Patterns.csv
    - Random fill per vertical to reach target
    """
    
    sample_rows = []
    
    # First, add all seed tickets
    all_seeds = set()
    for vertical, ticket_ids in seed_tickets.items():
        for tid in ticket_ids:
            tid_int = int(tid)
            # Check if ticket exists in full data
            match = full_df[full_df['Ticket ID'] == tid_int]
            if len(match) > 0:
                actual_vertical = match.iloc[0]['vertical']
                sample_rows.append({
                    'ticket_id': tid_int,
                    'vertical': actual_vertical,
                    'pattern_vertical': vertical,  # Which vertical it was listed under in Patterns.csv
                    'source': 'seed'
                })
                all_seeds.add(tid_int)
            else:
                print(f"Warning: Seed ticket {tid} not found in Full_Ticket_Data")
    
    print(f"\nSeed tickets found: {len(sample_rows)}")
    
    # Count seeds by vertical
    seed_by_vertical = {}
    for row in sample_rows:
        v = row['vertical']
        seed_by_vertical[v] = seed_by_vertical.get(v, 0) + 1
    print(f"Seeds by vertical: {seed_by_vertical}")
    
    # Calculate how many random tickets to add
    remaining = target_total - len(sample_rows)
    if remaining > 0:
        # Distribute evenly across verticals
        verticals = ['IgniteTech', 'Khoros', 'GFI']
        per_vertical = remaining // len(verticals)
        
        for vertical in verticals:
            # Get tickets from this vertical that aren't already seeds
            vertical_df = full_df[
                (full_df['vertical'] == vertical) & 
                (~full_df['Ticket ID'].isin(all_seeds))
            ]
            
            # Random sample
            n_to_add = min(per_vertical, len(vertical_df))
            if n_to_add > 0:
                random_sample = vertical_df.sample(n=n_to_add, random_state=42)
                for _, row in random_sample.iterrows():
                    sample_rows.append({
                        'ticket_id': int(row['Ticket ID']),
                        'vertical': vertical,
                        'pattern_vertical': None,
                        'source': 'random'
                    })
    
    return pd.DataFrame(sample_rows)


def main():
    print("=" * 60)
    print("Phase 0.1: Building POC Sample")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Extract seed ticket IDs from Patterns.csv
    print("\n1. Extracting seed tickets from Patterns.csv...")
    seed_tickets = extract_ticket_ids_from_patterns()
    
    for vertical, ids in seed_tickets.items():
        print(f"   {vertical}: {len(ids)} seed tickets")
    
    total_unique = len(set().union(*seed_tickets.values()))
    print(f"   Total unique seeds: {total_unique}")
    
    # Step 2: Load full ticket data
    print("\n2. Loading Full_Ticket_Data...")
    full_df = load_full_data()
    print(f"   Total tickets: {len(full_df)}")
    print(f"   By vertical: {full_df['vertical'].value_counts().to_dict()}")
    
    # Step 3: Build sample
    print("\n3. Building sample...")
    sample_df = build_sample(seed_tickets, full_df, target_total=100)
    
    # Summary
    print("\n" + "=" * 60)
    print("SAMPLE SUMMARY")
    print("=" * 60)
    print(f"Total tickets in sample: {len(sample_df)}")
    print(f"\nBy source:")
    print(sample_df['source'].value_counts().to_string())
    print(f"\nBy vertical:")
    print(sample_df['vertical'].value_counts().to_string())
    print(f"\nSeeds by pattern_vertical (which column they came from):")
    print(sample_df[sample_df['source'] == 'seed']['pattern_vertical'].value_counts().to_string())
    
    # Save
    sample_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✓ Sample saved to: {OUTPUT_FILE}")
    
    # Also save just the ticket IDs for easy reference
    ticket_list_file = OUTPUT_DIR / "poc_ticket_ids.txt"
    sample_df['ticket_id'].to_csv(ticket_list_file, index=False, header=False)
    print(f"✓ Ticket ID list saved to: {ticket_list_file}")
    
    return sample_df


if __name__ == "__main__":
    sample = main()


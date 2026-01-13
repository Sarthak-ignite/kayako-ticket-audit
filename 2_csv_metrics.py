#!/usr/bin/env python3
"""
Phase 0.3: Extract deterministic metrics from CSV for POC sample
- Read the Full_Ticket_Data CSV
- Filter to POC sample tickets
- Extract all relevant metrics and stage indicators
- Output: poc_csv_metrics.csv
"""

import pandas as pd
from pathlib import Path

# Paths
SAMPLE_FILE = Path("data/poc/poc_sample.csv")
FULL_DATA_CSV = Path("Full_Ticket_Data_1767638152669.csv")
OUTPUT_FILE = Path("data/poc/poc_csv_metrics.csv")

# Columns to extract from Full_Ticket_Data
COLUMNS_TO_EXTRACT = [
    # Identity
    'Ticket ID',
    'Brand',
    'Product',
    'Status',
    'Priority',
    'isSev1',
    'Channel',
    
    # Stage boundary signals
    'Level Solved',
    'First_L1_Agent_ID',
    'First L1 Agent',
    'firstL2AgentId',
    'firstL2AgentName',
    'firstReplierEmail',
    'externalTeam',
    'jiraId',
    
    # Time metrics (already computed in CSV)
    'initialResponseTime',
    'resolutionTime',
    'resolutionTimeWithoutLastPending',
    'timeSpentInNew',
    'timeSpentInOpen',
    'timeSpentInHold',
    'timeSpentInPending',
    'timeSpentInSolved',
    'timeSpentOpenL1',
    'timeSpentOpenL2',
    'timeSpentOpenUnassigned',
    
    # Resolution indicators
    'FCR',
    'fcrPlus',
    'l2Fcr',
    'Closed By Merge',
    
    # Timestamps
    'Ticket Created',
    'Ticket Updated',
    'Ticket Solved',
    'Ticket Closed',
    
    # Tags (useful for pattern detection)
    'tickettags',
]


def compute_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived fields for stage boundary detection."""
    
    # Normalize vertical
    brand_map = {'Ignite': 'IgniteTech', 'Khoros': 'Khoros', 'GFI': 'GFI'}
    df['vertical'] = df['Brand'].map(brand_map)
    
    # Stage boundary: was ticket handed to BU/L2?
    df['was_handed_to_bu'] = (
        df['firstL2AgentId'].notna() | 
        (df['timeSpentOpenL2'] > 0) |
        df['Level Solved'].str.contains('L2', case=False, na=False)
    )
    
    # Time in Central Support (L1)
    df['time_in_central_seconds'] = df['timeSpentOpenL1'].fillna(0)
    df['time_in_bu_seconds'] = df['timeSpentOpenL2'].fillna(0)
    
    # Convert time metrics to hours for readability
    df['time_in_central_hours'] = df['time_in_central_seconds'] / 3600
    df['time_in_bu_hours'] = df['time_in_bu_seconds'] / 3600
    df['initial_response_hours'] = df['initialResponseTime'].fillna(0) / 3600
    df['resolution_hours'] = df['resolutionTime'].fillna(0) / 3600
    
    # Is this a P1/SEV1?
    df['is_high_priority'] = (df['isSev1'] == 1) | (df['Priority'].str.lower() == 'urgent')
    
    # Has external team / Jira
    df['has_external_team'] = df['externalTeam'].notna() & (df['externalTeam'] != '')
    df['has_jira'] = df['jiraId'].notna() & (df['jiraId'] != '')
    
    return df


def main():
    print("=" * 60)
    print("Phase 0.3: Extract CSV Metrics for POC Sample")
    print("=" * 60)
    
    # Load POC sample
    sample_df = pd.read_csv(SAMPLE_FILE)
    sample_ticket_ids = set(sample_df['ticket_id'].tolist())
    print(f"\nPOC sample size: {len(sample_ticket_ids)} tickets")
    
    # Load full data
    print("\nLoading Full_Ticket_Data...")
    full_df = pd.read_csv(FULL_DATA_CSV, low_memory=False)
    print(f"Total tickets in CSV: {len(full_df)}")
    
    # Filter to sample tickets
    filtered_df = full_df[full_df['Ticket ID'].isin(sample_ticket_ids)].copy()
    print(f"Matched in sample: {len(filtered_df)}")
    
    # Select columns (only those that exist)
    available_cols = [c for c in COLUMNS_TO_EXTRACT if c in filtered_df.columns]
    missing_cols = [c for c in COLUMNS_TO_EXTRACT if c not in filtered_df.columns]
    
    if missing_cols:
        print(f"\nWarning: Missing columns: {missing_cols}")
    
    metrics_df = filtered_df[available_cols].copy()
    
    # Add derived fields
    print("\nComputing derived fields...")
    metrics_df = compute_derived_fields(metrics_df)
    
    # Summary stats
    print("\n" + "=" * 60)
    print("CSV METRICS SUMMARY")
    print("=" * 60)
    
    print(f"\nTickets by vertical:")
    print(metrics_df['vertical'].value_counts().to_string())
    
    print(f"\nTickets handed to BU: {metrics_df['was_handed_to_bu'].sum()} ({metrics_df['was_handed_to_bu'].mean()*100:.1f}%)")
    
    print(f"\nHigh priority (P1/SEV1): {metrics_df['is_high_priority'].sum()}")
    
    print(f"\nTime in Central Support (hours):")
    print(f"  Mean: {metrics_df['time_in_central_hours'].mean():.1f}")
    print(f"  Median: {metrics_df['time_in_central_hours'].median():.1f}")
    print(f"  P90: {metrics_df['time_in_central_hours'].quantile(0.9):.1f}")
    
    print(f"\nInitial Response Time (hours):")
    valid_irt = metrics_df['initial_response_hours'][metrics_df['initial_response_hours'] > 0]
    if len(valid_irt) > 0:
        print(f"  Mean: {valid_irt.mean():.1f}")
        print(f"  Median: {valid_irt.median():.1f}")
    
    print(f"\nTickets by Status:")
    print(metrics_df['Status'].value_counts().to_string())
    
    # Save
    metrics_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✓ CSV metrics saved to: {OUTPUT_FILE}")
    
    # Also print column list for reference
    print(f"\nColumns in output ({len(metrics_df.columns)}):")
    for col in sorted(metrics_df.columns):
        print(f"  - {col}")
    
    return metrics_df


if __name__ == "__main__":
    metrics = main()



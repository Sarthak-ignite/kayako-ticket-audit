#!/usr/bin/env python3
"""
Phase 0.2: Fetch all POC sample tickets from API
- Read ticket IDs from poc_sample.csv
- Fetch each ticket via the handler API
- Cache locally in data/poc/raw/ticket_{id}.json
"""

import json
import time
import requests
from pathlib import Path
import pandas as pd

# Paths
SAMPLE_FILE = Path("data/poc/poc_sample.csv")
OUTPUT_DIR = Path("data/poc/raw")
ERRORS_FILE = Path("data/poc/fetch_errors.csv")

# API Config
API_URL = "https://s42d56zhik.execute-api.us-east-1.amazonaws.com/Prod/handler"
HEADERS = {"Content-Type": "application/json"}

# Rate limiting
DELAY_BETWEEN_REQUESTS = 0.3  # seconds (faster for POC)


def fetch_ticket(ticket_id: int) -> dict:
    """Fetch a single ticket from the API."""
    payload = {
        "action_type": "get_ticket_360",
        "ticket_id": ticket_id
    }
    
    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    print("=" * 60)
    print("Phase 0.2: Fetching POC Sample Tickets")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load sample
    sample_df = pd.read_csv(SAMPLE_FILE)
    ticket_ids = sample_df['ticket_id'].tolist()
    
    print(f"\nTotal tickets to fetch: {len(ticket_ids)}")
    
    # Track results
    success_count = 0
    error_count = 0
    skipped_count = 0
    errors = []
    
    for i, ticket_id in enumerate(ticket_ids):
        output_file = OUTPUT_DIR / f"ticket_{ticket_id}.json"
        
        # Skip if already cached
        if output_file.exists():
            skipped_count += 1
            print(f"[{i+1}/{len(ticket_ids)}] Ticket {ticket_id}: CACHED (skipping)")
            continue
        
        try:
            print(f"[{i+1}/{len(ticket_ids)}] Fetching ticket {ticket_id}...", end=" ")
            data = fetch_ticket(ticket_id)
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            success_count += 1
            print("OK")
            
            # Rate limiting
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
        except requests.exceptions.RequestException as e:
            error_count += 1
            error_msg = str(e)
            print(f"ERROR: {error_msg[:50]}")
            errors.append({
                'ticket_id': ticket_id,
                'error': error_msg
            })
        
        except Exception as e:
            error_count += 1
            error_msg = str(e)
            print(f"ERROR: {error_msg[:50]}")
            errors.append({
                'ticket_id': ticket_id,
                'error': error_msg
            })
    
    # Save errors
    if errors:
        pd.DataFrame(errors).to_csv(ERRORS_FILE, index=False)
        print(f"\n✗ Errors saved to: {ERRORS_FILE}")
    
    # Summary
    print("\n" + "=" * 60)
    print("FETCH SUMMARY")
    print("=" * 60)
    print(f"Total tickets: {len(ticket_ids)}")
    print(f"Successfully fetched: {success_count}")
    print(f"Cached (skipped): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"\nRaw tickets saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()


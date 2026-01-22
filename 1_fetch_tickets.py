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
import pandas as pd

from config import (
    POC_SAMPLE_CSV as SAMPLE_FILE,
    RAW_DIR as OUTPUT_DIR,
    DATA_DIR,
    TICKET_API_URL as API_URL,
    TICKET_API_DELAY as DELAY_BETWEEN_REQUESTS,
    ensure_dirs,
)

ERRORS_FILE = DATA_DIR / "fetch_errors.csv"
HEADERS = {"Content-Type": "application/json"}


class InvalidTicketResponseError(Exception):
    """Raised when API returns an invalid or malformed ticket response."""
    pass


def validate_ticket_response(data: dict, ticket_id: int) -> None:
    """
    Validate that the API response has the expected structure.

    Expected structure:
    {
        "payload": {
            "ticket": {
                "metadata": {...},
                "interactions": [...]
            }
        }
    }

    Raises InvalidTicketResponseError if structure is invalid.
    """
    if not isinstance(data, dict):
        raise InvalidTicketResponseError(f"Response is not a dict: {type(data)}")

    # Check for API error responses
    if "error" in data:
        raise InvalidTicketResponseError(f"API returned error: {data.get('error')}")
    if "message" in data and "error" in str(data.get("message", "")).lower():
        raise InvalidTicketResponseError(f"API error message: {data.get('message')}")

    # Validate expected structure
    payload = data.get("payload")
    if not isinstance(payload, dict):
        raise InvalidTicketResponseError(f"Missing or invalid 'payload' field")

    ticket = payload.get("ticket")
    if not isinstance(ticket, dict):
        raise InvalidTicketResponseError(f"Missing or invalid 'payload.ticket' field")

    # Interactions should be a list (can be empty for some tickets)
    interactions = ticket.get("interactions")
    if interactions is not None and not isinstance(interactions, list):
        raise InvalidTicketResponseError(f"'interactions' is not a list: {type(interactions)}")


def fetch_ticket(ticket_id: int) -> dict:
    """
    Fetch a single ticket from the API.

    Raises:
        requests.exceptions.RequestException: On HTTP errors
        InvalidTicketResponseError: If response structure is invalid
    """
    payload = {
        "action_type": "get_ticket_360",
        "ticket_id": ticket_id
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    validate_ticket_response(data, ticket_id)

    return data


def main():
    print("=" * 60)
    print("Phase 0.2: Fetching POC Sample Tickets")
    print("=" * 60)

    # Create output directory
    ensure_dirs()
    
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
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"HTTP ERROR: {error_msg[:60]}")
            errors.append({
                'ticket_id': ticket_id,
                'error_type': error_type,
                'error': error_msg,
                'http_status': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            })

        except InvalidTicketResponseError as e:
            error_count += 1
            error_msg = str(e)
            print(f"INVALID RESPONSE: {error_msg[:60]}")
            errors.append({
                'ticket_id': ticket_id,
                'error_type': 'InvalidTicketResponseError',
                'error': error_msg,
                'http_status': None,
            })

        except Exception as e:
            error_count += 1
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"ERROR ({error_type}): {error_msg[:50]}")
            errors.append({
                'ticket_id': ticket_id,
                'error_type': error_type,
                'error': error_msg,
                'http_status': None,
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


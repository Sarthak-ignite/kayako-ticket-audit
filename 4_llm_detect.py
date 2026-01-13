#!/usr/bin/env python3
"""
Phase 0.5-0.6: LLM Pattern Detection
- Run pattern detection on all POC tickets
- Compare 6 models: 2 each from Anthropic, OpenAI, Gemini (SOTA + cheap)
- Output: detection results per model for comparison
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Paths
TAGGED_DIR = Path("data/poc/tagged")
CSV_METRICS_FILE = Path("data/poc/poc_csv_metrics.csv")
TICKET_METRICS_FILE = Path("data/poc/poc_ticket_metrics.csv")
OUTPUT_DIR = Path("data/poc/llm_results")

# Model configurations
MODELS = {
    # Anthropic models
    "claude-sonnet": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929",
        "tier": "sota",
    },
    "claude-haiku": {
        "provider": "anthropic", 
        "model": "claude-3-5-haiku-latest",
        "tier": "cheap",
    },
    "claude-haiku-4-5": {
        "provider": "anthropic", 
        "model": "claude-haiku-4-5-20251001",
        "tier": "cheap",
    },
    # OpenAI models
    "gpt-4o": {
        "provider": "openai",
        "model": "gpt-4o",
        "tier": "sota",
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "tier": "cheap",
    },
    "gpt-5.2": {
        "provider": "openai",
        "model": "gpt-5.2",
        "tier": "sota",
    },
    "gpt-5-mini": {
        "provider": "openai",
        "model": "gpt-5-mini",
        "tier": "cheap",
    },
    # Gemini models (disabled - quota exceeded)
    # "gemini-pro": {
    #     "provider": "gemini",
    #     "model": "gemini-1.5-pro",
    #     "tier": "sota",
    # },
    # "gemini-flash": {
    #     "provider": "gemini",
    #     "model": "gemini-1.5-flash",
    #     "tier": "cheap",
    # },
}

# Pattern detection prompt
SYSTEM_PROMPT = """You are an expert support quality analyst. Your task is to analyze support ticket interactions and detect quality issues.

For each pattern, you must:
1. Determine if the pattern is DETECTED (true/false)
2. Provide a brief REASONING (1-2 sentences)
3. Cite specific EVIDENCE from the interactions (exact quotes with timestamps)

Be conservative - only mark as detected if there is clear evidence."""

USER_PROMPT_TEMPLATE = """Analyze this support ticket for the following quality issues:

## Ticket Context
- Ticket ID: {ticket_id}
- Vertical: {vertical}
- Priority: {priority}
- Status: {status}
- Was handed to BU: {was_handed_to_bu}
- Time to first human (hours): {time_to_first_human_hours}
- Max gap between responses (hours): {max_gap_hours}

## Interactions Timeline
{interactions}

---

Detect the following patterns:

1. **AI_QUALITY_FAILURES**: AI responses are generic filler, provide wrong information, or make promises that aren't kept.

2. **AI_WALL_LOOPING**: Customer is stuck in an AI loop - AI keeps requesting the same information, or customer can't get past AI to reach a human.

3. **IGNORING_CONTEXT**: Support ignores information the customer already provided, asks for same logs/screenshots again, or doesn't check past similar tickets the customer references.

4. **RESPONSE_DELAYS**: Significant delays in responses (multiple days between interactions).

5. **PREMATURE_CLOSURE**: Ticket closed while customer was waiting for promised information, or customer gave up.

6. **P1_SEV1_MISHANDLING**: For high-priority/outage tickets: generic troubleshooting (browser cache, firewall, VPN) instead of immediate escalation.

Respond in this exact JSON format:
```json
{{
  "AI_QUALITY_FAILURES": {{
    "detected": true/false,
    "reasoning": "brief explanation",
    "evidence": ["quote with timestamp", ...]
  }},
  "AI_WALL_LOOPING": {{
    "detected": true/false,
    "reasoning": "brief explanation", 
    "evidence": ["quote with timestamp", ...]
  }},
  "IGNORING_CONTEXT": {{
    "detected": true/false,
    "reasoning": "brief explanation",
    "evidence": ["quote with timestamp", ...]
  }},
  "RESPONSE_DELAYS": {{
    "detected": true/false,
    "reasoning": "brief explanation",
    "evidence": ["quote with timestamp", ...]
  }},
  "PREMATURE_CLOSURE": {{
    "detected": true/false,
    "reasoning": "brief explanation",
    "evidence": ["quote with timestamp", ...]
  }},
  "P1_SEV1_MISHANDLING": {{
    "detected": true/false,
    "reasoning": "brief explanation",
    "evidence": ["quote with timestamp", ...]
  }}
}}
```"""


def call_anthropic(model: str, system: str, user: str) -> str:
    """Call Anthropic API."""
    import anthropic
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    message = client.messages.create(
        model=model,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    
    return message.content[0].text


def call_openai(model: str, system: str, user: str) -> str:
    """Call OpenAI API."""
    import openai
    
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # GPT-5+ models use max_completion_tokens instead of max_tokens
    if model.startswith("gpt-5") or model.startswith("o1"):
        # NOTE: GPT-5-mini can sometimes spend the whole budget on hidden reasoning and return empty content.
        # We bias it toward output with reasoning_effort="low" and retry once with a larger budget if needed.
        def _create(max_completion_tokens: int):
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                max_completion_tokens=max_completion_tokens,
                reasoning_effort="low",
                response_format={"type": "json_object"},
            )

        response = _create(2000)
        content = response.choices[0].message.content or ""
        if content.strip() == "":
            # Retry once with a higher completion budget
            response = _create(4000)
    else:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
    
    content = response.choices[0].message.content or ""
    return content


def call_gemini(model: str, system: str, user: str) -> str:
    """Call Gemini API."""
    import google.generativeai as genai
    
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    gen_model = genai.GenerativeModel(
        model_name=model,
        system_instruction=system
    )
    
    response = gen_model.generate_content(
        user,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=2000,
            response_mime_type="application/json"
        )
    )
    
    return response.text


def call_model(model_key: str, system: str, user: str) -> Optional[str]:
    """Call the appropriate model based on provider."""
    config = MODELS[model_key]
    provider = config["provider"]
    model = config["model"]
    
    try:
        if provider == "anthropic":
            return call_anthropic(model, system, user)
        elif provider == "openai":
            return call_openai(model, system, user)
        elif provider == "gemini":
            return call_gemini(model, system, user)
    except Exception as e:
        print(f"Error calling {model_key}: {e}")
        return None


def format_interactions(tagged_file: Path, max_interactions: int = 30, preview_chars: int = 300) -> str:
    """Format interactions for the prompt."""
    with open(tagged_file, 'r') as f:
        interactions = json.load(f)
    
    # Limit to most recent interactions if too many
    if len(interactions) > max_interactions:
        interactions = interactions[:max_interactions]
    
    lines = []
    for i, inter in enumerate(interactions):
        ts = inter.get('timestamp_str', 'unknown time')
        actor = inter.get('actor_name', 'Unknown')
        actor_type = inter.get('actor_type', 'General')
        preview = inter.get('text_preview', '')[:preview_chars]  # Limit text length
        
        lines.append(f"[{ts}] ({actor_type}) {actor}:\n{preview}\n")
    
    return "\n---\n".join(lines)


def parse_llm_response(response: str) -> Optional[Dict]:
    """Parse JSON response from LLM."""
    try:
        # Try to extract JSON from response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        else:
            json_str = response
        
        return json.loads(json_str.strip())
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None


def process_ticket(ticket_id: int, model_key: str, csv_row: pd.Series, ticket_metrics: pd.Series) -> Optional[Dict]:
    """Process a single ticket with a single model."""
    
    # Find tagged file
    tagged_file = TAGGED_DIR / f"ticket_{ticket_id}_tagged.json"
    if not tagged_file.exists():
        print(f"  Tagged file not found for {ticket_id}")
        return None
    
    # Format interactions (trim more aggressively for GPT-5-mini to avoid spending budget on hidden reasoning)
    max_interactions = 30
    preview_chars = 300
    if model_key in {"gpt-5-mini"}:
        max_interactions = 18
        preview_chars = 220
    interactions_text = format_interactions(tagged_file, max_interactions=max_interactions, preview_chars=preview_chars)
    
    # Build prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticket_id=ticket_id,
        vertical=csv_row.get('vertical', 'Unknown'),
        priority=csv_row.get('Priority', 'Unknown'),
        status=csv_row.get('Status', 'Unknown'),
        was_handed_to_bu=csv_row.get('was_handed_to_bu', False),
        time_to_first_human_hours=round(ticket_metrics.get('time_to_first_human_seconds', 0) / 3600, 1) if ticket_metrics.get('time_to_first_human_seconds') else 'N/A',
        max_gap_hours=round(ticket_metrics.get('max_gap_seconds', 0) / 3600, 1),
        interactions=interactions_text
    )
    
    # Call model
    response = call_model(model_key, SYSTEM_PROMPT, user_prompt)
    
    if not response:
        return None
    
    # Parse response
    result = parse_llm_response(response)
    
    if result:
        result['_raw_response'] = response
        result['_model'] = model_key
        result['_ticket_id'] = ticket_id
    
    return result


def run_model_on_all_tickets(model_key: str, csv_metrics: pd.DataFrame, ticket_metrics: pd.DataFrame, limit: Optional[int] = None):
    """Run a single model on all tickets."""
    
    model_output_dir = OUTPUT_DIR / model_key
    model_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get ticket IDs
    ticket_ids = csv_metrics['Ticket ID'].tolist()
    if limit:
        ticket_ids = ticket_ids[:limit]
    
    print(f"\nRunning {model_key} on {len(ticket_ids)} tickets...")
    
    results = []
    for i, ticket_id in enumerate(ticket_ids):
        # Check if already processed
        output_file = model_output_dir / f"ticket_{ticket_id}.json"
        if output_file.exists():
            print(f"  [{i+1}/{len(ticket_ids)}] Ticket {ticket_id}: CACHED")
            with open(output_file, 'r') as f:
                results.append(json.load(f))
            continue
        
        print(f"  [{i+1}/{len(ticket_ids)}] Processing ticket {ticket_id}...", end=" ")
        
        # Get metrics
        csv_row = csv_metrics[csv_metrics['Ticket ID'] == ticket_id].iloc[0] if len(csv_metrics[csv_metrics['Ticket ID'] == ticket_id]) > 0 else pd.Series()
        tm_row = ticket_metrics[ticket_metrics['ticket_id'] == ticket_id].iloc[0] if len(ticket_metrics[ticket_metrics['ticket_id'] == ticket_id]) > 0 else pd.Series()
        
        result = process_ticket(ticket_id, model_key, csv_row, tm_row)
        
        if result:
            # Save result
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            results.append(result)
            print("OK")
        else:
            print("FAILED")
        
        # Rate limiting
        time.sleep(0.5)
    
    return results


def summarize_results(model_key: str) -> Dict:
    """Summarize detection results for a model."""
    model_output_dir = OUTPUT_DIR / model_key
    
    if not model_output_dir.exists():
        return {}
    
    result_files = list(model_output_dir.glob("ticket_*.json"))
    
    patterns = ["AI_QUALITY_FAILURES", "AI_WALL_LOOPING", "IGNORING_CONTEXT", 
                "RESPONSE_DELAYS", "PREMATURE_CLOSURE", "P1_SEV1_MISHANDLING"]
    
    summary = {p: {"detected": 0, "total": 0} for p in patterns}
    
    for rf in result_files:
        with open(rf, 'r') as f:
            result = json.load(f)
        
        for pattern in patterns:
            if pattern in result:
                summary[pattern]["total"] += 1
                if result[pattern].get("detected", False):
                    summary[pattern]["detected"] += 1
    
    # Calculate percentages
    for pattern in patterns:
        total = summary[pattern]["total"]
        detected = summary[pattern]["detected"]
        summary[pattern]["percentage"] = round(detected / total * 100, 1) if total > 0 else 0
    
    return summary


def main():
    print("=" * 60)
    print("Phase 0.5-0.6: LLM Pattern Detection")
    print("=" * 60)
    
    # Check API keys
    apis = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    }
    
    print("\nAPI Key Status:")
    for key, value in apis.items():
        status = "✓ Found" if value else "✗ Missing"
        print(f"  {key}: {status}")
    
    if not any(apis.values()):
        print("\nNo API keys found! Please check your .env file.")
        return
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load metrics
    print("\nLoading metrics...")
    csv_metrics = pd.read_csv(CSV_METRICS_FILE)
    ticket_metrics = pd.read_csv(TICKET_METRICS_FILE)
    print(f"  CSV metrics: {len(csv_metrics)} tickets")
    print(f"  Ticket metrics: {len(ticket_metrics)} tickets")
    
    # Filter models based on available API keys
    available_models = {}
    for model_key, config in MODELS.items():
        provider = config["provider"]
        if provider == "anthropic" and apis["ANTHROPIC_API_KEY"]:
            available_models[model_key] = config
        elif provider == "openai" and apis["OPENAI_API_KEY"]:
            available_models[model_key] = config
        elif provider == "gemini" and apis["GEMINI_API_KEY"]:
            available_models[model_key] = config
    
    print(f"\nAvailable models: {list(available_models.keys())}")
    
    # Check for command line arguments for non-interactive mode
    import sys
    
    # Parse arguments: python 4_llm_detect.py [models] [limit]
    # models: all, sota, cheap, or comma-separated model names
    # limit: number of tickets or empty for all
    
    if len(sys.argv) > 1:
        model_arg = sys.argv[1].lower()
        if model_arg == "sota":
            models_to_run = {k: v for k, v in available_models.items() if v["tier"] == "sota"}
        elif model_arg == "cheap":
            models_to_run = {k: v for k, v in available_models.items() if v["tier"] == "cheap"}
        elif model_arg == "all":
            models_to_run = available_models
        else:
            # Comma-separated model names
            requested = [m.strip() for m in model_arg.split(",")]
            models_to_run = {k: v for k, v in available_models.items() if k in requested}
        
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    else:
        # Interactive mode
        print("\nSelect models to run:")
        print("  1. All available models")
        print("  2. SOTA models only (expensive)")
        print("  3. Cheap models only")
        print("  4. One model (specify)")
        
        choice = input("Choice [1]: ").strip() or "1"
        
        if choice == "2":
            models_to_run = {k: v for k, v in available_models.items() if v["tier"] == "sota"}
        elif choice == "3":
            models_to_run = {k: v for k, v in available_models.items() if v["tier"] == "cheap"}
        elif choice == "4":
            model_name = input(f"Model name ({', '.join(available_models.keys())}): ").strip()
            if model_name in available_models:
                models_to_run = {model_name: available_models[model_name]}
            else:
                print(f"Unknown model: {model_name}")
                return
        else:
            models_to_run = available_models
        
        limit_input = input("Limit tickets (empty for all): ").strip()
        limit = int(limit_input) if limit_input else None
    
    print(f"\nRunning models: {list(models_to_run.keys())}")
    print(f"Limit: {limit if limit else 'all tickets'}")
    
    # Run each model
    for model_key in models_to_run:
        run_model_on_all_tickets(model_key, csv_metrics, ticket_metrics, limit=limit)
    
    # Summary
    print("\n" + "=" * 60)
    print("DETECTION SUMMARY")
    print("=" * 60)
    
    patterns = ["AI_QUALITY_FAILURES", "AI_WALL_LOOPING", "IGNORING_CONTEXT", 
                "RESPONSE_DELAYS", "PREMATURE_CLOSURE", "P1_SEV1_MISHANDLING"]
    
    # Print header
    print(f"\n{'Pattern':<25}", end="")
    for model_key in models_to_run:
        print(f"{model_key:<15}", end="")
    print()
    print("-" * (25 + 15 * len(models_to_run)))
    
    # Get summaries
    summaries = {mk: summarize_results(mk) for mk in models_to_run}
    
    # Print each pattern
    for pattern in patterns:
        print(f"{pattern:<25}", end="")
        for model_key in models_to_run:
            summary = summaries.get(model_key, {})
            if pattern in summary:
                pct = summary[pattern]["percentage"]
                count = summary[pattern]["detected"]
                print(f"{count} ({pct}%)".ljust(15), end="")
            else:
                print("-".ljust(15), end="")
        print()


if __name__ == "__main__":
    main()


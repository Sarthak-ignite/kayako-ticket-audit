#!/usr/bin/env python3
"""
Pipeline runner for the Kayako ticket analysis workflow.

Orchestrates all pipeline steps:
1. Build sample (0_build_sample.py)
2. Fetch tickets (1_fetch_tickets.py)
3. Run LLM detection (llm_detect.py)
4. Evaluate results (evaluate.py)
5. Summarize results (9_summarize_llm_results.py)

Usage:
    python run_pipeline.py                    # Run full pipeline
    python run_pipeline.py --step detect      # Run only detection step
    python run_pipeline.py --step eval        # Run only evaluation step
    python run_pipeline.py --skip fetch       # Skip fetching (use cached)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

from config import (
    ensure_dirs,
    DATA_DIR,
    RAW_DIR,
    LLM_RESULTS_DIR,
    POC_SAMPLE_CSV,
    GROUND_TRUTH_CSV,
    get_llm_output_dir,
)


STEPS = {
    "sample": {
        "name": "Build Sample",
        "script": "0_build_sample.py",
        "description": "Extract seed tickets and build POC sample",
    },
    "fetch": {
        "name": "Fetch Tickets",
        "script": "1_fetch_tickets.py",
        "description": "Fetch ticket data from API",
    },
    "detect": {
        "name": "LLM Detection",
        "script": "llm_detect.py",
        "description": "Run LLM pattern detection",
    },
    "eval": {
        "name": "Evaluate",
        "script": "evaluate.py",
        "description": "Evaluate detection results",
    },
    "summarize": {
        "name": "Summarize",
        "script": "9_summarize_llm_results.py",
        "description": "Generate summary CSV",
    },
}

STEP_ORDER = ["sample", "fetch", "detect", "eval", "summarize"]


def run_step(step_id: str, extra_args: Optional[list[str]] = None) -> bool:
    """Run a single pipeline step."""
    step = STEPS[step_id]
    script = Path(step["script"])

    if not script.exists():
        print(f"ERROR: Script not found: {script}")
        return False

    print(f"\n{'='*72}")
    print(f"STEP: {step['name']}")
    print(f"Script: {script}")
    print(f"Description: {step['description']}")
    print("="*72)

    cmd = [sys.executable, str(script)]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd)
    return result.returncode == 0


def check_prerequisites(step_id: str) -> tuple[bool, str]:
    """Check if prerequisites for a step are met."""
    if step_id == "sample":
        return True, ""

    if step_id == "fetch":
        if not POC_SAMPLE_CSV.exists():
            return False, f"Missing {POC_SAMPLE_CSV}. Run 'sample' step first."
        return True, ""

    if step_id == "detect":
        if not RAW_DIR.exists() or not any(RAW_DIR.glob("ticket_*.json")):
            return False, f"No raw tickets in {RAW_DIR}. Run 'fetch' step first."
        return True, ""

    if step_id == "eval":
        results_dir = get_llm_output_dir()
        if not results_dir.exists() or not any(results_dir.glob("ticket_*.json")):
            return False, f"No results in {results_dir}. Run 'detect' step first."
        if not GROUND_TRUTH_CSV.exists():
            return False, f"Missing {GROUND_TRUTH_CSV}. Build ground truth first."
        return True, ""

    if step_id == "summarize":
        results_dir = get_llm_output_dir()
        if not results_dir.exists() or not any(results_dir.glob("ticket_*.json")):
            return False, f"No results in {results_dir}. Run 'detect' step first."
        return True, ""

    return True, ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run the Kayako ticket analysis pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Steps (in order):
  sample     Build POC sample from Patterns.csv
  fetch      Fetch tickets from API
  detect     Run LLM pattern detection
  eval       Evaluate against ground truth
  summarize  Generate summary CSV

Examples:
  python run_pipeline.py                    # Run full pipeline
  python run_pipeline.py --step detect      # Run only detection
  python run_pipeline.py --from detect      # Run from detection onwards
  python run_pipeline.py --skip fetch       # Skip fetch step
""",
    )
    p.add_argument(
        "--step",
        choices=STEP_ORDER,
        help="Run only this specific step",
    )
    p.add_argument(
        "--from",
        dest="from_step",
        choices=STEP_ORDER,
        help="Start from this step (run this and all following)",
    )
    p.add_argument(
        "--skip",
        nargs="+",
        choices=STEP_ORDER,
        default=[],
        help="Skip these steps",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Force re-run even if outputs exist",
    )
    p.add_argument(
        "--ticket-set",
        choices=["all", "ground_truth", "sample"],
        default="ground_truth",
        help="Which tickets to process in detect step (default: ground_truth)",
    )
    p.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Custom results directory for detect/eval/summarize steps",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dirs()

    # Determine which steps to run
    if args.step:
        steps_to_run = [args.step]
    elif args.from_step:
        start_idx = STEP_ORDER.index(args.from_step)
        steps_to_run = STEP_ORDER[start_idx:]
    else:
        steps_to_run = STEP_ORDER.copy()

    # Remove skipped steps
    steps_to_run = [s for s in steps_to_run if s not in args.skip]

    if not steps_to_run:
        print("No steps to run.")
        return

    print("="*72)
    print("KAYAKO TICKET ANALYSIS PIPELINE")
    print("="*72)
    print(f"Steps to run: {', '.join(steps_to_run)}")
    print(f"Ticket set: {args.ticket_set}")
    if args.results_dir:
        print(f"Results dir: {args.results_dir}")
    print()

    # Run steps
    failed = []
    for step_id in steps_to_run:
        # Check prerequisites
        ok, msg = check_prerequisites(step_id)
        if not ok:
            print(f"\nERROR: Prerequisites not met for '{step_id}': {msg}")
            failed.append(step_id)
            break

        # Build extra args for specific steps
        extra_args = []
        if step_id == "detect":
            extra_args.append(f"--ticket-set={args.ticket_set}")
            if args.results_dir:
                extra_args.append(f"--outdir={args.results_dir}")
            if args.force:
                extra_args.append("--force")

        elif step_id == "eval":
            results_dir = args.results_dir or str(get_llm_output_dir())
            extra_args.append(f"--results-dir={results_dir}")

        elif step_id == "summarize":
            results_dir = args.results_dir or str(get_llm_output_dir())
            extra_args.append(f"--results-dir={results_dir}")

        # Run the step
        success = run_step(step_id, extra_args)
        if not success:
            failed.append(step_id)
            print(f"\nSTEP FAILED: {step_id}")
            break

    # Summary
    print("\n" + "="*72)
    print("PIPELINE COMPLETE")
    print("="*72)

    if failed:
        print(f"FAILED STEPS: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("All steps completed successfully.")
        print(f"\nOutputs:")
        print(f"  - Sample: {POC_SAMPLE_CSV}")
        print(f"  - Raw tickets: {RAW_DIR}/")
        print(f"  - LLM results: {args.results_dir or get_llm_output_dir()}/")


if __name__ == "__main__":
    main()

"""
Central configuration for the Kayako ticket analysis pipeline.

All paths, constants, and settings in one place.
"""

from pathlib import Path
from typing import Any

# =============================================================================
# PATHS
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent

# Source data files
PATTERNS_CSV = REPO_ROOT / "IgniteTech_Khoros_GFI - Central Support Issues we see in tickets - Patterns.csv"
FULL_TICKET_DATA_CSV = REPO_ROOT / "Full_Ticket_Data_1767638152669.csv"

# Output directories
DATA_DIR = REPO_ROOT / "data/poc"
RAW_DIR = DATA_DIR / "raw"
TAGGED_DIR = DATA_DIR / "tagged"
LLM_RESULTS_DIR = DATA_DIR / "llm_results"

# Output files
POC_SAMPLE_CSV = DATA_DIR / "poc_sample.csv"
POC_TICKET_IDS_TXT = DATA_DIR / "poc_ticket_ids.txt"
POC_CSV_METRICS = DATA_DIR / "poc_csv_metrics.csv"
POC_TICKET_METRICS = DATA_DIR / "poc_ticket_metrics.csv"
GROUND_TRUTH_CSV = DATA_DIR / "ground_truth_expected.csv"
GROUND_TRUTH_JSON = DATA_DIR / "ground_truth_expected.json"
GROUND_TRUTH_OVERRIDES = DATA_DIR / "ground_truth_overrides.json"

# =============================================================================
# PATTERN DEFINITIONS
# =============================================================================

OUR_PATTERNS = [
    "AI_QUALITY_FAILURES",
    "AI_WALL_LOOPING",
    "IGNORING_CONTEXT",
    "RESPONSE_DELAYS",
    "PREMATURE_CLOSURE",
    "P1_SEV1_MISHANDLING",
]

# Human-readable labels for display
PATTERN_LABELS = {
    "AI_QUALITY_FAILURES": "AI Quality Failures",
    "AI_WALL_LOOPING": "AI Wall/Looping",
    "IGNORING_CONTEXT": "Ignoring Context",
    "RESPONSE_DELAYS": "Response Delays",
    "PREMATURE_CLOSURE": "Premature Closure",
    "P1_SEV1_MISHANDLING": "P1/SEV1 Mishandling",
}

# Mapping from Patterns.csv text to our canonical labels
PATTERN_TEXT_MAPPING = {
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

# =============================================================================
# CSV CONTEXT FIELDS
# =============================================================================

# Fields to extract from Full_Ticket_Data for LLM context
CSV_CONTEXT_FIELDS = [
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

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Ticket fetch API
TICKET_API_URL = "https://s42d56zhik.execute-api.us-east-1.amazonaws.com/Prod/handler"
TICKET_API_DELAY = 0.3  # seconds between requests

# LLM Configuration
LLM_CONFIG = {
    "model": "gpt-5.2",
    "max_completion_tokens": 1800,
    "reasoning_effort": "medium",
    "max_retries": 2,
    "retry_delay_base": 0.6,
    "call_delay": 0.35,  # seconds between calls
}

# Interaction formatting limits
INTERACTION_LIMITS = {
    "max_total_chars": 26000,
    "max_chars_per_interaction": 2200,
    "truncate_at": 2000,
}

# =============================================================================
# PATTERN DETECTION THRESHOLDS
# =============================================================================

# Thresholds for RESPONSE_DELAYS detection (in hours)
RESPONSE_DELAY_THRESHOLDS = {
    "initial_response_hours": 24,      # First response > 24h = delay
    "follow_up_gap_hours": 48,         # Gap between messages > 48h = delay
    "resolution_time_days": 7,         # Total resolution > 7 days = delay (if customer waiting)
}

# Indicators for P1_SEV1_MISHANDLING detection
P1_SEV1_INDICATORS = {
    # Keywords in ticket text that indicate P1/SEV1
    "keywords": [
        "outage", "down", "production down", "critical", "urgent",
        "sev1", "sev 1", "severity 1", "p1", "priority 1",
        "all users affected", "business impact", "revenue impact",
        "complete failure", "system down", "service unavailable",
    ],
    # Expected response time for P1/SEV1 (in hours)
    "max_response_hours": 4,
    # Expected resolution time for P1/SEV1 (in hours)
    "max_resolution_hours": 24,
}

# =============================================================================
# VERTICALS
# =============================================================================

VERTICALS = ["IgniteTech", "Khoros", "GFI"]

BRAND_TO_VERTICAL = {
    "Ignite": "IgniteTech",
    "Khoros": "Khoros",
    "GFI": "GFI",
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def ensure_dirs() -> None:
    """Create all output directories if they don't exist."""
    for d in [DATA_DIR, RAW_DIR, TAGGED_DIR, LLM_RESULTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def get_llm_output_dir(model_name: str = "gpt-5.2-v6") -> Path:
    """Get the output directory for a specific LLM model run."""
    return LLM_RESULTS_DIR / model_name

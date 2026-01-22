# Kayako Ticket Analyzer

A comprehensive support ticket quality analysis system combining deterministic metrics extraction with LLM-powered pattern detection. Built for analyzing Central Support performance across IgniteTech, Khoros, and GFI verticals.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Pattern Detection](#pattern-detection)
- [Project Structure](#project-structure)
- [Backend Pipeline](#backend-pipeline)
- [Web Dashboard](#web-dashboard)
- [Data Flow](#data-flow)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)

---

## Overview

This system analyzes Kayako support tickets to identify quality issues through two complementary approaches:

1. **Hard Metrics** - Algorithmically computed from CSV ticket data (timing, resolution, interactions)
2. **LLM Pattern Detection** - AI-powered analysis identifying 6 quality patterns with reasoning and evidence

### Key Capabilities

- Extract deterministic metrics from Kayako ticket exports
- Parse ticket interactions and classify actors (AI/Employee/Customer)
- Detect support quality patterns using GPT-5.2
- Evaluate detection accuracy against ground truth
- Interactive web dashboard for reviewing results

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                   │
├──────────────────┬──────────────────┬────────────────────────────────────┤
│ Full_Ticket_Data │   Patterns.csv   │         Kayako API                 │
│     (CSV)        │  (seed tickets)  │      (ticket_360)                  │
└────────┬─────────┴────────┬─────────┴──────────────┬─────────────────────┘
         │                  │                         │
         ▼                  ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        PYTHON PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  0_build_sample.py  →  1_fetch_tickets.py  →  2_csv_metrics.py          │
│                                              3_ticket_metrics.py         │
│                                                     │                    │
│                                                     ▼                    │
│  6_build_ground_truth.py  ←──  llm_detect.py  →  evaluate.py            │
│                                      │                                   │
│                                      ▼                                   │
│                           9_summarize_llm_results.py                     │
└─────────────────────────────────────────────────────────────────────────┘
         │                                                     │
         ▼                                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA OUTPUTS                                    │
├───────────────────────────────┬─────────────────────────────────────────┤
│   data/poc/raw/               │   data/poc/llm_results/                 │
│   (ticket JSONs)              │   (LLM detection results)               │
├───────────────────────────────┼─────────────────────────────────────────┤
│   poc_csv_metrics.csv         │   poc_llm_v6_sample_summary.csv         │
│   poc_ticket_metrics.csv      │   ground_truth_expected.csv             │
└───────────────────────────────┴─────────────────────────────────────────┘
         │                                                     │
         └─────────────────────────┬───────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        WEB DASHBOARD                                     │
│                       (Next.js + React)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  /tickets          - Searchable ticket list with filters                 │
│  /tickets/[id]     - Ticket detail with hard metrics + LLM patterns     │
│  /analytics        - Aggregate analytics with charts and filters        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Pattern Detection

The system detects 6 quality patterns that indicate potential support issues:

| Pattern | Description | Indicators |
|---------|-------------|------------|
| **AI_QUALITY_FAILURES** | AI (Atlas/Hermes) provides wrong, misleading, filler, or repetitive responses | Customer frustration, AI promises not delivered, repetitive AI text |
| **AI_WALL_LOOPING** | Customer stuck with AI, difficulty reaching human, repetitive AI loop | Multiple consecutive AI responses, customer asks for human, AI streak at start |
| **IGNORING_CONTEXT** | Support ignores info already provided or forces repetition | Customer mentions "already provided", repeated info requests |
| **RESPONSE_DELAYS** | Meaningful response gaps or customer complaints about waiting | Initial response >24h, gaps >48h, resolution >7 days |
| **PREMATURE_CLOSURE** | Ticket closed while customer still needs help | Auto-close warnings, status "Closed" with unresolved issues |
| **P1_SEV1_MISHANDLING** | High-severity/outage treated like routine troubleshooting | P1/SEV1 with slow response (>4h), generic troubleshooting for outages |

---

## Project Structure

```
kayako-tickets-analyser/
├── config.py                    # Central configuration (paths, patterns, thresholds)
├── run_pipeline.py              # Pipeline orchestrator
│
├── 0_build_sample.py            # Build POC sample from Patterns.csv + random fill
├── 1_fetch_tickets.py           # Fetch ticket_360 data from Kayako API
├── 2_csv_metrics.py             # Extract metrics from Full_Ticket_Data CSV
├── 3_ticket_metrics.py          # Parse interactions, tag actors, compute timeline metrics
├── 6_build_ground_truth.py      # Build ground truth from Patterns.csv + overrides
├── llm_detect.py                # LLM pattern detection (GPT-5.2)
├── evaluate.py                  # Evaluate LLM results against ground truth
├── 9_summarize_llm_results.py   # Generate summary CSV from LLM results
│
├── utils/                       # Shared utilities
│   ├── __init__.py              # Re-exports all utilities
│   ├── data_loader.py           # CSV/JSON loading functions
│   ├── formatters.py            # Text formatting for LLM prompts
│   └── llm_client.py            # OpenAI client with retry logic
│
├── data/poc/                    # Pipeline outputs
│   ├── raw/                     # Raw ticket_360 JSON files
│   ├── tagged/                  # Tagged interaction files
│   ├── llm_results/             # LLM detection outputs by model
│   ├── poc_sample.csv           # Sample ticket list
│   ├── poc_csv_metrics.csv      # Extracted CSV metrics
│   ├── poc_ticket_metrics.csv   # Interaction metrics
│   └── ground_truth_expected.csv # Ground truth labels
│
├── web/                         # Next.js web dashboard
│   ├── src/app/                 # App routes (pages)
│   ├── src/components/          # React components
│   └── src/lib/                 # Data loading, types, analytics
│
├── Full_Ticket_Data_*.csv       # Source ticket export (not in repo)
├── IgniteTech_Khoros_GFI...csv  # Patterns.csv with seed tickets
└── requirements.txt             # Python dependencies
```

---

## Backend Pipeline

### Script Reference

#### Phase 0: Data Preparation

| Script | Purpose | Inputs | Outputs |
|--------|---------|--------|---------|
| `0_build_sample.py` | Build POC sample of ~100 tickets from seed tickets + random fill | Patterns.csv, Full_Ticket_Data.csv | poc_sample.csv, poc_ticket_ids.txt |
| `1_fetch_tickets.py` | Fetch ticket_360 data from Kayako API for all sample tickets | poc_sample.csv | data/poc/raw/ticket_*.json |
| `2_csv_metrics.py` | Extract deterministic metrics from Full_Ticket_Data | Full_Ticket_Data.csv, poc_sample.csv | poc_csv_metrics.csv |
| `3_ticket_metrics.py` | Parse ticket JSONs, tag interactions (AI/Employee/Customer), compute timeline metrics | data/poc/raw/*.json | poc_ticket_metrics.csv, data/poc/tagged/*.json |

#### Phase 1: LLM Detection

| Script | Purpose | Inputs | Outputs |
|--------|---------|--------|---------|
| `llm_detect.py` | Run LLM pattern detection with recall-first approach | data/poc/raw/*.json, Full_Ticket_Data.csv | data/poc/llm_results/*/ticket_*.json |
| `6_build_ground_truth.py` | Build ground truth dataset from Patterns.csv with manual overrides | Patterns.csv, ground_truth_overrides.json | ground_truth_expected.csv, ground_truth_expected.json |

#### Phase 2: Evaluation & Reporting

| Script | Purpose | Inputs | Outputs |
|--------|---------|--------|---------|
| `evaluate.py` | Evaluate LLM results against ground truth (recall-only and full metrics) | ground_truth_expected.csv, llm_results/*.json | Console output |
| `9_summarize_llm_results.py` | Generate summary CSV with all detections + reasoning | llm_results/*.json, poc_sample.csv | poc_llm_v6_sample_summary.csv |

### Actor Classification

The `3_ticket_metrics.py` script classifies interaction actors:

| Type | Detection Method |
|------|------------------|
| **AI** | Name matches: atlas, hermes, cu chulainn ai manager, centralsupport-ai-acc, etc. |
| **Customer** | Matches requester name/email from ticket metadata |
| **Employee** | Has real name pattern, not AI or customer |
| **General** | System messages, unknown actors |

### Hard Metrics Computed

From `poc_csv_metrics.csv`:
- Initial response time, resolution time
- Time spent in each status (New, Open, Hold, Pending)
- Time at L1 (Central Support) vs L2 (Business Unit)
- FCR (First Contact Resolution) flags
- Escalation indicators

From `poc_ticket_metrics.csv`:
- Interaction counts by actor type
- Time to first human/AI response
- Maximum gap between interactions
- Count of gaps >24h and >48h
- Customer frustration keyword detection
- Previous ticket references

---

## Web Dashboard

### Technology Stack

- **Framework**: Next.js 16.1.1 with App Router
- **React**: 19.2.3 (Server Components + Client Components)
- **Styling**: Tailwind CSS 4 with dark mode support
- **Charts**: Recharts 3.7.0
- **Auth**: Clerk for authentication

### Pages & Features

#### Tickets List (`/tickets`)
- Paginated ticket list (25/50/100 per page)
- Filters: Dataset, Vertical, Product, Status, Source, Patterns, SEV1
- Debounced search by ticket ID or product
- Sortable by pattern count, update date, creation date
- Pattern badges showing detected issues

#### Ticket Detail (`/tickets/[id]`)
- **Hard Metrics Section**: Timing, resolution, interactions with alert flags
- **LLM Patterns Section**: 6 pattern cards with detection status, reasoning, evidence
- **Transcript Viewer**: Searchable chronological interaction history

#### Analytics Dashboard (`/analytics`)
- **Summary Cards**: Total tickets, detection rate, SEV1 count, avg patterns
- **Hard Metrics Overview**: Response time averages/medians, FCR rate, escalation rate
- **Charts**: Pattern distribution, vertical breakdown, pattern heatmap, source distribution
- **Product Table**: Sortable by detection rate with top patterns
- **Pattern Co-occurrence**: Which patterns appear together
- **Filters**: Same as tickets list plus priority filter

### Data Loading

The frontend reads data directly from the pipeline output CSVs:

```
poc_llm_v6_sample_summary.csv  →  Ticket list + LLM detections
poc_csv_metrics.csv            →  Hard timing/resolution metrics
poc_ticket_metrics.csv         →  Interaction metrics
data/poc/raw/ticket_*.json     →  Transcript data
data/poc/llm_results/          →  Full LLM results with reasoning
```

---

## Data Flow

### Ticket List Query Flow

```
1. Client requests /tickets?dataset=v6_sample&vertical=Khoros
2. Server loads poc_llm_v6_sample_summary.csv
3. Parse CSV rows → TicketListItem[]
4. Apply filters (vertical, product, status, patterns, etc.)
5. Sort and paginate
6. Return {total, items}
```

### Ticket Detail Query Flow

```
1. Client requests /tickets/60208754?dataset=v6_sample
2. Server loads in parallel:
   - Summary row from poc_llm_v6_sample_summary.csv
   - LLM result from llm_results/gpt-5.2-v6-sample/ticket_60208754.json
   - Transcript from raw/ticket_60208754.json
   - Hard metrics from poc_csv_metrics.csv + poc_ticket_metrics.csv
3. Compute derived flags (slow response, long resolution, etc.)
4. Return TicketDetail object
```

### Analytics Query Flow

```
1. Client requests /analytics?dataset=v6_sample&vertical=Khoros
2. Server loads all items from summary CSV
3. Extract filter options (verticals, products, statuses, priorities)
4. Apply filters
5. Compute in parallel:
   - Summary stats (totals, percentages)
   - Pattern stats (count per pattern)
   - Vertical stats (breakdown by vertical)
   - Product stats (top products by detection rate)
   - Status/Priority/Source breakdowns
   - Pattern co-occurrence matrix
   - Hard metrics summary (averages, medians, alert counts)
6. Return AnalyticsData object
```

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API key (for LLM detection)

### Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
```

### Web Dashboard

```bash
cd web

# Install dependencies
npm install

# Configure Clerk authentication
# Create .env.local with:
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/tickets
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/tickets

# Run development server
npm run dev
```

---

## Usage

### Full Pipeline

```bash
# Run complete pipeline
python run_pipeline.py

# Or run individual steps
python run_pipeline.py --step sample    # Build sample
python run_pipeline.py --step fetch     # Fetch tickets
python run_pipeline.py --step detect    # Run LLM detection
python run_pipeline.py --step eval      # Evaluate results
python run_pipeline.py --step summarize # Generate summary
```

### LLM Detection Options

```bash
# Run on ground truth tickets only (default)
python llm_detect.py --ticket-set ground_truth

# Run on all sample tickets
python llm_detect.py --ticket-set sample

# Run on all available tickets
python llm_detect.py --ticket-set all

# Force re-run (overwrite existing results)
python llm_detect.py --force

# Custom output directory
python llm_detect.py --outdir data/poc/llm_results/my-run

# Specific tickets
python llm_detect.py --tickets 60208754,60209095
```

### Evaluation Options

```bash
# Both recall-only and full metrics (default)
python evaluate.py --results-dir data/poc/llm_results/gpt-5.2-v6

# Recall-only (ignores false positives)
python evaluate.py --results-dir data/poc/llm_results/gpt-5.2-v6 --mode recall-only

# Full precision/recall/F1
python evaluate.py --results-dir data/poc/llm_results/gpt-5.2-v6 --mode full

# Show more missed labels
python evaluate.py --results-dir data/poc/llm_results/gpt-5.2-v6 --show-misses 100
```

### Web Dashboard

```bash
cd web
npm run dev     # Development (http://localhost:3000)
npm run build   # Production build
npm start       # Start production server
```

---

## Configuration

### config.py

Central configuration for all pipeline scripts:

```python
# Paths
REPO_ROOT = Path(__file__).resolve().parent
FULL_TICKET_DATA_CSV = REPO_ROOT / "Full_Ticket_Data_*.csv"
PATTERNS_CSV = REPO_ROOT / "IgniteTech_Khoros_GFI...csv"
DATA_DIR = REPO_ROOT / "data/poc"

# Pattern definitions
OUR_PATTERNS = [
    "AI_QUALITY_FAILURES", "AI_WALL_LOOPING", "IGNORING_CONTEXT",
    "RESPONSE_DELAYS", "PREMATURE_CLOSURE", "P1_SEV1_MISHANDLING"
]

# LLM configuration
LLM_CONFIG = {
    "model": "gpt-5.2",
    "max_completion_tokens": 1800,
    "reasoning_effort": "medium",
    "max_retries": 2,
}

# Thresholds for pattern detection
RESPONSE_DELAY_THRESHOLDS = {
    "initial_response_hours": 24,
    "follow_up_gap_hours": 48,
    "resolution_time_days": 7,
}

P1_SEV1_INDICATORS = {
    "max_response_hours": 4,
    "max_resolution_hours": 24,
}
```

### Dataset Configuration (web/src/lib/datasets.ts)

```typescript
export const DATASETS = {
  v6_sample: {
    id: "v6_sample",
    label: "GPT-5.2 v6 (sample)",
    summaryCsvPath: "data/poc/poc_llm_v6_sample_summary.csv",
    csvMetricsPath: "data/poc/poc_csv_metrics.csv",
    ticketMetricsPath: "data/poc/poc_ticket_metrics.csv",
    resultsDir: "data/poc/llm_results/gpt-5.2-v6-sample",
    rawDir: "data/poc/raw",
  },
  v6_gt: {
    id: "v6_gt",
    label: "GPT-5.2 v6 (ground-truth rerun)",
    // ... similar config
  },
};
```

---

## API Reference

### Internal API Routes

#### GET /api/tickets

Query tickets with filtering and pagination.

**Query Parameters:**
- `dataset` - Dataset ID (v6_sample, v6_gt)
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 25)
- `sort` - Sort field (default: detectedCount)
- `order` - Sort order (asc, desc)
- `search` - Search term (ticket ID or product)
- `vertical` - Filter by vertical
- `product` - Filter by product
- `status` - Filter by status
- `source` - Filter by source
- `pattern` - Filter by pattern(s)
- `onlySev1` - Show only SEV1 tickets

**Response:**
```json
{
  "total": 99,
  "items": [
    {
      "ticketId": 60208754,
      "vertical": "Khoros",
      "product": "Community",
      "status": "Closed",
      "predictedLabels": ["RESPONSE_DELAYS", "IGNORING_CONTEXT"],
      "detectedCount": 2,
      "isSev1": false
    }
  ]
}
```

#### GET /api/tickets/[id]

Get full ticket detail including patterns, metrics, and transcript.

**Query Parameters:**
- `dataset` - Dataset ID

**Response:**
```json
{
  "ticketId": 60208754,
  "dataset": "v6_sample",
  "summary": { /* TicketSummaryRow */ },
  "result": {
    "RESPONSE_DELAYS": {
      "detected": true,
      "reasoning": "...",
      "evidence": ["quote 1", "quote 2"]
    }
  },
  "transcript": [
    { "ts": "2025-01-06T10:30:00Z", "actor": "Customer", "text": "..." }
  ],
  "hardMetrics": {
    "csv": { "initialResponseTime": 3600, /* ... */ },
    "interactions": { "aiCount": 5, /* ... */ },
    "flags": { "slowInitialResponse": false, /* ... */ }
  }
}
```

#### GET /api/analytics

Compute aggregate analytics with optional filters.

**Query Parameters:** Same as /api/tickets filters

**Response:**
```json
{
  "summary": { "totalTickets": 99, "ticketsWithPatterns": 75, /* ... */ },
  "patternStats": [{ "pattern": "RESPONSE_DELAYS", "count": 50, "percentage": 50.5 }],
  "verticalStats": [{ "vertical": "Khoros", "totalTickets": 40, /* ... */ }],
  "productStats": [{ "product": "Community", "totalTickets": 15, "detectionRate": 80.0 }],
  "hardMetricsSummary": {
    "avgInitialResponseHours": 12.5,
    "medianInitialResponseHours": 8.2,
    "fcrRate": 25.0,
    "escalationRate": 35.0,
    "slowResponseCount": 10
  },
  "filterOptions": {
    "verticals": ["IgniteTech", "Khoros", "GFI"],
    "products": ["Community", "Social", /* ... */]
  }
}
```

---

## License

Internal use only - IgniteTech Group.

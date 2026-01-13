#!/usr/bin/env python3
"""
Improved LLM Pattern Detection with Enhanced Prompt (v2)
- Much clearer pattern definitions
- Specific signals to look for
- Examples of what to detect
- Lower threshold for detection to reduce false negatives
"""

import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import openai

load_dotenv()

# Tickets to process
ALL_TICKETS = [
    60005284, 60005331, 60011782, 60018792, 60069509, 60073150, 60073892, 60078199, 60082637, 60094192,
    60098171, 60098583, 60100448, 60101543, 60144719, 60149875, 60163212, 60164071, 60166415, 60169826,
    60177804, 60185126, 60185905, 60186930, 60190547, 60193443, 60195349, 60196166, 60196360, 60198743,
    60201836, 60209095, 60209553, 60210541, 60211680, 60214613, 60218313, 60220499, 60220701, 60225231,
    60226631, 60227783, 60230003, 60230438, 60231299, 60231851, 60232130, 60234621, 60237327, 60238295,
    60238457, 60239883, 60240989, 60241392, 60241518, 60242814, 60247476, 60252140, 60252864, 60256173,
    60258400
]

RAW_DIR = Path('data/poc/raw')
TAGGED_DIR = Path('data/poc/tagged')
OUTPUT_DIR = Path('data/poc/llm_results/gpt-5.2-v2')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Improved system prompt with much clearer definitions
SYSTEM_PROMPT = """You are an expert support quality analyst evaluating Central Support performance.

IMPORTANT: Your job is to FIND PROBLEMS. Be vigilant and flag issues. When in doubt, DETECT the pattern - we would rather have false positives than miss real problems.

You will analyze ticket interactions and detect 6 quality patterns. Each pattern has specific signals to look for."""

# Much more detailed user prompt with specific signals
USER_PROMPT_TEMPLATE = """# Support Ticket Analysis

**Ticket ID:** {ticket_id}

## Ticket Interactions (chronological)
{interactions}

---

# PATTERN DETECTION INSTRUCTIONS

Analyze the above ticket and detect these 6 patterns. For each, I've listed SPECIFIC SIGNALS to look for. If you see ANY of these signals, mark the pattern as DETECTED.

---

## 1. AI_QUALITY_FAILURES
**Definition:** AI (ATLAS/Hermes) provides responses that are generic filler, factually wrong, or makes promises it doesn't keep.

**DETECT if you see ANY of:**
- AI sends template responses that don't address the specific issue
- AI says "Thank you for reaching out" or "We understand" without solving anything
- AI provides incorrect information or misunderstands the problem
- AI promises to send something (logs, patch, info) but never does
- AI response is just links without real analysis
- AI addresses itself as "Dear ATLAS" (broken template)
- Customer explicitly says AI is wrong or unhelpful
- AI gives troubleshooting steps that don't match the issue described

---

## 2. AI_WALL_LOOPING
**Definition:** Customer gets stuck interacting with AI, can't reach a human, or AI asks for the same information repeatedly.

**DETECT if you see ANY of:**
- Customer says "I need to speak to someone" or "talk to a human" or "real person"
- Customer explicitly says they already provided information that AI is asking for again
- Multiple AI responses asking for logs/screenshots/info that was already provided
- AI keeps sending the same troubleshooting steps multiple times
- Customer expresses frustration at AI responses
- Long chains of only AI interactions with no human response
- AI creates ticket when customer says they already have one open
- Customer says "I already tried that" or "I already sent that"

---

## 3. IGNORING_CONTEXT
**Definition:** Support ignores information customer already provided or asks for same troubleshooting steps again.

**DETECT if you see ANY of:**
- Customer mentions they already provided logs/screenshots/info
- Customer references a previous ticket where they did same troubleshooting
- Support asks for information visible earlier in the same ticket
- Customer says "as I mentioned" or "I already explained" or "see my previous message"
- Multiple requests for the same logs or screenshots
- Support suggests troubleshooting customer explicitly says they tried
- Customer has to repeat their problem description multiple times
- Support doesn't acknowledge files/logs customer uploaded

---

## 4. RESPONSE_DELAYS
**Definition:** Significant delays (multiple days) between customer message and support response.

**DETECT if you see ANY of:**
- More than 2 calendar days between a customer message and support response
- Customer has to follow up because no response received
- Messages like "any update?" or "still waiting" or "it's been X days"
- Visible gaps in timestamps showing multi-day delays
- "We apologize for the delay" or similar acknowledgment of slow response
- Customer complains about response time

---

## 5. PREMATURE_CLOSURE
**Definition:** Ticket closed while customer is waiting for promised information, or customer gives up without resolution.

**DETECT if you see ANY of:**
- Ticket closed with AI saying "no response in 7 days"
- Customer's last message was a question or request that went unanswered
- AI says it will send info/patch/solution but ticket closes without it
- Customer says "I give up" or expresses resignation
- Ticket resolved while issue is clearly not fixed
- Auto-closure messages before customer confirmed resolution
- "If we don't hear from you, ticket will be closed" followed by closure
- Customer was waiting for follow-up that never came
- Only AI interactions exist (no human ever engaged)

---

## 6. P1_SEV1_MISHANDLING
**Definition:** High-priority outage/critical issue gets standard troubleshooting instead of immediate escalation.

**DETECT if you see ANY of:**
- Words like "SEV1", "P1", "critical", "outage", "production down", "urgent", "emergency"
- Multiple users or customers affected mentioned
- Business-critical system described as not working
- Platform-wide issue reported but generic troubleshooting given
- Support asks about browser/firewall/VPN/cache for a server-side issue
- Customer mentions this issue happened before (recurring pattern)
- "Entire team can't access" or similar company-wide impact
- Issue described as blocking business operations
- Support delays escalation to engineering for clearly platform issues
- Customer mentions SLA or time-sensitivity

---

# OUTPUT FORMAT

Return a JSON object with all 6 patterns. For EACH pattern:
- "detected": true/false
- "reasoning": Brief explanation (1-2 sentences)
- "evidence": Array of quoted excerpts from the ticket that support your decision

Remember: **When in doubt, DETECT.** We need to catch problems, not miss them.

```json
{{
  "AI_QUALITY_FAILURES": {{"detected": bool, "reasoning": "...", "evidence": [...]}},
  "AI_WALL_LOOPING": {{"detected": bool, "reasoning": "...", "evidence": [...]}},
  "IGNORING_CONTEXT": {{"detected": bool, "reasoning": "...", "evidence": [...]}},
  "RESPONSE_DELAYS": {{"detected": bool, "reasoning": "...", "evidence": [...]}},
  "PREMATURE_CLOSURE": {{"detected": bool, "reasoning": "...", "evidence": [...]}},
  "P1_SEV1_MISHANDLING": {{"detected": bool, "reasoning": "...", "evidence": [...]}}
}}
```"""


def format_interactions(raw_file: Path, max_chars: int = 25000) -> str:
    """Format interactions with more context for better detection."""
    with open(raw_file, 'r') as f:
        ticket_data = json.load(f)
    
    if 'payload' not in ticket_data or 'ticket' not in ticket_data['payload']:
        return "No interaction data available."
    
    ticket = ticket_data['payload']['ticket']
    interactions = ticket.get('interactions', [])
    
    # Get requester info for context
    requester = ticket.get('metadata', {}).get('requester', {})
    requester_name = requester.get('full_name', 'Unknown Customer')
    
    lines = [f"**Customer:** {requester_name}\n"]
    
    # Reverse to get chronological order
    interactions = list(reversed(interactions))
    
    total_chars = 0
    for inter in interactions:
        if isinstance(inter, list) and len(inter) >= 2:
            timestamp = inter[0]
            text = inter[1]
            
            # Truncate very long texts but keep more content
            if len(text) > 2000:
                text = text[:1800] + "\n...[truncated]..."
            
            line = f"[{timestamp}]\n{text}\n\n---\n"
            if total_chars + len(line) > max_chars:
                lines.append("\n...[earlier interactions truncated]...")
                break
            lines.append(line)
            total_chars += len(line)
    
    return "".join(lines)


def call_gpt52(ticket_id: int) -> dict:
    """Call GPT-5.2 with improved prompt."""
    raw_file = RAW_DIR / f"ticket_{ticket_id}.json"
    if not raw_file.exists():
        return None
    
    interactions_text = format_interactions(raw_file)
    user_prompt = USER_PROMPT_TEMPLATE.format(ticket_id=ticket_id, interactions=interactions_text)
    
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        max_completion_tokens=2000,
        reasoning_effort="medium",  # Increased for better analysis
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    if not content or content.strip() == '':
        return None
    
    try:
        return json.loads(content)
    except:
        return None


def main():
    print(f"Processing {len(ALL_TICKETS)} tickets with improved prompt (v2)")
    print("=" * 60)
    
    # Filter to only tickets that need processing
    to_process = []
    for tid in ALL_TICKETS:
        output_file = OUTPUT_DIR / f"ticket_{tid}.json"
        if not output_file.exists():
            to_process.append(tid)
    
    print(f"Already done: {len(ALL_TICKETS) - len(to_process)}")
    print(f"To process: {len(to_process)}")
    print()
    
    success = 0
    failed = 0
    
    for i, tid in enumerate(to_process):
        print(f"[{i+1}/{len(to_process)}] {tid}...", end=" ", flush=True)
        try:
            result = call_gpt52(tid)
            if result:
                result['_model'] = 'gpt-5.2-v2'
                result['_ticket_id'] = tid
                with open(OUTPUT_DIR / f"ticket_{tid}.json", 'w') as f:
                    json.dump(result, f, indent=2)
                print("OK")
                success += 1
            else:
                print("EMPTY")
                failed += 1
        except Exception as e:
            print(f"ERROR: {str(e)[:60]}")
            failed += 1
        time.sleep(0.5)
    
    print()
    print("=" * 60)
    print(f"Complete: {success} success, {failed} failed")
    print(f"Total results: {len(list(OUTPUT_DIR.glob('ticket_*.json')))}")


if __name__ == "__main__":
    main()



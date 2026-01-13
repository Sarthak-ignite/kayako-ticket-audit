#!/usr/bin/env python3
"""
Balanced LLM Pattern Detection (v3)
- High recall from v2
- Better precision with stricter criteria
- Requires stronger evidence before flagging
"""

import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import openai

load_dotenv()

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
OUTPUT_DIR = Path('data/poc/llm_results/gpt-5.2-v3')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are an expert support quality analyst evaluating Central Support performance.

Your job is to identify genuine support quality issues. Be thorough but precise - only flag patterns when there is CLEAR, UNAMBIGUOUS evidence. Each detection should be defensible with specific quotes."""

USER_PROMPT_TEMPLATE = """# Support Ticket Analysis

**Ticket ID:** {ticket_id}

## Ticket Interactions (chronological)
{interactions}

---

# PATTERN DETECTION INSTRUCTIONS

Analyze the ticket for these 6 quality patterns. Each has DETECT criteria and DO NOT DETECT criteria.

---

## 1. AI_QUALITY_FAILURES

**DETECT when AI (ATLAS/Hermes) clearly fails:**
- AI provides factually incorrect information about the product
- AI promises to send something specific but it's never sent
- AI addresses itself (e.g., "Dear ATLAS") showing broken template
- Customer explicitly says the AI response is wrong or unhelpful
- AI gives completely irrelevant troubleshooting (e.g., browser steps for server issue)

**DO NOT DETECT if:**
- AI simply asks clarifying questions (that's normal)
- AI provides links to documentation (that's helpful)
- AI's response is generic but accurate
- Only internal AI notes/status updates are visible

---

## 2. AI_WALL_LOOPING

**DETECT when customer is genuinely trapped:**
- Customer explicitly says "I need a human" or "talk to real person" AND doesn't get one
- AI asks for SAME specific information 2+ times within the ticket
- Customer explicitly says "I already provided that" or "I already tried that" to AI
- 3+ consecutive AI interactions with no human response despite customer asking

**DO NOT DETECT if:**
- Customer talks to AI once then gets human help
- AI asks for different information each time
- Customer doesn't explicitly request human assistance
- Internal AI notes (not customer-facing)

---

## 3. IGNORING_CONTEXT

**DETECT when support clearly ignores provided information:**
- Customer explicitly says "I already explained" or "as I mentioned" or "see above"
- Support asks for logs/files that customer already attached earlier in SAME ticket
- Customer references previous ticket AND support ignores it
- Same troubleshooting step requested 2+ times after customer said they did it

**DO NOT DETECT if:**
- Support asks for additional/different information
- First-time request for logs or details
- Customer hasn't explicitly indicated they provided the info before

---

## 4. RESPONSE_DELAYS

**DETECT only for significant delays:**
- Gap of 3+ calendar days between customer message and support response
- Customer explicitly complains about waiting ("still waiting", "any update", "it's been X days")
- Support explicitly apologizes for delay

**DO NOT DETECT if:**
- Less than 3 days between messages
- Delays are only between internal notes
- Customer caused the delay by not responding

---

## 5. PREMATURE_CLOSURE

**DETECT when ticket closed inappropriately:**
- Customer's LAST message was a question/request that went unanswered, then ticket closed
- AI promised to send info/solution, ticket closed without it being sent
- Customer explicitly says "I give up" or expresses they're abandoning (not resolving)
- Auto-closure while customer was clearly waiting for follow-up

**DO NOT DETECT if:**
- Customer confirmed resolution before closure
- Customer requested closure
- Ticket closed after issue was actually resolved
- Standard 7-day closure after customer stopped responding with no pending items

---

## 6. P1_SEV1_MISHANDLING

**DETECT only for clearly high-severity issues mishandled:**
- Ticket explicitly marked SEV1/P1/Critical AND support gives generic troubleshooting
- "Production down" or "complete outage" reported AND support asks about browser/VPN/cache
- Multiple users/entire team affected mentioned AND no escalation visible
- Customer explicitly mentions SLA violation or time-sensitivity AND issue not prioritized

**DO NOT DETECT if:**
- No explicit severity marker (P1/SEV1/Critical/Urgent)
- Issue affects only one user's access
- Standard troubleshooting is appropriate for the issue type
- Issue is clearly not production-impacting

---

# OUTPUT FORMAT

Return JSON with all 6 patterns. Require STRONG evidence to mark detected=true.

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
    
    requester = ticket.get('metadata', {}).get('requester', {})
    requester_name = requester.get('full_name', 'Unknown Customer')
    
    lines = [f"**Customer:** {requester_name}\n"]
    
    interactions = list(reversed(interactions))
    
    total_chars = 0
    for inter in interactions:
        if isinstance(inter, list) and len(inter) >= 2:
            timestamp = inter[0]
            text = inter[1]
            
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
        reasoning_effort="medium",
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
    print(f"Processing {len(ALL_TICKETS)} tickets with balanced prompt (v3)")
    print("=" * 60)
    
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
                result['_model'] = 'gpt-5.2-v3'
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



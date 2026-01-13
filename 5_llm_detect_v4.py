#!/usr/bin/env python3
"""
LLM Pattern Detection v4 - Middle ground
- Keep v2's comprehensive signal detection
- Add nuance: require clear customer impact or explicit signals
- Less restrictive than v3, more precise than v2
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
OUTPUT_DIR = Path('data/poc/llm_results/gpt-5.2-v4')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are an expert support quality analyst evaluating Central Support performance.

Your goal: Find genuine support quality issues that negatively impacted the customer experience. Flag patterns when there's reasonable evidence - you don't need absolute proof, but there should be clear indicators in the ticket."""

USER_PROMPT_TEMPLATE = """# Support Ticket Analysis

**Ticket ID:** {ticket_id}

## Ticket Interactions (chronological)
{interactions}

---

# DETECT THESE 6 PATTERNS

For each pattern, I list what to look for. Mark as DETECTED if you find reasonable evidence.

---

## 1. AI_QUALITY_FAILURES
AI (ATLAS/Hermes) responses are unhelpful, wrong, or misleading.

**Look for:**
- AI sends generic template without addressing the actual issue
- AI provides links but no actual analysis or answer
- AI promises something ("I will send", "team is analyzing") that doesn't happen
- AI gives wrong information or misunderstands the problem
- AI addresses itself ("Dear ATLAS") - broken template
- Customer explicitly says AI response was unhelpful

**Not a failure:** AI asking clarifying questions or requesting logs is normal and helpful.

---

## 2. AI_WALL_LOOPING
Customer stuck in AI loop, can't reach human, or AI repeats itself.

**Look for:**
- Customer asks for human/agent AND only gets more AI responses
- AI asks for same information 2+ times in the ticket
- Customer says "I already provided that" or "I already tried that"  
- Multiple AI messages without human intervention when customer needs human help
- Customer expresses frustration with AI specifically

**Not looping:** Single AI interaction before human takes over.

---

## 3. IGNORING_CONTEXT
Support ignores information customer already provided.

**Look for:**
- Customer says "I already explained", "as I mentioned", "see my previous message"
- Support asks for logs/info that customer attached earlier in the ticket
- Customer references previous ticket and support doesn't acknowledge
- Same troubleshooting suggested after customer said they tried it
- Support doesn't process feedback customer gave on a solution

**Not ignoring:** Asking for additional or different information.

---

## 4. RESPONSE_DELAYS  
Significant delays between customer message and support response.

**Look for:**
- 3+ calendar days gap between customer message and response
- Customer follows up asking for update or says they're waiting
- Support apologizes for delay
- Ticket shows long periods of no activity while issue is open

**Not a delay:** Normal business hours response times, customer-caused delays.

---

## 5. PREMATURE_CLOSURE
Ticket closed without resolution, or customer gave up.

**Look for:**
- Customer's last message was unanswered question/request, then ticket closed
- AI/support promised to send something, ticket closed without sending it
- Customer says "I give up" or indicates they're giving up (not resolving)
- Ticket auto-closed while customer was waiting for information
- No resolution evidence but ticket marked closed/resolved
- Only AI interactions exist throughout (no human engaged)

**Not premature:** Customer confirmed resolution, customer stopped responding with no pending items.

---

## 6. P1_SEV1_MISHANDLING
High-severity/urgent issues handled with standard process instead of urgency.

**Look for:**
- Customer reports outage/critical/urgent issue AND gets generic troubleshooting
- "Production down", "affecting all users", "business blocked" AND no escalation visible
- Platform-side issue AND support asks about browser/VPN/firewall
- Customer mentions this is a recurring issue AND treated as new
- Customer explicitly mentions urgency/SLA AND issue not prioritized

**Not mishandling:** Single-user issues, issues that genuinely need troubleshooting first.

---

# OUTPUT

Return JSON. Mark detected=true if you find reasonable evidence. Provide quotes.

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
    print(f"Processing {len(ALL_TICKETS)} tickets with v4 prompt")
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
                result['_model'] = 'gpt-5.2-v4'
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


if __name__ == "__main__":
    main()



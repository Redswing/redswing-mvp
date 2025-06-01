import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_message(message: str) -> dict:
    prompt = f"""
You are a smart assistant helping users log their golf, tennis, or pickleball performance through text messages.

Each message should be analyzed and converted to structured JSON using one of the following intents:

### INTENTS:
- "log_match" → Match result, e.g. score, outcome, opponent
- "log_stat" → Stat tracking, e.g. number of putts, types of errors, context info
- "get_summary" → Request for stats summary or trends
- "get_help" → Asking for help or guidance
- "unknown" → Message is unclear or not related to the app

### For "log_match", include:
- sport: "golf", "tennis", "pickleball" or "unknown"
- opponent: name or "N/A"
- score: string like "85" or "6-4, 6-3"
- outcome: "win", "loss", "draw", or "N/A"
- response: short friendly message

### For "log_stat", include:
- sport: "golf", "tennis", "pickleball" or "unknown"
- stat_type: e.g. "putts", "misses", "winners", "errors"
- stat_value: number or string (e.g. "32", "backhand", "deep")
- context: optional — e.g. "hole 7", "vs lefty", "first set"
- notes: optional comments from user
- response: short friendly message confirming stat

### If unclear, set intent to "unknown" and write a helpful response.

---

### Examples:

1. "Shot 88 with 32 putts"
→ intent: log_stat, sport: golf, stat_type: "putts", stat_value: 32, context: "18-hole round", notes: "", response: ✅ Got it! Logged 32 putts for your round.

2. "Beat Jamie 6-4, 6-2 in tennis"
→ intent: log_match, sport: tennis, opponent: Jamie, score: 6-4, 6-2, outcome: win, response: ✅ Match logged! You beat Jamie in tennis.

3. "I missed mostly on the forehand side"
→ intent: log_stat, sport: tennis, stat_type: "misses", stat_value: "forehand", context: "general", notes: "", response: Logged your shot tendency — we'll track that!

4. "Help"
→ intent: get_help, response: 🛠 You can log matches, track stats, or get summaries...

5. "Played Bob"
→ intent: unknown, response: ❓ I didn’t catch the score or sport. Can you send that again like “Beat Bob 6-3, 6-4 in tennis”?

Now parse this: \"{message.strip()}\"
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    raw = response.choices[0].message.content.strip()
    try:
        parsed = eval(raw)
        return parsed
    except Exception as e:
        return {
            "intent": "unknown",
            "response": "❓ Sorry, I couldn’t understand that. Can you rephrase your match result or stat?"
        }
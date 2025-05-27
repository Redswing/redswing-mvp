import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def parse_message(message: str):
    system_prompt = """
You are a smart assistant that helps users track golf and racquet sport matches by text message.

You must:
- Identify the user's **intent**: one of ["log_match", "get_summary", "get_help", "unknown"]
- If logging a match, extract: sport, opponent, score, outcome (win/loss/draw/N/A)
- Reply in JSON format like this:

{
  "intent": "log_match",
  "sport": "golf",
  "opponent": "N/A",
  "score": "85",
  "outcome": "N/A",
  "response": "✅ Match logged! Score: 85 in golf."
}

Always include the full response to send back to the user.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        temperature=0.2
    )

    try:
        return eval(response.choices[0].message["content"])
    except Exception:
        return {
            "intent": "unknown",
            "sport": None,
            "opponent": None,
            "score": None,
            "outcome": None,
            "response": "Sorry, I didn’t understand that. Try texting a match result like 'Beat Jamie 6-3, 6-4 in tennis.'"
        }
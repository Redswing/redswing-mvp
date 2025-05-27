from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_message(message: str) -> dict:
    prompt = f"""Extract intent and data from: "{message}".
Return JSON like:
{{
  "intent": "log_match",
  "sport": "golf",
  "opponent": "N/A",
  "score": "85",
  "outcome": "N/A",
  "response": "✅ Match logged! You shot 85 in golf."
}}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return eval(response.choices[0].message.content)
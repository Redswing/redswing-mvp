import os
from dotenv import load_dotenv

load_dotenv()  # ✅ This ensures SUPABASE_URL and key are loaded

from supabase import create_client
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def get_summary(user_id: str) -> str:
    # Step 1: Get recent 5–10 sessions
    result = supabase.table("sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
    matches = result.data

    if not matches:
        return "You don't have any matches logged yet. Just text your scores and I'll track them!"

    # Step 2: Format the matches into a bullet list
    match_list = []
    for m in matches:
        sport = m.get("sport", "unknown")
        score = m.get("score", "N/A")
        opponent = m.get("opponent", "N/A")
        outcome = m.get("outcome", "N/A")
        match_list.append(f"- {sport.title()} vs {opponent}, Score: {score}, Outcome: {outcome}")

    history_text = "\n".join(match_list)

    # Step 3: Send to GPT for summary
    prompt = f"""
Here's a user's last few match logs:

{history_text}

Write a concise 3-4 sentence summary of their performance. Mention any win streaks, score trends, or insights.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message["content"].strip()
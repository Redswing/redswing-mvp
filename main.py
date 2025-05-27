from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client
from utils.gpt_parser import parse_message
from utils.summary_generator import get_summary
from twilio.rest import Client
import os
import re

load_dotenv()
app = FastAPI()

# Supabase and Twilio setup
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

# CORS for Webflow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Can be tightened to your Webflow domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalize_us_phone(raw_phone: str) -> str:
    digits = re.sub(r"\D", "", raw_phone)
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    elif digits.startswith("+") and 11 <= len(digits) <= 15:
        return digits
    else:
        raise ValueError("Invalid phone number format")

@app.post("/web-signup")
async def web_signup(request: Request):
    form = await request.form()
    raw_phone = form.get("phone") or form.get("phone-2")

    if not raw_phone:
        return PlainTextResponse("Missing phone number", status_code=400)

    try:
        phone = normalize_us_phone(raw_phone.strip())
    except ValueError:
        return PlainTextResponse("Invalid phone number format. Please use a valid U.S. number.", status_code=400)

    whatsapp_phone = f"whatsapp:{phone}"

    try:
        user_res = supabase.table("users").select("id").eq("phone", whatsapp_phone).execute()
        if user_res.data:
            # Already exists — send confirmation message
            twilio_client.messages.create(
                body=(
                    "👋 You're already signed up for Redswing!\n\n"
                    "Just text me your golf or match results anytime, and I’ll log them for you.\n"
                    "Need help? Just text 'help'."
                ),
                from_=twilio_whatsapp_number,
                to=whatsapp_phone
            )
            return PlainTextResponse("User already exists", status_code=200)

        # Create user and send welcome message
        supabase.table("users").insert({"phone": whatsapp_phone}).execute()

        twilio_client.messages.create(
            body=(
                "👋 Welcome to Redswing — your match tracker for golf, pickleball, and tennis.\n\n"
                "Just text something like:\n"
                "“Shot 85 at Pinehurst”\n"
                "or “Beat Jamie 6-3, 6-4 in tennis”\n\n"
                "I’ll log it automatically.\n"
                "Text “help” anytime to see what you can do."
            ),
            from_=twilio_whatsapp_number,
            to=whatsapp_phone
        )

        return PlainTextResponse("Signup successful", status_code=200)

    except Exception as e:
        print("Error in /web-signup:", e)
        return PlainTextResponse("Something went wrong", status_code=400)

@app.post("/sms")
async def receive_message(request: Request):
    form = await request.form()
    message_body = form.get("Body").strip().lower()
    from_number = form.get("From")

    # Check or create user
    user_res = supabase.table("users").select("id").eq("phone", from_number).execute()
    if user_res.data:
        user_id = user_res.data[0]["id"]
    else:
        new_user = supabase.table("users").insert({"phone": from_number}).execute()
        user_id = new_user.data[0]["id"]

        twilio_client.messages.create(
            body="👋 Welcome to Redswing! Just text a result like 'Shot 88 at Pinehurst' to get started. Text 'help' for commands.",
            from_=twilio_whatsapp_number,
            to=from_number
        )
        return "OK"

    # ✅ Manual intent override
    if message_body in ["help", "commands", "what can you do"]:
        response_text = (
            "🛠 Here’s what you can do with Redswing:\n\n"
            "• Log a match — just text your result:\n"
            "  'Shot 88 at Pinehurst' or 'Beat Sam 6-4, 6-3 in tennis'\n\n"
            "• Get your stats — text 'summary'\n"
            "• Ask for help — text 'help' anytime\n\n"
            "📌 No app needed. Just play and text me."
        )
    elif message_body == "summary":
        response_text = get_summary(user_id)
    else:
        # Use GPT to parse the message
        parsed = parse_message(message_body)
        response_text = parsed.get("response", "Got it!")

        # Log the session
        supabase.table("sessions").insert({
            "user_id": user_id,
            "sport": parsed.get("sport"),
            "opponent": parsed.get("opponent"),
            "score": parsed.get("score"),
            "outcome": parsed.get("outcome"),
            "raw_message": message_body,
            "parsed_json": parsed
        }).execute()

    # Send the response
    twilio_client.messages.create(
        body=response_text,
        from_=twilio_whatsapp_number,
        to=from_number
    )

    return "OK"


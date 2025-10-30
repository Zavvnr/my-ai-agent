# agent.py (Updated with MCP)

import os
import smtplib
import requests
import google.generativeai as genai
import sys
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime, timedelta

print(f"--- Using google-generativeai version: {genai.__version__} ---")

# Load environment variables from .env file
load_dotenv()

# Configuration (all your keys and tokens)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GMAIL_SENDER = os.getenv('GMAIL_SENDER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
CANVAS_API_TOKEN = os.getenv('CANVAS_API_TOKEN')
CANVAS_BASE_URL = os.getenv('CANVAS_BASE_URL')
LOCATION = "Madison, Wisconsin"
TIMEZONE = "America/Chicago"

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

#
# -----------------------------------------------------
# START MCP IMPLEMENTATION
# -----------------------------------------------------
#

# 1. DEFINE THE SYSTEM INSTRUCTION (THE "RECIPE")
# This is your main prompt, telling the AI its job.
SYSTEM_INSTRUCTION = """
You are a helpful and motivational morning assistant.
Your task is to create a short, inspiring morning briefing for a university student.
The tone should be positive and encouraging. Start with a friendly greeting.

Format the output as a simple HTML email. Do not include <html> or <body> tags.
Use <h2> for the main title, <h3> for sub-sections, <p> for paragraphs, and <ul> and <li> for lists.

Based on the user's provided information (quote, weather, and Canvas tasks), generate:
1.  A "Today's Priorities" to-do list with 3-4 actionable items. Prioritize anything due today or tomorrow.
2.  A "Weekly Outlook" section that lists the other Canvas items.
"""

# 2. CREATE THE MODEL WITH THE INSTRUCTION
# We will get this name from your log. It might be 'models/gemini-1.0-pro'
# or 'models/text-bison-001'
THE_CORRECT_MODEL_NAME = "models/gemini-2.5-pro" 

model = genai.GenerativeModel(
    THE_CORRECT_MODEL_NAME,
    system_instruction=SYSTEM_INSTRUCTION
)

#
# -----------------------------------------------------
# END MCP IMPLEMENTATION
# -----------------------------------------------------
#

# ... (get_quote, get_weather, and get_canvas_events functions stay exactly the same) ...
def get_quote():
    # ... (your existing code) ...
    pass

def get_weather(city):
    # ... (your existing code) ...
    pass

def get_canvas_events():
    # ... (your existing code) ...
    pass


# 3. SIMPLIFY THE GENERATE FUNCTION (THE "INGREDIENTS")
# This function now only sends the *data* for the day.
def generate_ai_briefing(quote, weather, canvas_events):
    """Uses Gemini to generate a motivational to-do list."""
    
    # This is the "User Prompt". It's just the data.
    prompt = f"""
    Here is today's information for my briefing:
    - Today's date is {datetime.now().strftime('%A, %B %d, %Y')}.
    - Inspirational Quote: {quote}
    - Weather Forecast: {weather}
    - Upcoming from Canvas Calendar:
    {canvas_events}
    """
    
    try:
        # The model already knows how to format this
        # thanks to the system_instruction.
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error sending email: {e}", file=sys.stderr)
        # THIS IS THE ERROR WE'VE BEEN SEEING
        return f"<h3>Have a wonderful day!</h3><p>Could not generate AI suggestions. Error: {e}</p>"

# ... (send_email and main execution block stay the same) ...
def send_email(html_content):
    # ... (your existing code) ...
    pass

if __name__ == "__main__":
    print("Agent is running...")
    # 1. Gather data
    daily_quote = get_quote()
    weather_forecast = get_weather(LOCATION)
    canvas_events = get_canvas_events()

    # 2. Think with AI
    ai_content = generate_ai_briefing(daily_quote, weather_forecast, canvas_events)

    # 3. Send the email
    send_email(ai_content)
    print("Agent has finished its task.")

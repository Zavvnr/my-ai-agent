# agent.py (Updated with full debugging print statements)

import os
import smtplib
import requests
import google.generativeai as genai
import pytz
import sys  # We'll use this for error printing
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime, timedelta

# --- This print statement is already here and working ---
print(f"--- Using google-generativeai version: {genai.__version__} ---")

# Load environment variables from .env file
load_dotenv()

# Configuration
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
# MCP IMPLEMENTATION
# -----------------------------------------------------
#

# 1. DEFINE THE SYSTEM INSTRUCTION (THE "RECIPE")
SYSTEM_INSTRUCTION = """
You are a helpful and motivational morning assistant.
Your task is to create a short, inspiring morning briefing for a university student.
The tone should be positive and encouraging. Start with a friendly greeting.

Format the output as a simple HTML email. Do not include <html> or <body> tags.
Use <h2> for the main title, <h3> for sub-sections, <p> for paragraphs, and <ul> and <li> for lists.

Based on the user's provided information (quote, weather, and Canvas tasks), generate:
1.  A "Today's Priorities" to-do list with 3-4 actionable items. Prioritize conferences/one-time events before anything due today or tomorrow.
2.  A "Weekly Outlook" section that lists the other Canvas items.
"""

# 2. CREATE THE MODEL (Using the "pro" model you chose)
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

def get_quote():
    print("DEBUG: Fetching quote...")
    try:
        response = requests.get("https://zenquotes.io/api/random")
        response.raise_for_status()
        data = response.json()[0]
        return f'"{data["q"]}" - {data["a"]}'
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Error fetching quote: {e}", file=sys.stderr)
        return "Could not fetch a quote today, but make it a great day!"

def get_weather(city):
    print("DEBUG: Fetching weather...")
    try:
        url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=1&aqi=no&alerts=no"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        forecast = data['forecast']['forecastday'][0]['day']
        condition = forecast['condition']['text']
        temp_f = forecast['avgtemp_f']
        return f"Today in {city}, expect {condition} with an average temperature of {temp_f}°F."
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Error fetching weather: {e}", file=sys.stderr)
        return "Could not fetch the weather."

# GET CANVAS EVENTS
def get_canvas_events():
    print("DEBUG: Fetching Canvas events...")
    if not CANVAS_API_TOKEN or not CANVAS_BASE_URL:
        print("DEBUG: Canvas not configured.")
        return "Canvas integration not configured."

    api_url = f"{CANVAS_BASE_URL}/api/v1/users/self/upcoming_events"
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        events = response.json()

        if not events:
            print("DEBUG: No Canvas events found.")
            return "You have no upcoming assignments or events. Great job staying on top of things!"

        formatted_events = []
        local_tz = pytz.timezone(TIMEZONE)
        now = datetime.now(local_tz)

        for event in events[:7]: # Get up to 7 items
            time_str = None
            prefix = "Event" # Default prefix
            if event.get('plannable', {}).get('due_at'):
                time_str = event['plannable']['due_at']
                prefix = "Due"
            elif event.get('start_at'):
                time_str = event['start_at']
                prefix = "Starts"
            if not time_str:
                continue

            event_utc = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            event_local = event_utc.astimezone(local_tz)
            
            if event_local < now:
                continue

            if event_local.date() == now.date():
                day_str = f"Today at {event_local.strftime('%-I:%M %p')}"
            elif event_local.date() == (now + timedelta(days=1)).date():
                day_str = f"Tomorrow at {event_local.strftime('%-I:%M %p')}"
            else:
                day_str = f"on {event_local.strftime('%A, %b %d')}"

            title = event.get('title', 'No Title')
            course = event.get('context_name', 'General')
            formatted_events.append(f"- {prefix} {day_str}: [{course}] - {title}")

        return "\n".join(formatted_events) if formatted_events else "No upcoming events with due dates found."

    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Error fetching Canvas events: {e}", file=sys.stderr)
        return "Could not connect to Canvas."

def generate_ai_briefing(quote, weather, canvas_events):
    print("DEBUG: Inside generate_ai_briefing function.")
    prompt = f"""
    Here is today's information for my briefing:
    - Today's date is {datetime.now().strftime('%A, %B %d, %Y')}.
    - Inspirational Quote: {quote}
    - Weather Forecast: {weather}
    - Upcoming from Canvas Calendar:
    {canvas_events}
    """
    
    try:
        print("DEBUG: Calling AI model (gemini-2.5-pro)...")
        response = model.generate_content(prompt)
        
        if not response.text:
            print("DEBUG: AI returned an EMPTY response.")
        else:
            # Slice to avoid spamming the log
            print(f"DEBUG: AI returned a response. Start: {response.text[:70]}...")
            
        return response.text
        
    except Exception as e:
        # Use stderr to make sure this error appears
        print(f"CRITICAL: Error during AI generation: {e}", file=sys.stderr)
        return f"<h3>Error during AI generation</h3><p>{e}</p>" # Return an error message to email

def send_email(html_content):
    print("DEBUG: Inside send_email function.")
    
    if not html_content:
        print("DEBUG: HTML content is empty. Skipping email.")
        return # Don't send a blank email

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Your Morning Briefing - {datetime.now().strftime('%B %d')}"
    msg['From'] = GMAIL_SENDER
    msg['To'] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_content, 'html'))

    try:
        print("DEBUG: Attempting SMTP connection...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            print("DEBUG: Attempting SMTP login...")
            smtp_server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            print("DEBUG: Attempting to send mail...")
            smtp_server.sendmail(GMAIL_SENDER, RECIPIENT_EMAIL, msg.as_string())
        print("Email sent successfully!") # This is the original, good print

    except Exception as e:
        # Use stderr to make sure this error appears
        print(f"CRITICAL: Error sending email: {e}", file=sys.stderr)


# UPDATED MAIN EXECUTION BLOCK
if __name__ == "__main__":
    print("Agent is running...")
    
    # 1. Gather data
    daily_quote = get_quote()
    # Slice to keep log clean
    print(f"DEBUG: Quote retrieved: {daily_quote[:30]}...") 
    
    weather_forecast = get_weather(LOCATION)
    print(f"DEBUG: Weather retrieved: {weather_forecast}")
    
    canvas_events = get_canvas_events()
    # Slice to keep log clean
    print(f"DEBUG: Canvas events retrieved: {canvas_events[:50]}...")

    # 2. Think with AI
    print("DEBUG: Calling generate_ai_briefing...")
    ai_content = generate_ai_briefing(daily_quote, weather_forecast, canvas_events)

    # 3. Send the email
    print("DEBUG: Calling send_email...")
    send_email(ai_content)
    
    print("Agent has finished its task.")

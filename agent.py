# agent.py (Updated Version)

import os
import smtplib
import requests
import google.generativeai as genai
import pytz # New import for timezones
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GMAIL_SENDER = os.getenv('GMAIL_SENDER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
CANVAS_API_TOKEN = os.getenv('CANVAS_API_TOKEN') # New
CANVAS_BASE_URL = os.getenv('CANVAS_BASE_URL')   # New
LOCATION = "Madison, Wisconsin"
TIMEZONE = "America/Chicago" # For converting UTC dates from Canvas

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def get_quote():
    """Fetches a random quote from the ZenQuotes API."""
    try:
        response = requests.get("https://zenquotes.io/api/random")
        response.raise_for_status()
        data = response.json()[0]
        return f'"{data["q"]}" - {data["a"]}'
    except requests.exceptions.RequestException as e:
        print(f"Error fetching quote: {e}")
        return "Could not fetch a quote today, but make it a great day!"

def get_weather(city):
    """Fetches weather for a given city."""
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
        print(f"Error fetching weather: {e}")
        return "Could not fetch the weather."

# GET CANVAS EVENTS
def get_canvas_events():
    """Fetches upcoming events from the Canvas calendar."""
    if not CANVAS_API_TOKEN or not CANVAS_BASE_URL:
        return "Canvas integration not configured."

    api_url = f"{CANVAS_BASE_URL}/api/v1/users/self/upcoming_events"
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        events = response.json()

        if not events:
            return "You have no upcoming assignments or events. Great job staying on top of things!"

        # Let's format the events nicely
        formatted_events = []
        local_tz = pytz.timezone(TIMEZONE)
        now = datetime.now(local_tz)

        for event in events[:5]: # Get the top 5 events
            due_str = event.get('plannable', {}).get('due_at')
            if not due_str:
                continue

            # Convert UTC time from Canvas to local time
            due_utc = datetime.fromisoformat(due_str.replace('Z', '+00:00'))
            due_local = due_utc.astimezone(local_tz)

            # Format the due date string
            if due_local.date() == now.date():
                day_str = f"Today at {due_local.strftime('%-I:%M %p')}"
            elif due_local.date() == (now + timedelta(days=1)).date():
                day_str = f"Tomorrow at {due_local.strftime('%-I:%M %p')}"
            else:
                day_str = f"on {due_local.strftime('%A, %b %d')}"

            title = event.get('title', 'No Title')
            course = event.get('context_name', 'General')
            formatted_events.append(f"- Due {day_str}: [{course}] - {title}")

        return "\n".join(formatted_events) if formatted_events else "No upcoming events with due dates found."

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Canvas events: {e}")
        return "Could not connect to Canvas."

def generate_ai_briefing(quote, weather, canvas_events):
    """Uses Gemini to generate a motivational to-do list, now with Canvas info."""
    prompt = f"""
    You are a helpful and motivational morning assistant.
    Your task is to create a short, inspiring morning briefing for a university student.
    Today's date is {datetime.now().strftime('%A, %B %d, %Y')}.
    
    Here is today's information:
    - Inspirational Quote: {quote}
    - Weather Forecast: {weather}
    - Upcoming from Canvas Calendar:
    {canvas_events}

    Based on all this information, especially the upcoming deadlines from Canvas, generate a short, actionable to-do list for the day with 3-4 items.
    If there are assignments due today or tomorrow, make them a priority.
    The tone should be positive and encouraging. Start with a friendly greeting.
    Format the output as a simple HTML email. Do not include `<html>` or `<body>` tags.
    Use `<h2>` for the main title, `<h3>` for sub-sections, `<p>` for paragraphs, and `<ul>` and `<li>` for the list.
    Make sure to have a section for "Upcoming Deadlines" that lists the Canvas items.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating AI content: {e}")
        return "<h3>Have a wonderful day!</h3><p>Could not generate AI suggestions, but focus on your top priority and you'll do great.</p>"

def send_email(html_content):
    """Sends the email using Gmail's SMTP server."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Your Morning Briefing - {datetime.now().strftime('%B %d')}"
    msg['From'] = GMAIL_SENDER
    msg['To'] = RECIPIENT_EMAIL

    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            smtp_server.sendmail(GMAIL_SENDER, RECIPIENT_EMAIL, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# UPDATED MAIN EXECUTION BLOCK
if __name__ == "__main__":
    print("Agent is running...")
    # 1. Gather data
    daily_quote = get_quote()
    weather_forecast = get_weather(LOCATION)
    canvas_events = get_canvas_events() # New call

    # 2. Think with AI
    ai_content = generate_ai_briefing(daily_quote, weather_forecast, canvas_events) # Pass new data

    # 3. Send the email
    send_email(ai_content)
    print("Agent has finished its task.")
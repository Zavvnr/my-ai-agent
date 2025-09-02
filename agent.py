# agent.py

import os
import smtplib
import requests
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GMAIL_SENDER = os.getenv('GMAIL_SENDER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
LOCATION = "Madison, Wisconsin" # Our location from context

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_quote():
    """Fetches a random quote from a free API."""
    try:
        response = requests.get("https://api.quotable.io/random")
        response.raise_for_status() # Raise an exception for bad status codes
        data = response.json()
        return f'"{data["content"]}" - {data["author"]}'
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

def generate_ai_briefing(quote, weather):
    """Uses Gemini to generate a motivational to-do list."""
    prompt = f"""
    You are a helpful and motivational morning assistant.
    Your task is to create a short, inspiring morning briefing.
    Today's date is {datetime.now().strftime('%A, %B %d, %Y')}.
    
    Here is today's information:
    - Inspirational Quote: {quote}
    - Weather Forecast: {weather}

    Based on the quote and the weather, generate a short, actionable to-do list for the day with 3-4 items.
    The tone should be positive and encouraging. Start with a friendly greeting.
    Format the output as a simple HTML email. Do not include `<html>` or `<body>` tags.
    Use `<h2>` for the main title, `<h3>` for sub-sections, `<p>` for paragraphs, and `<ul>` and `<li>` for the list.
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

    # Attach the HTML content
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            smtp_server.sendmail(GMAIL_SENDER, RECIPIENT_EMAIL, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


if __name__ == "__main__":
    print("Agent is running...")
    # 1. Gather data
    daily_quote = get_quote()
    weather_forecast = get_weather(LOCATION)

    # 2. Think with AI
    ai_content = generate_ai_briefing(daily_quote, weather_forecast)

    # 3. Send the email
    send_email(ai_content)
    print("Agent has finished its task.")
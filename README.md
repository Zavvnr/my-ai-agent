This is a Personal Project

my-ai-agent was made with the help of google gemini. The purpose of this agent is to send an email to brief me in the morning about things that I need to do alongside a quote for the day and the weather condition. The reason for making this is because my habit of checking my email each morning to look for news, opportunities, etc. 

The program works by fetching data through weather API, canvas API, and gemini-2.5 pro. Using google, weather, and canvas APIs. The email sender is set to my personal email while the receiver is my school outlook email. This program will hopefully continue to improve my flexibility in desiding my actions and will continuously be improved with new ideas.

More specific workflow:
The program is divided into two main parts
- The Conductor (GitHub Actions): This is the main.yml file. It's the "boss" that wakes up, sets up the environment, and tells the script to run.
- The Worker (Python Script): This is the agent.py file. It's the "worker" that does all the actual tasks.

1. The Conductor (main.yml Workflow)
This process is the "how" and "when" the script runs.
- The Trigger: Your workflow starts in one of two ways:
    - On a schedule: The cron: '0 12 * * *' line tells GitHub to run this job automatically at 6:45 am CDT every day.
    - Manually: The workflow_dispatch: line allows you to go to the "Actions" tab on GitHub and manually runs a new workflow.

- The Setup: Once triggered, a fresh virtual computer (an ubuntu-latest runner) boots up and does the following:
    - actions/checkout@v3: It downloads a copy of the repository's code (agent.py, check_models.py, etc.).
    - actions/setup-python@v4: It installs the specific version of Python (3.10).
    - pip install ...: Installs the Python libraries the script needs, like google-generativeai, requests, and pytz. We added pip cache purge and --no-cache-dir to ensure it always gets the newest versions and doesn't use old, broken ones.

- The "Run" Command: This is the most important step.
    - The env: block securely injects all your GitHub Secrets (like GOOGLE_API_KEY, GMAIL_APP_PASSWORD, CANVAS_API_TOKEN, etc.) as environment variables.
    - It then runs the command python -u agent.py. The -u flag (which we added) ensures all print statements show up in the log immediately, which is crucial for debugging.

2. The Worker (agent.py Script)
This is the logical flow of the Python script from top to bottom.
- Initialization:
    - The script starts and prints "Agent is running...".
    - It loads all the environment variables (the secrets) that the main.yml file provided.
    - It configures the Google AI client with your GOOGLE_API_KEY.

- Model Context Protocol (MCP) Setup:
    - System Instruction: Define the SYSTEM_INSTRUCTION variable. This is the "recipe" or "persona" for the AI. It tells the model what its job is (e.g., "You are a motivational assistant," "Format as HTML," "Use <h2> tags," etc.).
    - Model Creation: Create the model object (e.g., gemini-2.5-pro) and pass that SYSTEM_INSTRUCTION in immediately. The model now "knows" its job before it even sees data.

- Data Gathering:
    - get_quote(): Script calls the ZenQuotes API and gets a random quote.
    - get_weather(): Calls the WeatherAPI (using WEATHER_API_KEY) and gets the forecast for Madison, WI.
    - get_canvas_events(): It calls the Canvas API (using CANVAS_API_TOKEN) and gets a list of upcoming assignments.

- AI Generation (The MCP "Payload"):
    - generate_ai_briefing() is called.
    - It bundles all the data gathered (the quote, weather, and task list) into a simple prompt.
    - It sends only this data (the "ingredients") to the model.
    - The model (which already has its "recipe") combines the instructions with the ingredients to generate the final, formatted HTML.

- Delivery:
    - send_email() is called with the AI's HTML response.
    - The script checks if the HTML is empty. If it is (because the AI failed), it skips sending an email (this is the key bug we fixed).
    - If the HTML is not empty, it connects to Google's mail server (smtp.gmail.com).
    - It securely logs in using GMAIL_SENDER email and the 16-digit GMAIL_APP_PASSWORD.
    - It sends the final email to the RECIPIENT_EMAIL.
    - It prints "Email sent successfully!".

- Finish:
    - The script prints "Agent has finished its task." and exits. The GitHub Action runner sees the script finished successfully and reports a green checkmark.

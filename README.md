# Assignment Planning Agent

## Overview
Assignment Planning Agent is a Python-based agentic AI application that helps students plan, manage, and track assignments, prioritize deadlines, as well as plan study sessions to maximize their academic progress in the midst of messy deadlines and constrained time. This agent recommends what to study, creates weekly plans, and records assignment progress.

It uses the auto GitHub Copilot SDK AI model that can request information through Python tools, analyze assignment data, and generate recommendations based on the user's needs.


## Features
- Study Recommendations: Recommends three ranked assignments based on available study time, deadlines, level of priority deemed by the user, and remaining work
- 7-Day Study Plan: Generates a seven-day plan that includes assignments, deadlines, session durations, daily totals, and a weekly total
- Progress Tracking: Records study minutes and updates assignment completion status
- Assignment Overview: Displays assignment titles, courses, due dates, level of priority, and remaining worktime

Other:

- AI Tool Calling: Allows the AI model to request assignment information and the current date and time through Python functions
- Bounded Agent Loop: Limits the number of model-response steps to prevent an agent run from continuing indefinitely

## How It Works
The application follows a reason-act-observe workflow:

1. User Input: The user selects an option from the command-line menu
2. Reason: The AI model determines what information it needs
3. Act: The model requests an approved Python tool
4. Observe: The application executes the tool and returns the results to the model
5. Respond: The model analyzes the results and either requests another tool or generates a final response

Note: The agent can make multiple tool calls depending on the user's request, subject to a maximum of eight model-response steps per run

## How to Run

<ins> Prerequisites: <ins>

- Python 3.10+ installed on your computer (Main programming language)
- asyncio (Included with Python; Runs the asynchronous agent workflow)
- json (Included with Python; Reads and writes assignment data)
- datetime and pathlib (Included with Python; Handle dates, times, and file paths)
- Access to the GitHub Copilot SDK and it's required authentication (Connects the application to the AI model)
- The project dependencies listed in requirements.txt

<ins> Install <ins>

1. Download the Repository (Choose either ZIP download or git clone)

Download ZIP: On the GitHub repository page, click Code → Download ZIP. Extract the downloaded files and open the project folder in your terminal or code editor

git clone: Open terminal

run:

git clone https://github.com/nzm9/assignment-planning-agent.git

cd assignment-planning-agent

2. Create virtual environment

From project root directory, run:
python -m venv .venv

3. Activate virtual environment (choose command that matches your operating system and terminal):

- Windows PowerShell (recommended):
.\.venv\Scripts\Activate.ps1

Note: If PowerShell blocks script execution, you can temporarily allow activation scripts for the current terminal session:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

This setting applies only to the current PowerShell session and resets when the terminal is closed, it is temporary and does not permanently change system settings. If you encounter any other issues activating the virtual environment, verify that Python is installed correctly and consult the documentation for your operating system or terminal.

- Windows Command Prompt (CMD):

.venv\Scripts\activate.bat

- macOS and Linux:

source .venv/bin/activate
Once activated, the terminal prompt should display (.venv)

4. Install project dependencies

Once the virtual environment is activated, run:

python -m pip install -r requirements.txt

5. Run the application

From the project root directory, execute:

python src/main.py

6. Menu Options

When the application starts, users can select from four options:

1. What should I work on right now? (3 recommendations): Get Study Recommendations by entering the number of minutes available and receive ranked study suggestions
2. Plan my next 7 days: Generate a weekly assignment plan with durations, deadlines, and workload totals
3. Update my progress: Record the minutes spent studying an assignment and save the updated progress
4. Show all assignments and deadlines: View all assignments and their current status

## Other 

### Assignment data

Assignment records are stored in data/assignments.json

Each record contains the following information:

- Assignment ID
- Course
- Assignment title
- Due date
- Status
- Estimated minutes
- Completed minutes
- Priority
- Remaining minutes

Note: Assignment priorities are currently set manually. The agent uses priority alongside deadlines, remaining work, and progress when making recommendations

## Technologies Used:
- Python
- GitHub Copilot SDK
- JSON for assignment data storage
- Visual Studio Code

Author: Nazeeha Muhammed

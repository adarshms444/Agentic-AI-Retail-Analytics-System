# components/tools.py

import os
import uuid
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly
import plotly.express
import plotly.graph_objects
import calendar
import smtplib
from email.message import EmailMessage
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
from .llm import get_llm

# Load environment variables and LLM one time
load_dotenv()
llm = get_llm()

# --- Tool 1: Web Search Tool ---
@tool
def web_search_tool(query: str) -> str:
    """
    Use this tool to find up-to-date information from the web to provide context to sales data.
    Useful for questions about competitors, market trends, or economic events.
    """
    tavily_tool = TavilySearchResults(max_results=5)
    return tavily_tool.invoke({"query": query})

# --- Tool 2: Visualization Tool ---
@tool
def visualization_tool(python_code: str) -> str:
    """
    Executes Python code that generates a Plotly chart and returns the chart's JSON string.
    The code must be complete and self-contained. It will have pandas (pd), plotly, and calendar available.
    The generated code must create a chart and assign its JSON representation to a variable named 'chart_json'.
    """
    try:
        # Define the safe "sandbox" environment for the AI's code to run in
        global_scope = {
            "pd": pd,
            "plotly": plotly,
            "px": plotly.express,
            "go": plotly.graph_objects,
            "calendar": calendar,
            "chart_json": "" # The AI's code is expected to populate this
        }
        
        exec(python_code, global_scope)
        
        # Return the JSON string created by the executed code
        return global_scope["chart_json"]
        
    except Exception as e:
        print(f"---[DEBUG] VISUALIZATION CODE FAILED. ERROR: {e} ---")
        return f"Error executing visualization code: {e}"

# --- Tool 3: Email Tool ---
@tool
def send_email_tool(to_recipient: str, subject: str, body: str) -> str:
    """
    Sends an email using the configured sender credentials.
    The 'body' argument is expected to be a complete HTML string.
    """
    sender_email = os.getenv("EMAIL_SENDER_ADDRESS")
    sender_password = os.getenv("EMAIL_SENDER_APP_PASSWORD")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 587)) # Default to 587 if not set

    if not all([sender_email, sender_password, smtp_server]):
        return "Error: Email sender credentials or server not configured in .env file."

    msg = EmailMessage()
    
    # Set the content as HTML
    msg.set_content("Please enable HTML to view this email.") # Fallback
    msg.add_alternative(body, subtype='html') # The main HTML body

    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_recipient

    try:
        # Connect to the server and send the email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() # Secure the connection
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return f"Email successfully sent to {to_recipient}."
    except Exception as e:
        print(f"Failed to send email: {e}")
        return f"Error: Failed to send email. Details: {e}"
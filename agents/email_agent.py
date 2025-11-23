# agents/email_agent.py

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_core.messages import AIMessage, HumanMessage
from components.llm import get_llm
from components.tools import send_email_tool

# --- Define your predefined team emails here ---
PREDEFINED_RECIPIENTS = ["adarshms147@gmail.com", "adarshadhi157@gmail.com"]

def run_email_agent(state: dict) -> dict:
    """
    Composes and sends a DETAILED HTML email.
    If new data exists, it uses that. If not, it formats the PREVIOUS AI response.
    """
    print("---RUNNING EMAIL AGENT (SMART CONTEXT)---")
    llm = get_llm()

    # 1. Get Inputs
    messages = state.get("messages", [])
    last_user_message = ""
    if messages and isinstance(messages[-1], HumanMessage):
        last_user_message = messages[-1].content

    structured_data_csv = state.get("structured_sql_data", "")
    
    # 2. Determine Context Source (The Fix)
    report_context = ""
    context_type = ""

    # CASE A: New Data exists in this turn
    if structured_data_csv and "Error" not in structured_data_csv and structured_data_csv.strip():
        report_context = structured_data_csv
        context_type = "raw_csv_data"
        print("---[DEBUG] Using NEW SQL data for email context.---")
    
    # CASE B: No new data, look at Chat History (Fix for 'send above report')
    else:
        print("---[DEBUG] No new data. Searching chat history for previous report...---")
        # Iterate backwards through messages, skipping the very last one (which is the 'send email' request)
        for msg in reversed(messages[:-1]):
            # We look for a substantial AI message that isn't a tool call
            if isinstance(msg, AIMessage) and len(msg.content) > 50 and not msg.content.strip().startswith("{"):
                report_context = msg.content
                context_type = "previous_chat_text"
                break
    
    if not report_context:
        return {"email_status": "Error: No data or previous report found to send."}

    # 3. Generate HTML Content
    prompt = f"""
    You are an AI assistant composing a professional HTML email report.
    
    **User Request:** "{last_user_message}"
    **Source Material type:** {context_type}
    **Content to Format:**
    ```text
    {report_context}
    ```

    **Your Task:**
    1.  **Extract Recipient:** From the User Request. If none, return "Error: No recipient".
    2.  **Generate Subject:** Create a clear subject line.
    3.  **Write HTML Body:**
        * Include the CSS style block provided below.
        * If the source is CSV, calculate totals and create a table.
        * If the source is Text (previous chat), format that text into professional HTML (headings, bullet points, paragraphs). Do not lose information.
        * Greeting/Closing: Add `<p>Hello,</p>` and `<p class="footer">Best regards,<br>Nexus Corpus Analytics Team</p>`.


    **Required CSS:**
    ```html
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; color: #333; background-color: #f9f9f9; }}
        .container {{ background-color: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        h2 {{ color: #1e3d59; border-bottom: 2px solid #1e3d59; padding-bottom: 8px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #e8f4fd; color: #1e3d59; }}
        .footer {{ margin-top: 30px; font-size: 0.9em; color: #888; }}
    </style>
    ```

    **Constraint:** Respond with ONLY a valid JSON object:
    {{ "recipient": "...", "subject": "...", "body": "<html>...</html>" }}
    """

    response = llm.invoke(prompt)
    raw_llm_output = response.content.strip()

    try:
        # Parsing Logic
        cleaned_output = raw_llm_output.strip().replace("```json", "").replace("```", "")
        email_data = json.loads(cleaned_output)
        
        recipient = email_data.get("recipient", "")
        subject = email_data.get("subject", "Analysis Report")
        body_html = email_data.get("body", "")

        # Handle Recipient
        final_recipients = []
        if recipient and "Error" not in recipient and "@" in recipient:
            final_recipients.append(recipient)
        else:
            print("---[INFO] No specific recipient found, using predefined list.---")
            final_recipients = PREDEFINED_RECIPIENTS

        # Send via Tool
        success_count = 0
        for rec in final_recipients:
            status = send_email_tool.invoke({
                "to_recipient": rec,
                "subject": subject,
                "body": body_html
            })
            if "successfully sent" in status:
                success_count += 1

        if success_count > 0:
            status_msg = f"Email successfully sent to {', '.join(final_recipients)}."
            print(f"---EMAIL SEND STATUS: {status_msg}---")
            return {"email_status": status_msg}
        else:
            return {"email_status": "Failed to send email."}

    except Exception as e:
        print(f"---EMAIL ERROR: {e}---")
        return {"email_status": f"Error generating email: {e}"}
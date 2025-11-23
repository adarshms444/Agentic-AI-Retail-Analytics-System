# graph/supervisor.py

from typing import TypedDict, List
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from components.llm import get_llm
from agents.sql_agent import run_sql_agent
from agents.web_agent import run_web_search_agent
from agents.viz_agent import run_visualization_agent
from agents.email_agent import run_email_agent
import pandas as pd
import io

class AgentState(TypedDict):
    messages: List[BaseMessage]
    next: str
    sql_data: str
    structured_sql_data: str
    web_search_data: str
    chart_path: str
    email_status: str


# -------------------------- REPLACE THIS IN GRAPH/SUPERVISOR.PY --------------------------
def supervisor_node(state: AgentState):
    """
    This supervisor has smarter routing. It passes the full history
    to the LLM and has stricter logic for the email agent.
    """
    print("---SUPERVISOR---")
    llm = get_llm()
    
    messages = state['messages']
    
    # Check for work done in this pass
    sql_data = state.get("sql_data")
    web_search_data = state.get("web_search_data") 
    chart_path = state.get("chart_path")
    email_status = state.get("email_status")
    
    # Get the last human query
    current_user_query = ""
    if messages and isinstance(messages[-1], HumanMessage):
        current_user_query = messages[-1].content
    
    # Check if this is the first step after the user's query
    is_first_step = sql_data is None and chart_path is None and email_status is None and web_search_data is None
    
    # Check if the query implies a full analysis
    is_analysis_query = "analysis" in current_user_query.lower() or "report" in current_user_query.lower()
    
    # Check if SQL failed or returned empty
    sql_failed_or_empty = (sql_data and ("Error:" in sql_data or "no results" in sql_data)) or \
                          (state.get("structured_sql_data") == "")
                          
    # --- NEW CHECK: Explicit Email Request ---
    is_email_request = "email" in current_user_query.lower() or "send" in current_user_query.lower()

    prompt = f"""
    You are an expert supervisor. Your job is to choose the next agent to call based on the user's *last message* and the work *just completed*.
    Do not repeat steps.

    **User's Last Message:** "{current_user_query}"
    **Work Done in This Turn:**
    - SQL Data Retrieved: {sql_data is not None}
    - Web Search Data Retrieved: {web_search_data is not None}
    - Chart Generated: {chart_path is not None}
    - Email Status: "{email_status}" (If this says 'successfully sent', stop. If 'Error', you may retry.)
    - SQL Failed or Returned Empty: {sql_failed_or_empty}
    - User is Explicitly Requesting Email: {is_email_request}

    **Available Agents:**
    - `sql_agent`: Call this to get data from the retail database. Use this for all analysis, reports, sales, profit, etc.
    - `web_search_agent`: Call this ONLY for general knowledge questions.
    - `visualization_agent`: Call this if a chart is needed AND data was successfully retrieved.
    - `email_agent`: Call this if `User is Explicitly Requesting Email: True`.
    - `summarize`: Call this when all information is gathered OR if a step fails.

    **Logic:**
    1.  **Handle SQL Failure:** If `SQL Failed or Returned Empty` is True, you MUST call `summarize` next.
    2.  **Handle Web Search Done:** If `Web Search Data Retrieved` is True, you MUST call `summarize`.
    3.  **Handle Email:** - If `User is Explicitly Requesting Email` is True...
        - AND `Email Status` does NOT contain "successfully sent"...
        - THEN call `email_agent`.
    4.  **Handle New Query:** If this is the first step (`SQL Data Retrieved: False`):
        - **If the query is about your database (sales, profit, report), call `sql_agent`.**
        - Call `web_search_agent` ONLY if the query is clearly about external, general knowledge.
    5.  **Handle "Analysis" Workflow:** If the user asked for "analysis" or "report" AND data was just retrieved (`SQL Data Retrieved: True`) AND no chart has been made (`Chart Generated: False`), you MUST call `visualization_agent` next.
    6.  **Default to Summarize:** In all other cases, call `summarize`.

    Your answer MUST be ONLY the name of the agent from the available list.
    """
    
    response = llm.invoke(prompt)
    verbose_output = response.content.strip()
    
    valid_agents = ["sql_agent", "web_search_agent", "visualization_agent", "email_agent", "summarize"]
    next_agent = ""
    
    positions = {agent: verbose_output.rfind(agent) for agent in valid_agents}
    found_agents = {agent: pos for agent, pos in positions.items() if pos != -1}
    if found_agents: next_agent = max(found_agents, key=found_agents.get)
    else: next_agent = "summarize"

    # --- GUARDRAILS ---
    if sql_failed_or_empty:
        if next_agent != 'summarize':
              print("---[INFO] SQL agent returned no results or an error. Forcing summarize.---")
              next_agent = "summarize"
    
    if is_analysis_query and not sql_failed_or_empty and sql_data is not None and chart_path is None:
          print("---[INFO] Analysis query detected. Forcing visualization.---")
          next_agent = "visualization_agent"
          
    # --- DELETED THE STRICT EMAIL LOOP PROTECTION HERE --- 
    # (We now trust the LLM logic + Prompt "Email Status" check above)

    if web_search_data is not None and next_agent == "web_search_agent":
        print("---[INFO] Web search data already exists. Forcing summarize.---")
        next_agent = "summarize"

    print(f"---SUPERVISOR'S (PARSED) DECISION: Route to {next_agent}---")
    
    return {"next": next_agent}

# -------------------------- UPDATED SUMMARIZER NODE (FLEXIBLE & SCHEMA-AWARE) --------------------------
def summarize_node(state: dict) -> dict:
    """
    Generates a truly DYNAMIC response, aware of 'sub_region'.
    """
    print("---GENERATING FINAL DYNAMIC SUMMARY---")
    
    # --- FIX: IMMEDIATE RETURN IF EMAIL SENT ---
    email_status = state.get("email_status")
    if email_status and "successfully sent" in email_status:
        # Direct response, no LLM needed. This fixes the "how-to" tutorial issue.
        return {"messages": [AIMessage(content=f"✅ **Success!** {email_status}")]}
    # -------------------------------------------
    
    llm = get_llm()

    messages = state.get("messages", [])
    if not messages:
        return {"messages": [AIMessage(content="Error: No messages found in state.")]}

    current_user_query = ""
    if isinstance(messages[-1], HumanMessage):
        current_user_query = messages[-1].content
    
    sql_data_summary = state.get("sql_data", None)
    structured_data_csv = state.get("structured_sql_data", None)
    web_data = state.get("web_search_data", "Not available.")
    chart_path = state.get("chart_path", "Not available.")

    report_context_for_prompt = "No primary data available for this query."
    using_history = False

    if structured_data_csv and "Error" not in structured_data_csv and structured_data_csv.strip() and "no results" not in structured_data_csv:
        report_context_for_prompt = f"""
        **Primary Data Source (Structured CSV):**
        ```csv
        {structured_data_csv}
        ```
        """
    elif len(messages) > 1:
        for i in range(len(messages) - 2, -1, -1):
             prev_msg = messages[i]
             if isinstance(prev_msg, AIMessage) and not prev_msg.content.strip().startswith("{"):
                 report_context_for_prompt = f"**Previous Analysis Report (from chat history):**\n---\n{prev_msg.content}\n---"
                 using_history = True
                 break
    
    if sql_data_summary and ("no results" in sql_data_summary or "Error:" in sql_data_summary):
        report_context_for_prompt = f"**Data Retrieval Status:**\n{sql_data_summary}"
        using_history = True 

    visualization_summary = "Not available."
    if chart_path and chart_path.strip().startswith("{"):
        visualization_summary = "An interactive chart providing a visual representation is available below."
    elif chart_path:
        visualization_summary = f"Chart generation attempt status: {chart_path}"

    prompt = f"""
    You are a senior retail analyst.
    
    **User's Current Query:** "{current_user_query}"
    
    **Context/Data Available:**
    {report_context_for_prompt}
    * Web Search Context: {web_data}
    * Visualization Note: {visualization_summary}

    **Your Task:**
    Provide the best possible answer.
    - If the query is simple, be concise.
    - If the query is broad ("analysis"), provide a detailed Markdown report.
    - If answering a follow-up, rely on the 'Previous Analysis Report'.
    
    **Formatting:**
       * Use clean, professional Markdown. **Use headings, tables, and bullet points ONLY if you think the complexity of the answer requires it.**
       * **DO NOT** use HTML tags.
       * **DO NOT** include calculation formulas.
       * **DO NOT** mention the email agent or its status.
       * **CURRENCY:** Always format monetary values in **Indian Rupees (₹)**. Never use the Dollar ($) symbol. (e.g., ₹1,50,000).

    Provide the most helpful and appropriately formatted response.
    """

    final_report = llm.invoke(prompt).content
    final_report_cleaned = final_report.strip().replace("```markdown", "").replace("```", "")
    
    return {"messages": [AIMessage(content=final_report_cleaned)]}

# -------------------------- GRAPH BUILDER --------------------------
def get_supervisor_graph():
    """
    Constructs and returns the compiled LangGraph for the agentic system.
    """
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("sql_agent", run_sql_agent)
    graph.add_node("web_search_agent", run_web_search_agent)
    graph.add_node("visualization_agent", run_visualization_agent)
    graph.add_node("email_agent", run_email_agent) 
    graph.add_node("summarize", summarize_node)

    graph.set_entry_point("supervisor")

    conditional_map = {
        "sql_agent": "sql_agent",
        "web_search_agent": "web_search_agent",
        "visualization_agent": "visualization_agent",
        "email_agent": "email_agent", 
        "summarize": "summarize",
    }
    graph.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
    
    graph.add_edge("sql_agent", "supervisor")
    graph.add_edge("web_search_agent", "supervisor")
    graph.add_edge("visualization_agent", "supervisor")
    graph.add_edge("email_agent", "supervisor") 
    graph.add_edge("summarize", END)

    return graph.compile()
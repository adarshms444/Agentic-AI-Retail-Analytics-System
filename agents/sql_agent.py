# agents/sql_agent.py

import os
import pandas as pd
import io
import psycopg2 
from components.llm import get_llm
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def run_sql_agent(state: dict) -> dict:
    """
    This is the final, correct version, with a prompt specifically
    designed for the 2-table schema with 'sub_region'.
    """
    print("---QUERYING DATABASE (FINAL, 'sub_region' AWARE METHOD)---")
    llm = get_llm()
    messages = state.get("messages", [])
    if not messages:
        return {"sql_data": "Error: No messages in state.", "structured_sql_data": "Error: No messages in state."}

    current_user_query = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            current_user_query = msg.content
            break
    
    if not current_user_query:
        return {"sql_data": "Error: No user query found.", "structured_sql_data": "Error: No user query found."}

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_uri = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    db = SQLDatabase.from_uri(db_uri)

    # 1. Define the chain to generate the SQL query
    # --- THIS IS THE CORRECTED PROMPT FOR YOUR NEW SCHEMA ---
    template = """
    You are a PostgreSQL expert data analyst. Your primary goal is to write the simplest, most efficient query that answers the user's question.
    Provide ONLY the SQL query. Do not add any explanation or markdown.

    **CRITICAL SCHEMA INFORMATION:**
    - You have two tables:
      1. 'gadgethub_master_sales' (aliased as 'm'): Use this for all high-level, total, or master-level queries (e.g., total profit, total sales amount). Its region column is 'region' (e.g., 'Kerala').
      2. 'gadgethub_category_breakdown' (aliased as 'c'): Use this ONLY when the user asks for specific product 'category' data OR a specific 'sub_region' (e.g., 'Kochi', 'Trivandrum').
    
    - **JOIN KEY:** `m.month = c.month`. **DO NOT JOIN ON 'region' or 'sub_region'.**
    - **DATE COLUMN:** The 'month' column in both tables is a proper `DATE` type. Use `EXTRACT(YEAR FROM month)`.
    - **CASE SENSITIVITY:** Use `ILIKE` for string comparisons (e.g., `c.sub_region ILIKE 'kochi'`, `c.category ILIKE 'laptops'`).

    **CRITICAL QUERYING RULES (MUST FOLLOW):**

    1.  **AVOID JOINs!** Only use a JOIN if the user *explicitly* asks to compare a master metric (like 'total_sales_amount') with a category metric (like 'category_sales_amount').
    
    2.  **DEFAULT TO 'gadgethub_master_sales':** For any general query about "sales", "profit", "revenue", or "analysis" for the whole 'Kerala' region, you MUST use ONLY the `gadgethub_master_sales` (m) table.
    
    3.  **USE 'gadgethub_category_breakdown'** for all queries about specific "categories" or "sub_regions".

    **Full Schema:**
    {schema} 

    **Example 1 (Master Table - General Analysis):**
    Question: sales analysis for 2024
    SQL Query: SELECT TO_CHAR(month, 'YYYY-MM') AS month_str, month_name, total_sales_amount, profit_amount, num_customers FROM gadgethub_master_sales WHERE EXTRACT(YEAR FROM month) = 2024 ORDER BY month;

    **Example 2 (Category Table - Sub-Region Query):**
    Question: How many laptops were sold in 2023 in kochi?
    SQL Query: SELECT SUM(category_units_sold) AS laptops_sold FROM gadgethub_category_breakdown WHERE category ILIKE 'laptops' AND EXTRACT(YEAR FROM month) = 2023 AND sub_region ILIKE 'kochi';

    **Example 3 (Category Table - Sub-Region Query):**
    Question: Show me all category sales in Kochi for May 2025.
    SQL Query: SELECT category, category_sales_amount FROM gadgethub_category_breakdown WHERE sub_region ILIKE 'Kochi' AND month = '2025-05-01';

    **Example 4 (JOIN IS NEEDED):**
    Question: Compare the total sales amount vs accessories sales in May 2024.
    SQL Query: SELECT m.total_sales_amount, c.category_sales_amount FROM gadgethub_master_sales m JOIN gadgethub_category_breakdown c ON m.month = c.month WHERE m.month = '2024-05-01' AND c.category ILIKE 'accessories';

    **Question:**
    {question}

    SQL Query:
    """
    prompt = PromptTemplate.from_template(template)
    # --- END OF CORRECTED PROMPT ---

    sql_chain = (
        {
            "schema": RunnableLambda(lambda x: db.get_table_info()),
            "question": RunnablePassthrough() 
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # 2. Invoke the chain to get the SQL query string
    sql_query_from_llm = sql_chain.invoke(current_user_query)
    cleaned_sql = sql_query_from_llm.strip().replace("```sql", "").replace("```", "").replace(";", "").strip()
    print(f"---Generated & Cleaned SQL Query:\n{cleaned_sql}---")
    
    conn = None
    try:
        # 3. Execute the query directly using psycopg2
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute(cleaned_sql)
        results = cursor.fetchall() # Get all data rows
        colnames = [desc[0] for desc in cursor.description]
        cursor.close()

        # 4. Create DataFrame with the *correct* columns
        df = pd.DataFrame(results, columns=colnames)
        
        if df.empty:
            summary = "Successfully executed SQL query. The query returned no results."
            csv_output = ""
        else:
            summary = f"Successfully executed SQL query.\nData has been successfully retrieved and structured. Preview:\n{df.head().to_string()}"
            csv_output = df.to_csv(index=False)
            
        print(f"---SQL SUMMARY: {summary}---")
        print(f"---SQL STRUCTURED DATA (CSV):\n{csv_output}\n---")
        
        return {"sql_data": summary, "structured_sql_data": csv_output}

    except Exception as e:
        print(f"An error occurred while processing data: {e}")
        error_msg = f"An error occurred while processing: {e}"
        return {"sql_data": error_msg, "structured_sql_data": error_msg}
    finally:
        if conn:
            conn.close()
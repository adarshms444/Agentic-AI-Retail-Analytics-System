# # agents/viz_agent.py

# import json
# from components.llm import get_llm
# from components.tools import visualization_tool
# from langchain_core.messages import HumanMessage

# def run_visualization_agent(state: dict) -> dict:
#     """
#     Generates Python code for an INTERACTIVE Plotly visualization,
#     intelligently choosing the best chart type for the data.
#     """
#     print("---GENERATING INTERACTIVE VISUALIZATION (SMART)---")

#     llm = get_llm()
#     user_input = ""
#     for msg in state['messages']: 
#         if isinstance(msg, HumanMessage):
#             user_input = msg.content
#             break
            
#     csv_data = state.get("structured_sql_data")

#     if not csv_data or "Error" in csv_data or not csv_data.strip():
#         return {"chart_path": "No valid data available to generate a visualization."}

#     # --- ENHANCED PROMPT FOR SMARTER CHART CHOICE ---
#     prompt = f"""
#     You are an expert Python data scientist specializing in Plotly. Your task is to write Python code
#     to generate the BEST possible interactive Plotly chart based on the user's query and the provided data.

#     User's Request: "{user_input}"

#     Data (in CSV format):
#     ```csv
#     {csv_data}
#     ```

#     **Instructions for your Python script:**
#     1.  **Read Data:** You MUST read the CSV data from `csv_data` using `io.StringIO` and pandas. The DataFrame MUST be named `df`.
#         ```python
#         import pandas as pd
#         import io
#         import calendar
#         csv_data = '''{csv_data}'''
#         df = pd.read_csv(io.StringIO(csv_data))
#         ```
#     2.  **Process Data:** If `df` has a 'month_name' or 'month' column, use it for the x-axis.
#     3.  **Choose Best Chart Type:** Analyze the data columns (e.g., 'total_sales_amount', 'profit_amount', 'month_name', 'category', 'sub_region') and user request.
#         * If data has a time column (like 'month_name' or 'year'), a **line chart** (`plotly.express.line`) is best to show trends.
#         * If data compares distinct categories (like 'category' or 'sub_region'), a **bar chart** (`plotly.express.bar`) is best.
#         * If data represents **proportions of a whole** (e.g., sales share by 'sub_region') and there are **few sub_regions** (e.g., less than 6), a **pie chart** (`plotly.express.pie`) is good for showing percentage breakdowns.
#         * If the goal is to show the **relationship** between two numerical columns (e.g., 'profit_amount' vs. 'total_sales_amount'), a **scatter plot** (`plotly.express.scatter`) is best to see correlation.
#     4.  **Handle Single Row Data (CRITICAL):**
#         * If `len(df) == 1`, it contains aggregated totals. You MUST reshape it using pandas `.melt()` to a 'Metric' and 'Value' column, then plot `fig = px.bar(df_reshaped, x='Metric', y='Value', ...)`.
#     5.  **Generate Chart:** Create the chart using `plotly.express`. Assign it to `fig`. Include clear titles and axis labels.
#     6.  **Return JSON:** At the end, convert the figure to JSON using `chart_json = fig.to_json()`.

#     Respond with ONLY the complete, raw Python script.
#     """

#     python_code_response = llm.invoke(prompt).content

#     cleaned_python_code = python_code_response.strip().replace("```python", "").replace("```", "")
#     print(f"---[DEBUG] CLEANED PYTHON CODE FOR VIZ:\n{cleaned_python_code}\n--------------------")

#     result = visualization_tool.invoke({"python_code": cleaned_python_code})
#     print(f"---VISUALIZATION RESULT (JSON): {result[:100]}...---")

#     return {"chart_path": result}


# agents/viz_agent.py

import json
import pandas as pd
import io
from langchain_core.messages import AIMessage, HumanMessage
from components.llm import get_llm

def run_visualization_agent(state: dict):
    """
    Generates Python code to visualize the data using Plotly.
    """
    print("---RUNNING VISUALIZATION AGENT---")
    llm = get_llm()
    
    # 1. Get Data
    structured_data = state.get("structured_sql_data", "")
    messages = state.get("messages", [])
    current_query = messages[-1].content if messages else "visualize data"

    if not structured_data or "Error" in structured_data:
        return {"chart_path": "Error: No valid data available to visualize."}

    # 2. Create Prompt for Code Generation
    prompt = f"""
    You are a Python Data Visualization Expert using Plotly.
    
    **User Query:** "{current_query}"
    
    **Data (CSV Format):**
    ```csv
    {structured_data}
    ```

    **Your Task:**
    Write a Python script to visualize this data. The script must:
    1.  Load the data into a pandas DataFrame.
    2.  Create a Plotly Express chart (`fig`).
    3.  Save it as a JSON string.

    **CRITICAL RULES:**
    1.  **USE ALL DATA:** Do NOT filter the dataframe inside your Python code unless the User Query specifically asks to filter (e.g., "Show me ONLY Kochi"). If the query is "Compare sub-regions", you MUST plot ALL sub-regions present in the CSV.
    2.  **IGNORE PREVIOUS CONTEXT:** Do not assume limits based on previous questions. If the CSV has 5 rows, plot 5 rows.
    3.  **CHART TYPE:**
        - Comparisons (Categories/Regions) -> **Bar Chart** (`px.bar`).
        - Trends (Dates/Months) -> **Line Chart** (`px.line`).
        - Proportions -> **Pie Chart** (`px.pie`).
    4.  **CURRENCY:** If the data is monetary, format hover labels as Indian Rupees (₹).
    5.  **OUTPUT:** Return ONLY the raw Python code. No Markdown, no explanations.

    **Expected Python Code Structure:**
    ```python
    import pandas as pd
    import plotly.express as px
    import io
    import json

    # Load data
    csv_data = \"\"\"{structured_data}\"\"\"
    df = pd.read_csv(io.StringIO(csv_data))

    # --- LOGIC TO FIX DATA TYPES IF NEEDED ---
    # Ensure numeric columns are numbers
    # Ensure dates are datetime objects

    # Create Chart (Use ALL data in df)
    fig = px.bar(df, x='...', y='...', title='...', text_auto=True) 
    
    # Format Currency (Optional but recommended)
    fig.update_layout(yaxis_tickprefix = '₹')

    # Return JSON
    print(fig.to_json())
    ```
    """

    # 3. Generate Code
    try:
        response = llm.invoke(prompt).content
        code = response.strip().replace("```python", "").replace("```", "")
        
        # 4. Execute Code safely
        # We use a captured stdout to get the JSON result
        import sys
        from io import StringIO
        
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        
        # Define the execution environment
        exec_globals = {}
        exec(code, exec_globals)
        
        sys.stdout = old_stdout
        chart_json = redirected_output.getvalue().strip()
        
        if not chart_json.startswith("{"):
             # Fallback if the LLM didn't print valid JSON
             return {"chart_path": "Error: Visualization code did not return valid JSON."}

        print("---CHART GENERATED SUCCESSFULLY---")
        return {"chart_path": chart_json}

    except Exception as e:
        print(f"---VISUALIZATION ERROR: {e}---")
        return {"chart_path": f"Error generating chart: {e}"}
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
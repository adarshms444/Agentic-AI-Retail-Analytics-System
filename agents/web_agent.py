# # agents/web_agent.py

# from components.tools import web_search_tool

# def run_web_search_agent(state: dict) -> dict:
#     """
#     Performs a web search based on the user's input to find contextual information.
    
#     Args:
#         state (dict): The current state of the graph.
        
#     Returns:
#         dict: The updated state with web search results.
#     """
#     print("---SEARCHING WEB---")
    
#     user_input = state.get("messages", [])[-1].content
    
#     # Augment the query for better contextual search
#     augmented_query = f"Economic trends or news relevant to the following sales query: '{user_input}'"
    
#     result = web_search_tool.invoke({"query": augmented_query})
    
#     print(f"---WEB SEARCH RESULT: {result}---")
    
#     return {"web_search_data": result}


# # agents/web_agent.py
from components.tools import web_search_tool

def run_web_search_agent(state: dict) -> dict:
    """
    Performs a web search based on the user's input to find contextual information.
    """
    print("---SEARCHING WEB---")
    
    user_input = state.get("messages", [])[-1].content
    augmented_query = f"Economic trends or news relevant to the following sales query: '{user_input}'"
    
    result = web_search_tool.invoke({"query": augmented_query})
    
    print(f"---WEB SEARCH RESULT: {result}---")
    
    return {"web_search_data": result}
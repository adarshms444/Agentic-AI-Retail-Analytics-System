# main.py

from langchain_core.messages import HumanMessage
from graph.supervisor import get_supervisor_graph
import uuid

def main():
    """
    The main entry point for the command-line application.
    """
    print("--- Agentic Retail Analytics System ---")
    print("Ask a question about your sales data. Type 'quit', 'exit', or 'bye' to end the conversation.")
    
    # Each conversation has a unique ID
    conversation_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": conversation_id}}

    # Get the compiled supervisor graph
    agent_system = get_supervisor_graph()

    # The main interaction loop
    while True:
        user_input = input("User: ")
        
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("AI: Goodbye!")
            break
            
        if not user_input.strip():
            continue

        # Prepare the input for the graph
        # The 'messages' field is a list, and we wrap the user input in a HumanMessage
        graph_input = {"messages": [HumanMessage(content=user_input)]}
        
        try:
            # Invoke the graph and stream the output
            print("\nAI: Thinking...")
            final_state = agent_system.invoke(graph_input, config=config)
            
            # The final response is the last AI message in the state
            final_response = final_state['messages'][-1].content
            
            print("\n----------------- FINAL REPORT -----------------")
            print(final_response)
            print("----------------------------------------------\n")
            
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Please try rephrasing your question.")


if __name__ == "__main__":
    main()
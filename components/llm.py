# # components/llm.py

# import os
# from langchain_google_genai import ChatGoogleGenerativeAI
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# def get_llm():
#     """
#     Initializes and returns the language model instance.
    
#     Currently configured for Google Gemini. Ensure GOOGLE_API_KEY is set in your .env file.
#     """
#     # For NVIDIA, you would use:
#     # from langchain_nvidia_ai_endpoints import ChatNVIDIA
#     # model = ChatNVIDIA(model="nvidia/nvidia-nemotron-nano-9b-v2")
    
#     model = ChatGoogleGenerativeAI(
#         model="gemini-1.5-pro-latest",
#         temperature=0,
#         max_tokens=None,
#         timeout=None,
#         max_retries=2,
#     )
#     return model



# components/llm.py

import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_llm():
    """
    Initializes and returns the language model instance Configured for OpenAI's GPT models.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in .env file. Please add it.")

    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    return model



# # components/llm.py

# components/llm.py

import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """
    Initializes and returns the language model instance, configured for NVIDIA.
    """
    if not os.getenv("NVIDIA_API_KEY"):
        raise ValueError("NVIDIA_API_KEY not found in .env file. Please add it.")
        
    # Using the specific model you selected from the NVIDIA dashboard
    # model = ChatNVIDIA(
    #     model="meta/llama-3.3-70b-instruct",
    #     temperature=0,
    #     max_tokens=4096,
    # )
    # return model
    
    # model = ChatNVIDIA(
    #     model="meta/llama-4-maverick-17b-128e-instruct",
    #     temperature=0,
    #     max_tokens=1024,
    # )
    # return model

    model = ChatNVIDIA(
        model="qwen/qwen2.5-coder-32b-instruct",
        temperature=0,
        max_tokens=4096,
    )
    return model
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

    model = ChatNVIDIA(
        model="qwen/qwen2.5-coder-32b-instruct",
        temperature=0,
        max_tokens=4096,
    )
    return model
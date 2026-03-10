"""
chat_handler.py
---------------
Direct LLM chat interface for the user to ask general programming or system questions.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from logger import get_logger

load_dotenv()
log = get_logger(__name__)

_CHAT_SYSTEM = """You are a highly intelligent and helpful AI coding assistant.
The user is asking a general question or chatting with you.
Provide a clear, concise, and helpful answer. You can provide code snippets if relevant, but do not generate whole files unless asked.
"""

def handle_chat(question: str) -> str:
    """Send a conversational question to the LLM and return the string response."""
    api_key = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
    
    if not api_key:
        return "Error: GROQ_API_KEY is not set in the .env file."
        
    try:
        log.info(f"Answering user question: '{question[:50]}...'")
        llm = ChatGroq(model=model, temperature=0.5, groq_api_key=api_key)
        response = llm.invoke([
            SystemMessage(content=_CHAT_SYSTEM),
            HumanMessage(content=question)
        ])
        return response.content.strip()
    except Exception as e:
        log.error(f"Chat failed: {e}")
        return f"Sorry, I failed to generate a response: {e}"

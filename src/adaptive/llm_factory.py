"""
LLM Factory Module supporting Groq API (primary, high-speed, free tier friendly)
and OpenAI API (fallback), with transparent fallbacks when keys are not configured.
"""

import os
from typing import Optional, Any
from src.config import settings

def get_llm(temperature: float = 0.0) -> Optional[Any]:
    """
    Initializes and returns a LangChain Chat Model.
    Prioritizes Groq API when GROQ_API_KEY is present, then OpenAI API.
    Returns None if no API keys are available (allowing deterministic educational fallback).
    """
    groq_api_key = os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
    openai_api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
    
    # Priority 1: Groq API
    if groq_api_key:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=groq_api_key,
                model_name=settings.GROQ_MODEL,
                temperature=temperature
            )
        except Exception as e:
            print(f"Warning: Failed to initialize ChatGroq: {e}")

    # Priority 2: OpenAI API
    if openai_api_key:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                openai_api_key=openai_api_key,
                model=settings.OPENAI_MODEL,
                temperature=temperature
            )
        except Exception as e:
            print(f"Warning: Failed to initialize ChatOpenAI: {e}")

    return None

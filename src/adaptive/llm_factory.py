"""
LLM Factory Module supporting Groq API (primary, high-speed, free tier friendly)
and OpenAI API (fallback), with transparent fallbacks when keys are not configured.
"""

import os
from typing import Optional, Any
from src.config import settings

def get_llm(temperature: float = 0.0, api_key: Optional[str] = None) -> Optional[Any]:
    """
    Initializes and returns a LangChain Chat Model.
    Prioritizes passed api_key or GROQ_API_KEY from environment.
    """
    groq_api_key = api_key or os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
    openai_api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
    provider = (os.getenv("LLM_PROVIDER") or settings.LLM_PROVIDER or "groq").lower()

    # Priority 1: Groq API
    if groq_api_key and "groq" in provider:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=groq_api_key,
                model_name=settings.GROQ_MODEL,
                temperature=temperature
            )
        except Exception as e:
            print(f"Warning: Failed to initialize ChatGroq: {e}")

    # Also try Groq if key starts with gsk_ regardless of provider setting
    if groq_api_key and groq_api_key.startswith("gsk_"):
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=groq_api_key,
                model_name=settings.GROQ_MODEL,
                temperature=temperature
            )
        except Exception as e:
            print(f"Warning: Failed to initialize ChatGroq with key: {e}")

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

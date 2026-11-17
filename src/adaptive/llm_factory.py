"""
LLM Factory Module supporting Groq API (primary, high-speed) and OpenAI API (fallback).
STRICT SECURITY POLICY: Only uses the API key explicitly provided from the frontend request.
Never falls back to environment variables.
"""

from typing import Optional, Any
from src.config import settings

def get_llm(temperature: float = 0.0, api_key: Optional[str] = None) -> Optional[Any]:
    """
    Initializes and returns a LangChain Chat Model.
    STRICT REQUIREMENT: Strictly uses the API key supplied from the frontend client.
    Does NOT use environment variables or fallback to backend-configured keys.
    """
    if not api_key or not isinstance(api_key, str) or not api_key.strip():
        return None

    clean_key = api_key.strip()

    # If it is a Groq key (starts with gsk_ or default)
    if clean_key.startswith("gsk_") or not clean_key.startswith("sk-"):
        try:
            from langchain_groq import ChatGroq
            models_to_try = [
                "openai/gpt-oss-120b",
                settings.GROQ_MODEL,
                "openai/gpt-oss-20b",
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant"
            ]
            try:
                import groq
                client = groq.Groq(api_key=clean_key)
                available = [m.id for m in client.models.list().data]
                for candidate in models_to_try:
                    if candidate in available:
                        return ChatGroq(
                            groq_api_key=clean_key,
                            model_name=candidate,
                            temperature=temperature
                        )
                chat_models = [m for m in available if "whisper" not in m and "guard" not in m]
                if chat_models:
                    return ChatGroq(
                        groq_api_key=clean_key,
                        model_name=chat_models[0],
                        temperature=temperature
                    )
            except Exception:
                return ChatGroq(
                    groq_api_key=clean_key,
                    model_name="llama-3.1-8b-instant",
                    temperature=temperature
                )
        except Exception as e:
            print(f"Warning: Failed to initialize ChatGroq with client API key: {e}")
            return None

    # OpenAI key (starts with sk-)
    if clean_key.startswith("sk-"):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                openai_api_key=clean_key,
                model=settings.OPENAI_MODEL,
                temperature=temperature
            )
        except Exception as e:
            print(f"Warning: Failed to initialize ChatOpenAI with client API key: {e}")
            return None

    return None

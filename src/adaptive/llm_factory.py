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
    Falls back gracefully across active Groq models:
    llama-3.3-70b-versatile -> llama-3.1-8b-instant -> mixtral-8x7b-32768.
    """
    groq_api_key = api_key or os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
    openai_api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY

    # Check if a Groq key is provided
    if groq_api_key:
        try:
            from langchain_groq import ChatGroq
            # Preferred model candidate list
            models_to_try = [
                settings.GROQ_MODEL,
                "llama-3.1-8b-instant",
                "llama-3.3-70b-versatile",
                "mixtral-8x7b-32768"
            ]
            
            # If the user's key allows listing models, query available models
            try:
                import groq
                client = groq.Groq(api_key=groq_api_key)
                available = [m.id for m in client.models.list().data]
                for candidate in models_to_try:
                    if candidate in available:
                        return ChatGroq(
                            groq_api_key=groq_api_key,
                            model_name=candidate,
                            temperature=temperature
                        )
                # If preferred not found, use first available chat model
                chat_models = [m for m in available if "whisper" not in m and "guard" not in m]
                if chat_models:
                    return ChatGroq(
                        groq_api_key=groq_api_key,
                        model_name=chat_models[0],
                        temperature=temperature
                    )
            except Exception:
                # If model listing fails, default to llama-3.1-8b-instant which is universally active
                return ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name="llama-3.1-8b-instant",
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

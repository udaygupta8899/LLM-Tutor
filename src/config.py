import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "LLM Tutor"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # LLM Providers & Keys
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "groq"  # "groq" or "openai"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Fast, state-of-the-art open weights on Groq
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Chroma Vector DB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "llm-course-materials"  # Updated to LLM Course & Research Papers
    CHROMA_FALLBACK_COLLECTION: str = "dl-tutor-chroma"    # Fallback to Deep Learning book
    
    # Retrieval Hyperparameters
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    RRF_K: int = 60
    TOP_K: int = 4
    ENABLE_RERANKER: bool = False
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Security / Prompt Injection Detection
    INJECTION_THRESHOLD_SUSPICIOUS: float = 0.40
    INJECTION_THRESHOLD_HIGH_RISK: float = 0.70
    SECURITY_DEFAULT_ACTION: str = "QUARANTINE"  # QUARANTINE, BLOCK, or SANITIZE
    
    # Agentic RAG Limits
    MAX_RETRIES: int = 3
    DEFAULT_TUTOR_MODE: str = "explain"  # explain, hint, quiz, socratic


settings = Settings()

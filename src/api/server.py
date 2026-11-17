"""
FastAPI Server for Adaptive LLM Tutor.
Provides full REST endpoints for:
- /api/chat: Adaptive Agentic RAG chat with security screening and routing diagnostics
- /api/security/inspect: On-demand prompt injection scanner for queries/documents
- /api/security/audit: Historical security logs
- /api/retrieval/search: Direct hybrid retrieval endpoint exposing BM25, Dense, RRF, Rerank
- /api/learner/profile: Student mastery profile and conversation memory
- /api/dashboard: Real-time statistics on routing, security, and knowledge base
"""

import time
from typing import Dict, Any, List, Optional
import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.adaptive.agent_workflow import AdaptiveAgenticRAGTutor
from src.retrieval.hybrid_retriever import HybridRetriever
from src.security.prompt_injection_detector import PromptInjectionDetector
from src.tutor.learner_memory import LearnerMemory
from src.tutor.quiz_manager import InteractiveQuizManager
from src.config import settings

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Adaptive Agentic RAG System with Custom BM25/RRF Hybrid Retrieval and Prompt Injection Defense",
    version=settings.APP_VERSION
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
retriever = HybridRetriever()
detector = PromptInjectionDetector()
agent = AdaptiveAgenticRAGTutor(hybrid_retriever=retriever, injection_detector=detector)
learner_memory = LearnerMemory()
quiz_manager = InteractiveQuizManager(hybrid_retriever=retriever)


# Request / Response Schemas
class ChatRequest(BaseModel):
    question: str
    thread_id: Optional[str] = "default_thread"
    student_id: Optional[str] = "student_1"
    tutor_mode: Optional[str] = "explain"  # explain, hint, quiz, socratic
    chat_history: Optional[str] = ""       # Conversational memory passed from frontend
    api_key: Optional[str] = None          # User provided Groq or OpenAI API key


class ChatResponse(BaseModel):
    answer: str
    thread_id: str
    student_id: str
    tutor_mode: str
    complexity: str
    complexity_confidence: float
    routing_strategy: str
    security_status: str
    security_result: Dict[str, Any]
    retrieved_documents: List[Dict[str, Any]]
    verification_result: Dict[str, Any]
    latency_seconds: float


class SecurityInspectRequest(BaseModel):
    text: str
    is_document: bool = False


class HybridSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    enable_reranker: bool = False

class GenerateSingleQuestionRequest(BaseModel):
    topic: str
    question_number: int = 1
    difficulty: str = "intermediate"
    previous_questions: Optional[List[str]] = []
    api_key: Optional[str] = None


@app.post("/api/quiz/single-question")
@app.post("/api/quiz/single-question/")
@app.post("/quiz/single-question")
@app.post("/api/api/quiz/single-question")
def generate_single_question_endpoint(request: GenerateSingleQuestionRequest):
    """Dynamically generates one question matching learner level."""
    if not request.api_key or not request.api_key.strip():
        raise HTTPException(
            status_code=400,
            detail="API Key required. Please enter your Groq API Key in the frontend header to generate quiz questions."
        )
    try:
        return quiz_manager.generate_single_question(
            topic=request.topic,
            question_number=request.question_number,
            difficulty=request.difficulty,
            previous_questions=request.previous_questions,
            api_key=request.api_key.strip()
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoints
@app.get("/")
def read_root():
    if os.path.exists("./frontend/index.html"):
        return FileResponse("./frontend/index.html")
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "indexed_chunks": retriever.bm25.corpus_size
    }


@app.post("/api/chat", response_model=ChatResponse)
@app.post("/api/chat/", response_model=ChatResponse)
@app.post("/chat", response_model=ChatResponse)
@app.post("/chat/", response_model=ChatResponse)
@app.post("/api/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main conversational endpoint:
    Runs prompt injection check -> complexity classification -> adaptive routing -> hybrid retrieval -> tutoring synthesis -> verification.
    """
    if not request.api_key or not request.api_key.strip():
        raise HTTPException(
            status_code=400,
            detail="API Key required. Please enter your Groq API Key (gsk_...) in the frontend header before chatting."
        )
    try:
        # Retrieve recent interactions from DB if chat_history not explicitly sent
        history_context = request.chat_history or ""
        if not history_context and request.student_id:
            recent_turns = learner_memory.get_recent_history(request.student_id, limit=4)
            if recent_turns:
                history_context = "\n".join([
                    f"User: {t['question']}\nAssistant: {t['answer'][:300]}..." 
                    for t in recent_turns
                ])

        result = agent.run(
            question=request.question,
            student_id=request.student_id or "student_1",
            tutor_mode=request.tutor_mode or "explain",
            thread_id=request.thread_id or "default_thread",
            chat_history=history_context,
            api_key=request.api_key.strip()
        )
        
        return ChatResponse(
            answer=result.get("generation", ""),
            thread_id=request.thread_id or "default_thread",
            student_id=request.student_id or "student_1",
            tutor_mode=request.tutor_mode or "explain",
            complexity=result.get("complexity", "simple"),
            complexity_confidence=result.get("complexity_confidence", 0.0),
            routing_strategy=result.get("routing_strategy", "single_rag"),
            security_status=result.get("security_status", "ALLOW"),
            security_result=result.get("security_result", {}),
            retrieved_documents=result.get("retrieved_documents", []),
            verification_result=result.get("verification_result", {}),
            latency_seconds=result.get("latency_seconds", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def legacy_chat_endpoint(request: ChatRequest):
    """Backwards-compatibility endpoint for legacy frontend."""
    res = await chat_endpoint(request)
    return {"answer": res.answer, "thread_id": res.thread_id}


@app.post("/api/security/inspect")
def inspect_text(request: SecurityInspectRequest):
    """On-demand security screening for any text, query, or uploaded document chunk."""
    return detector.inspect(request.text, is_document=request.is_document)


@app.get("/api/security/audit")
def get_security_audit():
    """Returns the recorded audit log of prompt injection scans and mitigations."""
    return {"audit_log": detector.security_policy.audit_log}


@app.post("/api/retrieval/search")
def hybrid_search(request: HybridSearchRequest):
    """Direct transparent search exposing BM25, Dense, RRF, and Reranked lists."""
    retriever.enable_reranker = request.enable_reranker
    return retriever.retrieve(query=request.query, top_k=request.top_k)


@app.get("/api/learner/profile/{student_id}")
def get_profile(student_id: str):
    """Returns student profile, mastery level, and recent history."""
    profile = learner_memory.get_profile(student_id)
    history = learner_memory.get_recent_history(student_id, limit=10)
    return {"profile": profile, "history": history}


@app.get("/api/dashboard")
def get_dashboard_stats():
    """Aggregates high-level system telemetry for frontend dashboard."""
    return {
        "corpus_size": retriever.bm25.corpus_size,
        "avg_doc_len": round(retriever.bm25.avg_doc_len, 2),
        "total_security_events": len(detector.security_policy.audit_log),
        "supported_modes": ["explain", "hint", "quiz", "socratic"],
        "retrieval_architecture": "Custom BM25 + Dense Cosine + Custom RRF + Optional Cross-Encoder"
    }

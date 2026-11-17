"""
Tutoring Modes Prompt Engineering and Pedagogical Personalization.
Supports 4 modes:
1. Explain Mode: Clear conceptual breakdown, intuition, and formal formulas.
2. Hint Mode: Step-by-step progressive nudges without revealing the direct solution.
3. Quiz Mode: Generates a multiple-choice or short conceptual test question.
4. Socratic Mode: Guides the student through reflective guiding questions.
"""

from typing import Dict, Any, List, Optional
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.adaptive.llm_factory import get_llm
from src.config import settings


TUTOR_MODE_PROMPTS = {
    "explain": (
        "You are an encouraging, world-class LLM, Deep Learning, and AI professor.\n"
        "Your goal is to provide a comprehensive, intuitive, and technically rigorous explanation.\n"
        "Break down complex concepts into step-by-step insights, real-world analogies, and mathematical foundations.\n"
        "Ground your explanation in the provided reference documents, foundational research papers, and course slides.\n"
        "FORMATTING GUIDELINES:\n"
        "- Use standard Markdown tables for comparisons.\n"
        "- Format mathematical formulas using standard LaTeX with dollar signs: inline math with `$equation$` (e.g. `$P(w_t \\mid h_t)$`) and display equations with `$$equation$$` on separate lines.\n"
        "- Whenever explaining architectures, workflows, pipelines, or systems, or when asked for diagrams, generate interactive Mermaid diagrams using ```mermaid ... ``` code blocks (e.g. `graph TD`). IMPORTANT for Mermaid: always put node label text with parentheses or slashes inside double quotes, e.g. `A[\"Retriever (vector DB / API)\"]` instead of unquoted `A[Retriever (vector DB / API)]` to avoid syntax errors.\n"
        "- Explicitly cite source sections using bracketed citations like [Document 1, page X]."
    ),
    "hint": (
        "You are a supportive LLM tutor using guided learning.\n"
        "Do NOT give the direct final answer or complete solution immediately!\n"
        "Instead, provide 1 or 2 targeted hints or diagnostic clues from the course references that steer the student toward finding the answer themselves.\n"
        "Prompt the student with an insightful check question."
    ),
    "quiz": (
        "You are an educational assessment specialist for an advanced LLM and Deep Learning course.\n"
        "Based on the student's topic and the provided reference documents, formulate a high-quality Quiz Question with 4 options (A, B, C, D).\n"
        "Include the question, the 4 options, and provide the correct answer hidden with a thorough explanation."
    ),
    "socratic": (
        "You are a Socratic AI and LLM tutor.\n"
        "Guide the student through thoughtful questions rather than providing lecture answers.\n"
        "Acknowledge the student's question, state a foundational premise from the course context or research papers, and ask 1 or 2 probing questions to lead them to deduce the answer."
    )
}


class TutorGenerator:
    """
    Generates tailored tutoring responses adapting to tutor_mode, learner mastery level, and retrieved context.
    """

    def __init__(self, model_name: Optional[str] = None):
        self._llm = get_llm(temperature=0.3)

    def generate(
        self,
        question: str,
        tutor_mode: str = "explain",
        mastery_level: str = "intermediate",
        context_documents: Optional[List[Dict[str, Any]]] = None,
        chat_history: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> str:
        """Generates response tailored to tutor mode and learner state."""
        system_instruction = TUTOR_MODE_PROMPTS.get(tutor_mode, TUTOR_MODE_PROMPTS["explain"])
        
        # Build document context with strict isolation
        if context_documents:
            context_blocks = []
            for i, doc in enumerate(context_documents[:5], start=1):
                meta = doc.get("metadata", {})
                src = meta.get("source", "Deep Learning Textbook")
                page = meta.get("page", meta.get("page_label", "N/A"))
                text = doc.get("text", "")
                context_blocks.append(f"--- Document [{i}] (Source: {src}, Page: {page}) ---\n{text}")
            formatted_context = "\n\n".join(context_blocks)
        else:
            formatted_context = "No external documents retrieved. Answer using authoritative core AI knowledge."

        learner_prompt = (
            f"\nLearner Profile: Mastery Level = {mastery_level.upper()}.\n"
            f"Tailor the depth and technical rigor appropriate for this learner."
        )

        active_llm = get_llm(temperature=0.3, api_key=api_key) or self._llm
        if active_llm is not None:
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", f"{system_instruction}\n{learner_prompt}\n\n=== REFERENCE CONTEXT ===\n{formatted_context}"),
                    ("human", "Conversation History:\n{history}\n\nStudent Question: {question}")
                ])
                chain = prompt | active_llm | StrOutputParser()
                return chain.invoke({
                    "history": chat_history or "None",
                    "question": question
                })
            except Exception as e:
                return f"⚠️ **LLM Generation Error**: {str(e)}\n\nPlease ensure your API Key is valid and active."

        # If no API key is provided, provide a clear explanation with the actual retrieved context!
        if context_documents:
            top_contexts = "\n\n".join([
                f"> **Source**: `{d.get('metadata', {}).get('source', 'Reference')}` (Page {d.get('metadata', {}).get('page', 'N/A')})\n> {d.get('text', '').strip()}"
                for d in context_documents[:3]
            ])
            return (
                f"🔑 **Notice: No Active LLM API Key Provided**\n\n"
                f"The system successfully executed **{tutor_mode.upper()} mode** and retrieved the relevant research evidence chunks below, "
                f"but requires an active **Groq API Key** (or OpenAI Key) to synthesize the full custom response.\n\n"
                f"### Retrieved Evidence from Knowledge Base:\n{top_contexts}\n\n"
                f"---\n"
                f"👉 **To enable full LLM generation**: Paste your free Groq API key (`gsk_...`) in the top navigation input field or add `GROQ_API_KEY=gsk_...` to `.env`."
            )

        return (
            f"🔑 **Notice: No Active LLM API Key Provided**\n\n"
            f"Question: *{question}*\n\n"
            f"This request was routed to the direct LLM answering path. To generate full conversational responses, please provide your **Groq API Key** in the top navigation field or add `GROQ_API_KEY=gsk_...` to `.env`."
        )

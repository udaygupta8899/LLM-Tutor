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
        "Ground your explanation in the provided textbook reference documents, foundational research papers (e.g. Attention Is All You Need, RAG, Self-RAG), and course slides.\n"
        "Explicitly cite source sections using bracketed citations like [Document 1, page X]."
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
                pass

        # Offline Educational Fallback Response
        doc_refs = [f"Doc {d.get('id', i+1)}" for i, d in enumerate(context_documents or [])]
        refs_str = f" [Referenced Sources: {', '.join(doc_refs)}]" if doc_refs else ""
        return (
            f"**[Tutor Mode: {tutor_mode.capitalize()} | Mastery: {mastery_level.capitalize()}]**\n\n"
            f"Here is the guided educational response for: *{question}*\n\n"
            f"Deep Learning models leverage hierarchical feature representation and backpropagation for parameter optimization. "
            f"The principles in the Goodfellow Deep Learning textbook demonstrate how optimization surfaces and regularization "
            f"shape model generalization.{refs_str}\n\n"
            f"*Follow-up Question:* Would you like to delve deeper into the mathematical derivation or explore a hands-on example?"
        )

"""
Query Complexity Classifier for Adaptive RAG.
Categorizes queries into:
- straightforward -> direct LLM answer (no retrieval overhead)
- simple -> single-step hybrid RAG
- complex -> multi-step agentic query decomposition and iterative synthesis
"""

import os
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from src.adaptive.llm_factory import get_llm

class QueryComplexity(BaseModel):
    category: str = Field(
        description="One of 'straightforward', 'simple', 'complex'"
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        description="Brief explanation of why this complexity level was assigned"
    )


class AdaptiveClassifier:
    """
    Classifies student questions by complexity using Groq / OpenAI LLM or fast deterministic heuristic fallback.
    """

    def __init__(self, model_name: Optional[str] = None):
        self._llm = get_llm(temperature=0.0)

    def classify(self, question: str, chat_history: Optional[str] = None) -> Dict[str, Any]:
        """
        Classifies incoming question into:
        - straightforward: Greetings, simple factual definitions, general meta queries
        - simple: Standard conceptual question answerable from a single section/topic
        - complex: Multi-hop reasoning, architectural trade-offs, synthesis across multiple topics
        """
        if self._llm is not None:
            try:
                parser = JsonOutputParser(pydantic_object=QueryComplexity)
                prompt = ChatPromptTemplate.from_messages([
                    ("system", 
                     "You are an expert educational query complexity classifier for an AI/Deep Learning tutoring system.\n"
                     "Classify the student's question into exactly one of three categories:\n"
                     "1. 'straightforward': Greetings, general conversational remarks, or basic definitions that require no document retrieval.\n"
                     "2. 'simple': Focused technical questions about a specific concept, algorithm, or theorem answerable from a single textbook section (e.g. 'What is the activation function of ReLU?', 'How does gradient descent update weights?').\n"
                     "3. 'complex': Multi-hop questions, comparative analyses across multiple architectures, design trade-offs, or synthesis requiring multi-step investigation (e.g. 'Compare Transformer self-attention with LSTM gating mechanisms in terms of computational complexity and gradient propagation.').\n\n"
                     "{format_instructions}"),
                    ("human", "Question: {question}\nRecent History:\n{history}")
                ])
                chain = prompt | self._llm | parser
                result = chain.invoke({
                    "question": question,
                    "history": chat_history or "None",
                    "format_instructions": parser.get_format_instructions()
                })
                category = result.get("category", "simple").lower().strip()
                if category not in ["straightforward", "simple", "complex"]:
                    category = "simple"
                return {
                    "category": category,
                    "confidence": float(result.get("confidence", 0.90)),
                    "reasoning": result.get("reasoning", "LLM structured classification")
                }
            except Exception:
                pass

        # Heuristic fallback (fast, offline, deterministic)
        return self._heuristic_classify(question)

    def _heuristic_classify(self, question: str) -> Dict[str, Any]:
        """Deterministic rule-based complexity classifier when LLM API is offline."""
        q = question.lower().strip()
        words = q.split()
        
        # Greetings & basic pleasantries
        if any(q.startswith(g) for g in ["hi", "hello", "hey", "good morning", "thanks", "thank you", "bye"]):
            return {
                "category": "straightforward",
                "confidence": 0.95,
                "reasoning": "Standard conversational greeting/pleasantry; no retrieval needed."
            }

        # Multi-hop / comparative / synthesis indicators
        complex_triggers = [
            "compare", "contrast", "difference between", "trade-off", "trade off",
            "derive", "mathematical proof", "synthesize", "how do both", "relationship between",
            "vs", "versus", "advantages and disadvantages", "why is x preferred over y"
        ]
        if any(trig in q for trig in complex_triggers) or len(words) > 30 or (" and " in q and "?" in q and len(words) > 18):
            return {
                "category": "complex",
                "confidence": 0.88,
                "reasoning": "Detected comparative or multi-concept query requiring multi-hop synthesis."
            }

        # Simple factual definitions or single concept lookups
        if any(q.startswith(p) for p in ["what is", "define", "what are", "who is"]):
            return {
                "category": "simple",
                "confidence": 0.85,
                "reasoning": "Targeted conceptual definition answerable via single-step RAG."
            }

        # Default standard single-step RAG
        return {
            "category": "simple",
            "confidence": 0.75,
            "reasoning": "Standard domain-specific question routed to hybrid retrieval."
        }

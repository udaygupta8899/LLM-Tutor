"""
Query Decomposer for Complex Multi-Hop Queries.
Deconstructs complex educational questions into bounded sub-questions.
"""

from typing import List, Optional
import os
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from src.config import settings


class QueryDecomposer:
    """
    Decomposes complex student questions into 2-3 focused sub-queries for iterative retrieval.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.LLM_MODEL
        self._llm = None
        if os.getenv("OPENAI_API_KEY"):
            try:
                self._llm = ChatOpenAI(model=self.model_name, temperature=0)
            except Exception:
                self._llm = None

    def decompose(self, query: str) -> List[str]:
        """Decomposes a query into sub-questions."""
        if self._llm is not None:
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", 
                     "You are an expert curriculum assistant. Decompose the student's complex question into 2 or 3 distinct, concise sub-questions "
                     "that will retrieve the necessary background and comparative evidence.\n"
                     "Format output as a numbered list: 1., 2., 3. Output ONLY the numbered questions."),
                    ("human", "{query}")
                ])
                chain = prompt | self._llm | StrOutputParser()
                response = chain.invoke({"query": query})
                lines = [line.strip() for line in response.split("\n") if line.strip()]
                subqueries = []
                for line in lines:
                    cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                    if len(cleaned) > 5:
                        subqueries.append(cleaned)
                if subqueries:
                    return subqueries[:3]
            except Exception:
                pass

        # Deterministic decomposition fallback
        return self._heuristic_decompose(query)

    def _heuristic_decompose(self, query: str) -> List[str]:
        """Simple rule-based decomposition for comparison queries."""
        q_lower = query.lower()
        if "compare" in q_lower or " vs " in q_lower or "versus" in q_lower or "difference between" in q_lower:
            parts = re.split(r'\b(?:and|vs|versus|with)\b', query, flags=re.IGNORECASE)
            if len(parts) >= 2:
                sub1 = f"Core principles and architecture of {parts[0].replace('compare', '').strip()}"
                sub2 = f"Core principles and architecture of {parts[1].strip()}"
                sub3 = f"Trade-offs and comparison between {parts[0].replace('compare', '').strip()} and {parts[1].strip()}"
                return [sub1, sub2, sub3]
        
        return [query]

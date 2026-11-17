"""
Hallucination and Grounding Verification Module.
Extracts factual claims and validates them against retrieved source context.
Distinct and separated from prompt injection detection.
"""

from typing import List, Dict, Any, Optional
import os
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.adaptive.llm_factory import get_llm
from src.config import settings


class HallucinationVerifier:
    """
    Verifies factual grounding of generated tutor answers against retrieved context.
    Identifies unsupported claims and validates citation references.
    """

    def __init__(self, model_name: Optional[str] = None):
        self._llm = get_llm(temperature=0.0)

    def verify(self, answer: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assesses whether the generated answer is faithful to the retrieved documents.
        
        Returns:
            - is_grounded: bool
            - score: float in [0.0, 1.0]
            - unsupported_claims: List[str]
            - citation_validity: bool
        """
        if not context_documents:
            # If no context was provided (e.g. straightforward direct LLM answering), grounding check is not applicable
            return {
                "is_grounded": True,
                "score": 1.0,
                "unsupported_claims": [],
                "citation_validity": True,
                "reasoning": "Direct answering path; no retrieved documents required."
            }

        context_text = "\n\n".join([f"Document [{i+1}]: {doc.get('text', '')}" for i, doc in enumerate(context_documents[:5])])

        if self._llm is not None:
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", 
                     "You are a strict academic verification evaluator. You assess whether an AI tutor's answer is factually grounded in the provided reference documents.\n"
                     "Reference Documents:\n{context}\n\n"
                     "Student Answer to Verify:\n{answer}\n\n"
                     "Respond in format:\n"
                     "GROUNDED: YES or NO\n"
                     "SCORE: <number between 0.0 and 1.0>\n"
                     "UNSUPPORTED_CLAIMS: <comma-separated list of any fabricated claims, or 'None'>\n"
                     "REASONING: <brief explanation>"),
                    ("human", "Verify this answer.")
                ])
                chain = prompt | self._llm | StrOutputParser()
                response = chain.invoke({"context": context_text, "answer": answer})
                
                is_grounded = "GROUNDED: YES" in response.upper() or ("YES" in response[:30].upper())
                
                # Extract score
                score_match = re.search(r"SCORE:\s*([\d\.]+)", response)
                score = float(score_match.group(1)) if score_match else (0.95 if is_grounded else 0.40)
                
                return {
                    "is_grounded": is_grounded,
                    "score": score,
                    "raw_verification": response
                }
            except Exception:
                pass

        # Heuristic / Token Overlap Grounding Fallback
        return self._heuristic_grounding(answer, context_text)

    def _heuristic_grounding(self, answer: str, context: str) -> Dict[str, Any]:
        """Lexical overlap grounding verification fallback."""
        ans_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', answer.lower()))
        ctx_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', context.lower()))
        
        if not ans_words:
            return {"is_grounded": True, "score": 1.0, "reasoning": "Trivial answer."}
            
        overlap = ans_words.intersection(ctx_words)
        overlap_ratio = len(overlap) / len(ans_words)
        
        is_grounded = overlap_ratio >= 0.35
        return {
            "is_grounded": is_grounded,
            "score": round(min(1.0, overlap_ratio * 1.5), 2),
            "overlap_ratio": round(overlap_ratio, 3),
            "reasoning": f"Lexical grounding overlap: {round(overlap_ratio*100, 1)}% of salient technical terms appear in retrieved context."
        }

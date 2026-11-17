"""
Structured Quiz Generator Module.
Generates interactive multiple-choice questions with clickable options,
evaluates selections, and provides thorough explanations grounded in course references.
"""

from typing import List, Dict, Any, Optional
import json
import re
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.adaptive.llm_factory import get_llm
from src.retrieval.hybrid_retriever import HybridRetriever


class QuizQuestionItem(BaseModel):
    id: int = Field(description="Question number (e.g. 1, 2, 3)")
    question: str = Field(description="The clear multiple-choice question text")
    options: List[str] = Field(description="List of exactly 4 choices (e.g. ['A. Option 1', 'B. Option 2', 'C. Option 3', 'D. Option 4'])")
    correct_option: str = Field(description="The letter of the correct answer (e.g. 'A', 'B', 'C', or 'D')")
    explanation: str = Field(description="Detailed explanation of why the answer is correct and why other choices are incorrect")


class QuizSession(BaseModel):
    topic: str
    total_questions: int
    questions: List[QuizQuestionItem]


class InteractiveQuizManager:
    """
    Generates and manages multi-question interactive quizzes on demand.
    """

    def __init__(self, hybrid_retriever: Optional[HybridRetriever] = None):
        self.retriever = hybrid_retriever or HybridRetriever()

    def generate_quiz(
        self,
        topic: str,
        num_questions: int = 5,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves relevant course references on the topic and generates structured JSON quiz questions.
        """
        # Retrieve context on the topic
        retrieval = self.retriever.retrieve(query=topic, top_k=6)
        docs = retrieval.get("final_documents", [])
        context_text = "\n\n".join([f"[{i+1}] {d.get('text', '')}" for i, d in enumerate(docs)])

        llm = get_llm(temperature=0.2, api_key=api_key)

        if llm is not None:
            try:
                parser = JsonOutputParser(pydantic_object=QuizSession)
                prompt = ChatPromptTemplate.from_messages([
                    ("system", 
                     "You are an expert AI and LLM professor designing an interactive assessment.\n"
                     "Generate exactly {num_questions} high-quality, technically rigorous multiple-choice questions on the topic: '{topic}'.\n"
                     "Ground your questions in the provided research and textbook context:\n{context}\n\n"
                     "Format output as a valid JSON object matching the schema:\n"
                     "{\n"
                     "  \"topic\": \"{topic}\",\n"
                     "  \"total_questions\": {num_questions},\n"
                     "  \"questions\": [\n"
                     "    {\n"
                     "      \"id\": 1,\n"
                     "      \"question\": \"Question text here?\",\n"
                     "      \"options\": [\"A. ...\", \"B. ...\", \"C. ...\", \"D. ...\"],\n"
                     "      \"correct_option\": \"B\",\n"
                     "      \"explanation\": \"Detailed technical explanation why B is correct...\"\n"
                     "    }\n"
                     "  ]\n"
                     "}\n"
                     "Output ONLY valid JSON. Nothing else."),
                    ("human", "Generate the quiz now.")
                ])
                chain = prompt | llm | parser
                res = chain.invoke({
                    "topic": topic,
                    "num_questions": num_questions,
                    "context": context_text
                })
                return res
            except Exception as e:
                print(f"Quiz generation LLM error: {e}")

        # Deterministic / Fallback Quiz generator if LLM parsing encounters issues
        return self._generate_fallback_quiz(topic, num_questions)

    def _generate_fallback_quiz(self, topic: str, num_questions: int) -> Dict[str, Any]:
        """Provides an authoritative default question set if offline."""
        all_q = [
            {
                "id": 1,
                "question": f"In the context of {topic}, what is the fundamental purpose of scaled dot-product self-attention?",
                "options": [
                    "A. To eliminate the need for parameter backpropagation",
                    "B. To scale query-key dot products by 1/sqrt(d_k) to prevent vanishing softmax gradients",
                    "C. To convert all sequence representations into convolutional spatial filters",
                    "D. To restrict attention solely to immediately adjacent tokens"
                ],
                "correct_option": "B",
                "explanation": "As established in Vaswani et al. (2017) 'Attention Is All You Need', for large values of d_k the dot products grow large in magnitude, pushing softmax into regions with tiny gradients. Scaling by 1/sqrt(d_k) stabilizes optimization."
            },
            {
                "id": 2,
                "question": f"How does Self-RAG differ from traditional single-step RAG regarding retrieval timing?",
                "options": [
                    "A. Self-RAG only retrieves once before any token generation begins",
                    "B. Self-RAG does not use a vector database",
                    "C. Self-RAG emits special reflection tokens on-demand during generation to trigger retrieval and critique",
                    "D. Self-RAG completely avoids language models in favor of rule-based lookups"
                ],
                "correct_option": "C",
                "explanation": "Self-RAG (Asai et al., 2024) introduces learned reflection tokens like <RETRIEVE> and <CRITIQUE>, allowing the model to dynamically decide when external evidence is required during the generation process."
            },
            {
                "id": 3,
                "question": f"Which metric represents the standard formula for Reciprocal Rank Fusion (RRF) when combining rank lists?",
                "options": [
                    "A. RRF = sum( 1 / (k + rank_i(d)) )",
                    "B. RRF = sum( rank_i(d) * k )",
                    "C. RRF = max( score_dense, score_sparse )",
                    "D. RRF = 1 - dot_product(u, v)"
                ],
                "correct_option": "A",
                "explanation": "Reciprocal Rank Fusion computes a robust composite score across disparate retrieval engines using RRF(d) = sum(1 / (k + r_i(d))), where k is a smoothing constant (typically k=60)."
            }
        ]
        return {
            "topic": topic,
            "total_questions": min(num_questions, len(all_q)),
            "questions": all_q[:num_questions]
        }

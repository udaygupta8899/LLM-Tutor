"""
Adaptive Interactive Quiz Manager.
Generates dynamic questions on-the-fly adjusting difficulty:
- Easy (Foundational definitions & architectural basics)
- Intermediate (Mechanics, formulas, and trade-offs)
- Advanced (Multi-hop comparisons, loss formulations, failure modes)
"""

from typing import List, Dict, Any, Optional
import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.adaptive.llm_factory import get_llm
from src.retrieval.hybrid_retriever import HybridRetriever


class InteractiveQuizManager:
    """
    Generates dynamic assessment questions progressing in difficulty based on user mastery.
    """

    def __init__(self, hybrid_retriever: Optional[HybridRetriever] = None):
        self.retriever = hybrid_retriever or HybridRetriever()

    def generate_single_question(
        self,
        topic: str,
        question_number: int,
        difficulty: str = "intermediate",
        previous_questions: Optional[List[str]] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically generates ONE tailored question matching the learner's current mastery level (easy, intermediate, advanced).
        """
        # Retrieve freshest context chunks for this topic
        retrieval = self.retriever.retrieve(query=f"{topic} {difficulty}", top_k=4)
        docs = retrieval.get("final_documents", [])
        context_text = "\n\n".join([f"[{i+1}] {d.get('text', '')}" for i, d in enumerate(docs)])

        llm = get_llm(temperature=0.4, api_key=api_key)

        prev_context = ""
        if previous_questions:
            prev_context = "Do NOT repeat or test the exact same concepts as these previous questions:\n" + "\n".join(f"- {q}" for q in previous_questions)

        difficulty_instructions = {
            "easy": "Difficulty: BEGINNER / EASY. Focus on core definitions, purpose, and basic terminology.",
            "intermediate": "Difficulty: INTERMEDIATE. Focus on algorithmic mechanisms, trade-offs, and operational equations.",
            "advanced": "Difficulty: ADVANCED / EXPERT. Focus on edge cases, mathematical derivations, ablation findings, and failure modes across architectures."
        }

        diff_desc = difficulty_instructions.get(difficulty.lower(), difficulty_instructions["intermediate"])

        if llm is None:
            raise ValueError(
                "No API Key provided! To dynamically generate dynamic quiz questions on the go with the LLM, "
                "please enter your Groq API key in the top bar or set GROQ_API_KEY in your .env file."
            )

        try:
            system_msg = (
                "You are an expert AI and LLM university professor creating an adaptive exam question on the go.\n"
                f"Topic: '{topic}'.\n"
                f"{diff_desc}\n"
                f"{prev_context}\n\n"
                f"Reference Course Evidence from vector DB:\n{context_text}\n\n"
                "Generate ONE multiple choice question with 4 options (A, B, C, D).\n"
                "Return strictly a raw JSON object with NO markdown formatting, NO backticks, adhering to this structure:\n"
                "{\n"
                f'  "id": {question_number},\n'
                f'  "difficulty": "{difficulty}",\n'
                '  "question": "Question text here?",\n'
                '  "options": ["A. Choice 1", "B. Choice 2", "C. Choice 3", "D. Choice 4"],\n'
                '  "correct_option": "B",\n'
                '  "explanation": "Detailed explanation of why B is correct..."\n'
                "}"
            )
            # Escape curly braces for LangChain ChatPromptTemplate template variables
            escaped_system_msg = system_msg.replace("{", "{{").replace("}", "}}")
            human_msg = f"Create dynamic question #{question_number} now."

            prompt = ChatPromptTemplate.from_messages([
                ("system", escaped_system_msg),
                ("human", human_msg)
            ])
            chain = prompt | llm | StrOutputParser()
            raw_out = chain.invoke({})
            
            # Strip markdown code fences if LLM wrapped in ```json
            cleaned = re.sub(r'^```(?:json)?\s*', '', raw_out.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r'\s*```$', '', cleaned.strip())
            
            data = json.loads(cleaned)
            data["difficulty"] = difficulty
            return data
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to generate dynamic question using LLM: {str(e)}")

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

        if llm is not None:
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system",
                     "You are an expert AI and LLM university professor creating an adaptive exam question.\n"
                     f"Topic: '{topic}'.\n"
                     f"{diff_desc}\n"
                     f"{prev_context}\n\n"
                     f"Reference Course Evidence:\n{context_text}\n\n"
                     "Generate ONE multiple choice question with 4 options (A, B, C, D).\n"
                     "Return strictly a raw JSON object with NO markdown formatting, NO backticks, in this exact format:\n"
                     "{\n"
                     f'  "id": {question_number},\n'
                     f'  "difficulty": "{difficulty}",\n'
                     '  "question": "Question text here?",\n'
                     '  "options": ["A. Choice 1", "B. Choice 2", "C. Choice 3", "D. Choice 4"],\n'
                     '  "correct_option": "B",\n'
                     '  "explanation": "Detailed explanation of why B is correct..."\n'
                     "}"),
                    ("human", f"Create question #{question_number} now.")
                ])
                chain = prompt | llm | StrOutputParser()
                raw_out = chain.invoke({})
                
                # Strip markdown code fences if LLM wrapped in ```json
                cleaned = re.sub(r'^```(?:json)?\s*', '', raw_out.strip(), flags=re.IGNORECASE)
                cleaned = re.sub(r'\s*```$', '', cleaned.strip())
                
                data = json.loads(cleaned)
                data["difficulty"] = difficulty
                return data
            except Exception as e:
                print(f"Dynamic single question error: {e}")

        # Dynamic fallback questions tailored by difficulty level
        return self._fallback_question_for_level(topic, question_number, difficulty)

    def _fallback_question_for_level(self, topic: str, q_num: int, difficulty: str) -> Dict[str, Any]:
        """Fallback question tailored to difficulty if LLM key is absent."""
        if difficulty == "easy":
            return {
                "id": q_num,
                "difficulty": "easy",
                "question": f"At a foundational level, what is the primary motivation for studying {topic} in modern Large Language Models?",
                "options": [
                    "A. To replace tokenization with convolutional pixel maps",
                    "B. To capture semantic dependencies across sequences or integrate external factual knowledge",
                    "C. To prevent the model from using GPU tensor cores",
                    "D. To guarantee zero parameter training loss in 1 epoch"
                ],
                "correct_option": "B",
                "explanation": f"In {topic}, the primary goal is capturing long-range contextual relationships or integrating non-parametric external retrieval memory to ground LLM generations."
            }
        elif difficulty == "advanced":
            return {
                "id": q_num,
                "difficulty": "advanced",
                "question": f"In advanced {topic} implementations (such as Self-RAG or FlashAttention), how are computational bottlenecks or hallucination risks formally mitigated?",
                "options": [
                    "A. By eliminating the multi-head projection matrices entirely",
                    "B. By learning special reflection tokens (<RETRIEVE>, <CRITIQUE>) or tiling memory to minimize HBM reads/writes",
                    "C. By running the model strictly on CPU DRAM",
                    "D. By fixing the attention matrix to a static uniform distribution"
                ],
                "correct_option": "B",
                "explanation": "Advanced methods use learned critique tokens to selectively trigger retrieval and verify factual grounding (Self-RAG), or tile attention computation in SRAM to avoid memory bandwidth bottlenecks (FlashAttention)."
            }
        else: # intermediate
            return {
                "id": q_num,
                "difficulty": "intermediate",
                "question": f"When analyzing {topic}, what mathematical role does the normalization/scaling factor play during inference?",
                "options": [
                    "A. It scales dot-product logits by 1/sqrt(d_k) to prevent softmax saturation into vanishing gradient regimes",
                    "B. It multiplies output activations by a random scalar to induce stochasticity",
                    "C. It zeroes out all odd-numbered token embeddings",
                    "D. It converts dense representations into sparse one-hot vectors"
                ],
                "correct_option": "A",
                "explanation": "Scaling by 1/sqrt(d_k) stabilizes dot products so that softmax distributions do not peak excessively, preserving smooth gradient flow during learning."
            }

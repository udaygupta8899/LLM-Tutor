"""
Adaptive Agentic RAG Graph Workflow using LangGraph.
Integrates:
1. Prompt Injection Detection (Security Gate)
2. Query Complexity Classification (Adaptive Router)
3. Routing: Straightforward -> Direct LLM; Simple -> Single-Step Hybrid RAG; Complex -> Agentic Decomposition & Iterative Hybrid Retrieval
4. Evidence Grading & Query Rewriting
5. Tutor Mode Generation
6. Grounding & Hallucination Verification
7. Learner Memory Updates
"""

from typing import List, Dict, Any, TypedDict, Optional
import time

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.security.prompt_injection_detector import PromptInjectionDetector
from src.adaptive.classifier import AdaptiveClassifier
from src.adaptive.decomposer import QueryDecomposer
from src.adaptive.verifier import HallucinationVerifier
from src.retrieval.hybrid_retriever import HybridRetriever
from src.tutor.tutor_generator import TutorGenerator
from src.tutor.learner_memory import LearnerMemory
from src.config import settings


class AgentState(TypedDict):
    question: str
    original_question: str
    student_id: str
    tutor_mode: str
    chat_history: str
    api_key: Optional[str]
    
    # Security layer state
    security_result: Dict[str, Any]
    security_status: str  # ALLOW, WARN, BLOCKED
    
    # Adaptive routing state
    complexity: str  # straightforward, simple, complex
    complexity_confidence: float
    routing_strategy: str  # direct, single_rag, agentic_rag
    
    # Multi-hop & retrieval state
    subqueries: List[str]
    retrieved_documents: List[Dict[str, Any]]
    retrieval_stats: Dict[str, Any]
    loop_step: int
    
    # Synthesis & Verification
    generation: str
    verification_result: Dict[str, Any]
    latency_seconds: float


class AdaptiveAgenticRAGTutor:
    """
    High-level orchestrator wrapping the LangGraph state machine.
    """

    def __init__(
        self,
        hybrid_retriever: Optional[HybridRetriever] = None,
        injection_detector: Optional[PromptInjectionDetector] = None
    ):
        self.detector = injection_detector or PromptInjectionDetector()
        self.retriever = hybrid_retriever or HybridRetriever()
        self.classifier = AdaptiveClassifier()
        self.decomposer = QueryDecomposer()
        self.verifier = HallucinationVerifier()
        self.generator = TutorGenerator()
        self.memory = LearnerMemory()
        
        # Build LangGraph workflow
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Nodes
        workflow.add_node("security_check", self._node_security_check)
        workflow.add_node("block_query", self._node_block_query)
        workflow.add_node("classify_complexity", self._node_classify_complexity)
        workflow.add_node("direct_generate", self._node_direct_generate)
        workflow.add_node("single_step_retrieve", self._node_single_step_retrieve)
        workflow.add_node("decompose_query", self._node_decompose_query)
        workflow.add_node("iterative_retrieve", self._node_iterative_retrieve)
        workflow.add_node("grade_evidence", self._node_grade_evidence)
        workflow.add_node("rewrite_query", self._node_rewrite_query)
        workflow.add_node("synthesize_answer", self._node_synthesize_answer)
        workflow.add_node("verify_grounding", self._node_verify_grounding)
        workflow.add_node("record_memory", self._node_record_memory)

        # Entry point
        workflow.set_entry_point("security_check")

        # Edges
        # 1. Security Decision
        workflow.add_conditional_edges(
            "security_check",
            lambda s: "blocked" if s.get("security_status") == "BLOCKED" else "allowed",
            {
                "blocked": "block_query",
                "allowed": "classify_complexity"
            }
        )
        workflow.add_edge("block_query", "record_memory")

        # 2. Adaptive Routing Decision
        workflow.add_conditional_edges(
            "classify_complexity",
            lambda s: s.get("complexity", "simple"),
            {
                "straightforward": "direct_generate",
                "simple": "single_step_retrieve",
                "complex": "decompose_query"
            }
        )

        # 3. Direct route goes straight to synthesis
        workflow.add_edge("direct_generate", "verify_grounding")

        # 4. Simple route retrieves then grades
        workflow.add_edge("single_step_retrieve", "grade_evidence")

        # 5. Complex route decomposes then iterates retrieval then grades
        workflow.add_edge("decompose_query", "iterative_retrieve")
        workflow.add_edge("iterative_retrieve", "grade_evidence")

        # 6. Evidence grading: rewrite if insufficient and under retry limit, otherwise synthesize
        def decide_evidence_sufficiency(state: AgentState):
            docs = state.get("retrieved_documents", [])
            loop = state.get("loop_step", 0)
            if not docs and loop < settings.MAX_RETRIES:
                return "rewrite"
            return "synthesize"

        workflow.add_conditional_edges(
            "grade_evidence",
            decide_evidence_sufficiency,
            {
                "rewrite": "rewrite_query",
                "synthesize": "synthesize_answer"
            }
        )
        workflow.add_edge("rewrite_query", "single_step_retrieve")

        # 7. Synthesis to verification
        workflow.add_edge("synthesize_answer", "verify_grounding")

        # 8. Verification to record memory and finish
        workflow.add_edge("verify_grounding", "record_memory")
        workflow.add_edge("record_memory", END)

        memory_checkpointer = MemorySaver()
        return workflow.compile(checkpointer=memory_checkpointer)

    # Node Implementations
    def _node_security_check(self, state: AgentState):
        question = state["question"]
        res = self.detector.inspect(question, is_document=False)
        status = "BLOCKED" if res["action"] == "BLOCK" else "ALLOW"
        return {"security_result": res, "security_status": status}

    def _node_block_query(self, state: AgentState):
        res = state["security_result"]
        return {
            "generation": (
                f"⚠️ **Security Alert**: Your request was flagged and quarantined by the Prompt Injection Detection Engine.\n\n"
                f"**Risk Level:** {res.get('risk_level', 'HIGH RISK')}\n"
                f"**Reason:** {res.get('explanation', 'Adversarial instruction patterns detected.')}\n\n"
                f"Please submit educational questions regarding Deep Learning and Machine Learning topics."
            ),
            "verification_result": {"is_grounded": True, "score": 1.0, "reasoning": "Security mitigation response."}
        }

    def _node_classify_complexity(self, state: AgentState):
        question = state["question"]
        history = state.get("chat_history", "")
        key = state.get("api_key")
        classification = self.classifier.classify(question, chat_history=history, api_key=key)
        
        comp = classification["category"]
        strategy = "direct" if comp == "straightforward" else ("single_rag" if comp == "simple" else "agentic_rag")
        
        return {
            "complexity": comp,
            "complexity_confidence": classification["confidence"],
            "routing_strategy": strategy
        }

    def _node_direct_generate(self, state: AgentState):
        question = state["question"]
        mode = state.get("tutor_mode", "explain")
        student_id = state.get("student_id", "default_student")
        profile = self.memory.get_profile(student_id)
        key = state.get("api_key")
        
        generation = self.generator.generate(
            question=question,
            tutor_mode=mode,
            mastery_level=profile["mastery_level"],
            context_documents=[],
            api_key=key
        )
        return {"generation": generation, "retrieved_documents": []}

    def _node_single_step_retrieve(self, state: AgentState):
        question = state["question"]
        retrieval = self.retriever.retrieve(query=question, top_k=settings.TOP_K)
        return {
            "retrieved_documents": retrieval["final_documents"],
            "retrieval_stats": retrieval["stats"]
        }

    def _node_decompose_query(self, state: AgentState):
        question = state["question"]
        key = state.get("api_key")
        subqueries = self.decomposer.decompose(question, api_key=key)
        return {"subqueries": subqueries}

    def _node_iterative_retrieve(self, state: AgentState):
        subqueries = state.get("subqueries", [state["question"]])
        aggregated_docs = []
        seen_ids = set()
        
        for sq in subqueries:
            res = self.retriever.retrieve(query=sq, top_k=2)
            for d in res["final_documents"]:
                if d["id"] not in seen_ids:
                    seen_ids.add(d["id"])
                    aggregated_docs.append(d)
                    
        return {
            "retrieved_documents": aggregated_docs[:settings.TOP_K + 2],
            "retrieval_stats": {"total_subqueries": len(subqueries), "unique_docs": len(aggregated_docs)}
        }

    def _node_grade_evidence(self, state: AgentState):
        # Filter out low-confidence documents or documents containing quarantined indirect injections
        clean_docs = []
        for doc in state.get("retrieved_documents", []):
            text = doc.get("text", "")
            # Security check on retrieved context chunk (Defense in depth)
            sec = self.detector.inspect(text, is_document=True)
            if sec["action"] != "QUARANTINE":
                clean_docs.append(doc)
                
        return {"retrieved_documents": clean_docs}

    def _node_rewrite_query(self, state: AgentState):
        loop_step = state.get("loop_step", 0)
        q = state.get("question", "")
        rewritten = f"{q} deep learning fundamentals and architecture"
        return {"question": rewritten, "loop_step": loop_step + 1}

    def _node_synthesize_answer(self, state: AgentState):
        question = state["original_question"]
        mode = state.get("tutor_mode", "explain")
        student_id = state.get("student_id", "default_student")
        profile = self.memory.get_profile(student_id)
        docs = state.get("retrieved_documents", [])
        key = state.get("api_key")
        
        generation = self.generator.generate(
            question=question,
            tutor_mode=mode,
            mastery_level=profile["mastery_level"],
            context_documents=docs,
            chat_history=state.get("chat_history"),
            api_key=key
        )
        return {"generation": generation}

    def _node_verify_grounding(self, state: AgentState):
        answer = state.get("generation", "")
        docs = state.get("retrieved_documents", [])
        key = state.get("api_key")
        v_res = self.verifier.verify(answer, docs, api_key=key)
        return {"verification_result": v_res}

    def _node_record_memory(self, state: AgentState):
        student_id = state.get("student_id", "default_student")
        q = state.get("original_question", "")
        ans = state.get("generation", "")
        comp = state.get("complexity", "unknown")
        mode = state.get("tutor_mode", "explain")
        grounded = state.get("verification_result", {}).get("is_grounded", True)
        
        self.memory.record_interaction(
            student_id=student_id,
            question=q,
            complexity=comp,
            tutor_mode=mode,
            answer=ans,
            grounded=grounded
        )
        return {}

    def run(
        self,
        question: str,
        student_id: str = "student_1",
        tutor_mode: str = "explain",
        thread_id: str = "default_thread",
        chat_history: str = "",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs the full Adaptive Agentic RAG tutoring pipeline.
        """
        start_time = time.time()
        
        initial_state: AgentState = {
            "question": question,
            "original_question": question,
            "student_id": student_id,
            "tutor_mode": tutor_mode,
            "chat_history": chat_history,
            "api_key": api_key,
            "security_result": {},
            "security_status": "PENDING",
            "complexity": "simple",
            "complexity_confidence": 0.0,
            "routing_strategy": "single_rag",
            "subqueries": [],
            "retrieved_documents": [],
            "retrieval_stats": {},
            "loop_step": 0,
            "generation": "",
            "verification_result": {},
            "latency_seconds": 0.0
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        final_state = self.graph.invoke(initial_state, config=config)
        
        elapsed = round(time.time() - start_time, 3)
        final_state["latency_seconds"] = elapsed
        return final_state

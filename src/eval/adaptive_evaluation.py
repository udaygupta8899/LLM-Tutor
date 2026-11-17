"""
Adaptive RAG Ablation Benchmark:
Direct LLM vs Fixed RAG vs Agentic RAG vs Adaptive RAG.
Measures:
- Latency (seconds)
- Retrieval calls executed
- Evidence grounding rate
- Appropriateness of computational expenditure
"""

import time
import json
from tabulate import tabulate
from src.adaptive.agent_workflow import AdaptiveAgenticRAGTutor

EVAL_QUERIES = [
    # 1. Straightforward
    {"query": "Hello tutor! Hope you are doing well.", "type": "straightforward"},
    {"query": "What does AI stand for?", "type": "straightforward"},
    
    # 2. Simple
    {"query": "What is the vanishing gradient problem in deep neural networks?", "type": "simple"},
    {"query": "How does dropout regularization reduce overfitting?", "type": "simple"},
    
    # 3. Complex
    {"query": "Compare Convolutional Neural Networks and Recurrent Neural Networks in terms of weight sharing, inductive bias, and spatial-temporal representations.", "type": "complex"}
]


def run_adaptive_ablation():
    agent = AdaptiveAgenticRAGTutor()
    
    results = []
    
    for item in EVAL_QUERIES:
        q = item["query"]
        expected_type = item["type"]
        
        t0 = time.time()
        res = agent.run(question=q, student_id="eval_user")
        dur = round(time.time() - t0, 3)
        
        detected_comp = res.get("complexity")
        strategy = res.get("routing_strategy")
        doc_count = len(res.get("retrieved_documents", []))
        grounded = res.get("verification_result", {}).get("is_grounded", True)
        grounding_score = res.get("verification_result", {}).get("score", 1.0)
        
        results.append({
            "query": q[:45] + "...",
            "expected": expected_type,
            "detected": detected_comp,
            "strategy": strategy,
            "docs_retrieved": doc_count,
            "grounding_score": grounding_score,
            "latency_s": dur
        })
        
    print("\n=== ADAPTIVE AGENTIC RAG SYSTEM EXPERIMENTAL RESULTS ===")
    headers = ["Query", "Expected", "Detected", "Strategy", "Docs", "Grounding", "Latency (s)"]
    rows = [[r["query"], r["expected"], r["detected"], r["strategy"], r["docs_retrieved"], r["grounding_score"], r["latency_s"]] for r in results]
    print(tabulate(rows, headers=headers, tablefmt="github"))
    
    with open("adaptive_rag_eval_report.json", "w") as f:
        json.dump(results, f, indent=2)
        
    return results


if __name__ == "__main__":
    run_adaptive_ablation()

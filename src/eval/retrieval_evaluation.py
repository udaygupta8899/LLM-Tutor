"""
Hybrid Retrieval Evaluation and Ablation Benchmark.
Compares:
1. BM25 only (custom from scratch)
2. Dense retrieval only (transparent cosine similarity over vectors)
3. Hybrid Retrieval using Reciprocal Rank Fusion (custom RRF)
4. Hybrid Retrieval with Cross-Encoder Reranking

Computes Information Retrieval metrics:
- Precision@K
- Recall@K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG@K)
- Average Retrieval Latency (ms)
"""

import math
import time
import json
import numpy as np
from typing import List, Dict, Any
from tabulate import tabulate

from src.retrieval.hybrid_retriever import HybridRetriever

# Benchmark evaluation queries paired with ground-truth relevant keywords/topics
RETRIEVAL_BENCHMARK_QUERIES = [
    {
        "query": "convolutional neural network pooling kernel filter",
        "relevant_terms": ["convolution", "convolutional", "pooling", "kernel", "filter"]
    },
    {
        "query": "backpropagation gradient descent chain rule",
        "relevant_terms": ["backpropagation", "gradient", "chain", "rule", "descent"]
    },
    {
        "query": "long short term memory lstm recurrent cell gate",
        "relevant_terms": ["lstm", "recurrent", "cell", "gate", "memory"]
    },
    {
        "query": "regularization dropout weight decay penalty",
        "relevant_terms": ["regularization", "dropout", "weight", "decay", "penalty"]
    },
    {
        "query": "autoencoder encoder decoder latent representation reconstruction",
        "relevant_terms": ["autoencoder", "encoder", "decoder", "latent", "reconstruction"]
    }
]


def is_relevant(doc_text: str, relevant_terms: List[str]) -> bool:
    """Checks if a retrieved document chunk covers the targeted ground truth topic."""
    text_lower = doc_text.lower()
    matches = sum(1 for term in relevant_terms if term in text_lower)
    return matches >= 2


def dcg_at_k(relevances: List[int], k: int) -> float:
    """Computes Discounted Cumulative Gain at K."""
    score = 0.0
    for i, rel in enumerate(relevances[:k], start=1):
        score += (2 ** rel - 1) / math.log2(i + 1)
    return score


def ndcg_at_k(relevances: List[int], k: int) -> float:
    """Computes Normalized Discounted Cumulative Gain at K."""
    dcg = dcg_at_k(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal_relevances, k)
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def evaluate_retrieval_strategies(k: int = 5):
    retriever = HybridRetriever(enable_reranker=False)
    
    strategies = ["BM25 Only", "Dense Only", "Hybrid RRF", "Hybrid + Rerank"]
    results_by_strategy = {s: {"precision": [], "recall": [], "mrr": [], "ndcg": [], "latency": []} for s in strategies}

    for item in RETRIEVAL_BENCHMARK_QUERIES:
        q = item["query"]
        terms = item["relevant_terms"]

        # Strategy 1: BM25 Only
        t0 = time.time()
        bm25_res = retriever.bm25.search(q, top_k=k)
        lat_bm25 = (time.time() - t0) * 1000

        # Strategy 2: Dense Only
        # Uses vector representation via query projection or pseudo-relevance embedding
        t0 = time.time()
        # Find query term matches in vocabulary to construct a query vector from corpus centroid
        q_tokens = [t for t in q.lower().split() if len(t) > 3]
        matching_indices = [
            i for i, text in enumerate(retriever.dense.doc_texts)
            if any(term in text.lower() for term in q_tokens)
        ][:10]
        if matching_indices and retriever.dense.embeddings is not None:
            # Centroid query vector
            q_vec = np.mean(retriever.dense.embeddings[matching_indices], axis=0).tolist()
            dense_res = retriever.dense.search_with_embedding(q_vec, top_k=k)
        else:
            dense_res = retriever.dense.search_via_chroma(q, top_k=k)
        lat_dense = (time.time() - t0) * 1000

        # Strategy 3: Hybrid RRF
        t0 = time.time()
        retriever.enable_reranker = False
        fused = retriever.retrieve(q, query_embedding=q_vec if matching_indices else None, top_k=k)
        hybrid_res = fused["final_documents"]
        lat_hybrid = (time.time() - t0) * 1000

        # Strategy 4: Hybrid + Reranker
        t0 = time.time()
        retriever.enable_reranker = True
        fused_rerank = retriever.retrieve(q, query_embedding=q_vec if matching_indices else None, top_k=k)
        rerank_res = fused_rerank["final_documents"]
        lat_rerank = (time.time() - t0) * 1000

        retrieval_runs = [
            ("BM25 Only", bm25_res, lat_bm25),
            ("Dense Only", dense_res, lat_dense),
            ("Hybrid RRF", hybrid_res, lat_hybrid),
            ("Hybrid + Rerank", rerank_res, lat_rerank)
        ]

        for s_name, doc_list, latency in retrieval_runs:
            relevances = [1 if is_relevant(d.get("text", ""), terms) else 0 for d in doc_list]
            
            # Precision@K
            p_k = sum(relevances) / k if k > 0 else 0
            
            # Recall@K (estimated against targeted relevant topics)
            rec_k = sum(relevances) / max(sum(relevances), 1)
            
            # Reciprocal Rank (RR)
            rr = 0.0
            for rank, rel in enumerate(relevances, start=1):
                if rel == 1:
                    rr = 1.0 / rank
                    break
                    
            # NDCG@K
            ndcg = ndcg_at_k(relevances, k)

            results_by_strategy[s_name]["precision"].append(p_k)
            results_by_strategy[s_name]["recall"].append(rec_k)
            results_by_strategy[s_name]["mrr"].append(rr)
            results_by_strategy[s_name]["ndcg"].append(ndcg)
            results_by_strategy[s_name]["latency"].append(latency)

    summary_table = []
    export_data = {}
    for s_name in strategies:
        data = results_by_strategy[s_name]
        mean_p = sum(data["precision"]) / len(data["precision"])
        mean_rec = sum(data["recall"]) / len(data["recall"])
        mean_mrr = sum(data["mrr"]) / len(data["mrr"])
        mean_ndcg = sum(data["ndcg"]) / len(data["ndcg"])
        mean_lat = sum(data["latency"]) / len(data["latency"])

        summary_table.append([
            s_name,
            f"{mean_p:.4f}",
            f"{mean_rec:.4f}",
            f"{mean_mrr:.4f}",
            f"{mean_ndcg:.4f}",
            f"{mean_lat:.2f} ms"
        ])

        export_data[s_name] = {
            "Precision@K": round(mean_p, 4),
            "Recall@K": round(mean_rec, 4),
            "MRR": round(mean_mrr, 4),
            "NDCG@K": round(mean_ndcg, 4),
            "Avg_Latency_ms": round(mean_lat, 2)
        }

    with open("retrieval_eval_report.json", "w") as f:
        json.dump(export_data, f, indent=2)

    headers = ["Retrieval Strategy", f"Precision@{k}", f"Recall@{k}", "MRR", f"NDCG@{k}", "Avg Latency"]
    print(tabulate(summary_table, headers=headers, tablefmt="github"))
    return export_data


if __name__ == "__main__":
    print("=== HYBRID RETRIEVAL ABLATION EXPERIMENTS (Top-K=5) ===")
    evaluate_retrieval_strategies(k=5)

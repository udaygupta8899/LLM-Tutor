r"""
Reciprocal Rank Fusion (RRF) Implementation from Scratch.
Merges rankings from multiple disparate information retrieval systems (e.g. BM25 & Dense).

Formula:
    RRF_score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}
where:
    - M is the set of retrieval models
    - r_m(d) is the 1-based rank of document d in model m
    - k is a smoothing constant (standard default = 60)
"""

from typing import List, Dict, Any, Optional


def reciprocal_rank_fusion(
    rankings: List[List[Dict[str, Any]]],
    k: int = 60,
    top_k: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fuses multiple ranked lists using Reciprocal Rank Fusion.
    
    Args:
        rankings: A list of rankings, where each ranking is a list of doc dicts 
                  containing at least 'id' and optionally 'text', 'metadata', 'score', 'rank'.
        k: Smoothing constant parameter (default: 60).
        top_k: Optional max number of fused documents to return.
        
    Returns:
        Sorted list of fused documents with composite 'rrf_score', 'rank', and individual model details.
    """
    if not rankings:
        return []

    # Map doc_id -> fused stats
    fused_docs: Dict[str, Dict[str, Any]] = {}

    for ranking_idx, rank_list in enumerate(rankings):
        for rank_position, doc in enumerate(rank_list, start=1):
            doc_id = doc.get("id")
            if not doc_id:
                continue

            # Compute reciprocal rank component
            rrf_increment = 1.0 / (k + rank_position)
            
            source_system = doc.get("retriever", f"model_{ranking_idx}")
            orig_score = doc.get("score", 0.0)

            if doc_id not in fused_docs:
                fused_docs[doc_id] = {
                    "id": doc_id,
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "rrf_score": 0.0,
                    "ranks": {},
                    "scores": {},
                    "sources": []
                }

            fused_docs[doc_id]["rrf_score"] += rrf_increment
            fused_docs[doc_id]["ranks"][source_system] = rank_position
            fused_docs[doc_id]["scores"][source_system] = orig_score
            if source_system not in fused_docs[doc_id]["sources"]:
                fused_docs[doc_id]["sources"].append(source_system)

    # Sort documents by RRF score descending
    sorted_docs = sorted(
        fused_docs.values(),
        key=lambda item: item["rrf_score"],
        reverse=True
    )

    # Assign final fused rank
    for rank, doc in enumerate(sorted_docs, start=1):
        doc["rank"] = rank

    if top_k is not None:
        return sorted_docs[:top_k]

    return sorted_docs

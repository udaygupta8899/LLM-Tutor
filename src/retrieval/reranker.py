"""
Reranker Module for Post-Retrieval Scoring.
Supports pretrained cross-encoder models and lightweight score fusion.
"""

from typing import List, Dict, Any, Optional
import os


class Reranker:
    """
    Cross-Encoder Reranker.
    Uses sentence-transformers CrossEncoder if available, with transparent fallback.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", enabled: bool = True):
        self.enabled = enabled
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None and self.enabled:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except Exception as e:
                # If model download fails or is offline, log and keep _model as None
                self._model = None

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate documents against query using cross-encoder scoring.
        """
        if not documents:
            return []

        if not self.enabled:
            return documents[:top_k] if top_k else documents

        self._load_model()
        if self._model is None:
            # Fallback: preserve original ranking
            return documents[:top_k] if top_k else documents

        pairs = [[query, doc.get("text", "")] for doc in documents]
        try:
            scores = self._model.predict(pairs)
            
            reranked = []
            for doc, score in zip(documents, scores):
                doc_copy = dict(doc)
                doc_copy["rerank_score"] = float(score)
                reranked.append(doc_copy)

            reranked.sort(key=lambda d: d["rerank_score"], reverse=True)
            for rank, doc in enumerate(reranked, start=1):
                doc["rerank_rank"] = rank

            return reranked[:top_k] if top_k else reranked
        except Exception:
            return documents[:top_k] if top_k else documents

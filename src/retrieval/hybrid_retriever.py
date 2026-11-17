"""
Hybrid Retriever Orchestrator.
Combines BM25 sparse lexical retrieval, dense semantic retrieval,
Reciprocal Rank Fusion (RRF), and optional cross-encoder reranking.
"""

from typing import List, Dict, Any, Optional
import os

from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense_retriever import DenseRetriever
from src.retrieval.rrf import reciprocal_rank_fusion
from src.retrieval.reranker import Reranker
from src.config import settings


class HybridRetriever:
    """
    Intelligent Hybrid Retrieval Engine.
    Executes lexical and semantic retrieval in parallel, combines via RRF, and applies reranking.
    """

    def __init__(
        self,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
        rrf_k: int = 60,
        enable_reranker: bool = False,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        self.rrf_k = rrf_k
        self.enable_reranker = enable_reranker

        # Initialize sub-retrievers
        self.bm25 = BM25Retriever(k1=bm25_k1, b=bm25_b)
        self.dense = DenseRetriever(
            persist_directory=persist_directory or settings.CHROMA_PERSIST_DIR,
            collection_name=collection_name or settings.CHROMA_COLLECTION_NAME
        )
        self.reranker = Reranker(
            model_name=settings.RERANKER_MODEL,
            enabled=enable_reranker
        )

        # Index BM25 from dense collection documents if available
        if len(self.dense.doc_texts) > 0:
            self.bm25.index_documents(
                documents=self.dense.doc_texts,
                doc_ids=self.dense.doc_ids,
                metadatas=self.dense.doc_metadatas
            )

    def index_documents(
        self,
        documents: List[str],
        doc_ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """Indexes documents into the sparse engine (and updates collection)."""
        self.bm25.index_documents(documents, doc_ids=doc_ids, metadatas=metadatas)

    def retrieve(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        candidate_multiplier: int = 4
    ) -> Dict[str, Any]:
        """
        Executes hybrid retrieval workflow:
        1. BM25 sparse search
        2. Dense vector search
        3. Reciprocal Rank Fusion
        4. Optional reranking
        
        Returns:
            Dictionary containing final results, intermediate rankings, and diagnostics.
        """
        candidates_k = max(top_k * candidate_multiplier, 20)

        # 1. BM25 Search
        bm25_results = self.bm25.search(query=query, top_k=candidates_k)

        # 2. Dense Search
        dense_results = []
        if query_embedding is not None:
            dense_results = self.dense.search_with_embedding(query_embedding, top_k=candidates_k)
        else:
            # Fallback to query_via_chroma if query embedding is not directly supplied
            dense_results = self.dense.search_via_chroma(query, top_k=candidates_k)

        # 3. Reciprocal Rank Fusion
        fused_results = reciprocal_rank_fusion(
            rankings=[bm25_results, dense_results],
            k=self.rrf_k,
            top_k=candidates_k
        )

        # 4. Optional Reranking
        final_results = fused_results
        if self.enable_reranker:
            final_results = self.reranker.rerank(
                query=query,
                documents=fused_results,
                top_k=top_k
            )
        else:
            final_results = fused_results[:top_k]

        return {
            "query": query,
            "final_documents": final_results,
            "bm25_candidates": bm25_results[:top_k],
            "dense_candidates": dense_results[:top_k],
            "fused_candidates": fused_results[:top_k],
            "stats": {
                "bm25_total_found": len(bm25_results),
                "dense_total_found": len(dense_results),
                "fused_total": len(fused_results),
                "reranker_applied": self.enable_reranker
            }
        }

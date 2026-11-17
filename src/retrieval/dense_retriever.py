"""
Dense Vector Retriever Module.
Interacts with ChromaDB and embedding models, computing cosine similarity 
and document ranking in custom, transparent Python code.
"""

import math
import numpy as np
from typing import List, Dict, Any, Optional
import chromadb
from src.config import settings


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two vectors from scratch."""
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b
    
    denom = math.sqrt(norm_a) * math.sqrt(norm_b)
    if denom == 0.0:
        return 0.0
    return dot / denom


class DenseRetriever:
    """
    Dense Semantic Retriever.
    Uses ChromaDB collection to fetch stored document vectors or documents,
    computes cosine similarities directly, and generates transparent semantic rankings.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        
        # Connect to ChromaDB
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        
        # Document and embedding cache
        self.doc_ids: List[str] = []
        self.doc_texts: List[str] = []
        self.doc_metadatas: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        
        self._load_collection_data()

    def _load_collection_data(self):
        """Loads all documents, metadatas, and embeddings from ChromaDB for fast in-memory similarity."""
        count = self.collection.count()
        if count == 0:
            return

        # Fetch in batches if necessary, or get all
        data = self.collection.get(include=["documents", "metadatas", "embeddings"])
        self.doc_ids = data["ids"]
        self.doc_texts = data["documents"]
        self.doc_metadatas = data["metadatas"] or [{} for _ in self.doc_ids]
        
        if data["embeddings"] is not None and len(data["embeddings"]) > 0:
            self.embeddings = np.array(data["embeddings"], dtype=np.float32)
            # Normalize embeddings for fast dot-product cosine similarity
            norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.normed_embeddings = self.embeddings / norms
        else:
            self.embeddings = None
            self.normed_embeddings = None

    def search_with_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Ranks all indexed documents against query_embedding using cosine similarity.
        """
        if self.normed_embeddings is None or len(self.doc_ids) == 0:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        # Matrix-vector dot product yields exact cosine similarities
        sim_scores = np.dot(self.normed_embeddings, q_vec)

        # Get top-k indices
        top_indices = np.argsort(sim_scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices, start=1):
            results.append({
                "id": self.doc_ids[idx],
                "score": float(sim_scores[idx]),
                "rank": rank,
                "text": self.doc_texts[idx],
                "metadata": self.doc_metadatas[idx],
                "retriever": "dense"
            })

        return results

    def search_via_chroma(
        self,
        query_text: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fallback search using Chroma's query interface (e.g. when embeddings are generated on-the-fly by Chroma).
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            output = []
            if results and results["ids"] and len(results["ids"][0]) > 0:
                ids = results["ids"][0]
                docs = results["documents"][0]
                metas = results["metadatas"][0]
                dists = results["distances"][0] if "distances" in results else [0.0] * len(ids)
                
                for rank, (doc_id, text, meta, dist) in enumerate(zip(ids, docs, metas, dists), start=1):
                    # Chroma distance is often L2 or cosine distance: score = 1 / (1 + dist) or 1 - dist
                    score = 1.0 - (dist if dist is not None else 0.0)
                    output.append({
                        "id": doc_id,
                        "score": float(score),
                        "rank": rank,
                        "text": text,
                        "metadata": meta,
                        "retriever": "dense"
                    })
            return output
        except Exception:
            # If default embedding function is not configured in chroma, fallback gracefully
            return []

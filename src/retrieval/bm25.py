"""
Custom BM25 (Best Matching 25) Implementation from Scratch.
Implements Okapi BM25 scoring with Robertson-Spärck Jones IDF and document length normalization.
Fully compliant with IR theory without external BM25 library dependencies.
"""

import math
from typing import List, Dict, Tuple, Any, Optional
from src.retrieval.tokenizer import tokenize


class BM25Retriever:
    """
    Okapi BM25 Retrieval Engine implemented from scratch.
    
    Formula:
        score(D, Q) = sum_{q in Q} IDF(q) * [ f(q, D) * (k1 + 1) ] / [ f(q, D) + k1 * (1 - b + b * (|D| / avgdl)) ]
        
    where Robertson-Spärck Jones IDF with floor correction is:
        IDF(q) = ln( (N - n(q) + 0.5) / (n(q) + 0.5) + 1.0 )
        (The + 1.0 inside log prevents negative IDF values for terms appearing in > N/2 docs).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        
        # Corpus statistics
        self.corpus_size: int = 0
        self.avg_doc_len: float = 0.0
        self.doc_lengths: List[int] = []
        
        # Documents storage: list of raw text, tokens, and metadata
        self.doc_ids: List[str] = []
        self.doc_texts: List[str] = []
        self.doc_metadatas: List[Dict[str, Any]] = []
        self.doc_tokens: List[List[str]] = []
        
        # Inverted index: term -> list of (doc_index, term_frequency)
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {}
        # Document frequency: term -> number of docs containing term
        self.doc_freqs: Dict[str, int] = {}
        # Precomputed IDF cache
        self.idf_cache: Dict[str, float] = {}

    def index_documents(
        self,
        documents: List[str],
        doc_ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Builds the BM25 inverted index and document statistics.
        """
        self.corpus_size = len(documents)
        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            return

        self.doc_texts = documents
        self.doc_ids = doc_ids if doc_ids is not None else [str(i) for i in range(self.corpus_size)]
        self.doc_metadatas = metadatas if metadatas is not None else [{} for _ in range(self.corpus_size)]
        
        self.doc_tokens = []
        self.doc_lengths = []
        self.inverted_index = {}
        self.doc_freqs = {}
        self.idf_cache = {}

        total_length = 0

        for doc_idx, text in enumerate(documents):
            tokens = tokenize(text)
            self.doc_tokens.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_length += doc_len

            # Count term frequencies in this document
            tf_map: Dict[str, int] = {}
            for token in tokens:
                tf_map[token] = tf_map.get(token, 0) + 1

            for token, tf in tf_map.items():
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append((doc_idx, tf))
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avg_doc_len = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

        # Precompute IDF for all terms in vocabulary
        for term, df in self.doc_freqs.items():
            self.idf_cache[term] = self._calculate_idf(df)

    def add_document(
        self,
        document: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Incrementally index a single document.
        """
        doc_idx = self.corpus_size
        doc_id = doc_id if doc_id is not None else str(doc_idx)
        metadata = metadata if metadata is not None else {}
        
        tokens = tokenize(document)
        doc_len = len(tokens)
        
        self.doc_ids.append(doc_id)
        self.doc_texts.append(document)
        self.doc_metadatas.append(metadata)
        self.doc_tokens.append(tokens)
        self.doc_lengths.append(doc_len)
        
        prev_total = self.avg_doc_len * self.corpus_size
        self.corpus_size += 1
        self.avg_doc_len = (prev_total + doc_len) / self.corpus_size

        tf_map: Dict[str, int] = {}
        for token in tokens:
            tf_map[token] = tf_map.get(token, 0) + 1

        for token, tf in tf_map.items():
            if token not in self.inverted_index:
                self.inverted_index[token] = []
            self.inverted_index[token].append((doc_idx, tf))
            self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        # Recompute IDF cache for modified terms
        for term in tf_map.keys():
            self.idf_cache[term] = self._calculate_idf(self.doc_freqs[term])

    def _calculate_idf(self, doc_freq: int) -> float:
        """
        Calculates Robertson-Spärck Jones IDF with Lucene/Okapi smoothing to ensure non-negativity:
        IDF(q) = ln( 1 + (N - n + 0.5) / (n + 0.5) )
        """
        numerator = self.corpus_size - doc_freq + 0.5
        denominator = doc_freq + 0.5
        return math.log(1.0 + (numerator / denominator))

    def get_idf(self, term: str) -> float:
        """Retrieves or calculates IDF for a term."""
        if term in self.idf_cache:
            return self.idf_cache[term]
        df = self.doc_freqs.get(term, 0)
        idf = self._calculate_idf(df)
        self.idf_cache[term] = idf
        return idf

    def score_query(self, query: str) -> List[Tuple[int, float]]:
        """
        Scores all candidate documents for a given query.
        Returns a list of (doc_idx, score).
        """
        query_tokens = tokenize(query)
        if not query_tokens or self.corpus_size == 0:
            return []

        doc_scores: Dict[int, float] = {}

        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            idf = self.get_idf(token)
            postings = self.inverted_index[token]

            for doc_idx, tf in postings:
                doc_len = self.doc_lengths[doc_idx]
                len_norm = 1.0 - self.b + self.b * (doc_len / self.avg_doc_len if self.avg_doc_len > 0 else 1.0)
                tf_component = (tf * (self.k1 + 1.0)) / (tf + self.k1 * len_norm)
                score = idf * tf_component

                doc_scores[doc_idx] = doc_scores.get(doc_idx, 0.0) + score

        # Sort candidate documents descending by score
        ranked_docs = sorted(doc_scores.items(), key=lambda item: item[1], reverse=True)
        return ranked_docs

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Executes BM25 search and returns the top-K documents formatted with metadata and rank.
        """
        ranked_scores = self.score_query(query)
        results = []

        for rank, (doc_idx, score) in enumerate(ranked_scores[:top_k], start=1):
            results.append({
                "id": self.doc_ids[doc_idx],
                "score": float(score),
                "rank": rank,
                "text": self.doc_texts[doc_idx],
                "metadata": self.doc_metadatas[doc_idx],
                "retriever": "bm25"
            })

        return results

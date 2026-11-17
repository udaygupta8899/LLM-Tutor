import pytest
import math
from src.retrieval.tokenizer import tokenize, clean_text, simple_stem
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense_retriever import cosine_similarity
from src.retrieval.rrf import reciprocal_rank_fusion


def test_tokenizer():
    text = "Convolutional neural networks are trained using backpropagation!"
    tokens = tokenize(text)
    assert "convolutional" in tokens or "convolution" in tokens
    assert "network" in tokens  # stem check
    assert "backpropagation" in tokens
    assert "are" not in tokens  # stopword check


def test_bm25_scoring_and_ranking():
    corpus = [
        "Convolutional neural networks are designed for computer vision and image processing.",
        "Recurrent neural networks and LSTMs process sequential data and natural language text.",
        "Support vector machines are supervised learning models for classification.",
        "Backpropagation computes the gradient of the loss function in neural networks."
    ]
    doc_ids = ["doc_cnn", "doc_rnn", "doc_svm", "doc_backprop"]
    
    bm25 = BM25Retriever(k1=1.5, b=0.75)
    bm25.index_documents(corpus, doc_ids=doc_ids)
    
    assert bm25.corpus_size == 4
    assert bm25.avg_doc_len > 0
    
    # Query for CNN
    cnn_results = bm25.search("convolutional networks vision", top_k=2)
    assert len(cnn_results) > 0
    assert cnn_results[0]["id"] == "doc_cnn"
    assert cnn_results[0]["score"] > 0
    
    # Query for RNN
    rnn_results = bm25.search("sequential text recurrent", top_k=2)
    assert len(rnn_results) > 0
    assert rnn_results[0]["id"] == "doc_rnn"


def test_bm25_incremental_indexing():
    bm25 = BM25Retriever()
    bm25.index_documents(["Deep learning is a subset of machine learning."], doc_ids=["d1"])
    assert bm25.corpus_size == 1
    
    bm25.add_document("Transformers use self-attention mechanisms.", doc_id="d2")
    assert bm25.corpus_size == 2
    
    res = bm25.search("transformers attention", top_k=1)
    assert res[0]["id"] == "d2"


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    
    assert math.isclose(cosine_similarity(v1, v2), 1.0, rel_tol=1e-5)
    assert math.isclose(cosine_similarity(v1, v3), 0.0, rel_tol=1e-5)


def test_rrf_fusion():
    bm25_ranking = [
        {"id": "doc1", "score": 4.5, "retriever": "bm25"},
        {"id": "doc2", "score": 3.2, "retriever": "bm25"},
        {"id": "doc3", "score": 1.1, "retriever": "bm25"}
    ]
    dense_ranking = [
        {"id": "doc2", "score": 0.95, "retriever": "dense"},
        {"id": "doc1", "score": 0.80, "retriever": "dense"},
        {"id": "doc4", "score": 0.70, "retriever": "dense"}
    ]
    
    k = 60
    fused = reciprocal_rank_fusion([bm25_ranking, dense_ranking], k=k)
    
    assert len(fused) == 4
    # Expected doc1 score: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.016393 + 0.016129 = 0.032522
    # Expected doc2 score: 1/(60+2) + 1/(60+1) = 0.032522
    # doc1 and doc2 should be at the top
    top_ids = [fused[0]["id"], fused[1]["id"]]
    assert "doc1" in top_ids and "doc2" in top_ids
    assert fused[0]["rank"] == 1
    assert fused[1]["rank"] == 2
    assert "bm25" in fused[0]["ranks"]
    assert "dense" in fused[0]["ranks"]

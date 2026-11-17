import pytest
from src.adaptive.classifier import AdaptiveClassifier
from src.adaptive.decomposer import QueryDecomposer
from src.adaptive.verifier import HallucinationVerifier


def test_classifier_straightforward():
    classifier = AdaptiveClassifier()
    res = classifier.classify("Hello! Good morning, tutor.")
    assert res["category"] == "straightforward"


def test_classifier_simple():
    classifier = AdaptiveClassifier()
    res = classifier.classify("What is the rectified linear unit (ReLU) activation function?")
    assert res["category"] == "simple"


def test_classifier_complex():
    classifier = AdaptiveClassifier()
    res = classifier.classify("Compare Transformer self-attention with LSTM gating mechanisms in terms of computational complexity.")
    assert res["category"] == "complex"


def test_query_decomposer():
    decomposer = QueryDecomposer()
    subqueries = decomposer.decompose("Compare Convolutional Neural Networks vs Recurrent Neural Networks")
    assert len(subqueries) >= 2


def test_hallucination_verifier():
    verifier = HallucinationVerifier()
    docs = [{"text": "Convolutional networks use spatial filters and pooling layers for image classification."}]
    answer = "Convolutional networks apply spatial filters and pooling operations to classify images."
    res = verifier.verify(answer, docs)
    assert res["is_grounded"] is True
    assert res["score"] > 0.5

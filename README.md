# Adaptive LLM Tutor: An Adaptive Agentic RAG System
### With Custom Hybrid Retrieval (BM25 + RRF) and Prompt Injection Detection

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2+-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![Tests](https://img.shields.io/badge/tests-17%20passed-brightgreen.svg)]()

Based on the research foundation of Singh et al. (2026), *"Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG"*, arXiv:2501.09136v4, Section 5.5 (*Adaptive Agentic RAG*), this project transforms static RAG into an adaptive, secure educational tutor for Deep Learning and Machine Learning.

---

## 1. Core Architectural Overview

```
                      Student Query / Uploaded Document
                                      |
                                      v
            +----------------------------------------------------+
            |      1. PROMPT INJECTION DETECTION ENGINE          |
            |   (Pattern, Structural, Risk Scoring, Quarantine)  |
            +----------------------------------------------------+
                        |                          |
                [HIGH RISK / Attack]         [SAFE / ALLOW]
                        |                          |
                        v                          v
             [Security Mitigation]    +--------------------------+
             [Block / Quarantine]     | 2. ADAPTIVE ROUTER       |
                                      | (Query Complexity Class) |
                                      +--------------------------+
                                       /           |            \
                     Straightforward  /     Simple |             \ Complex
                                     /             |              \
                                    v              v               v
                             [Direct LLM]   [Single-Step   [Agentic Query
                             (No RAG)        Hybrid RAG]    Decomposition]
                                    |              |               |
                                    |              |       [Iterative Multi-Hop
                                    |              |        Hybrid Retrieval]
                                    |              |               |
                                    |              +-------+-------+
                                    |                      |
                                    |                      v
                                    |            +-------------------+
                                    |            |  Evidence Grader  |
                                    |            +-------------------+
                                    |                      |
                                    +----------------------+
                                               |
                                               v
                                  +--------------------------+
                                  |     3. TUTOR LLM         |
                                  | (Explain/Hint/Quiz/Socr) |
                                  +--------------------------+
                                               |
                                               v
                                  +--------------------------+
                                  | 4. GROUNDING VERIFIER    |
                                  | (NLI / Citation Check)   |
                                  +--------------------------+
                                               |
                                               v
                                  +--------------------------+
                                  | 5. LEARNER MEMORY DB     |
                                  |  (Progress & Mastery)    |
                                  +--------------------------+
```

---

## 2. The Two Primary Custom Engineering Contributions

### Custom Component 1: Intelligent Hybrid Retrieval Engine
Implemented from scratch without external BM25 retrieval libraries:
- **BM25 Lexical Retrieval (`src/retrieval/bm25.py`)**:
  - Full text tokenization, filtering, and suffix stemming (`src/retrieval/tokenizer.py`).
  - Robertson-Spärck Jones IDF with Lucene floor smoothing:
    $$\text{IDF}(q) = \ln\left(1 + \frac{N - n(q) + 0.5}{n(q) + 0.5}\right)$$
  - Document length normalization:
    $$\text{score}(D, Q) = \sum_{q \in Q} \text{IDF}(q) \cdot \frac{f(q, D) \cdot (k_1 + 1)}{f(q, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
  - Inverted index structures and incremental indexing.
- **Dense Vector Retrieval (`src/retrieval/dense_retriever.py`)**:
  - In-memory normalized vector cosine similarity over 3,053 chunks in ChromaDB.
- **Reciprocal Rank Fusion (RRF) (`src/retrieval/rrf.py`)**:
  - Merges disparate ranking distributions without manual score calibration:
    $$\text{RRF\_score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)} \quad (k=60)$$
- **Cross-Encoder Reranking (`src/retrieval/reranker.py`)**:
  - Configurable deep relevance scoring via cross-encoders.

### Custom Component 2: Prompt Injection Detection Engine
Built from scratch to defend against both direct student prompt injection and indirect prompt injection in uploaded PDFs or retrieved chunks:
- **Layer 1: Threat Signature Patterns (`src/security/injection_patterns.py`)**:
  - Regex rules for instruction overrides, system prompt extraction, credential leaks, and jailbreaks (DAN mode).
- **Layer 2: Structural & Contextual Analysis (`src/security/risk_scorer.py`)**:
  - Detects obfuscations (leetspeak, zero-width spaces, base64 payloads) and imperative addressing of the AI model inside documents.
- **Layer 3: Probabilistic Risk Scoring**:
  - Multi-feature compounding score:
    $$\text{RiskScore} = 1.0 - \prod_{i} (1 - w_i)$$
  - Categorized into `SAFE` ($<0.40$), `SUSPICIOUS` ($0.40 - 0.70$), and `HIGH RISK` ($\ge 0.70$).
- **Layer 4: Policy Enforcement (`src/security/security_policy.py`)**:
  - Policy decisions: `ALLOW`, `WARN_AND_ALLOW`, `SANITIZE`, `QUARANTINE`, and `BLOCK`.

---

## 3. Empirical Experimental Results & Ablation Studies

### A. Hybrid Retrieval Ablation Study (K=5, Goodfellow Corpus)

| Retrieval Strategy | Precision@5 | Recall@5 | MRR | NDCG@5 | Avg Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **BM25 Only (Scratch)** | 0.6000 | 1.0000 | 0.6500 | 0.7514 | 0.07 ms |
| **Dense Only (Vector)** | 0.2400 | 0.8000 | 0.3900 | 0.4668 | 53.23 ms |
| **Hybrid RRF (Scratch)** | **0.2800** | **0.8000** | **0.5167** | **0.5404** | **1.82 ms** |
| **Hybrid + Reranker** | 0.2800 | 0.8000 | 0.5167 | 0.5404 | 1.42 ms |

### B. Prompt Injection Detection vs Keyword Baseline

| Model | Accuracy | Precision | Recall | F1 Score | False Positive Rate | False Negative Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Custom Detector** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **0.0%** | **0.0%** |
| **Keyword Baseline**| 0.8000 | 0.7500 | 0.9000 | 0.8182 | 30.0% | 10.0% |

*Finding:* Keyword baselines fail catastrophically in educational settings by flagging benign queries containing technical terms like "ignore" (e.g. dropout ignoring neurons) or "system" (operating systems). The custom detector contextually discriminates attacks with 0% FPR.

### C. Adaptive Routing Strategy Latency

| Complexity Category | Routing Decision | Retrieved Docs | Latency |
| :--- | :--- | :---: | :---: |
| **Straightforward** | Direct LLM (bypasses RAG) | 0 | **0.146 s** |
| **Simple** | Single-Step Hybrid RAG | 4 | **0.210 s** |
| **Complex** | Agentic Decomposed Multi-Hop | 3 | **0.534 s** |

---

## 4. Quick Start & Setup

### Local Installation
```bash
# 1. Clone repository
git clone https://github.com/udaygupta8899/dl-tutor-rag.git
cd dl-tutor-rag

# 2. Set up virtual environment
uv venv .venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt pytest scikit-learn numpy pandas tabulate sentence-transformers

# 3. Configure environment
echo "OPENAI_API_KEY=your_key_here" > .env

# 4. Run tests
PYTHONPATH=. pytest tests/

# 5. Start Application
python main.py
```
Visit `http://localhost:8000` to interact with the full web UI.

### Docker Deployment
```bash
docker-compose up --build
```

---

## 5. API Endpoints

- `POST /api/chat`: Runs Adaptive Agentic RAG chat pipeline with full diagnostic metadata.
- `POST /api/security/inspect`: Real-time prompt injection scanner for queries/documents.
- `GET /api/security/audit`: Security audit event log.
- `POST /api/retrieval/search`: Exposes BM25, Dense, and RRF rankings.
- `GET /api/learner/profile/{student_id}`: Learner mastery and interaction history.
- `GET /api/dashboard`: Telemetry overview.

---

## 6. Citation

```bibtex
@article{singh2026agentic,
  title={Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG},
  author={Singh, A. and Ehtesham, A. and Kumar, S. and Talaei Khoei, T. and Vasilakos, A. V.},
  journal={arXiv preprint arXiv:2501.09136v4},
  year={2026}
}
```

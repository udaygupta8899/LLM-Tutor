"""
Ingestion script to parse and index course materials into ChromaDB and custom BM25 index:
- LLM Course PPTs
- Foundational Research Papers:
  * Vaswani et al. (2017) "Attention Is All You Need"
  * Lewis et al. (2020) "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
  * Asai et al. (2024) "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection"
  * Singh et al. (2026) "Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG"
- Ian Goodfellow Deep Learning Textbook
"""

import os
import glob
import pypdf
import uuid
import chromadb
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings
from src.retrieval.bm25 import BM25Retriever


def extract_and_chunk_pdf(pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Dict[str, Any]]:
    """Extracts text per page and splits into chunks with metadata."""
    reader = pypdf.PdfReader(pdf_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    basename = os.path.basename(pdf_path)
    category = "paper" if "papers" in pdf_path else ("ppt" if "ppts" in pdf_path else "book")
    
    chunks = []
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text or not text.strip():
            continue
        splits = splitter.split_text(text)
        for s_idx, split_text in enumerate(splits):
            chunk_id = f"{basename}_p{page_idx+1}_c{s_idx+1}"
            chunks.append({
                "id": chunk_id,
                "text": split_text,
                "metadata": {
                    "source": basename,
                    "category": category,
                    "page": page_idx + 1,
                    "total_pages": len(reader.pages)
                }
            })
    return chunks


def ingest_course_materials(collection_name: str = "llm-course-materials"):
    """Ingests course slides and research papers into dedicated Chroma collection with 384-d onnx MiniLM embeddings."""
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection(name=collection_name)
    
    targets = glob.glob("knowledge_base/papers/*.pdf") + glob.glob("knowledge_base/ppts/*.pdf")
    
    total_added = 0
    batch_ids = []
    batch_docs = []
    batch_metas = []
    
    for pdf_path in targets:
        print(f"Processing: {pdf_path}...")
        chunks = extract_and_chunk_pdf(pdf_path)
        print(f"  Extracted {len(chunks)} chunks.")
        
        for c in chunks:
            batch_ids.append(c["id"])
            batch_docs.append(c["text"])
            batch_metas.append(c["metadata"])
            
            if len(batch_ids) >= 100:
                collection.upsert(ids=batch_ids, documents=batch_docs, metadatas=batch_metas)
                total_added += len(batch_ids)
                batch_ids, batch_docs, batch_metas = [], [], []

    if batch_ids:
        collection.upsert(ids=batch_ids, documents=batch_docs, metadatas=batch_metas)
        total_added += len(batch_ids)

    print(f"Successfully ingested {total_added} new chunks from LLM papers and slides into collection '{collection_name}'.")
    print(f"Total collection count now: {collection.count()}")


if __name__ == "__main__":
    ingest_course_materials()

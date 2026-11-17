FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    pytest scikit-learn numpy pandas tabulate sentence-transformers

# Copy application source code and pre-indexed vector store
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY chroma_db/ ./chroma_db/
COPY main.py .

# Expose port (Render sets $PORT dynamically)
EXPOSE 8000

# Run FastAPI server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

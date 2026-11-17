#!/bin/bash
# Start script for LLM Tutor (FastAPI backend + Next.js frontend)

echo "Starting LLM Tutor backend on port 8000..."
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Next.js frontend on port 3000..."
cd nextjs_frontend
npm run dev &
FRONTEND_PID=$!

echo "LLM Tutor is running!"
echo "Backend & Dashboard: http://localhost:8000"
echo "Next.js App:         http://localhost:3000"

wait $BACKEND_PID $FRONTEND_PID

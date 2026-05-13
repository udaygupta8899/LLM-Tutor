from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from agent import app as langgraph_agent 

# Initialize FastAPI
api = FastAPI(
    title="Deep Learning Tutor API",
    description="Backend for the Agentic RAG LangGraph workflow",
    version="1.0.0"
)

# Configure CORS to explicitly allow your frontend domains
# In production, replace the localhost with your actual Netlify URL
ALLOWED_ORIGINS = [
    "http://localhost:3000",         # For local Next.js testing
    "https://dl-tutor.novaric.in",   # Your production domain
    "https://heroic-cobbler-7548b3.netlify.app"  # Netlify preview URL (if applicable)
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST"],          # Only allow POST requests for the chat
    allow_headers=["*"],
)

# Define the expected request payload using Pydantic
class ChatRequest(BaseModel):
    question: str
    thread_id: str

# Define the response payload
class ChatResponse(BaseModel):
    answer: str
    thread_id: str

@api.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Receives a question and thread_id, runs the LangGraph agent, 
    and returns the generated answer.
    """
    try:
        # Set up the configuration for the checkpointer (memory)
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Prepare the initial state for the graph
        inputs = {"question": request.question, "loop_step": 0}
        
        # Run the graph
        # Note: We use .stream() to execute the graph nodes sequentially
        final_state = None
        for output in langgraph_agent.stream(inputs, config=config):
            # We capture the last output from the graph
            final_state = output
            
        if not final_state:
             raise HTTPException(status_code=500, detail="Graph failed to execute.")
            
        # Extract the generation from the final node (usually 'generate' or the end state)
        node_name = list(final_state.keys())[0]
        generated_answer = final_state[node_name].get("generation", "I am sorry, I couldn't generate an answer.")
        
        return ChatResponse(
            answer=generated_answer,
            thread_id=request.thread_id
        )

    except Exception as e:
        # Log the error on the server and return a clean error to the frontend
        print(f"Error during graph execution: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request.")

@api.get("/health")
async def health_check():
    """Simple endpoint to verify the server is running."""
    return {"status": "healthy"}
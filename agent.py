import os
from typing import List, TypedDict
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import requests
from dotenv import load_dotenv
load_dotenv()

# Set your API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def download_default_pdf(raw_url: str, save_path: str):
    """Downloads the default PDF if it doesn't already exist locally."""
    if not os.path.exists(save_path):
        print(f"Downloading textbook from GitHub... This might take a moment.")
        response = requests.get(raw_url)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print("Download complete!")
    else:
        print("Default textbook already exists locally. Skipping download.")

def ingest_pdf(file_path: str):
    """Loads a PDF and splits it into chunks."""
    print(f"Loading and splitting: {file_path}")
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    # Using a slightly larger chunk size for a textbook to capture full paragraphs
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return text_splitter.split_documents(docs)

# 1. Define the raw GitHub URL and local filename
GITHUB_RAW_URL = "https://raw.githubusercontent.com/janishar/mit-deep-learning-book-pdf/master/complete-book-pdf/Ian%20Goodfellow%2C%20Yoshua%20Bengio%2C%20Aaron%20Courville%20-%20Deep%20Learning%20(2017%2C%20MIT).pdf"
DEFAULT_PDF_FILENAME = "goodfellow_deep_learning.pdf"

# 2. Download the book
download_default_pdf(GITHUB_RAW_URL, DEFAULT_PDF_FILENAME)

# 3. Initialize Chroma DB with persistent storage
persist_dir = "./chroma_db"
vectorstore = Chroma(
    collection_name="dl-tutor-chroma",
    embedding_function=OpenAIEmbeddings(),
    persist_directory=persist_dir
)

# 4. Ingest and embed the book
if vectorstore._collection.count() == 0:
    print("Database is empty. Processing documents for the vector store...")
    
    # Check if the PDF is downloaded, if not download it
    download_default_pdf(GITHUB_RAW_URL, DEFAULT_PDF_FILENAME)
    
    # Ingest and embed the book
    default_docs = ingest_pdf(DEFAULT_PDF_FILENAME)
    vectorstore.add_documents(default_docs)
    print(f"Successfully added {len(default_docs)} chunks to the knowledge base.")
else:
    chunk_count = vectorstore._collection.count()
    print(f"Database found! Loaded {chunk_count} existing chunks from {persist_dir}.")
    print("Skipping PDF download and ingestion.")

# 5. Set up the retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

class GraphState(TypedDict):
    question: str
    generation: str
    documents: List[str]
    loop_step: int
    chat_history: List[str]
    relevance: str

def check_relevance(state):
    """Check if the user's question is related to Deep Learning, or is a greeting/pleasantry."""
    print("---CHECKING QUERY RELEVANCE---")
    question = state["question"]
    
    prompt = ChatPromptTemplate.from_template(
        "You are a relevance classifier. Classify the following user message into exactly one of three categories.\n\n"
        "User message: {question}\n\n"
        "Categories:\n"
        "- 'greeting' — if the message is a greeting, pleasantry, farewell, or expression of gratitude "
        "(e.g., hi, hello, hey, thanks, thank you, bye, goodbye, good morning, how are you).\n"
        "- 'yes' — if the message is a question or topic related to Deep Learning, Machine Learning, "
        "Artificial Intelligence, Neural Networks, or closely related mathematical/computational concepts "
        "(e.g., linear algebra for neural networks, optimization, probability for ML).\n"
        "- 'no' — if the message is about something clearly unrelated like cooking, sports, politics, "
        "entertainment, or any other off-topic subject.\n\n"
        "Answer with ONLY one word: 'greeting', 'yes', or 'no'. Nothing else."
    )
    
    chain = prompt | llm | StrOutputParser()
    score = chain.invoke({"question": question})
    
    return {"question": question, "relevance": score.strip().lower()}

def route_on_relevance(state):
    """Route based on whether the query is relevant to Deep Learning, a greeting, or unrelated."""
    relevance = state.get("relevance", "no")
    if "greeting" in relevance:
        print("---DECISION: GREETING DETECTED, RESPONDING WARMLY---")
        return "greeting"
    elif "yes" in relevance:
        print("---DECISION: QUERY IS RELEVANT, PROCEEDING TO RETRIEVAL---")
        return "relevant"
    else:
        print("---DECISION: QUERY IS NOT RELATED TO DEEP LEARNING---")
        return "not_relevant"

def greet(state):
    """Return a friendly greeting for pleasantries like hi, hello, thanks, etc."""
    print("---GREETING USER---")
    question = state["question"]
    chat_history = state.get("chat_history", [])
    
    prompt = ChatPromptTemplate.from_template(
        "You are a friendly Deep Learning tutor. The student has sent you a greeting or pleasantry.\n"
        "Respond warmly and briefly, and remind them that you're here to help with Deep Learning questions.\n"
        "Keep it to 1-2 sentences. Be friendly and encouraging.\n\n"
        "Student's message: {question}\n"
        "Your response:"
    )
    
    chain = prompt | llm | StrOutputParser()
    greeting_response = chain.invoke({"question": question})
    
    updated_history = chat_history.copy()
    updated_history.append(f"User: {question}")
    updated_history.append(f"Tutor: {greeting_response}")
    
    return {
        "documents": [],
        "question": question,
        "generation": greeting_response,
        "chat_history": updated_history,
        "loop_step": 0
    }

def reject(state):
    """Return a rejection message for unrelated queries."""
    print("---REJECTING UNRELATED QUERY---")
    question = state["question"]
    chat_history = state.get("chat_history", [])
    
    rejection_msg = (
        "I'm sorry, but your question doesn't appear to be related to Deep Learning. "
        "I'm a Deep Learning tutor and can only assist with questions about Deep Learning, "
        "Neural Networks, Machine Learning, and related concepts from the textbook. "
        "Please ask a question related to Deep Learning!"
    )
    
    updated_history = chat_history.copy()
    updated_history.append(f"User: {question}")
    updated_history.append(f"Tutor: {rejection_msg}")
    
    return {
        "documents": [],
        "question": question,
        "generation": rejection_msg,
        "chat_history": updated_history,
        "loop_step": 0
    }

def retrieve(state):
    print("---RETRIEVING DOCUMENTS---")
    question = state["question"]
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}

def grade_documents(state):
    print("---GRADING DOCUMENT RELEVANCE---")
    question = state["question"]
    documents = state["documents"]
    
    # Prompt for the LLM to act as a grader
    prompt = ChatPromptTemplate.from_template(
        "You are a grader assessing relevance of a retrieved document to a user question.\n"
        "Here is the retrieved document: \n\n {document} \n\n"
        "Here is the user question: {question}\n"
        "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.\n"
        "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."
    )
    
    grader_chain = prompt | llm | StrOutputParser()
    
    filtered_docs = []
    for d in documents:
        score = grader_chain.invoke({"question": question, "document": d.page_content})
        if "yes" in score.lower():
            filtered_docs.append(d)
            
    return {"documents": filtered_docs, "question": question}

def generate(state):
    print("---GENERATING ANSWER---")
    question = state["question"]
    documents = state["documents"]
    chat_history = state.get("chat_history", [])
    
    context = "\n\n".join([d.page_content for d in documents])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert Deep Learning tutor. Your role is to help students understand Deep Learning concepts "
         "using ONLY the provided context from the textbook.\n\n"
         "Rules:\n"
         "1. Answer the student's question based strictly on the provided context.\n"
         "2. If the context does not contain enough information to answer, say: "
         "'I don't have enough information in the textbook to answer that specific question.'\n"
         "3. If the question is not related to Deep Learning at all, say: "
         "'Your question is not related to Deep Learning. I can only assist with Deep Learning concepts.'\n"
         "4. Be clear, concise, and educational in your explanations."),
        ("human",
         "Context from textbook:\n{context}\n\n"
         "Student's question: {question}")
    ])
    
    rag_chain = prompt | llm | StrOutputParser()
    generation = rag_chain.invoke({"context": context, "question": question})
    
    # Save the interaction to memory
    updated_history = chat_history.copy()
    updated_history.append(f"User: {question}")
    updated_history.append(f"Tutor: {generation}")
    
    return {
        "documents": documents, 
        "question": question, 
        "generation": generation,
        "chat_history": updated_history,
        "loop_step": state.get("loop_step", 0)
    }

def rewrite_query(state):
    print("---REWRITING QUERY (WITH MEMORY)---")
    question = state["question"]
    chat_history = state.get("chat_history", [])
    loop_step = state.get("loop_step", 0)
    
    # Format the history into a single string for the prompt
    history_str = "\n".join(chat_history) if chat_history else "No previous conversation."
    
    prompt = ChatPromptTemplate.from_template(
        "You are a search query refinement assistant for a Deep Learning textbook retrieval system.\n\n"
        "Your job is VERY limited:\n"
        "1. Fix any grammatical or spelling errors in the user's question.\n"
        "2. If the question uses a pronoun or reference (like 'it', 'that', 'this') that refers to something "
        "from the conversation history, resolve it to be explicit.\n"
        "3. Do NOT change the meaning or intent of the question.\n"
        "4. Do NOT add Deep Learning terminology that the user did not use.\n"
        "5. Do NOT transform or reframe the question into a different question.\n"
        "6. Keep the question as close to the original as possible.\n\n"
        "Conversation History:\n{history}\n\n"
        "User's question: {question}\n"
        "Corrected question:"
    )
    
    rewriter_chain = prompt | llm | StrOutputParser()
    rewritten_question = rewriter_chain.invoke({"history": history_str, "question": question})
    
    return {"question": rewritten_question, "loop_step": loop_step + 1}

def check_hallucination(state):
    """
    Evaluates whether the generated answer is grounded in the retrieved documents.
    """
    print("---CHECKING FOR HALLUCINATIONS---")
    documents = state["documents"]
    generation = state["generation"]
    
    # Combine documents for context
    context = "\n\n".join([d.page_content for d in documents])
    
    prompt = ChatPromptTemplate.from_template(
        "You are a grader assessing whether an answer is grounded in a set of facts.\n"
        "Facts: {context}\n"
        "Answer: {generation}\n"
        "Does the answer contradict the facts? (yes/no)\n"
        "Is the core technical explanation supported by the facts? (yes/no)\n"
        "If the answer is factually consistent with the context, even if it uses better phrasing, score it 'yes'."
    )
    
    hallucination_chain = prompt | llm | StrOutputParser()
    score = hallucination_chain.invoke({"context": context, "generation": generation})
    
    if "yes" in score.lower():
        print("---DECISION: ANSWER IS GROUNDED (NO HALLUCINATION)---")
        return "grounded"
    else:
        print("---DECISION: HALLUCINATION DETECTED---")
        return "hallucinated"
    
def decide_to_generate(state):
    filtered_documents = state["documents"]
    loop_step = state.get("loop_step", 0)
    max_retries = 3 # Stop trying after 3 attempts
    
    if not filtered_documents:
        if loop_step >= max_retries:
            print(f"---DECISION: MAX RETRIES ({max_retries}) REACHED. FORCING GENERATION---")
            # We break the loop and send it to generate with empty documents
            return "generate"
        else:
            print(f"---DECISION: NO RELEVANT DOCUMENTS, REWRITING QUERY (Attempt {loop_step + 1}/{max_retries})---")
            return "rewrite_query"
    else:
        print("---DECISION: RELEVANT DOCUMENTS FOUND, GENERATING---")
        return "generate"

def decide_if_grounded(state):
    status = check_hallucination(state)
    loop_step = state.get("loop_step", 0)
    max_retries = 3
    
    if status == "grounded":
        return "useful"
    elif loop_step >= max_retries:
        print("---MAX RETRIES REACHED. RETURNING FALLBACK ANSWER---")
        return "max_retries"
    else:
        return "not_supported"

# Checkpointer
memory = MemorySaver()

# Build the graph
workflow = StateGraph(GraphState)

# Add all nodes
workflow.add_node("check_relevance", check_relevance)
workflow.add_node("greet", greet)
workflow.add_node("reject", reject)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("rewrite_query", rewrite_query)

# Entry point: check relevance first
workflow.set_entry_point("check_relevance")

# Route based on relevance
workflow.add_conditional_edges(
    "check_relevance",
    route_on_relevance,
    {
        "greeting": "greet",           # Greeting → respond warmly
        "relevant": "retrieve",        # DL-related → proceed to RAG
        "not_relevant": "reject",      # Unrelated → reject immediately
    },
)

# Greet and reject both end the graph
workflow.add_edge("greet", END)
workflow.add_edge("reject", END)

# Standard edges
workflow.add_edge("retrieve", "grade_documents")
workflow.add_edge("rewrite_query", "retrieve")

# Conditional routing after document grading
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "rewrite_query": "rewrite_query",
        "generate": "generate",
    },
)

# Conditional routing after generation (hallucination check)
workflow.add_conditional_edges(
    "generate",
    decide_if_grounded,
    {
        "useful": END,               # Answer is good, end the graph
        "not_supported": "rewrite_query", # Hallucinated! Go get different context
        "max_retries": END           # Stop infinite loops
    }
)

# Compile
app = workflow.compile(checkpointer=memory)
"""
Main FastAPI application entry point.
Run with: uvicorn main:app --reload
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger = logging.getLogger(__name__)
    logger.info(f"✓ Loaded environment variables from {env_path}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Document Intelligence Workspace API",
    description="API for document processing, classification, and retrieval with RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG engine
logger.info("Initializing RAG engine...")
rag_engine = None

try:
    logger.info("Step 1: Creating embedding model...")
    from embedding.model import create_embedding_model
    embedder = create_embedding_model()
    logger.info("✓ Embedding model created")
    
    logger.info("Step 2: Creating vector database...")
    from storage.vector_db import FaissVectorDatabase
    vector_db = FaissVectorDatabase(dimension=embedder.dimension)
    logger.info("✓ Vector database created")
    
    logger.info("Step 3: Creating LLM...")
    import os
    
    # Try Ollama first (local, no internet needed)
    try:
        from llm.ollama_model import OllamaLLM
        llm = OllamaLLM(model="llama2")
        if llm.available:
            logger.info("✓ Using Ollama LLM (Local, FREE, No Internet Needed)")
        else:
            raise Exception("Ollama not available")
    except Exception as e:
        # Fallback to HuggingFace
        logger.warning(f"Ollama not available: {e}")
        logger.info("Falling back to HuggingFace API...")
        
        from llm.serverless_model import HuggingFaceInferenceAPI
        hf_token = os.getenv("HUGGINGFACE_API_KEY")
        
        if not hf_token:
            logger.warning("⚠️  HUGGINGFACE_API_KEY not set!")
            logger.warning("Get free token: https://huggingface.co/settings/tokens")
            logger.info("OR install Ollama (local, no internet): https://ollama.ai")
        
        llm = HuggingFaceInferenceAPI(
            model_name="mistralai/Mistral-7B-Instruct-v0.2",
            api_key=hf_token
        )
        logger.info("✓ Using HuggingFace LLM (Requires Internet)")
    
    logger.info("Step 4: Creating RAG engine...")
    from rag.engine import RAGEngine
    rag_engine = RAGEngine(
        embedder=embedder,
        vector_db=vector_db,
        llm=llm,
        top_k=5,
        search_type="hybrid"
    )
    logger.info("✓ RAG engine initialized successfully")
    
except ImportError as e:
    logger.error(f"Import error while initializing RAG engine: {e}")
    logger.warning("Some modules may be missing. Install with: pip install -r requirements.txt")
    logger.info("Starting API in limited mode - /health endpoint will work")
    
except Exception as e:
    logger.error(f"Failed to initialize RAG engine: {e}")
    logger.warning("Starting API without RAG engine - limited functionality")
    import traceback
    logger.debug(traceback.format_exc())

# Register routes
if rag_engine:
    try:
        logger.info("Registering API routes...")
        from routes.routes import RAGAPIRouter
        router = RAGAPIRouter(app, rag_engine)
        logger.info("✓ API routes registered successfully")
    except ImportError as e:
        logger.error(f"Import error while registering routes: {e}")
        logger.warning("Some dependencies may be missing")
        logger.info("Routes will work with limited functionality")
    except Exception as e:
        logger.error(f"Failed to register routes: {e}")
        logger.warning("API will only have basic endpoints")
        import traceback
        logger.debug(traceback.format_exc())
else:
    logger.warning("RAG engine not available - registering minimal endpoints only")

# Always available endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Document Intelligence Workspace API",
        "version": "1.0.0",
        "status": "operational" if rag_engine else "limited",
        "rag_engine": "ready" if rag_engine else "not initialized",
        "docs": "/docs",
        "health": "/health",
        "message": "API is running" if rag_engine else "API is running in limited mode - RAG engine not initialized"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint - always available."""
    doc_count = 0
    if rag_engine:
        try:
            # Try to get document count if method exists
            if hasattr(rag_engine, 'count_documents'):
                doc_count = rag_engine.count_documents()
            elif hasattr(rag_engine, 'vector_db') and hasattr(rag_engine.vector_db, 'count'):
                doc_count = rag_engine.vector_db.count()
        except:
            doc_count = 0
    
    return {
        "status": "healthy" if rag_engine else "degraded",
        "version": "1.0.0",
        "rag_engine": "initialized" if rag_engine else "not initialized",
        "document_count": doc_count,
        "message": "System is operational" if rag_engine else "RAG engine not initialized - install dependencies and restart"
    }

@app.get("/status")
async def status():
    """Detailed status endpoint."""
    return {
        "api": "running",
        "version": "1.0.0",
        "components": {
            "rag_engine": "ready" if rag_engine else "not initialized",
            "vector_db": "ready" if rag_engine and hasattr(rag_engine, 'vector_db') else "not initialized",
            "llm": "ready" if rag_engine and hasattr(rag_engine, 'llm') else "not initialized",
            "embedder": "ready" if rag_engine and hasattr(rag_engine, 'embedder') else "not initialized",
        },
        "endpoints": {
            "root": "/",
            "health": "/health",
            "docs": "/docs",
            "upload": "/upload" if rag_engine else "unavailable",
            "query": "/query" if rag_engine else "unavailable",
            "search": "/search" if rag_engine else "unavailable"
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

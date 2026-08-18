"""
Main FastAPI application entry point.
Run with: uvicorn main:app --reload
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
try:
    from rag.engine import RAGEngine
    from config import get_model_config
    
    config = get_model_config()
    rag_engine = RAGEngine(
        use_serverless=config.get("use_serverless", False)
    )
    logger.info("✓ RAG engine initialized")
except Exception as e:
    logger.error(f"Failed to initialize RAG engine: {e}")
    logger.warning("Starting API without RAG engine - limited functionality")
    rag_engine = None

# Register routes
if rag_engine:
    from routes.routes import RAGAPIRouter
    router = RAGAPIRouter(app, rag_engine)
    logger.info("✓ API routes registered")
else:
    # Minimal health check if RAG engine fails
    @app.get("/health")
    async def health_check():
        return {
            "status": "degraded",
            "version": "1.0.0",
            "message": "RAG engine not initialized"
        }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Document Intelligence Workspace API",
        "version": "1.0.0",
        "status": "operational" if rag_engine else "degraded",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

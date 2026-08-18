"""
FastAPI routes for the RAG system API.
"""

import logging
import uuid
import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, File, UploadFile
from pydantic import BaseModel, Field
import tempfile
import os
import time
from PIL import Image

# Configure logging
logger = logging.getLogger(__name__)

# Optional Firebase import
try:
    from storage.firebase_client import get_db, get_bucket
    FIREBASE_AVAILABLE = True
    logger.info("Firebase client available")
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("Firebase not available - some features will be limited")

from document.ocr_processor import extract_text_from_image
from document.document_classifier import DocumentClassifier
from document.field_extractor import FieldExtractor


# Define Pydantic models for API requests and responses
class DocumentInput(BaseModel):
    """Input model for adding a document."""
    title: str
    text: str
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentsInput(BaseModel):
    """Input model for adding multiple documents."""
    documents: List[DocumentInput]


class QueryInput(BaseModel):
    """Input model for querying the RAG system."""
    query: str
    top_k: int = 5
    search_type: str = "hybrid"
    filter_dict: Optional[Dict[str, Any]] = None
    max_tokens: int = 512


class SearchResult(BaseModel):
    """Model for search results."""
    id: str
    text: str
    metadata: Dict[str, Any]
    score: float


class RAGResponse(BaseModel):
    """Model for RAG system responses."""
    query: str
    response: str
    retrieved_documents: List[SearchResult]
    search_type: str
    evidence: List[Dict[str, Any]] = []


class HealthResponse(BaseModel):
    """Model for system health check responses."""
    status: str
    version: str
    document_count: int
    message: Optional[str] = None


# Class to define API routes
class RAGAPIRouter:
    """FastAPI router for the RAG system API."""

    def __init__(self, app: FastAPI, rag_engine):
        """
        Initialize the API router.

        Args:
            app: FastAPI application
            rag_engine: RAG engine instance
        """
        self.app = app
        self.rag_engine = rag_engine

        # Classifier and field extractor are initialized once here, not
        # per-request — the classifier precomputes class embeddings at
        # init, and the extractor reuses the RAG engine's existing LLM
        # dispatch, so neither needs to be rebuilt on every upload.
        from embedding.model import create_embedding_model
        self.classifier = DocumentClassifier(create_embedding_model())
        self.extractor = FieldExtractor(self.rag_engine)

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all API routes."""

        @self.app.post("/documents", response_model=Dict[str, Any], summary="Add documents to the system")
        async def add_documents(documents: DocumentsInput):
            """
            Add documents to the search index.

            - **documents**: List of documents with text and metadata

            Returns:
                Status and number of documents added
            """
            try:
                # Extract text and metadata
                texts = [doc.text for doc in documents.documents]
                metadata = [
                    {
                        **doc.metadata,
                        "title": doc.title,
                        "source": doc.source or "API upload"
                    }
                    for doc in documents.documents
                ]

                # Add to RAG engine
                doc_ids = self.rag_engine.add_documents(texts, metadata)

                return {
                    "status": "success",
                    "message": f"Added {len(doc_ids)} documents",
                    "document_ids": doc_ids
                }
            except Exception as e:
                logger.error(f"Error adding documents: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to add documents: {str(e)}")

        @self.app.post("/upload", response_model=Dict[str, Any], summary="Upload and process document files")
        async def upload_document(
            file: UploadFile = File(...),
            chunk_size: int = Query(1000, ge=100, le=5000),
            chunk_overlap: int = Query(200, ge=0, le=500)
        ):
            """
            Upload and process a document file.

            - **file**: Document file to upload (PDF, TXT, DOCX, JPG, PNG, etc.)
            - **chunk_size**: Size of text chunks
            - **chunk_overlap**: Overlap between chunks

            Returns:
                Status and number of chunks extracted
            """
            doc_id = str(uuid.uuid4())
            
            # Use Firebase if available, otherwise work in-memory
            if FIREBASE_AVAILABLE:
                try:
                    db = get_db()
                    doc_ref = db.collection("documents").document(doc_id)
                except:
                    logger.warning("Firebase connection failed, continuing without it")
                    db = None
                    doc_ref = None
            else:
                db = None
                doc_ref = None

            try:
                # Import here to avoid circular imports
                from document.processor import DocumentProcessor

                start_time = time.time()
                content = await file.read()
                ext = os.path.splitext(file.filename)[1].lower()

                # Create the Firestore record if Firebase available
                if doc_ref:
                    try:
                        doc_ref.set({
                            "filename": file.filename,
                            "status": "UPLOADED",
                            "upload_time": datetime.datetime.utcnow(),
                            "document_id": doc_id,
                        })
                    except:
                        logger.warning("Could not write to Firebase, continuing")

                # Store in Firebase Storage if available
                if FIREBASE_AVAILABLE and doc_ref:
                    try:
                        bucket = get_bucket()
                        blob = bucket.blob(f"originals/{doc_id}{ext}")
                        blob.upload_from_string(content)
                        doc_ref.update({"storage_path": blob.name, "status": "PROCESSING"})
                    except:
                        logger.warning("Could not store in Firebase Storage, continuing")

                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name

                try:
                    # --- P1: OCR branch for images, existing processor for the rest ---
                    if ext in (".jpg", ".jpeg", ".png"):
                        if doc_ref:
                            try:
                                doc_ref.update({"status": "OCR"})
                            except:
                                pass
                        image = Image.open(temp_path)
                        text, ocr_confidence = extract_text_from_image(image)

                        if not text.strip():
                            if doc_ref:
                                try:
                                    doc_ref.update({"status": "FAILED", "error": "No text extracted via OCR"})
                                except:
                                    pass
                            return {
                                "status": "warning",
                                "message": "No text extracted from image"
                            }

                        chunks = [text]
                        chunk_metadata = [{
                            "filename": file.filename,
                            "source": file.filename,
                            "ocr_confidence": ocr_confidence,
                        }]
                        if doc_ref:
                            try:
                                doc_ref.update({"ocr_confidence": ocr_confidence})
                            except:
                                pass
                    else:
                        if doc_ref:
                            try:
                                doc_ref.update({"status": "EXTRACTING"})
                            except:
                                pass
                        processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                        chunks, chunk_metadata = processor.process_file(
                            temp_path,
                            metadata={"filename": file.filename, "source": file.filename}
                        )

                    if not chunks:
                        if doc_ref:
                            try:
                                doc_ref.update({"status": "FAILED", "error": "No text extracted from document"})
                            except:
                                pass
                        return {
                            "status": "warning",
                            "message": "No text extracted from document"
                        }

                    full_text = " ".join(chunks)

                    # --- P2: classification ---
                    if doc_ref:
                        try:
                            doc_ref.update({"status": "CLASSIFYING"})
                        except:
                            pass
                    doc_type, classification_confidence = self.classifier.classify(full_text)
                    if doc_ref:
                        try:
                            doc_ref.update({
                                "document_type": doc_type,
                                "classification_confidence": classification_confidence,
                            })
                        except:
                            pass

                    # --- P3: structured field extraction ---
                    if doc_ref:
                        try:
                            doc_ref.update({"status": "EXTRACTING_FIELDS"})
                        except:
                            pass
                    extracted_fields = self.extractor.extract(chunks, chunk_metadata, doc_type, file.filename)
                    if doc_ref:
                        try:
                            doc_ref.update({"extracted_fields": extracted_fields})
                        except:
                            pass

                    # Stamp every chunk with real identifiers
                    for m in chunk_metadata:
                        m["document_id"] = doc_id
                        m["document_type"] = doc_type
                        m["source"] = file.filename

                    # Add chunks to RAG engine
                    if doc_ref:
                        try:
                            doc_ref.update({"status": "INDEXING"})
                        except:
                            pass
                    doc_ids = self.rag_engine.add_documents(chunks, chunk_metadata)

                    if doc_ref:
                        try:
                            doc_ref.update({
                                "status": "COMPLETED",
                                "chunk_count": len(chunks),
                                "chunk_ids": doc_ids,
                            })
                        except:
                            pass

                    return {
                        "status": "success",
                        "message": f"Processed document into {len(chunks)} chunks",
                        "document_id": doc_id,
                        "document_type": doc_type,
                        "classification_confidence": float(classification_confidence),
                        "extracted_fields": extracted_fields,
                        "chunk_count": len(chunks),
                        "document_ids": doc_ids,
                        "processing_time_seconds": round(time.time() - start_time, 2),
                        "firebase_enabled": FIREBASE_AVAILABLE
                    }
                finally:
                    # Clean up temporary file
                    os.unlink(temp_path)
            except Exception as e:
                logger.error(f"Error processing document: {e}")
                if doc_ref:
                    try:
                        doc_ref.update({"status": "FAILED", "error": str(e)})
                    except:
                        pass
                raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

        @self.app.get("/documents/{document_id}/status", summary="Get document processing status")
        async def get_document_status(document_id: str):
            """
            Get the live processing status of a document from Firestore.

            - **document_id**: The document's UUID returned by /upload

            Returns:
                The document's current Firestore record
            """
            if not FIREBASE_AVAILABLE:
                return {
                    "status": "error",
                    "message": "Firebase not available - status tracking disabled",
                    "document_id": document_id
                }
            
            try:
                db = get_db()
                doc = db.collection("documents").document(document_id).get()
                if not doc.exists:
                    raise HTTPException(status_code=404, detail="Document not found")
                return doc.to_dict()
            except Exception as e:
                logger.error(f"Error fetching document status: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to fetch status: {str(e)}")

        @self.app.post("/query", response_model=RAGResponse, summary="Query the RAG system")
        async def query(query_input: QueryInput):
            """
            Generate a response for the query using the RAG system.

            - **query**: Query text
            - **top_k**: Number of documents to retrieve
            - **search_type**: Type of search ('semantic', 'keyword', 'hybrid')
            - **filter_dict**: Optional metadata filters
            - **max_tokens**: Maximum tokens in response

            Returns:
                RAG response with answer and retrieved documents
            """
            try:
                # Query RAG engine
                result = self.rag_engine.generate_response(
                    query=query_input.query,
                    top_k=query_input.top_k,
                    search_type=query_input.search_type,
                    filter_dict=query_input.filter_dict,
                    max_tokens=query_input.max_tokens
                )

                # Convert to response model
                return RAGResponse(
                    query=result["query"],
                    response=result["response"],
                    retrieved_documents=[...],  # unchanged
                    search_type=result["search_type"],
                    evidence=[
                        {
                            "source_document": doc["metadata"].get("source", "Unknown"),
                            "page": doc["metadata"].get("page", "unknown"),
                            "evidence_snippet": doc["text"][:200],
                            "confidence": round(doc["score"], 3),
                        }
                        for doc in result["retrieved_documents"]
                    ]
                )
            except Exception as e:
                logger.error(f"Error querying RAG system: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to query system: {str(e)}")

        @self.app.get("/search", summary="Search for documents without generating a response")
        async def search(
            query: str,
            top_k: int = Query(5, ge=1, le=20),
            search_type: str = Query("hybrid", regex="^(semantic|keyword|hybrid)$")
        ):
            """
            Search for documents without generating a response.

            - **query**: Search query
            - **top_k**: Number of results to return
            - **search_type**: Type of search

            Returns:
                Search results
            """
            try:
                # Search for documents
                results = self.rag_engine.search(
                    query=query,
                    top_k=top_k,
                    search_type=search_type
                )

                return {
                    "query": query,
                    "results": results,
                    "search_type": search_type,
                    "count": len(results)
                }
            except Exception as e:
                logger.error(f"Error searching documents: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")

        @self.app.delete("/documents", summary="Clear all documents from the system")
        async def clear_documents():
            """
            Clear all documents from the system.

            Returns:
                Status message
            """
            try:
                # Clear documents
                self.rag_engine.clear_documents()

                return {
                    "status": "success",
                    "message": "All documents cleared from the system"
                }
            except Exception as e:
                logger.error(f"Error clearing documents: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to clear documents: {str(e)}")

        @self.app.get("/health", response_model=HealthResponse, summary="Check system health")
        async def health_check():
            """
            Check if the system is healthy.

            Returns:
                System health status
            """
            try:
                # Get document count
                doc_count = self.rag_engine.count_documents()

                return HealthResponse(
                    status="healthy",
                    version="1.0.0",
                    document_count=doc_count,
                    message="System is operational"
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return HealthResponse(
                    status="unhealthy",
                    version="1.0.0",
                    document_count=0,
                    message=f"System error: {str(e)}"
                )
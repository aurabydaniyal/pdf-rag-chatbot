"""
FastAPI Backend for PDF RAG Chatbot
Handles HTTP requests from React Native mobile app
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import shutil
from typing import Optional, List
import logging

# Import custom modules
from ingest import PDFIngestor
from rag import RAGProcessor
from utils import validate_pdf, generate_document_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="PDF RAG Chatbot API",
    description="Local RAG chatbot for PDF documents",
    version="1.0.0"
)

# Configure CORS for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
try:
    ingestor = PDFIngestor()
    rag_processor = RAGProcessor()
    logger.info("✅ Core components initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize components: {str(e)}")
    raise

# ------------------- Request/Response Models -------------------

class QueryRequest(BaseModel):
    """Model for question-asking request"""
    query: str
    top_k: Optional[int] = 3
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What is Kubernetes?",
                "top_k": 3
            }
        }

class QueryResponse(BaseModel):
    """Model for question-answering response"""
    answer: str
    sources: List[dict]
    chunks_used: int
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "Kubernetes is a container orchestration platform...",
                "sources": [
                    {"document": "kubernetes_notes.pdf", "chunk_index": 0, "distance": 0.12}
                ],
                "chunks_used": 3
            }
        }

class UploadResponse(BaseModel):
    """Model for PDF upload response"""
    success: bool
    message: str
    document_name: str
    total_chunks: int

# ------------------- Endpoints -------------------

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "PDF RAG Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify service status"""
    try:
        # Check if Ollama is responsive
        ollama_status = rag_processor.check_ollama_status()
        
        return {
            "status": "healthy",
            "ollama_connected": ollama_status,
            "model_loaded": rag_processor.model_name if ollama_status else None
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/upload-pdf", 
          response_model=UploadResponse,
          tags=["Documents"],
          summary="Upload and index a PDF")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file, extract text, create embeddings, and store in ChromaDB
    
    - **file**: PDF file (multipart/form-data)
    - Returns: Document name and number of chunks created
    """
    try:
        # Step 1: Validate file
        validate_pdf(file)
        logger.info(f"📄 Processing PDF: {file.filename}")
        
        # Step 2: Save file temporarily
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        doc_id = generate_document_id(file.filename)
        safe_filename = f"{doc_id}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"💾 File saved: {file_path}")
        
        # Step 3: Ingest PDF to vector database
        result = ingestor.ingest_pdf(file_path, file.filename)
        
        # Step 4: Clean up temporary file
        os.remove(file_path)
        logger.info(f"🧹 Temporary file cleaned up")
        
        return {
            "success": True,
            "message": f"PDF '{file.filename}' indexed successfully",
            "document_name": file.filename,
            "total_chunks": result["total_chunks"]
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/ask", 
          response_model=QueryResponse,
          tags=["Questions"],
          summary="Ask a question about uploaded documents")
async def ask_question(request: QueryRequest):
    """
    Ask a question and get answer from PDF documents
    
    - **query**: Question text
    - **top_k**: Number of relevant chunks to retrieve (default: 3)
    - Returns: Answer with source citations
    """
    try:
        logger.info(f"❓ Question asked: {request.query[:100]}...")
        
        # Step 1: Search for relevant chunks
        search_results = ingestor.search(request.query, request.top_k)
        
        # Step 2: Check if any results found
        if not search_results['documents'] or not search_results['documents'][0]:
            return {
                "answer": "I couldn't find any relevant information about that in the uploaded documents. Please try rephrasing your question.",
                "sources": [],
                "chunks_used": 0
            }
        
        # Step 3: Process query with RAG
        result = rag_processor.process_query(request.query, search_results)
        
        logger.info(f"✅ Answer generated using {result['chunks_used']} chunks")
        return result
        
    except Exception as e:
        logger.error(f"Question processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/documents", tags=["Documents"])
async def list_documents():
    """
    List all indexed documents
    
    - Returns: List of document names and total count
    """
    try:
        # Get all documents from ChromaDB
        all_data = ingestor.collection.get()
        documents = set()
        
        # Extract unique document names from metadata
        for metadata in all_data.get('metadatas', []):
            if metadata and 'document' in metadata:
                documents.add(metadata['document'])
        
        return {
            "documents": sorted(list(documents)),
            "total_documents": len(documents)
        }
    except Exception as e:
        logger.error(f"List documents error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/documents/{document_name}", tags=["Documents"])
async def delete_document(document_name: str):
    """
    Delete a specific document from the vector database
    """
    try:
        # Get all data
        all_data = ingestor.collection.get()
        
        # Find IDs to delete
        ids_to_delete = []
        for i, metadata in enumerate(all_data.get('metadatas', [])):
            if metadata and metadata.get('document') == document_name:
                ids_to_delete.append(all_data['ids'][i])
        
        if ids_to_delete:
            ingestor.collection.delete(ids=ids_to_delete)
            return {
                "success": True,
                "message": f"Document '{document_name}' deleted",
                "chunks_deleted": len(ids_to_delete)
            }
        else:
            raise HTTPException(status_code=404, detail=f"Document '{document_name}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

# ------------------- Application Startup/Shutdown -------------------

@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup"""
    logger.info("🚀 Starting PDF RAG Chatbot API")
    logger.info(f"📚 Model: {rag_processor.model_name}")
    logger.info("🔗 Ollama URL: http://localhost:11434")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("🛑 Shutting down PDF RAG Chatbot API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
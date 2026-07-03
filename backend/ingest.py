"""
PDF Ingestion Module for RAG Pipeline
Handles PDF processing, chunking, embedding, and vector storage
"""

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings  # <-- IMPORT THIS
import os
import uuid
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PDFIngestor:
    def __init__(self, persist_directory: str = "./chroma_db"):
        logger.info("🚀 Initializing PDF Ingestor...")
        
        # 1. Embedding model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("📚 Embedding model loaded")
        
        # 2. ChromaDB Client (UPDATED)
        os.makedirs(persist_directory, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        logger.info(f"💾 ChromaDB initialized at: {persist_directory}")
        
        # 3. Collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="pdf_documents",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"📊 Collection ready: {self.collection.name}")
        
        # 4. Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        logger.info("✂️ Text splitter configured")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        logger.info(f"📄 Extracting text from: {pdf_path}")
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
            doc.close()
            full_text = "\n\n".join(text_parts)
            logger.info(f"📝 Extracted {len(full_text)} characters")
            return full_text
        except Exception as e:
            logger.error(f"❌ Error extracting text: {str(e)}")
            raise

    def create_chunks(self, text: str) -> List[str]:
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided for chunking")
            return []
        chunks = self.text_splitter.split_text(text)
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        logger.info(f"✂️ Created {len(chunks)} chunks")
        return chunks

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        logger.info(f"🧠 Generating embeddings for {len(texts)} texts...")
        try:
            embeddings = self.embedding_model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            ).tolist()
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {str(e)}")
            raise

    def ingest_pdf(self, pdf_path: str, document_name: str) -> Dict[str, Any]:
        logger.info(f"🚀 Starting ingestion of '{document_name}'...")
        
        text = self.extract_text_from_pdf(pdf_path)
        if not text.strip():
            return {"document_name": document_name, "total_chunks": 0, "status": "failed", "error": "No text extracted"}
        
        chunks = self.create_chunks(text)
        if not chunks:
            return {"document_name": document_name, "total_chunks": 0, "status": "failed", "error": "No chunks created"}
        
        embeddings = self.generate_embeddings(chunks)
        
        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
        metadatas = [
            {"document": document_name, "chunk_index": i, "chunk_total": len(chunks), "chunk_length": len(chunk)}
            for i, chunk in enumerate(chunks)
        ]
        
        try:
            self.collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Stored {len(chunks)} chunks in ChromaDB")
            return {"document_name": document_name, "total_chunks": len(chunks), "status": "success"}
        except Exception as e:
            logger.error(f"❌ Error storing in ChromaDB: {str(e)}")
            raise

    def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        logger.info(f"🔍 Searching for: '{query[:50]}...'")
        try:
            query_embedding = self.embedding_model.encode([query]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            return results
        except Exception as e:
            logger.error(f"❌ Search error: {str(e)}")
            raise

    def delete_document(self, document_name: str) -> int:
        logger.info(f"🗑️ Deleting document: {document_name}")
        try:
            all_data = self.collection.get()
            ids_to_delete = []
            for i, metadata in enumerate(all_data.get('metadatas', [])):
                if metadata and metadata.get('document') == document_name:
                    ids_to_delete.append(all_data['ids'][i])
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"✅ Deleted {len(ids_to_delete)} chunks")
                return len(ids_to_delete)
            return 0
        except Exception as e:
            logger.error(f"❌ Delete error: {str(e)}")
            raise
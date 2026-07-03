"""
Utility functions for the PDF RAG Chatbot
Includes validation, ID generation, and helper functions
"""

import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import re

def generate_document_id(filename: str) -> str:
    """
    Generate a unique document ID based on filename and timestamp
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Unique document ID (timestamp_hash)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Create hash of filename for uniqueness
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    return f"{timestamp}_{file_hash}"

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename (str): Full filename
        
    Returns:
        str: File extension in lowercase (e.g., '.pdf')
    """
    return os.path.splitext(filename)[1].lower()

def validate_pdf(file) -> bool:
    """
    Validate that the uploaded file is a PDF
    
    Args:
        file: UploadFile object
        
    Returns:
        bool: True if valid PDF
        
    Raises:
        ValueError: If file is not a valid PDF
    """
    # Check file extension
    if not file.filename:
        raise ValueError("No filename provided")
    
    ext = get_file_extension(file.filename)
    if ext != '.pdf':
        raise ValueError(f"Invalid file type: {ext}. Only PDF files are allowed")
    
    # Check content type (if available)
    if hasattr(file, 'content_type'):
        if file.content_type not in ['application/pdf', 'application/x-pdf']:
            # Some browsers may not send correct content type
            # So we don't strictly enforce this check
            pass
    
    # Check file size (optional - 50MB limit)
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    max_size = 50 * 1024 * 1024  # 50MB
    if size > max_size:
        raise ValueError(f"File too large: {size/1024/1024:.1f}MB (max: 50MB)")
    
    if size == 0:
        raise ValueError("File is empty")
    
    return True

def extract_metadata_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata from PDF using PyMuPDF
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        Dict: PDF metadata including title, author, pages, etc.
    """
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        
        metadata = {
            "file_name": os.path.basename(pdf_path),
            "file_size": os.path.getsize(pdf_path),
            "num_pages": len(doc),
            "title": doc.metadata.get("title", "Unknown"),
            "author": doc.metadata.get("author", "Unknown"),
            "creation_date": doc.metadata.get("creationDate", "Unknown"),
            "modification_date": doc.metadata.get("modDate", "Unknown")
        }
        
        doc.close()
        return metadata
        
    except Exception as e:
        return {
            "error": str(e),
            "file_name": os.path.basename(pdf_path)
        }

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove any path components
    basename = os.path.basename(filename)
    
    # Remove special characters
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', basename)
    
    return sanitized

def format_chunks_for_display(chunks: list, max_length: int = 200) -> list:
    """
    Format chunks for display with truncation
    
    Args:
        chunks (list): List of text chunks
        max_length (int): Maximum length for each chunk
        
    Returns:
        list: Formatted chunks
    """
    formatted = []
    for i, chunk in enumerate(chunks):
        if len(chunk) > max_length:
            formatted.append(f"{chunk[:max_length]}...")
        else:
            formatted.append(chunk)
    return formatted

def calculate_chunk_metrics(chunks: list) -> Dict[str, Any]:
    """
    Calculate metrics about chunks
    
    Args:
        chunks (list): List of text chunks
        
    Returns:
        Dict: Metrics like average length, min, max
    """
    if not chunks:
        return {"total_chunks": 0}
    
    lengths = [len(chunk) for chunk in chunks]
    
    return {
        "total_chunks": len(chunks),
        "avg_length": sum(lengths) / len(lengths),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "total_characters": sum(lengths)
    }
"""Pydantic models for API requests and responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SourceInfo(BaseModel):
    """Source document information.
    
    Attributes:
        filename: Name of the source document
        page: Page number (if applicable)
        chunk_index: Index of the chunk in the document
        score: Relevance score
        content: Chunk content
    """
    filename: str = Field(..., description="Source document filename")
    page: Optional[int] = Field(None, description="Page number if applicable")
    chunk_index: int = Field(..., description="Chunk index in document")
    score: float = Field(..., description="Relevance score")
    content: str = Field(..., description="Chunk content")


class ChatRequest(BaseModel):
    """Chat request model.
    
    Attributes:
        question: User's question
        temperature: Override temperature for this query
        top_k: Override top_k for this query
    """
    question: str = Field(..., min_length=1, description="User question")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature override")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Top K override")


class ChatResponse(BaseModel):
    """Chat response model.
    
    Attributes:
        answer: Generated answer
        sources: List of source documents
        query_time: Time taken for query (seconds)
    """
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceInfo] = Field(default_factory=list, description="Source documents")
    query_time: float = Field(..., description="Query time in seconds")


class DocumentUpload(BaseModel):
    """Document upload response model.
    
    Attributes:
        filename: Uploaded filename
        status: Upload status
        chunks: Number of chunks created
        message: Status message
    """
    filename: str = Field(..., description="Uploaded filename")
    status: str = Field(..., description="Upload status")
    chunks: int = Field(..., description="Number of chunks created")
    message: str = Field(..., description="Status message")


class DocumentInfo(BaseModel):
    """Document information model.
    
    Attributes:
        filename: Document filename
        upload_date: Upload timestamp
        chunks: Number of chunks
        file_size: File size in bytes
    """
    filename: str = Field(..., description="Document filename")
    upload_date: Optional[str] = Field(None, description="Upload timestamp")
    chunks: int = Field(..., description="Number of chunks")
    file_size: int = Field(..., description="File size in bytes")


class HealthResponse(BaseModel):
    """Health check response model.
    
    Attributes:
        status: Health status
        ollama_available: Whether Ollama is accessible
        chroma_ready: Whether ChromaDB is ready
    """
    status: str = Field(..., description="Health status")
    ollama_available: bool = Field(..., description="Ollama availability")
    chroma_ready: bool = Field(..., description="ChromaDB readiness")


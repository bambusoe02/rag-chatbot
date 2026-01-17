"""Configuration settings using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support.
    
    Attributes:
        OLLAMA_BASE_URL: Base URL for Ollama API
        OLLAMA_MODEL: Model name for Ollama
        TEMPERATURE: LLM temperature for generation
        EMBEDDING_MODEL: HuggingFace embedding model name
        CHROMA_DIR: Directory for ChromaDB persistence
        COLLECTION_NAME: ChromaDB collection name
        CHUNK_SIZE: Text chunk size for splitting
        CHUNK_OVERLAP: Overlap between chunks
        TOP_K: Number of top documents to retrieve
        UPLOAD_DIR: Directory for uploaded documents
    """
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:14b-instruct"
    TEMPERATURE: float = 0.1
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # ChromaDB
    CHROMA_DIR: str = "./data/chroma_db"
    COLLECTION_NAME: str = "documents"
    
    # Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 5
    
    # Paths
    UPLOAD_DIR: str = "./data/uploads"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env (like API_BASE_URL for frontend)


# Global settings instance
settings = Settings()


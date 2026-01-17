"""Core RAG engine for document retrieval and generation."""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from loguru import logger

from backend.config import settings
from backend.document_processor import DocumentProcessor
from backend.models import SourceInfo
from backend.vector_store import VectorStore


class RAGEngine:
    """Retrieval-Augmented Generation engine.
    
    Handles document indexing, retrieval, and answer generation using
    local Ollama LLM and ChromaDB vector store.
    """
    
    SYSTEM_PROMPT = """You are a helpful AI assistant. Answer ONLY based on provided documents.

RULES:
1. If info not in documents: say 'I could not find this information in the available documents'
2. Always cite sources: [Source: {filename}, page {page}]
3. Answer in the question's language (Polish/English)
4. Be concise but complete
5. If unclear, ask for clarification

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_model: Optional[str] = None,
        llm_model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """Initialize RAG engine with Ollama and embeddings.
        
        Args:
            vector_store: VectorStore instance (creates new if None)
            embedding_model: Embedding model name
            llm_model: Ollama model name
            temperature: LLM temperature
        """
        logger.info("=" * 50)
        logger.info("Initializing RAG Engine...")
        logger.info("=" * 50)
        
        try:
            # Check Ollama connection first
            import requests
            logger.info(f"Checking Ollama connection at {settings.OLLAMA_BASE_URL}...")
            try:
                response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info("✓ Ollama is running and accessible")
                else:
                    logger.warning(f"⚠️ Ollama returned status {response.status_code}")
            except Exception as e:
                logger.error(f"⚠️ Cannot connect to Ollama: {e}")
                logger.warning("Continuing anyway - will fail on query if Ollama is not available")
            
            # Initialize embeddings
            embedding_model_name = embedding_model or settings.EMBEDDING_MODEL
            logger.info(f"Loading embedding model: {embedding_model_name}")
            
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=embedding_model_name,
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True},
                )
                logger.info("✓ Embeddings initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
                raise
            
            # Initialize LLM
            llm_model_name = llm_model or settings.OLLAMA_MODEL
            ollama_base_url = settings.OLLAMA_BASE_URL
            self.temperature = temperature or settings.TEMPERATURE
            
            logger.info(f"Initializing Ollama LLM: {llm_model_name} at {ollama_base_url}")
            
            try:
                from langchain_community.llms import Ollama
                
                self.llm = Ollama(
                    base_url=ollama_base_url,
                    model=llm_model_name,
                    temperature=self.temperature,
                )
                logger.info("✓ Ollama LLM initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama LLM: {e}")
                raise
            
            # Initialize vector store WITHOUT custom embedding function
            # ChromaDB 0.3.x/0.4.x will use default SentenceTransformerEmbeddingFunction
            logger.info(f"Initializing ChromaDB at {settings.CHROMA_DIR}...")
            try:
                if vector_store is None:
                    self.vector_store = VectorStore(
                        persist_directory=settings.CHROMA_DIR,
                        collection_name=settings.COLLECTION_NAME,
                        embedding_function=None,  # Use ChromaDB's default embeddings
                    )
                else:
                    self.vector_store = vector_store
                logger.info("✓ ChromaDB vector store initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                raise
            
            # Initialize document processor
            logger.info("Initializing document processor...")
            try:
                self.processor = DocumentProcessor()
                logger.info("✓ Document processor initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize document processor: {e}")
                raise
            
            logger.info("=" * 50)
            logger.info("✅ RAG Engine initialized successfully!")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error("=" * 50)
            logger.error(f"❌ Failed to initialize RAG engine: {e}")
            logger.error("=" * 50)
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    
    def add_document(self, filepath: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
        """Add document to the vector store.
        
        Args:
            filepath: Path to document file
            metadata: Optional additional metadata
            
        Returns:
            Tuple of (number_of_chunks, document_metadata)
            
        Raises:
            Exception: If document processing fails
        """
        try:
            logger.info(f"Processing document: {filepath}")
            
            # Extract text and metadata
            text, doc_metadata = self.processor.extract_text(filepath)
            if metadata:
                doc_metadata.update(metadata)
            
            logger.info(f"Extracted {len(text)} characters from {doc_metadata['filename']}")
            
            # Chunk text
            chunks = self.processor.chunk_text(
                text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            
            if not chunks:
                raise ValueError(f"No chunks created from {filepath}")
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Generate embeddings and prepare data
            texts = []
            metadatas = []
            ids = []
            
            filename = doc_metadata["filename"]
            upload_date = doc_metadata.get("modified_date", "")
            
            for chunk_text, chunk_meta in chunks:
                chunk_metadata = {
                    "filename": filename,
                    "upload_date": upload_date,
                    "file_size": doc_metadata.get("file_size", 0),
                    "file_type": doc_metadata.get("file_type", ""),
                    **chunk_meta,
                }
                chunk_id = f"{filename}_{chunk_meta['chunk_index']}"
                
                texts.append(chunk_text)
                metadatas.append(chunk_metadata)
                ids.append(chunk_id)
            
            # Add to vector store
            logger.info(f"Adding {len(ids)} chunks to vector store...")
            self.vector_store.add(
                texts=texts,
                metadatas=metadatas,
                ids=ids,
            )
            
            logger.info(f"✓ Successfully added document {filename} with {len(chunks)} chunks")
            return len(chunks), doc_metadata
            
        except Exception as e:
            logger.error(f"Error adding document {filepath}: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    
    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Tuple[str, List[SourceInfo], float]:
        """Query the RAG system and generate answer.
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            temperature: Override temperature for this query
            
        Returns:
            Tuple of (answer, sources, query_time)
        """
        start_time = time.time()
        top_k = top_k or settings.TOP_K
        temp = temperature if temperature is not None else self.temperature
        
        try:
            logger.info(f"Processing query: {question[:50]}...")
            
            # Retrieve relevant documents
            results = self.vector_store.query(
                query_texts=[question],
                n_results=top_k,
            )
            
            # Process results
            sources: List[SourceInfo] = []
            context_parts = []
            
            if results.get("documents") and results["documents"][0]:
                documents = results["documents"][0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                ids_list = results.get("ids", [[]])[0]
                
                logger.info(f"Retrieved {len(documents)} relevant documents")
                
                for idx, (doc_text, metadata, distance, doc_id) in enumerate(
                    zip(documents, metadatas, distances, ids_list)
                ):
                    filename = metadata.get("filename", "unknown")
                    page = metadata.get("page")
                    chunk_index = metadata.get("chunk_index", idx)
                    score = 1.0 - distance  # Convert distance to similarity score
                    
                    sources.append(SourceInfo(
                        filename=filename,
                        page=page,
                        chunk_index=chunk_index,
                        score=score,
                        content=doc_text[:200] + "..." if len(doc_text) > 200 else doc_text,
                    ))
                    
                    # Build context with source citation
                    page_str = f", page {page}" if page else ""
                    context_parts.append(f"[Source: {filename}{page_str}]\n{doc_text}")
            
            # Combine context
            context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found."
            
            if not context_parts:
                logger.warning("No relevant documents found for query")
                return (
                    "I could not find relevant information in the available documents. Please upload documents first.",
                    [],
                    time.time() - start_time
                )
            
            # Generate prompt
            prompt = self.SYSTEM_PROMPT.format(
                context=context,
                question=question,
            )
            
            # Generate answer with LLM
            logger.info("Generating answer with Ollama LLM...")
            try:
                if temp != self.temperature:
                    # Temporarily change temperature
                    original_temp = self.llm.temperature
                    self.llm.temperature = temp
                    answer = self.llm.invoke(prompt)
                    self.llm.temperature = original_temp
                else:
                    answer = self.llm.invoke(prompt)
                
                logger.info("✓ Answer generated successfully")
            except Exception as e:
                logger.error(f"Error generating answer with LLM: {e}")
                raise
            
            query_time = time.time() - start_time
            
            logger.info(f"Query completed in {query_time:.2f}s, retrieved {len(sources)} sources")
            
            return answer.strip(), sources, query_time
            
        except Exception as e:
            query_time = time.time() - start_time
            logger.error(f"Error during query: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            error_msg = f"I encountered an error while processing your question: {str(e)}"
            return error_msg, [], query_time
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all indexed documents.
        
        Returns:
            List of document metadata dictionaries
        """
        try:
            return self.vector_store.list_documents()
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def delete_document(self, filename: str) -> bool:
        """Delete document from the index.
        
        Args:
            filename: Name of document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.vector_store.delete(where={"filename": filename})
            logger.info(f"✓ Deleted document: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {filename}: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about indexed documents.
        
        Returns:
            Dictionary with document_count and chunk_count
        """
        try:
            doc_count, chunk_count = self.vector_store.get_document_count()
            return {
                "document_count": doc_count,
                "chunk_count": chunk_count,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"document_count": 0, "chunk_count": 0}
    
    def clear_all(self) -> None:
        """Clear all documents from the index."""
        try:
            self.vector_store.clear()
            logger.info("✓ Cleared all documents from RAG engine")
        except Exception as e:
            logger.error(f"Error clearing documents: {str(e)}")
            raise

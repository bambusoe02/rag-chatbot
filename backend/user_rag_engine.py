"""User-specific RAG Engine with hybrid search support."""

import os
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from loguru import logger

from backend.config import settings
from backend.document_processor import DocumentProcessor
from backend.vector_store import VectorStore


class UserRAGEngine:
    """RAG Engine with user isolation and hybrid search (BM25 + Semantic).
    
    Each user has their own ChromaDB collection for document isolation.
    Supports hybrid search combining keyword (BM25) and semantic search.
    """
    
    SYSTEM_PROMPT = """You are a helpful AI assistant. Answer ONLY based on provided documents.

RULES:
1. If info not in documents: say 'I could not find this information in the available documents'
2. Always cite sources: [Source: {filename}, chunk {chunk_id}]
3. Answer in the question's language (Polish/English)
4. Be concise but complete
5. If unclear, ask for clarification

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
    
    def __init__(
        self,
        user_id: int,
        embedding_model: Optional[str] = None,
        llm_model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """Initialize RAG engine for a specific user.
        
        Args:
            user_id: User ID for document isolation
            embedding_model: Embedding model name
            llm_model: Ollama model name
            temperature: LLM temperature
        """
        self.user_id = user_id
        self.collection_name = f"user_{user_id}_documents"
        
        logger.info(f"Initializing RAG Engine for user {user_id}")
        
        try:
            # Initialize embeddings
            embedding_model_name = embedding_model or settings.EMBEDDING_MODEL
            logger.info(f"Loading embedding model: {embedding_model_name}")
            
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info("✓ Embeddings initialized")
            
            # Initialize LLM
            llm_model_name = llm_model or settings.OLLAMA_MODEL
            ollama_base_url = settings.OLLAMA_BASE_URL
            self.temperature = temperature or settings.TEMPERATURE
            
            from langchain_community.llms import Ollama
            
            self.llm = Ollama(
                base_url=ollama_base_url,
                model=llm_model_name,
                temperature=self.temperature,
            )
            logger.info(f"✓ LLM initialized: {llm_model_name}")
            
            # Initialize vector store with user-specific collection
            chroma_dir = settings.CHROMA_DIR
            logger.info(f"Initializing ChromaDB for user {user_id}...")
            
            self.vector_store = VectorStore(
                persist_directory=chroma_dir,
                collection_name=self.collection_name,
                embedding_function=None,  # Use ChromaDB's default embeddings
            )
            logger.info("✓ ChromaDB vector store initialized")
            
            # Initialize document processor
            self.processor = DocumentProcessor()
            logger.info("✓ Document processor initialized")
            
            # Initialize BM25 index for hybrid search
            self.bm25_index = None
            self.documents_text = []
            self._build_bm25_index()
            
            logger.info(f"✅ RAG Engine initialized for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG engine for user {user_id}: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    
    def _build_bm25_index(self):
        """Build BM25 keyword search index from documents."""
        try:
            # Get all documents from vector store
            results = self.vector_store.collection.get(limit=10000)
            
            if results and 'documents' in results and results['documents']:
                self.documents_text = results['documents']
                
                # Build BM25 index
                from rank_bm25 import BM25Okapi
                tokenized = [doc.lower().split() for doc in self.documents_text]
                if tokenized:
                    self.bm25_index = BM25Okapi(tokenized)
                    logger.info(f"✓ BM25 index built with {len(self.documents_text)} documents")
                else:
                    self.bm25_index = None
            else:
                self.documents_text = []
                self.bm25_index = None
                
        except ImportError:
            logger.warning("rank-bm25 not installed, BM25 search unavailable")
            self.bm25_index = None
        except Exception as e:
            logger.warning(f"Could not build BM25 index: {e}")
            self.bm25_index = None
    
    def add_document(self, filepath: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
        """Add document to user's vector store.
        
        Args:
            filepath: Path to document file
            metadata: Optional metadata dictionary
            
        Returns:
            Tuple of (number of chunks, metadata)
        """
        start_time = time.time()
        
        try:
            # Extract text
            text, file_metadata = self.processor.extract_text(filepath)
            
            # Merge metadata
            if metadata:
                file_metadata.update(metadata)
            
            # Split into chunks
            chunks = self.processor.chunk_text(text)
            
            # Prepare metadata for each chunk
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = file_metadata.copy()
                chunk_metadata.update({
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "user_id": self.user_id,
                })
                metadatas.append(chunk_metadata)
                ids.append(f"{file_metadata.get('filename', 'doc')}_{i}")
            
            # Add to vector store
            self.vector_store.add(chunks, metadatas, ids)
            
            # Rebuild BM25 index
            self._build_bm25_index()
            
            elapsed = time.time() - start_time
            logger.info(f"Added {len(chunks)} chunks for {file_metadata.get('filename')} in {elapsed:.2f}s")
            
            return len(chunks), file_metadata
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    def hybrid_search(self, query: str, k: int = 5, alpha: float = 0.7) -> List[Dict[str, Any]]:
        """Hybrid search combining BM25 (keyword) and semantic search.
        
        Args:
            query: Search query
            k: Number of results
            alpha: Weight for semantic search (0=only BM25, 1=only semantic)
            
        Returns:
            List of document dictionaries with scores
        """
        if not self.bm25_index or not self.documents_text:
            # Fallback to semantic only
            results = self.vector_store.query([query], n_results=k)
            return self._format_results(results)
        
        try:
            # BM25 search
            tokenized_query = query.lower().split()
            bm25_scores = np.array(self.bm25_index.get_scores(tokenized_query))
            
            # Semantic search
            semantic_results = self.vector_store.query([query], n_results=k * 2)
            
            if not semantic_results or not semantic_results.get('ids') or not semantic_results['ids'][0]:
                # Fallback to BM25 only
                top_indices = np.argsort(bm25_scores)[-k:][::-1]
                return [
                    {
                        "content": self.documents_text[i],
                        "score": float(bm25_scores[i]),
                        "metadata": {}
                    }
                    for i in top_indices if i < len(self.documents_text)
                ]
            
            # Get document indices from semantic results
            semantic_ids = semantic_results['ids'][0]
            semantic_docs = semantic_results.get('documents', [[]])[0]
            semantic_metadatas = semantic_results.get('metadatas', [[]])[0]
            semantic_distances = semantic_results.get('distances', [[]])[0]
            
            # Normalize scores
            if bm25_scores.max() > bm25_scores.min():
                bm25_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min())
            else:
                bm25_norm = np.zeros_like(bm25_scores)
            
            # Convert distances to scores (lower distance = higher score)
            semantic_scores = 1 - np.array(semantic_distances)
            if semantic_scores.max() > semantic_scores.min():
                semantic_norm = (semantic_scores - semantic_scores.min()) / (semantic_scores.max() - semantic_scores.min())
            else:
                semantic_norm = np.ones_like(semantic_scores)
            
            # Map semantic results to document indices
            doc_to_score = {}
            for i, doc_id in enumerate(semantic_ids):
                # Extract index from doc_id if possible
                try:
                    doc_idx = int(doc_id.split('_')[-1]) if '_' in doc_id else i
                except:
                    doc_idx = i
                
                if doc_idx < len(bm25_scores):
                    bm25_score_norm = float(bm25_norm[doc_idx])
                    semantic_score_norm = float(semantic_norm[i]) if i < len(semantic_norm) else 0.0
                    
                    # Combine scores
                    combined_score = alpha * semantic_score_norm + (1 - alpha) * bm25_score_norm
                    
                    doc_to_score[doc_idx] = {
                        "score": combined_score,
                        "content": semantic_docs[i] if i < len(semantic_docs) else "",
                        "metadata": semantic_metadatas[i] if i < len(semantic_metadatas) else {},
                    }
            
            # Sort by combined score and return top k
            sorted_results = sorted(doc_to_score.items(), key=lambda x: x[1]["score"], reverse=True)
            return [result[1] for _, result in sorted_results[:k]]
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            # Fallback to semantic only
            results = self.vector_store.query([query], n_results=k)
            return self._format_results(results)
    
    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format vector store results into standard format."""
        formatted = []
        if results and results.get('ids') and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                formatted.append({
                    "content": results.get('documents', [[]])[0][i] if results.get('documents') and i < len(results['documents'][0]) else "",
                    "score": 1 - float(results.get('distances', [[1.0]])[0][i]) if results.get('distances') and i < len(results['distances'][0]) else 0.0,
                    "metadata": results.get('metadatas', [[]])[0][i] if results.get('metadatas') and i < len(results['metadatas'][0]) else {},
                })
        return formatted
    
    def query(
        self,
        question: str,
        search_mode: str = "hybrid",
        k: int = 5,
        alpha: float = 0.7,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Query the RAG system.
        
        Args:
            question: User's question
            search_mode: "semantic", "keyword", or "hybrid"
            k: Number of documents to retrieve
            alpha: Weight for semantic search (for hybrid mode)
            temperature: Override temperature for this query
            
        Returns:
            Dictionary with answer, sources, and query_time
        """
        start_time = time.time()
        
        try:
            # Retrieve documents
            if search_mode == "semantic":
                results = self.vector_store.query([question], n_results=k)
                docs = self._format_results(results)
            elif search_mode == "keyword" and self.bm25_index:
                # BM25 only
                tokenized = question.lower().split()
                scores = np.array(self.bm25_index.get_scores(tokenized))
                top_indices = np.argsort(scores)[-k:][::-1]
                docs = [
                    {
                        "content": self.documents_text[i],
                        "score": float(scores[i]),
                        "metadata": {}
                    }
                    for i in top_indices if i < len(self.documents_text)
                ]
            else:  # hybrid
                docs = self.hybrid_search(question, k=k, alpha=alpha)
            
            if not docs:
                return {
                    "answer": "No relevant documents found. Please upload documents first.",
                    "sources": [],
                    "query_time": time.time() - start_time
                }
            
            # Build context
            context = "\n\n".join([doc["content"] for doc in docs[:k]])
            
            # Get metadata for sources
            sources = []
            for doc in docs[:3]:  # Top 3 sources
                metadata = doc.get("metadata", {})
                sources.append({
                    "filename": metadata.get("filename", "unknown"),
                    "chunk_id": metadata.get("chunk_id", 0),
                    "score": doc.get("score", 0.0),
                    "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                })
            
            # Generate answer
            prompt = self.SYSTEM_PROMPT.format(
                context=context,
                question=question
            )
            
            use_temperature = temperature if temperature is not None else self.temperature
            if use_temperature != self.temperature:
                # Create new LLM instance with different temperature
                from langchain_community.llms import Ollama
                temp_llm = Ollama(
                    base_url=settings.OLLAMA_BASE_URL,
                    model=settings.OLLAMA_MODEL,
                    temperature=use_temperature,
                )
                answer = temp_llm.invoke(prompt)
            else:
                answer = self.llm.invoke(prompt)
            
            query_time = time.time() - start_time
            
            return {
                "answer": answer,
                "sources": sources,
                "query_time": query_time
            }
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "query_time": time.time() - start_time
            }
    
    def list_documents(self) -> List[str]:
        """List all unique documents for this user."""
        try:
            results = self.vector_store.collection.get(limit=10000)
            filenames = set()
            if results and 'metadatas' in results:
                for meta in results['metadatas']:
                    if meta and 'filename' in meta:
                        filenames.add(meta['filename'])
            return list(filenames)
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    def delete_document(self, filename: str):
        """Delete all chunks of a document."""
        try:
            # Query chunks with this filename
            results = self.vector_store.collection.get(
                where={"filename": filename},
                limit=10000
            )
            
            if results and 'ids' in results and results['ids']:
                self.vector_store.collection.delete(ids=results['ids'])
                self._build_bm25_index()
                logger.info(f"Deleted document: {filename} ({len(results['ids'])} chunks)")
            else:
                logger.warning(f"Document not found: {filename}")
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    def clear_all(self):
        """Clear all documents for this user."""
        try:
            self.vector_store.clear()
            self._build_bm25_index()
            logger.info(f"Cleared all documents for user {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to clear documents: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for this user's documents."""
        try:
            doc_count, chunk_count = self.vector_store.get_document_count()
            return {
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "user_id": self.user_id,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "document_count": 0,
                "chunk_count": 0,
                "user_id": self.user_id,
            }


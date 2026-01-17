"""ChromaDB vector store wrapper for persistent storage."""

import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger


class VectorStore:
    """ChromaDB wrapper for document vector storage and retrieval.
    
    Provides persistent storage for document embeddings with metadata support.
    """
    
    def __init__(
        self,
        persist_directory: str,
        collection_name: str,
        embedding_function: Optional[Callable] = None,
    ):
        """Initialize ChromaDB client and collection.
        
        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the collection
            embedding_function: Optional custom embedding function
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.embedding_function = embedding_function
        
        # Initialize ChromaDB client with persistence
        try:
            # Try PersistentClient first (newer versions)
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
        except AttributeError:
            # Fall back to Client for older versions
            self.client = chromadb.Client(
                settings=ChromaSettings(
                    persist_directory=str(self.persist_directory),
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
        
        # Get or create collection WITHOUT embedding function
        # We'll handle embeddings manually
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            # If collection exists with embedding function, delete and recreate
            try:
                self.client.delete_collection(name=collection_name)
            except:
                pass
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        
        logger.info(f"Initialized ChromaDB collection '{collection_name}' at {persist_directory}")
    
    def add(
        self,
        texts: List[str],
        metadatas: List[Dict[str, any]],
        ids: List[str],
    ) -> None:
        """Add documents to the vector store.
        
        Args:
            texts: List of text chunks
            metadatas: List of metadata dictionaries
            ids: List of unique document IDs
        """
        if not texts or not ids:
            logger.warning("Attempted to add empty documents")
            return
        
        try:
            # For ChromaDB 0.3.x/0.4.x, use default embeddings
            # Custom embeddings would require consistent embedding function for both add and query
            # For simplicity, use ChromaDB's default embeddings
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"Added {len(ids)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, any]] = None,
    ) -> Dict[str, List]:
        """Query the vector store for similar documents.
        
        Args:
            query_texts: List of query texts (usually single item)
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary with keys: ids, distances, documents, metadatas
        """
        try:
            # For ChromaDB 0.3.x/0.4.x, always use query_texts
            # If we have custom embeddings, we need to ensure documents were added with same embeddings
            # For now, use ChromaDB's default embeddings for querying
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
            )
            logger.debug(f"Query returned {len(results.get('ids', [{}])[0])} results")
            return results
        except Exception as e:
            logger.error(f"Error querying vector store: {str(e)}")
            raise
    
    def delete(self, where: Optional[Dict[str, any]] = None, ids: Optional[List[str]] = None) -> None:
        """Delete documents from the vector store.
        
        Args:
            where: Metadata filter for deletion
            ids: Specific IDs to delete
        """
        try:
            if ids:
                self.collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents by IDs")
            elif where:
                self.collection.delete(where=where)
                logger.info(f"Deleted documents matching filter: {where}")
            else:
                logger.warning("No deletion criteria provided")
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    def list_documents(self) -> List[Dict[str, any]]:
        """List all unique documents in the store.
        
        Returns:
            List of document metadata dictionaries
        """
        try:
            # Get all results (with large limit)
            all_results = self.collection.get(limit=10000)
            
            # Group by filename
            doc_map: Dict[str, Dict[str, any]] = {}
            
            if all_results.get("metadatas"):
                for metadata, doc_id in zip(all_results["metadatas"], all_results["ids"]):
                    filename = metadata.get("filename", "unknown")
                    
                    if filename not in doc_map:
                        doc_map[filename] = {
                            "filename": filename,
                            "chunks": 0,
                            "upload_date": metadata.get("upload_date"),
                            "file_size": metadata.get("file_size", 0),
                        }
                    
                    doc_map[filename]["chunks"] += 1
            
            return list(doc_map.values())
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def get_document_count(self) -> Tuple[int, int]:
        """Get count of documents and chunks.
        
        Returns:
            Tuple of (document_count, chunk_count)
        """
        try:
            all_results = self.collection.get(limit=10000)
            chunk_count = len(all_results.get("ids", []))
            
            # Count unique filenames
            filenames = set()
            if all_results.get("metadatas"):
                for metadata in all_results["metadatas"]:
                    filename = metadata.get("filename", "unknown")
                    filenames.add(filename)
            
            return len(filenames), chunk_count
            
        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return 0, 0
    
    def clear(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Get all IDs and delete them
            all_results = self.collection.get(limit=10000)
            if all_results.get("ids"):
                self.collection.delete(ids=all_results["ids"])
            logger.info("Cleared all documents from vector store")
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise

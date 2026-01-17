"""Document processing for PDF, DOCX, TXT, and MD files."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from docx import Document as DocxDocument
from loguru import logger
from PyPDF2 import PdfReader

from backend.config import settings


class DocumentProcessor:
    """Process documents and extract text content.
    
    Supports PDF, DOCX, TXT, and MD file formats.
    """
    
    @staticmethod
    def extract_text(filepath: str) -> Tuple[str, Dict[str, any]]:
        """Extract text from supported document formats.
        
        Args:
            filepath: Path to the document file
            
        Returns:
            Tuple of (text content, metadata dictionary)
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file does not exist
            Exception: For document processing errors
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_ext = path.suffix.lower()
        metadata = DocumentProcessor.extract_metadata(filepath)
        
        try:
            if file_ext == ".pdf":
                text, pages = DocumentProcessor._extract_pdf(filepath)
                metadata["pages"] = pages
            elif file_ext == ".docx":
                text = DocumentProcessor._extract_docx(filepath)
            elif file_ext in [".txt", ".md"]:
                text = DocumentProcessor._extract_text_file(filepath)
            else:
                raise ValueError(
                    f"Unsupported file format: {file_ext}. "
                    "Supported formats: PDF, DOCX, TXT, MD"
                )
            
            logger.info(f"Extracted {len(text)} characters from {path.name}")
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error processing {filepath}: {str(e)}")
            raise
    
    @staticmethod
    def _extract_pdf(filepath: str) -> Tuple[str, int]:
        """Extract text from PDF file.
        
        Args:
            filepath: Path to PDF file
            
        Returns:
            Tuple of (text content, number of pages)
        """
        text_parts = []
        reader = PdfReader(filepath)
        
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text.strip():
                text_parts.append(f"--- Page {page_num} ---\n{page_text}")
        
        text = "\n\n".join(text_parts)
        return text, len(reader.pages)
    
    @staticmethod
    def _extract_docx(filepath: str) -> str:
        """Extract text from DOCX file.
        
        Args:
            filepath: Path to DOCX file
            
        Returns:
            Extracted text content
        """
        doc = DocxDocument(filepath)
        paragraphs = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        
        return "\n\n".join(paragraphs)
    
    @staticmethod
    def _extract_text_file(filepath: str) -> str:
        """Extract text from TXT or MD file.
        
        Args:
            filepath: Path to text file
            
        Returns:
            File content as string
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    @staticmethod
    def extract_metadata(filepath: str) -> Dict[str, any]:
        """Extract metadata from file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Dictionary with metadata
        """
        path = Path(filepath)
        stat = path.stat()
        
        return {
            "filename": path.name,
            "file_size": stat.st_size,
            "file_type": path.suffix.lower(),
            "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[Tuple[str, Dict[str, any]]]:
        """Split text into chunks with overlap.
        
        Args:
            text: Text content to chunk
            chunk_size: Size of each chunk (defaults to config)
            chunk_overlap: Overlap between chunks (defaults to config)
            
        Returns:
            List of tuples: (chunk_text, chunk_metadata)
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        if not text.strip():
            return []
        
        # Simple character-based chunking
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence or paragraph boundary
            if end < len(text):
                # Look for paragraph break first
                para_break = text.rfind("\n\n", start, end)
                if para_break > start:
                    end = para_break + 2
                else:
                    # Look for sentence boundary
                    sentence_break = max(
                        text.rfind(". ", start, end),
                        text.rfind("! ", start, end),
                        text.rfind("? ", start, end),
                    )
                    if sentence_break > start:
                        end = sentence_break + 2
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                # Extract page number if present
                page_match = re.search(r"--- Page (\d+) ---", chunk_text)
                page = int(page_match.group(1)) if page_match else None
                
                chunks.append((
                    chunk_text,
                    {
                        "chunk_index": chunk_index,
                        "start_char": start,
                        "end_char": end,
                        "page": page,
                    }
                ))
                chunk_index += 1
            
            start = end - chunk_overlap if chunk_overlap > 0 else end
            
            # Prevent infinite loop
            if start >= end:
                break
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks


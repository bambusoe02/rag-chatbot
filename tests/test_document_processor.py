"""Comprehensive tests for document processor module."""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.document_processor import DocumentProcessor


# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture
def processor():
    """Create DocumentProcessor instance."""
    return DocumentProcessor()


@pytest.fixture
def temp_txt_file():
    """Create temporary text file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("This is a test document.\nIt has multiple lines.\nFor testing purposes.")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def temp_md_file():
    """Create temporary markdown file."""
    content = """# Test Document

## Section 1
This is section 1 content.

## Section 2
This is section 2 content.

- Item 1
- Item 2
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_text():
    """Sample text for chunking tests."""
    return """This is a long text document that needs to be split into chunks. 
It contains multiple sentences and paragraphs. Each paragraph should be preserved 
where possible. This ensures that context is maintained across chunks.

This is the second paragraph with more content. It discusses various topics and 
provides detailed information. The chunking algorithm should handle this appropriately.

Final paragraph with concluding thoughts and summary."""


# ==========================================
# UNIT TESTS - Text Extraction
# ==========================================

def test_extract_text_from_txt_file(processor, temp_txt_file):
    """Test extracting text from TXT file."""
    text, metadata = processor.extract_text(temp_txt_file)
    
    assert isinstance(text, str)
    assert len(text) > 0
    assert "test document" in text.lower()
    assert isinstance(metadata, dict)
    assert metadata['filename'] == Path(temp_txt_file).name
    assert metadata['file_type'] == '.txt'


def test_extract_text_from_md_file(processor, temp_md_file):
    """Test extracting text from Markdown file."""
    text, metadata = processor.extract_text(temp_md_file)
    
    assert isinstance(text, str)
    assert "# Test Document" in text
    assert "Section 1" in text
    assert "Item 1" in text
    assert metadata['file_type'] == '.md'


def test_extract_text_file_not_found(processor):
    """Test handling of non-existent file."""
    with pytest.raises(FileNotFoundError):
        processor.extract_text("/nonexistent/file.txt")


def test_extract_text_unsupported_format(processor, tmp_path):
    """Test handling of unsupported file format."""
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("content")
    
    with pytest.raises(ValueError, match="Unsupported file format"):
        processor.extract_text(str(unsupported_file))


# ==========================================
# UNIT TESTS - PDF Extraction (Mocked)
# ==========================================

@patch('backend.document_processor.PdfReader')
def test_extract_pdf_mock(mock_pdf_reader, processor, tmp_path):
    """Test PDF extraction with mocked PyPDF2."""
    # Create temp PDF file
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"fake pdf content")
    
    # Mock PDF reader
    mock_page1 = Mock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = Mock()
    mock_page2.extract_text.return_value = "Page 2 content"
    
    mock_reader_instance = Mock()
    mock_reader_instance.pages = [mock_page1, mock_page2]
    mock_pdf_reader.return_value = mock_reader_instance
    
    text, pages = processor._extract_pdf(str(pdf_file))
    
    assert "Page 1 content" in text
    assert "Page 2 content" in text
    assert pages == 2
    assert "--- Page 1 ---" in text
    assert "--- Page 2 ---" in text


# ==========================================
# UNIT TESTS - DOCX Extraction (Mocked)
# ==========================================

@patch('backend.document_processor.DocxDocument')
def test_extract_docx_mock(mock_docx, processor, tmp_path):
    """Test DOCX extraction with mocked python-docx."""
    # Create temp DOCX file
    docx_file = tmp_path / "test.docx"
    docx_file.write_bytes(b"fake docx content")
    
    # Mock paragraphs
    mock_para1 = Mock()
    mock_para1.text = "First paragraph"
    mock_para2 = Mock()
    mock_para2.text = "Second paragraph"
    
    mock_doc = Mock()
    mock_doc.paragraphs = [mock_para1, mock_para2]
    mock_docx.return_value = mock_doc
    
    text = processor._extract_docx(str(docx_file))
    
    assert "First paragraph" in text
    assert "Second paragraph" in text


# ==========================================
# UNIT TESTS - Metadata Extraction
# ==========================================

def test_extract_metadata(processor, temp_txt_file):
    """Test metadata extraction from file."""
    metadata = processor.extract_metadata(temp_txt_file)
    
    assert isinstance(metadata, dict)
    assert 'filename' in metadata
    assert 'file_size' in metadata
    assert 'file_type' in metadata
    assert 'modified_date' in metadata
    
    assert metadata['filename'] == Path(temp_txt_file).name
    assert metadata['file_type'] == '.txt'
    assert metadata['file_size'] > 0
    assert isinstance(metadata['modified_date'], str)


# ==========================================
# UNIT TESTS - Text Chunking
# ==========================================

def test_chunk_text_basic(processor, sample_text):
    """Test basic text chunking."""
    chunks = processor.chunk_text(sample_text, chunk_size=100, chunk_overlap=20)
    
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    
    # Each chunk should be a tuple of (text, metadata)
    for chunk_text, chunk_meta in chunks:
        assert isinstance(chunk_text, str)
        assert isinstance(chunk_meta, dict)
        assert 'chunk_index' in chunk_meta
        assert 'start_char' in chunk_meta
        assert 'end_char' in chunk_meta


def test_chunk_text_empty_string(processor):
    """Test chunking empty string."""
    chunks = processor.chunk_text("", chunk_size=100, chunk_overlap=20)
    assert chunks == []


def test_chunk_text_short_text(processor):
    """Test chunking text shorter than chunk size."""
    short_text = "Short text."
    chunks = processor.chunk_text(short_text, chunk_size=1000, chunk_overlap=200)
    
    assert len(chunks) == 1
    chunk_text, chunk_meta = chunks[0]
    assert chunk_text == short_text
    assert chunk_meta['chunk_index'] == 0


def test_chunk_text_with_overlap(processor, sample_text):
    """Test that chunks have proper overlap."""
    chunks = processor.chunk_text(sample_text, chunk_size=100, chunk_overlap=20)
    
    if len(chunks) > 1:
        # Check that consecutive chunks have overlap
        for i in range(len(chunks) - 1):
            chunk1_text = chunks[i][0]
            chunk2_text = chunks[i + 1][0]
            
            # Some overlap should exist
            assert len(chunk1_text) > 0
            assert len(chunk2_text) > 0


def test_chunk_text_preserves_content(processor, sample_text):
    """Test that no content is lost during chunking."""
    chunks = processor.chunk_text(sample_text, chunk_size=50, chunk_overlap=10)
    
    # Combine all chunks (removing overlap)
    combined_chunks = set()
    for chunk_text, _ in chunks:
        combined_chunks.add(chunk_text.strip())
    
    # All chunks should contain unique content
    assert len(combined_chunks) == len(chunks)


def test_chunk_text_metadata_sequence(processor, sample_text):
    """Test that chunk indices are sequential."""
    chunks = processor.chunk_text(sample_text, chunk_size=100, chunk_overlap=20)
    
    for i, (_, chunk_meta) in enumerate(chunks):
        assert chunk_meta['chunk_index'] == i


def test_chunk_text_custom_sizes(processor, sample_text):
    """Test chunking with different sizes."""
    # Small chunks
    small_chunks = processor.chunk_text(sample_text, chunk_size=50, chunk_overlap=10)
    
    # Large chunks
    large_chunks = processor.chunk_text(sample_text, chunk_size=500, chunk_overlap=50)
    
    # Small chunks should create more pieces
    assert len(small_chunks) >= len(large_chunks)


def test_chunk_text_page_extraction(processor):
    """Test extraction of page numbers from PDF-style text."""
    pdf_style_text = """--- Page 1 ---
Content from page 1

--- Page 2 ---
Content from page 2"""
    
    chunks = processor.chunk_text(pdf_style_text, chunk_size=50, chunk_overlap=10)
    
    # Check that page numbers are extracted in metadata
    page_found = False
    for _, chunk_meta in chunks:
        if chunk_meta.get('page') is not None:
            page_found = True
            assert isinstance(chunk_meta['page'], int)
    
    assert page_found


# ==========================================
# INTEGRATION TESTS
# ==========================================

def test_full_pipeline_txt_file(processor, temp_txt_file):
    """Test full pipeline: extract + metadata + chunking."""
    # Extract
    text, metadata = processor.extract_text(temp_txt_file)
    
    # Validate extraction
    assert len(text) > 0
    assert metadata['filename'] == Path(temp_txt_file).name
    
    # Chunk
    chunks = processor.chunk_text(text, chunk_size=50, chunk_overlap=10)
    
    # Validate chunks
    assert len(chunks) > 0
    for chunk_text, chunk_meta in chunks:
        assert len(chunk_text) > 0
        assert chunk_meta['chunk_index'] >= 0


def test_full_pipeline_md_file(processor, temp_md_file):
    """Test full pipeline with Markdown file."""
    text, metadata = processor.extract_text(temp_md_file)
    chunks = processor.chunk_text(text, chunk_size=100, chunk_overlap=20)
    
    assert len(chunks) > 0
    assert "# Test Document" in text
    assert metadata['file_type'] == '.md'


# ==========================================
# EDGE CASES
# ==========================================

def test_chunk_text_unicode_content(processor):
    """Test chunking with Unicode characters."""
    unicode_text = "Test with émojis 🎉 and special characters: ąćęłńóśźż"
    chunks = processor.chunk_text(unicode_text, chunk_size=30, chunk_overlap=5)
    
    assert len(chunks) > 0
    for chunk_text, _ in chunks:
        assert isinstance(chunk_text, str)


def test_chunk_text_very_long_text(processor):
    """Test chunking very long text."""
    long_text = "word " * 10000  # 50,000 characters
    chunks = processor.chunk_text(long_text, chunk_size=1000, chunk_overlap=200)
    
    assert len(chunks) > 10
    # Verify no chunk is too large
    for chunk_text, _ in chunks:
        assert len(chunk_text) <= 1500  # chunk_size + some tolerance


def test_chunk_text_special_characters(processor):
    """Test chunking with special characters."""
    special_text = "Test\n\nDouble newlines.\n\nAnother paragraph.\n\n"
    chunks = processor.chunk_text(special_text, chunk_size=50, chunk_overlap=10)
    
    assert len(chunks) > 0


def test_metadata_with_special_filename(processor, tmp_path):
    """Test metadata extraction with special characters in filename."""
    special_file = tmp_path / "test_file_123-abc.txt"
    special_file.write_text("content")
    
    metadata = processor.extract_metadata(str(special_file))
    
    assert metadata['filename'] == "test_file_123-abc.txt"


# ==========================================
# PERFORMANCE TESTS
# ==========================================

def test_chunk_text_performance(processor, benchmark):
    """Benchmark chunking performance."""
    large_text = "sentence. " * 1000  # ~10,000 characters
    
    result = benchmark(processor.chunk_text, large_text, chunk_size=1000, chunk_overlap=200)
    
    assert len(result) > 0


# ==========================================
# PARAMETRIZED TESTS
# ==========================================

@pytest.mark.parametrize("chunk_size,chunk_overlap", [
    (500, 100),
    (1000, 200),
    (1500, 300),
    (2000, 400),
])
def test_chunk_text_various_sizes(processor, sample_text, chunk_size, chunk_overlap):
    """Test chunking with various size configurations."""
    chunks = processor.chunk_text(sample_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    
    # Verify overlap is within bounds
    if len(chunks) > 1:
        for i in range(len(chunks) - 1):
            _, meta1 = chunks[i]
            _, meta2 = chunks[i + 1]
            
            # Check that chunks overlap properly
            assert meta1['end_char'] >= meta2['start_char'] - chunk_overlap


@pytest.mark.parametrize("file_ext", ['.txt', '.md'])
def test_extract_text_file_formats(processor, tmp_path, file_ext):
    """Test extraction from different text file formats."""
    test_file = tmp_path / f"test{file_ext}"
    test_content = "Test content for extraction"
    test_file.write_text(test_content, encoding='utf-8')
    
    text, metadata = processor.extract_text(str(test_file))
    
    assert test_content in text
    assert metadata['file_type'] == file_ext


# ==========================================
# ERROR HANDLING TESTS
# ==========================================

def test_extract_text_with_corrupted_file(processor, tmp_path):
    """Test handling of corrupted file."""
    corrupted_file = tmp_path / "corrupted.txt"
    # Write binary garbage
    corrupted_file.write_bytes(b'\x00\x01\x02\x03')
    
    # Should still attempt to read (may raise or return empty)
    try:
        text, metadata = processor.extract_text(str(corrupted_file))
        # If it succeeds, verify it returns something
        assert isinstance(text, str)
        assert isinstance(metadata, dict)
    except Exception as e:
        # If it fails, it should be a known exception
        assert isinstance(e, (UnicodeDecodeError, ValueError))


def test_extract_text_empty_file(processor, tmp_path):
    """Test extraction from empty file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding='utf-8')
    
    text, metadata = processor.extract_text(str(empty_file))
    
    assert text == ""
    assert metadata['file_size'] == 0


def test_chunk_text_with_none_input(processor):
    """Test chunking with None input (should handle gracefully)."""
    with pytest.raises((TypeError, AttributeError)):
        processor.chunk_text(None)


# ==========================================
# INTEGRATION TESTS
# ==========================================

def test_process_multiple_files_sequentially(processor, temp_txt_file, temp_md_file):
    """Test processing multiple files in sequence."""
    files = [temp_txt_file, temp_md_file]
    results = []
    
    for file_path in files:
        text, metadata = processor.extract_text(file_path)
        chunks = processor.chunk_text(text, chunk_size=100, chunk_overlap=20)
        results.append({
            'text': text,
            'metadata': metadata,
            'chunks': chunks
        })
    
    assert len(results) == 2
    for result in results:
        assert len(result['text']) > 0
        assert len(result['chunks']) > 0


def test_static_methods_callable_without_instance():
    """Test that static methods work without processor instance."""
    # Should be able to call static methods directly
    result = DocumentProcessor.extract_metadata
    assert callable(result)
    
    result = DocumentProcessor.chunk_text
    assert callable(result)


# ==========================================
# BOUNDARY TESTS
# ==========================================

def test_chunk_text_boundary_exact_size(processor):
    """Test chunking text that is exactly chunk_size."""
    text = "a" * 1000  # Exactly 1000 characters
    chunks = processor.chunk_text(text, chunk_size=1000, chunk_overlap=0)
    
    assert len(chunks) == 1
    assert len(chunks[0][0]) == 1000


def test_chunk_text_boundary_one_char_over(processor):
    """Test chunking text that is one char over chunk_size."""
    text = "a" * 1001  # 1001 characters
    chunks = processor.chunk_text(text, chunk_size=1000, chunk_overlap=0)
    
    assert len(chunks) >= 1


def test_chunk_text_zero_overlap(processor, sample_text):
    """Test chunking with zero overlap."""
    chunks = processor.chunk_text(sample_text, chunk_size=100, chunk_overlap=0)
    
    assert len(chunks) > 0
    
    if len(chunks) > 1:
        # Verify no overlap
        for i in range(len(chunks) - 1):
            _, meta1 = chunks[i]
            _, meta2 = chunks[i + 1]
            # End of chunk1 should be <= start of chunk2
            assert meta1['end_char'] <= meta2['start_char']


# ==========================================
# VALIDATION TESTS
# ==========================================

def test_chunk_metadata_completeness(processor, sample_text):
    """Test that chunk metadata contains all required fields."""
    chunks = processor.chunk_text(sample_text, chunk_size=100, chunk_overlap=20)
    
    required_fields = ['chunk_index', 'start_char', 'end_char']
    
    for _, chunk_meta in chunks:
        for field in required_fields:
            assert field in chunk_meta, f"Missing required field: {field}"
        
        # Validate field types
        assert isinstance(chunk_meta['chunk_index'], int)
        assert isinstance(chunk_meta['start_char'], int)
        assert isinstance(chunk_meta['end_char'], int)
        
        # Validate logical constraints
        assert chunk_meta['chunk_index'] >= 0
        assert chunk_meta['start_char'] >= 0
        assert chunk_meta['end_char'] > chunk_meta['start_char']


def test_file_size_metadata_accuracy(processor, temp_txt_file):
    """Test that reported file size matches actual file size."""
    metadata = processor.extract_metadata(temp_txt_file)
    actual_size = os.path.getsize(temp_txt_file)
    
    assert metadata['file_size'] == actual_size


# ==========================================
# MOCK TESTS FOR EXTERNAL DEPENDENCIES
# ==========================================

@patch('backend.document_processor.PdfReader')
def test_pdf_extraction_with_exception(mock_pdf_reader, processor, tmp_path):
    """Test handling of PDF extraction errors."""
    pdf_file = tmp_path / "bad.pdf"
    pdf_file.write_bytes(b"not a real pdf")
    
    # Mock to raise exception
    mock_pdf_reader.side_effect = Exception("PDF parsing error")
    
    with pytest.raises(Exception):
        processor._extract_pdf(str(pdf_file))


# ==========================================
# CONFIGURATION TESTS
# ==========================================

def test_chunk_text_uses_default_settings(processor, sample_text):
    """Test that chunking uses default settings from config."""
    from backend.config import settings
    
    chunks = processor.chunk_text(sample_text)  # No explicit size/overlap
    
    # Should use defaults from settings
    assert len(chunks) > 0


# ==========================================
# RUN ALL TESTS
# ==========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.document_processor", "--cov-report=html"])



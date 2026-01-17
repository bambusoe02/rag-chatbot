# RAG Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot powered by local Qwen LLM, ChromaDB, and LangChain.

## Overview

This RAG chatbot allows you to upload documents (PDF, DOCX, TXT, MD) and ask questions about their content. It uses:

- **Local LLM**: Ollama with Qwen2.5:14b-instruct model
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Database**: ChromaDB with persistent storage
- **Framework**: LangChain for orchestration
- **Backend**: FastAPI REST API
- **Frontend**: Streamlit web interface

All processing happens locally - no cloud services or API keys required!

## Features

- 📄 **Document Upload**: Support for PDF, DOCX, TXT, and MD files
- 🔍 **Intelligent Retrieval**: Semantic search using ChromaDB
- 💬 **Chat Interface**: Interactive Q&A with your documents
- 📚 **Source Citation**: See which documents and pages were used
- ⚙️ **Configurable**: Adjust temperature, top-k, and chunk size
- 💾 **Persistent Storage**: Documents and vectors are saved locally
- 🎨 **Modern UI**: Clean Streamlit interface with real-time updates
- 🔒 **Privacy-First**: Everything runs locally, no data leaves your machine

## Prerequisites

- **Python 3.11+** (Python 3.12 recommended)
- **Ollama** installed and running
  ```bash
  # Install Ollama from https://ollama.ai
  # Pull the Qwen model:
  ollama pull qwen2.5:14b-instruct
  ```
- **Virtual environment** (recommended)

## Quick Start

### 1. Clone or Download

```bash
cd rag-chatbot
```

### 2. Check Ollama

Make sure Ollama is running and the model is available:

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama service
# Then pull the model if needed:
ollama pull qwen2.5:14b-instruct
```

### 3. Set Up Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file (optional - uses defaults if not present)
cp .env.example .env
```

### 4. Start the Application

#### Option A: Using the Startup Script (Recommended)

```bash
chmod +x start.sh
./start.sh
```

#### Option B: Manual Start

Terminal 1 - Start Backend:
```bash
cd backend
python main.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Start Frontend:
```bash
streamlit run frontend/app.py
```

### 5. Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Usage

### Uploading Documents

1. Click the file uploader in the sidebar
2. Select a PDF, DOCX, TXT, or MD file
3. Click "Upload" to index the document
4. Wait for processing to complete

### Asking Questions

1. Type your question in the chat input
2. Press Enter or click send
3. View the answer with source citations
4. Expand the "Sources" section to see relevant document excerpts

### Managing Documents

- **View Documents**: All indexed documents appear in the sidebar
- **Delete Document**: Click the 🗑️ button next to a document
- **Clear All**: Use the "Clear All Documents" button in the sidebar
- **View Statistics**: See document and chunk counts in the sidebar

### Configuration

Adjust settings in the sidebar:
- **Temperature** (0.0-1.0): Controls response randomness
- **Top K** (1-10): Number of documents to retrieve
- **Chunk Size**: Currently fixed in config, can be adjusted in `.env`

## API Documentation

The FastAPI backend provides a REST API:

### Endpoints

- `GET /health` - Health check
- `POST /upload` - Upload and index a document
- `GET /documents` - List all indexed documents
- `DELETE /documents/{filename}` - Delete a document
- `POST /chat` - Query the RAG system
- `GET /stats` - Get statistics
- `DELETE /clear` - Clear all documents

### Example API Usage

```bash
# Upload a document
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"

# Ask a question
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'

# List documents
curl "http://localhost:8000/documents"
```

See http://localhost:8000/docs for interactive API documentation.

## Project Structure

```
rag-chatbot/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry
│   ├── config.py                  # Settings with pydantic-settings
│   ├── rag_engine.py              # Core RAG logic
│   ├── document_processor.py      # PDF/DOCX processing
│   ├── vector_store.py            # ChromaDB wrapper
│   └── models.py                  # Pydantic schemas
├── frontend/
│   └── app.py                     # Streamlit UI
├── data/
│   ├── uploads/                   # User documents
│   └── chroma_db/                 # Vector database
├── tests/
│   ├── test_rag.py
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── start.sh                       # Startup script
```

## Configuration

Environment variables (in `.env` or `.env.example`):

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b-instruct
TEMPERATURE=0.1
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5
```

## Architecture Overview

1. **Document Processing**: Uploaded files are processed (PDF/DOCX/TXT/MD) and split into chunks
2. **Embedding Generation**: Chunks are embedded using sentence-transformers
3. **Vector Storage**: Embeddings are stored in ChromaDB with metadata
4. **Query Processing**: User questions are embedded and similar chunks are retrieved
5. **Response Generation**: Retrieved chunks are sent to Qwen LLM via Ollama for answer generation
6. **Source Citation**: Sources are tracked and displayed with answers

## Troubleshooting

### Ollama Connection Error

- **Problem**: "API is not available" or connection errors
- **Solution**: 
  - Ensure Ollama is running: `ollama list`
  - Check the model exists: `ollama show qwen2.5:14b-instruct`
  - Verify the base URL in `.env` matches your Ollama instance

### Model Not Found

- **Problem**: Error loading Qwen model
- **Solution**: Pull the model: `ollama pull qwen2.5:14b-instruct`

### Port Already in Use

- **Problem**: Port 8000 or 8501 already in use
- **Solution**: 
  - Change port in `uvicorn` command: `--port 8001`
  - For Streamlit: `streamlit run app.py --server.port 8502`

### Memory Issues

- **Problem**: Out of memory with large documents
- **Solution**:
  - Reduce `CHUNK_SIZE` in `.env`
  - Use a smaller Qwen model: `qwen2.5:7b-instruct`
  - Process fewer documents at once

### Slow Processing

- **Problem**: Documents take too long to process
- **Solution**:
  - Use GPU for embeddings (if available)
  - Reduce chunk size
  - Use faster CPU-optimized model

### ChromaDB Errors

- **Problem**: Database corruption or errors
- **Solution**: 
  - Delete `data/chroma_db/` directory
  - Restart the application to recreate the database

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

- Type hints throughout
- Google-style docstrings
- Error handling with user-friendly messages
- Logging with loguru

## License

This project is open source and available for personal and commercial use.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style
- Type hints are used
- Docstrings are included
- Tests are updated

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check logs in `logs/` directory

---

**Made with ❤️ using FastAPI, LangChain, ChromaDB, and Ollama**


# Claude RAG Chatbot

🚀 **Production-ready RAG chatbot using Claude API + FastAPI + Next.js**

A complete, enterprise-grade RAG (Retrieval-Augmented Generation) chatbot system with beautiful UI, source citations, and cloud deployment ready.

## ✨ Features

### Backend (FastAPI)
- ✅ Claude Sonnet 4 integration
- ✅ ChromaDB vector store
- ✅ Document parsing (PDF, TXT, MD, DOCX)
- ✅ Smart text chunking with overlap
- ✅ Semantic search with embeddings
- ✅ Source citations
- ✅ RESTful API with OpenAPI docs
- ✅ CORS enabled for frontend

### Frontend (Next.js)
- ✅ Modern UI with Tailwind CSS
- ✅ Real-time chat interface
- ✅ File drag & drop upload
- ✅ Source citations display
- ✅ Document management
- ✅ Responsive design
- ✅ Dark mode support

## 📁 Project Structure

```
claude-rag/
├── claude-rag-backend/     # FastAPI backend
│   ├── main.py             # FastAPI app
│   ├── routers/            # API routes
│   ├── rag/                # RAG components
│   ├── services/           # Utilities
│   ├── sample-docs/        # Sample documents
│   └── requirements.txt
│
└── claude-rag-frontend/     # Next.js frontend
    ├── app/                # Next.js pages
    ├── components/         # UI components
    ├── lib/                # API client
    └── package.json
```

## 🚀 Quick Start

### Backend Setup

```bash
cd claude-rag-backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API Docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd claude-rag-frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## 📚 Usage

1. **Upload Documents**: Go to `/upload` and upload PDF, TXT, MD, or DOCX files
2. **Chat**: Go to `/` and ask questions about your documents
3. **View Documents**: Go to `/documents` to see all uploaded documents

## 🌐 Deployment

### Railway (Backend)
1. Push code to GitHub
2. Connect repository to Railway
3. Add `ANTHROPIC_API_KEY` environment variable
4. Deploy!

See `claude-rag-backend/DEPLOYMENT.md` for detailed instructions.

### Vercel (Frontend)
1. Push code to GitHub
2. Import project in Vercel
3. Add `NEXT_PUBLIC_API_URL` environment variable
4. Deploy!

See `claude-rag-frontend/README.md` for detailed instructions.

## 🔑 Environment Variables

### Backend
- `ANTHROPIC_API_KEY` (required) - Your Anthropic API key
- `ALLOWED_ORIGINS` (optional) - CORS origins, comma-separated

### Frontend
- `NEXT_PUBLIC_API_URL` (required) - Backend API URL

## 📖 API Endpoints

### Upload
- `POST /api/upload/document` - Upload and process document

### Chat
- `POST /api/chat/message` - Send message and get RAG response

### Documents
- `GET /api/documents/list` - List all documents
- `GET /api/documents/stats` - Get collection statistics
- `DELETE /api/documents/{doc_id}` - Delete document

Full API documentation available at `/docs` when backend is running.

## 🎯 Why This Project?

### VS Local RAG (Ollama/Qwen)
- ✅ Cloud deployment (live demo!)
- ✅ Better LLM (Claude > Qwen for RAG)
- ✅ Lower cost ($0.003/1K tokens vs GPU)
- ✅ Faster responses
- ✅ Professional citations
- ✅ Production-ready

### Portfolio Impact
- ✅ Shows Claude API expertise
- ✅ Live demo capability
- ✅ Modern stack (Next.js 15, FastAPI)
- ✅ Real-world use case
- ✅ Enterprise-grade features

## 🛠️ Tech Stack

### Backend
- FastAPI 0.115
- Anthropic SDK 0.39
- ChromaDB 0.5.20
- Sentence Transformers 3.3.1
- Python 3.11+

### Frontend
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui

## 📝 Sample Documents

Sample documents are included in `claude-rag-backend/sample-docs/`:
- `company_policy.txt` - Company policy document
- `product_documentation.md` - Product documentation
- `technical_spec.txt` - Technical specifications

Upload these to test the RAG system!

## 🤝 Contributing

This is a portfolio project, but suggestions and improvements are welcome!

## 📄 License

MIT License - feel free to use this for your own projects!

## 🎉 Next Steps

1. Get your Anthropic API key from https://console.anthropic.com
2. Deploy backend to Railway
3. Deploy frontend to Vercel
4. Upload your documents
5. Start chatting!

---

**Built with ❤️ using Claude API**



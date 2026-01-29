# Quick Start Guide

Get started with RAG Chatbot API in 5 minutes.

## Prerequisites

- Python 3.11+ or Node.js 18+
- API access (register at https://rag-chatbot.com)

## Step 1: Authentication

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "email": "you@example.com",
    "password": "SecurePass123!"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=your_username&password=SecurePass123!"
```

Save the `access_token` from response.

## Step 2: Upload Document
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/document.pdf"
```

Wait for processing (usually 10-30 seconds).

## Step 3: Ask Questions
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main topic of the document?",
    "search_mode": "hybrid"
  }'
```

## Step 4: View Results

Response format:
```json
{
  "answer": "The document discusses...",
  "sources": [
    {
      "filename": "document.pdf",
      "chunk_id": 1,
      "relevance_score": 0.95,
      "text": "..."
    }
  ],
  "performance": {
    "total_ms": 1234,
    "search_ms": 234,
    "llm_ms": 1000
  }
}
```

## Next Steps

- [Full API Reference](/docs)
- [Python Client Example](/docs/examples/python_client.py)
- [JavaScript Client Example](/docs/examples/javascript_client.js)
- [Authentication Guide](/docs/guides/authentication.md)

## Common Issues

### "Not authenticated"
→ Check token is valid and in header

### "Rate limit exceeded"
→ Wait or upgrade plan

### "File too large"
→ Maximum 50MB per file

### "Unsupported file type"
→ Use PDF, DOCX, TXT, or MD

## Support

- 📧 Email: support@rag-chatbot.com
- 💬 Discord: https://discord.gg/ragchatbot
- 🐛 Issues: https://github.com/yourusername/rag-chatbot/issues


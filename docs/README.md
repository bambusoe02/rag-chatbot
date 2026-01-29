# RAG Chatbot API Documentation

Welcome to the RAG Chatbot API documentation!

## 📚 Documentation

### Getting Started
- [Quick Start Guide](guides/quickstart.md) - Get up and running in 5 minutes
- [Authentication](api/authentication.md) - JWT and API key authentication
- [API Reference](http://localhost:8000/docs) - Interactive Swagger UI
- [API Reference (ReDoc)](http://localhost:8000/redoc) - Alternative docs

### Examples
- [Python Client](examples/python_client.py) - Complete Python example
- [JavaScript Client](examples/javascript_client.js) - Complete JS example
- [Postman Collection](postman/collection.json) - Import into Postman

### API Specification
- [OpenAPI YAML](api/openapi.yaml) - OpenAPI 3.0 specification
- [OpenAPI JSON](api/openapi.json) - JSON format

## 🚀 Quick Example
```python
from rag_client import RagChatbotClient

client = RagChatbotClient()
client.login("username", "password")
client.upload_document("document.pdf")
answer = client.ask("What is machine learning?")
print(answer["answer"])
```

## 📖 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List documents
- `DELETE /api/documents/{filename}` - Delete document

### Chat
- `POST /api/chat` - Ask question

### API Keys
- `POST /api/keys` - Create API key
- `GET /api/keys` - List API keys
- `DELETE /api/keys/{key_id}` - Revoke key

### Analytics
- `GET /api/analytics/performance` - Performance metrics
- `GET /api/analytics/popular-queries` - Popular queries
- `GET /api/analytics/satisfaction` - User satisfaction

### Health
- `GET /health/status` - System health
- `GET /metrics` - Prometheus metrics

## 🔐 Authentication

Two methods:
1. **JWT Token** - `Authorization: Bearer <token>`
2. **API Key** - `X-API-Key: <key>`

See [Authentication Guide](api/authentication.md) for details.

## 📊 Rate Limits

- Authenticated: 100 requests/minute
- API Key: Custom limit
- Anonymous: 10 requests/minute

## 🆘 Support

- 📧 Email: support@rag-chatbot.com
- 💬 Discord: https://discord.gg/ragchatbot
- 🐛 GitHub: https://github.com/yourusername/rag-chatbot

## 📜 License

MIT License - see [LICENSE](../LICENSE)


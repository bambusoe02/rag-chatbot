# Authentication Guide

## Overview

RAG Chatbot API supports two authentication methods:
1. **JWT Tokens** - For user-based access
2. **API Keys** - For application/service access

## JWT Authentication

### 1. Register User

**Endpoint:** `POST /api/auth/register`

**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user",
  "created_at": "2025-01-23T10:00:00Z"
}
```

### 2. Login

**Endpoint:** `POST /api/auth/login`

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=john_doe&password=SecurePass123!"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 3. Use Token

Include token in `Authorization` header:
```bash
curl -X GET http://localhost:8000/api/documents \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Python:**
```python
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
headers = {"Authorization": f"Bearer {token}"}

response = requests.get("http://localhost:8000/api/documents", headers=headers)
```

**JavaScript:**
```javascript
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";

const response = await fetch('http://localhost:8000/api/documents', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Token Expiration

- Default expiration: **1 hour**
- Refresh: Login again to get new token
- Store securely: Use environment variables or secure storage

## API Key Authentication

### 1. Create API Key

**Endpoint:** `POST /api/keys`

**Request:**
```bash
curl -X POST http://localhost:8000/api/keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "permissions": ["read", "write"],
    "rate_limit": 1000
  }'
```

**Response:**
```json
{
  "id": "key_abc123xyz",
  "key": "sk_live_abc123xyz789...",
  "name": "Production API Key",
  "permissions": ["read", "write"],
  "rate_limit": 1000,
  "created_at": "2025-01-23T10:00:00Z"
}
```

⚠️ **Important:** Save the `key` value immediately - it's only shown once!

### 2. Use API Key

Include in `X-API-Key` header:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "X-API-Key: sk_live_abc123xyz789..." \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AI?"}'
```

**Python:**
```python
import requests

headers = {
    "X-API-Key": "sk_live_abc123xyz789...",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8000/api/chat",
    json={"question": "What is AI?"},
    headers=headers
)
```

### 3. Manage API Keys

**List keys:**
```bash
GET /api/keys
```

**Revoke key:**
```bash
DELETE /api/keys/{key_id}
```

**Update key:**
```bash
PATCH /api/keys/{key_id}
```

## Security Best Practices

### ✅ DO:
- Store tokens/keys in environment variables
- Use HTTPS in production
- Rotate API keys regularly
- Set appropriate rate limits
- Monitor API key usage
- Revoke unused keys

### ❌ DON'T:
- Commit tokens/keys to git
- Share keys publicly
- Use same key for multiple apps
- Embed keys in client-side code
- Ignore rate limit warnings

## Error Handling

### Invalid Token
```json
{
  "detail": "Invalid authentication credentials",
  "status_code": 401
}
```

### Expired Token
```json
{
  "detail": "Token has expired",
  "status_code": 401
}
```

### Missing Authentication
```json
{
  "detail": "Not authenticated",
  "status_code": 401
}
```

### Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds",
  "status_code": 429,
  "retry_after": 60
}
```

## Rate Limits

Default limits by authentication method:

| Method | Limit | Window |
|--------|-------|--------|
| JWT Token | 100 req/min | Per user |
| API Key | Custom | Per key |
| Anonymous | 10 req/min | Per IP |

Check rate limit status in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706011200
```


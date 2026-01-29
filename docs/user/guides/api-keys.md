# API Keys Guide

Create and manage API keys for programmatic access to RAG Chatbot.

## What Are API Keys?

API keys let you access RAG Chatbot programmatically:
- Integrate with your applications
- Automate workflows
- Build custom interfaces
- Access via Python, JavaScript, or any HTTP client

## Creating API Keys

### Step-by-Step

1. **Login** to your account
2. **Navigate** to "API Keys" in sidebar
3. **Click** "Create New Key"
4. **Fill in:**
   - Name (e.g., "Production API", "Test Integration")
   - Permissions (read, write, admin)
   - Rate limit (requests per hour)
5. **Click** "Generate"
6. **Save the key** immediately (shown only once!)

### Key Information

**Format:**
```
sk_live_abc123xyz789...
```

**Components:**
- `sk_` = Secret key prefix
- `live_` = Environment (live/test)
- `abc123xyz789...` = Unique identifier

⚠️ **Important:** Save key securely - it's only shown once!

## Using API Keys

### In HTTP Requests

**Header format:**
```
X-API-Key: sk_live_abc123xyz789...
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "X-API-Key: sk_live_abc123xyz789..." \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AI?"}'
```

### In Python

```python
import requests

headers = {
    "X-API-Key": "sk_live_abc123xyz789...",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8000/api/chat",
    json={"question": "What is machine learning?"},
    headers=headers
)
```

### In JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'X-API-Key': 'sk_live_abc123xyz789...',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: 'What is machine learning?'
  })
});
```

## Permissions

### Read Permission

**Allows:**
- ✅ View documents
- ✅ Ask questions
- ✅ View analytics
- ✅ List API keys

**Restricts:**
- ❌ Upload documents
- ❌ Delete documents
- ❌ Create API keys
- ❌ Modify settings

### Write Permission

**Allows:**
- ✅ Everything in Read
- ✅ Upload documents
- ✅ Delete documents
- ✅ Create webhooks

**Restricts:**
- ❌ Admin functions
- ❌ User management

### Admin Permission

**Allows:**
- ✅ Everything in Write
- ✅ User management
- ✅ System settings
- ✅ All admin functions

⚠️ **Use with caution!**

## Rate Limits

### Setting Limits

When creating key, set rate limit:
- **Default:** 100 requests/hour
- **Recommended:** Based on your needs
- **Maximum:** Plan-dependent

### Rate Limit Headers

Response includes rate limit info:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706011200
```

### Handling Rate Limits

**When limit exceeded:**
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds",
  "status_code": 429,
  "retry_after": 60
}
```

**Best practices:**
- Monitor `X-RateLimit-Remaining`
- Implement exponential backoff
- Cache responses when possible
- Request higher limits if needed

## Managing API Keys

### List Keys

View all your API keys:
- Name
- Permissions
- Rate limit
- Created date
- Last used
- Status (active/revoked)

### Revoke Keys

**When to revoke:**
- Key compromised
- No longer needed
- Rotating keys
- Security audit

**How to revoke:**
1. Find key in list
2. Click "Revoke" or "Delete"
3. Confirm action
4. Key immediately invalidated

⚠️ **Warning:** Revoked keys cannot be restored!

### Update Keys

**Can update:**
- Name
- Rate limit
- Permissions (upgrade only)

**Cannot update:**
- Key value itself (create new key)
- Created date
- Usage history

## Security Best Practices

### ✅ DO:

- **Store securely** - Environment variables, secrets manager
- **Rotate regularly** - Every 90 days recommended
- **Use different keys** - Separate for dev/staging/prod
- **Set appropriate limits** - Don't set too high
- **Monitor usage** - Check analytics regularly
- **Revoke unused keys** - Clean up old keys

### ❌ DON'T:

- **Commit to git** - Never commit keys
- **Share publicly** - Keep keys private
- **Use same key everywhere** - Separate per app
- **Set unlimited** - Always set reasonable limits
- **Ignore security alerts** - Act on warnings
- **Keep old keys** - Revoke when done

## Common Use Cases

### 1. Automated Document Processing

```python
# Upload documents automatically
for file in documents:
    client.upload_document(file)
    time.sleep(1)  # Rate limit friendly
```

### 2. Integration with Slack

```python
# Answer questions from Slack
@app.route('/slack/command', methods=['POST'])
def slack_command():
    question = request.form['text']
    answer = client.ask(question)
    return answer['answer']
```

### 3. Scheduled Queries

```python
# Daily report generation
def daily_report():
    questions = [
        "What are today's key metrics?",
        "Any critical issues?"
    ]
    for q in questions:
        answer = client.ask(q)
        send_email(answer)
```

### 4. Webhook Integration

```python
# Trigger on document upload
webhook = client.create_webhook(
    url="https://your-app.com/webhook",
    events=["document.uploaded"]
)
```

## Troubleshooting

### "Invalid API key"

**Check:**
1. Key copied correctly (no extra spaces)
2. Key not revoked
3. Using correct header name (`X-API-Key`)
4. Key belongs to your account

### "Rate limit exceeded"

**Solutions:**
1. Wait for reset period
2. Increase rate limit
3. Implement request queuing
4. Cache responses

### "Permission denied"

**Check:**
1. Key has required permissions
2. Endpoint requires specific permission
3. Upgrade key permissions if needed

### Key not working

**Try:**
1. Verify key is active (not revoked)
2. Check key format is correct
3. Test with simple request first
4. Check server logs for errors

## API Key vs JWT Token

| Feature | API Key | JWT Token |
|----------|---------|-----------|
| **Use case** | Applications | User sessions |
| **Expiration** | Never (until revoked) | 1 hour |
| **Scope** | Per-key permissions | User permissions |
| **Rate limit** | Per key | Per user |
| **Best for** | Automation | Interactive use |

## Next Steps

- [API Documentation](../../api/authentication.md)
- [Python Client Example](../../examples/python_client.py)
- [Integration Examples](../tutorials/integrations.md)


# Frequently Asked Questions (FAQ)

Quick answers to common questions.

## General

### What is RAG Chatbot?

RAG (Retrieval-Augmented Generation) Chatbot lets you upload documents and ask questions about them. It combines:
- **Retrieval:** Finding relevant information in your documents
- **Generation:** Using AI to formulate natural language answers

### How does it work?

1. You upload documents (PDF, DOCX, etc.)
2. System processes and indexes them
3. You ask questions in natural language
4. AI finds relevant passages and generates answers
5. Answers include source citations

### Is it free?

- **Cloud:** Free tier available (5GB storage, 100 docs)
- **Self-hosted:** Completely free and open-source
- **Pro plans:** Available with more features

### Is my data secure?

- **Cloud:** Encrypted in transit and at rest
- **Self-hosted:** Complete control, stays on your server
- **Privacy:** Your documents are never used to train AI models

## Account & Authentication

### How do I reset my password?

1. Click "Forgot Password" on login page
2. Enter your email
3. Check email for reset link
4. Click link and set new password

(Self-hosted: Contact your admin)

### Can I change my username?

Not currently. Username is permanent.
You can change display name in settings.

### How do I delete my account?

Settings → Account → Delete Account

⚠️ **Warning:** This deletes all your documents and data permanently!

### What if I forget my email?

Contact support with:
- Username
- Registration date (approximate)
- Last login IP (if known)

## Documents

### What file types are supported?

✅ Supported:
- PDF (.pdf)
- Word (.docx)
- Text (.txt)
- Markdown (.md)

❌ Not supported:
- Old Word (.doc) - convert to .docx
- PowerPoint - export to PDF
- Excel - export to PDF or CSV
- Images - use OCR tool first
- Videos/Audio - transcribe first

### Why is my upload failing?

Common reasons:
1. **File too large** - Max 50MB (split or compress)
2. **Unsupported format** - Convert to PDF/DOCX/TXT
3. **Corrupted file** - Re-download and try again
4. **Password protected** - Remove password first
5. **Network error** - Check internet connection

### How long does processing take?

Typical times:
- Small file (< 1MB): 10-20 seconds
- Medium file (1-10MB): 30-60 seconds
- Large file (10-50MB): 1-2 minutes

Factors:
- File size
- Document complexity
- Server load
- Number of pages

### Can I upload scanned PDFs?

Yes, but quality matters:
- ✅ Clear, high-resolution scans work well
- ⚠️ Low-quality scans may have errors
- ❌ Image-only PDFs need OCR first

**Tip:** Use Adobe Acrobat or similar to OCR first.

### Why can't I upload .doc files?

Old .doc format not supported. Convert to:
- .docx (File → Save As → .docx)
- .pdf (File → Save As → PDF)

### How many documents can I upload?

| Plan | Limit |
|------|-------|
| Free | 100 documents, 5GB total |
| Pro | 1,000 documents, 50GB |
| Enterprise | Unlimited |
| Self-hosted | Unlimited (depends on hardware) |

## Asking Questions

### Why is the answer wrong?

Possible reasons:
1. **Information not in document** - Upload relevant docs
2. **Question unclear** - Rephrase more specifically
3. **Wrong search mode** - Try hybrid or semantic
4. **Low-quality document** - Bad scan or formatting
5. **Complex question** - Break into smaller parts

### How do I get better answers?

See [Asking Questions Guide](../guides/asking-questions.md)

**Quick tips:**
- Be specific
- Provide context
- Use proper search mode
- Check sources cited
- Try rephrasing

### Can it answer questions not in documents?

**No!** RAG Chatbot only uses YOUR uploaded documents.

It **cannot**:
- Search the internet
- Use general knowledge
- Access real-time data
- Read documents you haven't uploaded

### What languages are supported?

**Documents:**
- English (best)
- Spanish, French, German, Italian (good)
- Polish, Portuguese, Dutch (good)
- Many others (varies)

**Interface:**
- English, Polish, German, French

**AI answers in same language as question.**

### Can I ask multiple questions at once?

Better to ask one at a time:

❌ "What's the revenue, who's the CEO, and when's the launch?"

✅ Three separate questions:
1. "What was the revenue?"
2. "Who is the CEO?"
3. "When is the product launch?"

## Search & Performance

### What's the difference between search modes?

**Hybrid (default):**
- Best overall
- Combines semantic + keyword
- Use for most questions

**Semantic:**
- Understands meaning
- Good for concepts
- Finds related info

**Keyword:**
- Exact word matching
- Good for names/dates/numbers
- Technical terms

See [Search Modes Guide](../guides/search-modes.md)

### Why are results slow?

Typical response times:
- Simple query: 1-3 seconds
- Complex query: 3-5 seconds
- Heavy load: 5-10 seconds

**If consistently > 10 seconds:**
- Check internet speed
- Try smaller documents
- Reduce top_k results
- Contact support

### How accurate are the answers?

Accuracy depends on:
- ✅ Document quality (80-95% for good docs)
- ✅ Question clarity (specific = better)
- ✅ Search mode (hybrid usually best)
- ❌ Document relevance (must contain answer)

**Always check cited sources!**

## API & Integration

### How do I get an API key?

1. Login to account
2. Go to "API Keys" page
3. Click "Create New Key"
4. Name your key
5. Set permissions
6. Save key (shown once!)

### What can I do with the API?

Everything you can do in UI:
- Upload documents
- Ask questions
- View analytics
- Manage documents
- Configure webhooks

See [API Documentation](../../api/authentication.md)

### Are there rate limits?

Yes:
- **Free:** 100 requests/hour
- **Pro:** 1,000 requests/hour
- **Enterprise:** Custom
- **Self-hosted:** Configure yourself

## Billing & Plans

### How do I upgrade my plan?

Settings → Subscription → Upgrade

### Can I downgrade?

Yes, but:
- Takes effect next billing cycle
- Must be within new plan's limits
- Extra documents must be deleted

### What payment methods are accepted?

- Credit/Debit card (Visa, Mastercard, Amex)
- PayPal (on annual plans)
- Wire transfer (Enterprise only)

### Can I get a refund?

- 30-day money-back guarantee
- Pro-rated refunds for annual plans
- No refund for usage-based fees

### Do you offer discounts?

- ✅ Annual plans (save 20%)
- ✅ Educational (50% off with .edu email)
- ✅ Non-profit (apply via form)
- ✅ Volume (Enterprise custom pricing)

## Technical Issues

### The app won't load

**Try:**
1. Refresh page (Ctrl+R / Cmd+R)
2. Clear browser cache
3. Try incognito/private mode
4. Try different browser
5. Check https://status.rag-chatbot.com

### I'm getting errors

**First:**
1. Screenshot the error
2. Note what you were doing
3. Check [Common Issues](common-issues.md)
4. Try again

**Then:**
- Email support with screenshot
- Include error message
- Describe steps to reproduce

### Can't login

**Reset password:**
Login page → "Forgot Password"

**Still issues:**
- Check username spelling
- Try incognito mode
- Clear cookies
- Contact support

### Page is stuck loading

**Try:**
1. Wait 30 seconds (might be slow)
2. Refresh page
3. Check internet connection
4. Try different browser
5. Clear cache

## Self-Hosted

### What are the system requirements?

**Minimum:**
- 8GB RAM
- 4 CPU cores
- 20GB disk space
- Linux/macOS/Windows (WSL2)

**Recommended:**
- 16GB RAM
- 8 CPU cores
- 50GB SSD
- GPU (optional, for faster LLM)

### How do I update?
```bash
cd rag-chatbot
git pull
docker-compose down
docker-compose up -d --build
```

### Can I use a different LLM?

Yes! Edit `docker-compose.yml`:
```yaml
environment:
  - OLLAMA_MODEL=llama2:13b
  # or mistral, codellama, etc.
```

### How do I backup my data?
```bash
./backup.sh
```

Backs up:
- Database
- Uploaded documents
- Vector embeddings
- Configuration

See [Backup Guide](../../README.md#backup)

## Still Have Questions?

### Contact Support

📧 **Email:** support@rag-chatbot.com
- Response time: 24-48 hours
- Include: username, error details, screenshots

💬 **Discord:** https://discord.gg/ragchatbot
- Community support
- Real-time help
- Feature discussions

🐛 **Bug Reports:** https://github.com/yourusername/rag-chatbot/issues
- Technical issues
- Feature requests
- Public discussion

📚 **Documentation:** https://docs.rag-chatbot.com
- Complete guides
- Video tutorials
- API reference

### Business Inquiries

💼 **Sales:** sales@rag-chatbot.com
- Enterprise plans
- Custom deployment
- Volume licensing

🤝 **Partnerships:** partners@rag-chatbot.com
- Integration partners
- Resellers
- White label


# Document Management Guide

Complete guide to uploading, organizing, and managing your documents.

## Uploading Documents

### Step-by-Step

1. **Click Upload Button**
   - Sidebar: "📄 Upload Documents"
   - Or drag & drop files onto page

2. **Select Files**
   - Single file: Click "Choose file"
   - Multiple files: Select multiple in dialog
   - Or: Drag multiple files at once

3. **Wait for Processing**
   - Small files: 10-20 seconds
   - Large files: 30-60 seconds
   - Very large: Up to 2 minutes

4. **Confirmation**
   - Green ✅ = Success
   - Red ❌ = Error (check message)

### Supported Formats

| Format | Extension | Max Size | Notes |
|--------|-----------|----------|-------|
| PDF | .pdf | 50 MB | Most common, best for scanned docs |
| Word | .docx | 50 MB | Modern Word format only |
| Text | .txt | 50 MB | Plain text, fast processing |
| Markdown | .md | 50 MB | Great for technical docs |

### What Happens During Upload

1. **Validation** - File type and size checked
2. **Upload** - File transferred to server
3. **Text Extraction** - Content extracted from file
4. **Chunking** - Split into manageable pieces
5. **Embedding** - Create vector representations
6. **Indexing** - Add to search database

**Total time:** Usually 30 seconds, varies by size

### Upload Tips

**✅ Best Practices:**
- Upload complete documents, not excerpts
- Use descriptive filenames
- Group related documents
- PDF quality matters (clear scans work best)
- Wait for previous upload to finish

**❌ Common Mistakes:**
- Uploading huge files (split them up)
- Corrupted or password-protected PDFs
- Images without text (use OCR first)
- Uploading executables (.exe, .sh)

## Viewing Your Documents

### Document List

In sidebar, see all uploaded documents:
- 📄 Filename
- 📅 Upload date
- 📊 File size
- ✅ Processing status

### Document Details

Click on document name to see:
- Number of chunks created
- Word count
- Upload timestamp
- Processing time
- Last queried

### Search Documents

Filter your document list:
```
Search box → Type filename or keyword
```

## Organizing Documents

### Naming Convention

Use descriptive names:
```
✅ GOOD:
- Q3_2024_Financial_Report.pdf
- Customer_Feedback_Jan_2024.docx
- Product_Roadmap_v2.txt

❌ BAD:
- document.pdf
- file1.txt
- untitled.docx
```

### Folder Structure (Self-Hosted)

Documents stored in:
```
data/uploads/user_<id>/
├── document1.pdf
├── document2.docx
└── document3.txt
```

### Tags and Metadata (Coming Soon)

Future features:
- Custom tags
- Categories
- Collections
- Sharing

## Deleting Documents

### How to Delete

1. Find document in list
2. Click 🗑️ (trash icon)
3. Confirm deletion
4. Document and embeddings removed

### What Gets Deleted

✅ Original file
✅ Text chunks
✅ Vector embeddings
✅ Metadata
❌ Chat history (kept for analytics)

### Bulk Delete

Delete multiple documents:
1. Select documents (checkboxes)
2. Click "Delete Selected"
3. Confirm

⚠️ **Warning: Deletion is permanent!**

## Document Limits

### File Size Limits

| Plan | Max File | Max Total |
|------|----------|-----------|
| Free | 50 MB | 5 GB |
| Pro | 100 MB | 50 GB |
| Enterprise | 500 MB | Unlimited |

### Document Count Limits

| Plan | Max Documents |
|------|---------------|
| Free | 100 |
| Pro | 1,000 |
| Enterprise | Unlimited |

### Self-Hosted

No limits! Depends only on your hardware.

## Advanced Features

### Batch Upload

Upload entire folder:
```bash
# Using API
for file in folder/*.pdf; do
  curl -X POST http://localhost:8000/api/documents/upload \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$file"
done
```

### Programmatic Upload

**Python:**
```python
from rag_client import RagChatbotClient

client = RagChatbotClient()
client.login("user", "pass")

# Upload multiple files
import os
for filename in os.listdir("docs/"):
    if filename.endswith(".pdf"):
        client.upload_document(f"docs/{filename}")
```

**JavaScript:**
```javascript
const client = new RagChatbotClient();
await client.login('user', 'pass');

// Upload from file input
const files = document.getElementById('fileInput').files;
for (let file of files) {
  await client.uploadDocument(file);
}
```

### Document Versioning (Pro)

Keep track of document versions:
- Upload new version with same name
- Access previous versions
- See change history
- Revert to older version

## Troubleshooting

### Upload Fails

**"File too large"**
→ Split into smaller files or upgrade plan

**"Unsupported file type"**
→ Convert to PDF, DOCX, TXT, or MD

**"Processing failed"**
→ File might be corrupted, try re-downloading

**"Timeout error"**
→ Large file, try again or split it

### Processing Stuck

If processing takes >5 minutes:
1. Refresh page
2. Check file size
3. Try uploading again
4. Contact support if persists

### Can't Find Document

- Check you're logged in as correct user
- Use search box to filter
- Check if upload completed successfully
- Look in analytics for upload confirmation

## Best Practices

### For Best Results

1. **Quality over quantity** - Upload relevant docs only
2. **Clear formatting** - Well-formatted docs work better
3. **Regular updates** - Keep documents current
4. **Organize systematically** - Use consistent naming
5. **Monitor storage** - Check usage regularly

### Document Preparation

Before uploading:
- ✅ Remove password protection
- ✅ Ensure text is selectable (not image-only PDF)
- ✅ Split very large files
- ✅ Use descriptive filenames
- ✅ Check for sensitive information

## FAQ

**Q: Can I upload scanned PDFs?**
A: Yes, but OCR quality affects results. Use clear scans.

**Q: Do you store my documents?**
A: Yes, on our servers (cloud) or your server (self-hosted).

**Q: Are documents private?**
A: Yes, only you can access your documents.

**Q: Can I share documents with others?**
A: Coming soon in Pro plan!

**Q: What languages are supported?**
A: All major languages, but English works best.

## Next Steps

- [Asking Questions Guide](asking-questions.md)
- [Search Modes Explained](search-modes.md)
- [Build a Knowledge Base Tutorial](../tutorials/knowledge-base.md)


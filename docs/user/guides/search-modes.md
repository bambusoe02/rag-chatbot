# Search Modes Explained

Understanding when to use each search mode for best results.

## Overview

RAG Chatbot offers three search modes, each optimized for different types of questions:

1. **Hybrid** (Default) - Best overall
2. **Semantic** - Understands meaning
3. **Keyword** - Exact matching

## 🔄 Hybrid Search (Recommended)

### What It Does

Combines semantic understanding with keyword matching for comprehensive results.

### Best For

- ✅ Most questions (default choice)
- ✅ General queries
- ✅ When unsure which mode to use
- ✅ Complex questions needing both meaning and exact terms

### How It Works

1. **Semantic search** finds conceptually related content
2. **Keyword search** finds exact word matches
3. **Combines** results with weighted scoring
4. **Ranks** by relevance

### Example

**Question:** "What are the benefits of machine learning?"

**Finds:**
- Documents with "machine learning" (keyword)
- Documents about "AI advantages" (semantic)
- Documents mentioning "ML benefits" (both)

### When to Use

**✅ Use Hybrid when:**
- Starting a new query
- Question has both concepts and specific terms
- Want comprehensive coverage
- Not sure which mode fits

**❌ Avoid Hybrid when:**
- Need exact phrase matching only
- Very technical/specific terminology
- Performance is critical (slightly slower)

## 🧠 Semantic Search

### What It Does

Understands meaning and context, finds related information even if words differ.

### Best For

- ✅ Conceptual questions
- ✅ Questions phrased differently than document
- ✅ Finding related topics
- ✅ Understanding context

### How It Works

1. Converts question to vector embedding
2. Compares with document embeddings
3. Finds semantically similar content
4. Ranks by meaning similarity

### Example

**Question:** "How does this improve user experience?"

**Finds:**
- "enhances usability" (same meaning)
- "better for customers" (related concept)
- "improves interface" (similar idea)
- Even if document doesn't use "user experience"

### When to Use

**✅ Use Semantic when:**
- Asking about concepts/ideas
- Question uses different words than document
- Looking for related information
- Understanding "why" or "how"

**❌ Avoid Semantic when:**
- Need exact word matches
- Looking for specific names/dates
- Technical jargon
- Acronyms or codes

## 🔍 Keyword Search

### What It Does

Finds exact word and phrase matches in documents.

### Best For

- ✅ Specific terms
- ✅ Names, dates, numbers
- ✅ Technical jargon
- ✅ Acronyms
- ✅ Exact phrases

### How It Works

1. Extracts keywords from question
2. Searches document text directly
3. Matches exact words/phrases
4. Ranks by frequency and position

### Example

**Question:** "Find mentions of GDPR compliance"

**Finds:**
- Only documents with "GDPR" and "compliance"
- Exact phrase matches
- Case-sensitive matching
- Won't find "data protection regulation" (different words)

### When to Use

**✅ Use Keyword when:**
- Looking for specific terms
- Names, dates, IDs, codes
- Technical specifications
- Exact phrase needed
- Fast results required

**❌ Avoid Keyword when:**
- Question uses synonyms
- Looking for concepts
- Need related information
- Question phrased differently

## Comparison Table

| Feature | Hybrid | Semantic | Keyword |
|---------|--------|----------|---------|
| **Speed** | Medium | Slower | Fastest |
| **Accuracy** | High | High | Medium |
| **Coverage** | Best | Good | Limited |
| **Concepts** | ✅ | ✅✅ | ❌ |
| **Exact Terms** | ✅ | ❌ | ✅✅ |
| **Synonyms** | ✅ | ✅✅ | ❌ |
| **Best For** | Most questions | Concepts | Specific terms |

## Quick Decision Guide

### Start Here:
```
Try Hybrid first (default)
```

### If answer is too general:
```
→ Try Keyword for specific terms
```

### If answer misses related info:
```
→ Try Semantic for concepts
```

### If answer seems wrong:
```
→ Try different mode
→ Rephrase question
→ Check document contains answer
```

## Real-World Examples

### Example 1: Research Paper

**Question:** "What methodology did they use?"

**Hybrid:** ✅ Finds "methodology", "approach", "method"
**Semantic:** ✅ Finds "research design", "study approach"
**Keyword:** ⚠️ Only if document says "methodology"

**Best:** Hybrid or Semantic

### Example 2: Technical Documentation

**Question:** "What is the API endpoint for user authentication?"

**Hybrid:** ✅ Good coverage
**Semantic:** ⚠️ Might miss exact endpoint
**Keyword:** ✅✅ Best - finds exact "API endpoint"

**Best:** Keyword

### Example 3: Business Report

**Question:** "What are the main risks?"

**Hybrid:** ✅✅ Best - finds "risks", "concerns", "challenges"
**Semantic:** ✅ Good - understands risk concept
**Keyword:** ⚠️ Only if document says "risks"

**Best:** Hybrid

### Example 4: Legal Document

**Question:** "When does the contract expire on 2024-12-31?"

**Hybrid:** ✅ Good
**Semantic:** ❌ Won't find exact date
**Keyword:** ✅✅ Best - exact date match

**Best:** Keyword

## Advanced Tips

### Combine Modes

For complex questions:
1. Start with Hybrid (overview)
2. Use Keyword (specific facts)
3. Use Semantic (related concepts)

### Mode Selection Strategy

**First query:** Always Hybrid
**Follow-up:** Choose based on first result
- Too general → Keyword
- Missing related info → Semantic
- Good result → Stay Hybrid

### Performance Considerations

**Speed ranking:**
1. Keyword (fastest)
2. Hybrid (medium)
3. Semantic (slowest)

**For large knowledge bases:**
- Keyword: < 1 second
- Hybrid: 1-3 seconds
- Semantic: 2-5 seconds

## Troubleshooting

### "No results found" in one mode

**Try:**
1. Different search mode
2. Broader question
3. Check document contains answer
4. Verify document uploaded correctly

### Results seem wrong

**Check:**
1. Are you using right mode for question type?
2. Try alternative mode
3. Rephrase question
4. Check source documents

### Too many irrelevant results

**Solutions:**
1. Be more specific in question
2. Use Keyword for exact terms
3. Add context/constraints
4. Filter by document (if multiple)

## Best Practices

### ✅ DO:
- Start with Hybrid (default)
- Switch modes if results poor
- Use Keyword for exact terms
- Use Semantic for concepts
- Experiment to find what works

### ❌ DON'T:
- Always use same mode
- Ignore mode differences
- Use Keyword for concepts
- Use Semantic for exact terms
- Forget to try alternatives

## Next Steps

- [Asking Effective Questions](asking-questions.md)
- [Advanced Queries Tutorial](../tutorials/advanced-queries.md)
- [Building a Knowledge Base](../tutorials/knowledge-base.md)


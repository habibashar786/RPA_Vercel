# Academic API Setup Guide for ResearchAI

## Overview

ResearchAI uses multiple academic databases to fetch research papers:
- **Semantic Scholar** - Main source for paper search, citations, and references
- **arXiv** - Preprint server for CS, Physics, Math, etc.
- **Papers With Code** - Papers with associated code implementations ⭐ NEW
- **Crossref** - DOI resolution and metadata
- **Frontiers** - Open access journals (optional)
- **PubMed** - Medical/life sciences papers (optional)

## Good News: API Keys are Optional!

**Semantic Scholar**, **arXiv**, and **Papers With Code** work without API keys:

| Service | Without API Key | With API Key |
|---------|-----------------|--------------|
| Semantic Scholar | 100 requests/5 min | 10,000 requests/day |
| arXiv | 3 requests/second | Same (no API key needed) |
| Papers With Code | Free, no limit | Same (no API key needed) |
| Crossref | 50 requests/second | Same (uses "polite" pool) |

For development and moderate usage, you don't need any API keys!

---

## 1. Semantic Scholar API Key (Optional - For Higher Rate Limits)

### When You Need It
- If you're generating many proposals quickly
- If you get rate limit errors (HTTP 429)

### How to Get It
1. Go to: https://www.semanticscholar.org/product/api
2. Click "Request API Key"
3. Fill out the form (academic/research use)
4. Wait for approval (usually instant to a few hours)

### Add to .env
```env
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
```

---

## 2. arXiv API (No Key Required)

arXiv doesn't require an API key. Just follow their rate limits:
- Maximum 3 requests per second
- Be polite with delays between requests

The system is already configured to respect these limits.

---

## 3. Papers With Code API ⭐ NEW

Papers With Code provides access to academic papers WITH code implementations. This is invaluable for:
- Finding reproducible research
- Getting GitHub repositories for papers
- Accessing benchmark results (SOTA)
- Finding datasets used in papers

### No API Key Required!
The API is completely free and open.

### Python Client (Automatically Used)
ResearchAI uses the official Python client for best results:
```bash
pip install paperswithcode-client
```

### Features Available
- Search papers by title, abstract, or topic
- Find code repositories for papers
- Get state-of-the-art results
- Browse methods and datasets

### Example Usage (Internal)
```python
from src.mcp_servers.papers_with_code_mcp import PapersWithCodeMCP

pwc = PapersWithCodeMCP()
results = await pwc.search_papers("transformer", limit=10)

for paper in results.data:
    print(f"{paper['title']}")
    print(f"  Has Code: {paper['has_code']}")
    print(f"  Code URL: {paper['code_url']}")
    print(f"  Stars: {paper['code_stars']}")
```

---

## 4. Crossref API (No Key Required)

Crossref uses a "polite pool" system. Add your email to get better rate limits:

### Add to .env (Recommended)
```env
CROSSREF_EMAIL=your.email@example.com
```

This puts you in the "polite pool" with faster responses.

---

## 5. Frontiers API Key (Optional)

For accessing Frontiers journals:

### How to Get It
1. Go to: https://www.frontiersin.org/api
2. Create an account
3. Request API access

### Add to .env
```env
FRONTIERS_API_KEY=your_api_key_here
```

---

## 6. PubMed API Key (Optional - For Medical Research)

For medical/life sciences research:

### How to Get It
1. Go to: https://www.ncbi.nlm.nih.gov/account/
2. Create an NCBI account
3. Go to Settings > API Key Management
4. Generate an API key

### Add to .env
```env
PUBMED_API_KEY=your_api_key_here
```

---

## Testing Your Setup

After configuring, test the APIs:

```bash
# Test all academic APIs
curl "http://localhost:8001/api/test/academic-search?query=transformer%20neural%20network&limit=5"
```

Expected response:
```json
{
  "query": "transformer neural network",
  "semantic_scholar": {"status": "success", "papers_found": 5, ...},
  "arxiv": {"status": "success", "papers_found": 5, ...},
  "papers_with_code": {"status": "success", "papers_found": 5, ...},
  "overall_status": "ready",
  "sources_online": 3
}
```

---

## Installing Dependencies

Run this command to install all academic API clients:

```bash
pip install paperswithcode-client semanticscholar arxiv httpx --break-system-packages
```

Or if using virtual environment:
```bash
pip install paperswithcode-client semanticscholar arxiv httpx
```

---

## Troubleshooting

### "Rate limit exceeded" (HTTP 429)
- Wait a few minutes and try again
- Consider getting a Semantic Scholar API key

### "Connection refused"
- Check your internet connection
- Some networks block API access

### No papers found
- Try a broader search query
- Check that MCP servers are enabled in `config/mcp_config.yaml`

### Papers With Code client not found
- Install: `pip install paperswithcode-client`
- The system will fallback to HTTP API if client is not installed

### Papers not in English
- The system filters for English papers by default
- Check `result_processing.filtering.languages` in config

---

## Current Configuration Status

Check your current configuration:

```bash
# View enabled MCP servers
grep "enabled:" config/mcp_config.yaml
```

Expected output:
```yaml
semantic_scholar:
  enabled: true
arxiv:
  enabled: true
papers_with_code:
  enabled: true
crossref:
  enabled: true
frontiers:
  enabled: false  # Optional
pubmed:
  enabled: false  # Optional
```

---

## Benefits of Papers With Code Integration

1. **Reproducibility**: Find papers that have actual code implementations
2. **Quality Signal**: Papers with code are often higher quality
3. **GitHub Stars**: Sort by popularity/community validation
4. **Framework Info**: Know if code is PyTorch, TensorFlow, etc.
5. **SOTA Results**: Access benchmark leaderboards
6. **Datasets**: Find datasets used in papers

---

## Support

If you encounter issues:
1. Check the backend logs for error messages
2. Test individual APIs using the test endpoint
3. Verify your API keys are correctly set in `.env`

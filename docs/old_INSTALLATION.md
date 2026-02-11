# 🚀 QUICK INSTALLATION GUIDE

**Issue:** `ModuleNotFoundError: No module named 'loguru'`  
**Solution:** Install required dependencies

---

## Option 1: Quick Install (Recommended)

### For Windows (Git Bash/PowerShell):

```bash
# Install minimal dependencies
pip install loguru pydantic python-dotenv pyyaml anthropic openai httpx requests redis pytest pytest-asyncio semanticscholar arxiv
```

### One-liner:
```bash
pip install loguru==0.7.2 pydantic==2.8.2 python-dotenv==1.0.1 pyyaml==6.0.2 anthropic==0.34.2 openai==1.42.0 httpx==0.27.2 requests==2.32.3 redis==5.0.8 pytest==8.3.2 pytest-asyncio==0.24.0 semanticscholar==0.8.4 arxiv==2.1.3
```

---

## Option 2: Use Setup Script

### Windows:
```bash
# Run the setup batch file
setup_minimal.bat
```

### Linux/Mac:
```bash
# Make executable
chmod +x setup_minimal.sh

# Run
./setup_minimal.sh
```

---

## Option 3: Install from Requirements File

### Minimal (Recommended for Testing):
```bash
pip install -r requirements-minimal.txt
```

### Full (All Features):
```bash
pip install -r requirements.txt
```

**Note:** Full installation may take 10-15 minutes and requires ~2GB of disk space.

---

## Verify Installation

```bash
# Test imports
python -c "import loguru; print('✅ loguru installed')"
python -c "import pydantic; print('✅ pydantic installed')"
python -c "import anthropic; print('✅ anthropic installed')"

# Run verification script
python verify_agents.py
```

**Expected Output:**
```
✅ loguru installed
✅ pydantic installed
✅ anthropic installed
```

---

## Run Tests

```bash
# Run integration tests
python tests/test_all_agents_integration.py
```

**Expected Output:**
```
============================================================
MULTI-AGENTIC RESEARCH PROPOSAL SYSTEM - INTEGRATION TESTS
============================================================
...
✅ ALL TESTS PASSED!
```

---

## Troubleshooting

### Issue: `pip` not found
```bash
# Try python -m pip instead
python -m pip install loguru pydantic python-dotenv
```

### Issue: Permission denied
```bash
# Use --user flag
pip install --user loguru pydantic python-dotenv
```

### Issue: SSL certificate error
```bash
# Use trusted host
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org loguru
```

### Issue: Virtual environment
```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Then install
pip install -r requirements-minimal.txt
```

---

## After Installation

1. **Configure Environment Variables**
   ```bash
   # Copy example file
   cp .env.example .env
   
   # Edit .env with your API keys
   nano .env  # or use any text editor
   ```

2. **Start Redis (if needed)**
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:latest
   
   # Verify
   redis-cli ping
   # Should return: PONG
   ```

3. **Run Tests**
   ```bash
   python tests/test_all_agents_integration.py
   ```

---

## Package Overview

### Essential Packages (Minimal Install):
- **loguru** (0.7.2) - Logging
- **pydantic** (2.8.2) - Data validation
- **python-dotenv** (1.0.1) - Environment variables
- **pyyaml** (6.0.2) - YAML parsing
- **anthropic** (0.34.2) - Claude API
- **openai** (1.42.0) - GPT API (fallback)
- **httpx** (0.27.2) - HTTP client
- **requests** (2.32.3) - HTTP library
- **redis** (5.0.8) - State management
- **pytest** (8.3.2) - Testing
- **pytest-asyncio** (0.24.0) - Async testing
- **semanticscholar** (0.8.4) - Academic search
- **arxiv** (2.1.3) - ArXiv API

**Total Size:** ~100-150 MB

### Full Install Includes:
- Document generation (python-docx, reportlab)
- Data processing (pandas, numpy)
- Visualization (plotly, matplotlib)
- NLP tools (spacy, nltk)
- And 60+ more packages

**Total Size:** ~2 GB

---

## Installation Time Estimates

| Option | Time | Size | Use Case |
|--------|------|------|----------|
| **Minimal** | 1-2 min | 150 MB | Testing, development |
| **Full** | 10-15 min | 2 GB | Production, all features |

---

## Quick Start After Installation

```bash
# 1. Verify installation
python verify_agents.py

# 2. Run integration tests
python tests/test_all_agents_integration.py

# 3. Check configuration
python -c "from src.core.config import Config; print(Config.load())"

# 4. Test LLM connection (requires API key)
python -c "from src.core.llm_provider import LLMProvider; print('LLM ready!')"
```

---

## Need Help?

- **Check logs:** Look for error messages
- **Verify Python version:** Should be 3.9+
- **Check internet connection:** For package downloads
- **Review documentation:** See `QUICK_START.md`

---

**Installation complete?** ✅  
**Next:** Run `python tests/test_all_agents_integration.py`

🚀 **Ready to go!**

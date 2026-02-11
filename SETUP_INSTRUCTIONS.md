# ResearchAI - Complete Setup & Running Instructions

## Quick Start (5 minutes)

### Step 1: Open PowerShell in the project directory
```powershell
cd C:\Users\ashar\Documents\rpa_claude_desktop
```

### Step 2: Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Run Diagnostics (Optional but Recommended)
```powershell
python diagnose.py
```

### Step 4: Start Backend Server
```powershell
uvicorn src.api.main:app --reload --port 8001 --host 0.0.0.0
```

### Step 5: Open New Terminal for Frontend
```powershell
cd C:\Users\ashar\Documents\rpa_claude_desktop\frontend
npm run dev
```

### Step 6: Access the Application
- **Frontend Dashboard**: http://localhost:3000/dashboard
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

---

## Testing the System

### Quick API Test
```powershell
cd C:\Users\ashar\Documents\rpa_claude_desktop
.\.venv\Scripts\Activate.ps1
python test_api_quick.py
```

### Test Individual Endpoints in Browser:
1. **Health**: http://localhost:8001/health
2. **System Status**: http://localhost:8001/api/system/status
3. **LLM Test**: http://localhost:8001/api/test/llm
4. **Academic Search Test**: http://localhost:8001/api/test/academic-search?query=AI&limit=3

---

## Troubleshooting

### Issue: "Module not found" errors
```powershell
# Make sure you're in the project root
cd C:\Users\ashar\Documents\rpa_claude_desktop

# Activate venv
.\.venv\Scripts\Activate.ps1

# Set PYTHONPATH
$env:PYTHONPATH = "$PWD"
```

### Issue: Backend won't start
```powershell
# Check if port 8001 is in use
netstat -ano | findstr :8001

# Kill the process if needed
taskkill /PID <PID> /F

# Try starting again
uvicorn src.api.main:app --reload --port 8001
```

### Issue: Frontend won't connect to backend
1. Make sure backend is running on port 8001
2. Check CORS settings in backend
3. Verify API_URL in frontend/src/services/api.ts is set to http://localhost:8001

### Issue: LLM not responding
1. Check your ANTHROPIC_API_KEY in .env
2. Test the LLM endpoint: http://localhost:8001/api/test/llm
3. Check backend logs for API errors

### Issue: Redis connection error
The system is configured to use **in-memory state** (no Redis required).
If you still see Redis errors:
```powershell
# Set environment variable
$env:USE_INMEMORY_STATE = "1"
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ResearchAI System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐         ┌─────────────────────────────┐   │
│  │   Frontend  │  HTTP   │         Backend API          │   │
│  │  Next.js    │◄───────►│    FastAPI (Port 8001)      │   │
│  │  Port 3000  │         │                              │   │
│  └─────────────┘         └──────────────┬──────────────┘   │
│                                         │                   │
│                          ┌──────────────┴──────────────┐   │
│                          │       Job Store              │   │
│                          │    (In-Memory Queue)         │   │
│                          └──────────────┬──────────────┘   │
│                                         │                   │
│          ┌──────────────────────────────┼────────────────┐ │
│          │                              │                │ │
│   ┌──────▼──────┐   ┌───────────┐   ┌──▼─────────┐      │ │
│   │ LLM Provider│   │  Academic │   │   State    │      │ │
│   │   (Claude)  │   │   APIs    │   │  Manager   │      │ │
│   └─────────────┘   └───────────┘   └────────────┘      │ │
│                                                          │ │
│   11 AI Agents:                                          │ │
│   - Literature Review    - Structure Formatting          │ │
│   - Introduction         - Front Matter                  │ │
│   - Methodology         - Reference Citation              │ │
│   - Risk Assessment     - Visualization                  │ │
│   - Quality Assurance   - Final Assembly                 │ │
│   - Methodology Optimizer                                │ │
│                                                          │ │
└──────────────────────────────────────────────────────────┘
```

---

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/system/status` | GET | Detailed system status |
| `/api/proposals/generate` | POST | Start proposal generation |
| `/api/proposals/jobs/{job_id}` | GET | Get job status |
| `/api/proposals/jobs/{job_id}/result` | GET | Get completed proposal |
| `/api/proposals/jobs/{job_id}/stream` | GET | SSE progress stream |
| `/api/test/llm` | GET | Test LLM connection |
| `/api/test/academic-search` | GET | Test academic APIs |
| `/agents` | GET | List all agents |

---

## Environment Variables (.env)

Key variables that should be configured:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...     # Your Anthropic API key

# Optional
OPENAI_API_KEY=sk-...            # OpenAI fallback
DEFAULT_LLM_PROVIDER=anthropic   # Primary LLM
DEFAULT_MODEL=claude-3-5-sonnet-20240620

# State Management
USE_INMEMORY_STATE=1             # No Redis needed

# API
API_PORT=8001
DEBUG=true
```

---

## Next Steps After Setup

1. **Test the API**: Run `python test_api_quick.py`
2. **Open Dashboard**: Go to http://localhost:3000/dashboard
3. **Generate a Proposal**: Fill in the form and click "Generate Proposal"
4. **Monitor Progress**: Watch the progress bar update in real-time
5. **Download Result**: Once complete, download the PDF/DOCX

---

## Support

If you encounter issues:
1. Check the backend terminal for error logs
2. Run the diagnostic script: `python diagnose.py`
3. Verify API endpoints work via browser or curl
4. Check that all environment variables are set correctly

---

Last Updated: December 15, 2025
Version: 1.0.0

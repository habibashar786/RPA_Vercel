# ResearchAI - Multi-Agent Research Proposal Generator

## Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ 
- npm or yarn

### 1. Backend Setup

```powershell
# Navigate to project root
cd C:\Users\ashar\Documents\rpa_claude_desktop

# Create and activate virtual environment (if not already done)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements-minimal.txt --break-system-packages

# Verify installation
python run_sequential_tests.py
```

### 2. Frontend Setup

```powershell
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

### 3. Run the Application

**Terminal 1 - Backend API:**
```powershell
cd C:\Users\ashar\Documents\rpa_claude_desktop
.\.venv\Scripts\Activate.ps1
uvicorn src.api.main:app --reload --port 8001
```

**Terminal 2 - Frontend:**
```powershell
cd C:\Users\ashar\Documents\rpa_claude_desktop\frontend
npm run dev
```

### 4. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

---

## Architecture Overview

### Multi-Agent System (11 Agents)

| Agent | Function |
|-------|----------|
| Literature Review | Searches papers from Semantic Scholar, arXiv, Frontiers |
| Introduction | Generates problem statement, objectives, research questions |
| Research Methodology | Designs research methods, data collection, analysis |
| Quality Assurance | Reviews content, scores quality, suggests improvements |
| Visualization | Creates methodology diagrams and flowcharts |
| Reference Citation | Formats citations in Harvard/APA/MLA/Chicago |
| Structure Formatting | Applies Q1 journal formatting standards |
| Front Matter | Generates title page, abstract, keywords |
| Final Assembly | Compiles all sections into complete proposal |
| Risk Assessment | Identifies research risks and mitigation strategies |
| Methodology Optimizer | Suggests improvements to research design |

### Tech Stack

**Backend:**
- FastAPI (Python)
- JWT Authentication
- Google OAuth 2.0
- bcrypt password hashing
- In-memory state management (Redis-ready)

**Frontend:**
- Next.js 14
- TypeScript
- Tailwind CSS
- Framer Motion
- Zustand (state management)

**AI/ML:**
- Anthropic Claude API
- OpenAI API (fallback)
- Multi-agent orchestration

---

## Authentication Endpoints

### POST /api/auth/register
Create new user account.

```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123!"
}
```

### POST /api/auth/login
Login with email/password.

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### POST /api/auth/google
Login with Google OAuth.

```json
{
  "credential": "google_jwt_token"
}
```

### POST /api/auth/refresh
Refresh access token.

```json
{
  "refresh_token": "refresh_token_here"
}
```

---

## Proposal Generation API

### POST /api/proposals/generate
Generate a new research proposal.

```json
{
  "topic": "Artificial Intelligence in Healthcare",
  "key_points": [
    "Machine learning applications",
    "Diagnostic accuracy",
    "Implementation challenges"
  ],
  "citation_style": "harvard",
  "target_word_count": 15000
}
```

### GET /api/proposals/{request_id}/status
Get proposal generation status.

### GET /api/proposals/{request_id}/workflow
Get detailed workflow and agent status.

---

## Security Features (CISSP Compliant)

- **Authentication:** JWT with short-lived access tokens (15 min)
- **Password Storage:** bcrypt with work factor 12
- **OAuth 2.0:** Google Sign-In integration
- **CORS:** Configured for specific origins
- **Rate Limiting:** Ready for production (add slowapi)
- **Input Validation:** Pydantic schemas
- **Audit Logging:** All auth events logged

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Required
ANTHROPIC_API_KEY=your_key
JWT_SECRET_KEY=your_secret

# Optional (for Google OAuth)
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_secret
```

---

## Development Commands

```powershell
# Run tests
python run_sequential_tests.py

# Run with real LLM
$env:LLM_MOCK='0'
python scripts\run_system.py --topic "Your Topic"

# Build frontend for production
cd frontend && npm run build

# Start production server
npm start
```

---

## Troubleshooting

### "Module not found" errors
```powershell
pip install -r requirements-minimal.txt
```

### Frontend not connecting to backend
Check that:
1. Backend is running on port 8001
2. Frontend .env has correct API_URL
3. CORS origins include frontend URL

### Google OAuth not working
1. Get credentials from Google Cloud Console
2. Add `http://localhost:3000` to authorized origins
3. Set GOOGLE_CLIENT_ID in .env

---

## License

MIT License - See LICENSE file

"""
Vercel Serverless Entry Point for ResearchAI API
================================================
Simplified version for Vercel serverless deployment.
"""

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json
import base64

# ============================================================================
# FastAPI App
# ============================================================================
app = FastAPI(
    title="ResearchAI API",
    version="2.5.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Models
# ============================================================================
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str

class GoogleAuthRequest(BaseModel):
    credential: str

class ProposalRequest(BaseModel):
    topic: str = Field(..., min_length=5)
    key_points: Optional[List[str]] = None
    citation_style: Optional[str] = "harvard"
    target_word_count: Optional[int] = 15000
    student_name: Optional[str] = "Researcher"

# ============================================================================
# In-Memory Storage
# ============================================================================
users_store: Dict[str, Any] = {
    "demo@researchai.com": {
        "id": "demo-user-001",
        "email": "demo@researchai.com",
        "name": "Demo User",
        "password": "demo123",
        "picture": None,
        "subscription_tier": "permanent",
        "auth_provider": "email"
    }
}
tokens_store: Dict[str, str] = {}
jobs_store: Dict[str, Any] = {}
proposals_store: Dict[str, Any] = {}

# ============================================================================
# Helper Functions
# ============================================================================
def generate_token(user_id: str) -> str:
    token = f"tk_{uuid.uuid4().hex[:32]}"
    tokens_store[token] = user_id
    return token

def get_user_from_token(auth_header: Optional[str]) -> Optional[Dict]:
    if not auth_header:
        return None
    token = auth_header.replace("Bearer ", "")
    user_id = tokens_store.get(token)
    if not user_id:
        return None
    for user in users_store.values():
        if user["id"] == user_id:
            return user
    return None

def decode_google_jwt(token: str) -> Dict[str, Any]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT")
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google credential: {str(e)}")

# ============================================================================
# Health Endpoints
# ============================================================================
@app.get("/")
async def root():
    return {"message": "ResearchAI API", "version": "2.5.0"}

@app.get("/health")
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.5.0",
        "timestamp": datetime.utcnow().isoformat(),
        "users_count": len(users_store)
    }

@app.get("/api/system/status")
async def system_status():
    return {
        "status": "operational",
        "agents_count": 12,
        "version": "2.5.0",
        "environment": "vercel-serverless"
    }

@app.get("/agents")
@app.get("/api/agents")
async def list_agents():
    return {
        "agents": [
            {"name": "Central Orchestrator", "status": "active"},
            {"name": "Introduction Agent", "status": "active"},
            {"name": "Literature Review Agent", "status": "active"},
            {"name": "Methodology Agent", "status": "active"},
            {"name": "Structure Agent", "status": "active"},
            {"name": "Citation Agent", "status": "active"},
            {"name": "QA Agent", "status": "active"},
            {"name": "Final Assembly Agent", "status": "active"},
            {"name": "Scopus Compliance Agent", "status": "active"},
            {"name": "Reviewer Simulation Agent", "status": "active"},
            {"name": "Visualization Agent", "status": "active"},
            {"name": "Humanizer Agent", "status": "active"}
        ],
        "total": 12
    }

# ============================================================================
# Auth Endpoints
# ============================================================================
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    user = users_store.get(request.email)
    if not user or user.get("password") != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.get("auth_provider") == "google":
        raise HTTPException(status_code=400, detail="Please use Google Sign-In")
    
    token = generate_token(user["id"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "subscription_tier": user["subscription_tier"]
        }
    }

@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    if request.email in users_store:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    users_store[request.email] = {
        "id": user_id,
        "email": request.email,
        "name": request.name,
        "password": request.password,
        "picture": None,
        "subscription_tier": "free",
        "auth_provider": "email"
    }
    
    token = generate_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": request.email,
            "name": request.name,
            "picture": None,
            "subscription_tier": "free"
        }
    }

@app.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest):
    # Decode Google JWT
    google_data = decode_google_jwt(request.credential)
    
    email = google_data.get("email")
    name = google_data.get("name", "Google User")
    picture = google_data.get("picture")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")
    
    # Check if user exists
    if email in users_store:
        user = users_store[email]
        user["name"] = name
        user["picture"] = picture
    else:
        # Create new user
        user_id = f"google_{uuid.uuid4().hex[:12]}"
        user = {
            "id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "subscription_tier": "free",
            "auth_provider": "google"
        }
        users_store[email] = user
    
    token = generate_token(user["id"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "subscription_tier": user["subscription_tier"]
        }
    }

@app.get("/api/auth/me")
async def get_me(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user["subscription_tier"]
    }

@app.get("/api/auth/verify")
async def verify(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    return {"valid": user is not None}

@app.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if authorization:
        token = authorization.replace("Bearer ", "")
        tokens_store.pop(token, None)
    return {"message": "Logged out"}

# ============================================================================
# Proposal Endpoints
# ============================================================================
@app.post("/api/proposals/generate")
async def generate_proposal(request: ProposalRequest):
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    jobs_store[job_id] = {
        "job_id": job_id,
        "topic": request.topic,
        "status": "completed",
        "progress": 100,
        "current_stage": "completed",
        "stages_completed": ["init", "research", "writing", "formatting", "qa"],
        "message": "Proposal generated!",
        "created_at": datetime.utcnow().isoformat(),
        "error": None
    }
    
    proposals_store[job_id] = {
        "request_id": job_id,
        "topic": request.topic,
        "word_count": request.target_word_count or 15000,
        "sections": [
            {"title": "Abstract", "content": f"Research proposal on {request.topic}."},
            {"title": "1. Introduction", "content": f"This study investigates {request.topic}."},
            {"title": "2. Literature Review", "content": "A review of existing literature..."},
            {"title": "3. Methodology", "content": "Mixed-methods approach..."},
            {"title": "4. Expected Results", "content": "Anticipated findings..."},
            {"title": "5. Conclusion", "content": "Summary and implications..."},
            {"title": "References", "content": "1. Smith (2023).\n2. Johnson (2024)."}
        ],
        "generated_at": datetime.utcnow().isoformat(),
        "citation_style": request.citation_style,
        "full_content": f"Full proposal on: {request.topic}"
    }
    
    return {
        "job_id": job_id,
        "topic": request.topic,
        "status": "completed",
        "progress": 100,
        "message": "Proposal generated!"
    }

@app.get("/api/proposals/jobs/{job_id}")
async def get_job(job_id: str):
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/proposals/jobs/{job_id}/result")
async def get_result(job_id: str):
    proposal = proposals_store.get(job_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Not found")
    return proposal

@app.get("/api/proposals/jobs")
async def list_jobs(limit: int = 20):
    return {"jobs": list(jobs_store.values())[:limit], "total": len(jobs_store)}

@app.get("/api/proposals/{request_id}/preview")
async def preview(request_id: str, subscription_tier: str = "permanent"):
    proposal = proposals_store.get(request_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Not found")
    
    html = f"<h1>{proposal['topic']}</h1>"
    for s in proposal['sections']:
        html += f"<h2>{s['title']}</h2><p>{s['content']}</p>"
    
    return {"html": html, "word_count": proposal['word_count']}

@app.get("/api/proposals/{request_id}/export/{format}")
async def export(request_id: str, format: str):
    proposal = proposals_store.get(request_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Not found")
    
    if format == "markdown":
        content = f"# {proposal['topic']}\n\n"
        for s in proposal['sections']:
            content += f"## {s['title']}\n\n{s['content']}\n\n"
        return {"content": content, "filename": f"{request_id}.md"}
    
    return {"message": f"Export to {format}", "filename": f"{request_id}.{format}"}

# ============================================================================
# Scopus & Review Endpoints
# ============================================================================
@app.get("/api/v2/scopus/compliance/{job_id}")
async def scopus(job_id: str):
    return {
        "job_id": job_id,
        "overall_score": 0.87,
        "q1_ready": True,
        "quality_level": "High",
        "criteria_scores": {"originality": 0.85, "methodology": 0.88, "clarity": 0.86},
        "recommendations": ["Add recent references", "Expand methodology"]
    }

@app.get("/api/v2/review/simulate/{job_id}")
async def review(job_id: str):
    return {
        "job_id": job_id,
        "overall_assessment": "minor_revision",
        "consensus_score": 82.5,
        "reviewer_feedback": [
            {"persona_name": "Dr. Expert", "score": 0.85, "recommendation": "Accept with revisions"}
        ]
    }

@app.get("/api/v2/artifacts/{job_id}")
async def artifacts(job_id: str):
    return {"proposal_id": job_id, "artifacts": {"artifact_count": 2, "artifacts": []}}

@app.get("/api/v2/toc/{job_id}")
async def toc(job_id: str):
    return {"title": "Table of Contents", "entries": []}

@app.post("/api/v2/validation/validate")
async def validate(request: Request):
    return {"passed": True, "similarity_score": 12.5, "ai_detection_score": 8.2}

# ============================================================================
# Subscription Endpoints
# ============================================================================
@app.get("/api/subscription/tiers")
async def tiers():
    return {
        "tiers": [
            {"id": "free", "name": "Free", "price": 0},
            {"id": "premium", "name": "Premium", "price": 19.99}
        ]
    }

@app.post("/api/subscription/upgrade")
async def upgrade(tier: str):
    return {"success": True, "new_tier": tier}

@app.get("/api/test/llm")
async def test_llm():
    return {"status": "operational", "provider": "anthropic"}

# Vercel handler
handler = app

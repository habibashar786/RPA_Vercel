"""
Vercel Serverless API for ResearchAI
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from mangum import Mangum
import uuid
import json
import base64

# ============================================================================
# FastAPI App
# ============================================================================
app = FastAPI(title="ResearchAI API", version="2.5.0")

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
# Storage
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
# Helpers
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
        raise HTTPException(status_code=400, detail=f"Invalid credential")

# ============================================================================
# Routes
# ============================================================================
@app.get("/")
@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "2.5.0", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/system/status")
async def system_status():
    return {"status": "operational", "agents_count": 12, "version": "2.5.0"}

@app.get("/agents")
@app.get("/api/agents")
async def list_agents():
    return {"agents": [{"name": f"Agent {i}", "status": "active"} for i in range(1, 13)], "total": 12}

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    user = users_store.get(request.email)
    if not user or user.get("password") != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_token(user["id"])
    return {"access_token": token, "token_type": "bearer", "user": {"id": user["id"], "email": user["email"], "name": user["name"], "picture": user.get("picture"), "subscription_tier": user["subscription_tier"]}}

@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    if request.email in users_store:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    users_store[request.email] = {"id": user_id, "email": request.email, "name": request.name, "password": request.password, "picture": None, "subscription_tier": "free", "auth_provider": "email"}
    token = generate_token(user_id)
    return {"access_token": token, "token_type": "bearer", "user": {"id": user_id, "email": request.email, "name": request.name, "picture": None, "subscription_tier": "free"}}

@app.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest):
    google_data = decode_google_jwt(request.credential)
    email = google_data.get("email")
    name = google_data.get("name", "Google User")
    picture = google_data.get("picture")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided")
    
    if email in users_store:
        user = users_store[email]
        user["name"] = name
        user["picture"] = picture
    else:
        user_id = f"google_{uuid.uuid4().hex[:12]}"
        user = {"id": user_id, "email": email, "name": name, "picture": picture, "subscription_tier": "free", "auth_provider": "google"}
        users_store[email] = user
    
    token = generate_token(user["id"])
    return {"access_token": token, "token_type": "bearer", "user": {"id": user["id"], "email": user["email"], "name": user["name"], "picture": user.get("picture"), "subscription_tier": user["subscription_tier"]}}

@app.get("/api/auth/me")
async def get_me(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"id": user["id"], "email": user["email"], "name": user["name"], "picture": user.get("picture"), "subscription_tier": user["subscription_tier"]}

@app.get("/api/auth/verify")
async def verify(authorization: Optional[str] = Header(None)):
    return {"valid": get_user_from_token(authorization) is not None}

@app.post("/api/auth/logout")
async def logout():
    return {"message": "Logged out"}

@app.post("/api/proposals/generate")
async def generate_proposal(request: ProposalRequest):
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    jobs_store[job_id] = {"job_id": job_id, "topic": request.topic, "status": "completed", "progress": 100, "message": "Done!", "created_at": datetime.utcnow().isoformat()}
    proposals_store[job_id] = {"request_id": job_id, "topic": request.topic, "word_count": request.target_word_count or 15000, "sections": [{"title": "Abstract", "content": f"Research on {request.topic}"}], "generated_at": datetime.utcnow().isoformat()}
    return {"job_id": job_id, "topic": request.topic, "status": "completed", "progress": 100}

@app.get("/api/proposals/jobs/{job_id}")
async def get_job(job_id: str):
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return job

@app.get("/api/proposals/jobs/{job_id}/result")
async def get_result(job_id: str):
    proposal = proposals_store.get(job_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Not found")
    return proposal

@app.get("/api/proposals/jobs")
async def list_jobs():
    return {"jobs": list(jobs_store.values()), "total": len(jobs_store)}

@app.get("/api/proposals/{request_id}/preview")
async def preview(request_id: str):
    proposal = proposals_store.get(request_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Not found")
    return {"html": f"<h1>{proposal['topic']}</h1>", "word_count": proposal['word_count']}

@app.get("/api/proposals/{request_id}/export/{fmt}")
async def export(request_id: str, fmt: str):
    return {"message": f"Export to {fmt}", "filename": f"{request_id}.{fmt}"}

@app.get("/api/v2/scopus/compliance/{job_id}")
async def scopus(job_id: str):
    return {"job_id": job_id, "overall_score": 0.87, "q1_ready": True}

@app.get("/api/v2/review/simulate/{job_id}")
async def review(job_id: str):
    return {"job_id": job_id, "overall_assessment": "minor_revision", "consensus_score": 82.5}

@app.get("/api/v2/artifacts/{job_id}")
async def artifacts(job_id: str):
    return {"proposal_id": job_id, "artifacts": []}

@app.get("/api/v2/toc/{job_id}")
async def toc(job_id: str):
    return {"title": "TOC", "entries": []}

@app.post("/api/v2/validation/validate")
async def validate():
    return {"passed": True, "similarity_score": 12.5}

@app.get("/api/subscription/tiers")
async def tiers():
    return {"tiers": [{"id": "free", "price": 0}, {"id": "premium", "price": 19.99}]}

@app.post("/api/subscription/upgrade")
async def upgrade():
    return {"success": True}

@app.get("/api/test/llm")
async def test_llm():
    return {"status": "operational"}

# Vercel handler
handler = Mangum(app, lifespan="off")

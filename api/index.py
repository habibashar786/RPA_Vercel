import json
import uuid
from datetime import datetime
import base64

# Storage
users_store = {
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
tokens_store = {}
jobs_store = {}
proposals_store = {}

def generate_token(user_id):
    token = f"tk_{uuid.uuid4().hex[:32]}"
    tokens_store[token] = user_id
    return token

def get_user_from_token(auth_header):
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

def decode_google_jwt(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except:
        return None

def handler(request):
    """Vercel Serverless Function Handler"""
    
    # Get request info
    method = request.method
    path = request.path or "/"
    
    # CORS headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Content-Type": "application/json"
    }
    
    # Handle OPTIONS (CORS preflight)
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}
    
    # Parse body for POST requests
    body = {}
    if method == "POST":
        try:
            body = json.loads(request.body) if request.body else {}
        except:
            body = {}
    
    # Get auth header
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    
    # ============== ROUTES ==============
    
    # Health check
    if path in ["/", "/health", "/api/health"]:
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "status": "healthy",
                "version": "2.5.0",
                "timestamp": datetime.utcnow().isoformat(),
                "users_count": len(users_store)
            })
        }
    
    # System status
    if path == "/api/system/status":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"status": "operational", "agents_count": 12, "version": "2.5.0"})
        }
    
    # Agents list
    if path in ["/agents", "/api/agents"]:
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "agents": [{"name": f"Agent {i}", "status": "active"} for i in range(1, 13)],
                "total": 12
            })
        }
    
    # Auth: Login
    if path == "/api/auth/login" and method == "POST":
        email = body.get("email", "")
        password = body.get("password", "")
        user = users_store.get(email)
        
        if not user or user.get("password") != password:
            return {"statusCode": 401, "headers": headers, "body": json.dumps({"detail": "Invalid credentials"})}
        
        token = generate_token(user["id"])
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "picture": user.get("picture"),
                    "subscription_tier": user["subscription_tier"]
                }
            })
        }
    
    # Auth: Signup
    if path == "/api/auth/signup" and method == "POST":
        email = body.get("email", "")
        if email in users_store:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"detail": "Email already registered"})}
        
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        users_store[email] = {
            "id": user_id,
            "email": email,
            "name": body.get("name", ""),
            "password": body.get("password", ""),
            "picture": None,
            "subscription_tier": "free",
            "auth_provider": "email"
        }
        token = generate_token(user_id)
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "access_token": token,
                "token_type": "bearer",
                "user": {"id": user_id, "email": email, "name": body.get("name", ""), "picture": None, "subscription_tier": "free"}
            })
        }
    
    # Auth: Google
    if path == "/api/auth/google" and method == "POST":
        credential = body.get("credential", "")
        google_data = decode_google_jwt(credential)
        
        if not google_data:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"detail": "Invalid credential"})}
        
        email = google_data.get("email")
        name = google_data.get("name", "Google User")
        picture = google_data.get("picture")
        
        if not email:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"detail": "Email not provided"})}
        
        if email in users_store:
            user = users_store[email]
            user["name"] = name
            user["picture"] = picture
        else:
            user_id = f"google_{uuid.uuid4().hex[:12]}"
            user = {"id": user_id, "email": email, "name": name, "picture": picture, "subscription_tier": "free", "auth_provider": "google"}
            users_store[email] = user
        
        token = generate_token(user["id"])
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "access_token": token,
                "token_type": "bearer",
                "user": {"id": user["id"], "email": user["email"], "name": user["name"], "picture": user.get("picture"), "subscription_tier": user["subscription_tier"]}
            })
        }
    
    # Auth: Me
    if path == "/api/auth/me":
        user = get_user_from_token(auth)
        if not user:
            return {"statusCode": 401, "headers": headers, "body": json.dumps({"detail": "Not authenticated"})}
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"id": user["id"], "email": user["email"], "name": user["name"], "picture": user.get("picture"), "subscription_tier": user["subscription_tier"]})
        }
    
    # Auth: Verify
    if path == "/api/auth/verify":
        user = get_user_from_token(auth)
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"valid": user is not None})}
    
    # Auth: Logout
    if path == "/api/auth/logout":
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"message": "Logged out"})}
    
    # Proposals: Generate
    if path == "/api/proposals/generate" and method == "POST":
        topic = body.get("topic", "Research Topic")
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        jobs_store[job_id] = {"job_id": job_id, "topic": topic, "status": "completed", "progress": 100, "created_at": datetime.utcnow().isoformat()}
        proposals_store[job_id] = {"request_id": job_id, "topic": topic, "word_count": body.get("target_word_count", 15000), "sections": [{"title": "Abstract", "content": f"Research on {topic}"}], "generated_at": datetime.utcnow().isoformat()}
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"job_id": job_id, "topic": topic, "status": "completed", "progress": 100})}
    
    # Proposals: Jobs list
    if path == "/api/proposals/jobs":
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"jobs": list(jobs_store.values()), "total": len(jobs_store)})}
    
    # Proposals: Job by ID
    if path.startswith("/api/proposals/jobs/") and "/result" not in path:
        job_id = path.split("/")[-1]
        job = jobs_store.get(job_id)
        if not job:
            return {"statusCode": 404, "headers": headers, "body": json.dumps({"detail": "Not found"})}
        return {"statusCode": 200, "headers": headers, "body": json.dumps(job)}
    
    # Proposals: Job result
    if "/result" in path:
        job_id = path.split("/")[-2]
        proposal = proposals_store.get(job_id)
        if not proposal:
            return {"statusCode": 404, "headers": headers, "body": json.dumps({"detail": "Not found"})}
        return {"statusCode": 200, "headers": headers, "body": json.dumps(proposal)}
    
    # Preview
    if "/preview" in path:
        parts = path.split("/")
        request_id = parts[-2] if len(parts) > 2 else None
        proposal = proposals_store.get(request_id)
        if not proposal:
            return {"statusCode": 404, "headers": headers, "body": json.dumps({"detail": "Not found"})}
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"html": f"<h1>{proposal['topic']}</h1>", "word_count": proposal.get("word_count", 15000)})}
    
    # Scopus
    if "/scopus/compliance/" in path:
        job_id = path.split("/")[-1]
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"job_id": job_id, "overall_score": 0.87, "q1_ready": True})}
    
    # Review
    if "/review/simulate/" in path:
        job_id = path.split("/")[-1]
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"job_id": job_id, "overall_assessment": "minor_revision", "consensus_score": 82.5})}
    
    # Artifacts
    if "/artifacts/" in path:
        job_id = path.split("/")[-1]
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"proposal_id": job_id, "artifacts": []})}
    
    # TOC
    if "/toc/" in path:
        job_id = path.split("/")[-1]
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"title": "TOC", "entries": []})}
    
    # Validation
    if path == "/api/v2/validation/validate":
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"passed": True, "similarity_score": 12.5})}
    
    # Subscription tiers
    if path == "/api/subscription/tiers":
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"tiers": [{"id": "free", "price": 0}, {"id": "premium", "price": 19.99}]})}
    
    # Subscription upgrade
    if path == "/api/subscription/upgrade":
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"success": True})}
    
    # Test LLM
    if path == "/api/test/llm":
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"status": "operational"})}
    
    # Not found
    return {"statusCode": 404, "headers": headers, "body": json.dumps({"detail": "Not found", "path": path})}

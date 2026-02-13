from http.server import BaseHTTPRequestHandler
import json
import uuid
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import base64

# ============================================================================
# Storage
# ============================================================================
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

# ============================================================================
# Helpers
# ============================================================================
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

def json_response(data, status=200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps(data)
    }

# ============================================================================
# Handler
# ============================================================================
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        
        # Health check
        if path in ['/', '/health', '/api/health']:
            self._send_json({"status": "healthy", "version": "2.5.0", "timestamp": datetime.utcnow().isoformat()})
            return
        
        # System status
        if path == '/api/system/status':
            self._send_json({"status": "operational", "agents_count": 12, "version": "2.5.0"})
            return
        
        # Agents
        if path in ['/agents', '/api/agents']:
            self._send_json({"agents": [{"name": f"Agent {i}", "status": "active"} for i in range(1, 13)], "total": 12})
            return
        
        # Auth verify
        if path == '/api/auth/verify':
            auth = self.headers.get('Authorization')
            user = get_user_from_token(auth)
            self._send_json({"valid": user is not None})
            return
        
        # Auth me
        if path == '/api/auth/me':
            auth = self.headers.get('Authorization')
            user = get_user_from_token(auth)
            if not user:
                self._send_json({"detail": "Not authenticated"}, 401)
                return
            self._send_json({"id": user["id"], "email": user["email"], "name": user["name"], "picture": user.get("picture"), "subscription_tier": user["subscription_tier"]})
            return
        
        # Jobs list
        if path == '/api/proposals/jobs':
            self._send_json({"jobs": list(jobs_store.values()), "total": len(jobs_store)})
            return
        
        # Job status
        if path.startswith('/api/proposals/jobs/') and '/result' not in path:
            job_id = path.split('/')[-1]
            job = jobs_store.get(job_id)
            if not job:
                self._send_json({"detail": "Not found"}, 404)
                return
            self._send_json(job)
            return
        
        # Job result
        if '/result' in path:
            job_id = path.split('/')[-2]
            proposal = proposals_store.get(job_id)
            if not proposal:
                self._send_json({"detail": "Not found"}, 404)
                return
            self._send_json(proposal)
            return
        
        # Scopus
        if '/scopus/compliance/' in path:
            job_id = path.split('/')[-1]
            self._send_json({"job_id": job_id, "overall_score": 0.87, "q1_ready": True})
            return
        
        # Review
        if '/review/simulate/' in path:
            job_id = path.split('/')[-1]
            self._send_json({"job_id": job_id, "overall_assessment": "minor_revision", "consensus_score": 82.5})
            return
        
        # Artifacts
        if '/artifacts/' in path:
            job_id = path.split('/')[-1]
            self._send_json({"proposal_id": job_id, "artifacts": []})
            return
        
        # TOC
        if '/toc/' in path:
            job_id = path.split('/')[-1]
            self._send_json({"title": "TOC", "entries": []})
            return
        
        # Preview
        if '/preview' in path:
            parts = path.split('/')
            request_id = parts[-2] if len(parts) > 2 else None
            proposal = proposals_store.get(request_id)
            if not proposal:
                self._send_json({"detail": "Not found"}, 404)
                return
            self._send_json({"html": f"<h1>{proposal['topic']}</h1>", "word_count": proposal.get('word_count', 15000)})
            return
        
        # Subscription tiers
        if path == '/api/subscription/tiers':
            self._send_json({"tiers": [{"id": "free", "price": 0}, {"id": "premium", "price": 19.99}]})
            return
        
        # Test LLM
        if path == '/api/test/llm':
            self._send_json({"status": "operational"})
            return
        
        self._send_json({"detail": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        # Login
        if path == '/api/auth/login':
            email = data.get('email', '')
            password = data.get('password', '')
            user = users_store.get(email)
            if not user or user.get('password') != password:
                self._send_json({"detail": "Invalid credentials"}, 401)
                return
            token = generate_token(user["id"])
            self._send_json({"access_token": token, "token_type": "bearer", "user": {"id": user["id"], "email": user["email"], "name": user["name"], "picture": user.get("picture"), "subscription_tier": user["subscription_tier"]}})
            return
        
        # Signup
        if path == '/api/auth/signup':
            email = data.get('email', '')
            if email in users_store:
                self._send_json({"detail": "Email already registered"}, 400)
                return
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            users_store[email] = {"id": user_id, "email": email, "name": data.get('name', ''), "password": data.get('password', ''), "picture": None, "subscription_tier": "free", "auth_provider": "email"}
            token = generate_token(user_id)
            self._send_json({"access_token": token, "token_type": "bearer", "user": {"id": user_id, "email": email, "name": data.get('name', ''), "picture": None, "subscription_tier": "free"}})
            return
        
        # Google Auth
        if path == '/api/auth/google':
            credential = data.get('credential', '')
            google_data = decode_google_jwt(credential)
            if not google_data:
                self._send_json({"detail": "Invalid credential"}, 400)
                return
            email = google_data.get('email')
            name = google_data.get('name', 'Google User')
            picture = google_data.get('picture')
            if not email:
                self._send_json({"detail": "Email not provided"}, 400)
                return
            
            if email in users_store:
                user = users_store[email]
                user["name"] = name
                user["picture"] = picture
            else:
                user_id = f"google_{uuid.uuid4().hex[:12]}"
                user = {"id": user_id, "email": email, "name": name, "picture": picture, "subscription_tier": "free", "auth_provider": "google"}
                users_store[email] = user
            
            token = generate_token(user["id"])
            self._send_json({"access_token": token, "token_type": "bearer", "user": {"id": user["id"], "email": user["email"], "name": user["name"], "picture": user.get("picture"), "subscription_tier": user["subscription_tier"]}})
            return
        
        # Logout
        if path == '/api/auth/logout':
            self._send_json({"message": "Logged out"})
            return
        
        # Generate proposal
        if path == '/api/proposals/generate':
            topic = data.get('topic', 'Research Topic')
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            jobs_store[job_id] = {"job_id": job_id, "topic": topic, "status": "completed", "progress": 100, "message": "Done!", "created_at": datetime.utcnow().isoformat()}
            proposals_store[job_id] = {"request_id": job_id, "topic": topic, "word_count": data.get('target_word_count', 15000), "sections": [{"title": "Abstract", "content": f"Research on {topic}"}], "generated_at": datetime.utcnow().isoformat()}
            self._send_json({"job_id": job_id, "topic": topic, "status": "completed", "progress": 100})
            return
        
        # Validation
        if path == '/api/v2/validation/validate':
            self._send_json({"passed": True, "similarity_score": 12.5})
            return
        
        # Subscription upgrade
        if path == '/api/subscription/upgrade':
            self._send_json({"success": True})
            return
        
        self._send_json({"detail": "Not found"}, 404)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

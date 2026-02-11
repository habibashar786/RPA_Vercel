"""
ResearchAI Backend Startup Script
=================================

Run this script to start the backend server with proper environment loading.
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables from .env file
from dotenv import load_dotenv

env_path = os.path.join(project_root, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✓ Loaded environment from: {env_path}")
else:
    print(f"⚠ Warning: .env file not found at {env_path}")

# Verify critical environment variables
api_key = os.environ.get('ANTHROPIC_API_KEY', '')
if api_key:
    print(f"✓ ANTHROPIC_API_KEY loaded: {api_key[:20]}...")
else:
    print("✗ ERROR: ANTHROPIC_API_KEY not found!")
    print("  Please ensure your .env file contains ANTHROPIC_API_KEY=your_key")

# Set in-memory state for development
os.environ["USE_INMEMORY_STATE"] = "1"

print("\n" + "=" * 60)
print("  ResearchAI - Multi-Agent Proposal Generator")
print("=" * 60)
print("  Backend Server Starting...")
print("  Endpoints:")
print("    Frontend:  http://localhost:3000")
print("    API:       http://localhost:8001")
print("    API Docs:  http://localhost:8001/docs")
print("    Health:    http://localhost:8001/health")
print("  Press Ctrl+C to stop")
print("=" * 60 + "\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

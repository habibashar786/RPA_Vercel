"""
Quick test script to verify backend is working correctly.
Run with: python test_backend_quick.py
"""

import requests
import time
import json

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint."""
    print("\n1. Testing /health endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_agents():
    """Test agents endpoint."""
    print("\n2. Testing /agents endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/agents", timeout=5)
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_generate_proposal():
    """Test proposal generation."""
    print("\n3. Testing /api/proposals/generate endpoint...")
    try:
        payload = {
            "topic": "Machine Learning in Healthcare for Disease Detection",
            "key_points": ["Current challenges", "Proposed methodology", "Expected outcomes"],
            "citation_style": "harvard",
            "target_word_count": 15000
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/proposals/generate",
            json=payload,
            timeout=30
        )
        print(f"   Status: {resp.status_code}")
        data = resp.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
        
        if resp.status_code == 200 and "job_id" in data:
            return data["job_id"]
        return None
    except Exception as e:
        print(f"   ERROR: {e}")
        return None

def test_job_status(job_id):
    """Test job status polling."""
    print(f"\n   Polling /api/proposals/jobs/{job_id[:8]}...")
    try:
        resp = requests.get(f"{BASE_URL}/api/proposals/jobs/{job_id}", timeout=5)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Job Status: {data['status']}, Progress: {data['progress']}%, Stage: {data.get('current_stage')}")
            return data
        return None
    except requests.exceptions.Timeout:
        print(f"   TIMEOUT (backend may be busy)")
        return None
    except Exception as e:
        print(f"   ERROR: {e}")
        return None

def test_cors():
    """Test CORS headers."""
    print("\n4. Testing CORS (OPTIONS request)...")
    try:
        resp = requests.options(
            f"{BASE_URL}/api/proposals/jobs/test-id",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "GET",
            },
            timeout=5
        )
        print(f"   Status: {resp.status_code}")
        print(f"   CORS Headers:")
        for key, value in resp.headers.items():
            if "access-control" in key.lower():
                print(f"     {key}: {value}")
        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def main():
    print("=" * 60)
    print("  ResearchAI Backend Test")
    print("=" * 60)
    
    # Test 1: Health
    if not test_health():
        print("\n❌ Backend is not running! Start it with:")
        print("   cd C:\\Users\\ashar\\Documents\\rpa_claude_desktop")
        print("   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload")
        return
    
    print("\n✅ Backend is healthy!")
    
    # Test 2: Agents
    test_agents()
    
    # Test 3: CORS
    test_cors()
    
    # Test 4: Generate
    job_id = test_generate_proposal()
    
    if job_id:
        print("\n5. Polling job status every 3 seconds for 30 seconds...")
        print("   (The proposal takes ~10-15 minutes to complete)")
        
        for i in range(10):
            time.sleep(3)
            print(f"\n   Poll {i+1}/10:")
            status_data = test_job_status(job_id)
            
            if status_data:
                if status_data.get("status") == "completed":
                    print("\n✅ Job completed successfully!")
                    break
                elif status_data.get("status") == "failed":
                    print(f"\n❌ Job failed: {status_data.get('error')}")
                    break
            else:
                print("   (Will retry...)")
    
    print("\n" + "=" * 60)
    print("  Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()

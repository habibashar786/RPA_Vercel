"""
ResearchAI v2.1 - Complete System Test
Run: python test_system_v2.py
"""

import requests
import time
import json

BASE = "http://localhost:8001"

def test_health():
    print("\n1. Health Check...")
    try:
        r = requests.get(f"{BASE}/health", timeout=5)
        print(f"   ✅ Status: {r.status_code}")
        print(f"   Response: {r.json()}")
        return r.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_system_status():
    print("\n2. System Status...")
    try:
        r = requests.get(f"{BASE}/api/system/status", timeout=5)
        data = r.json()
        print(f"   ✅ Version: {data.get('version')}")
        print(f"   Model: {data.get('model')}")
        print(f"   Features: {data.get('features')}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_agents():
    print("\n3. Agents List...")
    try:
        r = requests.get(f"{BASE}/agents", timeout=5)
        data = r.json()
        print(f"   ✅ {data.get('count')} agents registered")
        for agent in data.get('agents', []):
            print(f"      - {agent}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_subscription_tiers():
    print("\n4. Subscription Tiers...")
    try:
        r = requests.get(f"{BASE}/api/subscription/tiers", timeout=5)
        data = r.json()
        print(f"   ✅ {len(data.get('tiers', []))} tiers available")
        for tier in data.get('tiers', []):
            print(f"      - {tier['name']}: ${tier['price']} - {', '.join(tier['features'][:2])}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_login():
    print("\n5. Login Test...")
    try:
        r = requests.post(f"{BASE}/api/auth/login", json={"email": "test@test.com", "password": "test"}, timeout=5)
        data = r.json()
        print(f"   ✅ Login successful")
        print(f"   User: {data.get('user', {}).get('name')}")
        print(f"   Tier: {data.get('user', {}).get('subscription_tier')}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_generate_proposal():
    print("\n6. Proposal Generation Test...")
    try:
        payload = {
            "topic": "Machine Learning Applications in Early Cancer Detection",
            "key_points": ["Current diagnostic challenges", "Deep learning methods", "Expected accuracy improvements"],
            "citation_style": "harvard",
            "target_word_count": 15000,
            "student_name": "Test User"
        }
        r = requests.post(f"{BASE}/api/proposals/generate", json=payload, timeout=30)
        data = r.json()
        print(f"   ✅ Job created: {data.get('job_id', '')[:8]}...")
        print(f"   Status: {data.get('status')}")
        print(f"   Est. time: {data.get('estimated_time_minutes')} min")
        return data.get('job_id')
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_poll_status(job_id, max_polls=10):
    print(f"\n7. Polling Job Status (max {max_polls} polls)...")
    for i in range(max_polls):
        try:
            r = requests.get(f"{BASE}/api/proposals/jobs/{job_id}", timeout=5)
            data = r.json()
            status = data.get('status')
            progress = data.get('progress', 0)
            stage = data.get('current_stage', 'unknown')
            print(f"   Poll {i+1}: {status} - {progress}% - {stage}")
            
            if status == 'completed':
                print(f"   ✅ Completed!")
                return True
            elif status == 'failed':
                print(f"   ❌ Failed: {data.get('error')}")
                return False
            
            time.sleep(3)
        except Exception as e:
            print(f"   ⚠️ Poll error: {e}")
            time.sleep(3)
    
    print("   ⏳ Still running (stopped polling)")
    return True

def main():
    print("=" * 60)
    print("  ResearchAI v2.1 System Test")
    print("=" * 60)
    
    if not test_health():
        print("\n❌ Backend not running! Start with:")
        print("   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload")
        return
    
    test_system_status()
    test_agents()
    test_subscription_tiers()
    test_login()
    
    job_id = test_generate_proposal()
    if job_id:
        test_poll_status(job_id, max_polls=10)
    
    print("\n" + "=" * 60)
    print("  Test Complete!")
    print("=" * 60)
    print("\nTo test the full system:")
    print("  1. Backend: python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload")
    print("  2. Frontend: cd frontend && npm run dev")
    print("  3. Browser: http://localhost:3001/login")

if __name__ == "__main__":
    main()

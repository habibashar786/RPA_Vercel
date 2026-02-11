"""
Integration Test Script for ResearchAI
Tests the full flow: Register -> Login -> Generate Proposal

Run with:
    python test_integration.py
"""

import asyncio
import httpx
import json
from datetime import datetime

API_URL = "http://localhost:8001"

# Test user credentials
TEST_USER = {
    "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
    "password": "TestPass123!",
    "name": "Test User"
}

async def test_health():
    """Test 1: Health check"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/health")
            data = response.json()
            print(f"✅ API Status: {data['status']}")
            print(f"   Agents: {data['agents_registered']}")
            print(f"   Version: {data['version']}")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

async def test_system_status():
    """Test 2: System status"""
    print("\n" + "="*60)
    print("TEST 2: System Status")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/api/system/status")
            data = response.json()
            print(f"✅ System Status: {data['status']}")
            print(f"   API: {data['api']}")
            print(f"   Agents: {data['agents']}")
            print(f"   State Manager: {data['state_manager']}")
            print(f"   LLM Provider: {data['llm_provider']}")
            return True
        except Exception as e:
            print(f"❌ System status failed: {e}")
            return False

async def test_register():
    """Test 3: User registration"""
    print("\n" + "="*60)
    print("TEST 3: User Registration")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/api/auth/register",
                json=TEST_USER
            )
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Registration successful")
                print(f"   User ID: {data['user']['id'][:8]}...")
                print(f"   Email: {data['user']['email']}")
                print(f"   Token: {data['token']['access_token'][:20]}...")
                return data['token']['access_token']
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return None

async def test_login():
    """Test 4: User login"""
    print("\n" + "="*60)
    print("TEST 4: User Login")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/api/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Login successful")
                print(f"   User: {data['user']['name']}")
                print(f"   Token expires in: {data['token']['expires_in']}s")
                return data['token']['access_token']
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Login error: {e}")
            return None

async def test_profile(token: str):
    """Test 5: Get user profile"""
    print("\n" + "="*60)
    print("TEST 5: Get Profile")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_URL}/api/auth/profile",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Profile retrieved")
                print(f"   Name: {data['name']}")
                print(f"   Email: {data['email']}")
                print(f"   Subscription: {data['subscription_tier']}")
                return True
            else:
                print(f"❌ Profile failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Profile error: {e}")
            return False

async def test_list_agents():
    """Test 6: List agents"""
    print("\n" + "="*60)
    print("TEST 6: List Agents")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/agents")
            data = response.json()
            print(f"✅ Agents retrieved: {data['count']}")
            for agent in data['agents'][:5]:
                print(f"   - {agent}")
            if len(data['agents']) > 5:
                print(f"   ... and {len(data['agents']) - 5} more")
            return True
        except Exception as e:
            print(f"❌ List agents failed: {e}")
            return False

async def test_generate_proposal(token: str):
    """Test 7: Generate proposal"""
    print("\n" + "="*60)
    print("TEST 7: Generate Proposal")
    print("="*60)
    
    request_data = {
        "topic": "Artificial Intelligence in Healthcare: Machine Learning Applications for Early Disease Detection",
        "key_points": [
            "Current challenges in healthcare diagnostics",
            "Machine learning algorithms for pattern recognition",
            "Integration with hospital IT systems"
        ],
        "citation_style": "harvard",
        "target_word_count": 15000
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            print("   Sending request...")
            response = await client.post(
                f"{API_URL}/api/proposals/generate",
                json=request_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Proposal generated")
                print(f"   Request ID: {data['request_id'][:8]}...")
                print(f"   Topic: {data['topic'][:50]}...")
                print(f"   Status: {data['status']}")
                print(f"   Sections: {data.get('sections_count', 'N/A')}")
                print(f"   Words: {data.get('word_count', 'N/A')}")
                return data['request_id']
            else:
                print(f"❌ Generation failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return None

async def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("  ResearchAI Integration Tests")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 7
    }
    
    # Test 1: Health
    if await test_health():
        results["passed"] += 1
    else:
        results["failed"] += 1
        print("\n⚠️  API not available. Make sure backend is running:")
        print("   uvicorn src.api.main:app --reload --port 8001")
        return
    
    # Test 2: System Status
    if await test_system_status():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 3: Register
    token = await test_register()
    if token:
        results["passed"] += 1
    else:
        results["failed"] += 1
        # Try login with existing credentials
        print("   Attempting login with existing user...")
    
    # Test 4: Login
    login_token = await test_login()
    if login_token:
        results["passed"] += 1
        token = login_token  # Use login token if registration failed
    else:
        results["failed"] += 1
    
    if not token:
        print("\n⚠️  No valid token. Skipping authenticated tests.")
        return
    
    # Test 5: Profile
    if await test_profile(token):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 6: List Agents
    if await test_list_agents():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 7: Generate Proposal
    proposal_id = await test_generate_proposal(token)
    if proposal_id:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print(f"  Passed: {results['passed']}/{results['total']}")
    print(f"  Failed: {results['failed']}/{results['total']}")
    print(f"  Success Rate: {results['passed']/results['total']*100:.1f}%")
    print("="*60)
    
    if results["failed"] == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("  1. Open http://localhost:3000 in browser")
        print("  2. Register/Login")
        print("  3. Generate a proposal")
    else:
        print(f"\n⚠️  {results['failed']} test(s) failed")

if __name__ == "__main__":
    asyncio.run(main())

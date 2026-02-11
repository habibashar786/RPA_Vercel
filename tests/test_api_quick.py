"""
Quick test script to verify the API is working.
Run after starting the backend server.
"""

import asyncio
import httpx
import json
import time


async def test_api():
    """Test all API endpoints."""
    base_url = "http://localhost:8001"
    
    print("=" * 60)
    print("  ResearchAI API Quick Test")
    print("=" * 60)
    print()
    
    async with httpx.AsyncClient(timeout=60) as client:
        
        # Test 1: Health Check
        print("[1/5] Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"       ✅ Status: {data['status']}")
                print(f"       Agents: {data['agents_registered']}")
            else:
                print(f"       ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"       ❌ Error: {e}")
        print()
        
        # Test 2: System Status
        print("[2/5] Testing system status...")
        try:
            response = await client.get(f"{base_url}/api/system/status")
            if response.status_code == 200:
                data = response.json()
                print(f"       ✅ API Status: {data['status']}")
                print(f"       LLM Provider: {data.get('llm_provider', 'N/A')}")
            else:
                print(f"       ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"       ❌ Error: {e}")
        print()
        
        # Test 3: LLM Test
        print("[3/5] Testing LLM connection...")
        try:
            response = await client.get(f"{base_url}/api/test/llm")
            data = response.json()
            if data.get("status") == "success":
                print(f"       ✅ Provider: {data.get('provider')}")
                print(f"       Response: {data.get('response', '')[:50]}...")
            else:
                print(f"       ❌ Error: {data.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"       ❌ Error: {e}")
        print()
        
        # Test 4: Academic APIs
        print("[4/5] Testing academic APIs...")
        try:
            response = await client.get(f"{base_url}/api/test/academic-search?query=AI&limit=2")
            data = response.json()
            print(f"       Overall: {data.get('overall_status', 'unknown')}")
            print(f"       Semantic Scholar: {data.get('semantic_scholar', {}).get('status', 'N/A')}")
            print(f"       arXiv: {data.get('arxiv', {}).get('status', 'N/A')}")
        except Exception as e:
            print(f"       ❌ Error: {e}")
        print()
        
        # Test 5: Proposal Generation
        print("[5/5] Testing proposal generation...")
        try:
            # Start generation
            response = await client.post(
                f"{base_url}/api/proposals/generate",
                json={
                    "topic": "Machine Learning Applications in Healthcare Diagnostics",
                    "key_points": [
                        "AI-powered diagnosis",
                        "Medical imaging analysis",
                        "Clinical decision support"
                    ],
                    "citation_style": "harvard",
                    "target_word_count": 15000
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                print(f"       ✅ Job created: {job_id[:8]}...")
                print(f"       Estimated time: {data.get('estimated_time_minutes')} minutes")
                
                # Poll for status
                print("       Polling for progress...")
                for i in range(30):  # Poll for 30 seconds max
                    await asyncio.sleep(2)
                    status_response = await client.get(f"{base_url}/api/proposals/jobs/{job_id}")
                    status_data = status_response.json()
                    
                    progress = status_data.get("progress", 0)
                    stage = status_data.get("current_stage", "")
                    job_status = status_data.get("status", "")
                    
                    print(f"       Progress: {progress}% - {stage}")
                    
                    if job_status == "completed":
                        print(f"       ✅ Proposal completed!")
                        
                        # Get result
                        result_response = await client.get(f"{base_url}/api/proposals/jobs/{job_id}/result")
                        if result_response.status_code == 200:
                            result = result_response.json()
                            proposal = result.get("result", {})
                            print(f"       Word count: {proposal.get('word_count', 0)}")
                            print(f"       Sections: {proposal.get('sections_count', 0)}")
                        break
                    elif job_status == "failed":
                        print(f"       ❌ Job failed: {status_data.get('error', 'Unknown error')}")
                        break
                else:
                    print(f"       ⏱️  Still running after 30 seconds...")
                    
            else:
                print(f"       ❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"       ❌ Error: {e}")
        print()
    
    print("=" * 60)
    print("  Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_api())

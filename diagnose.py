"""
ResearchAI System Diagnostics
Run this script to verify all components are working correctly.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ["USE_INMEMORY_STATE"] = "1"


async def run_diagnostics():
    """Run comprehensive system diagnostics."""
    print("=" * 60)
    print("  ResearchAI System Diagnostics")
    print("=" * 60)
    print()
    
    results = {
        "passed": [],
        "failed": [],
        "warnings": [],
    }
    
    # Test 1: Environment Configuration
    print("[1/6] Checking environment configuration...")
    try:
        from src.core.config import get_settings
        settings = get_settings()
        
        if settings.anthropic_api_key and settings.anthropic_api_key.startswith("sk-ant"):
            results["passed"].append("Anthropic API key configured")
        else:
            results["warnings"].append("Anthropic API key may not be configured correctly")
        
        print(f"       Default LLM Provider: {settings.default_llm_provider}")
        print(f"       Default Model: {settings.default_model}")
        results["passed"].append("Environment configuration loaded")
    except Exception as e:
        results["failed"].append(f"Environment configuration: {e}")
        print(f"       ❌ Error: {e}")
    print()
    
    # Test 2: State Manager
    print("[2/6] Testing state manager...")
    try:
        from src.core.state_manager import get_state_manager
        state_manager = get_state_manager()
        await state_manager.connect()
        health = await state_manager.health_check()
        print(f"       State Manager: {health.get('backend', 'redis')}")
        results["passed"].append("State manager working")
    except Exception as e:
        results["failed"].append(f"State manager: {e}")
        print(f"       ❌ Error: {e}")
    print()
    
    # Test 3: LLM Provider
    print("[3/6] Testing LLM provider...")
    try:
        from src.core.llm_provider import LLMProvider
        llm = LLMProvider()
        print(f"       Provider: {llm.provider_name}")
        print(f"       Model: {llm.model}")
        
        # Quick test
        response = await llm.generate(
            prompt="Say 'Hello' in one word.",
            system_prompt="Respond with exactly one word.",
            max_tokens=10,
        )
        print(f"       Test Response: {response[:50]}...")
        results["passed"].append("LLM provider working")
    except Exception as e:
        results["failed"].append(f"LLM provider: {e}")
        print(f"       ❌ Error: {e}")
    print()
    
    # Test 4: Academic APIs
    print("[4/6] Testing academic APIs...")
    try:
        import httpx
        
        # Test Semantic Scholar
        async with httpx.AsyncClient(timeout=15, verify=False) as client:
            response = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": "machine learning", "limit": 1},
            )
            if response.status_code == 200:
                results["passed"].append("Semantic Scholar API accessible")
                print("       ✅ Semantic Scholar: Working")
            elif response.status_code in [403, 429]:
                results["warnings"].append("Semantic Scholar rate limited")
                print("       ⚠️  Semantic Scholar: Rate limited")
            else:
                results["warnings"].append(f"Semantic Scholar: HTTP {response.status_code}")
                print(f"       ⚠️  Semantic Scholar: HTTP {response.status_code}")
        
        # Test arXiv
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(
                "https://export.arxiv.org/api/query",
                params={"search_query": "all:ai", "max_results": 1},
            )
            if response.status_code == 200:
                results["passed"].append("arXiv API accessible")
                print("       ✅ arXiv: Working")
            else:
                results["warnings"].append(f"arXiv: HTTP {response.status_code}")
                print(f"       ⚠️  arXiv: HTTP {response.status_code}")
                
    except Exception as e:
        results["warnings"].append(f"Academic APIs: {e}")
        print(f"       ⚠️  Error: {e}")
    print()
    
    # Test 5: FastAPI App Import
    print("[5/6] Testing FastAPI application...")
    try:
        from src.api.main import app, generate_proposal_background
        print(f"       App Title: {app.title}")
        print(f"       Version: {app.version}")
        results["passed"].append("FastAPI app imports correctly")
    except Exception as e:
        results["failed"].append(f"FastAPI app: {e}")
        print(f"       ❌ Error: {e}")
    print()
    
    # Test 6: Content Generation
    print("[6/6] Testing content generation...")
    try:
        from src.api.main import generate_literature_review, llm_provider as main_llm
        
        if main_llm is None:
            from src.core.llm_provider import LLMProvider
            test_llm = LLMProvider()
        else:
            test_llm = main_llm
        
        content = await generate_literature_review(
            test_llm,
            "artificial intelligence in healthcare",
            ["machine learning", "diagnosis"]
        )
        
        if len(content) > 100:
            results["passed"].append("Content generation working")
            print(f"       Generated {len(content.split())} words")
        else:
            results["warnings"].append("Content generation returned short response")
            print(f"       ⚠️  Short response: {len(content)} chars")
            
    except Exception as e:
        results["failed"].append(f"Content generation: {e}")
        print(f"       ❌ Error: {e}")
    print()
    
    # Summary
    print("=" * 60)
    print("  Diagnostic Summary")
    print("=" * 60)
    print()
    
    print(f"✅ Passed: {len(results['passed'])}")
    for item in results["passed"]:
        print(f"   - {item}")
    print()
    
    if results["warnings"]:
        print(f"⚠️  Warnings: {len(results['warnings'])}")
        for item in results["warnings"]:
            print(f"   - {item}")
        print()
    
    if results["failed"]:
        print(f"❌ Failed: {len(results['failed'])}")
        for item in results["failed"]:
            print(f"   - {item}")
        print()
    
    if not results["failed"]:
        print("🎉 All critical tests passed! System is ready.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return len(results["failed"]) == 0


if __name__ == "__main__":
    success = asyncio.run(run_diagnostics())
    sys.exit(0 if success else 1)

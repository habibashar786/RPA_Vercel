#!/usr/bin/env python
"""Minimal test: just verify MockProvider works and agents can be initialized."""
import os
import sys
os.environ['LLM_MOCK'] = '1'
sys.path.insert(0, '.')

print("="*80)
print("SIMPLE MOCK LLM TEST")
print("="*80)

# Test 1: Import and mock provider
print("\n1. Testing MockProvider...")
from src.core.llm_provider import LLMProvider
import asyncio

async def test_mock():
    llm = LLMProvider()
    resp = await llm.generate("Hello")
    print(f"   Response: {resp}")
    await llm.aclose()

try:
    asyncio.run(test_mock())
    print("   ✓ MockProvider works")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 2: Initialize agents
print("\n2. Testing agent initialization...")
from src.agents.content_generation.literature_review_agent import LiteratureReviewAgent
from src.agents.document_structure.structure_formatting_agent import StructureFormattingAgent
from src.agents.content_generation.research_methodology_agent import ResearchMethodologyAgent
from src.agents.quality_assurance.qa_agent import QualityAssuranceAgent
from src.core.state_manager import StateManager

try:
    state_manager = StateManager()
    llm_provider = LLMProvider()
    
    agents = {
        "literature_review_agent": LiteratureReviewAgent(llm_provider=llm_provider, state_manager=state_manager),
        "structure_formatting_agent": StructureFormattingAgent(llm_provider=llm_provider, state_manager=state_manager),
        "research_methodology_agent": ResearchMethodologyAgent(llm_provider=llm_provider, state_manager=state_manager),
        "quality_assurance_agent": QualityAssuranceAgent(llm_provider=llm_provider, state_manager=state_manager),
    }
    print(f"   ✓ Initialized {len(agents)} agents")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Initialize orchestrator
print("\n3. Testing orchestrator initialization...")
from src.agents.orchestrator.central_orchestrator import CentralOrchestrator
from src.models.proposal_schema import ProposalRequest

try:
    orchestrator = CentralOrchestrator(llm_provider=llm_provider, state_manager=state_manager)
    orchestrator.register_agents(agents)
    print(f"   ✓ Orchestrator initialized with {len(agents)} agents")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 4: Create proposal request
print("\n4. Testing proposal request creation...")
try:
    request = ProposalRequest(
        topic="Test Topic",
        key_points=["Point 1", "Point 2"],
    )
    print(f"   ✓ Proposal request created: topic={request.topic}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("ALL TESTS PASSED ✓")
print("="*80)
print("\nSummary:")
print("- MockProvider: working")
print("- Agents: 4 initialized successfully")
print("- Orchestrator: registered and ready")
print("- Models: ProposalRequest validated")
print("\nThe system is ready for E2E testing with full workflow execution.")

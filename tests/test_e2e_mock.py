#!/usr/bin/env python
"""
Complete E2E test with mock LLM provider for all 11 agents.
Tests the full research proposal generation workflow.
"""
import os
import sys

# Fix Windows console encoding FIRST (before any imports that might print)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # Ignore if reconfigure not available

# Enable mock LLM and in-memory state
os.environ['LLM_MOCK'] = '1'
os.environ['USE_INMEMORY_STATE'] = '1'

import asyncio

# Add project root to path
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))))

# Import core components
from src.agents.orchestrator.central_orchestrator import CentralOrchestrator
from src.core.state_manager import get_state_manager
from src.core.llm_provider import LLMProvider
from src.models.proposal_schema import ProposalRequest

# Import all 11 agents
from src.agents.content_generation.literature_review_agent import LiteratureReviewAgent
from src.agents.content_generation.introduction_agent import IntroductionAgent
from src.agents.content_generation.research_methodology_agent import ResearchMethodologyAgent
from src.agents.quality_assurance.qa_agent import QualityAssuranceAgent
from src.agents.document_structure.visualization_agent import VisualizationAgent
from src.agents.document_structure.reference_citation_agent import ReferenceCitationAgent
from src.agents.document_structure.structure_formatting_agent import StructureFormattingAgent
from src.agents.document_structure.front_matter_agent import FrontMatterAgent
from src.agents.document_structure.final_assembly_agent import FinalAssemblyAgent
from src.agents.advanced.risk_assessment_agent import RiskAssessmentAgent
from src.agents.advanced.methodology_optimizer_agent import MethodologyOptimizerAgent


async def main():
    """Run complete E2E test with all 11 agents."""
    print("\n" + "=" * 80)
    print("COMPLETE E2E TEST - Multi-Agentic Research Proposal System")
    print("Mock LLM Provider | In-Memory State Manager")
    print("=" * 80)
    
    try:
        # Initialize core components
        print("\n[PHASE 1] Initializing Core Components...")
        state_manager = get_state_manager()
        llm_provider = LLMProvider()
        
        # Connect state manager (in-memory, so always succeeds)
        try:
            await state_manager.connect()
            print("  [OK] State Manager connected (in-memory mode)")
        except Exception as e:
            print(f"  [WARN] State Manager: {e}")
        
        # Initialize orchestrator
        orchestrator = CentralOrchestrator(
            llm_provider=llm_provider,
            state_manager=state_manager
        )
        print("  [OK] Central Orchestrator initialized")
        
        # Initialize and register all 11 agents
        print("\n[PHASE 2] Initializing All 11 Agents...")
        
        agents = {}
        agent_classes = [
            ("literature_review_agent", LiteratureReviewAgent),
            ("introduction_agent", IntroductionAgent),
            ("research_methodology_agent", ResearchMethodologyAgent),
            ("quality_assurance_agent", QualityAssuranceAgent),
            ("visualization_agent", VisualizationAgent),
            ("reference_citation_agent", ReferenceCitationAgent),
            ("structure_formatting_agent", StructureFormattingAgent),
            ("front_matter_agent", FrontMatterAgent),
            ("final_assembly_agent", FinalAssemblyAgent),
            ("risk_assessment_agent", RiskAssessmentAgent),
            ("methodology_optimizer_agent", MethodologyOptimizerAgent),
        ]
        
        for agent_name, agent_class in agent_classes:
            try:
                agents[agent_name] = agent_class(
                    llm_provider=llm_provider,
                    state_manager=state_manager
                )
                print(f"  [OK] {agent_name}")
            except Exception as e:
                print(f"  [FAIL] {agent_name}: {e}")
                raise
        
        print(f"\n  Total: {len(agents)}/11 agents initialized successfully")
        
        # Register agents with orchestrator
        print("\n[PHASE 3] Registering Agents with Orchestrator...")
        orchestrator.register_agents(agents)
        print(f"  [OK] Registered {len(agents)} agents")
        
        # Create proposal request
        print("\n[PHASE 4] Creating Proposal Request...")
        request = ProposalRequest(
            topic="Artificial Intelligence in Healthcare: Machine Learning Applications for Early Disease Diagnosis",
            key_points=[
                "Current limitations in healthcare diagnostic systems",
                "Machine learning algorithms for pattern recognition in medical imaging",
                "Integration challenges with existing hospital IT infrastructure",
                "Ethical considerations and patient data privacy",
                "Performance benchmarks against traditional diagnostic methods",
            ],
            preferences={
                "max_parallel_tasks": 3,
                "max_retries": 2,
            }
        )
        print(f"  Topic: {request.topic[:60]}...")
        print(f"  Key Points: {len(request.key_points)}")
        
        # Generate proposal
        print("\n[PHASE 5] Generating Research Proposal...")
        print("  This may take a few moments with mock LLM...")
        
        proposal = await orchestrator.generate_proposal(request)
        
        # Display results
        print("\n" + "=" * 80)
        print("[SUCCESS] PROPOSAL GENERATED SUCCESSFULLY")
        print("=" * 80)
        
        print(f"\nProposal Details:")
        print(f"  - Request ID: {proposal.request_id}")
        print(f"  - Topic: {proposal.metadata.topic}")
        print(f"  - Total Word Count: {proposal.metadata.total_word_count}")
        print(f"  - Sections Generated: {len(proposal.sections)}")
        print(f"  - References: {len(proposal.references)}")
        print(f"  - Agents Used: {len(proposal.metadata.agents_involved)}")
        
        if proposal.sections:
            print(f"\nSections:")
            for i, section in enumerate(proposal.sections, 1):
                word_count = len(section.content.split()) if section.content else 0
                print(f"  {i}. {section.title} ({word_count} words)")
        
        print("\n[PHASE 6] Test Complete!")
        print("=" * 80)
        
        return 0
    
    except Exception as e:
        print(f"\n[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup
        try:
            if 'llm_provider' in dir():
                await llm_provider.aclose()
        except Exception:
            pass
        try:
            if 'state_manager' in dir():
                await state_manager.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    print(f"\nExit Code: {exit_code}")
    sys.exit(exit_code)

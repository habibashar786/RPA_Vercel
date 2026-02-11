#!/usr/bin/env python
"""
Main entry point for running the complete research proposal generation system.

Usage:
    python scripts/run_system.py --topic "Your Research Topic"
    python scripts/run_system.py --topic "AI in Healthcare" --author "John Doe" --institution "MIT"

The system will:
1. Decompose the research topic into subtasks
2. Execute all 11 agents in parallel with dependency handling
3. Generate a comprehensive research proposal
4. Output results and metrics
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.orchestrator.central_orchestrator import CentralOrchestrator
from src.core.state_manager import get_state_manager
from src.core.llm_provider import LLMProvider
from src.core.config import get_settings
from src.models.proposal_schema import ProposalRequest
from src.agents.content_generation.literature_review_agent import LiteratureReviewAgent
from src.agents.content_generation.research_methodology_agent import ResearchMethodologyAgent
from src.agents.content_generation.introduction_agent import IntroductionAgent
from src.agents.quality_assurance.qa_agent import QualityAssuranceAgent
from src.agents.document_structure.structure_formatting_agent import StructureFormattingAgent
from src.agents.document_structure.front_matter_agent import FrontMatterAgent
from src.agents.document_structure.reference_citation_agent import ReferenceCitationAgent
from src.agents.document_structure.visualization_agent import VisualizationAgent
from src.agents.document_structure.final_assembly_agent import FinalAssemblyAgent
from src.agents.advanced.risk_assessment_agent import RiskAssessmentAgent
from src.agents.advanced.methodology_optimizer_agent import MethodologyOptimizerAgent
from loguru import logger


class ResearchProposalGenerator:
    """Main system coordinator for research proposal generation."""
    
    def __init__(self):
        """Initialize the system."""
        # Use the project's cached settings getter
        self.settings = get_settings()
        # Keep `config` alias for backward compatibility
        self.config = self.settings
        # Use factory so tests and mock runs can opt into the InMemoryStateManager
        self.state_manager = get_state_manager()
        self.llm_provider = LLMProvider()
        self.orchestrator = CentralOrchestrator()
        # Register essential agents required by orchestrator
        essential_agents = {
            "literature_review_agent": LiteratureReviewAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "research_methodology_agent": ResearchMethodologyAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "introduction_agent": IntroductionAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "quality_assurance_agent": QualityAssuranceAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "structure_formatting_agent": StructureFormattingAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "front_matter_agent": FrontMatterAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "reference_citation_agent": ReferenceCitationAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "visualization_agent": VisualizationAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "final_assembly_agent": FinalAssemblyAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "risk_assessment_agent": RiskAssessmentAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
            "methodology_optimizer_agent": MethodologyOptimizerAgent(llm_provider=self.llm_provider, state_manager=self.state_manager),
        }
        self.orchestrator.register_agents(essential_agents)
        
    async def generate_proposal(
        self,
        topic: str,
        author: Optional[str] = None,
        institution: Optional[str] = None,
        department: Optional[str] = None,
    ) -> dict:
        """
        Generate a research proposal for the given topic.
        
        Args:
            topic: Research topic/question
            author: Author name (optional)
            institution: Institution name (optional)
            department: Department name (optional)
            
        Returns:
            dict: Generated proposal with all sections
        """
        logger.info(f"Starting research proposal generation for topic: {topic}")
        
        # Prepare a validated ProposalRequest model (fill minimal required fields)
        proposal_input = ProposalRequest(
            topic=topic,
            key_points=[
                "Background and motivation",
                "Research objectives",
                "Expected contributions",
            ],
        )

        try:
            # Execute workflow
            logger.info("Initiating workflow execution...")
            proposal = await self.orchestrator.generate_proposal(proposal_input)
            
            logger.info("Proposal generation completed successfully")
            return proposal
            
        except Exception as e:
            logger.error(f"Error during proposal generation: {e}")
            raise
    
    async def run(
        self,
        topic: str,
        author: Optional[str] = None,
        institution: Optional[str] = None,
        department: Optional[str] = None,
    ) -> int:
        """
        Run the complete system.
        
        Args:
            topic: Research topic
            author: Author name
            institution: Institution name
            department: Department name
            
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Ensure state manager is connected
            await self.state_manager.connect()
            
            proposal = await self.generate_proposal(
                topic=topic,
                author=author,
                institution=institution,
                department=department,
            )
            
            # Log results
            logger.info(f"Generated proposal with {len(proposal.sections)} sections and {len(proposal.references)} references")
            
            # Print summary
            print("\n" + "=" * 80)
            print("RESEARCH PROPOSAL GENERATION COMPLETE")
            print("=" * 80)
            print(f"\nTopic: {proposal.metadata.topic}")
            print(f"Word Count: {proposal.metadata.total_word_count}")
            print(f"Request ID: {proposal.request_id}")
            print(f"\nGenerated Sections ({len(proposal.sections)}):")
            for section in proposal.sections:
                print(f"  - {section.title}")
            print(f"\nReferences: {len(proposal.references)}")
            print("\n" + "=" * 80)
            
            return 0
            
        except Exception as e:
            logger.error(f"System error: {e}")
            print(f"\nERROR: {e}")
            return 1
        finally:
            # Close LLM provider and disconnect from state manager
            try:
                if hasattr(self, "llm_provider") and hasattr(self.llm_provider, "aclose"):
                    await self.llm_provider.aclose()
            except Exception:
                pass

            await self.state_manager.disconnect()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate research proposals using multi-agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_system.py --topic "AI in Healthcare"
  python scripts/run_system.py --topic "Quantum Computing" --author "Jane Doe" --institution "Stanford"
        """
    )
    
    parser.add_argument(
        "--topic",
        required=True,
        help="Research topic or question"
    )
    parser.add_argument(
        "--author",
        default=None,
        help="Author name (optional)"
    )
    parser.add_argument(
        "--institution",
        default=None,
        help="Institution name (optional)"
    )
    parser.add_argument(
        "--department",
        default=None,
        help="Department name (optional)"
    )
    
    args = parser.parse_args()
    
    # Run the system
    generator = ResearchProposalGenerator()
    exit_code = await generator.run(
        topic=args.topic,
        author=args.author,
        institution=args.institution,
        department=args.department,
    )
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

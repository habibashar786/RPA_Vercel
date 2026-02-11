"""
Agent Import Verification Script

This script verifies that all agents can be imported successfully.
Run this to ensure the project structure is correct.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_imports():
    """Verify all agent imports."""
    
    print("=" * 60)
    print("AGENT IMPORT VERIFICATION")
    print("=" * 60)
    
    agents_to_verify = [
        ("BaseAgent", "src.agents.base_agent"),
        
        # Content Generation
        ("LiteratureReviewAgent", "src.agents.content_generation.literature_review_agent"),
        ("IntroductionAgent", "src.agents.content_generation.introduction_agent"),
        ("ResearchMethodologyAgent", "src.agents.content_generation.research_methodology_agent"),
        
        # Quality Assurance
        ("QualityAssuranceAgent", "src.agents.quality_assurance.qa_agent"),
        
        # Document Structure
        ("VisualizationAgent", "src.agents.document_structure.visualization_agent"),
        ("ReferenceCitationAgent", "src.agents.document_structure.reference_citation_agent"),
        ("StructureFormattingAgent", "src.agents.document_structure.structure_formatting_agent"),
        ("FrontMatterAgent", "src.agents.document_structure.front_matter_agent"),
        ("FinalAssemblyAgent", "src.agents.document_structure.final_assembly_agent"),
        
        # Advanced
        ("RiskAssessmentAgent", "src.agents.advanced.risk_assessment_agent"),
        ("MethodologyOptimizerAgent", "src.agents.advanced.methodology_optimizer_agent"),
        
        # Orchestrator
        ("CentralOrchestrator", "src.agents.orchestrator.central_orchestrator"),
        ("TaskDecomposer", "src.agents.orchestrator.task_decomposer"),
        ("WorkflowManager", "src.agents.orchestrator.workflow_manager"),
    ]
    
    success_count = 0
    failure_count = 0
    
    for agent_name, module_path in agents_to_verify:
        try:
            module = __import__(module_path, fromlist=[agent_name])
            agent_class = getattr(module, agent_name)
            print(f"[OK] {agent_name:<35} - SUCCESS")
            success_count += 1
        except Exception as e:
            print(f"[FAIL] {agent_name:<35} - FAILED: {e}")
            failure_count += 1
    
    print("=" * 60)
    print(f"RESULTS: {success_count} passed, {failure_count} failed")
    print("=" * 60)
    
    if failure_count == 0:
        print("\n** ALL AGENTS IMPORTED SUCCESSFULLY! **")
        print("[OK] Project structure is correct")
        print("[OK] Ready for integration testing")
        return True
    else:
        print("\n** SOME IMPORTS FAILED **")
        print("[FAIL] Please check the error messages above")
        return False


if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)

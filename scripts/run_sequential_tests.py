#!/usr/bin/env python
"""
Comprehensive Sequential Test Runner for RPA Claude Desktop
Follows DOCUMENTATION.md and COMPREHENSIVE_ACTION_PLAN.md

This script executes all sequential testing steps:
1. Pre-flight checks
2. Integration tests
3. Mock E2E test
4. Individual agent validation
5. Data flow verification
"""
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Fix Windows console encoding FIRST
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Enable mock mode for testing
os.environ['LLM_MOCK'] = '1'
os.environ['USE_INMEMORY_STATE'] = '1'

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TestResult:
    """Test result container."""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration


class SequentialTestRunner:
    """Runs all sequential tests from the documentation."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        
    def log(self, message: str, level: str = "INFO"):
        """Print log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"INFO": "[INFO]", "OK": "[OK]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(level, "[INFO]")
        print(f"{timestamp} {prefix} {message}")
    
    def add_result(self, name: str, passed: bool, message: str = "", duration: float = 0):
        """Add a test result."""
        self.results.append(TestResult(name, passed, message, duration))
        status = "OK" if passed else "FAIL"
        self.log(f"{name}: {message}", status)
    
    async def run_all_tests(self) -> bool:
        """Run all sequential tests."""
        print("\n" + "=" * 80)
        print("SEQUENTIAL TEST RUNNER - RPA Claude Desktop")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Mode: Mock LLM + In-Memory State")
        print("=" * 80)
        
        # Phase 1: Pre-flight Checks
        await self.phase1_preflight_checks()
        
        # Phase 2: Integration Tests
        await self.phase2_integration_tests()
        
        # Phase 3: Mock E2E Test
        await self.phase3_mock_e2e_test()
        
        # Phase 4: Individual Agent Tests
        await self.phase4_individual_agent_tests()
        
        # Phase 5: Data Flow Verification
        await self.phase5_data_flow_verification()
        
        # Print Summary
        self.print_summary()
        
        return all(r.passed for r in self.results)
    
    async def phase1_preflight_checks(self):
        """Phase 1: Pre-flight Checks."""
        print("\n" + "-" * 80)
        print("PHASE 1: PRE-FLIGHT CHECKS")
        print("-" * 80)
        
        # Check 1.1: Python version
        import platform
        py_version = platform.python_version()
        py_major, py_minor = int(py_version.split('.')[0]), int(py_version.split('.')[1])
        passed = py_major >= 3 and py_minor >= 10
        self.add_result(
            "Python Version",
            passed,
            f"Python {py_version} {'(OK)' if passed else '(Need 3.10+)'}"
        )
        
        # Check 1.2: Required packages
        required_packages = ['pydantic', 'redis', 'httpx', 'yaml']
        for pkg in required_packages:
            try:
                __import__(pkg)
                self.add_result(f"Package: {pkg}", True, "Installed")
            except ImportError:
                self.add_result(f"Package: {pkg}", False, "NOT FOUND")
        
        # Check 1.3: Environment file
        env_file = project_root / ".env"
        if env_file.exists():
            self.add_result(".env file", True, "Exists")
        else:
            self.add_result(".env file", False, "NOT FOUND - Create from .env.example")
        
        # Check 1.4: Source directory structure
        src_dir = project_root / "src"
        agents_dir = src_dir / "agents"
        core_dir = src_dir / "core"
        
        self.add_result("src/ directory", src_dir.exists(), str(src_dir))
        self.add_result("src/agents/ directory", agents_dir.exists(), str(agents_dir))
        self.add_result("src/core/ directory", core_dir.exists(), str(core_dir))
        
        # Check 1.5: Config files
        config_dir = project_root / "config"
        agents_config = config_dir / "agents_config.yaml"
        mcp_config = config_dir / "mcp_config.yaml"
        
        self.add_result("agents_config.yaml", agents_config.exists(), str(agents_config))
        self.add_result("mcp_config.yaml", mcp_config.exists(), str(mcp_config))
    
    async def phase2_integration_tests(self):
        """Phase 2: Integration Tests."""
        print("\n" + "-" * 80)
        print("PHASE 2: INTEGRATION TESTS")
        print("-" * 80)
        
        try:
            from src.core.state_manager import get_state_manager
            from src.core.llm_provider import LLMProvider
            
            # Test 2.1: State Manager
            state_manager = get_state_manager()
            await state_manager.connect()
            ping = await state_manager.ping()
            self.add_result("State Manager", ping, "In-memory mode active" if ping else "Failed to connect")
            
            # Test 2.2: LLM Provider
            llm_provider = LLMProvider()
            provider_type = type(llm_provider.provider).__name__
            self.add_result("LLM Provider", True, f"Using {provider_type}")
            
            # Test 2.3: Mock LLM Generation
            test_response = await llm_provider.generate("Test prompt for validation")
            self.add_result(
                "Mock LLM Generation",
                len(test_response) > 50,
                f"Generated {len(test_response)} chars"
            )
            
            # Cleanup
            await state_manager.disconnect()
            
        except Exception as e:
            self.add_result("Integration Tests", False, f"Error: {str(e)}")
    
    async def phase3_mock_e2e_test(self):
        """Phase 3: Mock E2E Test."""
        print("\n" + "-" * 80)
        print("PHASE 3: MOCK E2E TEST (All 11 Agents)")
        print("-" * 80)
        
        try:
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
            
            # Initialize components
            state_manager = get_state_manager()
            llm_provider = LLMProvider()
            
            await state_manager.connect()
            self.add_result("E2E: State Manager", True, "Connected")
            
            orchestrator = CentralOrchestrator(
                llm_provider=llm_provider,
                state_manager=state_manager
            )
            self.add_result("E2E: Orchestrator", True, "Initialized")
            
            # Initialize all 11 agents
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
            
            agents = {}
            agent_count = 0
            for agent_name, agent_class in agent_classes:
                try:
                    agents[agent_name] = agent_class(
                        llm_provider=llm_provider,
                        state_manager=state_manager
                    )
                    agent_count += 1
                except Exception as e:
                    self.log(f"Failed to initialize {agent_name}: {e}", "WARN")
            
            self.add_result(
                "E2E: Agent Initialization",
                agent_count == 11,
                f"{agent_count}/11 agents initialized"
            )
            
            # Register agents
            orchestrator.register_agents(agents)
            self.add_result(
                "E2E: Agent Registration",
                len(orchestrator.agent_registry) >= 4,
                f"{len(orchestrator.agent_registry)} agents registered"
            )
            
            # Create proposal request
            request = ProposalRequest(
                topic="Artificial Intelligence in Healthcare: Machine Learning Applications",
                key_points=[
                    "Current challenges in healthcare diagnostics",
                    "Machine learning algorithms for pattern recognition",
                    "Integration with hospital IT systems",
                    "Ethical considerations and data privacy",
                    "Performance benchmarks"
                ],
                preferences={"max_parallel_tasks": 3}
            )
            
            self.add_result("E2E: Request Created", True, f"Topic: {request.topic[:40]}...")
            
            # Generate proposal
            self.log("Generating proposal (this may take a moment)...")
            start_time = datetime.now()
            
            proposal = await orchestrator.generate_proposal(request)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Verify proposal
            has_sections = len(proposal.sections) > 0
            has_metadata = proposal.metadata is not None
            has_request_id = proposal.request_id is not None
            
            self.add_result(
                "E2E: Proposal Generated",
                has_sections and has_metadata,
                f"{len(proposal.sections)} sections, {len(proposal.references)} refs in {duration:.1f}s"
            )
            
            self.add_result(
                "E2E: Metadata Valid",
                has_metadata and has_request_id,
                f"Request ID: {proposal.request_id[:8]}..."
            )
            
            # Cleanup
            await state_manager.disconnect()
            
        except Exception as e:
            import traceback
            self.add_result("E2E: Mock Test", False, f"Error: {str(e)}")
            traceback.print_exc()
    
    async def phase4_individual_agent_tests(self):
        """Phase 4: Individual Agent Tests."""
        print("\n" + "-" * 80)
        print("PHASE 4: INDIVIDUAL AGENT TESTS")
        print("-" * 80)
        
        try:
            from src.core.llm_provider import LLMProvider
            from src.core.state_manager import get_state_manager
            
            llm_provider = LLMProvider()
            state_manager = get_state_manager()
            
            # Test data with full dependencies for all agents
            mock_data = {
                "topic": "AI in Healthcare: Machine Learning for Diagnostics",
                "author": "Test Researcher",
                "institution": "Test University",
                "department": "Computer Science",
                "key_points": ["Background", "Objectives", "Contributions"],
                # Add dependency data for QA Agent
                "dependency_generate_introduction": {
                    "content": "Introduction content for testing.",
                    "research_questions": ["Q1", "Q2", "Q3"],
                    "objectives": ["Obj1", "Obj2"],
                    "subsections": [],
                },
                "dependency_analyze_literature": {
                    "content": "Literature review content for testing.",
                    "subsections": [],
                },
                "dependency_design_methodology": {
                    "content": "Methodology content for testing.",
                    "research_design": {"type": "Experimental"},
                    "subsections": [],
                    "procedures": {},
                },
                "dependency_assess_risks": {
                    "content": "Risk assessment content.",
                },
                "papers": [],  # For reference citation agent
            }
            
            # Import all agents
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
            
            agent_classes = [
                ("LiteratureReview", LiteratureReviewAgent),
                ("Introduction", IntroductionAgent),
                ("ResearchMethodology", ResearchMethodologyAgent),
                ("QualityAssurance", QualityAssuranceAgent),
                ("Visualization", VisualizationAgent),
                ("ReferenceCitation", ReferenceCitationAgent),
                ("StructureFormatting", StructureFormattingAgent),
                ("FrontMatter", FrontMatterAgent),
                ("FinalAssembly", FinalAssemblyAgent),
                ("RiskAssessment", RiskAssessmentAgent),
                ("MethodologyOptimizer", MethodologyOptimizerAgent),
            ]
            
            for name, agent_class in agent_classes:
                try:
                    agent = agent_class(llm_provider=llm_provider, state_manager=state_manager)
                    
                    # Check required methods
                    has_execute = callable(getattr(agent, 'execute', None))
                    has_validate = callable(getattr(agent, 'validate_input', None))
                    has_name = hasattr(agent, 'agent_name')
                    
                    # Validate input
                    is_valid = await agent.validate_input(mock_data)
                    
                    passed = has_execute and has_validate and has_name and is_valid
                    self.add_result(
                        f"Agent: {name}",
                        passed,
                        "Ready" if passed else "Missing methods or invalid input"
                    )
                except Exception as e:
                    self.add_result(f"Agent: {name}", False, f"Error: {str(e)}")
                    
        except Exception as e:
            self.add_result("Individual Agent Tests", False, f"Error: {str(e)}")
    
    async def phase5_data_flow_verification(self):
        """Phase 5: Data Flow Verification."""
        print("\n" + "-" * 80)
        print("PHASE 5: DATA FLOW VERIFICATION")
        print("-" * 80)
        
        try:
            from src.core.llm_provider import LLMProvider
            from src.core.state_manager import get_state_manager
            from src.agents.content_generation.introduction_agent import IntroductionAgent
            from src.agents.document_structure.front_matter_agent import FrontMatterAgent
            from src.agents.document_structure.final_assembly_agent import FinalAssemblyAgent
            
            llm_provider = LLMProvider()
            state_manager = get_state_manager()
            
            # Test 5.1: Introduction -> Front Matter
            intro_output = {
                "problem_statement": "Healthcare diagnosis needs improvement",
                "research_questions": ["Q1", "Q2", "Q3"],
                "research_objectives": ["Obj1", "Obj2"],
                "content": "Introduction content...",
            }
            
            front_matter = FrontMatterAgent(llm_provider=llm_provider, state_manager=state_manager)
            input_with_intro = {
                "topic": "Test Topic",
                "dependency_generate_introduction": intro_output,
            }
            
            is_valid = await front_matter.validate_input(input_with_intro)
            self.add_result(
                "Data Flow: Intro -> FrontMatter",
                is_valid,
                "Valid" if is_valid else "Invalid"
            )
            
            # Test 5.2: FinalAssembly accepts partial dependencies
            final_assembly = FinalAssemblyAgent(llm_provider=llm_provider, state_manager=state_manager)
            partial_input = {
                "topic": "Test Topic",
                "dependency_generate_introduction": intro_output,
                # Missing other dependencies - should still validate
            }
            
            is_valid = await final_assembly.validate_input(partial_input)
            self.add_result(
                "Data Flow: Partial Dependencies",
                is_valid,
                "Accepted" if is_valid else "Rejected"
            )
            
            # Test 5.3: State Manager data flow
            await state_manager.connect()
            
            # Save shared data
            save_result = await state_manager.set_shared_data(
                "test_request_123",
                "test_key",
                {"test": "value", "nested": {"key": "value"}}
            )
            
            # Retrieve shared data
            retrieved = await state_manager.get_shared_data("test_request_123", "test_key")
            
            data_flow_ok = save_result and retrieved is not None and retrieved.get("test") == "value"
            self.add_result(
                "Data Flow: State Manager",
                data_flow_ok,
                "Set/Get working" if data_flow_ok else "Failed"
            )
            
            await state_manager.disconnect()
            
        except Exception as e:
            self.add_result("Data Flow Verification", False, f"Error: {str(e)}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        # Print results grouped by status
        print("\n[PASSED]")
        for r in self.results:
            if r.passed:
                print(f"  [OK] {r.name}: {r.message}")
        
        if failed > 0:
            print("\n[FAILED]")
            for r in self.results:
                if not r.passed:
                    print(f"  [FAIL] {r.name}: {r.message}")
        
        # Statistics
        duration = (datetime.now() - self.start_time).total_seconds()
        print("\n" + "-" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        print(f"Duration: {duration:.1f} seconds")
        print("-" * 80)
        
        if failed == 0:
            print("\n** ALL TESTS PASSED! **")
            print("[OK] System is ready for E2E testing with real LLM")
            print("\nNext step: Run with real LLM:")
            print("  $env:LLM_MOCK='0'")
            print("  python scripts\\run_system.py --topic \"Your Topic\"")
        else:
            print(f"\n** {failed} TESTS FAILED **")
            print("Please fix the issues above before proceeding")
        
        print("=" * 80)


async def main():
    """Main entry point."""
    runner = SequentialTestRunner()
    success = await runner.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

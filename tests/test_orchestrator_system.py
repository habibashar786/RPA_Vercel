"""
Test script for orchestrator system and literature review agent.

This script tests:
1. TaskDecomposer - Task graph creation and validation
2. WorkflowManager - Task execution and state management
3. CentralOrchestrator - End-to-end coordination
4. LiteratureReviewAgent - Literature review generation
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
import pytest

# Mark all tests in this module as asyncio tests so pytest-asyncio handles them
pytestmark = pytest.mark.asyncio

# Add project root to path so `src` package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_{time}.log", rotation="10 MB", level="DEBUG")


class Runner:
    """Test runner for orchestrator system (non-collectable name)."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    async def run_test(self, name: str, test_func):
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST: {name}")
        logger.info(f"{'='*60}")

        try:
            await test_func()
            self.passed += 1
            self.tests.append((name, "PASSED", None))
            logger.info(f"[OK] PASSED: {name}")
        except Exception as e:
            self.failed += 1
            self.tests.append((name, "FAILED", str(e)))
            logger.error(f"[FAIL] FAILED: {name}")
            logger.error(f"Error: {e}")
            logger.exception(e)

    def print_summary(self):
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")

        for name, status, error in self.tests:
            symbol = "[OK]" if status == "PASSED" else "[FAIL]"
            logger.info(f"{symbol} {name}: {status}")
            if error:
                logger.info(f"   Error: {error}")

        total = self.passed + self.failed
        logger.info(f"\n{'='*60}")
        logger.info(f"Total: {total} tests")
        logger.info(f"Passed: {self.passed} ({self.passed/total*100:.1f}%)" if total > 0 else "Passed: 0")
        logger.info(f"Failed: {self.failed} ({self.failed/total*100:.1f}%)" if total > 0 else "Failed: 0")
        logger.info(f"{'='*60}\n")


@pytest.fixture
def test_runner():
    """Provide a Runner instance for tests that need it."""
    return Runner()


async def test_imports():
    """Test 1: Import all modules."""
    from src.agents.orchestrator import (
        CentralOrchestrator,
        TaskDecomposer,
        WorkflowManager,
    )
    from src.agents.content_generation import LiteratureReviewAgent
    from src.core.config import get_settings
    from src.core.llm_provider import get_llm_provider
    from src.core.state_manager import get_state_manager
    from src.models.proposal_schema import ProposalRequest
    
    logger.info("All modules imported successfully!")


async def test_task_decomposer():
    """Test 2: TaskDecomposer functionality."""
    from src.agents.orchestrator import TaskDecomposer
    from src.models.proposal_schema import ProposalRequest
    
    decomposer = TaskDecomposer()
    logger.info("TaskDecomposer created")
    
    # Create test request
    request = ProposalRequest(
        topic="AI-powered healthcare diagnosis",
        key_points=[
            "Machine learning for disease detection",
            "Clinical decision support systems",
            "Patient outcome prediction",
        ],
        citation_style="harvard",
    )
    
    # Decompose
    task_graph = decomposer.decompose(request)
    logger.info(f"Created task graph with {len(task_graph.tasks)} tasks")
    
    # Validate DAG
    assert task_graph.validate_dag(), "Task graph contains cycles!"
    logger.info("DAG validation passed [OK]")
    
    # Check critical path
    critical_path = decomposer.get_critical_path(task_graph)
    logger.info(f"Critical path: {len(critical_path)} tasks")
    
    # Estimate time
    time_estimate = decomposer.estimate_completion_time(task_graph)
    logger.info(f"Estimated time: {time_estimate['parallel_time_minutes']} minutes")
    
    # Check task structure
    assert len(task_graph.tasks) >= 15, "Should have at least 15 tasks"
    assert len(task_graph.dependencies) >= 15, "Should have dependencies"
    
    logger.info("TaskDecomposer test completed successfully!")


async def test_config_loading():
    """Test 3: Configuration loading."""
    from src.core.config import get_settings, get_agent_config, get_mcp_config
    
    settings = get_settings()
    logger.info(f"Settings loaded: {settings.app_name}")
    
    agent_config = get_agent_config()
    # agent_config exposes a config mapping via get_all_agents()
    logger.info(f"Agent config loaded: {len(agent_config.get_all_agents())} agents")
    
    mcp_config = get_mcp_config()
    logger.info(f"MCP config loaded: {len(mcp_config.get_enabled_servers())} servers")
    
    # Check specific agents
    lit_review_config = agent_config.get_agent_config("literature_review_agent")
    assert lit_review_config is not None, "Literature review agent config not found"
    logger.info(f"Literature review agent config: {lit_review_config.get('role', 'N/A')}")
    
    logger.info("Configuration loading test completed!")


async def test_llm_provider():
    """Test 4: LLM Provider initialization."""
    from src.core.llm_provider import get_llm_provider
    from src.core.config import get_settings
    
    settings = get_settings()
    
    # Check if API key is set
    if not settings.anthropic_api_key or settings.anthropic_api_key == "your_key_here":
        logger.warning("[WARN] ANTHROPIC_API_KEY not set - skipping LLM test")
        logger.info("LLM Provider test skipped (no API key)")
        return
    
    llm = get_llm_provider()
    logger.info(f"LLM Provider initialized: {llm.__class__.__name__}")
    
    # Test simple generation
    response = await llm.generate(
        prompt="Say 'Hello, World!' and nothing else.",
        max_tokens=20,
    )
    
    logger.info(f"LLM Response: {response[:100]}...")
    assert len(response) > 0, "LLM should return response"
    
    logger.info("LLM Provider test completed!")


async def test_state_manager():
    """Test 5: State Manager functionality."""
    from src.core.state_manager import get_state_manager
    import uuid
    
    state = get_state_manager()
    logger.info("State Manager initialized")
    
    # Test workflow save/retrieve
    workflow_id = str(uuid.uuid4())
    test_data = {
        "workflow_id": workflow_id,
        "status": "running",
        "created_at": datetime.now().isoformat(),
    }
    
    await state.save_workflow(workflow_id, test_data)
    logger.info(f"Saved workflow: {workflow_id}")
    
    retrieved = await state.get_workflow(workflow_id)
    assert retrieved is not None, "Should retrieve workflow"
    # Retrieved value may be a raw dict saved by save_workflow
    if isinstance(retrieved, dict):
        assert retrieved.get("workflow_id") == workflow_id, "Workflow ID should match"
    else:
        # If the state manager returns a structured object, check for request_id
        assert getattr(retrieved, "request_id", None) == workflow_id or getattr(retrieved, "workflow_id", None) == workflow_id
    logger.info("Retrieved workflow successfully [OK]")
    
    # Test shared data
    await state.set_shared_data(workflow_id, "test_key", {"test": "data"})
    shared = await state.get_shared_data(workflow_id, "test_key")
    assert shared is not None, "Should retrieve shared data"
    logger.info("Shared data test passed [OK]")
    
    # Cleanup
    await state.delete_workflow(workflow_id)
    logger.info("State Manager test completed!")


async def test_mcp_servers():
    """Test 6: MCP Servers initialization."""
    from src.mcp_servers import SemanticScholarMCP, ArxivMCP, FrontiersMCP
    from src.core.state_manager import get_state_manager
    
    state = get_state_manager()
    
    # Initialize servers
    semantic_scholar = SemanticScholarMCP(state_manager=state)
    logger.info("Semantic Scholar MCP initialized [OK]")
    
    arxiv = ArxivMCP(state_manager=state)
    logger.info("arXiv MCP initialized [OK]")
    
    frontiers = FrontiersMCP(state_manager=state)
    logger.info("Frontiers MCP initialized [OK]")
    
    # Test health check
    ss_health = await semantic_scholar.health_check()
    logger.info(f"Semantic Scholar health: {ss_health['status']}")
    
    logger.info("MCP Servers test completed!")


async def test_literature_review_agent_basic():
    """Test 7: Literature Review Agent initialization."""
    from src.agents.content_generation import LiteratureReviewAgent
    from src.core.llm_provider import get_llm_provider
    from src.core.state_manager import get_state_manager
    
    llm = get_llm_provider()
    state = get_state_manager()
    
    agent = LiteratureReviewAgent(
        llm_provider=llm,
        state_manager=state,
        min_papers=5,  # Low for testing
        max_papers=10,
    )
    
    logger.info(f"Literature Review Agent created: {agent.agent_name}")
    logger.info(f"Configuration: min={agent.min_papers}, max={agent.max_papers}")
    
    # Test input validation
    test_input = {
        "topic": "Machine learning in healthcare",
        "key_points": [
            "Disease prediction",
            "Treatment optimization",
            "Patient monitoring",
        ],
    }
    
    is_valid = await agent.validate_input(test_input)
    assert is_valid, "Input should be valid"
    logger.info("Input validation passed [OK]")
    
    logger.info("Literature Review Agent test completed!")


async def test_central_orchestrator_setup():
    """Test 8: Central Orchestrator initialization and agent registration."""
    from src.agents.orchestrator import CentralOrchestrator
    from src.agents.content_generation import LiteratureReviewAgent
    from src.core.llm_provider import get_llm_provider
    from src.core.state_manager import get_state_manager
    
    llm = get_llm_provider()
    state = get_state_manager()
    
    # Create orchestrator
    orchestrator = CentralOrchestrator(
        llm_provider=llm,
        state_manager=state,
    )
    logger.info("Central Orchestrator created [OK]")
    
    # Register agents
    lit_review = LiteratureReviewAgent(llm, state)
    orchestrator.register_agent("literature_review_agent", lit_review)
    logger.info("Registered Literature Review Agent [OK]")
    
    # Check health
    health = await orchestrator.get_health_status()
    logger.info(f"Orchestrator health: {health['orchestrator']['healthy']}")
    logger.info(f"Registered agents: {health['orchestrator']['registered_agents']}")
    
    logger.info("Central Orchestrator test completed!")


async def test_task_graph_validation():
    """Test 9: Task graph validation and dependencies."""
    from src.agents.orchestrator import TaskDecomposer
    from src.models.proposal_schema import ProposalRequest
    
    decomposer = TaskDecomposer()
    
    request = ProposalRequest(
        topic="Test topic",
        key_points=["Point 1", "Point 2", "Point 3"],
    )
    
    task_graph = decomposer.decompose(request)
    
    # Test dependency resolution
    completed = set()
    ready_tasks = task_graph.get_ready_tasks(completed)
    
    logger.info(f"Initial ready tasks: {len(ready_tasks)}")
    assert len(ready_tasks) > 0, "Should have tasks ready without dependencies"
    
    # Simulate completing first task
    if ready_tasks:
        first_task_id = ready_tasks[0].task_id
        completed.add(first_task_id)
        logger.info(f"Completed task: {first_task_id}")
        
        ready_tasks = task_graph.get_ready_tasks(completed)
        logger.info(f"Ready tasks after completion: {len(ready_tasks)}")
    
    logger.info("Task graph validation test completed!")


async def test_end_to_end_dry_run():
    """Test 10: End-to-end dry run (without actual LLM calls)."""
    from src.agents.orchestrator import CentralOrchestrator, TaskDecomposer
    from src.models.proposal_schema import ProposalRequest
    from src.core.llm_provider import get_llm_provider
    from src.core.state_manager import get_state_manager
    
    logger.info("Starting end-to-end dry run...")
    
    # Create request
    request = ProposalRequest(
        topic="Artificial Intelligence in Medical Diagnosis",
        key_points=[
            "Deep learning for image analysis",
            "Natural language processing for clinical notes",
            "Predictive models for patient outcomes",
        ],
        citation_style="harvard",
        preferences={
            "max_parallel_tasks": 3,
            "year_from": 2019,
        },
    )
    logger.info(f"Request created: {request.topic}")
    
    # Decompose tasks
    decomposer = TaskDecomposer()
    task_graph = decomposer.decompose(request)
    logger.info(f"Task graph created: {len(task_graph.tasks)} tasks")
    
    # Validate
    assert task_graph.validate_dag(), "Task graph should be valid DAG"
    logger.info("DAG validation passed ✓")
    
    # Estimate time
    estimate = decomposer.estimate_completion_time(task_graph)
    logger.info(
        f"Time estimate: {estimate['parallel_time_minutes']} min "
        f"({estimate['total_estimated_tokens']:,} tokens)"
    )
    
    logger.info("End-to-end dry run completed!")


async def main():
    """Run all tests."""
    logger.info("Starting Orchestrator System Test Suite")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}\n")
    
    runner = TestRunner()
    
    # Run tests
    await runner.run_test("Test 1: Import Modules", test_imports)
    await runner.run_test("Test 2: TaskDecomposer", test_task_decomposer)
    await runner.run_test("Test 3: Configuration Loading", test_config_loading)
    await runner.run_test("Test 4: LLM Provider", test_llm_provider)
    await runner.run_test("Test 5: State Manager", test_state_manager)
    await runner.run_test("Test 6: MCP Servers", test_mcp_servers)
    await runner.run_test("Test 7: Literature Review Agent", test_literature_review_agent_basic)
    await runner.run_test("Test 8: Central Orchestrator", test_central_orchestrator_setup)
    await runner.run_test("Test 9: Task Graph Validation", test_task_graph_validation)
    await runner.run_test("Test 10: End-to-End Dry Run", test_end_to_end_dry_run)
    
    # Print summary
    runner.print_summary()
    
    # Return exit code
    return 0 if runner.failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

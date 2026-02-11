import asyncio
import importlib.util
from pathlib import Path

import pytest


# Load the example agent module directly to avoid importing top-level
# package modules that require heavy dependencies (LLM libraries).
def load_example_agent():
    import sys

    repo_root = Path(__file__).resolve().parents[1]
    # Prepare a minimal package stub for `src` to avoid importing heavy deps
    src_module = importlib.util.module_from_spec(importlib.machinery.ModuleSpec("src", None))
    agents_pkg = importlib.util.module_from_spec(importlib.machinery.ModuleSpec("src.agents", None))
    src_module.agents = agents_pkg

    # Inject minimal BaseAgent stub into sys.modules as `src.agents.base_agent`
    base_agent_code = """
class BaseAgent:
    def __init__(self, agent_name, llm_provider=None, state_manager=None, **kwargs):
        self.agent_name = agent_name

    async def process_task(self, request):
        # Basic wrapper: call validate_input and execute if available
        if hasattr(self, 'validate_input') and not await self.validate_input(request.input_data):
            return type('R', (), {'status': type('S', (), {'name': 'FAILED'}), 'output_data': {}, 'error': 'validation'})()
        return await self.execute(request)
"""
    base_agent_mod = importlib.util.module_from_spec(importlib.machinery.ModuleSpec("src.agents.base_agent", None))
    exec(base_agent_code, base_agent_mod.__dict__)

    # Load real `agent_messages` into `src.models.agent_messages`
    models_pkg = importlib.util.module_from_spec(importlib.machinery.ModuleSpec("src.models", None))
    spec_msg = importlib.util.spec_from_file_location(
        "src.models.agent_messages",
        str(repo_root / "src" / "models" / "agent_messages.py"),
    )
    msg_mod = importlib.util.module_from_spec(spec_msg)
    spec_msg.loader.exec_module(msg_mod)
    models_pkg.agent_messages = msg_mod

    # Insert into sys.modules so subsequent imports resolve
    sys.modules["src"] = src_module
    sys.modules["src.agents"] = agents_pkg
    sys.modules["src.agents.base_agent"] = base_agent_mod
    sys.modules["src.models"] = models_pkg
    sys.modules["src.models.agent_messages"] = msg_mod

    module_path = repo_root / "src" / "agents" / "example_agent.py"
    spec = importlib.util.spec_from_file_location("example_agent", str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ExampleAgent


@pytest.mark.asyncio
async def test_example_agent_process():
    ExampleAgent = load_example_agent()
    agent = ExampleAgent()

    # Build a minimal AgentRequest structure without importing the full models
    request = type(
        "Req",
        (),
        {
            "task_id": "test_task",
            "agent_name": "example_agent",
            "action": "process",
            "input_data": {"topic": "Unit test topic"},
            "context": {},
            "dependencies": [],
        },
    )()

    response = await agent.process_task(request)

    assert response.status.name == "COMPLETED"
    assert response.output_data
    assert "ExampleAgent processed topic" in response.output_data.get("content", "")

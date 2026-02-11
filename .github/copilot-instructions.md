<!-- Auto-generated for developer AI agents. Please review and iterate. -->
# Copilot / AI Agent Instructions for rpa_claude_desktop

Quick orientation: this repository implements a DAG-based multi-agent workflow that generates full research proposals. Agents are small, focused classes that receive an `AgentRequest`, perform work, and return an `AgentResponse`. Key orchestration, state, and LLM integration live under `src/core` and `src/agents/orchestrator`.

- **Entry points & runnable scripts**: `scripts/run_system.py` (CLI), `src/api/main.py` (FastAPI). Use `python scripts/run_system.py --topic "..."` for manual runs; start API with `uvicorn src.api.main:app --reload`.

- **Install / test**:
  - Create venv and install: `python -m venv venv; venv\Scripts\activate; pip install -r requirements.txt`
  - Run tests: `pytest -v` (configured in `pyproject.toml` with coverage settings).

Architecture fundamentals (read these files to understand behavior):
- `src/agents/orchestrator/task_decomposer.py` — defines the task templates and DAG used for every proposal. Agent names (`agent_type`) here must match keys in the orchestrator registry.
- `src/agents/orchestrator/workflow_manager.py` — executes the DAG with concurrency, retries, progress updates, and persists state.
- `src/agents/orchestrator/central_orchestrator.py` — high-level coordinator that validates requests, wires agents, and assembles final `ProposalResponse`.
- `src/core/state_manager.py` — Redis-backed state and pub/sub. Shared outputs are saved under keys like `task_output_{task_id}` and published on channels `events:{request_id}`.
- `src/core/llm_provider.py` — LLM abstraction. Use `get_llm_provider()` or `LLMProvider.generate(...)` / `.generate_with_messages(...)` / `.generate_with_retry(...)`.
- `src/agents/base_agent.py` — canonical agent interface. Implementations should provide `validate_input` and `execute` and call `process_task()` for standard lifecycle (metrics, error handling, shared outputs).

Concrete patterns and conventions (do this, not that):
- Agent naming: the `agent_type` string used in task templates (e.g. `literature_review_agent`, `structure_formatting_agent`) must be the same key used when registering agents with `CentralOrchestrator.register_agent(...)`.
- Shared context: task outputs are saved under workflow shared context with keys `task_output_{task_id}`. When preparing inputs, dependent tasks are available as `dependency_{dep_id}` in `WorkflowManager._prepare_task_input`.
- Persistence: workflows and artifacts are stored via `StateManager` (Redis). Many methods call `set_shared_data(..., ttl=86400)` — expect 24-hour TTL by default.
- Retries and error handling: `WorkflowManager` uses `max_retries` and exponential backoff. Return an `AgentResponse` with `success=True` and `output` for success; otherwise include `error`/`error_details` for troubleshooting.
- LLM usage: prefer `LLMProvider.generate_with_retry(...)` for critical prompts. Agent code commonly sets `system_prompt` from agent config `role`.

Files to reference for concrete examples:
- Agent base: `src/agents/base_agent.py` — shows `process_task`, `generate_text`, `save_output`, `publish_event` usage patterns.
- Task templates: `src/agents/orchestrator/task_decomposer.py` — shows canonical `agent_type` and token/priority metadata.
- State keys & pub/sub: `src/core/state_manager.py` and `src/agents/orchestrator/workflow_manager.py` (look for `task_output_` and `events:{request_id}`).
- LLM provider: `src/core/llm_provider.py` — shows how Claude/OpenAI provider wrappers are used; prefer provider-agnostic calls via `get_llm_provider()`.

Development notes for AI contributors (actionable):
- When adding an agent implementation:
  - Subclass `BaseAgent`, implement `validate_input` and `execute`.
  - Ensure the agent name matches the entry in `config/agents_config.yaml` and `task_decomposer` templates.
  - Use `await self.save_output(request_id, key, value)` to expose outputs to subsequent tasks. Use keys prefixed `task_output_{task_id}` for compatibility.
- For prompt/template changes: keep LLM calls isolated in agent `.generate_text()` / `.generate_with_retry()` so retries, system prompts, and provider selection remain consistent.
- For MCC/MCP connectors: follow `src/mcp_servers/base_mcp.py` contract (implement `search` / `fetch` methods). Register connectors in `config/mcp_config.yaml`.

Debug & troubleshooting quick tips:
- To inspect workflow state: connect to Redis (default URL in `.env` / `config`) and query keys `workflow:{workflow_id}` and `shared:{workflow_id}:*`.
- To reproduce a failed task locally: identify `task_id` in `workflow_state` and run its agent's `process_task()` with a constructed `AgentRequest` (see `src/models/agent_messages.py` for schema).
- Logging: `loguru` is used; adjust `log_level` in `src/core/config.py` or `.env` for more detail.

What NOT to change without coordination:
- Task IDs and `agent_type` strings in `task_decomposer` — changing these breaks workflows and registration mapping.
- Shared state key formats (`task_output_{task_id}`) and Redis TTL assumptions — many parts assume this convention.

If anything is unclear or you need more examples (e.g., a minimal agent skeleton or a unit test template), say which area and I will add a short, ready-to-run example and tests.

## Minimal Agent Skeleton (example)

Below is a minimal, copy-pasteable agent implementation that follows `BaseAgent` patterns used across the codebase. Save as `src/agents/example_agent.py` when you want to run it.

```python
from typing import Any, Dict

from src.agents.base_agent import BaseAgent
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class ExampleAgent(BaseAgent):
  """Minimal example agent used for tests and onboarding."""

  def __init__(self) -> None:
    super().__init__(agent_name="example_agent")

  async def validate_input(self, input_data: Dict[str, Any]) -> bool:
    # Simple validation: require a non-empty 'topic'
    return bool(input_data.get("topic"))

  async def execute(self, request: AgentRequest) -> AgentResponse:
    # Simple processing: echo the topic and return structured output
    topic = request.input_data.get("topic", "")
    content = f"ExampleAgent processed topic: {topic}"

    return AgentResponse(
      task_id=request.task_id,
      agent_name=self.agent_name,
      status=TaskStatus.COMPLETED,
      output_data={"content": content},
      metadata={"example": True},
    )

```

## Unit test example (pytest + asyncio)

Use this pattern to write lightweight unit tests for agents. Save as `tests/test_example_agent.py`.

```python
import pytest

from src.agents.example_agent import ExampleAgent
from src.models.agent_messages import AgentRequest


@pytest.mark.asyncio
async def test_example_agent_process():
  agent = ExampleAgent()

  request = AgentRequest(
    task_id="test_task",
    agent_name="example_agent",
    action="process",
    input_data={"topic": "Unit test topic"},
    context={},
    dependencies=[],
  )

  response = await agent.process_task(request)

  assert response.status.name == "COMPLETED"
  assert response.output_data
  assert "ExampleAgent processed topic" in response.output_data.get("content", "")

```

Run the test with:

```powershell
venv\Scripts\activate
pytest tests/test_example_agent.py -q
```

Notes:
- Use `agent.process_task(request)` (not `agent.execute`) when testing; `process_task` wraps validation, metrics, and error handling.
- When writing more realistic tests, you can inject a mock `llm_provider` into the agent constructor to avoid external API calls.

---

If you want, I can create `src/agents/example_agent.py` and `tests/test_example_agent.py` files now and run the tests. Should I proceed?

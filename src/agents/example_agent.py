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

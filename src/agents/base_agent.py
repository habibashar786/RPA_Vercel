"""
Base agent class for all specialized agents.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel

from src.core.config import get_agent_config, get_settings
from src.core.llm_provider import LLMProvider, get_llm_provider
from src.core.state_manager import StateManager, get_state_manager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    role: str = ""
    capabilities: List[str] = []
    timeout: int = 300


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(
        self,
        agent_name: str,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize base agent.

        Args:
            agent_name: Name of the agent
            llm_provider: LLM provider instance
            state_manager: State manager instance
        """
        self.agent_name = agent_name
        self.settings = get_settings()
        self.agent_config = self._load_config()

        # Initialize LLM provider
        self.llm = llm_provider or get_llm_provider(
            model=self.agent_config.model,
            temperature=self.agent_config.temperature,
            max_tokens=self.agent_config.max_tokens,
        )

        # Initialize state manager
        self.state = state_manager or get_state_manager()

        # Agent metadata
        self.agent_id = str(uuid4())
        self.created_at = datetime.now()
        self.task_count = 0
        self.total_processing_time = 0.0

        logger.info(f"Initialized agent: {self.agent_name} ({self.agent_id})")

    def _load_config(self) -> AgentConfig:
        """Load agent configuration from config file."""
        config_loader = get_agent_config()
        raw_config = config_loader.get_agent_config(self.agent_name)

        if not raw_config:
            logger.warning(f"No configuration found for agent: {self.agent_name}")
            return AgentConfig(
                name=self.agent_name,
                model=self.settings.default_model,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
            )

        return AgentConfig(
            name=raw_config.get("name", self.agent_name),
            model=raw_config.get("model", self.settings.default_model),
            temperature=raw_config.get("temperature", 0.7),
            max_tokens=raw_config.get("max_tokens", 4096),
            role=raw_config.get("role", ""),
            capabilities=raw_config.get("capabilities", []),
            timeout=raw_config.get("timeout", 300),
        )

    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute agent task.

        This is the main entry point for agent execution.
        Must be implemented by each specialized agent.

        Args:
            request: Agent request with task details

        Returns:
            AgentResponse: Agent response with results
        """
        pass

    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before processing.

        Args:
            input_data: Input data dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        pass

    async def process_task(self, request: AgentRequest) -> AgentResponse:
        """
        Process a task with error handling and metrics.

        Args:
            request: Agent request

        Returns:
            AgentResponse: Response with results or error
        """
        start_time = time.time()
        self.task_count += 1

        try:
            # Validate input
            if not await self.validate_input(request.input_data):
                return AgentResponse(
                    task_id=request.task_id,
                    agent_name=self.agent_name,
                    status=TaskStatus.FAILED,
                    error="Input validation failed",
                    execution_time=time.time() - start_time,
                )

            # Execute task
            logger.info(f"Agent {self.agent_name} processing task: {request.task_id}")
            response = await self.execute(request)

            # Update metrics
            execution_time = time.time() - start_time
            self.total_processing_time += execution_time
            response.execution_time = execution_time

            logger.info(
                f"Agent {self.agent_name} completed task {request.task_id} "
                f"in {execution_time:.2f}s"
            )

            return response

        except Exception as e:
            logger.error(f"Agent {self.agent_name} failed task {request.task_id}: {e}")
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.FAILED,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text using LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional LLM parameters

        Returns:
            str: Generated text
        """
        # Use agent's role as default system prompt
        if system_prompt is None and self.agent_config.role:
            system_prompt = self.agent_config.role

        try:
            response = await self.llm.generate(prompt, system_prompt, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise

    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> str:
        """
        Generate text with automatic retry.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_retries: Maximum retry attempts
            **kwargs: Additional LLM parameters

        Returns:
            str: Generated text
        """
        if system_prompt is None and self.agent_config.role:
            system_prompt = self.agent_config.role

        return await self.llm.generate_with_retry(
            prompt, system_prompt, max_retries, **kwargs
        )

    async def save_output(
        self, request_id: str, key: str, value: Any, ttl: int = 86400
    ) -> bool:
        """
        Save output data to shared state.

        Args:
            request_id: Workflow request ID
            key: Data key
            value: Data value
            ttl: Time to live in seconds

        Returns:
            bool: Success status
        """
        try:
            return await self.state.set_shared_data(request_id, key, value, ttl)
        except Exception as e:
            logger.error(f"Failed to save output: {e}")
            return False

    async def get_shared_output(self, request_id: str, key: str) -> Optional[Any]:
        """
        Get shared output from another agent.

        Args:
            request_id: Workflow request ID
            key: Data key

        Returns:
            Optional[Any]: Shared data or None
        """
        try:
            return await self.state.get_shared_data(request_id, key)
        except Exception as e:
            logger.error(f"Failed to get shared output: {e}")
            return None

    async def publish_event(
        self, event_type: str, data: Dict[str, Any], request_id: str
    ) -> bool:
        """
        Publish an event for other agents.

        Args:
            event_type: Type of event
            data: Event data
            request_id: Workflow request ID

        Returns:
            bool: Success status
        """
        try:
            message = {
                "event_type": event_type,
                "agent": self.agent_name,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "data": data,
            }
            channel = f"events:{request_id}"
            return await self.state.publish_message(channel, message)
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.

        Returns:
            Dict[str, Any]: Performance metrics
        """
        avg_time = (
            self.total_processing_time / self.task_count if self.task_count > 0 else 0
        )

        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "task_count": self.task_count,
            "total_processing_time": self.total_processing_time,
            "average_task_time": avg_time,
            "uptime": (datetime.now() - self.created_at).total_seconds(),
        }

    def __repr__(self) -> str:
        """String representation of agent."""
        return f"<{self.__class__.__name__}(name={self.agent_name}, id={self.agent_id})>"

"""
Agent communication message models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of an agent task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class MessageType(str, Enum):
    """Type of agent message."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    FEEDBACK = "feedback"


class AgentMessage(BaseModel):
    """Base message for agent communication."""

    message_id: str
    message_type: MessageType
    sender: str
    receiver: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    content: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentRequest(BaseModel):
    """Request message sent to an agent."""

    task_id: str
    agent_name: str
    action: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    timeout: int = 300  # seconds
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.now)


class AgentResponse(BaseModel):
    """Response message from an agent."""

    task_id: str
    agent_name: str
    status: TaskStatus
    output_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    token_usage: Optional[Dict[str, int]] = None
    next_actions: List[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=datetime.now)


class FeedbackMessage(BaseModel):
    """Feedback from QA or other review agents."""

    feedback_id: str
    task_id: str
    source_agent: str
    target_agent: str
    feedback_type: str = Field(default="revision_required")
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    approved: bool = False
    iteration: int = 1
    created_at: datetime = Field(default_factory=datetime.now)


class TaskDependency(BaseModel):
    """Dependency between tasks."""

    source_task: str
    target_task: str
    dependency_type: str = "sequential"  # sequential, parallel, optional
    required_data: List[str] = Field(default_factory=list)


class AgentCapability(BaseModel):
    """Capability definition for an agent."""

    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    required_tools: List[str] = Field(default_factory=list)
    estimated_time: Optional[int] = None  # seconds


class AgentRegistration(BaseModel):
    """Agent registration information."""

    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: List[AgentCapability] = Field(default_factory=list)
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    status: str = "active"
    registered_at: datetime = Field(default_factory=datetime.now)
    last_heartbeat: datetime = Field(default_factory=datetime.now)

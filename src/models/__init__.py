"""
Data models for the Research Proposal Generation System.
"""

from src.models.proposal_schema import (
    ProposalRequest,
    ProposalResponse,
    ProposalSection,
    ProposalMetadata,
)
from src.models.agent_messages import (
    AgentMessage,
    AgentRequest,
    AgentResponse,
    TaskStatus,
)
from src.models.workflow_state import (
    WorkflowState,
    WorkflowStatus,
    TaskResult,
    Task,
)

__all__ = [
    # Proposal models
    "ProposalRequest",
    "ProposalResponse",
    "ProposalSection",
    "ProposalMetadata",
    # Agent messages
    "AgentMessage",
    "AgentRequest",
    "AgentResponse",
    "TaskStatus",
    # Workflow models
    "WorkflowState",
    "WorkflowStatus",
    "TaskResult",
    "Task",
]

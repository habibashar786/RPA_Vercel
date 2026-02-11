"""
Workflow state management models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Overall workflow status."""

    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageType(str, Enum):
    """Workflow stages."""

    INITIALIZATION = "initialization"
    LITERATURE_REVIEW = "literature_review"
    INTRODUCTION = "introduction"
    METHODOLOGY = "methodology"
    VISUALIZATION = "visualization"
    QUALITY_ASSURANCE = "quality_assurance"
    FINALIZATION = "finalization"
    EXPORT = "export"


class Task(BaseModel):
    """Individual task in the workflow."""

    task_id: str
    task_name: str
    agent_name: str
    action: str
    status: str = "pending"
    dependencies: List[str] = Field(default_factory=list)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class TaskResult(BaseModel):
    """Result of a completed task."""

    task_id: str
    agent_name: str
    status: str
    output: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    duration: float = 0.0
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    completed_at: datetime = Field(default_factory=datetime.now)


class WorkflowState(BaseModel):
    """State of the entire workflow."""

    request_id: str
    status: WorkflowStatus = WorkflowStatus.INITIALIZED
    current_stage: StageType = StageType.INITIALIZATION
    progress_percentage: float = 0.0

    # Task management
    total_tasks: int = 0
    completed_tasks: List[TaskResult] = Field(default_factory=list)
    pending_tasks: List[Task] = Field(default_factory=list)
    active_tasks: List[Task] = Field(default_factory=list)
    failed_tasks: List[Task] = Field(default_factory=list)
    # Backwards-compatible single-error field
    error: Optional[str] = None

    # Data accumulation
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    generated_sections: Dict[str, Any] = Field(default_factory=dict)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    diagrams: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration: float = 0.0

    # Quality metrics
    quality_checks_passed: int = 0
    quality_checks_failed: int = 0
    revision_iterations: int = 0

    def update_progress(self) -> None:
        """Calculate and update progress percentage."""
        if self.total_tasks > 0:
            completed = len(self.completed_tasks)
            self.progress_percentage = (completed / self.total_tasks) * 100

        # Compatibility aliases for older code that used different names
        @property
        def tasks_pending(self) -> List[Task]:
            return self.pending_tasks

        @tasks_pending.setter
        def tasks_pending(self, value: List[Task]) -> None:
            self.pending_tasks = value

        @property
        def tasks_active(self) -> List[Task]:
            return self.active_tasks

        @tasks_active.setter
        def tasks_active(self, value: List[Task]) -> None:
            self.active_tasks = value

        @property
        def tasks_completed(self) -> List[TaskResult]:
            return self.completed_tasks

        @tasks_completed.setter
        def tasks_completed(self, value: List[TaskResult]) -> None:
            self.completed_tasks = value

        @property
        def tasks_failed(self) -> List[Task]:
            return self.failed_tasks

        @tasks_failed.setter
        def tasks_failed(self, value: List[Task]) -> None:
            self.failed_tasks = value

    def add_completed_task(self, result: TaskResult) -> None:
        """Add a completed task result."""
        self.completed_tasks.append(result)
        # Remove from active tasks
        self.active_tasks = [t for t in self.active_tasks if t.task_id != result.task_id]
        self.update_progress()

    def add_failed_task(self, task: Task) -> None:
        """Add a failed task."""
        self.failed_tasks.append(task)
        # Remove from active tasks
        self.active_tasks = [t for t in self.active_tasks if t.task_id != task.task_id]
        self.update_progress()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID from any list."""
        all_tasks = self.pending_tasks + self.active_tasks + self.failed_tasks
        for task in all_tasks:
            if task.task_id == task_id:
                return task

        # Check completed tasks
        for result in self.completed_tasks:
            if result.task_id == task_id:
                # Create task from result
                return Task(
                    task_id=result.task_id,
                    task_name=result.task_id,
                    agent_name=result.agent_name,
                    action="completed",
                    status="completed",
                )
        return None

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return (
            self.status == WorkflowStatus.COMPLETED
            and len(self.pending_tasks) == 0
            and len(self.active_tasks) == 0
        )

    def has_failures(self) -> bool:
        """Check if workflow has failures."""
        return len(self.failed_tasks) > 0 or len(self.errors) > 0


class WorkflowCheckpoint(BaseModel):
    """Checkpoint for workflow recovery."""

    checkpoint_id: str
    request_id: str
    workflow_state: WorkflowState
    stage: StageType
    timestamp: datetime = Field(default_factory=datetime.now)
    recoverable: bool = True


class WorkflowMetrics(BaseModel):
    """Metrics for workflow execution."""

    request_id: str
    total_duration: float
    agent_times: Dict[str, float] = Field(default_factory=dict)
    mcp_query_time: float = 0.0
    llm_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    papers_reviewed: int = 0
    sections_generated: int = 0
    revisions_made: int = 0
    final_word_count: int = 0
    quality_score: Optional[float] = None

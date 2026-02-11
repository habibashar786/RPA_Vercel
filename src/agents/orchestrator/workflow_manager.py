"""
Workflow Manager - Executes task DAG and manages workflow state.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.agents.orchestrator.task_decomposer import TaskGraph
from src.core.state_manager import StateManager, get_state_manager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus
from src.models.workflow_state import (
    Task,
    TaskResult,
    WorkflowState,
    WorkflowStatus,
)


class WorkflowExecutionError(Exception):
    """Exception raised during workflow execution."""
    
    def __init__(self, message: str, task_id: Optional[str] = None, details: Optional[Dict] = None):
        """Initialize workflow execution error."""
        super().__init__(message)
        self.task_id = task_id
        self.details = details or {}


class WorkflowManager:
    """
    Manages workflow execution using DAG-based task scheduling.
    
    Handles:
    - Parallel task execution
    - Dependency management
    - Error handling and retries
    - Progress tracking
    - State persistence
    """
    
    def __init__(
        self,
        workflow_id: str,
        task_graph: TaskGraph,
        agent_registry: Dict[str, BaseAgent],
        state_manager: Optional[StateManager] = None,
        max_parallel_tasks: int = 5,
        max_retries: int = 3,
    ):
        """
        Initialize workflow manager.
        
        Args:
            workflow_id: Unique workflow identifier
            task_graph: Task dependency graph
            agent_registry: Map of agent_type -> agent instance
            state_manager: State manager for persistence
            max_parallel_tasks: Maximum concurrent tasks
            max_retries: Maximum retry attempts per task
        """
        self.workflow_id = workflow_id
        self.task_graph = task_graph
        self.agent_registry = agent_registry
        self.state = state_manager or get_state_manager()
        self.max_parallel_tasks = max_parallel_tasks
        self.max_retries = max_retries
        
        # Execution tracking
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Workflow state
        self.workflow_state: Optional[WorkflowState] = None
        
        logger.info(
            f"WorkflowManager initialized: workflow_id={workflow_id}, "
            f"tasks={len(task_graph.tasks)}, max_parallel={max_parallel_tasks}"
        )
    
    async def execute(self) -> WorkflowState:
        """
        Execute the workflow.
        
        Returns:
            WorkflowState: Final workflow state
            
        Raises:
            WorkflowExecutionError: If workflow execution fails
        """
        logger.info(f"Starting workflow execution: {self.workflow_id}")
        
        # Initialize workflow state
        await self._initialize_workflow_state()
        
        try:
            # Execute tasks
            await self._execute_dag()
            
            # Mark workflow as complete
            self.workflow_state.status = WorkflowStatus.COMPLETED
            self.workflow_state.completed_at = datetime.now()
            
            logger.info(f"Workflow completed successfully: {self.workflow_id}")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            self.workflow_state.status = WorkflowStatus.FAILED
            self.workflow_state.error = str(e)
            raise WorkflowExecutionError(f"Workflow execution failed: {e}")
        
        finally:
            # Save final state
            await self._save_workflow_state()
        
        return self.workflow_state
    
    async def _initialize_workflow_state(self) -> None:
        """Initialize workflow state."""
        self.workflow_state = WorkflowState(
            request_id=self.workflow_id,
            status=WorkflowStatus.RUNNING,
            current_stage=self.task_graph.tasks[0].metadata.get("stage", "initialization") if self.task_graph.tasks else "initialization",
            total_tasks=len(self.task_graph.tasks),
            pending_tasks=[],
            active_tasks=[],
            completed_tasks=[],
            failed_tasks=[],
            shared_context={},
            created_at=datetime.now(),
        )
        
        await self._save_workflow_state()
        logger.info(f"Initialized workflow state: {self.workflow_id}")
    
    async def _execute_dag(self) -> None:
        """Execute task DAG with parallel processing."""
        while True:
            # Get tasks ready for execution
            ready_tasks = self.task_graph.get_ready_tasks(self.completed_tasks)
            
            # Filter out failed task dependencies
            ready_tasks = [
                task for task in ready_tasks
                if not self._has_failed_dependencies(task)
            ]
            
            # No more tasks to execute
            if not ready_tasks and not self.active_tasks:
                break
            
            # Start new tasks (up to max parallel limit)
            available_slots = self.max_parallel_tasks - len(self.active_tasks)
            tasks_to_start = ready_tasks[:available_slots]
            
            for task in tasks_to_start:
                await self._start_task(task)
            
            # Wait for at least one task to complete
            if self.active_tasks:
                done, pending = await asyncio.wait(
                    self.active_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                
                # Process completed tasks
                for completed_task in done:
                    await self._handle_task_completion(completed_task)
            
            # Update progress
            await self._update_progress()
            
            # Check if workflow should fail
            if self.failed_tasks and not ready_tasks and not self.active_tasks:
                failed_critical = any(
                    self.task_graph.get_task_by_id(task_id).priority >= 9
                    for task_id in self.failed_tasks
                )
                if failed_critical:
                    raise WorkflowExecutionError(
                        f"Critical tasks failed: {self.failed_tasks}",
                        details={"failed_tasks": list(self.failed_tasks)},
                    )
    
    def _has_failed_dependencies(self, task: Task) -> bool:
        """Check if task has failed dependencies."""
        dependencies = self.task_graph.dependencies.get(task.task_id, [])
        return any(dep_id in self.failed_tasks for dep_id in dependencies)
    
    async def _start_task(self, task: Task) -> None:
        """
        Start task execution.
        
        Args:
            task: Task to execute
        """
        logger.info(f"Starting task: {task.task_id} - {task.task_name}")
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS.value
        task.started_at = datetime.now()
        
        # Update workflow state
        if task.task_id in [t.task_id for t in self.workflow_state.pending_tasks]:
            self.workflow_state.pending_tasks = [t for t in self.workflow_state.pending_tasks if t.task_id != task.task_id]
        self.workflow_state.active_tasks.append(task)
        await self._save_workflow_state()
        
        # Create asyncio task
        async_task = asyncio.create_task(
            self._execute_task(task),
            name=task.task_id,
        )
        self.active_tasks[task.task_id] = async_task
    
    async def _execute_task(self, task: Task) -> TaskResult:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            TaskResult: Task execution result
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # Get agent for this task
                agent = self.agent_registry.get(task.agent_name)
                if not agent:
                    raise ValueError(f"No agent registered for type: {task.agent_name}")
                
                # Prepare agent request
                agent_request = AgentRequest(
                    task_id=task.task_id,
                    agent_name=task.agent_name,
                    action="process",
                    input_data=await self._prepare_task_input(task),
                    context=self.workflow_state.shared_context,
                    priority="high" if task.priority >= 8 else "normal",
                )
                
                # Execute task
                logger.debug(f"Executing task {task.task_id} with agent {task.agent_name}")
                agent_response = await agent.process_task(agent_request)
                
                # Create task result
                if agent_response.status == TaskStatus.COMPLETED:
                    result = TaskResult(
                        task_id=task.task_id,
                        agent_name=task.agent_name,
                        status=TaskStatus.COMPLETED.value,
                        output=agent_response.output_data,
                        metadata=agent_response.metadata,
                    )
                    
                    # Store output in shared context
                    await self._store_task_output(task.task_id, agent_response.output_data)
                    
                    logger.info(f"Task completed successfully: {task.task_id}")
                    return result
                else:
                    last_error = agent_response.error or f"Task ended with status: {agent_response.status}"
                    logger.warning(
                        f"Task failed (attempt {retry_count + 1}/{self.max_retries + 1}): "
                        f"{task.task_id} - {last_error}"
                    )
                    retry_count += 1
                    
                    if retry_count <= self.max_retries:
                        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Task execution error: {task.task_id} - {e}", exc_info=True)
                retry_count += 1
                
                if retry_count <= self.max_retries:
                    await asyncio.sleep(2 ** retry_count)
        
        # All retries exhausted
        result = TaskResult(
            task_id=task.task_id,
            agent_name=task.agent_name,
            status=TaskStatus.FAILED.value,
            error=last_error or "Unknown error",
        )
        
        logger.error(f"Task failed after {self.max_retries} retries: {task.task_id}")
        return result
    
    async def _prepare_task_input(self, task: Task) -> Dict[str, Any]:
        """
        Prepare input data for task execution.
        
        Args:
            task: Task to prepare input for
            
        Returns:
            Dict[str, Any]: Task input data
        """
        input_data = task.input_data.copy()
        
        # Add outputs from dependency tasks
        dependencies = self.task_graph.dependencies.get(task.task_id, [])
        for dep_id in dependencies:
            dep_output = self.workflow_state.shared_context.get(f"task_output_{dep_id}")
            if dep_output:
                input_data[f"dependency_{dep_id}"] = dep_output
        
        return input_data
    
    async def _store_task_output(self, task_id: str, output: Dict[str, Any]) -> None:
        """
        Store task output in shared context.
        
        Args:
            task_id: Task identifier
            output: Task output data
        """
        key = f"task_output_{task_id}"
        self.workflow_state.shared_context[key] = output
        
        # Also save to Redis for persistence
        await self.state.set_shared_data(
            self.workflow_id,
            key,
            output,
            ttl=86400,  # 24 hours
        )
    
    async def _handle_task_completion(self, async_task: asyncio.Task) -> None:
        """
        Handle completed task.
        
        Args:
            async_task: Completed asyncio task
        """
        task_id = async_task.get_name()
        
        try:
            result = await async_task
            
            # Update tracking
            if result.status == TaskStatus.COMPLETED.value:
                self.completed_tasks.add(task_id)
                self.workflow_state.completed_tasks.append(result)
                logger.info(f"Task succeeded: {task_id}")
            else:
                self.failed_tasks.add(task_id)
                task_obj = self.task_graph.get_task_by_id(task_id)
                if task_obj:
                    self.workflow_state.failed_tasks.append(task_obj)
                logger.error(f"Task failed: {task_id} - {result.error}")
            
            # Update task status
            task = self.task_graph.get_task_by_id(task_id)
            if task:
                task.status = TaskStatus.COMPLETED.value if result.status == TaskStatus.COMPLETED.value else TaskStatus.FAILED.value
                task.completed_at = datetime.now()
            
            # Remove from active tasks
            self.workflow_state.active_tasks = [t for t in self.workflow_state.active_tasks if t.task_id != task_id]
            del self.active_tasks[task_id]
            
        except Exception as e:
            logger.error(f"Error handling task completion: {task_id} - {e}")
            self.failed_tasks.add(task_id)
            task_obj = self.task_graph.get_task_by_id(task_id)
            if task_obj:
                self.workflow_state.failed_tasks.append(task_obj)
            
            self.workflow_state.active_tasks = [t for t in self.workflow_state.active_tasks if t.task_id != task_id]
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    async def _update_progress(self) -> None:
        """Update workflow progress metrics."""
        total_tasks = len(self.task_graph.tasks)
        completed = len(self.completed_tasks)
        failed = len(self.failed_tasks)
        active = len(self.active_tasks)
        pending = total_tasks - completed - failed - active
        
        progress = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        self.workflow_state.progress_percentage = round(progress, 2)
        
        # Update current stage based on active tasks
        if self.active_tasks:
            active_task_ids = list(self.active_tasks.keys())
            active_task = self.task_graph.get_task_by_id(active_task_ids[0])
            if active_task:
                self.workflow_state.current_stage = active_task.metadata.get(
                    "stage",
                    self.workflow_state.current_stage,
                )
        
        # Save state
        await self._save_workflow_state()
        
        logger.debug(
            f"Progress: {progress:.1f}% "
            f"(completed={completed}, active={active}, pending={pending}, failed={failed})"
        )
    
    async def _save_workflow_state(self) -> None:
        """Save workflow state to Redis."""
        try:
            await self.state.save_workflow_state(self.workflow_state)
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
    
    async def pause(self) -> None:
        """Pause workflow execution."""
        logger.info(f"Pausing workflow: {self.workflow_id}")
        self.workflow_state.status = WorkflowStatus.PAUSED
        await self._save_workflow_state()
        
        # Cancel active tasks
        for task_id, async_task in self.active_tasks.items():
            async_task.cancel()
            logger.debug(f"Cancelled task: {task_id}")
    
    async def resume(self) -> WorkflowState:
        """
        Resume paused workflow.
        
        Returns:
            WorkflowState: Workflow state after resume
        """
        if self.workflow_state.status != WorkflowStatus.PAUSED:
            raise ValueError("Workflow is not paused")
        
        logger.info(f"Resuming workflow: {self.workflow_id}")
        self.workflow_state.status = WorkflowStatus.RUNNING
        await self._save_workflow_state()
        
        return await self.execute()
    
    async def cancel(self) -> None:
        """Cancel workflow execution."""
        logger.info(f"Cancelling workflow: {self.workflow_id}")
        self.workflow_state.status = WorkflowStatus.CANCELLED
        await self._save_workflow_state()
        
        # Cancel all active tasks
        for task_id, async_task in self.active_tasks.items():
            async_task.cancel()
            logger.debug(f"Cancelled task: {task_id}")
        
        self.active_tasks.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current workflow status.
        
        Returns:
            Dict[str, Any]: Workflow status information
        """
        return {
            "workflow_id": self.workflow_id,
            "status": self.workflow_state.status.value,
            "progress": self.workflow_state.progress_percentage,
            "current_stage": self.workflow_state.current_stage,
            "tasks": {
                "total": len(self.task_graph.tasks),
                "completed": len(self.completed_tasks),
                "active": len(self.active_tasks),
                "pending": len(self.workflow_state.tasks_pending),
                "failed": len(self.failed_tasks),
            },
            "created_at": self.workflow_state.created_at.isoformat(),
            "completed_at": (
                self.workflow_state.completed_at.isoformat()
                if self.workflow_state.completed_at
                else None
            ),
        }
    
    async def get_task_results(self) -> List[TaskResult]:
        """
        Get results from all completed tasks.
        
        Returns:
            List[TaskResult]: Task results
        """
        results = []
        for task in self.task_graph.tasks:
            if task.result:
                results.append(task.result)
        return results
    
    async def cleanup(self) -> None:
        """Cleanup workflow resources."""
        logger.info(f"Cleaning up workflow: {self.workflow_id}")
        
        # Cancel any remaining active tasks
        for async_task in self.active_tasks.values():
            if not async_task.done():
                async_task.cancel()
        
        # Clear tracking sets
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.active_tasks.clear()

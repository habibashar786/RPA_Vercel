"""
Central Orchestrator - Main coordinator for research proposal generation.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.agents.orchestrator.task_decomposer import TaskDecomposer, TaskGraph
from src.agents.orchestrator.workflow_manager import WorkflowManager, WorkflowExecutionError
from src.core.config import get_settings
from src.core.llm_provider import LLMProvider, get_llm_provider
from src.core.state_manager import StateManager, get_state_manager
from src.models.proposal_schema import (
    ProposalRequest,
    ProposalResponse,
    ProposalMetadata,
    ProposalSection,
)
from src.models.workflow_state import WorkflowState, WorkflowStatus


class OrchestratorError(Exception):
    """Exception raised by orchestrator."""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, details: Optional[Dict] = None):
        """Initialize orchestrator error."""
        super().__init__(message)
        self.workflow_id = workflow_id
        self.details = details or {}


class CentralOrchestrator(BaseAgent):
    """
    Central Orchestrator Agent - Coordinates entire proposal generation workflow.
    
    Responsibilities:
    - Receive and validate proposal requests
    - Decompose requests into tasks
    - Manage agent registry
    - Execute workflow via WorkflowManager
    - Assemble final proposal
    - Handle errors and recovery
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize central orchestrator.
        
        Args:
            llm_provider: LLM provider for text generation
            state_manager: State manager for persistence
        """
        super().__init__(
            agent_name="central_orchestrator",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        self.settings = get_settings()
        self.task_decomposer = TaskDecomposer()
        self.agent_registry: Dict[str, BaseAgent] = {}
        
        # Active workflows
        self.active_workflows: Dict[str, WorkflowManager] = {}
        
        logger.info("CentralOrchestrator initialized")
    
    def register_agent(self, agent_type: str, agent: BaseAgent) -> None:
        """
        Register an agent for task execution.
        
        Args:
            agent_type: Type/name of the agent
            agent: Agent instance
        """
        self.agent_registry[agent_type] = agent
        logger.info(f"Registered agent: {agent_type} ({agent.__class__.__name__})")
    
    def register_agents(self, agents: Dict[str, BaseAgent]) -> None:
        """
        Register multiple agents at once.
        
        Args:
            agents: Dictionary of agent_type -> agent instance
        """
        for agent_type, agent in agents.items():
            self.register_agent(agent_type, agent)
        
        logger.info(f"Registered {len(agents)} agents")
    
    async def generate_proposal(
        self,
        request: ProposalRequest,
    ) -> ProposalResponse:
        """
        Generate research proposal from request.
        
        Args:
            request: Proposal generation request
            
        Returns:
            ProposalResponse: Complete proposal
            
        Raises:
            OrchestratorError: If proposal generation fails
        """
        request_id = str(uuid.uuid4())
        workflow_id = request_id  # Use request_id as workflow_id
        logger.info(f"Starting proposal generation: request_id={request_id}, topic={request.topic}")
        
        try:
            # Validate request
            self._validate_request(request)
            
            # Decompose into tasks
            task_graph = self.task_decomposer.decompose(request)
            logger.info(f"Task decomposition complete: {len(task_graph.tasks)} tasks")
            
            # Log critical path
            critical_path = self.task_decomposer.get_critical_path(task_graph)
            logger.info(f"Critical path: {critical_path}")
            
            # Estimate time
            time_estimate = self.task_decomposer.estimate_completion_time(task_graph)
            logger.info(
                f"Estimated completion time: {time_estimate['parallel_time_minutes']} minutes "
                f"({time_estimate['total_tasks']} tasks, {time_estimate['total_estimated_tokens']:,} tokens)"
            )
            
            # Create workflow manager
            workflow_manager = WorkflowManager(
                workflow_id=workflow_id,
                task_graph=task_graph,
                agent_registry=self.agent_registry,
                state_manager=self.state,
                max_parallel_tasks=request.preferences.get("max_parallel_tasks", 5),
                max_retries=request.preferences.get("max_retries", 3),
            )
            
            # Track workflow
            self.active_workflows[workflow_id] = workflow_manager
            
            # Execute workflow
            logger.info(f"Starting workflow execution: {workflow_id}")
            workflow_state = await workflow_manager.execute()
            
            # Check if workflow succeeded
            if workflow_state.status != WorkflowStatus.COMPLETED:
                raise OrchestratorError(
                    f"Workflow did not complete successfully: {workflow_state.status.value}",
                    workflow_id=workflow_id,
                    details={"error": workflow_state.error},
                )
            
            # Assemble final proposal
            logger.info(f"Assembling final proposal: {workflow_id}")
            proposal = await self._assemble_proposal(workflow_id, workflow_state, request)
            
            # Cleanup
            await workflow_manager.cleanup()
            del self.active_workflows[workflow_id]
            
            logger.info(f"Proposal generation completed: {workflow_id}")
            return proposal
            
        except WorkflowExecutionError as e:
            logger.error(f"Workflow execution failed: {e}")
            raise OrchestratorError(
                f"Workflow execution failed: {str(e)}",
                workflow_id=workflow_id,
                details=e.details if hasattr(e, 'details') else {},
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in proposal generation: {e}", exc_info=True)
            raise OrchestratorError(
                f"Proposal generation failed: {str(e)}",
                workflow_id=workflow_id,
            )
    
    def _validate_request(self, request: ProposalRequest) -> None:
        """
        Validate proposal request.
        
        Args:
            request: Proposal request to validate
            
        Raises:
            ValueError: If request is invalid
        """
        if not request.topic or len(request.topic.strip()) < 10:
            raise ValueError("Topic must be at least 10 characters")
        
        if not request.key_points or len(request.key_points) < 3:
            raise ValueError("At least 3 key points are required")
        
        # Check if required agents are registered
        required_agents = {
            "literature_review_agent",
            "research_methodology_agent",
            "quality_assurance_agent",
            "structure_formatting_agent",
        }
        
        missing_agents = required_agents - set(self.agent_registry.keys())
        if missing_agents:
            raise ValueError(f"Missing required agents: {', '.join(sorted(missing_agents))}")
        
        logger.debug("Request validation passed")
    
    async def _assemble_proposal(
        self,
        workflow_id: str,
        workflow_state: WorkflowState,
        request: ProposalRequest,
    ) -> ProposalResponse:
        """
        Assemble final proposal from workflow results.
        
        Args:
            workflow_id: Workflow identifier
            workflow_state: Final workflow state
            request: Original request
            
        Returns:
            ProposalResponse: Complete proposal
        """
        # Extract task outputs from shared context
        context = workflow_state.shared_context
        
        # Build sections from task outputs
        sections = []
        
        # Front Matter
        front_matter_data = context.get("task_output_generate_front_matter", {})
        if front_matter_data:
            sections.append(
                ProposalSection(
                    title="Front Matter",
                    content=front_matter_data.get("content", ""),
                    subsections=[],
                    metadata={
                        "abstract": front_matter_data.get("abstract", ""),
                        "keywords": front_matter_data.get("keywords", []),
                    },
                )
            )
        
        # Introduction
        intro_data = context.get("task_output_generate_introduction", {})
        if intro_data:
            sections.append(
                ProposalSection(
                    title="Introduction",
                    content=intro_data.get("content", ""),
                    subsections=intro_data.get("subsections", []),
                    metadata={
                        "problem_statement": intro_data.get("problem_statement", ""),
                        "objectives": intro_data.get("objectives", []),
                        "research_questions": intro_data.get("research_questions", []),
                    },
                )
            )
        
        # Literature Review
        lit_review_data = context.get("task_output_analyze_literature", {})
        if lit_review_data:
            sections.append(
                ProposalSection(
                    title="Literature Review",
                    content=lit_review_data.get("content", ""),
                    subsections=lit_review_data.get("subsections", []),
                    metadata={
                        "papers_reviewed": lit_review_data.get("papers_reviewed", 0),
                        "research_gaps": lit_review_data.get("research_gaps", []),
                    },
                )
            )
        
        # Methodology
        methodology_data = context.get("task_output_design_methodology", {})
        if methodology_data:
            sections.append(
                ProposalSection(
                    title="Research Methodology",
                    content=methodology_data.get("content", ""),
                    subsections=methodology_data.get("subsections", []),
                    metadata={
                        "design": methodology_data.get("design", ""),
                        "procedures": methodology_data.get("procedures", []),
                    },
                )
            )
        
        # Risk Assessment
        risk_data = context.get("task_output_assess_risks", {})
        if risk_data:
            sections.append(
                ProposalSection(
                    title="Risk Assessment",
                    content=risk_data.get("content", ""),
                    subsections=risk_data.get("subsections", []),
                    metadata={"risks": risk_data.get("risks", [])},
                )
            )
        
        # References
        citation_data = context.get("task_output_format_citations", {})
        references = citation_data.get("references", []) if citation_data else []
        
        # Calculate metrics
        total_words = sum(
            len(section.content.split()) +
            sum(
                len(subsec.content.split()) if hasattr(subsec, 'content') else len(subsec.get("content", "").split()) if isinstance(subsec, dict) else 0
                for subsec in section.subsections
            )
            for section in sections
        )
        
        # Create metadata
        metadata = ProposalMetadata(
            request_id=workflow_id,
            topic=request.topic if request.topic else "Untitled Research Proposal",
            total_word_count=total_words,
            agents_involved=list(self.agent_registry.keys()),
        )
        
        # Quality metrics
        qa_data = context.get("task_output_apply_revisions", {})
        quality_metrics = qa_data.get("quality_metrics", {}) if qa_data else {}
        
        # Create response
        proposal = ProposalResponse(
            request_id=workflow_id,
            metadata=metadata,
            sections=sections,
            references=references,
            export_urls={
                "pdf": "",  # To be generated by export service
                "docx": "",
                "latex": "",
            },
        )
        
        logger.info(
            f"Proposal assembled: {total_words} words, "
            f"{len(sections)} sections, {len(references)} references"
        )
        
        return proposal
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Dict[str, Any]: Workflow status
            
        Raises:
            ValueError: If workflow not found
        """
        workflow_manager = self.active_workflows.get(workflow_id)
        if not workflow_manager:
            # Try to load from state
            workflow_state = await self.state.get_workflow(workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            return {
                "workflow_id": workflow_id,
                "status": workflow_state.get("status", "unknown"),
                "progress": workflow_state.get("progress_percentage", 0),
                "current_stage": workflow_state.get("current_stage", ""),
                "active": False,
            }
        
        return workflow_manager.get_status()
    
    async def pause_workflow(self, workflow_id: str) -> None:
        """
        Pause a running workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Raises:
            ValueError: If workflow not found or not running
        """
        workflow_manager = self.active_workflows.get(workflow_id)
        if not workflow_manager:
            raise ValueError(f"Active workflow not found: {workflow_id}")
        
        await workflow_manager.pause()
        logger.info(f"Workflow paused: {workflow_id}")
    
    async def resume_workflow(self, workflow_id: str) -> WorkflowState:
        """
        Resume a paused workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            WorkflowState: Updated workflow state
            
        Raises:
            ValueError: If workflow not found or not paused
        """
        workflow_manager = self.active_workflows.get(workflow_id)
        if not workflow_manager:
            raise ValueError(f"Active workflow not found: {workflow_id}")
        
        logger.info(f"Resuming workflow: {workflow_id}")
        return await workflow_manager.resume()
    
    async def cancel_workflow(self, workflow_id: str) -> None:
        """
        Cancel a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Raises:
            ValueError: If workflow not found
        """
        workflow_manager = self.active_workflows.get(workflow_id)
        if not workflow_manager:
            raise ValueError(f"Active workflow not found: {workflow_id}")
        
        await workflow_manager.cancel()
        await workflow_manager.cleanup()
        del self.active_workflows[workflow_id]
        
        logger.info(f"Workflow cancelled: {workflow_id}")
    
    async def list_active_workflows(self) -> List[Dict[str, Any]]:
        """
        List all active workflows.
        
        Returns:
            List[Dict[str, Any]]: List of active workflow statuses
        """
        statuses = []
        for workflow_id, workflow_manager in self.active_workflows.items():
            try:
                status = workflow_manager.get_status()
                statuses.append(status)
            except Exception as e:
                logger.error(f"Error getting status for workflow {workflow_id}: {e}")
        
        return statuses
    
    async def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """
        Cleanup old completed workflows from state storage.
        
        Args:
            max_age_hours: Maximum age in hours for completed workflows
            
        Returns:
            int: Number of workflows cleaned up
        """
        # Get all workflows from state
        all_workflows = await self.state.list_workflows()
        
        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        for workflow_id in all_workflows:
            try:
                workflow_data = await self.state.get_workflow(workflow_id)
                if not workflow_data:
                    continue
                
                # Check if completed and old
                status = workflow_data.get("status")
                completed_at = workflow_data.get("completed_at")
                
                if status in ["completed", "failed", "cancelled"] and completed_at:
                    completed_timestamp = datetime.fromisoformat(completed_at).timestamp()
                    if completed_timestamp < cutoff_time:
                        await self.state.delete_workflow(workflow_id)
                        cleaned_count += 1
                        logger.debug(f"Cleaned up old workflow: {workflow_id}")
            
            except Exception as e:
                logger.error(f"Error cleaning up workflow {workflow_id}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old workflows")
        return cleaned_count
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of orchestrator and registered agents.
        
        Returns:
            Dict[str, Any]: Health status
        """
        agent_status = {}
        for agent_type, agent in self.agent_registry.items():
            try:
                metrics = agent.get_metrics()
                agent_status[agent_type] = {
                    "healthy": True,
                    "tasks_processed": metrics.get("total_tasks", 0),
                    "avg_execution_time": metrics.get("avg_execution_time", 0),
                }
            except Exception as e:
                agent_status[agent_type] = {
                    "healthy": False,
                    "error": str(e),
                }
        
        return {
            "orchestrator": {
                "healthy": True,
                "registered_agents": len(self.agent_registry),
                "active_workflows": len(self.active_workflows),
            },
            "agents": agent_status,
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute orchestrator task (BaseAgent interface).
        
        Args:
            input_data: Input data containing proposal request
            
        Returns:
            Dict[str, Any]: Execution result
        """
        # Create proposal request from input data
        request = ProposalRequest(**input_data)
        
        # Generate proposal
        proposal = await self.generate_proposal(request)
        
        # Return as dict
        return proposal.model_dump()
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data (BaseAgent interface).
        
        Args:
            input_data: Input data to validate
            
        Returns:
            bool: True if valid
        """
        try:
            ProposalRequest(**input_data)
            return True
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            return False

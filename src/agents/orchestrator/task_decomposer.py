"""
Task Decomposer - Breaks down proposal generation into atomic tasks.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from pydantic import BaseModel

from src.models.agent_messages import TaskDependency, TaskStatus
from src.models.proposal_schema import ProposalRequest
from src.models.workflow_state import Task, StageType as WorkflowStage


class TaskGraph(BaseModel):
    """Represents the task dependency graph."""
    
    tasks: List[Task]
    dependencies: Dict[str, List[str]]  # task_id -> list of dependent task_ids
    
    def get_ready_tasks(self, completed_task_ids: Set[str]) -> List[Task]:
        """
        Get tasks that are ready to execute (all dependencies completed).
        
        Args:
            completed_task_ids: Set of completed task IDs
            
        Returns:
            List[Task]: Tasks ready for execution
        """
        ready_tasks = []
        
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            task_deps = self.dependencies.get(task.task_id, [])
            if all(dep_id in completed_task_ids for dep_id in task_deps):
                ready_tasks.append(task)
        
        return ready_tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def validate_dag(self) -> bool:
        """
        Validate that the graph is a valid DAG (no cycles).
        
        Returns:
            bool: True if valid DAG, False otherwise
        """
        # Use DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for dep_id in self.dependencies.get(task_id, []):
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        for task in self.tasks:
            if task.task_id not in visited:
                if has_cycle(task.task_id):
                    return False
        
        return True


class TaskDecomposer:
    """
    Decomposes research proposal generation into atomic tasks.
    
    Creates a DAG of tasks with proper dependencies and priorities.
    """
    
    def __init__(self):
        """Initialize task decomposer."""
        self.task_templates = self._initialize_task_templates()
        logger.info("TaskDecomposer initialized")
    
    def _initialize_task_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize task templates for proposal generation.
        
        Returns:
            Dict[str, Dict]: Task templates with metadata
        """
        return {
            # Stage 1: Initialization
            "init_structure": {
                "name": "Initialize Document Structure",
                "description": "Create proposal outline and section placeholders",
                "stage": WorkflowStage.INITIALIZATION,
                "agent_type": "structure_formatting_agent",
                "priority": 10,
                "estimated_tokens": 500,
                "dependencies": [],
            },
            "generate_front_matter": {
                "name": "Generate Front Matter",
                "description": "Create abstract, keywords, dedication",
                "stage": WorkflowStage.INITIALIZATION,
                "agent_type": "front_matter_agent",
                "priority": 9,
                "estimated_tokens": 1000,
                "dependencies": ["init_structure"],
            },
            
            # Stage 2: Literature Review (Critical Path)
            "search_papers": {
                "name": "Search Academic Papers",
                "description": "Query MCP servers for relevant papers (30+ papers)",
                "stage": WorkflowStage.LITERATURE_REVIEW,
                "agent_type": "literature_review_agent",
                "priority": 10,
                "estimated_tokens": 2000,
                "dependencies": ["init_structure"],
            },
            "analyze_literature": {
                "name": "Analyze Literature",
                "description": "Analyze papers, identify gaps, synthesize findings",
                "stage": WorkflowStage.LITERATURE_REVIEW,
                "agent_type": "literature_review_agent",
                "priority": 10,
                "estimated_tokens": 8000,
                "dependencies": ["search_papers"],
            },
            "extract_citations": {
                "name": "Extract Citations",
                "description": "Extract and format citations from literature",
                "stage": WorkflowStage.LITERATURE_REVIEW,
                "agent_type": "reference_citation_agent",
                "priority": 8,
                "estimated_tokens": 1000,
                "dependencies": ["search_papers"],
            },
            
            # Stage 3: Introduction (depends on literature gaps)
            "generate_introduction": {
                "name": "Generate Introduction",
                "description": "Create problem statement, objectives, research questions",
                "stage": WorkflowStage.INTRODUCTION,
                "agent_type": "introduction_agent",
                "priority": 9,
                "estimated_tokens": 3000,
                "dependencies": ["analyze_literature"],
            },
            
            # Stage 4: Methodology
            "design_methodology": {
                "name": "Design Research Methodology",
                "description": "Create experimental design, procedures, tools",
                "stage": WorkflowStage.METHODOLOGY,
                "agent_type": "research_methodology_agent",
                "priority": 10,
                "estimated_tokens": 5000,
                "dependencies": ["generate_introduction"],
            },
            "create_diagrams": {
                "name": "Create Methodology Diagrams",
                "description": "Generate process flow diagrams and visualizations",
                "stage": WorkflowStage.VISUALIZATION,
                "agent_type": "visualization_agent",
                "priority": 7,
                "estimated_tokens": 2000,
                "dependencies": ["design_methodology"],
            },
            
            # Stage 5: Risk Assessment (parallel with methodology)
            "assess_risks": {
                "name": "Assess Research Risks",
                "description": "Identify and document potential risks and mitigations",
                "stage": WorkflowStage.METHODOLOGY,
                "agent_type": "risk_assessment_agent",
                "priority": 6,
                "estimated_tokens": 2000,
                "dependencies": ["design_methodology"],
            },
            
            # Stage 6: Optimization
            "optimize_methodology": {
                "name": "Optimize Methodology",
                "description": "AI-assisted methodology recommendations",
                "stage": WorkflowStage.METHODOLOGY,
                "agent_type": "methodology_optimizer_agent",
                "priority": 5,
                "estimated_tokens": 1500,
                "dependencies": ["design_methodology"],
            },
            
            # Stage 7: Quality Assurance (iterative)
            "quality_check_1": {
                "name": "Quality Check - First Pass",
                "description": "Review structure, coherence, Turnitin compliance",
                "stage": WorkflowStage.QUALITY_ASSURANCE,
                "agent_type": "quality_assurance_agent",
                "priority": 9,
                "estimated_tokens": 4000,
                "dependencies": [
                    "generate_introduction",
                    "design_methodology",
                    "analyze_literature",
                ],
            },
            "apply_revisions": {
                "name": "Apply QA Revisions",
                "description": "Implement quality assurance feedback",
                "stage": WorkflowStage.QUALITY_ASSURANCE,
                "agent_type": "quality_assurance_agent",
                "priority": 8,
                "estimated_tokens": 2000,
                "dependencies": ["quality_check_1"],
            },
            
            # Stage 8: AI Humanization (NEW - Critical for AI Detection)
            "humanize_content": {
                "name": "Humanize AI Content",
                "description": "Transform AI patterns to human-like writing, reduce AI detection score <10%",
                "stage": WorkflowStage.QUALITY_ASSURANCE,
                "agent_type": "ai_humanizer_agent",
                "priority": 9,
                "estimated_tokens": 3000,
                "dependencies": ["apply_revisions"],
            },
            
            # Stage 9: Finalization
            "format_citations": {
                "name": "Format Citations",
                "description": "Format all citations in Harvard style",
                "stage": WorkflowStage.FINALIZATION,
                "agent_type": "reference_citation_agent",
                "priority": 7,
                "estimated_tokens": 1500,
                "dependencies": ["humanize_content", "extract_citations"],
            },
            "final_formatting": {
                "name": "Final Document Formatting",
                "description": "Apply Q1 journal formatting standards",
                "stage": WorkflowStage.FINALIZATION,
                "agent_type": "structure_formatting_agent",
                "priority": 8,
                "estimated_tokens": 1000,
                "dependencies": ["format_citations"],
            },
            "generate_export": {
                "name": "Generate Export Files",
                "description": "Export to PDF and Word formats",
                "stage": WorkflowStage.EXPORT,
                "agent_type": "structure_formatting_agent",
                "priority": 6,
                "estimated_tokens": 500,
                "dependencies": ["final_formatting"],
            },
        }
    
    def decompose(self, request: ProposalRequest) -> TaskGraph:
        """
        Decompose proposal generation request into tasks.
        
        Args:
            request: Proposal generation request
            
        Returns:
            TaskGraph: Task dependency graph
        """
        logger.info(f"Decomposing request for topic: {request.topic}")
        
        tasks = []
        dependencies = {}
        
        # Create tasks from templates
        for task_id, template in self.task_templates.items():
            task = Task(
                task_id=task_id,
                task_name=template["name"],
                agent_name=template["agent_type"],
                action="process",
                status=TaskStatus.PENDING.value,
                dependencies=template.get("dependencies", []),
                priority=template.get("priority", 0),
                input_data={
                    "topic": request.topic,
                    "key_points": request.key_points,
                    "user_preferences": getattr(request, "preferences", {}),
                    "stage": template["stage"].value,
                    "estimated_tokens": template["estimated_tokens"],
                },
            )
            
            tasks.append(task)
            dependencies[task_id] = template["dependencies"]
        
        # Create task graph
        task_graph = TaskGraph(
            tasks=tasks,
            dependencies=dependencies,
        )
        
        # Validate DAG
        if not task_graph.validate_dag():
            raise ValueError("Invalid task graph: contains cycles")
        
        logger.info(f"Created task graph with {len(tasks)} tasks")
        self._log_task_summary(task_graph)
        
        return task_graph
    
    def _log_task_summary(self, task_graph: TaskGraph) -> None:
        """Log summary of task decomposition."""
        stage_counts = {}
        total_tokens = 0
        
        for task in task_graph.tasks:
            stage = task.metadata.get("stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            total_tokens += task.metadata.get("estimated_tokens", 0)
        
        logger.info(f"Task breakdown by stage:")
        for stage, count in sorted(stage_counts.items()):
            logger.info(f"  {stage}: {count} tasks")
        
        logger.info(f"Estimated total tokens: {total_tokens:,}")
    
    def get_critical_path(self, task_graph: TaskGraph) -> List[str]:
        """
        Calculate critical path through the task graph.
        
        Args:
            task_graph: Task dependency graph
            
        Returns:
            List[str]: Task IDs in critical path
        """
        # Simple critical path: tasks with highest priority and longest dependency chain
        def get_chain_length(task_id: str, memo: Dict[str, int]) -> int:
            if task_id in memo:
                return memo[task_id]
            
            deps = task_graph.dependencies.get(task_id, [])
            if not deps:
                memo[task_id] = 1
                return 1
            
            max_length = max(get_chain_length(dep, memo) for dep in deps)
            memo[task_id] = max_length + 1
            return memo[task_id]
        
        memo: Dict[str, int] = {}
        critical_tasks = []
        
        for task in task_graph.tasks:
            chain_length = get_chain_length(task.task_id, memo)
            if task.priority >= 9:  # High priority tasks
                critical_tasks.append((task.task_id, chain_length, task.priority))
        
        # Sort by chain length (descending) then priority (descending)
        critical_tasks.sort(key=lambda x: (-x[1], -x[2]))
        
        return [task_id for task_id, _, _ in critical_tasks]
    
    def estimate_completion_time(self, task_graph: TaskGraph) -> Dict[str, Any]:
        """
        Estimate completion time for the workflow.
        
        Args:
            task_graph: Task dependency graph
            
        Returns:
            Dict[str, Any]: Time estimates
        """
        # Rough estimates: 1000 tokens ≈ 2-3 seconds processing
        total_tokens = sum(
            task.metadata.get("estimated_tokens", 0) 
            for task in task_graph.tasks
        )
        
        # Sequential time (if all tasks run sequentially)
        sequential_time_seconds = (total_tokens / 1000) * 2.5
        
        # Parallel time (accounting for parallelizable tasks)
        # Estimate: ~60% of tasks can run in parallel
        parallel_time_seconds = sequential_time_seconds * 0.5
        
        return {
            "total_tasks": len(task_graph.tasks),
            "total_estimated_tokens": total_tokens,
            "sequential_time_seconds": int(sequential_time_seconds),
            "parallel_time_seconds": int(parallel_time_seconds),
            "sequential_time_minutes": round(sequential_time_seconds / 60, 1),
            "parallel_time_minutes": round(parallel_time_seconds / 60, 1),
        }
    
    def add_custom_task(
        self,
        task_graph: TaskGraph,
        task_id: str,
        name: str,
        description: str,
        agent_type: str,
        dependencies: List[str],
        priority: int = 5,
    ) -> TaskGraph:
        """
        Add a custom task to the task graph.
        
        Args:
            task_graph: Existing task graph
            task_id: Unique task identifier
            name: Task name
            description: Task description
            agent_type: Agent to execute task
            dependencies: List of task IDs this task depends on
            priority: Task priority (1-10)
            
        Returns:
            TaskGraph: Updated task graph
        """
        # Validate dependencies exist
        existing_ids = {task.task_id for task in task_graph.tasks}
        invalid_deps = [dep for dep in dependencies if dep not in existing_ids]
        
        if invalid_deps:
            raise ValueError(f"Invalid dependencies: {invalid_deps}")
        
        # Create new task
        new_task = Task(
            task_id=task_id,
            name=name,
            description=description,
            agent_type=agent_type,
            priority=priority,
            status=TaskStatus.PENDING,
            input_data={},
            metadata={"custom": True},
        )
        
        # Update graph
        task_graph.tasks.append(new_task)
        task_graph.dependencies[task_id] = dependencies
        
        # Validate DAG
        if not task_graph.validate_dag():
            raise ValueError("Adding this task creates a cycle in the graph")
        
        logger.info(f"Added custom task: {task_id}")
        return task_graph

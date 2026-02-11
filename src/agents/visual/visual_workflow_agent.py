"""
Visual Workflow Agent - Generates diagrams, flowcharts, and conceptual figures.
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from enum import Enum

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class DiagramType(Enum):
    WORKFLOW = "workflow"
    FLOWCHART = "flowchart"
    CONCEPTUAL = "conceptual"
    DATAFLOW = "dataflow"
    ARCHITECTURE = "architecture"
    GANTT = "gantt"


class VisualWorkflowAgent(BaseAgent):
    """Creates diagrams and conceptual figures for research proposals."""
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        super().__init__(
            agent_name="visual_workflow_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        self.generated_diagrams: Dict[str, Dict[str, Any]] = {}
        logger.info("VisualWorkflowAgent initialized")
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        try:
            input_data = request.input_data
            topic = input_data.get("topic", "")
            methodology = input_data.get("methodology", "")
            diagram_types = input_data.get("diagram_types", ["workflow", "flowchart", "conceptual"])
            
            logger.info(f"Generating visuals for topic: {topic}")
            
            diagrams = []
            for diagram_type in diagram_types:
                try:
                    diagram = await self._generate_diagram(diagram_type, topic, methodology)
                    if diagram:
                        diagrams.append(diagram)
                except Exception as e:
                    logger.warning(f"Failed to generate {diagram_type}: {e}")
            
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output_data={
                    "diagrams": diagrams,
                    "count": len(diagrams),
                    "formats_available": ["mermaid", "svg", "png"],
                },
            )
        except Exception as e:
            logger.error(f"Visual generation failed: {e}")
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.FAILED,
                error=str(e),
            )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "topic" in input_data
    
    async def _generate_diagram(self, diagram_type: str, topic: str, methodology: str) -> Optional[Dict[str, Any]]:
        generators = {
            "workflow": self._gen_workflow,
            "flowchart": self._gen_flowchart,
            "conceptual": self._gen_conceptual,
            "dataflow": self._gen_dataflow,
            "architecture": self._gen_architecture,
            "gantt": self._gen_gantt,
        }
        gen = generators.get(diagram_type)
        return await gen(topic, methodology) if gen else None
    
    async def _gen_workflow(self, topic: str, methodology: str) -> Dict[str, Any]:
        prompt = f"""Generate a Mermaid flowchart for research workflow on: {topic}
Show: Problem ID → Literature Review → Gap Analysis → Research Design → Data Collection → Analysis → Results → Conclusions
Use: flowchart TD with proper syntax. Output ONLY the mermaid code."""
        
        code = await self.generate_with_retry(prompt, max_tokens=1000)
        return {
            "id": str(uuid4())[:8],
            "type": "workflow",
            "title": "Research Workflow Diagram",
            "mermaid_code": self._extract_mermaid(code),
            "placement": "Chapter 1 or 3",
            "figure_number": "Figure 1",
        }
    
    async def _gen_flowchart(self, topic: str, methodology: str) -> Dict[str, Any]:
        prompt = f"""Generate a Mermaid methodology flowchart for: {topic}
Include: Research design, sampling, data collection, analysis steps.
Use subgraphs. Output ONLY mermaid code."""
        
        code = await self.generate_with_retry(prompt, max_tokens=1200)
        return {
            "id": str(uuid4())[:8],
            "type": "flowchart",
            "title": "Research Methodology Flowchart",
            "mermaid_code": self._extract_mermaid(code),
            "placement": "Chapter 3",
            "figure_number": "Figure 2",
        }
    
    async def _gen_conceptual(self, topic: str, methodology: str) -> Dict[str, Any]:
        prompt = f"""Generate a Mermaid conceptual framework diagram for: {topic}
Show: Independent variables, dependent variables, relationships.
Use flowchart LR with subgraphs. Output ONLY mermaid code."""
        
        code = await self.generate_with_retry(prompt, max_tokens=1000)
        return {
            "id": str(uuid4())[:8],
            "type": "conceptual",
            "title": "Conceptual Framework",
            "mermaid_code": self._extract_mermaid(code),
            "placement": "Chapter 1 or 2",
            "figure_number": "Figure 3",
        }
    
    async def _gen_dataflow(self, topic: str, methodology: str) -> Dict[str, Any]:
        prompt = f"""Generate a Mermaid data flow diagram for: {topic}
Show: Data sources → Collection → Preprocessing → Analysis → Output.
Use flowchart LR. Output ONLY mermaid code."""
        
        code = await self.generate_with_retry(prompt, max_tokens=1000)
        return {
            "id": str(uuid4())[:8],
            "type": "dataflow",
            "title": "Data Flow Diagram",
            "mermaid_code": self._extract_mermaid(code),
            "placement": "Chapter 3",
            "figure_number": "Figure 4",
        }
    
    async def _gen_architecture(self, topic: str, methodology: str) -> Dict[str, Any]:
        prompt = f"""Generate a Mermaid system architecture diagram for: {topic}
Show: Input layer, processing modules, output layer.
Use flowchart TB with subgraphs. Output ONLY mermaid code."""
        
        code = await self.generate_with_retry(prompt, max_tokens=1000)
        return {
            "id": str(uuid4())[:8],
            "type": "architecture",
            "title": "System Architecture",
            "mermaid_code": self._extract_mermaid(code),
            "placement": "Chapter 3",
            "figure_number": "Figure 5",
        }
    
    async def _gen_gantt(self, topic: str, methodology: str) -> Dict[str, Any]:
        return {
            "id": str(uuid4())[:8],
            "type": "gantt",
            "title": "Research Timeline",
            "mermaid_code": """gantt
    title Research Project Timeline
    dateFormat YYYY-MM-DD
    section Phase 1
    Literature Review :a1, 2024-01-01, 60d
    Problem Definition :a2, after a1, 30d
    section Phase 2
    Data Collection :b1, after a2, 60d
    Analysis :b2, after b1, 45d
    section Phase 3
    Writing :c1, after b2, 45d
    Revision :c2, after c1, 30d""",
            "placement": "Appendix A",
            "figure_number": "Figure A1",
        }
    
    def _extract_mermaid(self, text: str) -> str:
        match = re.search(r'```(?:mermaid)?\s*([\s\S]*?)```', text)
        if match:
            return match.group(1).strip()
        if any(k in text for k in ['flowchart', 'graph', 'gantt']):
            return text.strip()
        return "flowchart TD\n    A[Start] --> B[End]"

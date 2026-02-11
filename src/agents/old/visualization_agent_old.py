"""
Visualization Agent - Creates diagrams and visualizations.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager


class VisualizationAgent(BaseAgent):
    """
    Visualization Agent - Creates process flows and diagrams.
    
    Responsibilities:
    - Generate Mermaid.js flowcharts and diagrams
    - Create process flow diagrams for methodology
    - Generate data flow diagrams
    - Create architectural diagrams
    - Produce timeline/Gantt charts
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize visualization agent.
        
        Args:
            llm_provider: LLM provider for diagram generation
            state_manager: State manager for persistence
        """
        super().__init__(
            agent_name="visualization_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        logger.info("VisualizationAgent initialized")
    
    async def execute(self, request: Any) -> Any:
        """
        Execute visualization generation.
        
        Args:
            request: AgentRequest or Dict containing methodology and requirements
            
        Returns:
            AgentResponse or Dict containing diagrams in Mermaid syntax
        """
        # Handle both AgentRequest and dict input
        if hasattr(request, 'input_data'):
            input_data = request.input_data
            task_id = request.task_id
        else:
            input_data = request
            task_id = "direct_call"
        
        topic = input_data.get("topic", "")
        
        # Get methodology details
        methodology = input_data.get("dependency_design_methodology", {})
        
        logger.info(f"Generating visualizations for: {topic}")
        
        # Generate process flow diagram
        process_flow = await self._generate_process_flow(methodology, topic)
        logger.info("Process flow diagram generated")
        
        # Generate data flow diagram
        data_flow = await self._generate_data_flow(methodology, topic)
        logger.info("Data flow diagram generated")
        
        # Generate system architecture (if applicable)
        architecture = await self._generate_architecture(methodology, topic)
        logger.info("Architecture diagram generated")
        
        # Generate timeline/Gantt chart
        timeline = await self._generate_timeline(methodology, topic)
        logger.info("Timeline diagram generated")
        
        # Prepare output
        result = {
            "diagrams": {
                "process_flow": process_flow,
                "data_flow": data_flow,
                "architecture": architecture,
                "timeline": timeline,
            },
            "metadata": {
                "total_diagrams": 4,
                "diagram_format": "mermaid",
            },
        }
        
        logger.info(f"Generated {result['metadata']['total_diagrams']} diagrams")
        
        # Return AgentResponse if called with AgentRequest
        if hasattr(request, 'input_data'):
            return AgentResponse(
                task_id=task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output_data=result,
            )
        return result
    
    async def _generate_process_flow(
        self,
        methodology: Dict[str, Any],
        topic: str,
    ) -> Dict[str, Any]:
        """Generate research process flow diagram."""
        
        procedures = methodology.get("procedures", {})
        design = methodology.get("design", {})
        
        prompt = f"""
Create a Mermaid.js flowchart showing the research process for: {topic}

Research Design: {design.get('strategy', 'Experimental')}

Procedures:
{self._format_procedures(procedures)}

Requirements:
1. Use flowchart syntax (graph TD)
2. Show clear process flow from start to end
3. Include decision points if applicable
4. Use appropriate shapes (rectangles, diamonds, etc.)
5. Keep it clear and professional

Output ONLY the Mermaid code starting with 'graph TD'
"""
        
        mermaid_code = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3,
        )
        
        # Clean and validate
        mermaid_code = self._clean_mermaid_code(mermaid_code)
        
        return {
            "type": "flowchart",
            "title": "Research Process Flow",
            "mermaid_code": mermaid_code,
            "description": "Step-by-step research process workflow",
        }
    
    async def _generate_data_flow(
        self,
        methodology: Dict[str, Any],
        topic: str,
    ) -> Dict[str, Any]:
        """Generate data flow diagram."""
        
        data_collection = methodology.get("procedures", {}).get("data_collection", {})
        analysis = methodology.get("procedures", {}).get("analysis", {})
        
        prompt = f"""
Create a Mermaid.js flowchart showing data flow for: {topic}

Data Collection:
- Sources: {', '.join(data_collection.get('primary_sources', ['Data sources']))}
- Instruments: {', '.join(data_collection.get('instruments', ['Instruments']))}

Analysis:
- Techniques: {', '.join(analysis.get('techniques', ['Analysis methods']))}
- Tools: {', '.join(analysis.get('tools', ['Analysis tools']))}

Requirements:
1. Show data movement from collection to analysis to results
2. Include data transformation steps
3. Use appropriate Mermaid syntax
4. Keep it clear and organized

Output ONLY the Mermaid code starting with 'graph LR' or 'graph TD'
"""
        
        mermaid_code = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=800,
            temperature=0.3,
        )
        
        mermaid_code = self._clean_mermaid_code(mermaid_code)
        
        return {
            "type": "flowchart",
            "title": "Data Flow Diagram",
            "mermaid_code": mermaid_code,
            "description": "Data collection, processing, and analysis workflow",
        }
    
    async def _generate_architecture(
        self,
        methodology: Dict[str, Any],
        topic: str,
    ) -> Dict[str, Any]:
        """Generate system/model architecture diagram."""
        
        experimental_setup = methodology.get("procedures", {}).get("experimental_setup", {})
        
        # Check if system architecture is applicable
        if not experimental_setup or "system" not in topic.lower():
            return {
                "type": "architecture",
                "title": "System Architecture",
                "mermaid_code": None,
                "description": "Not applicable for this research",
            }
        
        prompt = f"""
Create a Mermaid.js diagram showing system architecture for: {topic}

Variables:
{self._format_dict(experimental_setup.get('variables', {}))}

Components:
{', '.join(experimental_setup.get('resources', ['System components']))}

Requirements:
1. Use appropriate diagram type (graph, flowchart, or class diagram)
2. Show system components and relationships
3. Include data flow if applicable
4. Keep it professional and clear

Output ONLY the Mermaid code
"""
        
        mermaid_code = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3,
        )
        
        mermaid_code = self._clean_mermaid_code(mermaid_code)
        
        return {
            "type": "architecture",
            "title": "System Architecture",
            "mermaid_code": mermaid_code,
            "description": "High-level system architecture and components",
        }
    
    async def _generate_timeline(
        self,
        methodology: Dict[str, Any],
        topic: str,
    ) -> Dict[str, Any]:
        """Generate project timeline/Gantt chart."""
        
        prompt = f"""
Create a Mermaid.js Gantt chart for research project: {topic}

Research phases (typical for academic research):
1. Literature Review (2 months)
2. Methodology Development (1 month)
3. Data Collection (3 months)
4. Data Analysis (2 months)
5. Results Interpretation (1 month)
6. Writing & Revision (2 months)

Requirements:
1. Use Gantt chart syntax (gantt)
2. Show realistic timeline (total 9-12 months)
3. Include milestones
4. Show dependencies if applicable

Output ONLY the Mermaid code starting with 'gantt'
"""
        
        mermaid_code = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=800,
            temperature=0.3,
        )
        
        mermaid_code = self._clean_mermaid_code(mermaid_code)
        
        return {
            "type": "gantt",
            "title": "Research Timeline",
            "mermaid_code": mermaid_code,
            "description": "Project timeline and milestones",
        }
    
    def _format_procedures(self, procedures: Dict[str, Any]) -> str:
        """Format procedures for prompt."""
        if not procedures:
            return "Standard research procedures"
        
        formatted = []
        for key, value in procedures.items():
            if isinstance(value, dict):
                formatted.append(f"{key}: {self._format_dict(value)}")
            elif isinstance(value, list):
                formatted.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                formatted.append(f"{key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_dict(self, d: Dict[str, Any]) -> str:
        """Format dictionary for prompt."""
        if not d:
            return "N/A"
        
        items = []
        for key, value in d.items():
            if isinstance(value, list):
                items.append(f"{key}={', '.join(str(v) for v in value)}")
            else:
                items.append(f"{key}={value}")
        
        return ", ".join(items)
    
    def _clean_mermaid_code(self, code: str) -> str:
        """Clean and validate Mermaid code."""
        # Remove markdown code fences if present
        code = code.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            # Remove first and last lines (code fences)
            code = "\n".join(lines[1:-1]) if len(lines) > 2 else code
        
        # Remove "mermaid" language identifier
        if code.startswith("mermaid\n"):
            code = code[8:]
        
        return code.strip()
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        required_fields = ["topic"]
        
        for field in required_fields:
            if field not in input_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        return True

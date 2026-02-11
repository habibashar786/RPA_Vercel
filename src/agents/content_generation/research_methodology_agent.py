"""
Research Methodology Agent - Designs comprehensive research methodology.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class ResearchMethodologyAgent(BaseAgent):
    """
    Research Methodology Agent - Creates detailed methodology section.
    
    Responsibilities:
    - Design research approach
    - Define data collection methods
    - Specify analysis procedures
    - Detail experimental setup
    - Create process flows
    - Address ethical considerations
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize methodology agent.
        
        Args:
            llm_provider: LLM provider for text generation
            state_manager: State manager for persistence
        """
        super().__init__(
            agent_name="research_methodology_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        logger.info("ResearchMethodologyAgent initialized")
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute methodology generation.
        
        Args:
            request: Agent request containing topic, objectives, research questions
            
        Returns:
            AgentResponse with methodology content and metadata
        """
        try:
            input_data = request.input_data
            topic = input_data.get("topic", "")
            
            # Get introduction outputs
            intro_data = input_data.get("dependency_generate_introduction", {})
            objectives = intro_data.get("objectives", [])
            research_questions = intro_data.get("research_questions", [])
            
            logger.info(f"Generating methodology for: {topic}")
            
            # Design research approach
            research_design = await self._design_research_approach(
                topic, objectives, research_questions
            )
            logger.info("Research design complete")
            
            # Data collection methods
            data_collection = await self._design_data_collection(
                topic, objectives
            )
            logger.info("Data collection methods designed")
            
            # Analysis procedures
            analysis_methods = await self._design_analysis_methods(
                topic, research_questions
            )
            logger.info("Analysis methods designed")
            
            # Experimental setup
            experimental_setup = await self._design_experimental_setup(
                topic, objectives
            )
            logger.info("Experimental setup designed")
            
            # Ethical considerations
            ethical_considerations = await self._generate_ethical_considerations(
                topic
            )
            logger.info("Ethical considerations generated")
            
            # Synthesize complete methodology
            methodology_content = await self._synthesize_methodology(
                topic,
                research_design,
                data_collection,
                analysis_methods,
                experimental_setup,
                ethical_considerations,
            )
            logger.info("Methodology synthesis complete")
            
            # Prepare output
            output_data = {
                "content": methodology_content["main_content"],
                "subsections": methodology_content["subsections"],
                "design": research_design,
                "procedures": {
                    "data_collection": data_collection,
                    "analysis": analysis_methods,
                    "experimental_setup": experimental_setup,
                },
                "ethical_considerations": ethical_considerations,
                "metadata": {
                    "word_count": len(methodology_content["main_content"].split()),
                    "num_subsections": len(methodology_content["subsections"]),
                },
            }
            
            logger.info(
                f"Methodology complete: {output_data['metadata']['word_count']} words, "
                f"{output_data['metadata']['num_subsections']} subsections"
            )
            
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output_data=output_data,
            )
        
        except Exception as e:
            logger.error(f"ResearchMethodologyAgent failed: {e}")
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.FAILED,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )
    
    async def _design_research_approach(
        self,
        topic: str,
        objectives: List[str],
        research_questions: List[str],
    ) -> Dict[str, Any]:
        """Design overall research approach."""
        
        prompt = f"""
Design a comprehensive research approach for: {topic}

Research Objectives:
{chr(10).join(f"- {obj}" for obj in objectives)}

Research Questions:
{chr(10).join(f"- {q}" for q in research_questions)}

Specify:
1. Research paradigm (e.g., positivist, interpretivist, mixed methods)
2. Research strategy (e.g., experimental, survey, case study)
3. Time horizon (cross-sectional vs longitudinal)
4. Justification for approach

Format as JSON:
{{
  "paradigm": "...",
  "strategy": "...",
  "time_horizon": "...",
  "justification": "..."
}}
"""
        
        response = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
        )
        
        try:
            import json
            return json.loads(response)
        except:
            return {
                "paradigm": "Quantitative",
                "strategy": "Experimental design",
                "time_horizon": "Cross-sectional",
                "justification": "This approach aligns with the research objectives and questions",
            }
    
    async def _design_data_collection(
        self,
        topic: str,
        objectives: List[str],
    ) -> Dict[str, Any]:
        """Design data collection methods."""
        
        prompt = f"""
Design data collection methods for research on: {topic}

Objectives:
{chr(10).join(f"- {obj}" for obj in objectives)}

Specify:
1. Primary data sources
2. Secondary data sources
3. Sampling method and size
4. Data collection instruments
5. Data collection procedure (step-by-step)

Format as JSON:
{{
  "primary_sources": ["...", "..."],
  "secondary_sources": ["...", "..."],
  "sampling": {{"method": "...", "size": "..."}},
  "instruments": ["...", "..."],
  "procedure": ["Step 1...", "Step 2..."]
}}
"""
        
        response = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )
        
        try:
            import json
            return json.loads(response)
        except:
            return {
                "primary_sources": ["Experimental data", "Survey responses"],
                "secondary_sources": ["Published literature", "Public datasets"],
                "sampling": {"method": "Random sampling", "size": "N=100"},
                "instruments": ["Questionnaire", "Measurement tools"],
                "procedure": [
                    "Participant recruitment",
                    "Data collection",
                    "Quality assurance",
                ],
            }
    
    async def _design_analysis_methods(
        self,
        topic: str,
        research_questions: List[str],
    ) -> Dict[str, Any]:
        """Design analysis methods."""
        
        prompt = f"""
Design data analysis methods for: {topic}

Research Questions:
{chr(10).join(f"- {q}" for q in research_questions)}

Specify:
1. Statistical/analytical techniques
2. Software/tools to be used
3. Analysis workflow
4. Validation methods

Format as JSON:
{{
  "techniques": ["...", "..."],
  "tools": ["...", "..."],
  "workflow": ["Step 1...", "Step 2..."],
  "validation": ["...", "..."]
}}
"""
        
        response = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
        )
        
        try:
            import json
            return json.loads(response)
        except:
            return {
                "techniques": ["Descriptive statistics", "Regression analysis"],
                "tools": ["Python (pandas, scikit-learn)", "R (tidyverse)"],
                "workflow": [
                    "Data preprocessing",
                    "Exploratory analysis",
                    "Model development",
                    "Results interpretation",
                ],
                "validation": ["Cross-validation", "Statistical significance testing"],
            }
    
    async def _design_experimental_setup(
        self,
        topic: str,
        objectives: List[str],
    ) -> Dict[str, Any]:
        """Design experimental setup."""
        
        prompt = f"""
Design experimental setup for: {topic}

Objectives:
{chr(10).join(f"- {obj}" for obj in objectives)}

Specify:
1. Variables (independent, dependent, control)
2. Experimental conditions
3. Measurement procedures
4. Equipment/resources needed

Format as JSON:
{{
  "variables": {{
    "independent": ["...", "..."],
    "dependent": ["...", "..."],
    "control": ["...", "..."]
  }},
  "conditions": ["Condition 1...", "Condition 2..."],
  "measurements": ["...", "..."],
  "resources": ["...", "..."]
}}
"""
        
        response = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
        )
        
        try:
            import json
            return json.loads(response)
        except:
            return {
                "variables": {
                    "independent": ["Treatment variable"],
                    "dependent": ["Outcome measure"],
                    "control": ["Confounding variables"],
                },
                "conditions": ["Control condition", "Treatment condition"],
                "measurements": ["Primary outcome", "Secondary outcomes"],
                "resources": ["Laboratory equipment", "Computing resources"],
            }
    
    async def _generate_ethical_considerations(
        self,
        topic: str,
    ) -> List[str]:
        """Generate ethical considerations."""
        
        prompt = f"""
Identify key ethical considerations for research on: {topic}

Include:
1. Participant rights and welfare
2. Informed consent procedures
3. Data privacy and confidentiality
4. Risk mitigation strategies
5. Institutional review requirements

Format as JSON array of strings (4-6 considerations).
"""
        
        response = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=600,
            temperature=0.7,
        )
        
        try:
            import json
            considerations = json.loads(response)
            if isinstance(considerations, list):
                return considerations
        except:
            pass
        
        return [
            "Informed consent will be obtained from all participants",
            "Data will be anonymized to protect participant privacy",
            "Ethical approval will be sought from the institutional review board",
            "Participants can withdraw at any time without penalty",
        ]
    
    async def _synthesize_methodology(
        self,
        topic: str,
        research_design: Dict[str, Any],
        data_collection: Dict[str, Any],
        analysis_methods: Dict[str, Any],
        experimental_setup: Dict[str, Any],
        ethical_considerations: List[str],
    ) -> Dict[str, Any]:
        """Synthesize complete methodology section."""
        
        prompt = f"""
Write a comprehensive methodology section for research on: {topic}

Research Design:
- Paradigm: {research_design.get('paradigm', 'N/A')}
- Strategy: {research_design.get('strategy', 'N/A')}
- Time Horizon: {research_design.get('time_horizon', 'N/A')}

Data Collection:
- Sampling: {data_collection.get('sampling', {}).get('method', 'N/A')} (n={data_collection.get('sampling', {}).get('size', 'N/A')})
- Sources: {', '.join(data_collection.get('primary_sources', []))}

Analysis Methods:
- Techniques: {', '.join(analysis_methods.get('techniques', []))}
- Tools: {', '.join(analysis_methods.get('tools', []))}

Requirements:
1. Write in academic style (3rd person, future tense)
2. Organize into clear subsections
3. Provide detailed procedures
4. Justify methodological choices
5. Include ethical considerations
6. Target 2500-3000 words

Format as JSON:
{{
  "main_content": "Overview paragraph...",
  "subsections": [
    {{"title": "Research Design", "content": "..."}},
    {{"title": "Data Collection", "content": "..."}},
    {{"title": "Data Analysis", "content": "..."}},
    {{"title": "Experimental Setup", "content": "..."}},
    {{"title": "Ethical Considerations", "content": "..."}}
  ]
}}
"""
        
        response = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=6000,
            temperature=0.7,
        )
        
        try:
            import json
            return json.loads(response)
        except:
            # Fallback
            return {
                "main_content": f"This section outlines the methodology for investigating {topic}.",
                "subsections": [
                    {
                        "title": "Research Design",
                        "content": f"The research will employ a {research_design.get('paradigm', 'quantitative')} approach using {research_design.get('strategy', 'experimental')} design.",
                    },
                    {
                        "title": "Data Collection",
                        "content": f"Data will be collected using {', '.join(data_collection.get('instruments', ['standard instruments']))}.",
                    },
                    {
                        "title": "Data Analysis",
                        "content": f"Analysis will employ {', '.join(analysis_methods.get('techniques', ['appropriate statistical methods']))}.",
                    },
                    {
                        "title": "Ethical Considerations",
                        "content": "\n".join(ethical_considerations),
                    },
                ],
            }
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        required_fields = ["topic"]
        
        for field in required_fields:
            if field not in input_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        return True

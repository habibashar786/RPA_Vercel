"""
Introduction Agent - Generates problem statement, objectives, and research questions.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


def _get_gap_description(gap: Any) -> str:
    """Safely extract description from a research gap object or dict."""
    if isinstance(gap, dict):
        return gap.get('description', str(gap))
    return getattr(gap, 'description', str(gap))


def _get_gap_significance(gap: Any) -> str:
    """Safely extract significance from a research gap object or dict."""
    if isinstance(gap, dict):
        return gap.get('significance', 'high')
    return getattr(gap, 'significance', 'high')


class IntroductionAgent(BaseAgent):
    """
    Introduction Agent - Creates compelling introduction section.
    
    Responsibilities:
    - Generate problem statement
    - Define research objectives  
    - Formulate research questions
    - Establish significance and scope
    - Build narrative from literature gaps
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize introduction agent.
        
        Args:
            llm_provider: LLM provider for text generation
            state_manager: State manager for persistence
        """
        super().__init__(
            agent_name="introduction_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        logger.info("IntroductionAgent initialized")
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute introduction generation.
        
        Args:
            request: AgentRequest containing topic, key_points, literature analysis
            
        Returns:
            AgentResponse containing introduction content and metadata
        """
        try:
            input_data = request.input_data
            topic = input_data.get("topic", "")
            key_points = input_data.get("key_points", [])
            
            # Get literature review outputs
            lit_analysis = input_data.get("dependency_analyze_literature", {})
            research_gaps = lit_analysis.get("research_gaps", [])
            
            logger.info(f"Generating introduction for: {topic}")
            
            # Generate problem statement
            problem_statement = await self._generate_problem_statement(
                topic, key_points, research_gaps
            )
            logger.info("Problem statement generated")
            
            # Generate objectives
            objectives = await self._generate_objectives(
                topic, key_points, research_gaps
            )
            logger.info(f"Generated {len(objectives)} objectives")
            
            # Generate research questions
            research_questions = await self._generate_research_questions(
                topic, objectives, research_gaps
            )
            logger.info(f"Generated {len(research_questions)} research questions")
            
            # Generate full introduction
            introduction_content = await self._synthesize_introduction(
                topic,
                problem_statement,
                objectives,
                research_questions,
                research_gaps,
            )
            logger.info("Introduction synthesis complete")
            
            # Prepare output
            result = {
                "content": introduction_content["main_content"],
                "subsections": introduction_content["subsections"],
                "problem_statement": problem_statement,
                "objectives": objectives,
                "research_questions": research_questions,
                "metadata": {
                    "word_count": len(introduction_content["main_content"].split()),
                    "num_objectives": len(objectives),
                    "num_questions": len(research_questions),
                },
            }
            
            logger.info(
                f"Introduction complete: {result['metadata']['word_count']} words, "
                f"{len(objectives)} objectives, {len(research_questions)} questions"
            )
            
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output_data=result,
            )
        
        except Exception as e:
            logger.error(f"Introduction generation failed: {e}")
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.FAILED,
                error=str(e),
            )
    
    async def _generate_problem_statement(
        self,
        topic: str,
        key_points: List[str],
        research_gaps: List[Any],
    ) -> str:
        """Generate compelling problem statement."""
        
        gaps_summary = "\n".join([
            f"- {_get_gap_description(gap)}"
            for gap in research_gaps[:3]
        ])
        
        prompt = f"""
Write a compelling problem statement for a research proposal on: {topic}

Key Points:
{chr(10).join(f"- {point}" for point in key_points)}

Identified Research Gaps:
{gaps_summary}

Requirements:
1. Start with broad context (2-3 sentences)
2. Narrow to specific problem (2-3 sentences)
3. Highlight significance and urgency
4. Connect to research gaps
5. Use academic tone (3rd person)
6. Target 150-200 words

Format as a single cohesive paragraph.
"""
        
        problem_statement = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
        )
        
        return problem_statement.strip()
    
    async def _generate_objectives(
        self,
        topic: str,
        key_points: List[str],
        research_gaps: List[Any],
    ) -> List[str]:
        """Generate research objectives."""
        
        gaps_summary = "\n".join([
            f"- {_get_gap_description(gap)}"
            for gap in research_gaps
        ])
        
        prompt = f"""
Generate 4-6 specific, measurable research objectives for: {topic}

Key Points to Address:
{chr(10).join(f"- {point}" for point in key_points)}

Research Gaps to Fill:
{gaps_summary}

Requirements:
1. Start each objective with action verbs (e.g., "To investigate...", "To develop...", "To evaluate...")
2. Make them SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
3. Ensure they address identified gaps
4. Order from broad to specific
5. Each objective should be 1-2 sentences

Format as JSON array of strings.
"""
        
        response = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
        )
        
        try:
            import json
            objectives = json.loads(response)
            if isinstance(objectives, list):
                return objectives
        except:
            pass
        
        # Fallback objectives
        return [
            f"To investigate {key_points[0] if key_points else 'the primary research area'}",
            f"To develop methods addressing {_get_gap_description(research_gaps[0]) if research_gaps else 'identified gaps'}",
            "To evaluate the effectiveness of proposed approaches",
            "To validate findings through empirical analysis",
        ]
    
    async def _generate_research_questions(
        self,
        topic: str,
        objectives: List[str],
        research_gaps: List[Any],
    ) -> List[str]:
        """Generate research questions."""
        
        gaps_list = "\n".join([
            f"- {_get_gap_description(gap)}"
            for gap in research_gaps[:3]
        ])
        
        prompt = f"""
Generate 3-5 focused research questions for: {topic}

Research Objectives:
{chr(10).join(f"{i+1}. {obj}" for i, obj in enumerate(objectives))}

Research Gaps:
{gaps_list}

Requirements:
1. Each question should map to one or more objectives
2. Use question words (How, What, Why, To what extent)
3. Be specific and answerable through research
4. Build on each other logically
5. Avoid yes/no questions

Format as JSON array of strings.
"""
        
        response = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=600,
            temperature=0.7,
        )
        
        try:
            import json
            questions = json.loads(response)
            if isinstance(questions, list):
                return questions
        except:
            pass
        
        # Fallback questions
        return [
            f"What are the key factors influencing {topic}?",
            f"How can {objectives[0].lower() if objectives else 'the research objectives'} be achieved?",
            "What are the implications of the proposed approach?",
        ]
    
    async def _synthesize_introduction(
        self,
        topic: str,
        problem_statement: str,
        objectives: List[str],
        research_questions: List[str],
        research_gaps: List[Any],
    ) -> Dict[str, Any]:
        """Synthesize complete introduction section."""
        
        gaps_addressed = "\n".join([
            f"- {_get_gap_description(gap)}: Significance - {_get_gap_significance(gap)}"
            for gap in research_gaps[:3]
        ])
        
        prompt = f"""
Write a comprehensive introduction section for a research proposal on: {topic}

Problem Statement:
{problem_statement}

Research Objectives:
{chr(10).join(f"{i+1}. {obj}" for i, obj in enumerate(objectives))}

Research Questions:
{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(research_questions))}

Research Gaps Addressed:
{gaps_addressed}

Requirements:
1. Start with broad context and background (200 words)
2. Include problem statement naturally
3. Discuss significance and impact (150 words)
4. Present research objectives clearly
5. State research questions
6. Outline scope and limitations (100 words)
7. Preview methodology briefly (50 words)
8. Use academic style, 3rd person
9. Total target: 1500-2000 words

Format as JSON:
{{
  "main_content": "Opening paragraph...",
  "subsections": [
    {{"title": "Background and Context", "content": "..."}},
    {{"title": "Problem Statement", "content": "..."}},
    {{"title": "Research Objectives", "content": "..."}},
    {{"title": "Research Questions", "content": "..."}},
    {{"title": "Scope and Significance", "content": "..."}}
  ]
}}
"""
        
        response = await self.generate_with_retry(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.7,
        )
        
        try:
            import json
            introduction = json.loads(response)
            return introduction
        except:
            # Fallback structure
            return {
                "main_content": f"This research proposal addresses {topic}, focusing on several key areas of investigation.",
                "subsections": [
                    {
                        "title": "Background and Context",
                        "content": problem_statement,
                    },
                    {
                        "title": "Research Objectives",
                        "content": "\n".join(f"{i+1}. {obj}" for i, obj in enumerate(objectives)),
                    },
                    {
                        "title": "Research Questions",
                        "content": "\n".join(f"{i+1}. {q}" for i, q in enumerate(research_questions)),
                    },
                ],
            }
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        # Topic is required
        if "topic" not in input_data or not input_data.get("topic"):
            logger.error("Missing required field: topic")
            return False
        
        # key_points is optional but should be a list if provided
        key_points = input_data.get("key_points", [])
        if not isinstance(key_points, list):
            logger.error("key_points must be a list")
            return False
        
        return True

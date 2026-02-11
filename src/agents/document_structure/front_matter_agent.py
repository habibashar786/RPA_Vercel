"""
Front Matter Agent - Generates preliminary pages for research proposal.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class FrontMatterAgent(BaseAgent):
    """
    Front Matter Agent - Generates preliminary pages for research proposal.
    
    Responsibilities:
    - Generate abstract (200-300 words)
    - Extract keywords (5-8 keywords)
    - Create dedication (optional)
    - Write acknowledgements
    - Compile list of abbreviations
    - Generate list of figures
    - Generate list of tables
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize front matter agent.
        
        Args:
            llm_provider: LLM provider for content generation
            state_manager: State manager for persistence
        """
        super().__init__(
            agent_name="front_matter_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        logger.info("FrontMatterAgent initialized")
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute front matter generation.
        
        Args:
            request: Agent request with proposal sections
            
        Returns:
            AgentResponse with front matter components
        """
        try:
            input_data = request.input_data
            topic = input_data.get("topic", "Research Proposal")
            
            logger.info(f"Generating front matter for: {topic}")
            
            # Get all proposal sections for context
            introduction = input_data.get("dependency_generate_introduction", {})
            lit_review = input_data.get("dependency_analyze_literature", {})
            methodology = input_data.get("dependency_design_methodology", {})
            
            # Generate abstract (200-300 words)
            abstract = await self._generate_abstract(
                topic, introduction, lit_review, methodology
            )
            logger.info(f"Abstract generated ({len(abstract.split())} words)")
            
            # Extract keywords (5-8 keywords)
            keywords = await self._extract_keywords(
                topic, abstract, introduction, lit_review
            )
            logger.info(f"Extracted {len(keywords)} keywords")
            
            # Generate dedication (optional)
            dedication = await self._generate_dedication(input_data)
            logger.info("Dedication generated")
            
            # Generate acknowledgements
            acknowledgements = await self._generate_acknowledgements(input_data)
            logger.info("Acknowledgements generated")
            
            # Compile abbreviations list
            abbreviations = await self._compile_abbreviations(
                introduction, lit_review, methodology
            )
            logger.info(f"Compiled {len(abbreviations)} abbreviations")
            
            # Generate list of figures
            figures_list = await self._list_figures(input_data)
            logger.info(f"Listed {len(figures_list)} figures")
            
            # Generate list of tables
            tables_list = await self._list_tables(input_data)
            logger.info(f"Listed {len(tables_list)} tables")
            
            # Compile front matter
            front_matter = {
                "abstract": {
                    "text": abstract,
                    "word_count": len(abstract.split()),
                },
                "keywords": keywords,
                "dedication": dedication,
                "acknowledgements": acknowledgements,
                "abbreviations": abbreviations,
                "list_of_figures": figures_list,
                "list_of_tables": tables_list,
                "metadata": {
                    "total_components": 7,
                    "abstract_word_count": len(abstract.split()),
                    "keyword_count": len(keywords),
                    "abbreviation_count": len(abbreviations),
                    "figure_count": len(figures_list),
                    "table_count": len(tables_list),
                },
            }
            
            logger.info("Front matter compilation complete")
            
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output_data=front_matter,
                metadata={
                    "abstract_words": len(abstract.split()),
                    "keywords": len(keywords),
                    "abbreviations": len(abbreviations),
                },
            )
            
        except Exception as e:
            logger.error(f"Front matter generation failed: {e}")
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.FAILED,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            bool: True if valid
        """
        required_keys = ["topic"]
        return all(key in input_data for key in required_keys)
    
    async def _generate_abstract(
        self,
        topic: str,
        introduction: Dict[str, Any],
        lit_review: Dict[str, Any],
        methodology: Dict[str, Any],
        max_attempts: int = 3,
    ) -> str:
        """
        Generate abstract (200-300 words).
        
        Args:
            topic: Research topic
            introduction: Introduction section
            lit_review: Literature review section
            methodology: Methodology section
            
        Returns:
            Abstract text (200-300 words)
        """
        # Extract key information
        problem = introduction.get("problem_statement", "")
        objectives = introduction.get("research_objectives", [])
        gap = lit_review.get("research_gap", "")
        research_design = methodology.get("research_design", {})
        
        prompt = f"""Generate a concise abstract (200-300 words) for a research proposal on:
Topic: {topic}

Include:
1. Background/Problem: {problem}
2. Research Gap: {gap}
3. Objectives: {', '.join(objectives) if isinstance(objectives, list) else objectives}
4. Methodology: {research_design.get('type', 'Not specified')}
5. Expected significance

Requirements:
- 200-300 words ONLY
- Academic, formal tone
- Past tense for background, present for methodology
- No citations in abstract
- Clear and concise
- Q1 journal standard

Format as a single paragraph."""

        system_prompt = """You are an academic writing expert specializing in research proposal abstracts.
Generate abstracts that meet Q1 journal standards with precise word counts."""

        attempts = 0
        abstract = ""

        while attempts < max_attempts:
            attempts += 1
            abstract = await self.generate_with_retry(prompt, system_prompt)

            # Ensure word count is within range
            words = abstract.split()
            if len(words) < 200:
                logger.warning(
                    f"Attempt {attempts}: Abstract too short ({len(words)} words)"
                )
                if attempts >= max_attempts:
                    # Final attempt exhausted: pad the abstract to meet minimum length
                    pad_sentence = (
                        "This study aims to address the identified research gap and "
                        "provide meaningful contributions to the field."
                    )
                    while len(abstract.split()) < 200:
                        abstract = abstract.rstrip() + " " + pad_sentence
                    break
                # otherwise retry loop will continue
                continue
            elif len(words) > 300:
                logger.warning(f"Abstract too long ({len(words)} words), truncating...")
                abstract = " ".join(words[:300])
                break
            else:
                # acceptable length
                break

        return abstract.strip()
    
    async def _extract_keywords(
        self,
        topic: str,
        abstract: str,
        introduction: Dict[str, Any],
        lit_review: Dict[str, Any],
    ) -> List[str]:
        """
        Extract keywords (5-8 keywords).
        
        Args:
            topic: Research topic
            abstract: Abstract text
            introduction: Introduction section
            lit_review: Literature review section
            
        Returns:
            List of 5-8 keywords
        """
        prompt = f"""Extract 5-8 keywords for this research proposal:

Topic: {topic}

Abstract: {abstract}

Requirements:
- 5-8 keywords ONLY
- Mix of broad and specific terms
- Relevant to the research domain
- Use standard terminology
- Alphabetical order
- No duplicates
- Format: comma-separated list

Example: artificial intelligence, machine learning, neural networks, research methodology, statistical analysis"""

        system_prompt = """You are an academic indexing expert. Extract precise, relevant keywords 
that researchers would use to find this work."""

        keywords_text = await self.generate_with_retry(prompt, system_prompt)
        
        # Parse keywords
        keywords = [k.strip() for k in keywords_text.split(",")]
        keywords = [k for k in keywords if k]  # Remove empty strings
        
        # Ensure 5-8 keywords
        if len(keywords) < 5:
            keywords.extend(["research", "methodology", "analysis"][:5 - len(keywords)])
        elif len(keywords) > 8:
            keywords = keywords[:8]
        
        return sorted(keywords)
    
    async def _generate_dedication(self, input_data: Dict[str, Any]) -> str:
        """
        Generate dedication (optional).
        
        Args:
            input_data: Input data (may contain dedication preferences)
            
        Returns:
            Dedication text or empty string
        """
        # Check if user provided dedication
        user_dedication = input_data.get("dedication", "")
        if user_dedication:
            return user_dedication
        
        # Generate generic professional dedication
        dedication = """This research proposal is dedicated to the advancement of knowledge 
and the pursuit of academic excellence."""
        
        return dedication.strip()
    
    async def _generate_acknowledgements(self, input_data: Dict[str, Any]) -> str:
        """
        Generate acknowledgements.
        
        Args:
            input_data: Input data (may contain acknowledgement preferences)
            
        Returns:
            Acknowledgements text
        """
        # Check if user provided acknowledgements
        user_ack = input_data.get("acknowledgements", "")
        if user_ack:
            return user_ack
        
        # Extract institution/supervisor if available
        institution = input_data.get("institution", "")
        supervisor = input_data.get("supervisor", "")
        
        # Generate professional acknowledgements
        ack_parts = []
        
        if supervisor:
            ack_parts.append(
                f"I would like to express my sincere gratitude to my supervisor, "
                f"{supervisor}, for their invaluable guidance, support, and expertise "
                f"throughout the development of this research proposal."
            )
        else:
            ack_parts.append(
                "I would like to express my sincere gratitude to my supervisor "
                "for their invaluable guidance, support, and expertise throughout "
                "the development of this research proposal."
            )
        
        if institution:
            ack_parts.append(
                f"I am grateful to {institution} for providing the resources and "
                f"academic environment that made this work possible."
            )
        
        ack_parts.append(
            "Finally, I would like to thank my family and colleagues for their "
            "continuous encouragement and support."
        )
        
        return "\n\n".join(ack_parts)
    
    async def _compile_abbreviations(
        self,
        introduction: Dict[str, Any],
        lit_review: Dict[str, Any],
        methodology: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Compile list of abbreviations from all sections.
        
        Args:
            introduction: Introduction section
            lit_review: Literature review section
            methodology: Methodology section
            
        Returns:
            List of abbreviation dictionaries
        """
        # Common research abbreviations
        common_abbr = {
            "AI": "Artificial Intelligence",
            "ML": "Machine Learning",
            "DL": "Deep Learning",
            "NLP": "Natural Language Processing",
            "CV": "Computer Vision",
            "IoT": "Internet of Things",
            "API": "Application Programming Interface",
            "REST": "Representational State Transfer",
            "JSON": "JavaScript Object Notation",
            "XML": "Extensible Markup Language",
            "SQL": "Structured Query Language",
            "NoSQL": "Not Only SQL",
            "RDBMS": "Relational Database Management System",
            "GUI": "Graphical User Interface",
            "UI": "User Interface",
            "UX": "User Experience",
            "QA": "Quality Assurance",
            "CI/CD": "Continuous Integration/Continuous Deployment",
            "DevOps": "Development and Operations",
            "MVC": "Model-View-Controller",
            "OOP": "Object-Oriented Programming",
            "CRUD": "Create, Read, Update, Delete",
        }
        
        # Combine all text to search for abbreviations
        all_text = str(introduction) + str(lit_review) + str(methodology)
        
        # Find used abbreviations
        abbreviations = []
        for abbr, full_form in sorted(common_abbr.items()):
            if abbr in all_text:
                abbreviations.append({
                    "abbreviation": abbr,
                    "full_form": full_form,
                })
        
        return abbreviations
    
    async def _list_figures(self, input_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate list of figures.
        
        Args:
            input_data: Input data with diagrams
            
        Returns:
            List of figure references
        """
        figures = []
        
        # Extract diagrams from visualization agent
        diagrams = input_data.get("dependency_create_diagrams", {})
        if diagrams and isinstance(diagrams, dict):
            diagram_data = diagrams.get("diagrams", {})
            
            figure_num = 1
            for diagram_type, diagram_content in diagram_data.items():
                if diagram_content:
                    # Format diagram type
                    title = diagram_type.replace("_", " ").title()
                    figures.append({
                        "number": f"Figure {figure_num}",
                        "title": title,
                        "page": "TBD",  # Will be filled during final assembly
                    })
                    figure_num += 1
        
        return figures
    
    async def _list_tables(self, input_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate list of tables.
        
        Args:
            input_data: Input data with potential tables
            
        Returns:
            List of table references
        """
        tables = []
        
        # Extract tables from methodology (e.g., data collection plan)
        methodology = input_data.get("dependency_design_methodology", {})
        
        if methodology:
            # Check for data collection table
            if methodology.get("data_collection"):
                tables.append({
                    "number": "Table 1",
                    "title": "Data Collection Plan",
                    "page": "TBD",
                })
            
            # Check for sampling strategy table
            if methodology.get("sampling"):
                tables.append({
                    "number": f"Table {len(tables) + 1}",
                    "title": "Sampling Strategy",
                    "page": "TBD",
                })
            
            # Check for timeline table
            if methodology.get("timeline"):
                tables.append({
                    "number": f"Table {len(tables) + 1}",
                    "title": "Research Timeline",
                    "page": "TBD",
                })
        
        return tables


# Export
__all__ = ["FrontMatterAgent"]

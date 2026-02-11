"""
Reference and Citation Agent - Manages citations and bibliography.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentResponse, TaskStatus


class ReferenceCitationAgent(BaseAgent):
    """
    Reference and Citation Agent - Harvard style citation management.
    
    Responsibilities:
    - Format citations in Harvard style
    - Compile reference list
    - Validate citation accuracy
    - Ensure proper sequencing
    - Check for missing/incomplete citations
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
        citation_style: str = "harvard",
    ):
        """Initialize reference citation agent."""
        super().__init__(
            agent_name="reference_citation_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        self.citation_style = citation_style
        logger.info(f"ReferenceCitationAgent initialized: style={citation_style}")
    
    async def execute(self, input_data: Any) -> AgentResponse:
        """Execute citation management and return an AgentResponse."""

        # Handle both dict and AgentRequest input
        if hasattr(input_data, "input_data"):
            # It's an AgentRequest, extract the dict
            data = input_data.input_data or {}
        elif isinstance(input_data, dict):
            # It's already a dict
            data = input_data
        else:
            # Unknown wrapper, try to coerce to dict
            try:
                data = dict(input_data)
            except Exception:
                data = {}

        # Extract citations from literature review (support multiple key variants)
        lit_review = data.get("dependency_analyze_literature") or data.get("analyze_literature") or data
        papers = []
        citations = []
        if isinstance(lit_review, dict):
            papers = lit_review.get("papers", []) or []
            citations = lit_review.get("citations", []) or []

        logger.info(f"Processing {len(papers)} papers for citations")

        # Format references in Harvard style
        formatted_refs = await self._format_references(papers, citations)

        # Generate in-text citation guide
        citation_guide = self._generate_citation_guide(formatted_refs)

        # Sort alphabetically
        sorted_refs = sorted(formatted_refs, key=lambda x: x.get("formatted", ""))

        result = {
            "references": sorted_refs,
            "citation_guide": citation_guide,
            "total_references": len(sorted_refs),
            "citation_style": self.citation_style,
        }

        logger.info(f"Generated {len(sorted_refs)} references in {self.citation_style} style")

        return AgentResponse(
            task_id=getattr(input_data, "task_id", "unknown_task"),
            agent_name=self.agent_name,
            status=TaskStatus.COMPLETED,
            output_data=result,
            metadata={"generated_refs": len(sorted_refs)},
        )
    
    async def _format_references(
        self,
        papers: List[Dict],
        citations: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Format references in Harvard style."""
        formatted = []
        
        for paper in papers:
            authors = paper.get("authors", [])
            year = paper.get("year", "n.d.")
            title = paper.get("title", "")
            venue = paper.get("venue", "")
            doi = paper.get("doi", "")
            url = paper.get("url", "")
            
            # Format authors (Harvard style)
            if not authors:
                author_str = "Anonymous"
            elif len(authors) == 1:
                author_str = authors[0]
            elif len(authors) == 2:
                author_str = f"{authors[0]} and {authors[1]}"
            else:
                author_str = f"{authors[0]} et al."
            
            # Build Harvard citation
            harvard_ref = f"{author_str} ({year}) '{title}', {venue}"
            if doi:
                harvard_ref += f", doi:{doi}"
            elif url:
                harvard_ref += f". Available at: {url}"
            harvard_ref += "."
            
            formatted.append({
                "authors": authors,
                "year": year,
                "title": title,
                "formatted": harvard_ref,
                "in_text": f"{author_str.split(' ')[-1]}, {year}",
            })
        
        return formatted
    
    def _generate_citation_guide(self, formatted_refs: List[Dict]) -> str:
        """Generate citation usage guide."""
        return "\n".join([
            f"In-text: ({ref['in_text']}) → Reference: {ref['formatted']}"
            for ref in formatted_refs[:10]  # First 10 as examples
        ])
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        return True  # Can work with empty input

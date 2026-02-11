"""
Literature Review Agent - Analyzes academic papers and identifies research gaps.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.mcp_servers.arxiv_mcp import ArxivMCP
from src.mcp_servers.frontiers_mcp import FrontiersMCP
from src.mcp_servers.semantic_scholar_mcp import SemanticScholarMCP
from src.mcp_servers.papers_with_code_mcp import PapersWithCodeMCP
from src.models.proposal_schema import LiteraturePaper, ResearchGap
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class LiteratureReviewAgent(BaseAgent):
    """
    Literature Review Agent - Conducts comprehensive literature review.
    
    Responsibilities:
    - Query multiple MCP servers for papers
    - Filter and rank papers by relevance
    - Analyze paper content
    - Synthesize findings
    - Identify research gaps
    - Paraphrase content for Turnitin compliance
    - Extract citations
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
        min_papers: int = 30,
        max_papers: int = 50,
    ):
        """
        Initialize literature review agent.
        
        Args:
            llm_provider: LLM provider for analysis
            state_manager: State manager for caching
            min_papers: Minimum number of papers to review
            max_papers: Maximum number of papers to process
        """
        super().__init__(
            agent_name="literature_review_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        self.min_papers = min_papers
        self.max_papers = max_papers
        
        # Initialize MCP servers
        self.semantic_scholar = SemanticScholarMCP(state_manager=state_manager)
        self.arxiv = ArxivMCP(state_manager=state_manager)
        self.frontiers = FrontiersMCP(state_manager=state_manager)
        self.papers_with_code = PapersWithCodeMCP(state_manager=state_manager)
        
        logger.info(
            f"LiteratureReviewAgent initialized: "
            f"min_papers={min_papers}, max_papers={max_papers}, "
            f"sources=[semantic_scholar, arxiv, frontiers, papers_with_code]"
        )
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute literature review.
        
        Args:
            request: Agent request with input data
            
        Returns:
            AgentResponse containing literature review content, papers, and gaps
        """
        try:
            input_data = request.input_data
            topic = input_data.get("topic", "")
            key_points = input_data.get("key_points", [])
            preferences = input_data.get("user_preferences", {})
            
            logger.info(f"Starting literature review for topic: {topic}")
            
            # Step 1: Search for papers
            papers = await self._search_papers(topic, key_points, preferences)
            logger.info(f"Retrieved {len(papers)} papers from MCP servers")
            
            if len(papers) < self.min_papers:
                logger.warning(
                    f"Found only {len(papers)} papers, below minimum of {self.min_papers}"
                )
            
            # Step 2: Rank and filter papers
            ranked_papers = await self._rank_papers(papers, topic, key_points)
            selected_papers = ranked_papers[:self.max_papers]
            logger.info(f"Selected top {len(selected_papers)} papers for analysis")
            
            # Step 3: Analyze papers
            analysis = await self._analyze_papers(selected_papers, topic, key_points)
            logger.info("Paper analysis complete")
            
            # Step 4: Identify research gaps
            research_gaps = await self._identify_research_gaps(
                analysis, topic, key_points
            )
            logger.info(f"Identified {len(research_gaps)} research gaps")
            
            # Step 5: Synthesize literature review content
            review_content = await self._synthesize_review(
                selected_papers, analysis, research_gaps, topic
            )
            logger.info("Literature review synthesis complete")
            
            # Step 6: Extract citations
            citations = self._extract_citations(selected_papers)
            
            # Prepare output
            result = {
                "content": review_content["main_content"],
                "subsections": review_content["subsections"],
                "papers_reviewed": len(selected_papers),
                "research_gaps": [gap.model_dump() for gap in research_gaps],
                "papers": [self._paper_to_dict(paper) for paper in selected_papers],
                "citations": citations,
                "metadata": {
                    "total_papers_found": len(papers),
                    "papers_analyzed": len(selected_papers),
                    "word_count": len(review_content["main_content"].split()),
                    "sources": ["semantic_scholar", "arxiv", "frontiers", "papers_with_code"],
                },
            }
            
            logger.info(
                f"Literature review complete: {result['metadata']['word_count']} words, "
                f"{len(selected_papers)} papers, {len(research_gaps)} gaps"
            )
            
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output_data=result,
            )
        
        except Exception as e:
            logger.error(f"Literature review failed: {e}")
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.FAILED,
                error=str(e),
            )
        
        finally:
            # Cleanup MCP server sessions to prevent resource leaks
            await self._cleanup_mcp_sessions()
    
    async def _cleanup_mcp_sessions(self) -> None:
        """Clean up MCP server HTTP sessions."""
        try:
            await self.semantic_scholar.disconnect()
            await self.arxiv.disconnect()
            await self.frontiers.disconnect()
            await self.papers_with_code.disconnect()
        except Exception as e:
            logger.warning(f"Error cleaning up MCP sessions: {e}")
    
    async def _search_papers(
        self,
        topic: str,
        key_points: List[str],
        preferences: Dict[str, Any],
    ) -> List[LiteraturePaper]:
        """
        Search for papers across multiple MCP servers.
        
        Args:
            topic: Research topic
            key_points: Key points to focus on
            preferences: User preferences (year range, etc.)
            
        Returns:
            List[LiteraturePaper]: Retrieved papers
        """
        # Construct search queries
        queries = self._construct_search_queries(topic, key_points)
        
        # Prepare filters
        current_year = datetime.now().year
        filters = {
            "year_from": preferences.get("year_from", current_year - 6),  # Last 6 years
            "year_to": preferences.get("year_to", current_year),
            "min_citations": preferences.get("min_citations", 5),
        }
        
        # Search in parallel across all MCP servers
        search_tasks = []
        
        # Semantic Scholar
        for query in queries:
            search_tasks.append(
                self.semantic_scholar.search_papers(
                    query=query,
                    limit=20,
                    filters=filters,
                    use_cache=True,
                )
            )
        
        # arXiv
        for query in queries:
            search_tasks.append(
                self.arxiv.search_papers(
                    query=query,
                    limit=15,
                    filters=filters,
                    use_cache=True,
                )
            )
        
        # Frontiers
        for query in queries:
            search_tasks.append(
                self.frontiers.search_papers(
                    query=query,
                    limit=10,
                    filters=filters,
                    use_cache=True,
                )
            )
        
        # Papers With Code (for papers with implementations)
        for query in queries:
            search_tasks.append(
                self.papers_with_code.search_papers(
                    query=query,
                    limit=15,
                    filters=filters,
                    use_cache=True,
                )
            )
        
        logger.info(f"Executing {len(search_tasks)} parallel search queries across 4 sources")
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Collect and deduplicate papers
        all_papers = []
        seen_titles = set()
        seen_dois = set()
        
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Search error: {result}")
                continue
            
            if not result.success:
                logger.warning(f"Search failed: {result.error}")
                continue
            
            for paper_data in result.data:
                # Convert to LiteraturePaper
                paper = self._dict_to_paper(paper_data)
                
                # Deduplicate by title and DOI
                title_lower = paper.title.lower().strip()
                if title_lower in seen_titles:
                    continue
                
                if paper.doi and paper.doi in seen_dois:
                    continue
                
                seen_titles.add(title_lower)
                if paper.doi:
                    seen_dois.add(paper.doi)
                
                all_papers.append(paper)
        
        logger.info(f"Found {len(all_papers)} unique papers after deduplication")
        return all_papers
    
    def _construct_search_queries(
        self,
        topic: str,
        key_points: List[str],
    ) -> List[str]:
        """
        Construct search queries from topic and key points.
        
        Args:
            topic: Main research topic
            key_points: Key points to include
            
        Returns:
            List[str]: Search queries
        """
        queries = [topic]
        
        # Add queries combining topic with key points
        for point in key_points[:3]:  # Use top 3 key points
            queries.append(f"{topic} {point}")
        
        return queries
    
    async def _rank_papers(
        self,
        papers: List[LiteraturePaper],
        topic: str,
        key_points: List[str],
    ) -> List[LiteraturePaper]:
        """
        Rank papers by relevance to topic and key points.
        
        Args:
            papers: List of papers to rank
            topic: Research topic
            key_points: Key points
            
        Returns:
            List[LiteraturePaper]: Sorted papers (most relevant first)
        """
        logger.info(f"Ranking {len(papers)} papers for relevance")
        
        # Calculate relevance scores
        scored_papers = []
        
        topic_keywords = set(topic.lower().split())
        key_point_keywords = set()
        for point in key_points:
            key_point_keywords.update(point.lower().split())
        
        for paper in papers:
            score = 0.0
            
            # Title relevance (30%)
            title_words = set(paper.title.lower().split())
            title_overlap = len(title_words & topic_keywords)
            score += title_overlap * 0.3
            
            # Abstract relevance (40%)
            if paper.abstract:
                abstract_words = set(paper.abstract.lower().split())
                abstract_overlap = len(abstract_words & topic_keywords)
                abstract_key_overlap = len(abstract_words & key_point_keywords)
                score += (abstract_overlap * 0.3) + (abstract_key_overlap * 0.1)
            
            # Citation count (20%)
            citation_score = min(paper.citation_count / 100, 1.0)  # Normalize to 0-1
            score += citation_score * 0.2
            
            # Recency (10%)
            current_year = datetime.now().year
            if paper.year:
                age = current_year - paper.year
                recency_score = max(0, 1 - (age / 10))  # Papers older than 10 years get 0
                score += recency_score * 0.1
            
            scored_papers.append((score, paper))
        
        # Sort by score (descending)
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        
        ranked_papers = [paper for score, paper in scored_papers]
        
        logger.info(
            f"Top paper scores: "
            f"{[f'{score:.2f}' for score, _ in scored_papers[:5]]}"
        )
        
        return ranked_papers
    
    async def _analyze_papers(
        self,
        papers: List[LiteraturePaper],
        topic: str,
        key_points: List[str],
    ) -> Dict[str, Any]:
        """
        Analyze papers to extract key findings and themes.
        
        Args:
            papers: Papers to analyze
            topic: Research topic
            key_points: Key points of interest
            
        Returns:
            Dict containing analysis results
        """
        logger.info(f"Analyzing {len(papers)} papers")
        
        # Prepare paper summaries for LLM
        paper_summaries = []
        for i, paper in enumerate(papers[:20], 1):  # Analyze top 20 in detail
            summary = f"""
Paper {i}:
Title: {paper.title}
Authors: {', '.join(paper.authors[:3])}
Year: {paper.year}
Citations: {paper.citation_count}
Abstract: {paper.abstract[:500] if paper.abstract else 'N/A'}
"""
            paper_summaries.append(summary)
        
        # Use LLM to analyze papers
        analysis_prompt = f"""
You are analyzing academic papers for a research proposal on: {topic}

Key points of interest:
{chr(10).join(f"- {point}" for point in key_points)}

Papers to analyze:
{chr(10).join(paper_summaries)}

Provide a comprehensive analysis including:
1. Main themes and trends across papers
2. Key methodologies used
3. Common findings and conclusions
4. Identified limitations in existing research
5. Areas where research is lacking or contradictory

Format your response as JSON with these keys: themes, methodologies, findings, limitations, gaps
"""
        
        analysis_response = await self.generate_with_retry(
            prompt=analysis_prompt,
            max_tokens=4000,
        )
        
        # Parse LLM response
        try:
            import json
            analysis = json.loads(analysis_response)
        except:
            # Fallback to basic structure if parsing fails
            analysis = {
                "themes": ["Unable to parse detailed themes"],
                "methodologies": ["Various methodologies identified"],
                "findings": ["Multiple findings across papers"],
                "limitations": ["Some limitations noted"],
                "gaps": ["Research gaps identified"],
            }
        
        return analysis
    
    async def _identify_research_gaps(
        self,
        analysis: Dict[str, Any],
        topic: str,
        key_points: List[str],
    ) -> List[ResearchGap]:
        """
        Identify research gaps from paper analysis.
        
        Args:
            analysis: Analysis results
            topic: Research topic
            key_points: Key points
            
        Returns:
            List[ResearchGap]: Identified research gaps
        """
        logger.info("Identifying research gaps")
        
        gap_prompt = f"""
Based on this literature analysis for the topic "{topic}":

Identified Gaps and Limitations:
{chr(10).join(f"- {gap}" for gap in analysis.get('gaps', []))}
{chr(10).join(f"- {lim}" for lim in analysis.get('limitations', []))}

Key Research Points:
{chr(10).join(f"- {point}" for point in key_points)}

Identify 3-5 specific, actionable research gaps that:
1. Are clearly not addressed by existing literature
2. Are significant to the field
3. Are feasible to research
4. Align with the key points

For each gap, provide:
- Title (brief description)
- Description (detailed explanation)
- Significance (why it matters)
- Current state (what exists now)

Format as JSON array with objects containing: title, description, significance, current_state
"""
        
        gaps_response = await self.generate_with_retry(
            prompt=gap_prompt,
            max_tokens=2000,
        )
        
        # Parse gaps
        import uuid
        try:
            import json
            gaps_data = json.loads(gaps_response)
            
            research_gaps = []
            for gap_dict in gaps_data:
                gap = ResearchGap(
                    gap_id=str(uuid.uuid4()),
                    description=gap_dict.get("description", ""),
                    significance=gap_dict.get("significance", ""),
                )
                research_gaps.append(gap)
        
        except:
            # Fallback gaps
            research_gaps = [
                ResearchGap(
                    gap_id=str(uuid.uuid4()),
                    description="Limited studies using advanced methodologies",
                    significance="high",
                ),
                ResearchGap(
                    gap_id=str(uuid.uuid4()),
                    description="Lack of research in specific contexts",
                    significance="high",
                ),
            ]
        
        return research_gaps
    
    async def _synthesize_review(
        self,
        papers: List[LiteraturePaper],
        analysis: Dict[str, Any],
        gaps: List[ResearchGap],
        topic: str,
    ) -> Dict[str, Any]:
        """
        Synthesize literature review content.
        
        Args:
            papers: Reviewed papers
            analysis: Analysis results
            gaps: Research gaps
            topic: Research topic
            
        Returns:
            Dict with main_content and subsections
        """
        logger.info("Synthesizing literature review content")
        
        synthesis_prompt = f"""
Write a comprehensive literature review section for a research proposal on: {topic}

Based on analysis of {len(papers)} academic papers, synthesize the following into a cohesive narrative:

THEMES:
{chr(10).join(f"- {theme}" for theme in analysis.get('themes', []))}

METHODOLOGIES:
{chr(10).join(f"- {method}" for method in analysis.get('methodologies', []))}

KEY FINDINGS:
{chr(10).join(f"- {finding}" for finding in analysis.get('findings', []))}

RESEARCH GAPS:
{chr(10).join(f"- {gap.description}" for gap in gaps)}

Requirements:
1. Write in academic style (3rd person, formal tone)
2. Organize into clear themes/subsections
3. Include in-text citations (Author, Year)
4. Paraphrase all content (no direct quotes)
5. Synthesize findings, don't just list papers
6. Build narrative leading to research gaps
7. Target 2000-2500 words

Format as JSON:
{{
  "main_content": "Introduction paragraph...",
  "subsections": [
    {{"title": "Theme 1", "content": "..."}},
    {{"title": "Theme 2", "content": "..."}}
  ]
}}
"""
        
        review_response = await self.generate_with_retry(
            prompt=synthesis_prompt,
            max_tokens=6000,
            temperature=0.7,
        )
        
        # Parse response
        try:
            import json
            review_content = json.loads(review_response)
        except:
            # Fallback structure
            review_content = {
                "main_content": f"This literature review examines recent research on {topic}, analyzing {len(papers)} papers to identify key themes, methodologies, and research gaps.",
                "subsections": [
                    {
                        "title": "Overview of Current Research",
                        "content": f"Analysis of {len(papers)} papers reveals several key themes in the literature.",
                    },
                    {
                        "title": "Research Gaps",
                        "content": f"Despite extensive research, {len(gaps)} significant gaps remain in the literature.",
                    },
                ],
            }
        
        return review_content
    
    def _dict_to_paper(self, paper_data: Dict[str, Any]) -> LiteraturePaper:
        """Convert dictionary to LiteraturePaper model."""
        return LiteraturePaper(
            paper_id=paper_data.get("paper_id", ""),
            title=paper_data.get("title", ""),
            authors=paper_data.get("authors", []),
            year=paper_data.get("year"),
            abstract=paper_data.get("abstract") or "",
            venue=paper_data.get("venue", ""),
            citation_count=paper_data.get("citation_count", 0),
            doi=paper_data.get("doi"),
            url=paper_data.get("url", ""),
            source=paper_data.get("source", ""),
        )
    
    def _paper_to_dict(self, paper: LiteraturePaper) -> Dict[str, Any]:
        """Convert LiteraturePaper to dictionary."""
        return paper.model_dump()
    
    def _extract_citations(self, papers: List[LiteraturePaper]) -> List[Dict[str, Any]]:
        """
        Extract citations from papers.
        
        Args:
            papers: List of papers
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        for paper in papers:
            citation = {
                "authors": paper.authors,
                "year": paper.year,
                "title": paper.title,
                "venue": paper.venue,
                "doi": paper.doi,
                "url": paper.url,
            }
            citations.append(citation)
        
        return citations
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            bool: True if valid
        """
        # Topic is required
        if "topic" not in input_data or not input_data.get("topic"):
            logger.error("Missing required field: topic")
            return False
        
        # key_points is optional but should be a list if provided
        key_points = input_data.get("key_points", [])
        if not isinstance(key_points, list):
            logger.error("key_points must be a list")
            return False
        
        # Warn but don't fail if less than 3 key_points
        if len(key_points) < 3:
            logger.warning(f"Only {len(key_points)} key points provided, ideally need at least 3")
        
        return True

"""
Semantic Scholar MCP server implementation.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.mcp_servers.base_mcp import BaseMCPServer, MCPError, MCPResponse


class SemanticScholarMCP(BaseMCPServer):
    """Semantic Scholar academic database MCP server."""

    def __init__(self, state_manager=None):
        """Initialize Semantic Scholar MCP server."""
        super().__init__("semantic_scholar", state_manager)
        self.base_url = self.config.get("base_url", "https://api.semanticscholar.org/graph/v1")
        self.fields = self.config.get("parameters", {}).get("fields", [])

    async def search_papers(
        self,
        query: str,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Search for papers on Semantic Scholar.

        Args:
            query: Search query
            limit: Maximum number of results (default 100, max 1000)
            filters: Filters like year_from, year_to, min_citations
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Search results with paper data
        """
        try:
            # Check cache
            cache_key = self._generate_cache_key(query, filters)
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            # Prepare search parameters
            params = {
                "query": query,
                "limit": min(limit, self.config.get("parameters", {}).get("max_limit", 1000)),
                "fields": ",".join(self.fields) if self.fields else None,
            }

            # Apply filters
            if filters:
                if "year_from" in filters:
                    params["year"] = f"{filters['year_from']}-"
                if "year_to" in filters:
                    year_param = params.get("year", "")
                    params["year"] = f"{year_param}{filters['year_to']}"
                if "min_citations" in filters:
                    params["minCitationCount"] = filters["min_citations"]
                if "publication_types" in filters:
                    params["publicationTypes"] = ",".join(filters["publication_types"])

            # Make request
            endpoint = self.config.get("endpoints", {}).get("search", "/paper/search")
            url = f"{self.base_url}{endpoint}"

            logger.info(f"Searching Semantic Scholar: query='{query}', limit={limit}")
            response_data = await self._make_request("GET", url, params=params)

            # Process results
            papers = response_data.get("data", [])
            normalized_papers = [self._normalize_paper(paper) for paper in papers]

            # Create response
            mcp_response = MCPResponse(
                success=True,
                data=normalized_papers,
                metadata={
                    "total": response_data.get("total", len(papers)),
                    "offset": response_data.get("offset", 0),
                    "next": response_data.get("next"),
                    "query": query,
                    "filters": filters or {},
                },
                source=self.server_name,
            )

            # Cache response
            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            logger.info(f"Found {len(normalized_papers)} papers on Semantic Scholar")
            return mcp_response

        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def get_paper_details(
        self,
        paper_id: str,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get detailed information about a specific paper.

        Args:
            paper_id: Semantic Scholar paper ID
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Paper details
        """
        try:
            # Check cache
            cache_key = f"paper_{paper_id}"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            # Prepare request
            params = {"fields": ",".join(self.fields)} if self.fields else None
            endpoint = self.config.get("endpoints", {}).get("paper_details", "/paper/{paper_id}")
            url = f"{self.base_url}{endpoint}".replace("{paper_id}", paper_id)

            logger.debug(f"Fetching paper details: {paper_id}")
            response_data = await self._make_request("GET", url, params=params)

            # Normalize paper
            normalized_paper = self._normalize_paper(response_data)

            # Create response
            mcp_response = MCPResponse(
                success=True,
                data=[normalized_paper],
                metadata={"paper_id": paper_id},
                source=self.server_name,
            )

            # Cache response
            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            return mcp_response

        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Error fetching paper {paper_id}: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def get_paper_citations(
        self,
        paper_id: str,
        limit: int = 100,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get citations for a paper.

        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of citations
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Citation data
        """
        try:
            cache_key = f"citations_{paper_id}_{limit}"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            params = {
                "limit": limit,
                "fields": ",".join(self.fields) if self.fields else None,
            }

            endpoint = self.config.get("endpoints", {}).get("citations", "/paper/{paper_id}/citations")
            url = f"{self.base_url}{endpoint}".replace("{paper_id}", paper_id)

            logger.debug(f"Fetching citations for paper: {paper_id}")
            response_data = await self._make_request("GET", url, params=params)

            citations = response_data.get("data", [])
            normalized_citations = [
                self._normalize_paper(cite.get("citingPaper", {})) for cite in citations
            ]

            mcp_response = MCPResponse(
                success=True,
                data=normalized_citations,
                metadata={
                    "paper_id": paper_id,
                    "citation_count": len(citations),
                },
                source=self.server_name,
            )

            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            return mcp_response

        except Exception as e:
            logger.error(f"Error fetching citations: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def get_paper_references(
        self,
        paper_id: str,
        limit: int = 100,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get references for a paper.

        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of references
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Reference data
        """
        try:
            cache_key = f"references_{paper_id}_{limit}"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            params = {
                "limit": limit,
                "fields": ",".join(self.fields) if self.fields else None,
            }

            endpoint = self.config.get("endpoints", {}).get("references", "/paper/{paper_id}/references")
            url = f"{self.base_url}{endpoint}".replace("{paper_id}", paper_id)

            logger.debug(f"Fetching references for paper: {paper_id}")
            response_data = await self._make_request("GET", url, params=params)

            references = response_data.get("data", [])
            normalized_refs = [
                self._normalize_paper(ref.get("citedPaper", {})) for ref in references
            ]

            mcp_response = MCPResponse(
                success=True,
                data=normalized_refs,
                metadata={
                    "paper_id": paper_id,
                    "reference_count": len(references),
                },
                source=self.server_name,
            )

            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            return mcp_response

        except Exception as e:
            logger.error(f"Error fetching references: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def get_recommendations(
        self,
        paper_id: str,
        limit: int = 10,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get recommended papers based on a paper.

        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of recommendations
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Recommended papers
        """
        try:
            cache_key = f"recommendations_{paper_id}_{limit}"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            params = {
                "limit": limit,
                "fields": ",".join(self.fields) if self.fields else None,
            }

            # Note: This endpoint may not be available in all versions
            url = f"{self.base_url}/recommendations/v1/papers/forpaper/{paper_id}"

            logger.debug(f"Fetching recommendations for paper: {paper_id}")
            response_data = await self._make_request("GET", url, params=params)

            recommendations = response_data.get("recommendedPapers", [])
            normalized_recs = [self._normalize_paper(paper) for paper in recommendations]

            mcp_response = MCPResponse(
                success=True,
                data=normalized_recs,
                metadata={
                    "paper_id": paper_id,
                    "recommendation_count": len(recommendations),
                },
                source=self.server_name,
            )

            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            return mcp_response

        except Exception as e:
            logger.warning(f"Error fetching recommendations (may not be supported): {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Semantic Scholar paper data to common format.

        Args:
            raw_paper: Raw paper data from Semantic Scholar API

        Returns:
            Dict[str, Any]: Normalized paper data
        """
        if not raw_paper:
            return {}

        # Extract authors
        authors = []
        for author in raw_paper.get("authors", []):
            if isinstance(author, dict):
                authors.append(author.get("name", "Unknown"))
            elif isinstance(author, str):
                authors.append(author)

        # Extract external IDs
        external_ids = raw_paper.get("externalIds", {})

        # Normalize paper data
        normalized = {
            "paper_id": raw_paper.get("paperId", ""),
            "title": raw_paper.get("title", ""),
            "abstract": raw_paper.get("abstract", ""),
            "year": raw_paper.get("year"),
            "authors": authors,
            "venue": raw_paper.get("venue", ""),
            "citation_count": raw_paper.get("citationCount", 0),
            "reference_count": raw_paper.get("referenceCount", 0),
            "publication_date": raw_paper.get("publicationDate"),
            "journal": raw_paper.get("journal", {}).get("name") if raw_paper.get("journal") else None,
            "doi": external_ids.get("DOI"),
            "arxiv_id": external_ids.get("ArXiv"),
            "pubmed_id": external_ids.get("PubMed"),
            "url": raw_paper.get("url", f"https://www.semanticscholar.org/paper/{raw_paper.get('paperId', '')}"),
            "source": "semantic_scholar",
            "raw_data": raw_paper,  # Keep raw data for reference
        }

        return normalized

    async def batch_search(
        self,
        queries: List[str],
        limit_per_query: int = 50,
        filters: Optional[Dict[str, Any]] = None,
    ) -> MCPResponse:
        """
        Perform multiple searches in parallel.

        Args:
            queries: List of search queries
            limit_per_query: Limit per query
            filters: Common filters for all queries

        Returns:
            MCPResponse: Combined results from all queries
        """
        import asyncio

        tasks = [
            self.search_papers(query, limit_per_query, filters)
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_papers = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({"query": queries[i], "error": str(result)})
            elif result.success:
                all_papers.extend(result.data)

        return MCPResponse(
            success=len(all_papers) > 0,
            data=all_papers,
            metadata={
                "total_queries": len(queries),
                "total_papers": len(all_papers),
                "errors": len(errors),
                "error_details": errors,
            },
            source=self.server_name,
        )

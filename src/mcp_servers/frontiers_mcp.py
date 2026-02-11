"""
Frontiers MCP server implementation.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.mcp_servers.base_mcp import BaseMCPServer, MCPError, MCPResponse


class FrontiersMCP(BaseMCPServer):
    """Frontiers open access journal MCP server."""

    def __init__(self, state_manager=None):
        """Initialize Frontiers MCP server."""
        super().__init__("frontiers", state_manager)
        self.base_url = self.config.get("base_url", "https://api.frontiersin.org")
        self.fields = self.config.get("parameters", {}).get("fields", [])

    async def search_papers(
        self,
        query: str,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Search for papers on Frontiers.

        Args:
            query: Search query
            limit: Maximum number of results (default 100, max 200)
            filters: Filters like article_types, journals, open_access_only
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
                "limit": min(limit, self.config.get("parameters", {}).get("max_limit", 200)),
                "offset": 0,
            }

            # Add fields if configured
            if self.fields:
                params["fields"] = ",".join(self.fields)

            # Apply filters
            if filters:
                filter_config = self.config.get("filters", {})

                # Article types filter
                if "article_types" in filters:
                    params["article_type"] = ",".join(filters["article_types"])
                elif filter_config.get("article_types"):
                    params["article_type"] = ",".join(filter_config["article_types"])

                # Journal filter
                if "journals" in filters:
                    params["journal"] = ",".join(filters["journals"])

                # Date range
                if "year_from" in filters:
                    params["published_from"] = f"{filters['year_from']}-01-01"
                if "year_to" in filters:
                    params["published_to"] = f"{filters['year_to']}-12-31"

                # Open access only (default from config)
                if filters.get("open_access_only", filter_config.get("open_access_only", True)):
                    params["open_access"] = "true"

                # Peer reviewed filter
                if filters.get("peer_reviewed", filter_config.get("peer_reviewed", True)):
                    params["peer_reviewed"] = "true"

            # Make request
            endpoint = self.config.get("endpoints", {}).get("search", "/v1/articles")
            url = f"{self.base_url}{endpoint}"

            logger.info(f"Searching Frontiers: query='{query}', limit={limit}")
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
                    "limit": params["limit"],
                    "query": query,
                    "filters": filters or {},
                },
                source=self.server_name,
            )

            # Cache response
            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            logger.info(f"Found {len(normalized_papers)} papers on Frontiers")
            return mcp_response

        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Frontiers search error: {e}")
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
        Get detailed information about a specific Frontiers article.

        Args:
            paper_id: Frontiers article ID or DOI
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
            params = {}
            if self.fields:
                params["fields"] = ",".join(self.fields)

            endpoint = self.config.get("endpoints", {}).get("article", "/v1/articles/{article_id}")
            url = f"{self.base_url}{endpoint}".replace("{article_id}", paper_id)

            logger.debug(f"Fetching Frontiers article details: {paper_id}")
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
            logger.error(f"Error fetching Frontiers article {paper_id}: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def get_journals(self, use_cache: bool = True) -> MCPResponse:
        """
        Get list of Frontiers journals.

        Args:
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Journal list
        """
        try:
            cache_key = "journals_list"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            endpoint = self.config.get("endpoints", {}).get("journals", "/v1/journals")
            url = f"{self.base_url}{endpoint}"

            logger.debug("Fetching Frontiers journals list")
            response_data = await self._make_request("GET", url)

            journals = response_data.get("data", [])

            mcp_response = MCPResponse(
                success=True,
                data=journals,
                metadata={"journal_count": len(journals)},
                source=self.server_name,
            )

            # Cache for longer (journals don't change often)
            if use_cache:
                await self._cache_response(cache_key, mcp_response, ttl=604800)  # 1 week

            return mcp_response

        except Exception as e:
            logger.error(f"Error fetching journals list: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def search_by_topic(
        self,
        topic: str,
        limit: int = 50,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Search papers by research topic.

        Args:
            topic: Research topic name
            limit: Maximum number of results
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Papers related to the topic
        """
        try:
            cache_key = f"topic_{topic}_{limit}"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            endpoint = self.config.get("endpoints", {}).get("topics", "/v1/research-topics")
            url = f"{self.base_url}{endpoint}"

            params = {
                "topic": topic,
                "limit": limit,
            }

            logger.debug(f"Searching by topic: {topic}")
            response_data = await self._make_request("GET", url, params=params)

            papers = response_data.get("articles", [])
            normalized_papers = [self._normalize_paper(paper) for paper in papers]

            mcp_response = MCPResponse(
                success=True,
                data=normalized_papers,
                metadata={
                    "topic": topic,
                    "total": len(papers),
                },
                source=self.server_name,
            )

            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            return mcp_response

        except Exception as e:
            logger.warning(f"Topic search may not be supported: {e}")
            # Fallback to regular search
            return await self.search_papers(query=topic, limit=limit, use_cache=use_cache)

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Frontiers paper data to common format.

        Args:
            raw_paper: Raw paper data from Frontiers API

        Returns:
            Dict[str, Any]: Normalized paper data
        """
        if not raw_paper:
            return {}

        # Extract authors
        authors = []
        for author in raw_paper.get("authors", []):
            if isinstance(author, dict):
                first_name = author.get("first_name", "")
                last_name = author.get("last_name", "")
                full_name = f"{first_name} {last_name}".strip()
                if full_name:
                    authors.append(full_name)
            elif isinstance(author, str):
                authors.append(author)

        # Extract publication date and year
        pub_date = raw_paper.get("publicationDate") or raw_paper.get("publication_date")
        year = None
        if pub_date:
            try:
                year = int(pub_date[:4])
            except (ValueError, IndexError, TypeError):
                pass

        # Extract journal info
        journal_name = None
        journal_data = raw_paper.get("journal", {})
        if isinstance(journal_data, dict):
            journal_name = journal_data.get("name") or journal_data.get("title")
        elif isinstance(journal_data, str):
            journal_name = journal_data

        # Extract keywords
        keywords = raw_paper.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",")]

        # Normalize paper data
        normalized = {
            "paper_id": raw_paper.get("id", ""),
            "title": raw_paper.get("title", ""),
            "abstract": raw_paper.get("abstract", ""),
            "year": year,
            "authors": authors,
            "venue": journal_name or "Frontiers",
            "citation_count": raw_paper.get("citations", 0),
            "reference_count": 0,  # Not typically provided
            "publication_date": pub_date,
            "journal": journal_name,
            "doi": raw_paper.get("doi"),
            "url": raw_paper.get("url", ""),
            "pdf_url": raw_paper.get("pdf_url"),
            "keywords": keywords,
            "article_type": raw_paper.get("article_type") or raw_paper.get("type"),
            "open_access": raw_paper.get("open_access", True),
            "peer_reviewed": raw_paper.get("peer_reviewed", True),
            "source": "frontiers",
            "raw_data": raw_paper,
        }

        return normalized

    async def get_open_access_papers(
        self,
        query: str,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> MCPResponse:
        """
        Search for open access papers (Frontiers specialty).

        Args:
            query: Search query
            limit: Maximum number of results
            filters: Additional filters

        Returns:
            MCPResponse: Open access papers
        """
        # Ensure open access filter is set
        filters = filters or {}
        filters["open_access_only"] = True

        return await self.search_papers(query, limit, filters, use_cache=True)

    async def search_by_journal(
        self,
        journal_name: str,
        query: Optional[str] = None,
        limit: int = 50,
    ) -> MCPResponse:
        """
        Search papers within a specific Frontiers journal.

        Args:
            journal_name: Name of the Frontiers journal
            query: Optional search query within the journal
            limit: Maximum number of results

        Returns:
            MCPResponse: Papers from the journal
        """
        filters = {"journals": [journal_name]}

        search_query = query if query else "*"

        return await self.search_papers(
            query=search_query,
            limit=limit,
            filters=filters,
            use_cache=True,
        )

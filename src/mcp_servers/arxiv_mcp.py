"""
arXiv MCP server implementation.
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from loguru import logger

from src.mcp_servers.base_mcp import BaseMCPServer, MCPError, MCPResponse


class ArxivMCP(BaseMCPServer):
    """arXiv preprint repository MCP server."""

    def __init__(self, state_manager=None):
        """Initialize arXiv MCP server."""
        super().__init__("arxiv", state_manager)
        self.base_url = self.config.get("base_url", "http://export.arxiv.org/api")

        # arXiv namespaces for XML parsing
        self.namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

    async def search_papers(
        self,
        query: str,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Search for papers on arXiv.

        Args:
            query: Search query (can use arXiv search syntax)
            limit: Maximum number of results
            filters: Filters like categories, sort_by, sort_order
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

            # Build search query
            search_query = self._build_search_query(query, filters)

            # Prepare request parameters
            params = {
                "search_query": search_query,
                "start": 0,
                "max_results": min(limit, self.config.get("parameters", {}).get("max_results", 100)),
                "sortBy": filters.get("sort_by", "relevance") if filters else "relevance",
                "sortOrder": filters.get("sort_order", "descending") if filters else "descending",
            }

            # Make request
            endpoint = self.config.get("endpoints", {}).get("search", "/query")
            url = f"{self.base_url}{endpoint}"

            logger.info(f"Searching arXiv: query='{query}', limit={limit}")

            # arXiv returns XML, so we need custom handling
            response_text = await self._make_arxiv_request(url, params)

            # Parse XML response
            papers = self._parse_arxiv_response(response_text)
            normalized_papers = [self._normalize_paper(paper) for paper in papers]

            # Create response
            mcp_response = MCPResponse(
                success=True,
                data=normalized_papers,
                metadata={
                    "total": len(papers),
                    "query": query,
                    "filters": filters or {},
                },
                source=self.server_name,
            )

            # Cache response
            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            logger.info(f"Found {len(normalized_papers)} papers on arXiv")
            return mcp_response

        except MCPError:
            raise
        except Exception as e:
            logger.error(f"arXiv search error: {e}")
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
        Get detailed information about a specific arXiv paper.

        Args:
            paper_id: arXiv paper ID (e.g., "2301.12345" or "cs/0001234")
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

            # Clean paper ID (remove version if present)
            clean_id = paper_id.split("v")[0]

            # Search by ID
            params = {
                "id_list": clean_id,
                "max_results": 1,
            }

            endpoint = self.config.get("endpoints", {}).get("search", "/query")
            url = f"{self.base_url}{endpoint}"

            logger.debug(f"Fetching arXiv paper details: {paper_id}")
            response_text = await self._make_arxiv_request(url, params)

            # Parse response
            papers = self._parse_arxiv_response(response_text)

            if not papers:
                return MCPResponse(
                    success=False,
                    error=f"Paper not found: {paper_id}",
                    source=self.server_name,
                )

            normalized_paper = self._normalize_paper(papers[0])

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

        except Exception as e:
            logger.error(f"Error fetching arXiv paper {paper_id}: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def _make_arxiv_request(self, url: str, params: Dict[str, Any]) -> str:
        """
        Make request to arXiv API and return text response.

        Args:
            url: Request URL
            params: Query parameters

        Returns:
            str: Response text (XML)
        """
        await self.connect()
        await self._check_rate_limit()

        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.text()

        except Exception as e:
            raise MCPError(f"arXiv request failed: {str(e)}")

    def _build_search_query(self, query: str, filters: Optional[Dict[str, Any]]) -> str:
        """
        Build arXiv search query with filters.

        Args:
            query: Base search query
            filters: Additional filters

        Returns:
            str: Formatted search query
        """
        # Start with base query
        search_parts = [f"all:{query}"]

        if filters:
            # Add category filter
            if "categories" in filters and filters["categories"]:
                categories = filters["categories"]
                if isinstance(categories, list):
                    cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
                    search_parts.append(f"({cat_query})")
                else:
                    search_parts.append(f"cat:{categories}")

            # Add author filter
            if "author" in filters:
                search_parts.append(f"au:{filters['author']}")

            # Add title filter
            if "title" in filters:
                search_parts.append(f"ti:{filters['title']}")

        return " AND ".join(search_parts)

    def _parse_arxiv_response(self, xml_text: str) -> List[Dict[str, Any]]:
        """
        Parse arXiv XML response.

        Args:
            xml_text: XML response text

        Returns:
            List[Dict[str, Any]]: Parsed papers
        """
        try:
            root = ET.fromstring(xml_text)
            papers = []

            for entry in root.findall("atom:entry", self.namespaces):
                paper = {}

                # Basic fields
                paper["id"] = self._get_element_text(entry, "atom:id")
                paper["title"] = self._get_element_text(entry, "atom:title").strip()
                paper["summary"] = self._get_element_text(entry, "atom:summary").strip()
                paper["published"] = self._get_element_text(entry, "atom:published")
                paper["updated"] = self._get_element_text(entry, "atom:updated")

                # Extract arXiv ID from full URL
                if paper["id"]:
                    paper["arxiv_id"] = paper["id"].split("/")[-1]

                # Authors
                authors = []
                for author in entry.findall("atom:author", self.namespaces):
                    name = self._get_element_text(author, "atom:name")
                    if name:
                        authors.append(name)
                paper["authors"] = authors

                # Categories
                categories = []
                for category in entry.findall("atom:category", self.namespaces):
                    term = category.get("term")
                    if term:
                        categories.append(term)
                paper["categories"] = categories

                # Primary category
                primary_cat = entry.find("arxiv:primary_category", self.namespaces)
                if primary_cat is not None:
                    paper["primary_category"] = primary_cat.get("term")

                # Links (PDF, abstract page)
                for link in entry.findall("atom:link", self.namespaces):
                    rel = link.get("rel")
                    href = link.get("href")
                    if rel == "alternate":
                        paper["abstract_url"] = href
                    elif link.get("title") == "pdf":
                        paper["pdf_url"] = href

                # DOI
                doi_elem = entry.find("arxiv:doi", self.namespaces)
                if doi_elem is not None:
                    paper["doi"] = doi_elem.text

                # Journal reference
                journal_ref = entry.find("arxiv:journal_ref", self.namespaces)
                if journal_ref is not None:
                    paper["journal_ref"] = journal_ref.text

                # Comment
                comment = entry.find("arxiv:comment", self.namespaces)
                if comment is not None:
                    paper["comment"] = comment.text

                papers.append(paper)

            return papers

        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing arXiv response: {e}")
            return []

    def _get_element_text(self, parent, tag: str) -> str:
        """Get text from XML element."""
        elem = parent.find(tag, self.namespaces)
        return elem.text if elem is not None and elem.text else ""

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize arXiv paper data to common format.

        Args:
            raw_paper: Raw paper data from arXiv API

        Returns:
            Dict[str, Any]: Normalized paper data
        """
        if not raw_paper:
            return {}

        # Extract year from published date
        year = None
        if raw_paper.get("published"):
            try:
                year = int(raw_paper["published"][:4])
            except (ValueError, IndexError):
                pass

        # Normalize paper data
        normalized = {
            "paper_id": raw_paper.get("arxiv_id", ""),
            "title": raw_paper.get("title", ""),
            "abstract": raw_paper.get("summary", ""),
            "year": year,
            "authors": raw_paper.get("authors", []),
            "venue": raw_paper.get("journal_ref", "arXiv"),
            "citation_count": 0,  # arXiv doesn't provide citation counts
            "reference_count": 0,
            "publication_date": raw_paper.get("published"),
            "updated_date": raw_paper.get("updated"),
            "journal": raw_paper.get("journal_ref"),
            "doi": raw_paper.get("doi"),
            "arxiv_id": raw_paper.get("arxiv_id"),
            "categories": raw_paper.get("categories", []),
            "primary_category": raw_paper.get("primary_category"),
            "url": raw_paper.get("abstract_url", ""),
            "pdf_url": raw_paper.get("pdf_url", ""),
            "comment": raw_paper.get("comment"),
            "source": "arxiv",
            "raw_data": raw_paper,
        }

        return normalized

    async def search_by_category(
        self,
        category: str,
        limit: int = 100,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Search papers by arXiv category.

        Args:
            category: arXiv category (e.g., "cs.AI", "stat.ML")
            limit: Maximum number of results
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Papers in the category
        """
        filters = {"categories": [category]}
        return await self.search_papers(
            query="*",  # Match all
            limit=limit,
            filters=filters,
            use_cache=use_cache,
        )

    async def get_recent_papers(
        self,
        category: Optional[str] = None,
        days: int = 7,
        limit: int = 50,
    ) -> MCPResponse:
        """
        Get recent papers from arXiv.

        Args:
            category: Optional category filter
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            MCPResponse: Recent papers
        """
        from datetime import datetime, timedelta

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Format for arXiv (they don't support date filtering directly)
        # So we'll use sort by submittedDate descending
        filters = {
            "sort_by": "submittedDate",
            "sort_order": "descending",
        }

        if category:
            filters["categories"] = [category]

        return await self.search_papers(
            query="*",
            limit=limit,
            filters=filters,
            use_cache=False,  # Recent papers shouldn't be cached long
        )

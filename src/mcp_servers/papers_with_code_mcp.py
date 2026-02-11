"""
Papers With Code MCP server implementation.

Provides access to academic papers with associated code repositories,
datasets, methods, and benchmark results.
"""

import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger

from src.mcp_servers.base_mcp import BaseMCPServer, MCPError, MCPResponse


class PapersWithCodeMCP(BaseMCPServer):
    """Papers With Code academic database MCP server."""

    def __init__(self, state_manager=None):
        """Initialize Papers With Code MCP server."""
        super().__init__("papers_with_code", state_manager)
        self.base_url = self.config.get("base_url", "https://paperswithcode.com/api/v1")
        self._client = None
        self._use_client = False
        
        # Try to import the official client
        try:
            from paperswithcode import PapersWithCodeClient
            self._client = PapersWithCodeClient()
            self._use_client = True
            logger.info("Papers With Code: Using official Python client")
        except ImportError:
            logger.warning("Papers With Code: Official client not installed, using HTTP API")
            logger.info("Install with: pip install paperswithcode-client")

    async def search_papers(
        self,
        query: str,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Search for papers on Papers With Code.

        Args:
            query: Search query (title, abstract, or topic)
            limit: Maximum number of results
            filters: Optional filters (task, method, conference, etc.)
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

            logger.info(f"Searching Papers With Code: query='{query}', limit={limit}")
            
            if self._use_client:
                papers = await self._search_with_client(query, limit, filters)
            else:
                papers = await self._search_with_http(query, limit, filters)

            # Normalize papers
            normalized_papers = [self._normalize_paper(paper) for paper in papers]

            # Create response
            mcp_response = MCPResponse(
                success=True,
                data=normalized_papers,
                metadata={
                    "total": len(normalized_papers),
                    "query": query,
                    "filters": filters or {},
                    "source": "papers_with_code",
                },
                source=self.server_name,
            )

            # Cache response
            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            logger.info(f"Found {len(normalized_papers)} papers on Papers With Code")
            return mcp_response

        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Papers With Code search error: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def _search_with_client(
        self,
        query: str,
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search using the official Python client."""
        from paperswithcode import PapersWithCodeClient
        
        # Run in thread pool since client is synchronous
        loop = asyncio.get_event_loop()
        
        def _sync_search():
            client = PapersWithCodeClient()
            papers = []
            
            # Search by query
            try:
                # Try searching papers directly
                results = client.paper_list(q=query)
                
                for paper in results.results[:limit]:
                    paper_dict = {
                        "id": getattr(paper, 'id', None),
                        "title": getattr(paper, 'title', ''),
                        "abstract": getattr(paper, 'abstract', ''),
                        "url_abs": getattr(paper, 'url_abs', ''),
                        "url_pdf": getattr(paper, 'url_pdf', ''),
                        "arxiv_id": getattr(paper, 'arxiv_id', None),
                        "conference": getattr(paper, 'conference', None),
                        "proceeding": getattr(paper, 'proceeding', None),
                        "authors": getattr(paper, 'authors', []),
                        "published": getattr(paper, 'published', None),
                        "tasks": [],
                        "methods": [],
                        "repositories": [],
                    }
                    
                    # Try to get associated repositories
                    try:
                        if paper.id:
                            repos = client.paper_repository_list(paper_id=paper.id)
                            paper_dict["repositories"] = [
                                {
                                    "url": getattr(r, 'url', ''),
                                    "stars": getattr(r, 'stars', 0),
                                    "framework": getattr(r, 'framework', ''),
                                }
                                for r in repos.results[:5]  # Top 5 repos
                            ]
                    except Exception:
                        pass
                    
                    papers.append(paper_dict)
                    
            except Exception as e:
                logger.warning(f"Client search failed: {e}, trying task-based search")
                
                # Fallback: search by task if direct search fails
                if filters and filters.get("task"):
                    try:
                        task_papers = client.paper_list(task=filters["task"])
                        for paper in task_papers.results[:limit]:
                            papers.append({
                                "id": getattr(paper, 'id', None),
                                "title": getattr(paper, 'title', ''),
                                "abstract": getattr(paper, 'abstract', ''),
                                "url_abs": getattr(paper, 'url_abs', ''),
                                "arxiv_id": getattr(paper, 'arxiv_id', None),
                                "authors": getattr(paper, 'authors', []),
                                "published": getattr(paper, 'published', None),
                            })
                    except Exception as task_err:
                        logger.error(f"Task-based search also failed: {task_err}")
            
            return papers
        
        papers = await loop.run_in_executor(None, _sync_search)
        return papers

    async def _search_with_http(
        self,
        query: str,
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search using direct HTTP API calls."""
        import httpx
        import ssl
        import certifi
        
        papers = []
        
        # Create SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        async with httpx.AsyncClient(timeout=30, verify=ssl_context, follow_redirects=True) as client:
            # Search papers endpoint
            params = {
                "q": query,
                "items_per_page": min(limit, 50),  # API limit
            }
            
            # Add filters
            if filters:
                if filters.get("task"):
                    params["task"] = filters["task"]
                if filters.get("conference"):
                    params["conference"] = filters["conference"]
            
            try:
                response = await client.get(
                    f"{self.base_url}/papers/",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                
                for paper in data.get("results", [])[:limit]:
                    papers.append(paper)
                    
            except httpx.HTTPError as e:
                logger.error(f"HTTP error searching Papers With Code: {e}")
                raise MCPError(f"HTTP error: {e}")
        
        return papers

    async def get_paper_details(
        self,
        paper_id: str,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get detailed information about a specific paper.

        Args:
            paper_id: Papers With Code paper ID
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Paper details including code repositories
        """
        try:
            cache_key = f"pwc_paper_{paper_id}"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            logger.debug(f"Fetching paper details: {paper_id}")

            if self._use_client:
                paper_data = await self._get_paper_with_client(paper_id)
            else:
                paper_data = await self._get_paper_with_http(paper_id)

            normalized_paper = self._normalize_paper(paper_data)

            mcp_response = MCPResponse(
                success=True,
                data=[normalized_paper],
                metadata={"paper_id": paper_id},
                source=self.server_name,
            )

            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            return mcp_response

        except Exception as e:
            logger.error(f"Error fetching paper {paper_id}: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def _get_paper_with_client(self, paper_id: str) -> Dict[str, Any]:
        """Get paper details using official client."""
        loop = asyncio.get_event_loop()
        
        def _sync_get():
            from paperswithcode import PapersWithCodeClient
            client = PapersWithCodeClient()
            
            paper = client.paper_get(paper_id=paper_id)
            
            paper_dict = {
                "id": getattr(paper, 'id', None),
                "title": getattr(paper, 'title', ''),
                "abstract": getattr(paper, 'abstract', ''),
                "url_abs": getattr(paper, 'url_abs', ''),
                "url_pdf": getattr(paper, 'url_pdf', ''),
                "arxiv_id": getattr(paper, 'arxiv_id', None),
                "conference": getattr(paper, 'conference', None),
                "authors": getattr(paper, 'authors', []),
                "published": getattr(paper, 'published', None),
                "repositories": [],
                "tasks": [],
                "methods": [],
                "datasets": [],
            }
            
            # Get repositories
            try:
                repos = client.paper_repository_list(paper_id=paper_id)
                paper_dict["repositories"] = [
                    {
                        "url": getattr(r, 'url', ''),
                        "stars": getattr(r, 'stars', 0),
                        "framework": getattr(r, 'framework', ''),
                        "is_official": getattr(r, 'is_official', False),
                    }
                    for r in repos.results
                ]
            except Exception:
                pass
            
            # Get tasks
            try:
                tasks = client.paper_task_list(paper_id=paper_id)
                paper_dict["tasks"] = [
                    getattr(t, 'name', '') for t in tasks.results
                ]
            except Exception:
                pass
            
            # Get methods
            try:
                methods = client.paper_method_list(paper_id=paper_id)
                paper_dict["methods"] = [
                    {
                        "name": getattr(m, 'name', ''),
                        "full_name": getattr(m, 'full_name', ''),
                    }
                    for m in methods.results
                ]
            except Exception:
                pass
            
            return paper_dict
        
        return await loop.run_in_executor(None, _sync_get)

    async def _get_paper_with_http(self, paper_id: str) -> Dict[str, Any]:
        """Get paper details using HTTP API."""
        import httpx
        import ssl
        import certifi
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        async with httpx.AsyncClient(timeout=30, verify=ssl_context, follow_redirects=True) as client:
            response = await client.get(f"{self.base_url}/papers/{paper_id}/")
            response.raise_for_status()
            return response.json()

    async def search_by_task(
        self,
        task: str,
        limit: int = 50,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Search papers by ML task (e.g., 'image-classification', 'object-detection').

        Args:
            task: ML task name
            limit: Maximum number of results
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Papers related to the task
        """
        return await self.search_papers(
            query="",
            limit=limit,
            filters={"task": task},
            use_cache=use_cache,
        )

    async def get_paper_repositories(
        self,
        paper_id: str,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get code repositories associated with a paper.

        Args:
            paper_id: Papers With Code paper ID
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: List of code repositories
        """
        try:
            cache_key = f"pwc_repos_{paper_id}"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            logger.debug(f"Fetching repositories for paper: {paper_id}")

            if self._use_client:
                repos = await self._get_repos_with_client(paper_id)
            else:
                repos = await self._get_repos_with_http(paper_id)

            mcp_response = MCPResponse(
                success=True,
                data=repos,
                metadata={
                    "paper_id": paper_id,
                    "repository_count": len(repos),
                },
                source=self.server_name,
            )

            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            return mcp_response

        except Exception as e:
            logger.error(f"Error fetching repositories: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def _get_repos_with_client(self, paper_id: str) -> List[Dict[str, Any]]:
        """Get repositories using official client."""
        loop = asyncio.get_event_loop()
        
        def _sync_get():
            from paperswithcode import PapersWithCodeClient
            client = PapersWithCodeClient()
            
            repos = client.paper_repository_list(paper_id=paper_id)
            return [
                {
                    "url": getattr(r, 'url', ''),
                    "stars": getattr(r, 'stars', 0),
                    "framework": getattr(r, 'framework', ''),
                    "is_official": getattr(r, 'is_official', False),
                    "description": getattr(r, 'description', ''),
                }
                for r in repos.results
            ]
        
        return await loop.run_in_executor(None, _sync_get)

    async def _get_repos_with_http(self, paper_id: str) -> List[Dict[str, Any]]:
        """Get repositories using HTTP API."""
        import httpx
        import ssl
        import certifi
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        async with httpx.AsyncClient(timeout=30, verify=ssl_context, follow_redirects=True) as client:
            response = await client.get(
                f"{self.base_url}/papers/{paper_id}/repositories/"
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    async def get_sota_results(
        self,
        task: str,
        dataset: Optional[str] = None,
        limit: int = 20,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get state-of-the-art results for a task/dataset.

        Args:
            task: ML task name
            dataset: Optional dataset name
            limit: Maximum number of results
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: SOTA results with metrics
        """
        try:
            cache_key = f"pwc_sota_{task}_{dataset}_{limit}"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            logger.info(f"Fetching SOTA results for task: {task}")

            if self._use_client:
                results = await self._get_sota_with_client(task, dataset, limit)
            else:
                results = await self._get_sota_with_http(task, dataset, limit)

            mcp_response = MCPResponse(
                success=True,
                data=results,
                metadata={
                    "task": task,
                    "dataset": dataset,
                    "result_count": len(results),
                },
                source=self.server_name,
            )

            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            return mcp_response

        except Exception as e:
            logger.error(f"Error fetching SOTA results: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def _get_sota_with_client(
        self,
        task: str,
        dataset: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get SOTA results using official client."""
        loop = asyncio.get_event_loop()
        
        def _sync_get():
            from paperswithcode import PapersWithCodeClient
            client = PapersWithCodeClient()
            
            results = []
            try:
                # Get evaluation results for the task
                evals = client.evaluation_list(task=task)
                
                for eval_item in evals.results[:limit]:
                    results.append({
                        "task": task,
                        "dataset": getattr(eval_item, 'dataset', ''),
                        "metric": getattr(eval_item, 'metric', ''),
                        "model": getattr(eval_item, 'model', ''),
                        "paper_title": getattr(eval_item, 'paper_title', ''),
                        "score": getattr(eval_item, 'score', None),
                    })
            except Exception as e:
                logger.warning(f"Could not fetch SOTA results: {e}")
            
            return results
        
        return await loop.run_in_executor(None, _sync_get)

    async def _get_sota_with_http(
        self,
        task: str,
        dataset: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get SOTA results using HTTP API."""
        import httpx
        import ssl
        import certifi
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        async with httpx.AsyncClient(timeout=30, verify=ssl_context, follow_redirects=True) as client:
            params = {"task": task, "items_per_page": limit}
            if dataset:
                params["dataset"] = dataset
            
            response = await client.get(
                f"{self.base_url}/evaluations/",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    async def get_methods(
        self,
        query: str = "",
        limit: int = 20,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get ML methods/techniques.

        Args:
            query: Search query for methods
            limit: Maximum number of results
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: List of methods
        """
        try:
            cache_key = f"pwc_methods_{query}_{limit}"
            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return cached

            if self._use_client:
                methods = await self._get_methods_with_client(query, limit)
            else:
                methods = await self._get_methods_with_http(query, limit)

            mcp_response = MCPResponse(
                success=True,
                data=methods,
                metadata={"query": query, "method_count": len(methods)},
                source=self.server_name,
            )

            if use_cache:
                await self._cache_response(cache_key, mcp_response)

            return mcp_response

        except Exception as e:
            logger.error(f"Error fetching methods: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                source=self.server_name,
            )

    async def _get_methods_with_client(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Get methods using official client."""
        loop = asyncio.get_event_loop()
        
        def _sync_get():
            from paperswithcode import PapersWithCodeClient
            client = PapersWithCodeClient()
            
            methods = client.method_list(q=query) if query else client.method_list()
            return [
                {
                    "name": getattr(m, 'name', ''),
                    "full_name": getattr(m, 'full_name', ''),
                    "description": getattr(m, 'description', ''),
                    "paper_count": getattr(m, 'paper_count', 0),
                }
                for m in methods.results[:limit]
            ]
        
        return await loop.run_in_executor(None, _sync_get)

    async def _get_methods_with_http(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Get methods using HTTP API."""
        import httpx
        import ssl
        import certifi
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        async with httpx.AsyncClient(timeout=30, verify=ssl_context, follow_redirects=True) as client:
            params = {"items_per_page": limit}
            if query:
                params["q"] = query
            
            response = await client.get(
                f"{self.base_url}/methods/",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Papers With Code paper data to common format.

        Args:
            raw_paper: Raw paper data from PWC API

        Returns:
            Dict[str, Any]: Normalized paper data
        """
        if not raw_paper:
            return {}

        # Extract authors
        authors = raw_paper.get("authors", [])
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(",")]

        # Extract repositories
        repositories = raw_paper.get("repositories", [])
        repo_urls = [r.get("url", "") for r in repositories if isinstance(r, dict)]
        
        # Get best repo (most stars or official)
        best_repo = None
        if repositories:
            official = [r for r in repositories if r.get("is_official")]
            if official:
                best_repo = official[0]
            else:
                sorted_repos = sorted(
                    repositories,
                    key=lambda x: x.get("stars", 0),
                    reverse=True,
                )
                if sorted_repos:
                    best_repo = sorted_repos[0]

        # Normalize paper data
        normalized = {
            "paper_id": raw_paper.get("id", ""),
            "title": raw_paper.get("title", ""),
            "abstract": raw_paper.get("abstract", ""),
            "year": self._extract_year(raw_paper.get("published")),
            "authors": authors[:10],  # Limit to first 10 authors
            "venue": raw_paper.get("conference") or raw_paper.get("proceeding", ""),
            "citation_count": raw_paper.get("citation_count", 0),
            "publication_date": raw_paper.get("published"),
            "doi": raw_paper.get("doi"),
            "arxiv_id": raw_paper.get("arxiv_id"),
            "url": raw_paper.get("url_abs") or f"https://paperswithcode.com/paper/{raw_paper.get('id', '')}",
            "pdf_url": raw_paper.get("url_pdf"),
            "source": "papers_with_code",
            # PWC-specific fields
            "has_code": len(repositories) > 0,
            "code_url": best_repo.get("url") if best_repo else None,
            "code_stars": best_repo.get("stars", 0) if best_repo else 0,
            "code_framework": best_repo.get("framework", "") if best_repo else "",
            "repositories": repositories,
            "tasks": raw_paper.get("tasks", []),
            "methods": raw_paper.get("methods", []),
            "datasets": raw_paper.get("datasets", []),
            "raw_data": raw_paper,
        }

        return normalized

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from date string."""
        if not date_str:
            return None
        try:
            if isinstance(date_str, str):
                return int(date_str[:4])
            return None
        except (ValueError, TypeError):
            return None

    async def batch_search(
        self,
        queries: List[str],
        limit_per_query: int = 20,
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

        # Deduplicate by paper_id
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            paper_id = paper.get("paper_id") or paper.get("arxiv_id") or paper.get("title")
            if paper_id not in seen_ids:
                seen_ids.add(paper_id)
                unique_papers.append(paper)

        return MCPResponse(
            success=len(unique_papers) > 0,
            data=unique_papers,
            metadata={
                "total_queries": len(queries),
                "total_papers": len(unique_papers),
                "errors": len(errors),
                "error_details": errors,
            },
            source=self.server_name,
        )

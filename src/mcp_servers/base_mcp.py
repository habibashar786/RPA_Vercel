"""
Base MCP server class for academic database integration.
"""

import asyncio
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import ssl
import certifi
from loguru import logger
from pydantic import BaseModel

from src.core.config import get_mcp_config, get_settings
from src.core.state_manager import StateManager, get_state_manager


class MCPError(Exception):
    """Base exception for MCP server errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        """Initialize MCP error."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class MCPResponse(BaseModel):
    """Response from MCP server."""

    success: bool
    data: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None
    source: str
    timestamp: datetime = None

    def __init__(self, **data):
        """Initialize with current timestamp."""
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)


class BaseMCPServer(ABC):
    """Base class for MCP servers."""

    def __init__(
        self,
        server_name: str,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize MCP server.

        Args:
            server_name: Name of the MCP server (e.g., 'semantic_scholar')
            state_manager: State manager for caching
        """
        self.server_name = server_name
        self.settings = get_settings()
        self.mcp_config = get_mcp_config()
        self.config = self.mcp_config.get_server_config(server_name)
        self.global_config = self.mcp_config.get_global_settings()

        # State manager for caching
        self.state = state_manager or get_state_manager()

        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None

        # Rate limiting
        self._request_times: List[float] = []
        self._rate_limit_lock = asyncio.Lock()

        # Validate configuration
        if not self.config:
            raise ValueError(f"No configuration found for MCP server: {server_name}")

        if not self.config.get("enabled", False):
            logger.warning(f"MCP server {server_name} is disabled in configuration")

        logger.info(f"Initialized MCP server: {server_name}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Initialize HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                total=self.global_config.get("read_timeout", 30),
                connect=self.global_config.get("connection_timeout", 10),
            )
            # Create SSL context with proper certificates
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._get_headers(),
                connector=connector,
            )
            logger.debug(f"Connected MCP server: {self.server_name}")

    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug(f"Disconnected MCP server: {self.server_name}")

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        headers = {
            "User-Agent": self.global_config.get("user_agent", "ResearchProposalGenerator/1.0"),
            "Accept": "application/json",
        }

        # Add authentication if configured
        auth_config = self.config.get("authentication", {})
        auth_type = auth_config.get("type")

        if auth_type == "api_key":
            key_env = auth_config.get("key_env_var")
            if key_env:
                api_key = getattr(self.settings, key_env.lower(), None)
                if api_key:
                    header_name = auth_config.get("header_name", "Authorization")
                    prefix = auth_config.get("prefix", "")
                    headers[header_name] = f"{prefix} {api_key}".strip()

        return headers

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limits."""
        rate_limits = self.config.get("rate_limits", {})
        requests_per_second = rate_limits.get("requests_per_second")

        if not requests_per_second:
            return

        async with self._rate_limit_lock:
            now = asyncio.get_event_loop().time()

            # Remove requests older than 1 second
            self._request_times = [t for t in self._request_times if now - t < 1.0]

            # Check if we've hit the limit
            if len(self._request_times) >= requests_per_second:
                sleep_time = 1.0 - (now - self._request_times[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                    self._request_times = []

            self._request_times.append(now)

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            json_data: JSON body data
            retry_count: Current retry attempt

        Returns:
            Dict[str, Any]: Response data

        Raises:
            MCPError: If request fails after retries
        """
        await self.connect()
        await self._check_rate_limit()

        retry_policy = self.config.get("retry_policy", {})
        max_retries = retry_policy.get("max_retries", 3)
        backoff_factor = retry_policy.get("backoff_factor", 2)
        retry_statuses = retry_policy.get("retry_on_status", [429, 500, 502, 503, 504])

        try:
            async with self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            ) as response:

                # Check for rate limiting
                if response.status in retry_statuses and retry_count < max_retries:
                    wait_time = backoff_factor ** retry_count
                    logger.warning(
                        f"Request failed with status {response.status}, "
                        f"retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    return await self._make_request(method, url, params, json_data, retry_count + 1)

                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as e:
            if retry_count < max_retries:
                wait_time = backoff_factor ** retry_count
                logger.warning(f"Request error: {e}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, url, params, json_data, retry_count + 1)

            raise MCPError(
                f"Request failed after {max_retries} retries: {str(e)}",
                status_code=getattr(e, 'status', None),
            )

        except Exception as e:
            raise MCPError(f"Unexpected error in request: {str(e)}")

    def _generate_cache_key(self, query: str, filters: Optional[Dict] = None) -> str:
        """Generate cache key for query."""
        key_parts = [self.server_name, query]
        if filters:
            key_parts.append(str(sorted(filters.items())))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _get_cached_response(self, cache_key: str) -> Optional[MCPResponse]:
        """Get cached response if available."""
        if not self.global_config.get("caching", {}).get("enabled", True):
            return None

        try:
            cached = await self.state.cache_get(cache_key)
            if cached:
                logger.debug(f"Cache hit for key: {cache_key}")
                return MCPResponse(**cached)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")

        return None

    async def _cache_response(self, cache_key: str, response: MCPResponse, ttl: Optional[int] = None) -> bool:
        """Cache response."""
        if not self.global_config.get("caching", {}).get("enabled", True):
            return False

        try:
            ttl = ttl or self.global_config.get("caching", {}).get("ttl", 86400)
            await self.state.cache_set(cache_key, response.model_dump(), ttl)
            logger.debug(f"Cached response for key: {cache_key}")
            return True
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
            return False

    @abstractmethod
    async def search_papers(
        self,
        query: str,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Search for academic papers.

        Args:
            query: Search query
            limit: Maximum number of results
            filters: Additional filters (year, venue, etc.)
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Search results
        """
        pass

    @abstractmethod
    async def get_paper_details(
        self,
        paper_id: str,
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get detailed information about a paper.

        Args:
            paper_id: Paper identifier
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Paper details
        """
        pass

    async def batch_get_papers(
        self,
        paper_ids: List[str],
        use_cache: bool = True,
    ) -> MCPResponse:
        """
        Get details for multiple papers.

        Args:
            paper_ids: List of paper identifiers
            use_cache: Whether to use cached results

        Returns:
            MCPResponse: Batch paper details
        """
        results = []
        errors = []

        for paper_id in paper_ids:
            try:
                response = await self.get_paper_details(paper_id, use_cache)
                if response.success and response.data:
                    results.extend(response.data)
            except Exception as e:
                logger.error(f"Error fetching paper {paper_id}: {e}")
                errors.append({"paper_id": paper_id, "error": str(e)})

        return MCPResponse(
            success=len(results) > 0,
            data=results,
            metadata={"total": len(results), "errors": len(errors), "error_details": errors},
            source=self.server_name,
        )

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize paper data to common format.

        Args:
            raw_paper: Raw paper data from API

        Returns:
            Dict[str, Any]: Normalized paper data
        """
        # To be implemented by subclasses with server-specific normalization
        return raw_paper

    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health.

        Returns:
            Dict[str, Any]: Health status
        """
        try:
            await self.connect()
            return {
                "server": self.server_name,
                "status": "healthy",
                "enabled": self.config.get("enabled", False),
                "base_url": self.config.get("base_url", ""),
            }
        except Exception as e:
            return {
                "server": self.server_name,
                "status": "unhealthy",
                "error": str(e),
            }

    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(name={self.server_name})>"

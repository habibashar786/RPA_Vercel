"""
MCP (Model Context Protocol) servers for academic database access.
"""

from src.mcp_servers.base_mcp import BaseMCPServer, MCPResponse, MCPError
from src.mcp_servers.semantic_scholar_mcp import SemanticScholarMCP
from src.mcp_servers.arxiv_mcp import ArxivMCP
from src.mcp_servers.frontiers_mcp import FrontiersMCP

__all__ = [
    "BaseMCPServer",
    "MCPResponse",
    "MCPError",
    "SemanticScholarMCP",
    "ArxivMCP",
    "FrontiersMCP",
]

"""
Configuration management for the Research Proposal Generation System.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and config files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Research Proposal Generator"
    app_version: str = "0.1.0"
    debug: bool = False
    testing: bool = False
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_workers: int = 4

    # LLM Configuration
    anthropic_api_key: str = ""
    openai_api_key: Optional[str] = None
    default_llm_provider: str = "anthropic"
    default_model: str = "claude-3-5-sonnet-20240620"
    temperature: float = 0.7
    max_tokens: int = 4096
    max_retries: int = 3

    # Academic Database APIs
    semantic_scholar_api_key: Optional[str] = None
    arxiv_api_key: Optional[str] = None
    frontiers_api_key: Optional[str] = None
    pubmed_api_key: Optional[str] = None

    # Vector Database
    vector_db_path: Path = Path("./data/vector_db")
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./data/research_proposals.db"
    database_echo: bool = False

    # Workflow Configuration
    max_parallel_agents: int = 5
    task_timeout: int = 300
    enable_caching: bool = True
    enable_parallel_processing: bool = True

    # MCP Server Configuration
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 5000
    mcp_timeout: int = 60

    # Document Generation
    output_format: str = "pdf,docx"
    output_directory: Path = Path("./data/outputs")
    font_family: str = "Times New Roman"
    font_size: int = 12
    citation_style: str = "harvard"

    # Logging
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_format: str = "json"
    log_file: Path = Path("./logs/app.log")

    # Monitoring
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    sentry_dsn: Optional[str] = None

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Feature Flags
    enable_ai_optimization: bool = True
    enable_risk_assessment: bool = True
    enable_turnitin_check: bool = True

    # Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    config_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "config")
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")

    @field_validator("output_directory", "vector_db_path", "data_dir", "logs_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output formats."""
        valid_formats = {"pdf", "docx", "tex"}
        formats = {f.strip().lower() for f in v.split(",")}
        if not formats.issubset(valid_formats):
            raise ValueError(f"Invalid output format. Valid options: {valid_formats}")
        return v

    def get_output_formats(self) -> List[str]:
        """Get list of output formats."""
        return [f.strip().lower() for f in self.output_format.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


class AgentConfig:
    """Configuration loader for agent-specific settings."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize agent configuration."""
        if config_path is None:
            settings = get_settings()
            config_path = settings.config_dir / "agents_config.yaml"

        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        agents = self._config.get("agents", {})
        if agent_name == "orchestrator":
            return self._config.get("orchestrator", {})
        return agents.get(agent_name, {})

    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration."""
        return self._config.get("workflow", {})

    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent configurations."""
        return self._config.get("agents", {})

    @property
    def config(self) -> Dict[str, Any]:
        """Get raw configuration dictionary."""
        return self._config


class MCPConfig:
    """Configuration loader for MCP server settings."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize MCP configuration."""
        if config_path is None:
            settings = get_settings()
            config_path = settings.config_dir / "mcp_config.yaml"

        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

    def get_server_config(self, server_name: str) -> Dict[str, Any]:
        """Get configuration for a specific MCP server."""
        servers = self._config.get("mcp_servers", {})
        return servers.get(server_name, {})

    def get_enabled_servers(self) -> List[str]:
        """Get list of enabled MCP servers."""
        servers = self._config.get("mcp_servers", {})
        return [name for name, config in servers.items() if config.get("enabled", False)]

    def get_search_strategy(self, strategy_name: str = "comprehensive") -> Dict[str, Any]:
        """Get search strategy configuration."""
        strategies = self._config.get("search_strategy", {}).get("strategies", {})
        return strategies.get(strategy_name, strategies.get("comprehensive", {}))

    def get_global_settings(self) -> Dict[str, Any]:
        """Get global MCP settings."""
        return self._config.get("global_settings", {})

    @property
    def config(self) -> Dict[str, Any]:
        """Get raw configuration dictionary."""
        return self._config


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


@lru_cache()
def get_agent_config() -> AgentConfig:
    """Get cached agent configuration instance."""
    return AgentConfig()


@lru_cache()
def get_mcp_config() -> MCPConfig:
    """Get cached MCP configuration instance."""
    return MCPConfig()


def reload_config() -> None:
    """Clear configuration cache and reload."""
    get_settings.cache_clear()
    get_agent_config.cache_clear()
    get_mcp_config.cache_clear()

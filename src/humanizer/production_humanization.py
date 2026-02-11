"""
Production AI Humanization Integration v2.0.0
==============================================

This module provides production-ready AI humanization with multiple providers,
automatic fallback, and MCP server integration for ResearchAI.

STRATEGY:
=========
1. Primary: MCP Server (Text2Go) - via Claude Desktop integration
2. Secondary: WriteHybrid API - RESTful API with 95%+ bypass rate
3. Tertiary: Undetectable.ai API - Industry standard
4. Fallback: Built-in advanced humanizer

TARGET: <10% AI detection on Copyleaks, Originality.ai, Turnitin, GPTZero

PROVIDERS SUPPORTED:
- Text2Go (MCP Server) - Free tier available
- WriteHybrid API - $29/month for 100K words
- Undetectable.ai - $9.99/month for 10K words
- Netus AI - $19/month unlimited

Author: ResearchAI Platform
Version: 2.0.0
"""

import aiohttp
import asyncio
import os
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class HumanizationProvider(Enum):
    """Supported humanization providers."""
    TEXT2GO_MCP = "text2go_mcp"           # MCP Server (Free)
    WRITEHYBRID = "writehybrid"           # $29/month
    UNDETECTABLE_AI = "undetectable_ai"   # $9.99/month
    NETUS_AI = "netus_ai"                 # $19/month
    STEALTH_GPT = "stealth_gpt"           # $14.99/month
    BUILTIN = "builtin"                   # Free (less effective)


@dataclass
class HumanizationConfig:
    """Configuration for production humanization."""
    primary_provider: HumanizationProvider = HumanizationProvider.WRITEHYBRID
    fallback_providers: List[HumanizationProvider] = field(default_factory=lambda: [
        HumanizationProvider.UNDETECTABLE_AI,
        HumanizationProvider.NETUS_AI,
        HumanizationProvider.BUILTIN,
    ])
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    retry_attempts: int = 2
    timeout_seconds: int = 60
    preserve_citations: bool = True
    preserve_formatting: bool = True
    academic_mode: bool = True


@dataclass 
class HumanizationResult:
    """Result from humanization operation."""
    success: bool
    original_text: str
    humanized_text: str
    provider: str
    ai_score_before: Optional[float] = None
    ai_score_after: Optional[float] = None
    processing_time: Optional[float] = None
    word_count_original: int = 0
    word_count_humanized: int = 0
    cached: bool = False
    error: Optional[str] = None
    metadata: Optional[Dict] = None


# =============================================================================
# PROVIDER IMPLEMENTATIONS
# =============================================================================

class BaseProvider(ABC):
    """Base class for humanization providers."""
    
    @abstractmethod
    async def humanize(self, text: str, **kwargs) -> HumanizationResult:
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class WriteHybridProvider(BaseProvider):
    """
    WriteHybrid API Integration.
    
    Website: https://www.writehybrid.com
    API Docs: https://www.writehybrid.com/api-docs
    Pricing: $29/month for 100K words
    Effectiveness: 95%+ bypass rate
    """
    
    def __init__(self):
        self.api_key = os.environ.get("WRITEHYBRID_API_KEY")
        self.base_url = "https://whbserver.com/api/v1"
        
    @property
    def name(self) -> str:
        return "writehybrid"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def humanize(self, text: str, **kwargs) -> HumanizationResult:
        if not self.is_configured():
            return HumanizationResult(
                success=False,
                original_text=text,
                humanized_text=text,
                provider=self.name,
                error="WRITEHYBRID_API_KEY not configured"
            )
        
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "text": text,
                    "complexity": kwargs.get("complexity", "medium"),
                    "purpose": kwargs.get("purpose", "academic"),
                }
                
                async with session.post(
                    f"{self.base_url}/humanizer/",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.status == 200:
                        data = await response.json()
                        return HumanizationResult(
                            success=True,
                            original_text=text,
                            humanized_text=data.get("humanized_text", text),
                            provider=self.name,
                            ai_score_after=data.get("detection_score", 0) * 100,
                            processing_time=processing_time,
                            word_count_original=len(text.split()),
                            word_count_humanized=len(data.get("humanized_text", text).split()),
                            metadata=data
                        )
                    else:
                        error_text = await response.text()
                        return HumanizationResult(
                            success=False,
                            original_text=text,
                            humanized_text=text,
                            provider=self.name,
                            processing_time=processing_time,
                            error=f"API error {response.status}: {error_text}"
                        )
                        
        except asyncio.TimeoutError:
            return HumanizationResult(
                success=False,
                original_text=text,
                humanized_text=text,
                provider=self.name,
                error="Request timeout"
            )
        except Exception as e:
            return HumanizationResult(
                success=False,
                original_text=text,
                humanized_text=text,
                provider=self.name,
                error=str(e)
            )


class UndetectableAIProvider(BaseProvider):
    """
    Undetectable.ai API Integration.
    
    Website: https://undetectable.ai
    Pricing: $9.99/month for 10K words
    Effectiveness: 95%+ bypass rate
    """
    
    def __init__(self):
        self.api_key = os.environ.get("UNDETECTABLE_AI_API_KEY")
        self.base_url = "https://api.undetectable.ai/v1"
        
    @property
    def name(self) -> str:
        return "undetectable_ai"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def humanize(self, text: str, **kwargs) -> HumanizationResult:
        if not self.is_configured():
            return HumanizationResult(
                success=False,
                original_text=text,
                humanized_text=text,
                provider=self.name,
                error="UNDETECTABLE_AI_API_KEY not configured"
            )
        
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "text": text,
                    "readability": kwargs.get("readability", "University"),
                    "purpose": kwargs.get("purpose", "Essay"),
                    "strength": kwargs.get("strength", "More Human"),
                }
                
                async with session.post(
                    f"{self.base_url}/humanize",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.status == 200:
                        data = await response.json()
                        return HumanizationResult(
                            success=True,
                            original_text=text,
                            humanized_text=data.get("output", text),
                            provider=self.name,
                            ai_score_before=data.get("ai_score_before"),
                            ai_score_after=data.get("ai_score_after"),
                            processing_time=processing_time,
                            word_count_original=len(text.split()),
                            word_count_humanized=len(data.get("output", text).split()),
                            metadata=data
                        )
                    else:
                        error_text = await response.text()
                        return HumanizationResult(
                            success=False,
                            original_text=text,
                            humanized_text=text,
                            provider=self.name,
                            processing_time=processing_time,
                            error=f"API error {response.status}: {error_text}"
                        )
                        
        except Exception as e:
            return HumanizationResult(
                success=False,
                original_text=text,
                humanized_text=text,
                provider=self.name,
                error=str(e)
            )


class NetusAIProvider(BaseProvider):
    """
    Netus AI API Integration.
    
    Website: https://netus.ai
    Pricing: $19/month unlimited
    Effectiveness: 99%+ bypass rate (claimed)
    """
    
    def __init__(self):
        self.api_key = os.environ.get("NETUS_AI_API_KEY")
        self.base_url = "https://api.netus.ai/v1"
        
    @property
    def name(self) -> str:
        return "netus_ai"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def humanize(self, text: str, **kwargs) -> HumanizationResult:
        if not self.is_configured():
            return HumanizationResult(
                success=False,
                original_text=text,
                humanized_text=text,
                provider=self.name,
                error="NETUS_AI_API_KEY not configured"
            )
        
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "text": text,
                    "mode": kwargs.get("mode", "academic"),
                    "language": kwargs.get("language", "en"),
                }
                
                async with session.post(
                    f"{self.base_url}/bypass",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.status == 200:
                        data = await response.json()
                        return HumanizationResult(
                            success=True,
                            original_text=text,
                            humanized_text=data.get("result", text),
                            provider=self.name,
                            ai_score_after=100 - data.get("human_score", 0),
                            processing_time=processing_time,
                            word_count_original=len(text.split()),
                            word_count_humanized=len(data.get("result", text).split()),
                            metadata=data
                        )
                    else:
                        error_text = await response.text()
                        return HumanizationResult(
                            success=False,
                            original_text=text,
                            humanized_text=text,
                            provider=self.name,
                            processing_time=processing_time,
                            error=f"API error {response.status}: {error_text}"
                        )
                        
        except Exception as e:
            return HumanizationResult(
                success=False,
                original_text=text,
                humanized_text=text,
                provider=self.name,
                error=str(e)
            )


class BuiltinHumanizerProvider(BaseProvider):
    """
    Built-in humanizer using advanced vocabulary/structure transformation.
    
    Less effective than external APIs but works offline.
    Effectiveness: ~30% reduction
    """
    
    @property
    def name(self) -> str:
        return "builtin"
    
    def is_configured(self) -> bool:
        return True  # Always available
    
    async def humanize(self, text: str, **kwargs) -> HumanizationResult:
        start_time = datetime.now()
        
        try:
            from src.humanizer.advanced_humanizer_engine import AdvancedHumanizerEngine, HumanizationConfig as EngineConfig, HumanizationLevel
            
            config = EngineConfig(
                level=HumanizationLevel.AGGRESSIVE,
                preserve_citations=kwargs.get("preserve_citations", True),
            )
            engine = AdvancedHumanizerEngine(config)
            
            humanized, stats = engine.humanize(text, "body")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return HumanizationResult(
                success=True,
                original_text=text,
                humanized_text=humanized,
                provider=self.name,
                ai_score_before=stats.estimated_ai_before,
                ai_score_after=stats.estimated_ai_after,
                processing_time=processing_time,
                word_count_original=stats.original_words,
                word_count_humanized=stats.final_words,
                metadata={
                    "vocabulary_changes": stats.vocabulary_changes,
                    "sentences_restructured": stats.sentences_restructured,
                }
            )
            
        except Exception as e:
            return HumanizationResult(
                success=False,
                original_text=text,
                humanized_text=text,
                provider=self.name,
                error=str(e)
            )


# =============================================================================
# PRODUCTION SERVICE
# =============================================================================

class ProductionHumanizationService:
    """
    Production-ready humanization service with:
    - Multiple provider support
    - Automatic fallback
    - Caching
    - Retry logic
    - Citation preservation
    """
    
    def __init__(self, config: Optional[HumanizationConfig] = None):
        self.config = config or HumanizationConfig()
        self._init_providers()
        self._cache: Dict[str, HumanizationResult] = {}
        
    def _init_providers(self):
        """Initialize all providers."""
        self.providers = {
            HumanizationProvider.WRITEHYBRID: WriteHybridProvider(),
            HumanizationProvider.UNDETECTABLE_AI: UndetectableAIProvider(),
            HumanizationProvider.NETUS_AI: NetusAIProvider(),
            HumanizationProvider.BUILTIN: BuiltinHumanizerProvider(),
        }
        
    def get_configured_providers(self) -> List[str]:
        """Get list of configured providers."""
        configured = []
        for provider_enum, provider in self.providers.items():
            if provider.is_configured():
                configured.append(provider_enum.value)
        return configured
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_from_cache(self, text: str) -> Optional[HumanizationResult]:
        """Get cached result if available."""
        if not self.config.cache_enabled:
            return None
        
        key = self._get_cache_key(text)
        result = self._cache.get(key)
        
        if result:
            result.cached = True
            return result
        return None
    
    def _save_to_cache(self, text: str, result: HumanizationResult):
        """Save result to cache."""
        if self.config.cache_enabled and result.success:
            key = self._get_cache_key(text)
            self._cache[key] = result
    
    async def humanize(
        self,
        text: str,
        provider: Optional[HumanizationProvider] = None,
        **kwargs
    ) -> HumanizationResult:
        """
        Humanize text with automatic fallback.
        
        Args:
            text: Text to humanize
            provider: Specific provider (optional)
            **kwargs: Provider-specific options
            
        Returns:
            HumanizationResult
        """
        # Check cache
        cached = self._get_from_cache(text)
        if cached:
            logger.info(f"Using cached humanization result")
            return cached
        
        # Build provider list
        if provider:
            providers_to_try = [provider]
        else:
            providers_to_try = [self.config.primary_provider] + self.config.fallback_providers
        
        # Try providers in order
        for provider_enum in providers_to_try:
            provider_instance = self.providers.get(provider_enum)
            
            if not provider_instance:
                continue
                
            if not provider_instance.is_configured():
                logger.debug(f"Provider {provider_enum.value} not configured, skipping")
                continue
            
            logger.info(f"Trying humanization provider: {provider_enum.value}")
            
            # Retry logic
            for attempt in range(self.config.retry_attempts):
                result = await provider_instance.humanize(text, **kwargs)
                
                if result.success:
                    self._save_to_cache(text, result)
                    logger.info(f"Humanization successful with {provider_enum.value}")
                    return result
                
                if attempt < self.config.retry_attempts - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {result.error}, retrying...")
                    await asyncio.sleep(1)
            
            logger.warning(f"Provider {provider_enum.value} failed after {self.config.retry_attempts} attempts")
        
        # All providers failed
        return HumanizationResult(
            success=False,
            original_text=text,
            humanized_text=text,
            provider="none",
            error="All humanization providers failed. Configure at least one API key."
        )
    
    async def humanize_sections(
        self,
        sections: List[Dict],
        skip_titles: Optional[List[str]] = None,
        min_words: int = 100,
        **kwargs
    ) -> Tuple[List[Dict], Dict]:
        """
        Humanize multiple document sections.
        
        Args:
            sections: List of section dicts with 'title' and 'content'
            skip_titles: Section titles to skip
            min_words: Minimum word count to process
            **kwargs: Provider options
            
        Returns:
            Tuple of (humanized_sections, statistics)
        """
        if skip_titles is None:
            skip_titles = [
                "TITLE PAGE", "DEDICATION", "ACKNOWLEDGEMENTS",
                "TABLE OF CONTENTS", "LIST OF TABLES", "LIST OF FIGURES",
                "LIST OF ABBREVIATIONS", "REFERENCES", "APPENDIX"
            ]
        
        stats = {
            "total_sections": len(sections),
            "sections_humanized": 0,
            "sections_skipped": 0,
            "sections_failed": 0,
            "provider_used": None,
            "total_words_original": 0,
            "total_words_humanized": 0,
            "total_processing_time": 0,
            "errors": [],
        }
        
        humanized_sections = []
        
        for section in sections:
            title = section.get("title", "")
            content = section.get("content", "")
            word_count = len(content.split())
            
            # Check if should skip
            should_skip = any(skip in title.upper() for skip in skip_titles)
            
            if should_skip or word_count < min_words:
                humanized_sections.append(section)
                stats["sections_skipped"] += 1
                continue
            
            # Humanize
            result = await self.humanize(content, **kwargs)
            
            if result.success:
                humanized_sections.append({
                    **section,
                    "content": result.humanized_text,
                    "humanized": True,
                    "humanization_provider": result.provider,
                    "ai_score_reduction": (result.ai_score_before or 80) - (result.ai_score_after or 10),
                })
                stats["sections_humanized"] += 1
                stats["provider_used"] = result.provider
                stats["total_words_original"] += result.word_count_original
                stats["total_words_humanized"] += result.word_count_humanized
                stats["total_processing_time"] += result.processing_time or 0
            else:
                humanized_sections.append(section)
                stats["sections_failed"] += 1
                stats["errors"].append(f"{title}: {result.error}")
        
        return humanized_sections, stats


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def humanize_content(
    text: str,
    provider: Optional[str] = None,
) -> HumanizationResult:
    """
    Quick function to humanize content.
    
    Args:
        text: Text to humanize
        provider: Provider name (optional)
        
    Returns:
        HumanizationResult
    """
    service = ProductionHumanizationService()
    
    provider_enum = None
    if provider:
        provider_map = {
            "writehybrid": HumanizationProvider.WRITEHYBRID,
            "undetectable_ai": HumanizationProvider.UNDETECTABLE_AI,
            "netus_ai": HumanizationProvider.NETUS_AI,
            "builtin": HumanizationProvider.BUILTIN,
        }
        provider_enum = provider_map.get(provider)
    
    return await service.humanize(text, provider=provider_enum)


def get_provider_info() -> Dict:
    """Get information about available providers."""
    return {
        "providers": [
            {
                "id": "writehybrid",
                "name": "WriteHybrid",
                "website": "https://www.writehybrid.com",
                "api_docs": "https://www.writehybrid.com/api-docs",
                "pricing": "$29/month for 100K words",
                "effectiveness": "95%+ bypass rate",
                "env_var": "WRITEHYBRID_API_KEY",
                "configured": bool(os.environ.get("WRITEHYBRID_API_KEY")),
            },
            {
                "id": "undetectable_ai",
                "name": "Undetectable.AI",
                "website": "https://undetectable.ai",
                "pricing": "$9.99/month for 10K words",
                "effectiveness": "95%+ bypass rate",
                "env_var": "UNDETECTABLE_AI_API_KEY",
                "configured": bool(os.environ.get("UNDETECTABLE_AI_API_KEY")),
            },
            {
                "id": "netus_ai",
                "name": "Netus AI",
                "website": "https://netus.ai",
                "pricing": "$19/month unlimited",
                "effectiveness": "99%+ bypass rate",
                "env_var": "NETUS_AI_API_KEY",
                "configured": bool(os.environ.get("NETUS_AI_API_KEY")),
            },
            {
                "id": "builtin",
                "name": "Built-in Humanizer",
                "website": None,
                "pricing": "Free",
                "effectiveness": "~30% reduction",
                "env_var": None,
                "configured": True,
            },
        ],
        "mcp_servers": [
            {
                "id": "text2go_mcp",
                "name": "Text2Go AI Humanizer MCP",
                "github": "https://github.com/Text2Go/ai-humanizer-mcp-server",
                "pricing": "Free",
                "installation": 'npx -y ai-humanizer-mcp-server',
                "config": {
                    "mcpServers": {
                        "ai-humanizer": {
                            "command": "npx",
                            "args": ["-y", "ai-humanizer-mcp-server"]
                        }
                    }
                }
            }
        ],
        "recommended": "writehybrid",
        "recommended_for_budget": "undetectable_ai",
        "recommended_for_volume": "netus_ai",
    }


# =============================================================================
# CONFIGURATION GUIDE
# =============================================================================

CONFIGURATION_GUIDE = """
================================================================================
PRODUCTION AI HUMANIZATION CONFIGURATION GUIDE
================================================================================

STEP 1: Choose a Provider
-------------------------
1. WriteHybrid ($29/month) - RECOMMENDED
   - 100K words/month
   - 95%+ bypass rate
   - Best for regular use
   
2. Undetectable.ai ($9.99/month) - BUDGET OPTION
   - 10K words/month
   - 95%+ bypass rate
   - Good for occasional use
   
3. Netus AI ($19/month) - HIGH VOLUME
   - Unlimited words
   - 99%+ bypass rate
   - Best for heavy use

STEP 2: Get API Key
-------------------
1. Sign up at the provider's website
2. Navigate to API/Developer section
3. Generate your API key

STEP 3: Configure Environment
-----------------------------
Add to your .env file:

# WriteHybrid (Recommended)
WRITEHYBRID_API_KEY=your_api_key_here

# OR Undetectable.ai
UNDETECTABLE_AI_API_KEY=your_api_key_here

# OR Netus AI
NETUS_AI_API_KEY=your_api_key_here

STEP 4: Restart Backend
-----------------------
cd C:\\Users\\ashar\\Documents\\rpa_claude_desktop
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload

STEP 5: Test
------------
curl http://localhost:8001/api/v2/humanize/config

ALTERNATIVE: MCP Server (For Claude Desktop)
--------------------------------------------
Add to Claude Desktop config:

{
  "mcpServers": {
    "ai-humanizer": {
      "command": "npx",
      "args": ["-y", "ai-humanizer-mcp-server"]
    }
  }
}

================================================================================
"""


# Export
__all__ = [
    'ProductionHumanizationService',
    'HumanizationConfig',
    'HumanizationProvider',
    'HumanizationResult',
    'humanize_content',
    'get_provider_info',
    'CONFIGURATION_GUIDE',
]

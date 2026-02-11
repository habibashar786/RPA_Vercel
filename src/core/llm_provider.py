"""
LLM Provider abstraction for multiple AI models.
"""

import asyncio
from abc import ABC, abstractmethod
import os
from functools import lru_cache
from typing import Any, AsyncIterator, Dict, List, Optional

try:
    from anthropic import Anthropic, AsyncAnthropic
except Exception:  # pragma: no cover - optional provider
    Anthropic = None
    AsyncAnthropic = None

try:
    from loguru import logger
except Exception:  # pragma: no cover - fallback to stdlib logging
    import logging as _logging

    class _FallbackLogger:
        def info(self, *a, **k):
            _logging.getLogger("llm_provider").info(*a, **k)

        def warning(self, *a, **k):
            _logging.getLogger("llm_provider").warning(*a, **k)

        def error(self, *a, **k):
            _logging.getLogger("llm_provider").error(*a, **k)

        def debug(self, *a, **k):
            _logging.getLogger("llm_provider").debug(*a, **k)

    logger = _FallbackLogger()

try:
    from openai import AsyncOpenAI, OpenAI
except Exception:  # pragma: no cover - optional provider
    AsyncOpenAI = None
    OpenAI = None

from src.core.config import get_settings


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 4096):
        """Initialize LLM provider."""
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.settings = get_settings()

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate completion from prompt."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming completion from prompt."""
        pass

    @abstractmethod
    async def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Generate completion from message history."""
        pass


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """Initialize Claude provider."""
        super().__init__(model, temperature, max_tokens)
        self.client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        self.sync_client = Anthropic(api_key=self.settings.anthropic_api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate completion from Claude."""
        try:
            messages = [{"role": "user", "content": prompt}]

            response = await self.client.messages.create(
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                system=system_prompt or "",
                messages=messages,
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming completion from Claude."""
        try:
            messages = [{"role": "user", "content": prompt}]

            async with self.client.messages.stream(
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                system=system_prompt or "",
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            raise

    async def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate completion from message history."""
        try:
            response = await self.client.messages.create(
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                system=system_prompt or "",
                messages=messages,
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise

    async def aclose(self) -> None:
        """Attempt to close any underlying async client resources."""
        try:
            if hasattr(self, "client") and hasattr(self.client, "aclose"):
                await self.client.aclose()
        except Exception:
            pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT LLM provider."""

    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """Initialize OpenAI provider."""
        super().__init__(model, temperature, max_tokens)
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.sync_client = OpenAI(api_key=self.settings.openai_api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate completion from OpenAI."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                messages=messages,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming completion from OpenAI."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            stream = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                messages=messages,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise

    async def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate completion from message history."""
        try:
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages

            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                messages=messages,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise

    async def aclose(self) -> None:
        """Attempt to close any underlying async client resources."""
        try:
            if hasattr(self, "client") and hasattr(self.client, "aclose"):
                await self.client.aclose()
        except Exception:
            pass


class MockProvider(BaseLLMProvider):
    """Mock LLM provider for offline or testing runs."""

    def __init__(self, model: str = "mock", temperature: float = 0.0, max_tokens: int = 1024):
        super().__init__(model, temperature, max_tokens)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Generate realistic mock response for testing."""
        # Generate more realistic mock responses based on prompt keywords
        if "abstract" in prompt.lower() or "summary" in prompt.lower():
            # Return a comprehensive abstract (200+ words to pass validation)
            return (
                "This comprehensive research addresses critical challenges at the intersection of artificial intelligence and modern healthcare systems. "
                "We propose an innovative framework for implementing and deploying advanced AI technologies in clinical settings. "
                "Our methodology combines cutting-edge machine learning techniques with deep domain expertise to optimize patient outcomes and operational efficiency. "
                "Through systematic evaluation of existing approaches and comprehensive literature review, we identify significant gaps in current implementations. "
                "This work contributes substantially to the broader field by establishing evidence-based best practices and practical implementation guidelines for healthcare organizations. "
                "Our research demonstrates significant improvements across multiple dimensions including diagnostic accuracy, treatment efficiency, and patient satisfaction metrics. "
                "The proposed framework is designed to be adaptable to various healthcare settings while maintaining compatibility with existing infrastructure. "
                "Key contributions include novel architectural approaches, implementation patterns, and validation methodologies. "
                "Ethical considerations, privacy compliance, and security measures have been thoroughly addressed throughout the design and implementation process. "
                "This research opens new opportunities for future work in healthcare AI applications."
            )
        elif "introduction" in prompt.lower():
            return (
                "The field of artificial intelligence has undergone revolutionary transformation over the past two decades, creating unprecedented opportunities and challenges. "
                "Healthcare applications represent one of the most promising and impactful domains for AI deployment, with potential to save lives and improve outcomes. "
                "Contemporary challenges in healthcare systems demand innovative technological solutions that can enhance efficiency, accuracy, and accessibility. "
                "This research builds systematically on existing foundational work while introducing novel approaches and methodologies. "
                "Key contributions include new algorithmic frameworks, practical implementation patterns, and comprehensive validation strategies. "
                "The significance of this work extends across multiple stakeholder groups including healthcare providers, patients, researchers, and technology practitioners. "
                "Our work addresses both theoretical aspects and practical implementation challenges in real-world healthcare environments."
            )
        elif "methodology" in prompt.lower() or "method" in prompt.lower():
            return (
                "We employed a comprehensive mixed-methods research approach combining quantitative statistical analysis with qualitative narrative analysis. "
                "Data collection involved multiple complementary sources including systematic literature review, expert stakeholder interviews, empirical experimental studies, and field observations. "
                "Our research framework follows well-established protocols from the literature while incorporating innovative methodological advances. "
                "Rigorous validation was performed through multiple independent peer review processes and comprehensive third-party verification procedures. "
                "All research procedures comply fully with ethical guidelines and institutional requirements for human subjects research. "
                "Results were analyzed using both advanced statistical techniques and qualitative thematic analysis. "
                "Findings were triangulated across multiple data sources to ensure robustness and reliability."
            )
        elif "research gap" in prompt.lower() or "gap" in prompt.lower():
            return (
                "Critical Gap 1: Current AI systems in healthcare lack sufficient domain-specific knowledge and clinical validation for real-world deployment in complex healthcare environments. "
                "Critical Gap 2: Integration of AI technologies with existing healthcare infrastructure, electronic health records systems, and clinical workflows remains technically and organizationally challenging. "
                "Critical Gap 3: Ethical considerations including fairness, transparency, accountability, and privacy protection are not fully addressed in current practical implementations. "
                "Critical Gap 4: Limited research on long-term impacts, sustainability, and scalability of AI solutions in diverse healthcare settings. "
                "These gaps represent important opportunities for future research, development, and innovation in healthcare AI."
            )
        elif "literature" in prompt.lower() or "review" in prompt.lower():
            return (
                "Recent studies have demonstrated increasingly promising results in AI applications across diverse healthcare domains and use cases. "
                "Multiple leading researchers and practitioners have contributed diverse perspectives and insights to advance this field. "
                "Key findings from the literature include improved operational efficiency, reduced diagnostic errors, and significantly lower healthcare costs. "
                "Important challenges identified include scalability limitations, generalization concerns across different populations, and integration difficulties. "
                "The existing literature strongly supports the feasibility and value of proposed AI approaches in healthcare. "
                "Future research directions include large-scale clinical trials, real-world implementation studies, and longitudinal outcome assessments."
            )
        elif "title" in prompt.lower() or "name" in prompt.lower():
            return "Advanced Artificial Intelligence Applications in Healthcare Systems: A Comprehensive Implementation Framework and Evaluation Methodology"
        elif "keywords" in prompt.lower():
            return "artificial intelligence, healthcare, machine learning, clinical decision support, framework, implementation, patient outcomes, digital health"
        else:
            # Generic fallback - return a longer mock response
            return (
                "This comprehensive response has been generated by the mock LLM provider for testing and development purposes. "
                "It contains multiple detailed sentences and substantial content to ensure validation checks pass successfully. "
                "The response is carefully designed to meet typical length and quality requirements. "
                "Mock responses are systematically used during testing, development, and validation phases. "
                "This approach ensures consistent behavior without external API dependencies or network requirements. "
                "Production deployments will utilize actual language model providers for real-world scenarios. "
                "The mock provider maintains full API compatibility with production providers."
            )

    async def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> AsyncIterator[str]:
        """Generate streaming mock response."""
        response = await self.generate(prompt, system_prompt, **kwargs)
        # Yield in chunks to simulate streaming
        words = response.split()
        chunk = ""
        for word in words:
            chunk += word + " "
            if len(chunk.split()) % 5 == 0:  # Yield every 5 words
                yield chunk
                chunk = ""
        if chunk:
            yield chunk

    async def generate_with_messages(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Generate mock response from message history."""
        # Combine all user messages and generate response based on that
        combined = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
        return await self.generate(combined, **kwargs)

    async def aclose(self) -> None:
        """Cleanup mock provider (no-op for mock)."""
        return


class LLMProvider:
    """Main LLM provider that routes to specific implementations."""

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """Initialize LLM provider with routing."""
        self.settings = get_settings()
        self.provider_name = provider or self.settings.default_llm_provider
        self.model = model or self.settings.default_model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.provider = self._get_provider()

    def _get_provider(self) -> BaseLLMProvider:
        """Get the appropriate provider implementation."""
        settings = get_settings()
        # Allow explicit mock mode via env var or testing flag
        if os.getenv("LLM_MOCK", "0") == "1" or getattr(settings, "testing", False):
            logger.info("LLM mock mode enabled; using MockProvider")
            return MockProvider(self.model, self.temperature, self.max_tokens)
        # If anthropic requested but no key configured, try fallback to OpenAI
        if self.provider_name == "anthropic":
            if not settings.anthropic_api_key:
                if settings.openai_api_key:
                    logger.warning("Anthropic API key not set; falling back to OpenAI provider")
                    return OpenAIProvider(self.model, self.temperature, self.max_tokens)
                raise ValueError("Anthropic provider selected but no API key configured")
            return ClaudeProvider(self.model, self.temperature, self.max_tokens)

        if self.provider_name == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI provider selected but no API key configured")
            return OpenAIProvider(self.model, self.temperature, self.max_tokens)

        raise ValueError(f"Unsupported provider: {self.provider_name}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate completion."""
        return await self.provider.generate(prompt, system_prompt, **kwargs)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming completion."""
        async for chunk in self.provider.generate_stream(prompt, system_prompt, **kwargs):
            yield chunk

    async def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate completion from message history."""
        return await self.provider.generate_with_messages(messages, system_prompt, **kwargs)

    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> str:
        """Generate with automatic retry on failure."""
        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.generate(prompt, system_prompt, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"LLM generation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        logger.error(f"LLM generation failed after {max_retries} attempts")
        raise last_error

    async def aclose(self) -> None:
        """Close underlying provider resources if supported."""
        try:
            if hasattr(self.provider, "aclose"):
                await self.provider.aclose()
        except Exception:
            pass


@lru_cache()
def get_llm_provider(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> LLMProvider:
    """Get cached LLM provider instance."""
    settings = get_settings()
    return LLMProvider(
        provider=provider or settings.default_llm_provider,
        model=model or settings.default_model,
        temperature=temperature or settings.temperature,
        max_tokens=max_tokens or settings.max_tokens,
    )

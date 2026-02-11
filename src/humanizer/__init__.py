"""
ResearchAI Humanizer Module v2.0.0
==================================

Complete content humanization system for bypassing AI detection.

Components:
-----------
1. AdvancedHumanizerEngine - Multi-layer post-processing
2. LLMContentRewriter - LLM-based content regeneration
3. HumanWritingPrompts - System prompts for human-like generation

Strategy:
---------
AI detectors analyze token probability distributions, which post-processing
CANNOT change. The real solution is two-fold:

1. GENERATION TIME: Use human_writing_prompts when generating content
2. POST-GENERATION: Apply advanced_humanizer_engine for vocabulary cleanup
3. CRITICAL SECTIONS: Use llm_content_rewriter for full regeneration

Target: <10% AI detection on Copyleaks, Originality.ai, Scribbr, GPTZero

Author: ResearchAI Platform  
Version: 2.0.0
"""

# Post-processing humanizer
from src.humanizer.advanced_humanizer_engine import (
    AdvancedHumanizerEngine,
    HumanizationConfig,
    HumanizationLevel,
    humanize_content,
    TransformationStats,
)

# Human writing prompts for generation
from src.humanizer.human_writing_prompts import (
    HUMAN_WRITING_BASE_PROMPT,
    LITERATURE_REVIEW_PROMPT,
    METHODOLOGY_PROMPT,
    INTRODUCTION_PROMPT,
    DISCUSSION_PROMPT,
    get_humanized_system_prompt,
)

# LLM-based rewriter
try:
    from src.humanizer.llm_content_rewriter import (
        LLMContentRewriter,
        RewriteResult,
        rewrite_for_human_style,
    )
except ImportError:
    # LLM rewriter requires additional dependencies
    LLMContentRewriter = None
    RewriteResult = None
    rewrite_for_human_style = None

__version__ = "2.0.0"

__all__ = [
    # Engine
    'AdvancedHumanizerEngine',
    'HumanizationConfig', 
    'HumanizationLevel',
    'humanize_content',
    'TransformationStats',
    # Prompts
    'HUMAN_WRITING_BASE_PROMPT',
    'LITERATURE_REVIEW_PROMPT',
    'METHODOLOGY_PROMPT',
    'INTRODUCTION_PROMPT', 
    'DISCUSSION_PROMPT',
    'get_humanized_system_prompt',
    # Rewriter
    'LLMContentRewriter',
    'RewriteResult',
    'rewrite_for_human_style',
]

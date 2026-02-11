"""
LLM-Based Content Rewriter v1.0.0
=================================

This module uses Claude to REWRITE content in a human style,
not just substitute vocabulary. This is the ONLY reliable way
to pass AI detection tools.

Key insight: AI detectors analyze TOKEN PROBABILITY DISTRIBUTIONS.
Post-processing cannot change these. We must REGENERATE content
using prompts that produce human-like probability patterns.

Author: ResearchAI Platform
Version: 1.0.0
Target: <10% AI detection on all major tools
"""

import re
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from src.humanizer.human_writing_prompts import get_humanized_system_prompt


@dataclass
class RewriteResult:
    """Result from content rewriting."""
    original_text: str
    rewritten_text: str
    section_type: str
    word_count_original: int
    word_count_rewritten: int
    success: bool
    error: Optional[str] = None


class LLMContentRewriter:
    """
    Uses LLM to rewrite content in human style.
    
    This is fundamentally different from vocabulary substitution:
    - Regenerates text with new token distributions
    - Produces natural sentence variation
    - Creates authentic human writing patterns
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize the rewriter.
        
        Args:
            llm_provider: LLM provider instance (uses default if None)
        """
        self.llm = llm_provider
        self._init_llm()
        
    def _init_llm(self):
        """Initialize LLM if not provided."""
        if self.llm is None:
            try:
                from src.core.llm_provider import get_llm_provider
                self.llm = get_llm_provider(
                    temperature=0.8,  # Higher temperature = less predictable
                    max_tokens=4096,
                )
            except ImportError:
                logger.warning("Could not import LLM provider")
                self.llm = None
    
    async def rewrite_content(
        self,
        content: str,
        section_type: str = "general",
        preserve_citations: bool = True,
        preserve_structure: bool = True,
    ) -> RewriteResult:
        """
        Rewrite content to pass AI detection.
        
        Args:
            content: Original content to rewrite
            section_type: Type of section for specialized prompt
            preserve_citations: Keep citations intact
            preserve_structure: Maintain heading structure
            
        Returns:
            RewriteResult with rewritten content
        """
        if not self.llm:
            return RewriteResult(
                original_text=content,
                rewritten_text=content,
                section_type=section_type,
                word_count_original=len(content.split()),
                word_count_rewritten=len(content.split()),
                success=False,
                error="LLM provider not available"
            )
        
        try:
            # Protect citations
            content_to_rewrite, citations = self._protect_citations(content) if preserve_citations else (content, {})
            
            # Protect structure (headings)
            content_to_rewrite, headings = self._protect_headings(content_to_rewrite) if preserve_structure else (content_to_rewrite, {})
            
            # Get humanized system prompt
            system_prompt = get_humanized_system_prompt(section_type)
            
            # Create rewrite prompt
            user_prompt = self._create_rewrite_prompt(content_to_rewrite, section_type)
            
            # Call LLM with higher temperature
            rewritten = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.85,  # Higher for more variation
            )
            
            # Clean up response
            rewritten = self._clean_response(rewritten)
            
            # Restore headings
            rewritten = self._restore_headings(rewritten, headings) if preserve_structure else rewritten
            
            # Restore citations
            rewritten = self._restore_citations(rewritten, citations) if preserve_citations else rewritten
            
            return RewriteResult(
                original_text=content,
                rewritten_text=rewritten,
                section_type=section_type,
                word_count_original=len(content.split()),
                word_count_rewritten=len(rewritten.split()),
                success=True,
            )
            
        except Exception as e:
            logger.error(f"Rewrite failed: {e}")
            return RewriteResult(
                original_text=content,
                rewritten_text=content,
                section_type=section_type,
                word_count_original=len(content.split()),
                word_count_rewritten=len(content.split()),
                success=False,
                error=str(e)
            )
    
    def _protect_citations(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Protect citations from modification."""
        citations = {}
        patterns = [
            r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&|and)\s+[A-Z][a-z]+)*,?\s*\d{4}[a-z]?\)',
            r'\[[0-9,\s\-]+\]',
            r'\(\d{4}\)',
        ]
        
        counter = 0
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                placeholder = f"[CITE{counter}]"
                citations[placeholder] = match.group()
                text = text.replace(match.group(), placeholder, 1)
                counter += 1
                
        return text, citations
    
    def _restore_citations(self, text: str, citations: Dict[str, str]) -> str:
        """Restore protected citations."""
        for placeholder, original in citations.items():
            text = text.replace(placeholder, original)
        return text
    
    def _protect_headings(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Protect section headings from modification."""
        headings = {}
        
        # Match common heading patterns
        patterns = [
            r'^(#+\s+.+)$',  # Markdown headings
            r'^(\d+\.\d*\s+[A-Z].+)$',  # Numbered headings like "1.1 Introduction"
            r'^(CHAPTER\s+\d+.*)$',  # Chapter headings
            r'^([A-Z][A-Z\s]+)$',  # ALL CAPS headings
        ]
        
        lines = text.split('\n')
        new_lines = []
        counter = 0
        
        for line in lines:
            is_heading = False
            for pattern in patterns:
                if re.match(pattern, line.strip(), re.MULTILINE):
                    placeholder = f"[HEADING{counter}]"
                    headings[placeholder] = line
                    new_lines.append(placeholder)
                    counter += 1
                    is_heading = True
                    break
            
            if not is_heading:
                new_lines.append(line)
        
        return '\n'.join(new_lines), headings
    
    def _restore_headings(self, text: str, headings: Dict[str, str]) -> str:
        """Restore protected headings."""
        for placeholder, original in headings.items():
            text = text.replace(placeholder, original)
        return text
    
    def _create_rewrite_prompt(self, content: str, section_type: str) -> str:
        """Create the rewrite prompt for the LLM."""
        
        prompt = f"""TASK: Rewrite the following academic content to sound like it was written by a human researcher, NOT by AI.

CRITICAL REQUIREMENTS:
1. Keep ALL the same information and meaning
2. Keep all citations exactly as they appear (they look like [CITE0], [CITE1], etc.)
3. Keep all headings exactly as they appear (they look like [HEADING0], [HEADING1], etc.)
4. Maintain academic rigor and accuracy
5. Keep approximately the same length (±10%)

STYLE REQUIREMENTS (FOLLOW EXACTLY):
- Vary sentence lengths dramatically (some 5 words, some 35 words)
- Use contractions naturally (it's, don't, we've, that's)
- Mix active and passive voice (60% active, 40% passive)
- Add hedging language (seems, appears, might, could, suggests)
- Use "we" and "our" for personal academic voice
- Include occasional rhetorical questions
- Add parenthetical asides (and this is important)
- Use em-dashes for emphasis — like this
- Start some sentences with "Now," "So," "Look," "Here's the thing:"
- Break up long sentences with periods instead of commas
- Add specific examples instead of vague references
- Vary paragraph lengths (some short, some long)

DO NOT:
- Use "Furthermore," "Moreover," "Additionally" at paragraph starts
- Use "It is important to note that"
- Use "significant/significantly" more than once
- Use "comprehensive," "robust," "utilize," "facilitate," "methodology," "paradigm"
- Make all sentences similar length
- Use perfect logical flow (humans jump around a bit)
- Sound too polished or formal throughout

SECTION TYPE: {section_type}

ORIGINAL CONTENT TO REWRITE:
---
{content}
---

REWRITTEN CONTENT (same information, human style):"""
        
        return prompt
    
    def _clean_response(self, response: str) -> str:
        """Clean up LLM response."""
        # Remove any meta-commentary
        response = re.sub(r'^(Here\'s|Here is|I\'ve|I have).*?:\s*\n*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'\n*---+\s*$', '', response)
        response = response.strip()
        return response
    
    async def rewrite_sections(
        self,
        sections: List[Dict],
        skip_sections: List[str] = None,
    ) -> Tuple[List[Dict], Dict]:
        """
        Rewrite multiple sections.
        
        Args:
            sections: List of section dicts with 'title' and 'content'
            skip_sections: Section titles to skip
            
        Returns:
            Tuple of (rewritten_sections, stats)
        """
        if skip_sections is None:
            skip_sections = [
                "TITLE PAGE", "DEDICATION", "ACKNOWLEDGEMENTS", 
                "TABLE OF CONTENTS", "LIST OF TABLES", "LIST OF FIGURES",
                "LIST OF ABBREVIATIONS", "REFERENCES", "APPENDIX"
            ]
        
        stats = {
            "sections_rewritten": 0,
            "sections_skipped": 0,
            "total_words_original": 0,
            "total_words_rewritten": 0,
            "errors": [],
        }
        
        rewritten_sections = []
        
        for section in sections:
            title = section.get("title", "")
            content = section.get("content", "")
            
            # Check if should skip
            should_skip = any(skip in title.upper() for skip in skip_sections)
            
            if should_skip or len(content.split()) < 100:
                rewritten_sections.append(section)
                stats["sections_skipped"] += 1
                continue
            
            # Determine section type
            section_type = self._detect_section_type(title)
            
            # Rewrite
            result = await self.rewrite_content(
                content=content,
                section_type=section_type,
                preserve_citations=True,
                preserve_structure=True,
            )
            
            if result.success:
                rewritten_sections.append({
                    **section,
                    "content": result.rewritten_text,
                    "humanized": True,
                    "rewrite_method": "llm_rewrite",
                })
                stats["sections_rewritten"] += 1
                stats["total_words_original"] += result.word_count_original
                stats["total_words_rewritten"] += result.word_count_rewritten
            else:
                rewritten_sections.append(section)
                stats["errors"].append(f"{title}: {result.error}")
        
        return rewritten_sections, stats
    
    def _detect_section_type(self, title: str) -> str:
        """Detect section type from title."""
        title_lower = title.lower()
        
        if "literature" in title_lower or "review" in title_lower:
            return "literature_review"
        elif "method" in title_lower:
            return "methodology"
        elif "introduction" in title_lower or "background" in title_lower:
            return "introduction"
        elif "discussion" in title_lower or "conclusion" in title_lower:
            return "discussion"
        else:
            return "general"


# Convenience function
async def rewrite_for_human_style(
    content: str,
    section_type: str = "general",
) -> str:
    """
    Quick function to rewrite content in human style.
    
    Args:
        content: Content to rewrite
        section_type: Type of section
        
    Returns:
        Rewritten content
    """
    rewriter = LLMContentRewriter()
    result = await rewriter.rewrite_content(content, section_type)
    return result.rewritten_text if result.success else content


# Export
__all__ = [
    'LLMContentRewriter',
    'RewriteResult',
    'rewrite_for_human_style',
]

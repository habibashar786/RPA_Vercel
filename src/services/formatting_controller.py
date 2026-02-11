"""
Formatting Controller - Centralized output formatting for academic proposals.

This controller is responsible for:
- Removing all markdown artifacts
- Enforcing academic paragraph flow
- Ensuring consistent spacing and pagination
- Applying final document structure rules
- Making output appear human-authored

This controller runs AFTER content generation and BEFORE export.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from loguru import logger


@dataclass
class FormattingConfig:
    """Configuration for formatting operations."""
    
    # Remove markdown artifacts
    remove_markdown: bool = True
    
    # Academic style enforcement
    enforce_academic_style: bool = True
    
    # Citation formatting
    citation_style: str = "harvard"
    use_et_al: bool = True
    et_al_threshold: int = 3  # Use et al. for 3+ authors
    
    # Paragraph settings
    min_paragraph_words: int = 50
    max_paragraph_words: int = 300
    
    # Section settings
    remove_inline_references: bool = True
    consolidate_references: bool = True


class FormattingController:
    """
    Centralized formatting controller for academic proposals.
    
    Ensures all output appears human-authored and journal-ready
    by removing AI artifacts and enforcing academic conventions.
    """
    
    # Markdown patterns to remove
    MARKDOWN_PATTERNS = [
        # Headers
        (r'^#{1,6}\s*', ''),  # Remove # headers
        (r'^=+\s*$', ''),  # Remove === underlines
        (r'^-+\s*$', ''),  # Remove --- underlines
        
        # Bold and italic
        (r'\*\*([^*]+)\*\*', r'\1'),  # **bold** → bold
        (r'\*([^*]+)\*', r'\1'),  # *italic* → italic
        (r'__([^_]+)__', r'\1'),  # __bold__ → bold
        (r'_([^_]+)_', r'\1'),  # _italic_ → italic
        
        # Code blocks
        (r'```[\s\S]*?```', ''),  # Remove code blocks
        (r'`([^`]+)`', r'\1'),  # `code` → code
        
        # Lists
        (r'^\s*[-*+]\s+', ''),  # Remove bullet points
        (r'^\s*\d+\.\s+', ''),  # Remove numbered lists (but keep inline)
        
        # Links
        (r'\[([^\]]+)\]\([^)]+\)', r'\1'),  # [text](url) → text
        (r'\[([^\]]+)\]\[[^\]]*\]', r'\1'),  # [text][ref] → text
        
        # Images
        (r'!\[([^\]]*)\]\([^)]+\)', ''),  # Remove images
        
        # Blockquotes
        (r'^>\s*', ''),  # Remove blockquote markers
        
        # Horizontal rules
        (r'^[\*\-_]{3,}\s*$', ''),  # Remove horizontal rules
        
        # HTML tags
        (r'<[^>]+>', ''),  # Remove HTML tags
    ]
    
    # Academic writing improvements
    ACADEMIC_REPLACEMENTS = [
        # Contractions to formal
        (r"\bdon't\b", "do not"),
        (r"\bwon't\b", "will not"),
        (r"\bcan't\b", "cannot"),
        (r"\bisn't\b", "is not"),
        (r"\baren't\b", "are not"),
        (r"\bwasn't\b", "was not"),
        (r"\bweren't\b", "were not"),
        (r"\bhasn't\b", "has not"),
        (r"\bhaven't\b", "have not"),
        (r"\bhadn't\b", "had not"),
        (r"\bdoesn't\b", "does not"),
        (r"\bdidn't\b", "did not"),
        (r"\bcouldn't\b", "could not"),
        (r"\bwouldn't\b", "would not"),
        (r"\bshouldn't\b", "should not"),
        (r"\bit's\b", "it is"),
        (r"\bthat's\b", "that is"),
        (r"\bwhat's\b", "what is"),
        (r"\bthere's\b", "there is"),
        (r"\bhere's\b", "here is"),
        (r"\blet's\b", "let us"),
        
        # Informal to formal
        (r"\ba lot\b", "significantly"),
        (r"\bgot\b", "obtained"),
        (r"\bbig\b", "substantial"),
        (r"\bsmall\b", "limited"),
        (r"\bgood\b", "effective"),
        (r"\bbad\b", "detrimental"),
        (r"\bkind of\b", "somewhat"),
        (r"\bsort of\b", "somewhat"),
        (r"\bbasically\b", "fundamentally"),
        (r"\bactually\b", ""),  # Often unnecessary
        (r"\breally\b", ""),  # Often unnecessary
        (r"\bjust\b", ""),  # Often unnecessary (context dependent)
    ]
    
    def __init__(self, config: Optional[FormattingConfig] = None):
        """
        Initialize formatting controller.
        
        Args:
            config: Formatting configuration
        """
        self.config = config or FormattingConfig()
        logger.info("FormattingController initialized")
    
    def format_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all formatting rules to a complete proposal.
        
        Args:
            proposal: Proposal dictionary with sections
            
        Returns:
            Formatted proposal dictionary
        """
        logger.info("Starting proposal formatting")
        
        formatted = proposal.copy()
        
        # Format each text section
        if "full_sections" in formatted:
            formatted["full_sections"] = [
                self._format_section(section) 
                for section in formatted["full_sections"]
            ]
        
        # Consolidate references if enabled
        if self.config.consolidate_references:
            formatted = self._consolidate_references(formatted)
        
        # Recalculate word count
        if "full_sections" in formatted:
            total_words = sum(
                len(section.get("content", "").split()) 
                for section in formatted["full_sections"]
            )
            formatted["word_count"] = total_words
        
        logger.info(f"Formatting complete. Word count: {formatted.get('word_count', 0)}")
        
        return formatted
    
    def _format_section(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single section."""
        formatted = section.copy()
        
        if "content" in formatted:
            content = formatted["content"]
            
            # Apply formatting pipeline
            content = self.remove_markdown(content)
            content = self.enforce_academic_style(content)
            content = self.format_citations(content)
            content = self.clean_whitespace(content)
            
            formatted["content"] = content
        
        return formatted
    
    def remove_markdown(self, text: str) -> str:
        """
        Remove all markdown formatting artifacts.
        
        Args:
            text: Input text with potential markdown
            
        Returns:
            Clean text without markdown
        """
        if not self.config.remove_markdown:
            return text
        
        result = text
        
        # Apply patterns line by line for line-start patterns
        lines = result.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = line
            for pattern, replacement in self.MARKDOWN_PATTERNS:
                if pattern.startswith('^'):
                    # Line-start pattern
                    cleaned_line = re.sub(pattern, replacement, cleaned_line, flags=re.MULTILINE)
                else:
                    cleaned_line = re.sub(pattern, replacement, cleaned_line)
            
            # Skip empty lines that were just markdown
            if cleaned_line.strip() or line.strip() == '':
                cleaned_lines.append(cleaned_line)
        
        result = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive blank lines
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result
    
    def enforce_academic_style(self, text: str) -> str:
        """
        Enforce academic writing conventions.
        
        Args:
            text: Input text
            
        Returns:
            Text with academic style improvements
        """
        if not self.config.enforce_academic_style:
            return text
        
        result = text
        
        for pattern, replacement in self.ACADEMIC_REPLACEMENTS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Remove double spaces created by replacements
        result = re.sub(r'  +', ' ', result)
        
        return result
    
    def format_citations(self, text: str) -> str:
        """
        Format citations to Harvard style with et al.
        
        Args:
            text: Input text with citations
            
        Returns:
            Text with properly formatted citations
        """
        # Pattern to match various citation formats
        # (Author1, Author2, Author3, Year) → (Author1 et al., Year)
        
        def format_citation_match(match):
            citation_text = match.group(1)
            
            # Check if it's a multi-author citation
            # Pattern: Name1, Name2, Name3, Year or Name1, Name2 and Name3, Year
            multi_author_pattern = r'^([^,]+(?:,\s*[^,]+){2,}),?\s*(\d{4}[a-z]?)$'
            multi_match = re.match(multi_author_pattern, citation_text)
            
            if multi_match and self.config.use_et_al:
                authors_part = multi_match.group(1)
                year = multi_match.group(2)
                
                # Count authors
                authors = re.split(r',\s*(?:and\s+)?|\s+and\s+', authors_part)
                authors = [a.strip() for a in authors if a.strip()]
                
                if len(authors) >= self.config.et_al_threshold:
                    first_author = authors[0]
                    return f"({first_author} et al., {year})"
            
            return match.group(0)
        
        # Apply to parenthetical citations
        result = re.sub(r'\(([^)]+)\)', format_citation_match, text)
        
        return result
    
    def clean_whitespace(self, text: str) -> str:
        """
        Clean up whitespace issues.
        
        Args:
            text: Input text
            
        Returns:
            Text with clean whitespace
        """
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        result = '\n'.join(lines)
        
        # Ensure proper spacing after periods
        result = re.sub(r'\.([A-Z])', r'. \1', result)
        
        # Remove space before punctuation
        result = re.sub(r'\s+([.,;:!?])', r'\1', result)
        
        # Ensure single space after punctuation
        result = re.sub(r'([.,;:!?])\s*', r'\1 ', result)
        
        # Fix double punctuation
        result = re.sub(r'([.,;:!?])\s*\1', r'\1', result)
        
        # Remove multiple spaces
        result = re.sub(r' {2,}', ' ', result)
        
        return result.strip()
    
    def _consolidate_references(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolidate all references into a single section.
        
        Removes inline reference lists from subsections and
        ensures all references appear only in the final REFERENCES section.
        """
        if "full_sections" not in proposal:
            return proposal
        
        all_references = []
        sections = proposal["full_sections"]
        
        # Collect references and remove inline reference sections
        for section in sections:
            content = section.get("content", "")
            
            # Check for inline references section
            refs_pattern = r'(?i)\n\s*references?\s*:?\s*\n[\s\S]*?(?=\n\s*[A-Z]|\Z)'
            ref_match = re.search(refs_pattern, content)
            
            if ref_match and section.get("title", "").lower() != "references":
                # Extract references
                ref_text = ref_match.group(0)
                refs = self._parse_references(ref_text)
                all_references.extend(refs)
                
                # Remove inline references
                section["content"] = content[:ref_match.start()] + content[ref_match.end():]
        
        # Find or create references section
        refs_section = None
        for section in sections:
            if "reference" in section.get("title", "").lower():
                refs_section = section
                break
        
        if refs_section is None:
            refs_section = {"title": "References", "content": ""}
            sections.append(refs_section)
        
        # Merge references
        existing_refs = self._parse_references(refs_section.get("content", ""))
        all_references.extend(existing_refs)
        
        # Deduplicate references
        unique_refs = list(dict.fromkeys(all_references))
        
        # Sort references alphabetically
        unique_refs.sort()
        
        # Format references section
        refs_section["content"] = '\n\n'.join(unique_refs)
        
        proposal["full_sections"] = sections
        
        return proposal
    
    def _parse_references(self, text: str) -> List[str]:
        """Parse individual references from text."""
        if not text:
            return []
        
        # Split by common reference delimiters
        # Try numbered format first
        refs = re.split(r'\n\s*\[\d+\]\s*|\n\s*\d+\.\s+', text)
        
        if len(refs) <= 2:
            # Try splitting by blank lines
            refs = text.split('\n\n')
        
        # Clean and filter
        cleaned = []
        for ref in refs:
            ref = ref.strip()
            # Filter out non-reference lines
            if len(ref) > 30 and '(' in ref and ')' in ref:
                cleaned.append(ref)
        
        return cleaned
    
    def format_for_export(
        self, 
        proposal: Dict[str, Any], 
        format_type: str = "docx"
    ) -> Dict[str, Any]:
        """
        Apply final formatting for specific export format.
        
        Args:
            proposal: Proposal dictionary
            format_type: Export format (docx, pdf, markdown)
            
        Returns:
            Proposal ready for export
        """
        formatted = self.format_proposal(proposal)
        
        if format_type == "markdown":
            # For markdown, we might want to add some structure back
            pass
        elif format_type in ("docx", "pdf"):
            # For Word/PDF, ensure clean text only
            for section in formatted.get("full_sections", []):
                section["content"] = self.remove_markdown(section.get("content", ""))
        
        return formatted


# Global instance
_formatting_controller: Optional[FormattingController] = None


def get_formatting_controller(config: Optional[FormattingConfig] = None) -> FormattingController:
    """Get or create the formatting controller instance."""
    global _formatting_controller
    if _formatting_controller is None:
        _formatting_controller = FormattingController(config)
    return _formatting_controller

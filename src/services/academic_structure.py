"""
Academic Structure Template - Q1/Scopus/Elsevier Format.

This module defines the exact structure and formatting rules
for academic research proposals following Q1 journal standards.

Structure follows the exact specification:
- Title Page
- Dedication Page
- Acknowledgement Page
- Abstract
- Table of Contents
- Chapters 1-3
- References
- Appendix
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from loguru import logger


class CitationStyle(Enum):
    """Supported citation styles."""
    HARVARD = "harvard"
    APA = "apa"
    IEEE = "ieee"
    CHICAGO = "chicago"


@dataclass
class PageSettings:
    """Page layout settings."""
    page_size: str = "A4"
    margin_top: float = 2.54  # cm
    margin_bottom: float = 2.54
    margin_left: float = 3.17
    margin_right: float = 2.54
    font_family: str = "Times New Roman"
    font_size: int = 12
    line_spacing: float = 1.5
    paragraph_spacing: float = 0.0
    first_line_indent: float = 1.27  # cm


@dataclass
class ProposalMetadata:
    """Metadata for the research proposal."""
    title: str
    author_name: str
    institution: str = ""
    department: str = ""
    supervisor_name: str = ""
    submission_date: str = field(default_factory=lambda: datetime.now().strftime("%B %Y"))
    dedication_to: str = ""
    acknowledgements_list: List[str] = field(default_factory=list)


@dataclass
class TableOfContentsEntry:
    """Single entry in table of contents."""
    title: str
    page_number: int
    level: int = 0  # 0 = chapter, 1 = section, 2 = subsection
    is_numbered: bool = True


class AcademicStructureTemplate:
    """
    Template for Q1/Scopus/Elsevier-style research proposals.
    
    Generates properly formatted academic documents with:
    - Title page with centered elements
    - Dedication and acknowledgement pages
    - Abstract with specific structure
    - Detailed table of contents
    - Properly numbered chapters and sections
    - Consolidated references section
    - Appendices
    """
    
    # Standard chapter structure
    CHAPTER_STRUCTURE = {
        1: {
            "title": "INTRODUCTION",
            "sections": [
                "Background of Study",
                "Problem Statement",
                "Aim and Objectives",
                "Scope of the Study",
                "Significance of the Study",
                "Structure of the Study",
            ]
        },
        2: {
            "title": "LITERATURE REVIEW",
            "sections": [
                "Introduction",
                "Literature Review",
                "Summary of Gaps",
                "Discussion",
            ]
        },
        3: {
            "title": "RESEARCH METHODOLOGY",
            "sections": [
                "Introduction",
                "Research Methodology",
                "Dataset Description",
                "Missing Values Imputation and Encoding",
                "Exploratory Data Analysis",
                "Design of Experimental Study",
                "Model Development",
                "Data Splitting",
                "Feature Selection",
                "Evaluating Multiple Models",
                "Comparative Analysis and Outcome",
                "Ethical Consideration",
                "Collaboration and Feedback",
                "Deliverables and Reports",
                "Required Resources",
                "Risk and Contingency Plan",
            ]
        }
    }
    
    # Pre-chapter sections (unnumbered)
    PRE_SECTIONS = [
        "DEDICATION",
        "ACKNOWLEDGEMENTS",
        "ABSTRACT",
        "LIST OF ABBREVIATIONS",
    ]
    
    def __init__(
        self,
        metadata: Optional[ProposalMetadata] = None,
        page_settings: Optional[PageSettings] = None,
        citation_style: CitationStyle = CitationStyle.HARVARD,
    ):
        """
        Initialize academic structure template.
        
        Args:
            metadata: Proposal metadata
            page_settings: Page layout settings
            citation_style: Citation formatting style
        """
        self.metadata = metadata or ProposalMetadata(
            title="Research Proposal",
            author_name="Author Name",
        )
        self.page_settings = page_settings or PageSettings()
        self.citation_style = citation_style
        
        logger.info("AcademicStructureTemplate initialized")
    
    def generate_title_page(self) -> Dict[str, Any]:
        """
        Generate title page content.
        
        Returns:
            Dict with title page structure
        """
        return {
            "type": "title_page",
            "page_number": 1,
            "content": {
                "title": self.metadata.title.upper(),
                "author": self.metadata.author_name,
                "institution": self.metadata.institution,
                "department": self.metadata.department,
                "date": self.metadata.submission_date,
            },
            "formatting": {
                "title_position": "center_upper",
                "author_position": "center_middle",
                "date_position": "center_lower",
                "page_number_position": "bottom_right",
                "page_number_format": "1 | {total}",
            }
        }
    
    def generate_dedication_page(self) -> Dict[str, Any]:
        """
        Generate dedication page content.
        
        Returns:
            Dict with dedication page structure
        """
        dedication_text = self._generate_dedication_text()
        
        return {
            "type": "dedication",
            "page_number": 2,
            "title": "DEDICATION",
            "content": dedication_text,
            "formatting": {
                "content_position": "center",
                "page_number_position": "bottom_right",
                "page_number_format": "2 | {total}",
            }
        }
    
    def _generate_dedication_text(self) -> str:
        """Generate appropriate dedication text."""
        if self.metadata.dedication_to:
            return f"""This research proposal is dedicated to {self.metadata.dedication_to}, whose unwavering support and encouragement have been instrumental in the pursuit of this academic endeavor.

Additionally, this work is dedicated to the pioneering researchers and scholars in the field whose foundational contributions have made this research possible, and to all those who continue to advance the boundaries of knowledge in this domain."""
        
        return """This research proposal is dedicated to the advancement of knowledge and to all scholars who have contributed to this field of study.

It is also dedicated to my family, mentors, and colleagues whose support and guidance have been invaluable throughout this academic journey."""
    
    def generate_acknowledgement_page(self) -> Dict[str, Any]:
        """
        Generate acknowledgement page content.
        
        Returns:
            Dict with acknowledgement page structure
        """
        acknowledgement_text = self._generate_acknowledgement_text()
        
        return {
            "type": "acknowledgement",
            "page_number": 3,
            "title": "ACKNOWLEDGEMENTS",
            "content": acknowledgement_text,
            "formatting": {
                "page_number_position": "bottom_right",
                "page_number_format": "3 | {total}",
            }
        }
    
    def _generate_acknowledgement_text(self) -> str:
        """Generate appropriate acknowledgement text."""
        supervisor_ack = ""
        if self.metadata.supervisor_name:
            supervisor_ack = f"I would like to express my sincere gratitude to my supervisor, {self.metadata.supervisor_name}, for their invaluable guidance, continuous support, and expert insights throughout the development of this research proposal. Their scholarly direction and constructive feedback have been instrumental in shaping this work."
        else:
            supervisor_ack = "I would like to express my sincere gratitude to my supervisor for their invaluable guidance, continuous support, and expert insights throughout the development of this research proposal."
        
        institution_ack = ""
        if self.metadata.institution:
            institution_ack = f"\n\nI am deeply grateful to {self.metadata.institution} for providing the academic environment and resources necessary for conducting this research."
        
        return f"""{supervisor_ack}
{institution_ack}

I extend my appreciation to the faculty members and staff who have contributed to my academic development and provided assistance during this research process.

My heartfelt thanks go to my family and friends for their unwavering support, patience, and encouragement throughout this academic journey.

I also acknowledge the contributions of all participants and collaborators who have made this research possible.

Finally, I am grateful to all the researchers and scholars whose work has informed and inspired this study."""
    
    def generate_abstract_template(self) -> Dict[str, Any]:
        """
        Generate abstract structure template.
        
        Abstract must contain:
        - 3 lines: Introduction of problem
        - 3 lines: Proposal focus
        - 4 lines: Literature summary
        - 3 lines: Discussion summary
        - 2 lines: Expected results
        
        Returns:
            Dict with abstract structure
        """
        return {
            "type": "abstract",
            "title": "ABSTRACT",
            "structure": {
                "problem_introduction": {
                    "lines": 3,
                    "description": "Introduction of the research problem and its context"
                },
                "proposal_focus": {
                    "lines": 3,
                    "description": "Clear statement of what this proposal addresses"
                },
                "literature_summary": {
                    "lines": 4,
                    "description": "Summary of key literature and current state of research"
                },
                "discussion_summary": {
                    "lines": 3,
                    "description": "Summary of research approach and methodology"
                },
                "expected_results": {
                    "lines": 2,
                    "description": "Expected outcomes and contributions"
                }
            },
            "total_words": "250-300",
            "formatting": {
                "single_paragraph": True,
                "no_citations": True,
            }
        }
    
    def generate_table_of_contents(self, total_pages: int = 50) -> List[TableOfContentsEntry]:
        """
        Generate table of contents entries.
        
        Args:
            total_pages: Estimated total pages
            
        Returns:
            List of TOC entries
        """
        toc = []
        current_page = 4  # After title, dedication, acknowledgement
        
        # Pre-sections (unnumbered)
        for section in self.PRE_SECTIONS:
            toc.append(TableOfContentsEntry(
                title=section,
                page_number=current_page,
                level=0,
                is_numbered=False,
            ))
            current_page += 1 if section != "ABSTRACT" else 1
        
        # Chapters
        for chapter_num, chapter_info in self.CHAPTER_STRUCTURE.items():
            # Chapter heading
            toc.append(TableOfContentsEntry(
                title=f"CHAPTER {chapter_num}: {chapter_info['title']}",
                page_number=current_page,
                level=0,
                is_numbered=True,
            ))
            current_page += 1
            
            # Sections
            for i, section in enumerate(chapter_info['sections'], 1):
                toc.append(TableOfContentsEntry(
                    title=f"{chapter_num}.{i} {section}",
                    page_number=current_page,
                    level=1,
                    is_numbered=True,
                ))
                current_page += 2  # Estimate 2 pages per section
        
        # References
        toc.append(TableOfContentsEntry(
            title="REFERENCES",
            page_number=current_page,
            level=0,
            is_numbered=False,
        ))
        current_page += 3
        
        # Appendix
        toc.append(TableOfContentsEntry(
            title="APPENDIX A: RESEARCH PLAN",
            page_number=current_page,
            level=0,
            is_numbered=False,
        ))
        
        return toc
    
    def generate_chapter_template(self, chapter_num: int) -> Dict[str, Any]:
        """
        Generate template for a specific chapter.
        
        Args:
            chapter_num: Chapter number (1, 2, or 3)
            
        Returns:
            Dict with chapter structure
        """
        if chapter_num not in self.CHAPTER_STRUCTURE:
            raise ValueError(f"Invalid chapter number: {chapter_num}")
        
        chapter_info = self.CHAPTER_STRUCTURE[chapter_num]
        
        sections = []
        for i, section_title in enumerate(chapter_info["sections"], 1):
            sections.append({
                "number": f"{chapter_num}.{i}",
                "title": section_title,
                "content_placeholder": f"[Content for {section_title}]",
            })
        
        return {
            "chapter_number": chapter_num,
            "title": f"CHAPTER {chapter_num}: {chapter_info['title']}",
            "sections": sections,
        }
    
    def generate_references_section(
        self, 
        references: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate properly formatted references section.
        
        Args:
            references: List of reference dictionaries
            
        Returns:
            Dict with references section structure
        """
        formatted_refs = []
        
        for ref in references:
            formatted_ref = self._format_reference(ref)
            if formatted_ref:
                formatted_refs.append(formatted_ref)
        
        # Sort alphabetically by first author
        formatted_refs.sort()
        
        return {
            "type": "references",
            "title": "REFERENCES",
            "references": formatted_refs,
            "count": len(formatted_refs),
        }
    
    def _format_reference(self, ref: Dict[str, Any]) -> str:
        """Format a single reference in Harvard style."""
        authors = ref.get("authors", [])
        year = ref.get("year", "n.d.")
        title = ref.get("title", "")
        venue = ref.get("venue", "")
        doi = ref.get("doi", "")
        
        if not authors or not title:
            return ""
        
        # Format authors
        if len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]} and {authors[1]}"
        else:
            author_str = f"{authors[0]} et al."
        
        # Harvard format
        citation = f"{author_str} ({year}) '{title}'"
        
        if venue:
            citation += f", {venue}"
        
        if doi:
            citation += f". doi: {doi}"
        
        citation += "."
        
        return citation
    
    def generate_appendix_template(self) -> Dict[str, Any]:
        """
        Generate appendix structure.
        
        Returns:
            Dict with appendix structure
        """
        return {
            "type": "appendix",
            "title": "APPENDIX A: RESEARCH PLAN",
            "content": {
                "gantt_chart": "[Research Timeline Gantt Chart]",
                "milestones": "[Key Milestones and Deliverables]",
                "resources": "[Required Resources and Budget]",
            }
        }
    
    def get_full_structure(self) -> Dict[str, Any]:
        """
        Get the complete proposal structure.
        
        Returns:
            Dict with full proposal structure
        """
        return {
            "metadata": {
                "title": self.metadata.title,
                "author": self.metadata.author_name,
                "institution": self.metadata.institution,
                "department": self.metadata.department,
                "submission_date": self.metadata.submission_date,
                "citation_style": self.citation_style.value,
            },
            "page_settings": {
                "page_size": self.page_settings.page_size,
                "margins": {
                    "top": self.page_settings.margin_top,
                    "bottom": self.page_settings.margin_bottom,
                    "left": self.page_settings.margin_left,
                    "right": self.page_settings.margin_right,
                },
                "font": {
                    "family": self.page_settings.font_family,
                    "size": self.page_settings.font_size,
                },
                "spacing": {
                    "line": self.page_settings.line_spacing,
                    "paragraph": self.page_settings.paragraph_spacing,
                    "first_line_indent": self.page_settings.first_line_indent,
                },
            },
            "front_matter": {
                "title_page": self.generate_title_page(),
                "dedication": self.generate_dedication_page(),
                "acknowledgement": self.generate_acknowledgement_page(),
                "abstract": self.generate_abstract_template(),
                "table_of_contents": [
                    entry.__dict__ for entry in self.generate_table_of_contents()
                ],
            },
            "chapters": {
                1: self.generate_chapter_template(1),
                2: self.generate_chapter_template(2),
                3: self.generate_chapter_template(3),
            },
            "back_matter": {
                "references": {"title": "REFERENCES", "references": []},
                "appendix": self.generate_appendix_template(),
            },
        }
    
    def map_content_to_structure(
        self, 
        generated_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map generated content to the academic structure.
        
        Args:
            generated_content: Content from generation pipeline
            
        Returns:
            Content organized into academic structure
        """
        structure = self.get_full_structure()
        
        sections = generated_content.get("full_sections", [])
        
        # Map sections to chapters based on title matching
        for section in sections:
            title = section.get("title", "").lower()
            content = section.get("content", "")
            
            if "introduction" in title:
                self._map_to_chapter(structure, 1, content)
            elif "literature" in title or "review" in title:
                self._map_to_chapter(structure, 2, content)
            elif "methodology" in title or "method" in title:
                self._map_to_chapter(structure, 3, content)
            elif "reference" in title:
                structure["back_matter"]["references"]["content"] = content
        
        return structure
    
    def _map_to_chapter(
        self, 
        structure: Dict[str, Any], 
        chapter_num: int, 
        content: str
    ) -> None:
        """Map content to a specific chapter."""
        if chapter_num in structure.get("chapters", {}):
            structure["chapters"][chapter_num]["content"] = content


# Factory function
def create_academic_template(
    title: str,
    author_name: str,
    institution: str = "",
    department: str = "",
    supervisor_name: str = "",
    citation_style: str = "harvard",
) -> AcademicStructureTemplate:
    """
    Create an academic structure template with metadata.
    
    Args:
        title: Proposal title
        author_name: Author's name
        institution: Institution name
        department: Department name
        supervisor_name: Supervisor's name
        citation_style: Citation style to use
        
    Returns:
        Configured AcademicStructureTemplate
    """
    metadata = ProposalMetadata(
        title=title,
        author_name=author_name,
        institution=institution,
        department=department,
        supervisor_name=supervisor_name,
    )
    
    style = CitationStyle.HARVARD
    if citation_style.lower() == "apa":
        style = CitationStyle.APA
    elif citation_style.lower() == "ieee":
        style = CitationStyle.IEEE
    elif citation_style.lower() == "chicago":
        style = CitationStyle.CHICAGO
    
    return AcademicStructureTemplate(
        metadata=metadata,
        citation_style=style,
    )

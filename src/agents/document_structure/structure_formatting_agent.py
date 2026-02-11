"""
Structure Formatting Agent - Applies Q1 journal formatting standards.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class StructureFormattingAgent(BaseAgent):
    """
    Structure Formatting Agent - Applies Q1 journal formatting standards.
    
    Responsibilities:
    - Apply Times New Roman 12pt font
    - Set 1.5 line spacing
    - Configure 1-inch margins
    - Generate section numbering (1, 1.1, 1.1.1)
    - Create table of contents
    - Add page numbers
    - Manage headers and footers
    - Apply title page formatting
    - Format headings hierarchy
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize structure formatting agent.
        
        Args:
            llm_provider: LLM provider (minimal use, mostly formatting)
            state_manager: State manager for persistence
        """
        super().__init__(
            agent_name="structure_formatting_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        # Q1 Journal formatting standards
        self.formatting_specs = {
            "font": {
                "name": "Times New Roman",
                "size": 12,
                "color": "black",
            },
            "spacing": {
                "line": 1.5,
                "before_paragraph": 0,
                "after_paragraph": 6,
            },
            "margins": {
                "top": 1.0,
                "bottom": 1.0,
                "left": 1.0,
                "right": 1.0,
            },
            "headings": {
                "h1": {"size": 14, "bold": True, "uppercase": True},
                "h2": {"size": 13, "bold": True, "uppercase": False},
                "h3": {"size": 12, "bold": True, "uppercase": False},
                "h4": {"size": 12, "bold": False, "italic": True, "uppercase": False},
            },
            "page_numbers": {
                "position": "bottom_center",
                "format": "arabic",
                "start": 1,
            },
        }
        
        logger.info("StructureFormattingAgent initialized with Q1 journal standards")
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute structure formatting.
        
        Args:
            request: Agent request with document sections
            
        Returns:
            AgentResponse with formatting specifications
        """
        try:
            input_data = request.input_data
            logger.info("Applying Q1 journal formatting standards")
            
            # Extract document sections
            sections = self._extract_sections(input_data)
            logger.info(f"Extracted {len(sections)} sections for formatting")
            
            # Generate section numbering
            numbered_sections = await self._apply_section_numbering(sections)
            logger.info("Section numbering applied")
            
            # Generate table of contents
            toc = await self._generate_table_of_contents(numbered_sections)
            logger.info("Table of contents generated")
            
            # Apply font formatting specifications
            font_specs = self._apply_font_formatting(numbered_sections)
            logger.info("Font formatting specifications applied")
            
            # Apply spacing and margins
            spacing_specs = self._apply_spacing_margins()
            logger.info("Spacing and margin specifications applied")
            
            # Configure page numbering
            page_config = self._configure_page_numbering(numbered_sections)
            logger.info("Page numbering configured")
            
            # Generate headers and footers
            header_footer = self._generate_header_footer(input_data)
            logger.info("Headers and footers configured")
            
            # Create title page specifications
            title_page = await self._create_title_page_spec(input_data)
            logger.info("Title page specifications created")
            
            # Compile formatting document
            formatting_doc = {
                "sections": numbered_sections,
                "table_of_contents": toc,
                "font_specifications": font_specs,
                "spacing_specifications": spacing_specs,
                "page_configuration": page_config,
                "header_footer": header_footer,
                "title_page": title_page,
                "formatting_standards": self.formatting_specs,
                "metadata": {
                    "total_sections": len(numbered_sections),
                    "toc_entries": len(toc),
                    "formatting_standard": "Q1 Journal",
                    "word_processor": "MS Word compatible",
                },
            }
            
            logger.info("Formatting specifications compiled successfully")
            
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output=formatting_doc,
                metadata={
                    "sections_formatted": len(numbered_sections),
                    "toc_entries": len(toc),
                    "formatting_standard": "Q1 Journal",
                },
            )
            
        except Exception as e:
            logger.error(f"Structure formatting failed: {e}")
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.FAILED,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            bool: True if valid
        """
        required_keys = ["topic"]
        return all(key in input_data for key in required_keys)
    
    def _extract_sections(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all document sections from dependencies.
        
        Args:
            input_data: Complete input data with dependencies
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        # Extract front matter
        front_matter = input_data.get("dependency_generate_front_matter", {})
        if front_matter:
            sections.append({
                "type": "front_matter",
                "title": "Front Matter",
                "level": 0,
                "content": front_matter,
                "page_break_before": False,
            })
        
        # Extract introduction
        introduction = input_data.get("dependency_generate_introduction", {})
        if introduction:
            sections.append({
                "type": "introduction",
                "title": "1. INTRODUCTION",
                "level": 1,
                "content": introduction,
                "page_break_before": True,
            })
        
        # Extract literature review
        lit_review = input_data.get("dependency_analyze_literature", {})
        if lit_review:
            sections.append({
                "type": "literature_review",
                "title": "2. LITERATURE REVIEW",
                "level": 1,
                "content": lit_review,
                "page_break_before": True,
            })
        
        # Extract methodology
        methodology = input_data.get("dependency_design_methodology", {})
        if methodology:
            sections.append({
                "type": "methodology",
                "title": "3. RESEARCH METHODOLOGY",
                "level": 1,
                "content": methodology,
                "page_break_before": True,
            })
        
        # Extract diagrams
        diagrams = input_data.get("dependency_create_diagrams", {})
        if diagrams:
            sections.append({
                "type": "diagrams",
                "title": "4. DIAGRAMS AND VISUALIZATIONS",
                "level": 1,
                "content": diagrams,
                "page_break_before": True,
            })
        
        # Extract risk assessment
        risk_assessment = input_data.get("dependency_assess_risks", {})
        if risk_assessment:
            sections.append({
                "type": "risk_assessment",
                "title": "5. RISK ASSESSMENT",
                "level": 1,
                "content": risk_assessment,
                "page_break_before": True,
            })
        
        # Extract references
        references = input_data.get("dependency_format_citations", {})
        if references:
            sections.append({
                "type": "references",
                "title": "REFERENCES",
                "level": 1,
                "content": references,
                "page_break_before": True,
            })
        
        return sections
    
    async def _apply_section_numbering(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply hierarchical section numbering.
        
        Args:
            sections: List of sections
            
        Returns:
            Sections with numbering applied
        """
        numbered_sections = []
        counters = {1: 0, 2: 0, 3: 0, 4: 0}
        
        for section in sections:
            # Skip front matter and references from numbering
            if section["type"] in ["front_matter", "references"]:
                numbered_sections.append(section)
                continue
            
            level = section.get("level", 1)
            
            # Increment counter for this level
            counters[level] += 1
            
            # Reset lower-level counters
            for l in range(level + 1, 5):
                counters[l] = 0
            
            # Generate number string
            if level == 1:
                number = str(counters[1])
            elif level == 2:
                number = f"{counters[1]}.{counters[2]}"
            elif level == 3:
                number = f"{counters[1]}.{counters[2]}.{counters[3]}"
            elif level == 4:
                number = f"{counters[1]}.{counters[2]}.{counters[3]}.{counters[4]}"
            
            # Update section with number
            section["number"] = number
            
            # Update title with number if not already present
            if not section["title"].startswith(number):
                # Remove old number if present
                title_parts = section["title"].split(" ", 1)
                if title_parts[0].replace(".", "").isdigit():
                    section["title"] = f"{number}. {title_parts[1]}"
                else:
                    section["title"] = f"{number}. {section['title']}"
            
            numbered_sections.append(section)
        
        return numbered_sections
    
    async def _generate_table_of_contents(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate table of contents from sections.
        
        Args:
            sections: Numbered sections
            
        Returns:
            Table of contents entries
        """
        toc_entries = []
        page_number = 1  # Start from page 1 (after title page)
        
        for section in sections:
            # Skip front matter components from TOC
            if section["type"] == "front_matter":
                continue
            
            # Add TOC entry
            entry = {
                "title": section["title"],
                "page": page_number,
                "level": section.get("level", 1),
                "number": section.get("number", ""),
            }
            toc_entries.append(entry)
            
            # Estimate pages (rough calculation: 300 words per page)
            content = section.get("content", {})
            if isinstance(content, dict):
                # Count words in all text fields
                word_count = sum(
                    len(str(v).split())
                    for v in content.values()
                    if isinstance(v, (str, list))
                )
            else:
                word_count = len(str(content).split())
            
            estimated_pages = max(1, word_count // 300)
            page_number += estimated_pages
        
        return toc_entries
    
    def _apply_font_formatting(
        self,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply font formatting specifications.
        
        Args:
            sections: Document sections
            
        Returns:
            Font formatting specifications
        """
        formatting = {
            "body_text": {
                "font_name": self.formatting_specs["font"]["name"],
                "font_size": self.formatting_specs["font"]["size"],
                "color": self.formatting_specs["font"]["color"],
                "alignment": "justify",
            },
            "headings": {},
        }
        
        # Apply heading styles for each level
        for level, specs in self.formatting_specs["headings"].items():
            formatting["headings"][level] = {
                "font_name": self.formatting_specs["font"]["name"],
                "font_size": specs["size"],
                "bold": specs["bold"],
                "uppercase": specs.get("uppercase", False),
                "italic": specs.get("italic", False),
                "alignment": "left",
                "spacing_before": 12,
                "spacing_after": 6,
            }
        
        return formatting
    
    def _apply_spacing_margins(self) -> Dict[str, Any]:
        """
        Apply spacing and margin specifications.
        
        Returns:
            Spacing and margin specifications
        """
        return {
            "line_spacing": self.formatting_specs["spacing"]["line"],
            "paragraph_spacing": {
                "before": self.formatting_specs["spacing"]["before_paragraph"],
                "after": self.formatting_specs["spacing"]["after_paragraph"],
            },
            "margins": {
                "top": self.formatting_specs["margins"]["top"],
                "bottom": self.formatting_specs["margins"]["bottom"],
                "left": self.formatting_specs["margins"]["left"],
                "right": self.formatting_specs["margins"]["right"],
                "units": "inches",
            },
            "page_size": {
                "width": 8.5,
                "height": 11,
                "units": "inches",
                "orientation": "portrait",
            },
        }
    
    def _configure_page_numbering(
        self,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Configure page numbering.
        
        Args:
            sections: Document sections
            
        Returns:
            Page numbering configuration
        """
        return {
            "start_page": self.formatting_specs["page_numbers"]["start"],
            "position": self.formatting_specs["page_numbers"]["position"],
            "format": self.formatting_specs["page_numbers"]["format"],
            "font": {
                "name": self.formatting_specs["font"]["name"],
                "size": 10,
            },
            "alignment": "center",
            "exclude_first_page": True,  # Don't number title page
            "roman_numerals_for_frontmatter": True,
        }
    
    def _generate_header_footer(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate header and footer specifications.
        
        Args:
            input_data: Input data with topic
            
        Returns:
            Header and footer specifications
        """
        topic = input_data.get("topic", "Research Proposal")
        
        # Extract author if available
        author = input_data.get("author", "")
        
        return {
            "header": {
                "enabled": True,
                "content": {
                    "left": "",
                    "center": "",
                    "right": f"{topic[:50]}...",  # Truncate long titles
                },
                "font": {
                    "name": self.formatting_specs["font"]["name"],
                    "size": 10,
                },
                "exclude_first_page": True,
            },
            "footer": {
                "enabled": True,
                "content": {
                    "left": author if author else "",
                    "center": "Page {PAGE_NUMBER}",
                    "right": "",
                },
                "font": {
                    "name": self.formatting_specs["font"]["name"],
                    "size": 10,
                },
                "exclude_first_page": True,
            },
        }
    
    async def _create_title_page_spec(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create title page specifications.
        
        Args:
            input_data: Input data with proposal details
            
        Returns:
            Title page specifications
        """
        topic = input_data.get("topic", "Research Proposal")
        author = input_data.get("author", "")
        institution = input_data.get("institution", "")
        department = input_data.get("department", "")
        date = input_data.get("date", "")
        
        return {
            "title": {
                "text": topic,
                "font_size": 18,
                "bold": True,
                "uppercase": True,
                "alignment": "center",
                "spacing_after": 24,
            },
            "subtitle": {
                "text": "Research Proposal",
                "font_size": 14,
                "bold": False,
                "alignment": "center",
                "spacing_after": 48,
            },
            "author": {
                "text": author,
                "font_size": 12,
                "bold": False,
                "alignment": "center",
                "spacing_after": 12,
            },
            "institution": {
                "text": institution,
                "font_size": 12,
                "bold": False,
                "alignment": "center",
                "spacing_after": 6,
            },
            "department": {
                "text": department,
                "font_size": 12,
                "bold": False,
                "alignment": "center",
                "spacing_after": 48,
            },
            "date": {
                "text": date,
                "font_size": 12,
                "bold": False,
                "alignment": "center",
            },
            "vertical_alignment": "center",
            "page_break_after": True,
        }


# Export
__all__ = ["StructureFormattingAgent"]

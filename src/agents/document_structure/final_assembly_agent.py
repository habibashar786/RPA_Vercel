"""
Final Assembly Agent - Compiles and exports complete research proposal.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class FinalAssemblyAgent(BaseAgent):
    """
    Final Assembly Agent - Compiles and exports complete research proposal.
    
    Responsibilities:
    - Assemble all sections in correct order
    - Generate appendices if needed
    - Create complete table of contents
    - Prepare for PDF export
    - Prepare for Word (.docx) export
    - Add final page numbers
    - Perform final validation
    - Generate document metadata
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize final assembly agent.
        
        Args:
            llm_provider: LLM provider (minimal use)
            state_manager: State manager for persistence
        """
        super().__init__(
            agent_name="final_assembly_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        # Document assembly order
        self.assembly_order = [
            "title_page",
            "dedication",
            "acknowledgements",
            "abstract",
            "table_of_contents",
            "list_of_figures",
            "list_of_tables",
            "list_of_abbreviations",
            "introduction",
            "literature_review",
            "methodology",
            "diagrams",
            "risk_assessment",
            "references",
            "appendices",
        ]
        
        logger.info("FinalAssemblyAgent initialized")
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute final document assembly.
        
        Args:
            request: Agent request with all document sections
            
        Returns:
            AgentResponse with complete assembled document
        """
        try:
            input_data = request.input_data
            topic = input_data.get("topic", "Research Proposal")
            
            logger.info(f"Assembling final document: {topic}")
            
            # Collect all sections
            sections = await self._collect_sections(input_data)
            logger.info(f"Collected {len(sections)} sections")
            
            # Assemble in correct order
            assembled_doc = await self._assemble_sections(sections, input_data)
            logger.info("Sections assembled in order")
            
            # Generate appendices if needed
            appendices = await self._generate_appendices(input_data)
            if appendices:
                assembled_doc["sections"]["appendices"] = appendices
                logger.info(f"Generated {len(appendices)} appendices")
            
            # Create final table of contents with actual page numbers
            final_toc = await self._create_final_toc(assembled_doc)
            assembled_doc["front_matter"]["table_of_contents"] = final_toc
            logger.info("Final table of contents created")
            
            # Calculate document statistics
            stats = self._calculate_statistics(assembled_doc)
            logger.info(f"Document statistics: {stats['total_words']} words, "
                       f"{stats['total_pages']} pages")
            
            # Prepare export specifications
            export_specs = await self._prepare_export_specs(assembled_doc, input_data)
            logger.info("Export specifications prepared")
            
            # Perform final validation
            validation = await self._final_validation(assembled_doc, stats)
            logger.info(f"Validation status: {validation['status']}")
            
            # Generate document metadata
            metadata = self._generate_document_metadata(input_data, stats, validation)
            logger.info("Document metadata generated")
            
            # Compile final output
            final_output = {
                "document": assembled_doc,
                "statistics": stats,
                "export_specifications": export_specs,
                "validation": validation,
                "metadata": metadata,
                "assembly_timestamp": datetime.now().isoformat(),
            }
            
            logger.info("Final document assembly complete")
            
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output=final_output,
                metadata={
                    "total_words": stats["total_words"],
                    "total_pages": stats["total_pages"],
                    "section_count": len(sections),
                    "validation_status": validation["status"],
                },
            )
            
        except Exception as e:
            logger.error(f"Final assembly failed: {e}")
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
    
    async def _collect_sections(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Collect all document sections from dependencies.
        
        Args:
            input_data: Complete input data
            
        Returns:
            Dictionary of all sections
        """
        sections = {}
        
        # Front matter
        sections["front_matter"] = input_data.get("dependency_generate_front_matter", {})
        
        # Main content sections
        sections["introduction"] = input_data.get("dependency_generate_introduction", {})
        sections["literature_review"] = input_data.get("dependency_analyze_literature", {})
        sections["methodology"] = input_data.get("dependency_design_methodology", {})
        sections["diagrams"] = input_data.get("dependency_create_diagrams", {})
        sections["risk_assessment"] = input_data.get("dependency_assess_risks", {})
        
        # Citations
        sections["references"] = input_data.get("dependency_format_citations", {})
        
        # Formatting
        sections["formatting"] = input_data.get("dependency_final_formatting", {})
        
        # Quality check results
        sections["quality_check"] = input_data.get("dependency_quality_check_1", {})
        
        return sections
    
    async def _assemble_sections(
        self,
        sections: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assemble sections in correct order.
        
        Args:
            sections: Dictionary of all sections
            input_data: Original input data
            
        Returns:
            Assembled document structure
        """
        formatting = sections.get("formatting", {})
        front_matter = sections.get("front_matter", {})
        
        assembled = {
            "title_page": formatting.get("title_page", {}),
            "front_matter": {
                "dedication": front_matter.get("dedication", ""),
                "acknowledgements": front_matter.get("acknowledgements", ""),
                "abstract": front_matter.get("abstract", {}),
                "keywords": front_matter.get("keywords", []),
                "table_of_contents": [],  # Will be updated with final TOC
                "list_of_figures": front_matter.get("list_of_figures", []),
                "list_of_tables": front_matter.get("list_of_tables", []),
                "list_of_abbreviations": front_matter.get("abbreviations", []),
            },
            "sections": {
                "introduction": sections.get("introduction", {}),
                "literature_review": sections.get("literature_review", {}),
                "methodology": sections.get("methodology", {}),
                "diagrams": sections.get("diagrams", {}),
                "risk_assessment": sections.get("risk_assessment", {}),
            },
            "back_matter": {
                "references": sections.get("references", {}),
                "appendices": [],  # Will be populated if needed
            },
            "formatting": formatting,
            "quality_assessment": sections.get("quality_check", {}),
        }
        
        return assembled
    
    async def _generate_appendices(
        self,
        input_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate appendices if needed.
        
        Args:
            input_data: Input data
            
        Returns:
            List of appendices
        """
        appendices = []
        
        # Appendix A: Research Instruments (if applicable)
        methodology = input_data.get("dependency_design_methodology", {})
        if methodology.get("data_collection"):
            appendices.append({
                "id": "A",
                "title": "Research Instruments",
                "content": {
                    "description": "Data collection instruments and tools",
                    "instruments": methodology.get("data_collection", {}),
                },
            })
        
        # Appendix B: Detailed Timeline
        if methodology.get("timeline"):
            appendices.append({
                "id": chr(65 + len(appendices)),  # B, C, D, etc.
                "title": "Detailed Research Timeline",
                "content": methodology.get("timeline", {}),
            })
        
        # Appendix C: Budget Breakdown (if provided)
        if input_data.get("budget"):
            appendices.append({
                "id": chr(65 + len(appendices)),
                "title": "Budget Breakdown",
                "content": input_data.get("budget", {}),
            })
        
        # Appendix D: Ethical Considerations
        if methodology.get("ethical_considerations"):
            appendices.append({
                "id": chr(65 + len(appendices)),
                "title": "Ethical Considerations",
                "content": methodology.get("ethical_considerations", {}),
            })
        
        return appendices
    
    async def _create_final_toc(
        self,
        assembled_doc: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create final table of contents with actual page numbers.
        
        Args:
            assembled_doc: Assembled document
            
        Returns:
            Final table of contents
        """
        toc = []
        current_page = 1
        
        # Front matter (roman numerals)
        front_matter_items = [
            ("Dedication", "dedication"),
            ("Acknowledgements", "acknowledgements"),
            ("Abstract", "abstract"),
            ("List of Figures", "list_of_figures"),
            ("List of Tables", "list_of_tables"),
            ("List of Abbreviations", "list_of_abbreviations"),
        ]
        
        roman_page = 1
        for title, key in front_matter_items:
            content = assembled_doc["front_matter"].get(key)
            if content:
                toc.append({
                    "title": title,
                    "page": self._to_roman(roman_page),
                    "level": 0,
                })
                roman_page += 1
        
        # Main sections (arabic numerals)
        sections_map = {
            "1. INTRODUCTION": "introduction",
            "2. LITERATURE REVIEW": "literature_review",
            "3. RESEARCH METHODOLOGY": "methodology",
            "4. DIAGRAMS AND VISUALIZATIONS": "diagrams",
            "5. RISK ASSESSMENT": "risk_assessment",
        }
        
        for title, key in sections_map.items():
            content = assembled_doc["sections"].get(key)
            if content:
                # Estimate pages (300 words per page)
                word_count = self._count_words(content)
                pages = max(1, word_count // 300)
                
                toc.append({
                    "title": title,
                    "page": current_page,
                    "level": 1,
                })
                current_page += pages
        
        # References
        if assembled_doc["back_matter"].get("references"):
            toc.append({
                "title": "REFERENCES",
                "page": current_page,
                "level": 1,
            })
            current_page += 2  # Estimate 2 pages for references
        
        # Appendices
        for appendix in assembled_doc["back_matter"].get("appendices", []):
            toc.append({
                "title": f"APPENDIX {appendix['id']}: {appendix['title']}",
                "page": current_page,
                "level": 1,
            })
            current_page += 1
        
        return toc
    
    def _calculate_statistics(self, assembled_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate document statistics.
        
        Args:
            assembled_doc: Assembled document
            
        Returns:
            Document statistics
        """
        total_words = 0
        section_stats = {}
        
        # Count words in each section
        for section_name, content in assembled_doc["sections"].items():
            word_count = self._count_words(content)
            total_words += word_count
            section_stats[section_name] = {
                "words": word_count,
                "pages": max(1, word_count // 300),
            }
        
        # Count front matter words
        front_matter_words = self._count_words(assembled_doc["front_matter"])
        total_words += front_matter_words
        
        # Count references
        references_words = self._count_words(assembled_doc["back_matter"]["references"])
        total_words += references_words
        
        # Estimate total pages
        total_pages = max(1, total_words // 300)
        
        # Count figures and tables
        figures = len(assembled_doc["front_matter"].get("list_of_figures", []))
        tables = len(assembled_doc["front_matter"].get("list_of_tables", []))
        
        return {
            "total_words": total_words,
            "total_pages": total_pages,
            "section_statistics": section_stats,
            "front_matter_words": front_matter_words,
            "references_count": len(
                assembled_doc["back_matter"]["references"].get("citations", [])
            ),
            "figures_count": figures,
            "tables_count": tables,
            "appendices_count": len(assembled_doc["back_matter"].get("appendices", [])),
        }
    
    async def _prepare_export_specs(
        self,
        assembled_doc: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare export specifications for PDF and Word.
        
        Args:
            assembled_doc: Assembled document
            input_data: Original input data
            
        Returns:
            Export specifications
        """
        topic = input_data.get("topic", "Research Proposal")
        
        return {
            "pdf": {
                "filename": f"{topic.replace(' ', '_')}_Proposal.pdf",
                "format": "PDF/A",
                "compression": True,
                "bookmarks": True,
                "metadata": {
                    "title": topic,
                    "subject": "Research Proposal",
                    "author": input_data.get("author", ""),
                    "creator": "Multi-Agentic Research Proposal System",
                },
            },
            "docx": {
                "filename": f"{topic.replace(' ', '_')}_Proposal.docx",
                "format": "Office Open XML",
                "compatibility_mode": "Word 2016+",
                "track_changes": False,
                "metadata": {
                    "title": topic,
                    "subject": "Research Proposal",
                    "author": input_data.get("author", ""),
                    "category": "Academic Research",
                },
            },
            "markdown": {
                "filename": f"{topic.replace(' ', '_')}_Proposal.md",
                "format": "GitHub Flavored Markdown",
                "include_yaml_frontmatter": True,
            },
        }
    
    async def _final_validation(
        self,
        assembled_doc: Dict[str, Any],
        stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform final validation checks.
        
        Args:
            assembled_doc: Assembled document
            stats: Document statistics
            
        Returns:
            Validation results
        """
        issues = []
        warnings = []
        
        # Check word count (target: 15,000+ words)
        if stats["total_words"] < 15000:
            issues.append(f"Word count ({stats['total_words']}) below target (15,000)")
        
        # Check required sections
        required_sections = ["introduction", "literature_review", "methodology"]
        for section in required_sections:
            if not assembled_doc["sections"].get(section):
                issues.append(f"Missing required section: {section}")
        
        # Check front matter completeness
        required_front_matter = ["abstract", "keywords"]
        for item in required_front_matter:
            if not assembled_doc["front_matter"].get(item):
                issues.append(f"Missing front matter: {item}")
        
        # Check abstract word count
        abstract = assembled_doc["front_matter"].get("abstract", {})
        abstract_words = abstract.get("word_count", 0)
        if abstract_words < 200 or abstract_words > 300:
            warnings.append(f"Abstract word count ({abstract_words}) outside range (200-300)")
        
        # Check references
        ref_count = stats.get("references_count", 0)
        if ref_count < 30:
            warnings.append(f"Reference count ({ref_count}) below recommended (30+)")
        
        # Determine validation status
        if issues:
            status = "FAILED"
        elif warnings:
            status = "PASSED_WITH_WARNINGS"
        else:
            status = "PASSED"
        
        return {
            "status": status,
            "issues": issues,
            "warnings": warnings,
            "checks_passed": len(issues) == 0,
            "total_checks": len(required_sections) + len(required_front_matter) + 3,
        }
    
    def _generate_document_metadata(
        self,
        input_data: Dict[str, Any],
        stats: Dict[str, Any],
        validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive document metadata.
        
        Args:
            input_data: Original input data
            stats: Document statistics
            validation: Validation results
            
        Returns:
            Document metadata
        """
        return {
            "title": input_data.get("topic", "Research Proposal"),
            "author": input_data.get("author", ""),
            "institution": input_data.get("institution", ""),
            "department": input_data.get("department", ""),
            "date_created": datetime.now().isoformat(),
            "version": "1.0",
            "word_count": stats["total_words"],
            "page_count": stats["total_pages"],
            "validation_status": validation["status"],
            "formatting_standard": "Q1 Journal",
            "generated_by": "Multi-Agentic Research Proposal System",
            "system_version": "1.0.0",
        }
    
    def _count_words(self, content: Any) -> int:
        """
        Count words in content.
        
        Args:
            content: Content to count (dict, list, or string)
            
        Returns:
            Word count
        """
        if isinstance(content, dict):
            return sum(self._count_words(v) for v in content.values())
        elif isinstance(content, list):
            return sum(self._count_words(item) for item in content)
        elif isinstance(content, str):
            return len(content.split())
        else:
            return 0
    
    def _to_roman(self, num: int) -> str:
        """
        Convert number to Roman numerals.
        
        Args:
            num: Number to convert
            
        Returns:
            Roman numeral string
        """
        values = [
            (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')
        ]
        
        result = ''
        for value, numeral in values:
            count = num // value
            if count:
                result += numeral * count
                num -= value * count
        
        return result


# Export
__all__ = ["FinalAssemblyAgent"]

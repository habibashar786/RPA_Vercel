"""
Services module for ResearchAI platform.
Contains PDF ingestion, formatting, and utility services.
"""

from .pdf_ingestion import PDFIngestionService, ParsedPaper
from .formatting_controller import FormattingController
from .academic_structure import AcademicStructureTemplate

__all__ = [
    "PDFIngestionService",
    "ParsedPaper",
    "FormattingController", 
    "AcademicStructureTemplate",
]

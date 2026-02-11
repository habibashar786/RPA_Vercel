"""
Proposal data models and schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SectionType(str, Enum):
    """Types of sections in a research proposal."""

    TITLE_PAGE = "title_page"
    DEDICATION = "dedication"
    ACKNOWLEDGEMENT = "acknowledgement"
    ABSTRACT = "abstract"
    TABLE_OF_CONTENTS = "table_of_contents"
    LIST_OF_FIGURES = "list_of_figures"
    LIST_OF_ABBREVIATIONS = "list_of_abbreviations"
    INTRODUCTION = "introduction"
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY = "methodology"
    EXPECTED_OUTCOMES = "expected_outcomes"
    ETHICAL_CONSIDERATIONS = "ethical_considerations"
    REQUIRED_RESOURCES = "required_resources"
    RISK_PLAN = "risk_plan"
    REFERENCES = "references"
    APPENDIX = "appendix"


class CitationStyle(str, Enum):
    """Supported citation styles."""

    HARVARD = "harvard"
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"


class OutputFormat(str, Enum):
    """Supported output formats."""

    PDF = "pdf"
    DOCX = "docx"
    LATEX = "latex"


class ProposalRequest(BaseModel):
    """Request model for generating a research proposal."""

    topic: str = Field(..., min_length=10, max_length=500, description="Research topic")
    key_points: List[str] = Field(
        ..., min_length=1, max_length=20, description="Key points to cover"
    )
    user_id: Optional[str] = Field(None, description="User identifier")
    custom_requirements: Optional[Dict[str, Any]] = Field(
        None, description="Custom requirements"
    )
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Execution preferences for the workflow")
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    citation_style: CitationStyle = Field(
        default=CitationStyle.HARVARD, description="Citation style preference"
    )
    output_formats: List[OutputFormat] = Field(
        default=[OutputFormat.PDF, OutputFormat.DOCX], description="Output formats"
    )
    target_word_count: int = Field(
        default=15000, ge=10000, le=25000, description="Target word count"
    )
    literature_years: int = Field(
        default=6, ge=3, le=15, description="Years for recent literature"
    )
    min_papers: int = Field(
        default=30, ge=20, le=100, description="Minimum papers to review"
    )

    @field_validator("key_points")
    @classmethod
    def validate_key_points(cls, v: List[str]) -> List[str]:
        """Validate key points are not empty."""
        return [kp.strip() for kp in v if kp.strip()]


class ProposalSection(BaseModel):
    """A section of the research proposal."""

    section_type: Optional[SectionType] = None
    title: str
    content: str
    word_count: int = 0
    subsections: List["ProposalSection"] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    citations: List[str] = Field(default_factory=list)
    figures: List[Dict[str, Any]] = Field(default_factory=list)
    generated_by: Optional[str] = Field(None, description="Agent that generated this")
    created_at: datetime = Field(default_factory=datetime.now)
    revised_count: int = 0

    def calculate_word_count(self) -> int:
        """Calculate word count for this section."""
        count = len(self.content.split())
        for subsection in self.subsections:
            count += subsection.calculate_word_count()
        self.word_count = count
        return count


class Citation(BaseModel):
    """Citation information."""

    citation_id: str
    authors: List[str]
    title: str
    year: int
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    citation_text: str
    citation_style: CitationStyle = CitationStyle.HARVARD


class ProposalMetadata(BaseModel):
    """Metadata for the research proposal."""

    request_id: str
    topic: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: int = 1
    status: str = "draft"
    total_word_count: int = 0
    paper_count: int = 0
    citations: List[Citation] = Field(default_factory=list)
    agents_involved: List[str] = Field(default_factory=list)
    processing_time: float = 0.0
    quality_score: Optional[float] = None
    turnitin_estimated: Optional[float] = None


class ProposalResponse(BaseModel):
    """Complete research proposal response."""

    request_id: str
    metadata: ProposalMetadata
    sections: List[ProposalSection]
    references: List[Citation] = Field(default_factory=list)
    appendices: List[Dict[str, Any]] = Field(default_factory=list)
    diagrams: List[Dict[str, Any]] = Field(default_factory=list)
    qa_report: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    export_urls: Dict[str, str] = Field(default_factory=dict)

    def get_total_word_count(self) -> int:
        """Calculate total word count."""
        total = sum(section.calculate_word_count() for section in self.sections)
        self.metadata.total_word_count = total
        return total

    def get_section(self, section_type: SectionType) -> Optional[ProposalSection]:
        """Get a specific section by type."""
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None


class LiteraturePaper(BaseModel):
    """Information about a reviewed paper."""

    paper_id: str
    title: str
    authors: List[str]
    year: int
    abstract: str
    venue: Optional[str] = None
    citation_count: int = 0
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    source: str  # semantic_scholar, arxiv, frontiers, etc.
    relevance_score: float = 0.0
    key_findings: Optional[str] = None
    research_gaps: List[str] = Field(default_factory=list)
    methodology: Optional[str] = None


class ResearchGap(BaseModel):
    """Identified research gap from literature review."""

    gap_id: str
    title: str = ""  # Brief title for the gap (optional, defaults to empty)
    description: str
    related_papers: List[str] = Field(default_factory=list)
    significance: str = "medium"  # low, medium, high, critical
    addressable: bool = True
    proposed_approach: Optional[str] = None
    current_state: Optional[str] = None  # What exists now


class MethodologyDesign(BaseModel):
    """Research methodology design."""

    paradigm: str  # positivist, interpretivist, pragmatist
    approach: str  # quantitative, qualitative, mixed
    design: str  # experimental, correlational, case study, etc.
    data_collection: List[str] = Field(default_factory=list)
    data_analysis: List[str] = Field(default_factory=list)
    sample_size: Optional[int] = None
    sample_strategy: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    process_flow: Optional[str] = None  # Mermaid diagram code
    ethical_considerations: List[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    """Quality assurance report."""

    overall_score: float = Field(ge=0.0, le=1.0)
    structure_score: float = Field(ge=0.0, le=1.0)
    clarity_score: float = Field(ge=0.0, le=1.0)
    coherence_score: float = Field(ge=0.0, le=1.0)
    originality_score: float = Field(ge=0.0, le=1.0)
    citation_accuracy: float = Field(ge=0.0, le=1.0)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    passed: bool = False
    turnitin_estimate: Optional[float] = None
    iteration: int = 1

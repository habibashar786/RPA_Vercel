"""
ResearchAI v2.5.2 - Dynamic Title Page Generator
=================================================
Modular component for generating professional title pages with:
- User name injection ({{USER_NAME}} variable)
- Line-based precision layout (matching reference image)
- WCAG AA compliant styling
- Page break enforcement
- Watermark compatibility

Reference Image Layout:
- Title: TOP, center-justified, Bold, All-Caps
- Author Name: 7 lines below title
- "RESEARCH PROPOSAL": 10 lines below author
- Date: 13 lines below "RESEARCH PROPOSAL"
- "1 | Page" footer at bottom right
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# LINE HEIGHT CONSTANT (based on 12pt font, ~18pt leading)
LINE_HEIGHT = 18  # points per line


@dataclass
class TitlePageData:
    """Data container for title page content."""
    title: str
    author_name: str
    document_type: str = "RESEARCH PROPOSAL"
    date_footer: str = ""
    institution: str = ""
    department: str = ""
    supervisor_name: str = ""
    
    def __post_init__(self):
        # Generate dynamic date if not provided
        if not self.date_footer:
            self.date_footer = datetime.now().strftime("%B %Y").upper()


class TitlePageGenerator:
    """
    Title Page Generator Component
    
    Implements:
    1. Dynamic Variable Injection ({{USER_NAME}})
    2. Line-Based Precision Layout (Reference Image Match)
    3. Modular Architecture (separate from main assembly)
    4. PDF Precision & Watermark Compatibility
    
    Layout Specification (from reference image):
    - Title at TOP with minimal margin
    - 7 lines gap → Author Name
    - 10 lines gap → "RESEARCH PROPOSAL" (FIXED)
    - 13 lines gap → Date (FIXED)
    - "1 | Page" footer at bottom right
    """
    
    # CSS Template for Title Page - Line-based layout
    CSS_TEMPLATE = """
    /* Title Page CSS - ResearchAI v2.5.2 */
    .title-page {
        width: 100%;
        height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0.3in 1.5in 1in 1.5in;
        box-sizing: border-box;
        page-break-after: always;
        position: relative;
        font-family: 'Times New Roman', Times, serif;
    }
    
    /* Title Block - At very top */
    .title-block {
        text-align: center;
        font-size: 14pt;
        font-weight: bold;
        text-transform: uppercase;
        line-height: 1.4;
        margin-bottom: calc(7 * 18pt); /* 7 lines gap */
    }
    
    /* Author Name - 7 lines below title */
    .author-block {
        text-align: center;
        font-size: 12pt;
        font-variant: small-caps;
        margin-bottom: calc(10 * 18pt); /* 10 lines gap - FIXED */
    }
    
    /* Document Type - 10 lines below author */
    .document-type-block {
        text-align: center;
        font-size: 12pt;
        font-weight: bold;
        margin-bottom: calc(13 * 18pt); /* 13 lines gap - FIXED */
    }
    
    /* Date Footer - 13 lines below document type */
    .date-footer {
        text-align: center;
        font-size: 12pt;
    }
    
    /* Page Number Footer */
    .page-footer {
        position: absolute;
        bottom: 1.5cm;
        right: 2cm;
        font-size: 10pt;
    }
    """
    
    @staticmethod
    def generate_title_page(user_data: Dict[str, Any], proposal_data: Dict[str, Any]) -> TitlePageData:
        """
        Generate title page data from user and proposal information.
        
        Args:
            user_data: Dictionary containing user information (name, student_name, etc.)
            proposal_data: Dictionary containing proposal information (topic, etc.)
        
        Returns:
            TitlePageData: Data container with all title page content
        """
        # Extract author name with fallback chain
        author_name = (
            user_data.get("name") or
            user_data.get("student_name") or
            user_data.get("author_name") or
            user_data.get("user_name") or
            proposal_data.get("student_name") or
            "Researcher"
        )
        
        # Extract topic/title
        title = (
            proposal_data.get("topic") or
            proposal_data.get("title") or
            "Research Proposal"
        )
        
        # Optional fields
        institution = user_data.get("institution", "") or proposal_data.get("institution", "")
        department = user_data.get("department", "") or proposal_data.get("department", "")
        supervisor_name = user_data.get("supervisor_name", "") or proposal_data.get("supervisor_name", "")
        
        return TitlePageData(
            title=title,
            author_name=author_name,
            institution=institution,
            department=department,
            supervisor_name=supervisor_name,
        )
    
    @staticmethod
    def to_html(data: TitlePageData, include_css: bool = True) -> str:
        """
        Generate HTML representation of the title page.
        
        Args:
            data: TitlePageData container
            include_css: Whether to include inline CSS styles
        
        Returns:
            str: HTML string for the title page
        """
        css = TitlePageGenerator.CSS_TEMPLATE if include_css else ""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>{css}</style>
</head>
<body>
    <div class="title-page">
        <div class="title-block">{data.title.upper()}</div>
        <div class="author-block">{data.author_name.title()}</div>
        <div class="document-type-block">{data.document_type}</div>
        <div class="date-footer">{data.date_footer}</div>
        <div class="page-footer">1 | Page</div>
    </div>
</body>
</html>
"""
        return html
    
    @staticmethod
    def to_plain_text(data: TitlePageData) -> str:
        """
        Generate plain text representation of the title page.
        
        Args:
            data: TitlePageData container
        
        Returns:
            str: Plain text string for the title page
        """
        # Calculate line gaps
        title_lines = data.title.upper()
        gap_7 = "\n" * 7
        gap_10 = "\n" * 10
        gap_13 = "\n" * 13
        
        text = f"""{title_lines}
{gap_7}
{data.author_name.title()}
{gap_10}
{data.document_type}
{gap_13}
{data.date_footer}
"""
        return text
    
    @staticmethod
    def to_reportlab_story(data: TitlePageData, doc, styles) -> list:
        """
        Generate ReportLab story elements for the title page.
        
        Args:
            data: TitlePageData container
            doc: ReportLab SimpleDocTemplate
            styles: ReportLab StyleSheet
        
        Returns:
            list: List of ReportLab flowable elements
        """
        from reportlab.platypus import Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import inch
        
        story = []
        
        # Title style
        title_style = ParagraphStyle(
            'TitlePageTitle',
            parent=styles['Title'],
            fontSize=14,
            fontName='Times-Bold',
            alignment=TA_CENTER,
            leading=20,
            spaceAfter=0,
        )
        
        # Author style
        author_style = ParagraphStyle(
            'TitlePageAuthor',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Times-Roman',
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        
        # Document type style
        doc_type_style = ParagraphStyle(
            'TitlePageDocType',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Times-Bold',
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        
        # Date style
        date_style = ParagraphStyle(
            'TitlePageDate',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Times-Roman',
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        
        # Build story with line-based spacing
        story.append(Spacer(1, 0.3*inch))  # Small top margin
        story.append(Paragraph(data.title.upper(), title_style))
        story.append(Spacer(1, 7 * LINE_HEIGHT))  # 7 lines gap
        story.append(Paragraph(data.author_name.title(), author_style))
        story.append(Spacer(1, 10 * LINE_HEIGHT))  # 10 lines gap (FIXED)
        story.append(Paragraph(data.document_type, doc_type_style))
        story.append(Spacer(1, 13 * LINE_HEIGHT))  # 13 lines gap (FIXED)
        story.append(Paragraph(data.date_footer, date_style))
        story.append(PageBreak())
        
        return story
    
    @staticmethod
    def validate_layout(data: TitlePageData) -> Dict[str, Any]:
        """
        Validate title page layout for compliance.
        
        Args:
            data: TitlePageData container
        
        Returns:
            dict: Validation result with issues and suggestions
        """
        issues = []
        warnings = []
        
        # Check title length
        if len(data.title) > 200:
            warnings.append("Title is very long (>200 chars), may wrap to many lines")
        
        # Check author name
        if not data.author_name or data.author_name == "Researcher":
            issues.append("Author name not specified, using default 'Researcher'")
        
        # Check date format
        if not data.date_footer:
            warnings.append("Date footer not specified, using current date")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "data": {
                "title_length": len(data.title),
                "author_name": data.author_name,
                "date_footer": data.date_footer,
            }
        }


# Module-level convenience function
def generate_title_page(user_data: Dict[str, Any], proposal_data: Dict[str, Any]) -> TitlePageData:
    """
    Generate title page data from user and proposal information.
    
    This is the main entry point for the title page generator module.
    
    Args:
        user_data: Dictionary containing user information
        proposal_data: Dictionary containing proposal information
    
    Returns:
        TitlePageData: Data container with all title page content
    """
    return TitlePageGenerator.generate_title_page(user_data, proposal_data)


# Module-level instance for easy import
title_page_generator = TitlePageGenerator()

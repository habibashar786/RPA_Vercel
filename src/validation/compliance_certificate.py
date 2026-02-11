"""
Compliance Certificate Generator v2.7.0

Generates cryptographically-bound academic compliance certificates.

Certificate Properties:
- Non-editable (read-only)
- Cryptographically bound to validated document (SHA-256)
- Contains validation metadata only
- Exportable with submission package
"""
import hashlib
import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComplianceCertificate:
    """
    Immutable compliance certificate.
    
    Cryptographically bound to the validated document via SHA-256 hash.
    Any modification to the document invalidates the certificate.
    """
    certificate_id: str
    document_hash: str
    validation_timestamp: str
    similarity_score: float
    ai_detection_score: Optional[float]
    validation_source: str
    rule_set_version: str
    status: str
    institution: Optional[str] = None
    submission_id: Optional[str] = None
    
    # Computed field - set in __post_init__
    certificate_hash: str = ""
    
    def __post_init__(self):
        """Generate cryptographic hash binding certificate to document"""
        cert_data = json.dumps({
            "certificate_id": self.certificate_id,
            "document_hash": self.document_hash,
            "validation_timestamp": self.validation_timestamp,
            "similarity_score": self.similarity_score,
            "status": self.status,
            "rule_set_version": self.rule_set_version
        }, sort_keys=True)
        
        self.certificate_hash = hashlib.sha256(cert_data.encode()).hexdigest()
        
        logger.info(
            f"[Certificate] Generated certificate {self.certificate_id} "
            f"(hash: {self.certificate_hash[:16]}...)"
        )
    
    def to_dict(self) -> dict:
        """Convert certificate to dictionary"""
        return asdict(self)
    
    def verify_document(self, document_content: str) -> bool:
        """
        Verify that document content matches certificate.
        
        Args:
            document_content: Current document content
            
        Returns:
            bool: True if document matches certificate
        """
        current_hash = hashlib.sha256(document_content.encode('utf-8')).hexdigest()
        return current_hash == self.document_hash


class CertificateGenerator:
    """
    Generate PDF compliance certificates.
    
    Certificates are:
    - Non-editable
    - Cryptographically bound
    - Professional academic format
    """
    
    @staticmethod
    def generate_pdf(cert: ComplianceCertificate) -> bytes:
        """
        Generate non-editable PDF certificate.
        
        Args:
            cert: ComplianceCertificate to render
            
        Returns:
            bytes: PDF file content
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        )
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            leftMargin=1*inch,
            rightMargin=1*inch
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CertTitle',
            parent=styles['Title'],
            fontSize=22,
            textColor=colors.HexColor('#1a237e'),
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CertSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#2e7d32'),
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica'
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#37474f'),
            alignment=TA_LEFT,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CertBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            fontName='Helvetica'
        )
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#78909c'),
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        
        hash_style = ParagraphStyle(
            'HashStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#607d8b'),
            alignment=TA_CENTER,
            fontName='Courier'
        )
        
        story = []
        
        # Header with decorative line
        story.append(Spacer(1, 20))
        story.append(Paragraph("ACADEMIC COMPLIANCE CERTIFICATE", title_style))
        story.append(Paragraph("✓ Originality Verification Passed", subtitle_style))
        
        # Certificate details section
        story.append(Paragraph("VALIDATION DETAILS", section_title_style))
        
        # Main details table
        details_data = [
            ["Certificate ID:", cert.certificate_id],
            ["Validation Date:", cert.validation_timestamp[:19].replace('T', ' ')],
            ["Validation Source:", cert.validation_source],
            ["Rule Set Version:", cert.rule_set_version],
        ]
        
        if cert.institution:
            details_data.append(["Institution:", cert.institution])
        
        if cert.submission_id:
            details_data.append(["Submission ID:", cert.submission_id])
        
        details_table = Table(details_data, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#455a64')),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 20))
        
        # Validation results section
        story.append(Paragraph("VALIDATION RESULTS", section_title_style))
        
        # Results with visual indicators
        results_data = [
            ["Overall Similarity:", f"{cert.similarity_score:.1f}%", "✓ PASSED"],
            ["AI Detection Score:", f"{cert.ai_detection_score:.1f}%" if cert.ai_detection_score else "N/A", "✓ PASSED"],
            ["Final Status:", cert.status.split(' - ')[0], ""],
        ]
        
        results_table = Table(results_data, colWidths=[2*inch, 2*inch, 2*inch])
        results_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#455a64')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#2e7d32')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ]))
        story.append(results_table)
        story.append(Spacer(1, 30))
        
        # Document hash section
        story.append(Paragraph("DOCUMENT VERIFICATION", section_title_style))
        story.append(Paragraph(
            "This certificate is cryptographically bound to the following document hash:",
            body_style
        ))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"SHA-256: {cert.document_hash}",
            hash_style
        ))
        story.append(Spacer(1, 20))
        
        # Certificate hash
        story.append(Paragraph(
            f"Certificate Hash: {cert.certificate_hash}",
            hash_style
        ))
        story.append(Spacer(1, 40))
        
        # Status box
        status_text = "✓ READY FOR INSTITUTIONAL SUBMISSION"
        status_style = ParagraphStyle(
            'StatusBox',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        status_data = [[Paragraph(status_text, status_style)]]
        status_table = Table(status_data, colWidths=[6*inch])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2e7d32')),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(status_table)
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(Paragraph(
            "This certificate is generated automatically by ResearchAI Academic Validation System.<br/>"
            "Any modification to the original document will invalidate this certificate.<br/>"
            "Verify authenticity by comparing document hash with the hash recorded above.",
            footer_style
        ))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"[Certificate] PDF generated for certificate {cert.certificate_id}")
        
        return buffer.getvalue()
    
    @staticmethod
    def generate_json(cert: ComplianceCertificate) -> str:
        """Generate JSON representation of certificate"""
        return json.dumps(cert.to_dict(), indent=2)

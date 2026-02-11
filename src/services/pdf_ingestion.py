"""
PDF Ingestion Service - Parses uploaded PDF research papers.

This service extracts structured content from PDF papers including:
- Abstract
- Methodology sections
- Key findings
- References
- Metadata (authors, year, DOI)

The extracted content is used to augment the literature review
without disrupting existing text-based ingestion pipelines.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger

# PDF parsing libraries - graceful fallback
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not installed. Install with: pip install pymupdf")

try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    from pdfminer.layout import LAParams
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False
    logger.warning("pdfminer not installed. Install with: pip install pdfminer.six")


@dataclass
class ParsedPaper:
    """Structured representation of a parsed PDF paper."""
    
    file_path: str
    file_hash: str
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    abstract: str = ""
    introduction: str = ""
    methodology: str = ""
    results: str = ""
    discussion: str = ""
    conclusion: str = ""
    references: List[str] = field(default_factory=list)
    full_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    parsed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_literature_source(self) -> Dict[str, Any]:
        """Convert to format compatible with existing literature sources."""
        return {
            "paper_id": self.file_hash[:16],
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "source": "uploaded_pdf",
            "methodology_summary": self.methodology[:500] if self.methodology else "",
            "key_findings": self.results[:500] if self.results else "",
            "citation_count": 0,  # Unknown for uploaded papers
            "doi": self.metadata.get("doi"),
            "url": f"file://{self.file_path}",
        }
    
    def get_citation_text(self, style: str = "harvard") -> str:
        """Generate citation text in specified style."""
        if not self.authors:
            first_author = "Unknown"
        elif len(self.authors) == 1:
            first_author = self.authors[0]
        elif len(self.authors) == 2:
            first_author = f"{self.authors[0]} and {self.authors[1]}"
        else:
            first_author = f"{self.authors[0]} et al."
        
        year = self.year or "n.d."
        
        if style.lower() == "harvard":
            return f"{first_author} ({year}) '{self.title}'"
        elif style.lower() == "apa":
            return f"{first_author} ({year}). {self.title}."
        else:
            return f"{first_author} ({year})"


class PDFIngestionService:
    """
    Service for ingesting and parsing PDF research papers.
    
    Features:
    - Extracts text from PDF files
    - Identifies document sections (abstract, methodology, etc.)
    - Extracts references
    - Caches parsed results
    - Provides structured output compatible with literature agents
    """
    
    UPLOAD_FOLDER = Path("data/uploaded_papers")
    CACHE_FOLDER = Path("data/pdf_cache")
    
    # Section identification patterns
    SECTION_PATTERNS = {
        "abstract": [
            r"(?i)^abstract[\s:]*$",
            r"(?i)^summary[\s:]*$",
        ],
        "introduction": [
            r"(?i)^1\.?\s*introduction",
            r"(?i)^introduction[\s:]*$",
            r"(?i)^i\.?\s*introduction",
        ],
        "methodology": [
            r"(?i)^(?:\d\.?\s*)?(?:research\s+)?method(?:ology)?",
            r"(?i)^(?:\d\.?\s*)?materials?\s+and\s+methods?",
            r"(?i)^(?:\d\.?\s*)?experimental\s+(?:design|setup)",
            r"(?i)^(?:\d\.?\s*)?research\s+design",
        ],
        "results": [
            r"(?i)^(?:\d\.?\s*)?results?(?:\s+and\s+discussion)?",
            r"(?i)^(?:\d\.?\s*)?findings",
            r"(?i)^(?:\d\.?\s*)?experimental\s+results",
        ],
        "discussion": [
            r"(?i)^(?:\d\.?\s*)?discussion",
            r"(?i)^(?:\d\.?\s*)?analysis",
        ],
        "conclusion": [
            r"(?i)^(?:\d\.?\s*)?conclusions?",
            r"(?i)^(?:\d\.?\s*)?concluding\s+remarks",
            r"(?i)^(?:\d\.?\s*)?summary\s+and\s+conclusions?",
        ],
        "references": [
            r"(?i)^references?[\s:]*$",
            r"(?i)^bibliography[\s:]*$",
            r"(?i)^works?\s+cited",
            r"(?i)^literature\s+cited",
        ],
    }
    
    def __init__(self, upload_folder: Optional[str] = None):
        """
        Initialize PDF ingestion service.
        
        Args:
            upload_folder: Custom folder for uploaded PDFs
        """
        self.upload_folder = Path(upload_folder) if upload_folder else self.UPLOAD_FOLDER
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.CACHE_FOLDER.mkdir(parents=True, exist_ok=True)
        
        self.parsed_papers: Dict[str, ParsedPaper] = {}
        
        logger.info(f"PDFIngestionService initialized. Upload folder: {self.upload_folder}")
        logger.info(f"PDF parsing available: PyMuPDF={PYMUPDF_AVAILABLE}, pdfminer={PDFMINER_AVAILABLE}")
    
    def list_uploaded_papers(self) -> List[Path]:
        """List all PDF files in the upload folder."""
        return list(self.upload_folder.glob("*.pdf"))
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    async def ingest_all_papers(self) -> List[ParsedPaper]:
        """
        Ingest all PDF papers from the upload folder.
        
        Returns:
            List of parsed papers
        """
        papers = []
        pdf_files = self.list_uploaded_papers()
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                paper = await self.parse_pdf(pdf_file)
                if paper:
                    papers.append(paper)
                    self.parsed_papers[paper.file_hash] = paper
            except Exception as e:
                logger.error(f"Failed to parse {pdf_file}: {e}")
        
        logger.info(f"Successfully parsed {len(papers)} papers")
        return papers
    
    async def parse_pdf(self, file_path: Path) -> Optional[ParsedPaper]:
        """
        Parse a single PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            ParsedPaper object or None if parsing fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"PDF file not found: {file_path}")
            return None
        
        file_hash = self.get_file_hash(file_path)
        
        # Check cache
        if file_hash in self.parsed_papers:
            logger.info(f"Using cached parse for: {file_path.name}")
            return self.parsed_papers[file_hash]
        
        logger.info(f"Parsing PDF: {file_path.name}")
        
        # Extract text
        full_text = self._extract_text(file_path)
        
        if not full_text:
            logger.warning(f"No text extracted from: {file_path.name}")
            return None
        
        # Extract metadata
        metadata = self._extract_metadata(file_path)
        
        # Identify sections
        sections = self._identify_sections(full_text)
        
        # Extract title and authors
        title, authors = self._extract_title_and_authors(full_text, metadata)
        
        # Extract year
        year = self._extract_year(full_text, metadata)
        
        # Extract references
        references = self._extract_references(sections.get("references", ""))
        
        paper = ParsedPaper(
            file_path=str(file_path),
            file_hash=file_hash,
            title=title,
            authors=authors,
            year=year,
            abstract=sections.get("abstract", ""),
            introduction=sections.get("introduction", ""),
            methodology=sections.get("methodology", ""),
            results=sections.get("results", ""),
            discussion=sections.get("discussion", ""),
            conclusion=sections.get("conclusion", ""),
            references=references,
            full_text=full_text,
            metadata=metadata,
        )
        
        self.parsed_papers[file_hash] = paper
        logger.info(f"Successfully parsed: {title[:50]}...")
        
        return paper
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from PDF using available libraries."""
        
        # Try PyMuPDF first (faster, better formatting)
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                if text.strip():
                    return text
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {e}")
        
        # Fallback to pdfminer
        if PDFMINER_AVAILABLE:
            try:
                laparams = LAParams(
                    line_margin=0.5,
                    word_margin=0.1,
                    char_margin=2.0,
                )
                text = pdfminer_extract(str(file_path), laparams=laparams)
                if text.strip():
                    return text
            except Exception as e:
                logger.warning(f"pdfminer extraction failed: {e}")
        
        logger.error(f"No PDF extraction library available or all failed for: {file_path}")
        return ""
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from PDF."""
        metadata = {}
        
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(file_path)
                metadata = dict(doc.metadata) if doc.metadata else {}
                doc.close()
            except Exception as e:
                logger.warning(f"Metadata extraction failed: {e}")
        
        return metadata
    
    def _identify_sections(self, text: str) -> Dict[str, str]:
        """
        Identify and extract sections from the document text.
        
        Args:
            text: Full document text
            
        Returns:
            Dict mapping section names to their content
        """
        sections = {}
        lines = text.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if line is a section header
            section_found = None
            for section_name, patterns in self.SECTION_PATTERNS.items():
                for pattern in patterns:
                    if re.match(pattern, line_stripped):
                        section_found = section_name
                        break
                if section_found:
                    break
            
            if section_found:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                current_section = section_found
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_title_and_authors(
        self, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """Extract title and authors from text and metadata."""
        
        # Try metadata first
        title = metadata.get("title", "")
        authors = []
        
        if metadata.get("author"):
            author_str = metadata["author"]
            # Split by common delimiters
            authors = re.split(r'[,;]|\band\b', author_str)
            authors = [a.strip() for a in authors if a.strip()]
        
        # If no title in metadata, use first non-empty line
        if not title:
            lines = text.split('\n')
            for line in lines[:20]:  # Check first 20 lines
                line = line.strip()
                if len(line) > 10 and len(line) < 200:
                    # Likely a title
                    title = line
                    break
        
        return title, authors
    
    def _extract_year(self, text: str, metadata: Dict[str, Any]) -> Optional[int]:
        """Extract publication year."""
        
        # Try metadata
        if metadata.get("creationDate"):
            try:
                # PDF date format: D:20231015...
                date_str = metadata["creationDate"]
                if date_str.startswith("D:"):
                    year = int(date_str[2:6])
                    if 1900 <= year <= 2100:
                        return year
            except:
                pass
        
        # Search in text for year patterns
        year_pattern = r'\b(19|20)\d{2}\b'
        matches = re.findall(year_pattern, text[:2000])  # Search in first 2000 chars
        
        if matches:
            # Get most recent year that's not in the future
            current_year = datetime.now().year
            years = [int(m + y[-2:]) for m in matches for y in [text]]
            valid_years = [y for y in years if 1990 <= y <= current_year]
            if valid_years:
                return max(valid_years)
        
        return None
    
    def _extract_references(self, references_text: str) -> List[str]:
        """Extract individual references from references section."""
        if not references_text:
            return []
        
        references = []
        
        # Try to split by numbered references
        numbered = re.split(r'\n\s*\[\d+\]|\n\s*\d+\.\s', references_text)
        if len(numbered) > 3:
            references = [ref.strip() for ref in numbered if len(ref.strip()) > 20]
        else:
            # Split by blank lines or author-year patterns
            refs = re.split(r'\n\s*\n', references_text)
            references = [ref.strip() for ref in refs if len(ref.strip()) > 20]
        
        return references[:100]  # Limit to 100 references
    
    def get_papers_for_literature_review(self) -> List[Dict[str, Any]]:
        """
        Get all parsed papers in format suitable for literature review agent.
        
        Returns:
            List of paper dictionaries compatible with existing literature sources
        """
        return [paper.to_literature_source() for paper in self.parsed_papers.values()]
    
    def get_citations(self, style: str = "harvard") -> List[str]:
        """
        Get formatted citations for all parsed papers.
        
        Args:
            style: Citation style (harvard, apa)
            
        Returns:
            List of formatted citation strings
        """
        return [paper.get_citation_text(style) for paper in self.parsed_papers.values()]
    
    async def save_uploaded_file(self, filename: str, content: bytes) -> Path:
        """
        Save an uploaded PDF file.
        
        Args:
            filename: Original filename
            content: File content bytes
            
        Returns:
            Path to saved file
        """
        # Sanitize filename
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        if not safe_filename.lower().endswith('.pdf'):
            safe_filename += '.pdf'
        
        file_path = self.upload_folder / safe_filename
        
        # Handle duplicates
        counter = 1
        while file_path.exists():
            stem = safe_filename.rsplit('.', 1)[0]
            file_path = self.upload_folder / f"{stem}_{counter}.pdf"
            counter += 1
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Saved uploaded file: {file_path}")
        return file_path


# Global instance
_pdf_service: Optional[PDFIngestionService] = None


def get_pdf_service() -> PDFIngestionService:
    """Get or create the PDF ingestion service instance."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFIngestionService()
    return _pdf_service

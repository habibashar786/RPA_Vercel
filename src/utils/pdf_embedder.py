"""
ResearchAI v2.5.0 - PDF Visualization Embedder Patch
=====================================================
This module provides helper functions to embed Gantt, WBS, and RTM
images into PDF, DOCX, and LaTeX exports.
"""

import io
import logging
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


def generate_all_visualization_images() -> Dict[str, Optional[bytes]]:
    """
    Generate all visualization images (Gantt, WBS, RTM) using the unified generator.
    
    Returns:
        Dict with keys 'gantt', 'wbs', 'rtm' containing PNG bytes or None if failed.
    """
    result = {
        'gantt': None,
        'wbs': None,
        'rtm': None,
    }
    
    try:
        from src.utils.visualization_generator import visualization_generator
        result['gantt'] = visualization_generator.generate_gantt_image()
        result['wbs'] = visualization_generator.generate_wbs_image()
        result['rtm'] = visualization_generator.generate_rtm_image()
        logger.info("All visualization images generated successfully (Gantt, WBS, RTM)")
    except ImportError as e:
        logger.warning(f"Visualization generator not available: {e}")
        # Try legacy gantt generator
        try:
            from src.utils.gantt_generator import gantt_generator
            result['gantt'] = gantt_generator.generate_gantt_image()
            logger.info("Gantt chart generated (legacy)")
        except Exception as e2:
            logger.warning(f"Legacy gantt generator failed: {e2}")
    except Exception as e:
        logger.warning(f"Failed to generate visualizations: {e}")
    
    return result


def embed_image_in_story(
    story: list,
    image_bytes: bytes,
    doc,
    caption: str,
    styles
) -> bool:
    """
    Embed an image into a ReportLab story list.
    
    Args:
        story: The ReportLab story list
        image_bytes: PNG image as bytes
        doc: The SimpleDocTemplate instance
        caption: Figure caption text
        styles: ReportLab getSampleStyleSheet() result
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from reportlab.platypus import Spacer, Paragraph, Image
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        
        img_buffer = io.BytesIO(image_bytes)
        img_width = doc.width
        img_height = img_width * 0.6  # Aspect ratio for WBS/RTM
        
        img = Image(img_buffer, width=img_width, height=img_height)
        story.append(img)
        story.append(Spacer(1, 12))
        
        caption_style = ParagraphStyle(
            'Caption', 
            parent=styles['Normal'], 
            fontSize=10, 
            alignment=TA_CENTER, 
            fontName='Times-Italic'
        )
        story.append(Paragraph(caption, caption_style))
        
        return True
    except Exception as e:
        logger.warning(f"Failed to embed image: {e}")
        return False


def get_appendix_image_config() -> Dict[str, Dict[str, Any]]:
    """
    Get configuration for appendix image embedding.
    
    Returns:
        Dict mapping appendix identifiers to their image config.
    """
    return {
        'APPENDIX B': {
            'key': 'gantt',
            'caption': 'Figure B.1: Research Timeline - Gantt Chart (15 Months)',
            'aspect_ratio': 0.5,
            'keywords': ['GANTT', 'TIMELINE'],
        },
        'APPENDIX C': {
            'key': 'wbs',
            'caption': 'Figure C.1: Work Breakdown Structure (WBS)',
            'aspect_ratio': 0.75,
            'keywords': ['WBS', 'WORK BREAKDOWN', 'BREAKDOWN STRUCTURE'],
        },
        'APPENDIX D': {
            'key': 'rtm',
            'caption': 'Figure D.1: Requirements Traceability Matrix (RTM)',
            'aspect_ratio': 0.7,
            'keywords': ['RTM', 'REQUIREMENTS', 'TRACEABILITY'],
        },
    }


def should_embed_image(title: str, appendix_id: str, config: Dict) -> bool:
    """
    Check if an image should be embedded for the given section title.
    
    Args:
        title: Section title
        appendix_id: Appendix identifier (e.g., 'APPENDIX B')
        config: Configuration dict for this appendix
        
    Returns:
        True if image should be embedded
    """
    if appendix_id not in title:
        return False
    
    title_upper = title.upper()
    return any(keyword in title_upper for keyword in config.get('keywords', []))

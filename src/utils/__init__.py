"""
ResearchAI Utils Module v2.5.0
==============================
Utility functions and generators for the ResearchAI system.

Features:
- Gantt Chart Generation
- Work Breakdown Structure (WBS) Visualization
- Requirements Traceability Matrix (RTM) Generation
- Unified Visualization Pipeline
"""

from .gantt_generator import (
    gantt_generator, 
    generate_gantt_for_pdf, 
    generate_gantt_base64_for_html
)

from .visualization_generator import (
    visualization_generator,
    generate_gantt_for_pdf as generate_gantt_v2,
    generate_wbs_for_pdf,
    generate_rtm_for_pdf,
    generate_all_visualizations,
    DAVINCI_PALETTE,
    PHASE_COLORS,
)

__all__ = [
    # Legacy gantt generator
    'gantt_generator',
    'generate_gantt_for_pdf',
    'generate_gantt_base64_for_html',
    # New unified visualization generator
    'visualization_generator',
    'generate_gantt_v2',
    'generate_wbs_for_pdf',
    'generate_rtm_for_pdf',
    'generate_all_visualizations',
    'DAVINCI_PALETTE',
    'PHASE_COLORS',
]

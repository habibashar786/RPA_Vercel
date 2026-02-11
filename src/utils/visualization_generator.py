"""
ResearchAI v2.5.0 - Unified Visualization Generator
====================================================
Generates professional visualizations for all appendices:
- Gantt Chart (Appendix B)
- Work Breakdown Structure (Appendix C)
- Requirements Traceability Matrix (Appendix D)

Design Philosophy: Leonardo da Vinci inspired - clarity, precision, elegance
Architecture: Multi-agent compatible, state-of-the-art AI/ML integration
"""

import io
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import base64

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for server
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
    from matplotlib.lines import Line2D
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# =============================================================================
# Color Palette - Leonardo da Vinci Inspired (Renaissance Earth Tones + Modern)
# =============================================================================
DAVINCI_PALETTE = {
    "primary": "#2c3e50",      # Deep charcoal (like his sfumato shadows)
    "secondary": "#8b7355",    # Warm sepia (manuscript tone)
    "accent1": "#c9a66b",      # Golden ochre (his favorite)
    "accent2": "#6b8e7a",      # Muted sage green (nature studies)
    "accent3": "#9b7653",      # Terra cotta (Italian earth)
    "accent4": "#5d6d7e",      # Cool slate blue (sky studies)
    "background": "#faf8f5",   # Aged parchment
    "text": "#1a1a1a",         # Deep ink
    "grid": "#e8e4df",         # Subtle grid
    "success": "#27ae60",      # Modern green for status
    "warning": "#f39c12",      # Amber warning
    "complete": "#2ecc71",     # Complete status
}

# Phase colors - gradient from warm to cool (visual flow)
PHASE_COLORS = [
    "#6366f1",  # Indigo
    "#8b5cf6",  # Purple
    "#a855f7",  # Violet
    "#d946ef",  # Fuchsia
    "#ec4899",  # Pink
    "#f43f5e",  # Rose
    "#ef4444",  # Red
    "#22c55e",  # Green
    "#14b8a6",  # Teal
]


class UnifiedVisualizationGenerator:
    """
    Unified visualization generator for all research proposal appendices.
    
    Implements:
    - Precision Effect: Exact, calibrated outputs
    - Design Thinking: User-centric visual hierarchy
    - Leonardo's Principles: Clarity, proportion, elegance
    """
    
    # ==========================================================================
    # Default Data Structures
    # ==========================================================================
    
    DEFAULT_GANTT_PHASES = [
        {"name": "Literature Review & Gap Analysis", "start": 1, "duration": 3, "color": PHASE_COLORS[0]},
        {"name": "Research Design & Methodology", "start": 2, "duration": 2, "color": PHASE_COLORS[1]},
        {"name": "Data Collection Framework", "start": 4, "duration": 3, "color": PHASE_COLORS[2]},
        {"name": "Data Preprocessing & Cleaning", "start": 6, "duration": 2, "color": PHASE_COLORS[3]},
        {"name": "Model Development & Training", "start": 7, "duration": 4, "color": PHASE_COLORS[4]},
        {"name": "Validation & Testing", "start": 10, "duration": 2, "color": PHASE_COLORS[5]},
        {"name": "Results Analysis & Interpretation", "start": 11, "duration": 2, "color": PHASE_COLORS[6]},
        {"name": "Documentation & Thesis Writing", "start": 3, "duration": 10, "color": PHASE_COLORS[7]},
        {"name": "Publication & Dissemination", "start": 12, "duration": 3, "color": PHASE_COLORS[8]},
    ]
    
    DEFAULT_WBS_STRUCTURE = {
        "1.0": {
            "name": "Research Proposal",
            "children": {
                "1.1": {
                    "name": "Problem Definition",
                    "deliverables": [
                        ("1.1.1", "Background Study", "Context Report"),
                        ("1.1.2", "Problem Statement", "Problem Definition Document"),
                        ("1.1.3", "Research Objectives", "Objectives List"),
                    ]
                },
                "1.2": {
                    "name": "Literature Review",
                    "deliverables": [
                        ("1.2.1", "Source Collection", "Bibliography Database"),
                        ("1.2.2", "Critical Analysis", "Analysis Report"),
                        ("1.2.3", "Gap Identification", "Gap Matrix"),
                    ]
                },
                "1.3": {
                    "name": "Research Methodology",
                    "deliverables": [
                        ("1.3.1", "Research Design", "Design Document"),
                        ("1.3.2", "Data Collection Plan", "Collection Protocol"),
                        ("1.3.3", "Analysis Strategy", "Analysis Plan"),
                        ("1.3.4", "Validation Approach", "Validation Framework"),
                    ]
                },
                "1.4": {
                    "name": "Implementation",
                    "deliverables": [
                        ("1.4.1", "Data Preprocessing", "Clean Dataset"),
                        ("1.4.2", "Model Development", "Trained Model"),
                        ("1.4.3", "Testing & Validation", "Test Results"),
                    ]
                },
                "1.5": {
                    "name": "Documentation",
                    "deliverables": [
                        ("1.5.1", "Results Documentation", "Results Chapter"),
                        ("1.5.2", "Discussion", "Discussion Chapter"),
                        ("1.5.3", "Conclusions", "Conclusions Chapter"),
                    ]
                },
            }
        }
    }
    
    DEFAULT_RTM_REQUIREMENTS = [
        {"id": "REQ-001", "description": "Identify and analyze research gaps", "source": "Chapter 1 (1.2)", "agent": "LiteratureReviewAgent", "status": "Complete"},
        {"id": "REQ-002", "description": "Establish theoretical framework", "source": "Chapter 1 (1.3)", "agent": "LiteratureReviewAgent", "status": "Complete"},
        {"id": "REQ-003", "description": "Design appropriate methodology", "source": "Chapter 1 (1.3)", "agent": "MethodologyAgent", "status": "Complete"},
        {"id": "REQ-004", "description": "Define data collection strategy", "source": "Chapter 3 (3.3)", "agent": "MethodologyAgent", "status": "Complete"},
        {"id": "REQ-005", "description": "Develop and validate model", "source": "Chapter 3 (3.7)", "agent": "MethodologyOptimizerAgent", "status": "Complete"},
        {"id": "REQ-006", "description": "Ensure ethical compliance", "source": "Chapter 3 (3.12)", "agent": "RiskAssessmentAgent", "status": "Complete"},
        {"id": "REQ-007", "description": "Generate proper citations", "source": "Academic Standards", "agent": "ReferenceCitationAgent", "status": "Complete"},
        {"id": "REQ-008", "description": "Produce Q1 journal-standard doc", "source": "Quality Standards", "agent": "QualityAssuranceAgent", "status": "Complete"},
    ]
    
    def __init__(self):
        self.gantt_phases = self.DEFAULT_GANTT_PHASES
        self.wbs_structure = self.DEFAULT_WBS_STRUCTURE
        self.rtm_requirements = self.DEFAULT_RTM_REQUIREMENTS
    
    # ==========================================================================
    # GANTT CHART GENERATOR - v2.5.8 Dynamic Subscription-Aware Timeline
    # ==========================================================================
    
    def generate_gantt_image(self, 
                              title: str = "Research Timeline",
                              phases: List[Dict] = None,
                              figsize: Tuple[int, int] = (16, 10),
                              dpi: int = 150,
                              subscription_type: str = "proposal") -> bytes:
        """Generate professional Gantt chart with dynamic dates and subscription awareness.
        
        v2.5.8 Features:
        - Dynamic dates from current system date
        - Subscription-aware duration:
          * proposal = 4 weeks
          * interim = 12 weeks  
          * thesis = 24 weeks
        - Completion percentage display
        - Filled vs shaded progress bars
        - Dynamic figure title based on subscription
        
        Args:
            title: Base title (will be enhanced with subscription info)
            phases: Optional custom phases
            figsize: Figure size tuple
            dpi: Resolution
            subscription_type: 'proposal' | 'interim' | 'thesis'
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for visualization generation")
        
        from datetime import datetime, timedelta
        
        # =================================================================
        # SUBSCRIPTION-DRIVEN TIMELINE CONFIGURATION
        # =================================================================
        subscription_config = {
            "proposal": {"weeks": 4, "label": "Proposal", "months": 1},
            "interim": {"weeks": 12, "label": "Interim Report", "months": 3},
            "thesis": {"weeks": 24, "label": "Thesis", "months": 6},
        }
        
        config = subscription_config.get(subscription_type.lower(), subscription_config["proposal"])
        total_weeks = config["weeks"]
        timeline_label = config["label"]
        
        # =================================================================
        # DYNAMIC DATE CALCULATION (Current date as baseline)
        # =================================================================
        start_date = datetime.now()
        
        # Generate week labels dynamically from current date
        week_dates = []
        for i in range(total_weeks):
            week_start = start_date + timedelta(weeks=i)
            week_dates.append(week_start.strftime("%d %b"))
        
        # Generate month headers dynamically
        months = []
        current_month = start_date.month
        current_year = start_date.year
        week_idx = 0
        
        while week_idx < total_weeks:
            month_start_week = week_idx
            month_name = (start_date + timedelta(weeks=week_idx)).strftime("%b, %Y")
            weeks_in_month = 0
            
            # Count weeks in this month
            while week_idx < total_weeks:
                check_date = start_date + timedelta(weeks=week_idx)
                if check_date.month != (start_date + timedelta(weeks=month_start_week)).month:
                    break
                weeks_in_month += 1
                week_idx += 1
            
            if weeks_in_month > 0:
                months.append({"name": month_name, "weeks": weeks_in_month, "start": month_start_week})
        
        # =================================================================
        # TASK DEFINITIONS WITH DYNAMIC SCHEDULING
        # =================================================================
        # Scale task timings based on subscription duration
        scale_factor = total_weeks / 16  # Base is 16 weeks
        
        def scale_week(week):
            return max(1, min(total_weeks, int(week * scale_factor)))
        
        # Task colors for visual distinction
        task_colors = [
            "#1E90FF",  # Dodger Blue
            "#4169E1",  # Royal Blue
            "#32CD32",  # Lime Green
            "#DAA520",  # Goldenrod
            "#9ACD32",  # Yellow Green
            "#00CED1",  # Dark Turquoise
            "#4682B4",  # Steel Blue
            "#228B22",  # Forest Green
            "#BA55D3",  # Medium Orchid
            "#2E8B57",  # Sea Green
        ]
        
        # Define tasks with completion percentages
        tasks = [
            {"id": 1, "name": "PROBLEM STATEMENT", "start_week": scale_week(1), "end_week": scale_week(4), "progress": 100, "color": task_colors[0]},
            {"id": 2, "name": "AIMS AND OBJECTIVES", "start_week": scale_week(2), "end_week": scale_week(5), "progress": 100, "color": task_colors[1]},
            {"id": 3, "name": "BACKGROUND", "start_week": scale_week(4), "end_week": scale_week(8), "progress": 100, "color": task_colors[2]},
            {"id": 4, "name": "SIGNIFICANCE OF STUDY", "start_week": scale_week(5), "end_week": scale_week(9), "progress": 100, "color": task_colors[3]},
            {"id": 5, "name": "SCOPE OF STUDY", "start_week": scale_week(6), "end_week": scale_week(9), "progress": 100, "color": task_colors[4]},
            {"id": 6, "name": "ABSTRACT", "start_week": scale_week(8), "end_week": scale_week(10), "progress": 100, "color": task_colors[5]},
            {"id": 7, "name": "RESEARCH METHODOLOGY", "start_week": scale_week(9), "end_week": scale_week(13), "progress": 100, "color": task_colors[6]},
            {"id": 8, "name": "REQUIREMENT RESOURCES", "start_week": scale_week(10), "end_week": scale_week(15), "progress": 100, "color": task_colors[7]},
            {"id": 9, "name": "RESEARCH PLAN", "start_week": scale_week(5), "end_week": scale_week(9), "progress": 100, "color": task_colors[8]},
            {"id": 10, "name": "REFERENCES", "start_week": scale_week(12), "end_week": scale_week(16), "progress": 100, "color": task_colors[9]},
        ]
        
        # Ensure end_week doesn't exceed total_weeks
        for task in tasks:
            task["end_week"] = min(task["end_week"], total_weeks)
            task["start_week"] = min(task["start_week"], total_weeks - 1)
        
        # =================================================================
        # CREATE FIGURE
        # =================================================================
        fig = plt.figure(figsize=figsize, facecolor='white')
        ax = fig.add_subplot(111)
        ax.set_facecolor('white')
        
        # Layout parameters
        n_tasks = len(tasks)
        row_height = 0.8
        
        # Column widths - adjust based on total weeks
        id_col_width = 1.5
        name_col_width = 8
        week_col_width = max(1.5, 32 / total_weeks)  # Scale width based on weeks
        total_timeline_width = total_weeks * week_col_width
        
        # =================================================================
        # DRAW HEADERS
        # =================================================================
        month_header_y = n_tasks + 1.5
        week_header_y = n_tasks + 0.7
        timeline_start = id_col_width + name_col_width
        
        # ID column header
        ax.add_patch(Rectangle((0, n_tasks + 0.2), id_col_width, 2.0,
                               facecolor='#4A5568', edgecolor='#2D3748', linewidth=1))
        ax.text(id_col_width/2, n_tasks + 1.2, 'ID', ha='center', va='center',
               fontsize=10, fontweight='bold', color='white')
        
        # Name column header
        ax.add_patch(Rectangle((id_col_width, n_tasks + 0.2), name_col_width, 2.0,
                               facecolor='#4A5568', edgecolor='#2D3748', linewidth=1))
        ax.text(id_col_width + name_col_width/2, n_tasks + 1.2, 'Name', ha='center', va='center',
               fontsize=10, fontweight='bold', color='white')
        
        # Month headers (dynamic)
        for month in months:
            month_x = timeline_start + month["start"] * week_col_width
            month_width = month["weeks"] * week_col_width
            
            ax.add_patch(Rectangle((month_x, month_header_y), month_width, 0.8,
                                   facecolor='#4A5568', edgecolor='#2D3748', linewidth=1))
            ax.text(month_x + month_width/2, month_header_y + 0.4, month["name"],
                   ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        
        # Week headers (dynamic dates)
        for week_idx in range(total_weeks):
            week_x = timeline_start + week_idx * week_col_width
            
            ax.add_patch(Rectangle((week_x, week_header_y), week_col_width, 0.8,
                                   facecolor='#E2E8F0', edgecolor='#CBD5E0', linewidth=0.5))
            ax.text(week_x + week_col_width/2, week_header_y + 0.4, week_dates[week_idx],
                   ha='center', va='center', fontsize=6, color='#4A5568')
        
        # =================================================================
        # DRAW TASK ROWS WITH PROGRESS BARS
        # =================================================================
        for task_idx, task in enumerate(tasks):
            row_y = n_tasks - task_idx - 1
            row_bg = 'white' if task_idx % 2 == 0 else '#F7FAFC'
            
            # ID cell
            ax.add_patch(Rectangle((0, row_y), id_col_width, row_height,
                                   facecolor=row_bg, edgecolor='#E2E8F0', linewidth=0.5))
            ax.text(id_col_width/2, row_y + row_height/2, str(task["id"]),
                   ha='center', va='center', fontsize=9, fontweight='bold', color='#2D3748')
            
            # Name cell (without percentage - percentage is now inside the bar)
            ax.add_patch(Rectangle((id_col_width, row_y), name_col_width, row_height,
                                   facecolor=row_bg, edgecolor='#E2E8F0', linewidth=0.5))
            
            # Task name only (no percentage here)
            ax.text(id_col_width + 0.3, row_y + row_height/2, task['name'],
                   ha='left', va='center', fontsize=7.5, color='#2D3748')
            
            # Timeline cells (weekly grid)
            for week_idx in range(total_weeks):
                week_x = timeline_start + week_idx * week_col_width
                ax.add_patch(Rectangle((week_x, row_y), week_col_width, row_height,
                                       facecolor=row_bg, edgecolor='#EDF2F7', linewidth=0.3))
            
            # Task bar
            bar_start_x = timeline_start + (task["start_week"] - 1) * week_col_width
            bar_width = (task["end_week"] - task["start_week"] + 1) * week_col_width
            bar_y = row_y + 0.15
            bar_height = row_height - 0.3
            
            # Calculate progress width
            progress_width = bar_width * (task["progress"] / 100)
            remaining_width = bar_width - progress_width
            
            # Background bar (unfilled/remaining - light gray with stripes effect)
            ax.add_patch(Rectangle((bar_start_x, bar_y), bar_width, bar_height,
                                   facecolor='#E2E8F0', edgecolor='none', linewidth=0, zorder=2))
            
            # Progress bar (filled - task color)
            if progress_width > 0:
                ax.add_patch(Rectangle((bar_start_x, bar_y), progress_width, bar_height,
                                       facecolor=task["color"], edgecolor='none', linewidth=0, zorder=3))
            
            # Bar border
            ax.add_patch(Rectangle((bar_start_x, bar_y), bar_width, bar_height,
                                   facecolor='none', edgecolor='#718096', linewidth=0.8, zorder=4))
            
            # v2.5.9: Percentage text INSIDE the progress bar (black color)
            bar_center_x = bar_start_x + bar_width / 2
            bar_center_y = bar_y + bar_height / 2
            ax.text(bar_center_x, bar_center_y, f"{task['progress']}%",
                   ha='center', va='center', fontsize=8, fontweight='bold', 
                   color='black', zorder=5)
        
        # =================================================================
        # SET AXIS LIMITS AND TITLE
        # =================================================================
        total_width = id_col_width + name_col_width + total_timeline_width
        ax.set_xlim(0, total_width)
        ax.set_ylim(-0.5, n_tasks + 2.5)
        ax.axis('off')
        
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        plt.close(fig)
        
        return buffer.getvalue()
    
    def get_gantt_figure_title(self, subscription_type: str = "proposal") -> str:
        """Generate dynamic figure title based on subscription type.
        
        Returns:
            Formatted figure title string
        """
        titles = {
            "proposal": "Figure B.1: Research Timeline – Proposal (4 Weeks)",
            "interim": "Figure B.1: Research Timeline – Interim Report (12 Weeks)",
            "thesis": "Figure B.1: Research Timeline – Thesis (24 Weeks)",
        }
        return titles.get(subscription_type.lower(), titles["proposal"])
    
    # ==========================================================================
    # WORK BREAKDOWN STRUCTURE (WBS) GENERATOR
    # ==========================================================================
    
    def generate_wbs_image(self,
                           title: str = None,  # REMOVED: No background title
                           structure: Dict = None,
                           figsize: Tuple[int, int] = (16, 12),
                           dpi: int = 150) -> bytes:
        """Generate hierarchical WBS diagram with high-contrast, readable text.
        
        FIXES APPLIED (v2.5.2):
        - REMOVED background "Work Breakdown Structure (WBS)" title text
        - Root node "1.0 Research Proposal" is the only header
        - Clean, uncluttered design matching reference image
        - WCAG AA compliance maintained
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for visualization generation")
        
        if structure is None:
            structure = self.wbs_structure
            
        fig, ax = plt.subplots(figsize=figsize, facecolor=DAVINCI_PALETTE["background"])
        ax.set_facecolor(DAVINCI_PALETTE["background"])
        ax.axis('off')
        
        # HIGH CONTRAST COLOR SCHEME (WCAG AA Compliant)
        HIGH_CONTRAST = {
            "root_bg": "#1e3a5f",      # Deep navy for root (high contrast)
            "root_text": "#ffffff",    # Pure white text
            "level1_bg": "#c9a66b",    # Golden ochre
            "level1_text": "#1a1a1a",  # Dark text on light bg
            "level2_bg": "#ffffff",    # White background
            "level2_text": "#1a1a1a",  # Dark text
            "level2_border": "#5d6d7e", # Slate border
            "deliverable_text": "#4a5568",  # Medium gray for deliverables
            "connector": "#94a3b8",    # Light slate for lines
        }
        
        def draw_box(x, y, width, height, text, level=0, deliverable=None):
            """Draw a styled box with HIGH CONTRAST text."""
            
            # Select colors based on level
            if level == 0:  # Root
                bg_color = HIGH_CONTRAST["root_bg"]
                text_color = HIGH_CONTRAST["root_text"]
                border_color = HIGH_CONTRAST["root_bg"]
            elif level == 1:  # Level 1 children
                bg_color = HIGH_CONTRAST["level1_bg"]
                text_color = HIGH_CONTRAST["level1_text"]
                border_color = HIGH_CONTRAST["level1_bg"]
            else:  # Level 2+ deliverables
                bg_color = HIGH_CONTRAST["level2_bg"]
                text_color = HIGH_CONTRAST["level2_text"]
                border_color = HIGH_CONTRAST["level2_border"]
            
            # Shadow (subtle)
            shadow = FancyBboxPatch((x+0.01, y-0.01), width, height,
                                   boxstyle="round,pad=0.02,rounding_size=0.02",
                                   facecolor='#00000010', edgecolor='none')
            ax.add_patch(shadow)
            
            # Main box with solid background
            box = FancyBboxPatch((x, y), width, height,
                                boxstyle="round,pad=0.02,rounding_size=0.02",
                                facecolor=bg_color,
                                edgecolor=border_color, linewidth=2)
            ax.add_patch(box)
            
            # Text with high contrast - NEVER use gray on dark backgrounds
            fontsize = 11 if level == 0 else (9 if level == 1 else 8)
            fontweight = 'bold'
            
            ax.text(x + width/2, y + height/2, text, ha='center', va='center',
                   fontsize=fontsize, fontweight=fontweight, color=text_color,
                   wrap=True, zorder=10)  # High z-order ensures text is on top
            
            # Deliverable text (only for level 2)
            if deliverable and level >= 2:
                ax.text(x + width/2, y + 0.01, f"→ {deliverable}",
                       ha='center', va='bottom', fontsize=6, 
                       color=HIGH_CONTRAST["deliverable_text"], style='italic')
        
        def draw_connector(x1, y1, x2, y2):
            """Draw connector line with good visibility."""
            mid_y = (y1 + y2) / 2
            ax.plot([x1, x1, x2, x2], [y1, mid_y, mid_y, y2], 
                   color=HIGH_CONTRAST["connector"], linewidth=1.5, zorder=0)
        
        # ===== ROOT NODE (1.0 Research Proposal) =====
        # This is the ONLY header - no background "WBS" text
        # Position at top center of diagram
        root_width, root_height = 0.28, 0.06
        root_x = 0.36  # Centered
        root_y = 0.92  # Moved up since no background title
        draw_box(root_x, root_y, root_width, root_height, "1.0 Research Proposal", level=0)
        
        # ===== LEVEL 1 CHILDREN =====
        level1_y = 0.78
        level1_items = list(structure["1.0"]["children"].items())
        n_items = len(level1_items)
        level1_width = 0.85 / n_items
        
        for i, (code, data) in enumerate(level1_items):
            # Calculate x position for even distribution
            x = 0.075 + i * level1_width
            box_width = level1_width * 0.85
            
            # Draw level 1 box
            draw_box(x, level1_y, box_width, 0.065, f"{code}\n{data['name']}", level=1)
            
            # Connect to root
            draw_connector(root_x + root_width/2, root_y, 
                          x + box_width/2, level1_y + 0.065)
            
            # ===== LEVEL 2 DELIVERABLES =====
            deliverables = data.get('deliverables', [])
            if deliverables:
                del_height = 0.055
                start_y = level1_y - 0.10
                
                for j, (del_code, del_name, del_output) in enumerate(deliverables):
                    del_y = start_y - j * 0.08
                    del_width = box_width * 1.0
                    del_x = x
                    
                    # Draw deliverable box
                    draw_box(del_x, del_y, del_width, del_height, 
                            f"{del_code} {del_name}", level=2, deliverable=del_output)
                    
                    # Connect to parent
                    draw_connector(x + box_width/2, level1_y, 
                                  del_x + del_width/2, del_y + del_height)
        
        # ===== NO BACKGROUND TITLE =====
        # v2.5.2: Removed "Work Breakdown Structure (WBS)" background text
        # The root node "1.0 Research Proposal" is the only header
        # This matches the reference image exactly
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight',
                   facecolor=DAVINCI_PALETTE["background"], edgecolor='none')
        buffer.seek(0)
        plt.close(fig)
        
        return buffer.getvalue()
    
    # ==========================================================================
    # REQUIREMENTS TRACEABILITY MATRIX (RTM) GENERATOR
    # ==========================================================================
    
    def generate_rtm_image(self,
                           title: str = "Requirements Traceability Matrix (RTM)",
                           requirements: List[Dict] = None,
                           figsize: Tuple[int, int] = (14, 10),
                           dpi: int = 150) -> bytes:
        """Generate professional RTM table visualization.
        
        v2.5.4 FIX: Removed background title text that was appearing behind
        the header row. Title now only appears ABOVE the table, not behind it.
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for visualization generation")
        
        if requirements is None:
            requirements = self.rtm_requirements
            
        fig, ax = plt.subplots(figsize=figsize, facecolor=DAVINCI_PALETTE["background"])
        ax.set_facecolor(DAVINCI_PALETTE["background"])
        ax.axis('off')
        
        # Table dimensions
        n_rows = len(requirements) + 1  # +1 for header
        n_cols = 5
        cell_height = 0.08
        col_widths = [0.10, 0.30, 0.18, 0.22, 0.12]  # REQ ID, Description, Source, Agent, Status
        
        # v2.5.4: Title at TOP of figure, ABOVE the table
        # This is the ONLY title - no background text
        ax.text(0.5, 0.97, title, ha='center', va='top', fontsize=18,
               fontweight='bold', color=DAVINCI_PALETTE["primary"], style='italic',
               transform=ax.transAxes, zorder=1)
        
        # Start table BELOW the title (moved down from 0.85 to 0.82)
        start_y = 0.82
        start_x = 0.04
        
        # Header
        headers = ["REQ ID", "Description", "Source", "Delivered By", "Status"]
        x = start_x
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            rect = FancyBboxPatch((x, start_y), width - 0.005, cell_height,
                                 boxstyle="round,pad=0.01,rounding_size=0.01",
                                 facecolor=DAVINCI_PALETTE["primary"],
                                 edgecolor=DAVINCI_PALETTE["primary"], linewidth=1)
            ax.add_patch(rect)
            ax.text(x + width/2, start_y + cell_height/2, header, ha='center', va='center',
                   fontsize=9, fontweight='bold', color='white')
            x += width
        
        # Data rows
        for row_idx, req in enumerate(requirements):
            y = start_y - (row_idx + 1) * (cell_height + 0.01)
            x = start_x
            
            row_color = DAVINCI_PALETTE["background"] if row_idx % 2 == 0 else '#f5f3f0'
            
            row_data = [req["id"], req["description"], req["source"], req["agent"], req["status"]]
            
            for col_idx, (data, width) in enumerate(zip(row_data, col_widths)):
                # Cell background
                rect = Rectangle((x, y), width - 0.005, cell_height,
                                facecolor=row_color,
                                edgecolor=DAVINCI_PALETTE["grid"], linewidth=0.5)
                ax.add_patch(rect)
                
                # Status column special formatting
                if col_idx == 4:  # Status column
                    status_color = DAVINCI_PALETTE["complete"] if "Complete" in data else DAVINCI_PALETTE["warning"]
                    status_symbol = "✓" if "Complete" in data else "○"
                    ax.text(x + width/2, y + cell_height/2, status_symbol, ha='center', va='center',
                           fontsize=12, fontweight='bold', color=status_color)
                else:
                    fontsize = 7 if col_idx == 1 else 8
                    ax.text(x + width/2, y + cell_height/2, data, ha='center', va='center',
                           fontsize=fontsize, color=DAVINCI_PALETTE["text"], wrap=True)
                x += width
        
        # Summary box
        summary_y = start_y - (len(requirements) + 2) * (cell_height + 0.01)
        completed = sum(1 for r in requirements if "Complete" in r["status"])
        total = len(requirements)
        
        summary_box = FancyBboxPatch((start_x, summary_y), 0.92, cell_height * 1.5,
                                    boxstyle="round,pad=0.02,rounding_size=0.02",
                                    facecolor=DAVINCI_PALETTE["accent2"],
                                    edgecolor=DAVINCI_PALETTE["accent2"], linewidth=2)
        ax.add_patch(summary_box)
        
        ax.text(start_x + 0.46, summary_y + cell_height * 0.75,
               f"Total Requirements: {total}  |  Completed: {completed} ({completed/total*100:.0f}%)  |  Status: All requirements traced ✓",
               ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        
        # v2.5.4: Title is now drawn FIRST at top of figure (line ~420)
        # NO duplicate title here - this was causing background text issue
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight',
                   facecolor=DAVINCI_PALETTE["background"], edgecolor='none')
        buffer.seek(0)
        plt.close(fig)
        
        return buffer.getvalue()
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def generate_all_images(self) -> Dict[str, bytes]:
        """Generate all visualization images at once."""
        return {
            "gantt": self.generate_gantt_image(),
            "wbs": self.generate_wbs_image(),
            "rtm": self.generate_rtm_image(),
        }
    
    def generate_base64(self, image_type: str) -> str:
        """Generate base64 encoded image for HTML embedding."""
        generators = {
            "gantt": self.generate_gantt_image,
            "wbs": self.generate_wbs_image,
            "rtm": self.generate_rtm_image,
        }
        if image_type not in generators:
            raise ValueError(f"Unknown image type: {image_type}")
        png_bytes = generators[image_type]()
        return base64.b64encode(png_bytes).decode('utf-8')


# =============================================================================
# Singleton Instance
# =============================================================================
visualization_generator = UnifiedVisualizationGenerator()


# =============================================================================
# Helper Functions
# =============================================================================
def generate_gantt_for_pdf(subscription_type: str = "proposal") -> bytes:
    """Generate Gantt chart for PDF embedding.
    
    Args:
        subscription_type: 'proposal' (4 weeks) | 'interim' (12 weeks) | 'thesis' (24 weeks)
    """
    return visualization_generator.generate_gantt_image(subscription_type=subscription_type)


def get_gantt_title(subscription_type: str = "proposal") -> str:
    """Get dynamic figure title for Gantt chart."""
    return visualization_generator.get_gantt_figure_title(subscription_type)


def generate_wbs_for_pdf() -> bytes:
    """Generate WBS diagram for PDF embedding."""
    return visualization_generator.generate_wbs_image()


def generate_rtm_for_pdf() -> bytes:
    """Generate RTM table for PDF embedding."""
    return visualization_generator.generate_rtm_image()


def generate_all_visualizations() -> Dict[str, bytes]:
    """Generate all visualization images."""
    return visualization_generator.generate_all_images()

"""
ResearchAI v2.4.0 - Gantt Chart Generator
==========================================
Generates professional Gantt chart images for PDF/DOCX appendix.
Uses matplotlib to create publication-quality timeline visualizations.
"""

import io
from typing import List, Dict, Tuple
from datetime import datetime
import base64

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class GanttChartGenerator:
    """Generates professional Gantt chart images for research proposals."""
    
    # Research phases with timeline
    DEFAULT_PHASES = [
        {"name": "Literature Review & Gap Analysis", "start": 1, "duration": 3, "color": "#6366f1"},
        {"name": "Research Design & Methodology", "start": 2, "duration": 2, "color": "#8b5cf6"},
        {"name": "Data Collection Framework", "start": 4, "duration": 3, "color": "#a855f7"},
        {"name": "Data Preprocessing & Cleaning", "start": 6, "duration": 2, "color": "#d946ef"},
        {"name": "Model Development & Training", "start": 7, "duration": 4, "color": "#ec4899"},
        {"name": "Validation & Testing", "start": 10, "duration": 2, "color": "#f43f5e"},
        {"name": "Results Analysis & Interpretation", "start": 11, "duration": 2, "color": "#ef4444"},
        {"name": "Documentation & Thesis Writing", "start": 3, "duration": 10, "color": "#22c55e"},
        {"name": "Publication & Dissemination", "start": 12, "duration": 3, "color": "#14b8a6"},
    ]
    
    def __init__(self):
        self.phases = self.DEFAULT_PHASES
        
    def generate_gantt_image(self, 
                              title: str = "Research Timeline (15 Months)",
                              phases: List[Dict] = None,
                              figsize: Tuple[int, int] = (14, 8),
                              dpi: int = 150) -> bytes:
        """
        Generate a Gantt chart image as PNG bytes.
        
        Args:
            title: Chart title
            phases: List of phase dictionaries with name, start, duration, color
            figsize: Figure size in inches
            dpi: Resolution
            
        Returns:
            PNG image as bytes
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for Gantt chart generation")
        
        if phases is None:
            phases = self.phases
            
        # Create figure
        fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        
        # Set up the chart
        ax.set_facecolor('#f8fafc')
        
        # Add grid
        ax.set_axisbelow(True)
        ax.xaxis.grid(True, linestyle='--', alpha=0.7, color='#e2e8f0')
        ax.yaxis.grid(False)
        
        # Plot bars
        y_positions = range(len(phases))
        bar_height = 0.6
        
        for i, phase in enumerate(phases):
            # Create bar
            ax.barh(i, phase['duration'], left=phase['start'], height=bar_height,
                   color=phase['color'], alpha=0.85, edgecolor='white', linewidth=1.5)
            
            # Add phase name inside or beside the bar
            text_x = phase['start'] + phase['duration'] / 2
            ax.text(text_x, i, phase['name'], ha='center', va='center',
                   fontsize=9, fontweight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor=phase['color'], alpha=0.9))
        
        # Configure axes
        ax.set_yticks(y_positions)
        ax.set_yticklabels([f"Phase {i+1}" for i in range(len(phases))], fontsize=10)
        
        # X-axis: months
        max_month = max(p['start'] + p['duration'] for p in phases)
        ax.set_xlim(0, max_month + 1)
        ax.set_xticks(range(0, max_month + 2))
        ax.set_xticklabels([f"M{i}" if i > 0 else "" for i in range(max_month + 2)], fontsize=9)
        ax.set_xlabel("Timeline (Months)", fontsize=11, fontweight='bold')
        
        # Invert y-axis to show first phase at top
        ax.invert_yaxis()
        
        # Title
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color='#1e293b')
        
        # Add legend
        legend_elements = [mpatches.Patch(facecolor=p['color'], label=p['name'], alpha=0.85) 
                         for p in phases]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.0, -0.1),
                 ncol=3, fontsize=8, frameon=True, fancybox=True, shadow=True)
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.25)
        
        # Save to bytes
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        plt.close(fig)
        
        return buffer.getvalue()
    
    def generate_gantt_base64(self, **kwargs) -> str:
        """Generate Gantt chart as base64 encoded string."""
        png_bytes = self.generate_gantt_image(**kwargs)
        return base64.b64encode(png_bytes).decode('utf-8')
    
    def generate_simple_text_gantt(self) -> str:
        """Generate a text-based Gantt chart for non-image contexts."""
        lines = ["Research Timeline (15 Months)", "=" * 60, ""]
        
        for i, phase in enumerate(self.phases, 1):
            start = phase['start']
            end = start + phase['duration']
            bar = "░" * (start - 1) + "█" * phase['duration'] + "░" * (15 - end + 1)
            lines.append(f"Phase {i}: {phase['name']}")
            lines.append(f"  Months {start}-{end}: [{bar}]")
            lines.append("")
        
        return "\n".join(lines)


# Singleton instance
gantt_generator = GanttChartGenerator()


def generate_gantt_for_pdf() -> bytes:
    """Helper function to generate Gantt chart for PDF embedding."""
    return gantt_generator.generate_gantt_image()


def generate_gantt_base64_for_html() -> str:
    """Helper function to generate Gantt chart for HTML embedding."""
    return gantt_generator.generate_gantt_base64()

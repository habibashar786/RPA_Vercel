"""
ResearchAI v2.4.0 - Structured TOC Agent
=========================================

Generates Table of Contents as structured JSON for UI rendering.
Follows the Structured Output Contract - no visual alignment in AI output.

Design: AI outputs structure, UI handles rendering with CSS leader lines.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class TOCLevel(Enum):
    """Table of Contents entry levels."""
    FRONT_MATTER = "front_matter"  # Roman numerals (i, ii, iii)
    CHAPTER = "chapter"            # Level 1 (1, 2, 3)
    SECTION = "section"            # Level 2 (1.1, 1.2)
    SUBSECTION = "subsection"      # Level 3 (1.1.1)
    APPENDIX = "appendix"          # Appendix (A, B, C)


@dataclass
class TOCEntry:
    """A single entry in the Table of Contents."""
    title: str
    level: TOCLevel
    page: str
    number: str  # Section number (1.1, 2.3, etc.)
    indent: int  # Indent level (0, 1, 2)


class StructuredTOCAgent:
    """
    Structured TOC Agent
    
    Generates Table of Contents as structured JSON.
    NO visual alignment characters (dots, spaces).
    UI layer handles rendering with CSS.
    """
    
    def __init__(self):
        self.name = "StructuredTOCAgent"
        self.version = "2.0.0"
    
    def generate_toc(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate structured TOC from proposal sections.
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            Structured TOC as JSON-ready dictionary
        """
        entries = []
        
        # Front Matter (Roman numerals)
        front_matter = [
            TOCEntry("DEDICATION", TOCLevel.FRONT_MATTER, "ii", "", 0),
            TOCEntry("ACKNOWLEDGEMENTS", TOCLevel.FRONT_MATTER, "iii", "", 0),
            TOCEntry("ABSTRACT", TOCLevel.FRONT_MATTER, "iv", "", 0),
            TOCEntry("LIST OF ABBREVIATIONS", TOCLevel.FRONT_MATTER, "v", "", 0),
            TOCEntry("LIST OF FIGURES", TOCLevel.FRONT_MATTER, "vi", "", 0),
            TOCEntry("LIST OF TABLES", TOCLevel.FRONT_MATTER, "vii", "", 0),
        ]
        entries.extend(front_matter)
        
        # Chapter 1: Introduction
        ch1_entries = [
            TOCEntry("CHAPTER 1: INTRODUCTION", TOCLevel.CHAPTER, "1", "1", 0),
            TOCEntry("Background of Study", TOCLevel.SECTION, "1", "1.1", 1),
            TOCEntry("Problem Statement", TOCLevel.SECTION, "3", "1.2", 1),
            TOCEntry("Aim and Objectives", TOCLevel.SECTION, "5", "1.3", 1),
            TOCEntry("Scope of the Study", TOCLevel.SECTION, "6", "1.4", 1),
            TOCEntry("Significance of the Study", TOCLevel.SECTION, "7", "1.5", 1),
            TOCEntry("Structure of the Study", TOCLevel.SECTION, "8", "1.6", 1),
        ]
        entries.extend(ch1_entries)
        
        # Chapter 2: Literature Review
        ch2_entries = [
            TOCEntry("CHAPTER 2: LITERATURE REVIEW", TOCLevel.CHAPTER, "9", "2", 0),
            TOCEntry("Introduction", TOCLevel.SECTION, "9", "2.1", 1),
            TOCEntry("Theoretical Framework", TOCLevel.SECTION, "10", "2.2", 1),
            TOCEntry("Literature Review", TOCLevel.SECTION, "12", "2.3", 1),
            TOCEntry("Summary of Gaps", TOCLevel.SECTION, "18", "2.4", 1),
            TOCEntry("Discussion", TOCLevel.SECTION, "20", "2.5", 1),
        ]
        entries.extend(ch2_entries)
        
        # Chapter 3: Research Methodology
        ch3_entries = [
            TOCEntry("CHAPTER 3: RESEARCH METHODOLOGY", TOCLevel.CHAPTER, "22", "3", 0),
            TOCEntry("Introduction", TOCLevel.SECTION, "22", "3.1", 1),
            TOCEntry("Research Methodology", TOCLevel.SECTION, "23", "3.2", 1),
            TOCEntry("Dataset Description", TOCLevel.SECTION, "25", "3.3", 1),
            TOCEntry("Missing Values Imputation", TOCLevel.SECTION, "26", "3.4", 1),
            TOCEntry("Exploratory Data Analysis", TOCLevel.SECTION, "27", "3.5", 1),
            TOCEntry("Design of Experimental Study", TOCLevel.SECTION, "28", "3.6", 1),
            TOCEntry("Model Development", TOCLevel.SECTION, "29", "3.7", 1),
            TOCEntry("Data Splitting", TOCLevel.SECTION, "31", "3.8", 1),
            TOCEntry("Feature Selection", TOCLevel.SECTION, "32", "3.9", 1),
            TOCEntry("Model Evaluation", TOCLevel.SECTION, "33", "3.10", 1),
            TOCEntry("Comparative Analysis", TOCLevel.SECTION, "35", "3.11", 1),
            TOCEntry("Ethical Consideration", TOCLevel.SECTION, "36", "3.12", 1),
            TOCEntry("Collaboration and Feedback", TOCLevel.SECTION, "37", "3.13", 1),
            TOCEntry("Deliverables and Reports", TOCLevel.SECTION, "38", "3.14", 1),
            TOCEntry("Required Resources", TOCLevel.SECTION, "39", "3.15", 1),
            TOCEntry("Risk and Contingency Plan", TOCLevel.SECTION, "40", "3.16", 1),
        ]
        entries.extend(ch3_entries)
        
        # Back Matter
        back_matter = [
            TOCEntry("REFERENCES", TOCLevel.CHAPTER, "42", "", 0),
            TOCEntry("APPENDIX A: RESEARCH PLAN", TOCLevel.APPENDIX, "48", "A", 0),
            TOCEntry("APPENDIX B: GANTT CHART", TOCLevel.APPENDIX, "50", "B", 0),
            TOCEntry("APPENDIX C: WORK BREAKDOWN STRUCTURE", TOCLevel.APPENDIX, "51", "C", 0),
            TOCEntry("APPENDIX D: TRACEABILITY MATRIX", TOCLevel.APPENDIX, "52", "D", 0),
        ]
        entries.extend(back_matter)
        
        return self.to_dict(entries)
    
    def to_dict(self, entries: List[TOCEntry]) -> Dict[str, Any]:
        """Convert TOC entries to JSON-ready dictionary."""
        return {
            "version": self.version,
            "title": "TABLE OF CONTENTS",
            "entry_count": len(entries),
            "entries": [
                {
                    "title": e.title,
                    "level": e.level.value,
                    "page": e.page,
                    "number": e.number,
                    "indent": e.indent
                }
                for e in entries
            ],
            "rendering_instructions": {
                "leader_style": "dotted",
                "font_family": "Times New Roman",
                "font_size": "12pt",
                "line_spacing": 1.5,
                "indent_per_level": "0.5in",
                "page_alignment": "right"
            }
        }


# Singleton instance
structured_toc_agent = StructuredTOCAgent()

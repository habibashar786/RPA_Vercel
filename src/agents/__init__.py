"""
ResearchAI v2.4.0 - Agents Module
=================================

Multi-agent orchestration for Q1 journal-standard research proposal generation.

Agent Categories:
- Content Generation: Introduction, Literature Review, Methodology
- Quality Assurance: Proofreading, Validation, Optimization
- Document Structure: Formatting, Assembly, Front Matter, Structured TOC
- Visualization: Gantt, WBS, RTM, Kanban, Flowcharts
- Post-Generation: Scopus Compliance, Reviewer Simulation, Email Notifications
"""

# v2.0 Enhanced Agents
from .scopus_compliance_agent import ScopusComplianceAgentV2, scopus_compliance_agent
from .reviewer_simulation_agent import ReviewerSimulationAgentV2, reviewer_simulation_agent
from .email_notification_agent import EmailNotificationAgent, email_notification_agent

# v2.4 New Agents (Precision Effect)
from .visualization_agent import VisualizationAgentV2, visualization_agent
from .structured_toc_agent import StructuredTOCAgent, structured_toc_agent

__all__ = [
    # Scopus & Review Agents
    'ScopusComplianceAgentV2',
    'scopus_compliance_agent',
    'ReviewerSimulationAgentV2', 
    'reviewer_simulation_agent',
    
    # Notification Agent
    'EmailNotificationAgent',
    'email_notification_agent',
    
    # Visualization Agent v2.4
    'VisualizationAgentV2',
    'visualization_agent',
    
    # Structured TOC Agent v2.4
    'StructuredTOCAgent',
    'structured_toc_agent',
]

__version__ = "2.4.0"

"""
ResearchAI - Multi-Agent Research Proposal Generation System
=============================================================

Production-ready FastAPI application for generating Q1 journal-standard
research proposals with:
- Multi-agent orchestration (12 agents including Proofreading Agent)
- PDF paper ingestion
- Visual diagram generation
- Harvard citation style
- Academic Q1/Scopus/Elsevier formatting
- Subscription tier management (Free/Non-permanent/Permanent)
- Watermark enforcement for non-permanent subscribers
- Professional title page and TOC formatting
- No markdown artifacts in output
"""

import asyncio
import uuid
import os
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
from pydantic import BaseModel, Field
import logging
import json
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set environment variable to use in-memory state
os.environ["USE_INMEMORY_STATE"] = "1"


# ============================================================================
# Subscription Tier Enum
# ============================================================================
class SubscriptionTier(str, Enum):
    FREE = "free"
    NON_PERMANENT = "non_permanent"  # Has watermark
    PERMANENT = "permanent"  # Clean PDF, no watermark


# ============================================================================
# In-Memory Job Store
# ============================================================================
class JobStore:
    """In-memory store for tracking background jobs."""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_job(self, job_id: str, topic: str, metadata: Dict = None) -> Dict[str, Any]:
        job = {
            "job_id": job_id,
            "topic": topic,
            "metadata": metadata or {},
            "status": "pending",
            "progress": 0,
            "current_stage": "initializing",
            "stages_completed": [],
            "message": "Job created, waiting to start...",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "result": None,
        }
        self.jobs[job_id] = job
        logger.info(f"[JobStore] Created job {job_id} for topic: {topic[:50]}...")
        return job
    
    def update_job(self, job_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        if job_id not in self.jobs:
            logger.warning(f"[JobStore] Job {job_id} not found for update")
            return None
        self.jobs[job_id].update(kwargs)
        self.jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"[Job {job_id[:8]}] Updated: status={self.jobs[job_id].get('status')}, progress={self.jobs[job_id].get('progress')}%")
        return self.jobs[job_id]
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.jobs.get(job_id)
        return job
    
    def list_jobs(self, limit: int = 20) -> list:
        jobs = list(self.jobs.values())
        return sorted(jobs, key=lambda x: x["created_at"], reverse=True)[:limit]


# Global stores
job_store = JobStore()
completed_proposals: Dict[str, Any] = {}
uploaded_pdfs: Dict[str, Any] = {}


# ============================================================================
# Target Word Count Configuration - Precision Effect Strategy
# ============================================================================
VALID_WORD_COUNTS = [3000, 5000, 10000, 15000, 20000]
WORD_COUNT_CONFIGS = {
    3000: {"name": "Express", "chapters": "condensed", "est_time": 3, "lit_review_words": 800, "methodology_words": 600},
    5000: {"name": "Brief", "chapters": "standard", "est_time": 5, "lit_review_words": 1200, "methodology_words": 1000},
    10000: {"name": "Standard", "chapters": "full", "est_time": 8, "lit_review_words": 2500, "methodology_words": 2000},
    15000: {"name": "Comprehensive", "chapters": "detailed", "est_time": 12, "lit_review_words": 4000, "methodology_words": 3500},
    20000: {"name": "Extended", "chapters": "extended", "est_time": 18, "lit_review_words": 5500, "methodology_words": 5000},
}


# ============================================================================
# Request/Response Models
# ============================================================================
class ProposalGenerationRequest(BaseModel):
    """Flexible request model with target word count options (Precision Effect)."""
    topic: str = Field(..., min_length=10, description="Research topic")
    
    # Frontend fields
    key_points: Optional[List[str]] = Field(default=None, description="Key research points")
    citation_style: Optional[str] = Field(default="harvard", description="Citation style")
    target_word_count: Optional[int] = Field(
        default=15000, 
        description="Target word count: 3000 (Express), 5000 (Brief), 10000 (Standard), 15000 (Comprehensive), 20000 (Extended)"
    )
    
    # Original fields (with defaults)
    student_name: str = Field(default="Researcher", description="Student/Author name")
    supervisor_name: str = Field(default="", description="Supervisor name")
    institution: str = Field(default="", description="Institution name")
    department: str = Field(default="", description="Department name")
    dedication_to: str = Field(default="", description="Dedication recipient")
    include_visuals: bool = Field(default=True, description="Generate visual diagrams")
    
    class Config:
        extra = "ignore"
    
    def get_validated_word_count(self) -> int:
        """Return validated word count, defaulting to nearest valid option."""
        if self.target_word_count in VALID_WORD_COUNTS:
            return self.target_word_count
        return min(VALID_WORD_COUNTS, key=lambda x: abs(x - (self.target_word_count or 15000)))
    
    def get_word_count_config(self) -> Dict[str, Any]:
        """Get configuration for the target word count."""
        count = self.get_validated_word_count()
        return WORD_COUNT_CONFIGS[count]


class ProposalGenerationResponse(BaseModel):
    job_id: str
    topic: str
    status: str
    message: str
    progress: int = 0
    current_stage: Optional[str] = None
    estimated_time_minutes: int = 15


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    current_stage: Optional[str] = None
    stages_completed: List[str] = []
    message: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Formatting Utilities - Remove ALL Markdown
# ============================================================================
def remove_markdown(text: str) -> str:
    """Remove all markdown formatting from text."""
    if not text:
        return text
    
    result = text
    result = re.sub(r'^#{1,6}\s*', '', result, flags=re.MULTILINE)
    result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)
    result = re.sub(r'\*([^*]+)\*', r'\1', result)
    result = re.sub(r'__([^_]+)__', r'\1', result)
    result = re.sub(r'_([^_]+)_', r'\1', result)
    result = re.sub(r'```[\s\S]*?```', '', result)
    result = re.sub(r'`([^`]+)`', r'\1', result)
    result = re.sub(r'^\s*[-*+]\s+', '', result, flags=re.MULTILINE)
    result = re.sub(r'^\s*\d+\.\s+', '', result, flags=re.MULTILINE)
    result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)
    result = re.sub(r'^>\s*', '', result, flags=re.MULTILINE)
    
    return result


def format_academic_content(text: str) -> str:
    """Format content for academic Q1 standards."""
    result = remove_markdown(text)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title="ResearchAI - Multi-Agent Proposal Generator",
    description="Generate Q1 journal-standard research proposals with AI agents",
    version="2.7.3"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# LLM Provider - Mock or Real
# ============================================================================
class MockLLMProvider:
    """Mock LLM provider for testing without API calls."""
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock content based on prompt keywords."""
        await asyncio.sleep(0.1)  # Simulate API latency
        
        if "dedication" in prompt.lower():
            return "This work is dedicated to my family, mentors, and all those who have supported my academic journey."
        
        elif "acknowledgement" in prompt.lower():
            return """I would like to express my sincere gratitude to my supervisor for their invaluable guidance and support throughout this research. I am also grateful to the faculty members and staff who provided assistance and resources. Special thanks to my colleagues for their constructive feedback and encouragement. Finally, I thank my family for their unwavering support and understanding during this academic endeavor."""
        
        elif "abstract" in prompt.lower():
            return """This research proposal presents a comprehensive investigation into the proposed research topic. The study addresses significant gaps in the current literature and aims to contribute new knowledge to the field. The methodology employs a mixed-methods approach combining quantitative analysis with qualitative insights. Expected outcomes include theoretical contributions and practical implications for stakeholders. The research timeline spans 12 months with clearly defined milestones and deliverables."""
        
        elif "background" in prompt.lower():
            return """The research area has evolved significantly over the past decade, driven by technological advancements and changing societal needs. Historical developments have shaped current understanding, while recent studies have identified critical gaps requiring further investigation. The theoretical framework underpinning this research draws from established models while incorporating contemporary perspectives. This background provides essential context for understanding the research problem and its significance."""
        
        elif "problem statement" in prompt.lower():
            return """Despite considerable advances in the field, significant challenges remain unaddressed. Current approaches have limitations in addressing complex, real-world scenarios. The lack of comprehensive solutions has implications for both theory and practice. This research addresses these gaps by proposing innovative approaches that build upon existing knowledge while introducing novel perspectives. The problem is both timely and relevant given current developments in the field."""
        
        elif "aims" in prompt.lower() or "objective" in prompt.lower():
            return """The primary aim of this research is to investigate and develop solutions for the identified research problem. This will be achieved through the following specific objectives: First, to conduct a comprehensive review of existing literature and identify knowledge gaps. Second, to design and implement a robust methodology for data collection and analysis. Third, to analyze findings and develop theoretical frameworks. Fourth, to validate results and propose practical recommendations for implementation."""
        
        elif "scope" in prompt.lower():
            return """This research focuses specifically on the defined research domain within established boundaries. The study includes analysis of relevant variables and their relationships. Geographically, the research encompasses selected study areas appropriate for the investigation. Temporally, the study covers a defined period suitable for comprehensive analysis. Certain aspects are excluded to maintain focus and feasibility within the research timeline."""
        
        elif "significance" in prompt.lower():
            return """This research makes significant contributions to both theoretical understanding and practical application. Theoretically, the study advances knowledge by addressing identified gaps and proposing new frameworks. Practically, the findings will benefit stakeholders by providing evidence-based recommendations. The research also contributes methodologically by demonstrating effective approaches for similar investigations. These contributions establish the importance and value of the proposed research."""
        
        elif "literature" in prompt.lower() and "review" in prompt.lower():
            return """The literature review examines key theoretical frameworks and empirical studies relevant to this research. Foundational works established core concepts that continue to influence current understanding. Recent studies have expanded knowledge while identifying areas requiring further investigation. Thematic analysis reveals patterns and relationships among key variables. The synthesis of existing literature provides a solid foundation for this research while highlighting the unique contribution of the proposed study. Multiple scholarly sources support the theoretical framework adopted in this investigation."""
        
        elif "methodology" in prompt.lower():
            return """This research employs a comprehensive methodological approach designed to address the research objectives effectively. The research philosophy adopts a pragmatic stance, allowing for flexibility in method selection. The research design follows a sequential mixed-methods approach, combining quantitative surveys with qualitative interviews. The target population includes relevant stakeholders, with sampling employing stratified random techniques to ensure representativeness. Data collection instruments include validated questionnaires and semi-structured interview protocols. Analysis will utilize both statistical techniques and thematic analysis. Quality assurance measures include validity testing, reliability assessment, and triangulation. Ethical considerations address informed consent, confidentiality, and data protection requirements."""
        
        elif "risk" in prompt.lower():
            return """Risk assessment identifies potential challenges and mitigation strategies for this research. Technical risks include data collection challenges, addressed through pilot testing and alternative methods. Timeline risks are mitigated through buffer periods and prioritization of critical activities. Resource risks are managed through early procurement and backup arrangements. Quality risks are addressed through validation procedures and expert review. Contingency plans are established for each identified risk category."""
        
        elif "reference" in prompt.lower():
            return """1. Anderson, J. & Smith, K. (2023). Advances in research methodology: A comprehensive review. Journal of Academic Research, 45(2), 112-128.

2. Brown, M., Davis, L., & Wilson, R. (2022). Theoretical frameworks for contemporary studies. Research Quarterly, 38(4), 234-251.

3. Chen, X. & Kumar, P. (2024). Emerging trends in the field: Implications for future research. International Journal of Studies, 52(1), 45-67.

4. Garcia, A., Martinez, B., & Lee, S. (2023). Methodological innovations in mixed-methods research. Methodology Review, 29(3), 178-195.

5. Johnson, T. & Williams, E. (2022). Data analysis techniques for modern research. Analytics Journal, 41(2), 89-106.

6. Miller, R., Thompson, H., & Clark, D. (2024). Quality assurance in academic research. Quality Studies, 33(1), 23-41.

7. Patel, N. & Robinson, G. (2023). Ethical considerations in contemporary research. Ethics Review, 27(4), 156-173.

8. Taylor, S., Adams, J., & White, M. (2022). Sampling strategies for population studies. Statistics Today, 44(3), 201-218.

9. Wang, L. & Harris, C. (2024). Literature synthesis methods: Best practices. Review Methodology, 36(2), 134-151.

10. Young, K., Green, P., & Scott, R. (2023). Practical applications of research findings. Applied Research, 48(1), 67-84."""
        
        elif "timeline" in prompt.lower() or "plan" in prompt.lower():
            return """The research timeline spans 12 months with distinct phases. Phase 1 (Months 1-3) focuses on literature review and methodology refinement. Phase 2 (Months 4-6) involves data collection and preliminary analysis. Phase 3 (Months 7-9) encompasses comprehensive data analysis and interpretation. Phase 4 (Months 10-12) dedicates to writing, review, and final submission. Key milestones include proposal defense, ethics approval, data collection completion, and thesis submission."""
        
        elif "chapter" in prompt.lower():
            return """This chapter provides essential context and structure for the research. The content addresses key aspects of the research topic in a systematic manner. Discussion proceeds from foundational concepts to specific applications. Each section builds upon previous content to develop comprehensive understanding. The chapter concludes by establishing connections to subsequent research phases."""
        
        else:
            return """This section presents important content relevant to the research objectives. The analysis demonstrates rigorous academic standards while maintaining clarity and accessibility. Evidence supports the arguments presented, with appropriate citations to scholarly sources. The discussion considers multiple perspectives and acknowledges limitations. Conclusions drawn contribute to the overall research narrative and objectives."""


class RealLLMProvider:
    """Real LLM provider using Anthropic API."""
    
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate content using Anthropic API."""
        try:
            import httpx
            
            max_tokens = kwargs.get("max_tokens", 4096)
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": max_tokens,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["content"][0]["text"]
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    return f"Error generating content: {response.status_code}"
                    
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return f"Error: {str(e)}"


def get_llm_provider():
    """Get appropriate LLM provider based on environment."""
    if os.environ.get("LLM_MOCK", "0") == "1":
        logger.info("Using MockLLMProvider")
        return MockLLMProvider()
    else:
        logger.info("Using RealLLMProvider")
        return RealLLMProvider()


# ============================================================================
# Prompt Templates
# ============================================================================
def get_citation_rule(style: str = "harvard") -> str:
    """Get citation formatting rule based on style."""
    if style == "apa":
        return " Use APA 7th edition citation format."
    elif style == "mla":
        return " Use MLA 9th edition citation format."
    elif style == "chicago":
        return " Use Chicago Manual of Style citation format."
    else:
        return " Use Harvard citation format (Author, Year)."


def get_prompts(topic: str, target_words: int = 15000, citation_style: str = "harvard") -> Dict[str, str]:
    """Generate all prompts for proposal sections with word count scaling."""
    
    citation_rule = get_citation_rule(citation_style)
    
    # Scale factors based on target word count
    scale = target_words / 15000  # Base is 15000 words
    
    def scaled(base_words: int) -> int:
        return max(100, int(base_words * scale))
    
    prompts = {}
    
    # Front Matter
    base_words = 100
    prompts["dedication"] = f"""Write a sincere academic dedication for a research proposal on: {topic}

Requirements: 2-3 paragraphs, sincere, formal, NO markdown formatting."""
    
    prompts["acknowledgements"] = f"""Write professional acknowledgements for a research proposal on: {topic}

Requirements: 3-4 paragraphs, thank supervisor, institution, colleagues, family. NO markdown."""
    
    base_words = 300
    prompts["abstract"] = f"""Write an academic abstract for a research proposal on: {topic}

Write {scaled(base_words)} words covering: background, problem, methodology, expected outcomes.
NO markdown formatting."""
    
    # Chapter 1: Introduction
    base_words = 500
    prompts["background"] = f"""Write the research background for: {topic}

{int(base_words * 0.8)}-{base_words} words, historical context, current relevance. NO markdown.{citation_rule}"""
    
    prompts["problem_statement"] = f"""Write the problem statement for: {topic}

{int(base_words * 0.8)}-{base_words} words, specific problem, why it needs attention. NO markdown.{citation_rule}"""
    
    prompts["aims_objectives"] = f"""Write aims and objectives for: {topic}

ONE primary aim, 3-4 specific objectives in prose paragraphs (~{base_words} words). NO numbered lists. NO markdown."""
    
    prompts["scope"] = f"""Write the scope and delimitations for: {topic}

2-3 paragraphs (~{base_words} words), boundaries, inclusions/exclusions. NO markdown."""
    
    prompts["significance"] = f"""Write the significance of the study for: {topic}

2-3 paragraphs (~{base_words} words), theoretical/practical contributions. NO markdown.{citation_rule}"""
    
    prompts["chapter_outline"] = f"""Write a brief chapter outline for a proposal on: {topic}

1-2 paragraphs (~{base_words} words) describing chapter contents. NO markdown."""
    
    # Chapter 2: Literature Review
    base_words = 2000
    prompts["lit_intro"] = f"""Write the introduction to the literature review for: {topic}

{int(base_words * 0.8)}-{base_words} words, purpose, key themes. NO markdown.
Include at least 5 in-text
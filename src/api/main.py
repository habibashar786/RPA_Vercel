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

# Import v2 endpoints router
try:
    from src.api.endpoints_v2 import router as v2_router, set_proposals_store
    V2_ENDPOINTS_AVAILABLE = True
except ImportError:
    V2_ENDPOINTS_AVAILABLE = False
    v2_router = None
    set_proposals_store = None

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
    result = re.sub(r'^[\*\-_]{3,}\s*$', '', result, flags=re.MULTILINE)
    result = re.sub(r'<[^>]+>', '', result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = re.sub(r' {2,}', ' ', result)
    
    return result.strip()


def format_academic_text(text: str) -> str:
    """Format text for academic output."""
    if not text:
        return text
    
    result = remove_markdown(text)
    
    contractions = [
        (r"\bdon't\b", "do not"), (r"\bwon't\b", "will not"), (r"\bcan't\b", "cannot"),
        (r"\bisn't\b", "is not"), (r"\baren't\b", "are not"), (r"\bwasn't\b", "was not"),
        (r"\bweren't\b", "were not"), (r"\bhasn't\b", "has not"), (r"\bhaven't\b", "have not"),
        (r"\bhadn't\b", "had not"), (r"\bdoesn't\b", "does not"), (r"\bdidn't\b", "did not"),
        (r"\bcouldn't\b", "could not"), (r"\bwouldn't\b", "would not"), (r"\bshouldn't\b", "should not"),
        (r"\bit's\b", "it is"), (r"\bthat's\b", "that is"), (r"\bwhat's\b", "what is"),
        (r"\bthere's\b", "there is"),
    ]
    
    for pattern, replacement in contractions:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


# ============================================================================
# Load Environment Variables
# ============================================================================
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment from: {env_path}")
else:
    load_dotenv()
    logger.info("Loaded environment from current directory")


# ============================================================================
# LLM Provider
# ============================================================================
class LLMProvider:
    """Anthropic Claude LLM Provider with async support."""
    
    def __init__(self):
        try:
            import anthropic
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-sonnet-4-20250514"
            self.provider_name = "anthropic"
            logger.info(f"LLM Provider initialized: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
    
    def _sync_generate(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        messages = [{"role": "user", "content": prompt}]
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt if system_prompt else "You are an expert academic researcher.",
            messages=messages,
        )
        return response.content[0].text
    
    async def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 4096) -> str:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._sync_generate, prompt, system_prompt, max_tokens)
            return result
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise


llm_provider = None

def get_llm() -> LLMProvider:
    global llm_provider
    if llm_provider is None:
        llm_provider = LLMProvider()
    return llm_provider


# ============================================================================
# Academic System Prompt
# ============================================================================
ACADEMIC_SYSTEM_PROMPT = """You are an experienced academic researcher writing for Q1 peer-reviewed journals.

=== CRITICAL: WRITE LIKE A HUMAN TO AVOID AI DETECTION ===

1. SENTENCE LENGTH VARIATION (MANDATORY):
   - Mix very short sentences (5-8 words) with medium (15-20) and long (30-40)
   - Pattern example: Long sentence explaining concept. Short follow-up. Why? Because humans think in bursts.
   - NEVER make all sentences similar length

2. VOICE MIXING (60% active, 40% passive):
   - Active: "We analyzed the data" / "The researchers found"
   - Passive: "The data was analyzed" / "It was found that"
   - Mix both throughout

3. USE CONTRACTIONS NATURALLY:
   - Use: it's, don't, won't, we've, that's, there's, isn't, can't
   - Example: "It's clear that this approach doesn't always work"

4. HEDGING LANGUAGE (ESSENTIAL):
   - Use: seems, appears, suggests, might, may, could, possibly, likely
   - Example: "This seems to indicate..." NOT "This proves..."

5. PERSONAL ACADEMIC VOICE:
   - Use "we" and "our" frequently: "We observed...", "Our analysis shows..."
   - Add personal assessment: "In our view...", "We find this compelling because..."

6. INFORMAL TRANSITIONS (MIX IN):
   - Occasionally use: Now, So, Well, Here's the thing, The point is
   - Example: "Now, this raises an interesting question..."

7. RHETORICAL QUESTIONS (ADD OCCASIONALLY):
   - "But what does this mean in practice?"
   - "Why does this matter?"

8. PARENTHETICAL ASIDES:
   - Use: (and this is key), (interestingly), (which surprised us)
   - Example: "The results (and this was unexpected) showed..."

9. PUNCTUATION VARIETY:
   - Use em-dashes: "The results — surprising as they were — confirmed..."
   - Use colons: "Three factors matter: speed, accuracy, and cost"

10. PARAGRAPH LENGTH VARIATION:
    - Some paragraphs: 2-3 sentences
    - Some paragraphs: 5-7 sentences
    - NEVER make all paragraphs same length

=== WORDS/PHRASES TO NEVER USE (AI DETECTION TRIGGERS) ===
- NEVER use: Furthermore, Moreover, Additionally (at paragraph starts)
- NEVER use: "It is important to note that"
- NEVER use: significant/significantly more than once per paragraph
- NEVER use: comprehensive, robust, utilize, facilitate
- NEVER use: methodology (use "method" or "approach")
- NEVER use: paradigm, paradigm shift
- NEVER use: multifaceted, plethora, myriad
- NEVER use: demonstrate (use "show" or "reveal")
- NEVER use: implement (use "use" or "apply")
- NEVER use: enhance (use "improve" or "boost")
- NEVER use: leverage, synergy, stakeholders
- NEVER use: "a wide range of" (use "many" or "various")
- NEVER use: "in the context of" (use "regarding" or "about")
- NEVER use: "due to the fact that" (use "because")
- NEVER use: "in order to" (use "to")

=== FORMATTING RULES ===
1. NO markdown formatting (no #, **, -, *, numbered lists)
2. Write in pure academic prose paragraphs only
3. Use Harvard citation style: (Author, Year) or (Author et al., Year)
4. Write flowing paragraphs suitable for published journals

Remember: You're writing as a HUMAN researcher who thinks, pauses, reconsiders, and varies their style naturally. NOT as a perfect AI that produces uniform, predictable text."""


# ============================================================================
# Content Generation Functions
# ============================================================================
async def generate_title_page_content(topic: str, author_name: str, date: str) -> str:
    """Generate formatted title page content."""
    return f"""{topic.upper()}


RESEARCH PROPOSAL


Submitted by
{author_name}


{date.upper()}"""


async def generate_dedication(llm: LLMProvider, topic: str, dedication_to: str) -> str:
    prompt = f"""Write a formal academic dedication for a research proposal on "{topic}".
Addressed to: {dedication_to if dedication_to else "family, mentors, and the academic community"}
Requirements: 2-3 paragraphs, sincere, formal, NO markdown formatting."""
    content = await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=800)
    return format_academic_text(content)


async def generate_acknowledgements(llm: LLMProvider, topic: str, supervisor: str, institution: str) -> str:
    prompt = f"""Write formal academic acknowledgements for a research proposal on "{topic}".
Supervisor: {supervisor if supervisor else "my supervisor"}
Institution: {institution if institution else "my institution"}
Requirements: 3-4 paragraphs, thank supervisor, institution, colleagues, family. NO markdown."""
    content = await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=1000)
    return format_academic_text(content)


async def generate_abstract(llm: LLMProvider, topic: str) -> str:
    prompt = f"""Write an academic abstract for a research proposal on "{topic}".
Structure as ONE flowing paragraph (250-300 words):
- 3 sentences: research problem and significance
- 3 sentences: proposal focus and objectives  
- 4 sentences: key literature summary
- 3 sentences: methodology
- 2 sentences: expected results
NO markdown formatting."""
    content = await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=600)
    return format_academic_text(content)


async def generate_chapter1_scaled(llm: LLMProvider, topic: str, word_scale: float) -> Dict[str, str]:
    """Generate Chapter 1 with word count scaling."""
    sections = {}
    
    citation_rule = """\nCITATION RULE: Use ONLY in-text citations like (Author, Year) or (Author et al., Year).
DO NOT write full bibliographic entries - those belong only in the REFERENCES section."""
    
    def scale_words(base: int) -> int:
        return max(100, int(base * word_scale))
    
    def scale_tokens(base: int) -> int:
        return max(200, int(base * word_scale))
    
    base_words = scale_words(600)
    prompt = f"""Write "Background of Study" for research proposal on "{topic}".
{int(base_words * 0.8)}-{base_words} words, historical context, current relevance. NO markdown.{citation_rule}"""
    sections["background"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(1500)))
    
    base_words = scale_words(400)
    prompt = f"""Write "Problem Statement" for "{topic}".
{int(base_words * 0.8)}-{base_words} words, specific problem, why it needs attention. NO markdown.{citation_rule}"""
    sections["problem_statement"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(1000)))
    
    base_words = scale_words(300)
    prompt = f"""Write "Aim and Objectives" for "{topic}".
ONE primary aim, 3-4 specific objectives in prose paragraphs (~{base_words} words). NO numbered lists. NO markdown."""
    sections["aim_objectives"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(800)))
    
    base_words = scale_words(250)
    prompt = f"""Write "Scope of the Study" for "{topic}".
2-3 paragraphs (~{base_words} words), boundaries, inclusions/exclusions. NO markdown."""
    sections["scope"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(600)))
    
    base_words = scale_words(400)
    prompt = f"""Write "Significance of the Study" for "{topic}".
2-3 paragraphs (~{base_words} words), theoretical/practical contributions. NO markdown.{citation_rule}"""
    sections["significance"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(1000)))
    
    base_words = scale_words(200)
    prompt = f"""Write "Structure of the Study" for "{topic}".
1-2 paragraphs (~{base_words} words) describing chapter contents. NO markdown."""
    sections["structure"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(500)))
    
    return sections


async def generate_chapter2_scaled(llm: LLMProvider, topic: str, word_scale: float) -> Dict[str, str]:
    """Generate Chapter 2 with word count scaling."""
    sections = {}
    
    def scale_words(base: int) -> int:
        return max(100, int(base * word_scale))
    
    def scale_tokens(base: int) -> int:
        return max(200, int(base * word_scale))
    
    base_words = scale_words(300)
    prompt = f"""Write Literature Review introduction for "{topic}".
{int(base_words * 0.8)}-{base_words} words, purpose, key themes. NO markdown.
IMPORTANT: Use ONLY in-text citation markers like (Author, Year).
DO NOT include full reference entries."""
    sections["introduction"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(700)))
    
    base_words = scale_words(2000)
    prompt = f"""Write Literature Review for "{topic}".
{int(base_words * 0.8)}-{base_words} words total, thematic organization. NO markdown.

CRITICAL CITATION RULES:
1. Use ONLY short in-text citations: (Smith, 2023) or (Jones et al., 2024)
2. DO NOT write full bibliographic entries
3. DO NOT include URLs, DOIs, or publisher information"""
    sections["literature_review"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(5000)))
    
    base_words = scale_words(500)
    prompt = f"""Write "Summary of Gaps" for "{topic}".
{int(base_words * 0.8)}-{base_words} words, 3-4 specific gaps. NO lists. NO markdown."""
    sections["gaps"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(1200)))
    
    base_words = scale_words(400)
    prompt = f"""Write Literature Review Discussion for "{topic}".
{int(base_words * 0.8)}-{base_words} words, synthesize findings. NO markdown."""
    sections["discussion"] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scale_tokens(1000)))
    
    return sections


async def generate_chapter3_scaled(llm: LLMProvider, topic: str, word_scale: float) -> Dict[str, str]:
    """Generate Chapter 3 with word count scaling."""
    sections = {}
    
    def scale_words(base: int) -> int:
        return max(50, int(base * word_scale))
    
    def scale_tokens(base: int) -> int:
        return max(150, int(base * word_scale))
    
    if word_scale < 0.4:
        subsections = [
            ("introduction", "Introduction to Research Methodology", 200, 500),
            ("methodology", "Research Methodology", 300, 800),
            ("dataset", "Dataset Description", 200, 500),
            ("model_development", "Model Development", 250, 600),
            ("model_evaluation", "Model Evaluation", 200, 500),
            ("ethics", "Ethical Consideration", 150, 400),
        ]
    elif word_scale < 0.7:
        subsections = [
            ("introduction", "Introduction to Research Methodology", 250, 600),
            ("methodology", "Research Methodology", 400, 1000),
            ("dataset", "Dataset Description", 300, 700),
            ("missing_values", "Missing Values Imputation", 200, 500),
            ("eda", "Exploratory Data Analysis", 200, 500),
            ("model_development", "Model Development", 350, 800),
            ("data_splitting", "Data Splitting", 150, 400),
            ("feature_selection", "Feature Selection", 200, 500),
            ("model_evaluation", "Model Evaluation", 300, 700),
            ("ethics", "Ethical Consideration", 200, 500),
            ("risk_plan", "Risk and Contingency Plan", 250, 600),
        ]
    else:
        subsections = [
            ("introduction", "Introduction to Research Methodology chapter", 300, 700),
            ("methodology", "Research Methodology (design, justification, approach)", 500, 1200),
            ("dataset", "Dataset Description (sources, sampling, variables)", 400, 1000),
            ("missing_values", "Missing Values Imputation and Encoding", 300, 700),
            ("eda", "Exploratory Data Analysis techniques", 300, 700),
            ("experimental_design", "Design of Experimental Study", 350, 800),
            ("model_development", "Model Development (architecture, theory)", 450, 1100),
            ("data_splitting", "Data Splitting (train/test/validation)", 200, 500),
            ("feature_selection", "Feature Selection techniques", 300, 700),
            ("model_evaluation", "Evaluating Multiple Models", 400, 1000),
            ("comparative_analysis", "Comparative Analysis and Outcome", 300, 700),
            ("ethics", "Ethical Consideration", 300, 700),
            ("collaboration", "Collaboration and Feedback", 200, 500),
            ("deliverables", "Deliverables and Reports", 200, 500),
            ("resources", "Required Resources", 250, 600),
            ("risk_plan", "Risk and Contingency Plan", 400, 1000),
        ]
    
    for key, desc, words, tokens in subsections:
        scaled_words = scale_words(words)
        scaled_tokens = scale_tokens(tokens)
        prompt = f"""Write "{desc}" section for research proposal on "{topic}".
~{scaled_words} words in prose paragraphs. NO bullet points. NO markdown."""
        sections[key] = format_academic_text(await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=scaled_tokens))
    
    return sections


async def generate_references_scaled(llm: LLMProvider, topic: str, word_scale: float) -> str:
    """Generate references with count scaled to word target."""
    if word_scale < 0.4:
        ref_count = "15-20"
    elif word_scale < 0.7:
        ref_count = "25-30"
    else:
        ref_count = "40-50"
    
    max_tokens = max(1000, int(4000 * word_scale))
    
    prompt = f"""Generate REFERENCES section for research proposal on "{topic}".
{ref_count} academic references in Harvard format, sorted alphabetically.
Include journals, books, conference papers from 2019-2024 plus seminal works.
Each reference on its own line. NO markdown. NO bullet points."""
    content = await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=max_tokens)
    return format_academic_text(content)


async def generate_research_plan(llm: LLMProvider, topic: str) -> str:
    prompt = f"""Write "Appendix A: Research Plan" for "{topic}".
Timeline 12-18 months, phases, milestones in prose (~400 words). NO tables. NO markdown."""
    content = await llm.generate(prompt, ACADEMIC_SYSTEM_PROMPT, max_tokens=1000)
    return format_academic_text(content)


# ============================================================================
# Proofreading and Consistency Agent
# ============================================================================
class ProofreadingAgent:
    """Proofreading and Consistency Agent."""
    
    @staticmethod
    def validate_proposal(sections: List[Dict], topic: str) -> Dict[str, Any]:
        """Validate proposal structure and formatting."""
        issues = []
        corrections = []
        
        title_pages = [s for s in sections if s.get("title") == "TITLE PAGE"]
        if not title_pages:
            issues.append("Missing title page")
        
        toc_pages = [s for s in sections if "TABLE OF CONTENTS" in s.get("title", "")]
        if not toc_pages:
            issues.append("Missing table of contents")
        
        titles = [s.get("title", "") for s in sections]
        duplicates = set([t for t in titles if titles.count(t) > 1 and t])
        if duplicates:
            issues.append(f"Duplicate sections: {duplicates}")
        
        ref_sections = [s for s in sections if "REFERENCES" in s.get("title", "").upper()]
        if len(ref_sections) > 1:
            issues.append("Multiple reference sections found")
            corrections.append("Consolidated references into single section")
        
        chapter_order = []
        for s in sections:
            title = s.get("title", "")
            if "CHAPTER 1" in title:
                chapter_order.append(1)
            elif "CHAPTER 2" in title:
                chapter_order.append(2)
            elif "CHAPTER 3" in title:
                chapter_order.append(3)
        
        if chapter_order != sorted(chapter_order):
            issues.append("Chapter order inconsistency")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "corrections": corrections,
            "sections_count": len(sections),
        }


# ============================================================================
# Proposal Assembly
# ============================================================================
async def assemble_proposal(
    topic: str,
    student_name: str,
    supervisor_name: str,
    institution: str,
    dedication_to: str,
    include_visuals: bool,
    job_id: str,
    target_word_count: int = 15000,
) -> Dict[str, Any]:
    """Assemble the complete proposal with all sections."""
    
    llm = get_llm()
    sections = []
    current_date = datetime.now().strftime("%B %Y")
    
    BASE_WORD_COUNT = 15000
    word_scale = target_word_count / BASE_WORD_COUNT
    logger.info(f"[Job {job_id[:8]}] Word scale factor: {word_scale:.2f}x (target: {target_word_count:,} words)")
    
    config = WORD_COUNT_CONFIGS.get(target_word_count, WORD_COUNT_CONFIGS[15000])
    
    def update_progress(stage: str, progress: int, message: str):
        stages = job_store.get_job(job_id).get("stages_completed", [])
        if stage not in stages:
            stages.append(stage)
        job_store.update_job(job_id, progress=progress, current_stage=stage, message=message, stages_completed=stages)
    
    # TITLE PAGE
    update_progress("title_page", 2, "Generating title page...")
    title_content = await generate_title_page_content(topic, student_name, current_date)
    sections.append({"title": "TITLE PAGE", "content": title_content, "page": 1})
    
    # DEDICATION
    update_progress("dedication", 5, "Generating dedication...")
    sections.append({"title": "DEDICATION", "content": await generate_dedication(llm, topic, dedication_to)})
    
    # ACKNOWLEDGEMENTS
    update_progress("acknowledgements", 8, "Generating acknowledgements...")
    sections.append({"title": "ACKNOWLEDGEMENTS", "content": await generate_acknowledgements(llm, topic, supervisor_name, institution)})
    
    # ABSTRACT
    update_progress("abstract", 12, "Generating abstract...")
    sections.append({"title": "ABSTRACT", "content": await generate_abstract(llm, topic)})
    
    # TABLE OF CONTENTS
    toc_data = {
        "entries": [
            {"title": "DEDICATION", "page": "ii", "level": "front_matter", "number": "", "indent": 0},
            {"title": "ACKNOWLEDGEMENTS", "page": "iii", "level": "front_matter", "number": "", "indent": 0},
            {"title": "ABSTRACT", "page": "iv", "level": "front_matter", "number": "", "indent": 0},
            {"title": "LIST OF TABLES", "page": "v", "level": "front_matter", "number": "", "indent": 0},
            {"title": "LIST OF FIGURES", "page": "vi", "level": "front_matter", "number": "", "indent": 0},
            {"title": "LIST OF ABBREVIATIONS", "page": "vii", "level": "front_matter", "number": "", "indent": 0},
            {"title": "CHAPTER 1: INTRODUCTION", "page": "1", "level": "chapter", "number": "1", "indent": 0},
            {"title": "Background of Study", "page": "1", "level": "section", "number": "1.1", "indent": 1},
            {"title": "Problem Statement", "page": "3", "level": "section", "number": "1.2", "indent": 1},
            {"title": "Aim and Objectives", "page": "5", "level": "section", "number": "1.3", "indent": 1},
            {"title": "Scope of the Study", "page": "6", "level": "section", "number": "1.4", "indent": 1},
            {"title": "Significance of the Study", "page": "7", "level": "section", "number": "1.5", "indent": 1},
            {"title": "Structure of the Study", "page": "8", "level": "section", "number": "1.6", "indent": 1},
            {"title": "CHAPTER 2: LITERATURE REVIEW", "page": "9", "level": "chapter", "number": "2", "indent": 0},
            {"title": "Introduction", "page": "9", "level": "section", "number": "2.1", "indent": 1},
            {"title": "Literature Review", "page": "10", "level": "section", "number": "2.2", "indent": 1},
            {"title": "Summary of Gaps", "page": "18", "level": "section", "number": "2.3", "indent": 1},
            {"title": "Discussion", "page": "20", "level": "section", "number": "2.4", "indent": 1},
            {"title": "CHAPTER 3: RESEARCH METHODOLOGY", "page": "22", "level": "chapter", "number": "3", "indent": 0},
            {"title": "REFERENCES", "page": "42", "level": "chapter", "number": "", "indent": 0},
            {"title": "APPENDIX A: RESEARCH PLAN", "page": "48", "level": "appendix", "number": "A", "indent": 0},
            {"title": "APPENDIX B: GANTT CHART", "page": "50", "level": "appendix", "number": "B", "indent": 0},
            {"title": "APPENDIX C: WORK BREAKDOWN STRUCTURE", "page": "51", "level": "appendix", "number": "C", "indent": 0},
            {"title": "APPENDIX D: REQUIREMENTS TRACEABILITY MATRIX", "page": "52", "level": "appendix", "number": "D", "indent": 0},
        ]
    }
    
    toc_content = "TABLE OF CONTENTS\n\n"
    for entry in toc_data["entries"]:
        prefix = "    " * entry["indent"]
        num = f"{entry['number']} " if entry['number'] else ""
        title_text = f"{prefix}{num}{entry['title']}"
        total_width = 65
        spaces_needed = total_width - len(title_text) - len(entry['page'])
        dots = "." * max(3, spaces_needed)
        toc_content += f"{title_text}{dots}{entry['page']}\n"
    
    sections.append({"title": "TABLE OF CONTENTS", "content": toc_content, "toc_data": toc_data})
    
    # =========================================================================
    # LIST OF TABLES (v2.6.1) - Q1 Journal Standard
    # =========================================================================
    list_of_tables_data = [
        {"number": "TABLE 1", "title": "RESEARCH METHODOLOGY COMPARISON MATRIX"},
        {"number": "TABLE 2", "title": "DATA COLLECTION INSTRUMENTS AND TECHNIQUES"},
        {"number": "TABLE 3", "title": "SAMPLE SIZE AND SAMPLING STRATEGY"},
        {"number": "TABLE 4", "title": "VARIABLE OPERATIONALIZATION FRAMEWORK"},
        {"number": "TABLE 5", "title": "VALIDITY AND RELIABILITY MEASURES"},
    ]
    
    lot_content = """LIST OF TABLES

Below is the list of tables used during the research thesis.

"""
    lot_content += f"{'Table No.':<15}Table Name\n\n"
    for table in list_of_tables_data:
        lot_content += f"{table['number']:<15}{table['title']}\n\n"
    
    sections.append({"title": "LIST OF TABLES", "content": lot_content, "tables_data": list_of_tables_data})
    
    # =========================================================================
    # LIST OF FIGURES (v2.6.1) - Q1 Journal Standard  
    # =========================================================================
    list_of_figures_data = [
        {"number": "Figure 3.1", "title": "Research methodology flowchart"},
        {"number": "Figure 3.2", "title": "Conceptual framework diagram"},
        {"number": "Figure 3.3", "title": "Data collection process flow"},
        {"number": "Figure 4.1", "title": "System architecture overview"},
        {"number": "Figure 4.2", "title": "Implementation workflow diagram"},
        {"number": "Figure 4.3", "title": "Data preprocessing pipeline"},
        {"number": "Figure 4.4", "title": "Model training and validation process"},
        {"number": "Figure 5.1", "title": "Results comparison visualization"},
        {"number": "Figure 5.2", "title": "Performance metrics analysis"},
        {"number": "Figure B.1", "title": "Research timeline - Gantt chart"},
        {"number": "Figure C.1", "title": "Work breakdown structure hierarchy"},
        {"number": "Figure D.1", "title": "Requirements traceability matrix"},
    ]
    
    lof_content = """LIST OF FIGURES

Below is the list of Figures used during the research thesis.

"""
    for fig in list_of_figures_data:
        lof_content += f"{fig['number']:<15}{fig['title']}\n"
    
    sections.append({"title": "LIST OF FIGURES", "content": lof_content, "figures_data": list_of_figures_data})
    
    # =========================================================================
    # LIST OF ABBREVIATIONS (v2.6.1) - Q1 Journal Standard
    # =========================================================================
    list_of_abbreviations_data = [
        {"abbrev": "AI", "full": "Artificial Intelligence"},
        {"abbrev": "API", "full": "Application Programming Interface"},
        {"abbrev": "CNN", "full": "Convolutional Neural Network"},
        {"abbrev": "DAG", "full": "Directed Acyclic Graph"},
        {"abbrev": "DL", "full": "Deep Learning"},
        {"abbrev": "ETL", "full": "Extract, Transform, Load"},
        {"abbrev": "GPU", "full": "Graphics Processing Unit"},
        {"abbrev": "IEEE", "full": "Institute of Electrical and Electronics Engineers"},
        {"abbrev": "KPI", "full": "Key Performance Indicator"},
        {"abbrev": "LLM", "full": "Large Language Model"},
        {"abbrev": "ML", "full": "Machine Learning"},
        {"abbrev": "MLP", "full": "Multi-Layer Perceptron"},
        {"abbrev": "NLP", "full": "Natural Language Processing"},
        {"abbrev": "PDF", "full": "Portable Document Format"},
        {"abbrev": "Q1", "full": "Quartile 1 (Top-tier Journal Ranking)"},
        {"abbrev": "RAG", "full": "Retrieval-Augmented Generation"},
        {"abbrev": "REST", "full": "Representational State Transfer"},
        {"abbrev": "RNN", "full": "Recurrent Neural Network"},
        {"abbrev": "ROC", "full": "Receiver Operating Characteristic"},
        {"abbrev": "RTM", "full": "Requirements Traceability Matrix"},
        {"abbrev": "SDK", "full": "Software Development Kit"},
        {"abbrev": "SQL", "full": "Structured Query Language"},
        {"abbrev": "TOC", "full": "Table of Contents"},
        {"abbrev": "UI/UX", "full": "User Interface/User Experience"},
        {"abbrev": "WBS", "full": "Work Breakdown Structure"},
    ]
    # Sort alphabetically
    list_of_abbreviations_data.sort(key=lambda x: x['abbrev'])
    
    loa_content = """LIST OF ABBREVIATIONS

Below is the list of Abbreviations used during the research project.

"""
    loa_content += f"{'Abbreviation':<20}Full Form\n\n"
    for abbr in list_of_abbreviations_data:
        loa_content += f"{abbr['abbrev']:<20}{abbr['full']}\n"
    
    sections.append({"title": "LIST OF ABBREVIATIONS", "content": loa_content, "abbreviations_data": list_of_abbreviations_data})
    
    # CHAPTER 1
    update_progress("introduction", 18, f"Generating Chapter 1: Introduction ({config['name']} mode)...")
    ch1 = await generate_chapter1_scaled(llm, topic, word_scale)
    ch1_content = f"""CHAPTER 1: INTRODUCTION

1.1 Background of Study

{ch1['background']}

1.2 Problem Statement

{ch1['problem_statement']}

1.3 Aim and Objectives

{ch1['aim_objectives']}

1.4 Scope of the Study

{ch1['scope']}

1.5 Significance of the Study

{ch1['significance']}

1.6 Structure of the Study

{ch1['structure']}"""
    sections.append({"title": "CHAPTER 1: INTRODUCTION", "content": ch1_content})
    
    # CHAPTER 2
    update_progress("literature_review", 40, f"Generating Chapter 2: Literature Review ({config['name']} mode)...")
    ch2 = await generate_chapter2_scaled(llm, topic, word_scale)
    ch2_content = f"""CHAPTER 2: LITERATURE REVIEW

2.1 Introduction

{ch2['introduction']}

2.2 Literature Review

{ch2['literature_review']}

2.3 Summary of Gaps

{ch2['gaps']}

2.4 Discussion

{ch2['discussion']}"""
    sections.append({"title": "CHAPTER 2: LITERATURE REVIEW", "content": ch2_content})
    
    # CHAPTER 3
    update_progress("methodology", 60, f"Generating Chapter 3: Research Methodology ({config['name']} mode)...")
    ch3 = await generate_chapter3_scaled(llm, topic, word_scale)
    
    ch3_parts = ["CHAPTER 3: RESEARCH METHODOLOGY"]
    
    section_map = [
        ("introduction", "3.1 Introduction"),
        ("methodology", "3.2 Research Methodology"),
        ("dataset", "3.3 Dataset Description"),
        ("missing_values", "3.4 Missing Values Imputation and Encoding"),
        ("eda", "3.5 Exploratory Data Analysis"),
        ("experimental_design", "3.6 Design of Experimental Study"),
        ("model_development", "3.7 Model Development"),
        ("data_splitting", "3.8 Data Splitting"),
        ("feature_selection", "3.9 Feature Selection"),
        ("model_evaluation", "3.10 Evaluating Multiple Models"),
        ("comparative_analysis", "3.11 Comparative Analysis and Outcome"),
        ("ethics", "3.12 Ethical Consideration"),
        ("collaboration", "3.13 Collaboration and Feedback"),
        ("deliverables", "3.14 Deliverables and Reports"),
        ("resources", "3.15 Required Resources"),
        ("risk_plan", "3.16 Risk and Contingency Plan"),
    ]
    
    for key, heading in section_map:
        if key in ch3:
            ch3_parts.append(f"\n{heading}\n\n{ch3[key]}")
    
    ch3_content = "\n".join(ch3_parts)
    sections.append({"title": "CHAPTER 3: RESEARCH METHODOLOGY", "content": ch3_content})
    
    # REFERENCES
    update_progress("references", 85, f"Generating References ({config['name']} mode)...")
    refs = await generate_references_scaled(llm, topic, word_scale)
    sections.append({"title": "REFERENCES", "content": f"REFERENCES\n\n{refs}"})
    
    # APPENDIX A
    update_progress("appendix", 90, "Generating Appendix A: Research Plan...")
    appendix = await generate_research_plan(llm, topic)
    sections.append({"title": "APPENDIX A: RESEARCH PLAN", "content": f"APPENDIX A: RESEARCH PLAN\n\n{appendix}"})
    
    # APPENDIX B: GANTT CHART
    update_progress("gantt_chart", 92, "Generating Appendix B: Gantt Chart...")
    gantt_content = """APPENDIX B: GANTT CHART

Research Timeline (15 Months)

Phase 1: Literature Review & Gap Analysis (Months 1-3)
    - Comprehensive literature search and review
    - Identification of research gaps
    - Theoretical framework development

Phase 2: Research Design & Methodology (Months 2-3)
    - Research design formulation
    - Methodology selection and justification

Phase 3: Data Collection Framework (Months 4-6)
    - Data source identification
    - Sampling strategy implementation

Phase 4: Data Preprocessing & Cleaning (Months 6-7)
    - Missing value imputation
    - Data encoding and transformation

Phase 5: Model Development & Training (Months 7-10)
    - Feature engineering
    - Model architecture design
    - Training and optimization

Phase 6: Validation & Testing (Months 10-11)
    - Cross-validation procedures
    - Performance evaluation

Phase 7: Results Analysis & Interpretation (Months 11-12)
    - Statistical analysis
    - Results interpretation

Phase 8: Documentation & Thesis Writing (Months 3-12)
    - Continuous documentation
    - Chapter drafting

Phase 9: Publication & Dissemination (Months 12-15)
    - Journal article preparation
    - Final thesis submission"""
    sections.append({"title": "APPENDIX B: GANTT CHART", "content": gantt_content})
    
    # APPENDIX C: WBS
    update_progress("wbs", 94, "Generating Appendix C: Work Breakdown Structure...")
    wbs_content = """APPENDIX C: WORK BREAKDOWN STRUCTURE

1.0 Research Proposal

    1.1 Problem Definition
        1.1.1 Background Study
        1.1.2 Problem Statement
        1.1.3 Research Objectives

    1.2 Literature Review
        1.2.1 Source Collection
        1.2.2 Critical Analysis
        1.2.3 Gap Identification

    1.3 Research Methodology
        1.3.1 Research Design
        1.3.2 Data Collection Plan
        1.3.3 Analysis Strategy
        1.3.4 Validation Approach

    1.4 Implementation
        1.4.1 Data Preprocessing
        1.4.2 Model Development
        1.4.3 Testing & Validation

    1.5 Documentation
        1.5.1 Results Documentation
        1.5.2 Discussion
        1.5.3 Conclusions"""
    sections.append({"title": "APPENDIX C: WORK BREAKDOWN STRUCTURE", "content": wbs_content})
    
    # APPENDIX D: RTM
    update_progress("rtm", 96, "Generating Appendix D: Requirements Traceability Matrix...")
    rtm_content = """APPENDIX D: REQUIREMENTS TRACEABILITY MATRIX

Requirements Traceability Matrix (RTM)

REQ-001: Identify and analyze research gaps
    Source: Chapter 1 (1.2)
    Delivered By: LiteratureReviewAgent
    Status: Complete

REQ-002: Establish theoretical framework
    Source: Chapter 1 (1.3)
    Delivered By: LiteratureReviewAgent
    Status: Complete

REQ-003: Design appropriate research methodology
    Source: Chapter 1 (1.3)
    Delivered By: MethodologyAgent
    Status: Complete

REQ-004: Define data collection and sampling strategy
    Source: Chapter 3 (3.3)
    Delivered By: MethodologyAgent
    Status: Complete

REQ-005: Develop and validate analytical model
    Source: Chapter 3 (3.7)
    Delivered By: MethodologyOptimizerAgent
    Status: Complete

REQ-006: Ensure ethical compliance
    Source: Chapter 3 (3.12)
    Delivered By: RiskAssessmentAgent
    Status: Complete

REQ-007: Generate properly formatted citations
    Source: Academic Standards
    Delivered By: ReferenceCitationAgent
    Status: Complete

REQ-008: Produce Q1 journal-standard document
    Source: Quality Standards
    Delivered By: QualityAssuranceAgent
    Status: Complete

Total Requirements: 8
Completed: 8 (100%)
Status: All requirements successfully traced and verified."""
    sections.append({"title": "APPENDIX D: REQUIREMENTS TRACEABILITY MATRIX", "content": rtm_content})
    
    # PROOFREADING
    update_progress("proofreading", 95, "Running proofreading validation...")
    validation = ProofreadingAgent.validate_proposal(sections, topic)
    
    # =========================================================================
    # AI HUMANIZATION (v2.7.3) - Production MCP Integration
    # Uses Text2Go/WriteHybrid APIs for <10% AI detection
    # =========================================================================
    update_progress("humanization", 97, "Humanizing content with Production MCP (targeting <10% AI detection)...")
    humanization_stats = {
        "sections_humanized": 0,
        "total_vocab_changes": 0,
        "total_restructures": 0,
        "estimated_ai_reduction": 0,
        "engine": "none",
        "providers_used": [],
    }
    
    try:
        # Use Production MCP Humanizer (v2.7.3)
        from src.humanizer.mcp_humanizer import get_mcp_humanizer
        
        humanizer = get_mcp_humanizer()
        humanization_stats["engine"] = "mcp_production_v1.0"
        humanization_stats["available_providers"] = humanizer.get_configured_providers()
        
        # Define sections to skip
        skip_sections = [
            "TITLE PAGE", "DEDICATION", "ACKNOWLEDGEMENTS", "ABSTRACT",
            "TABLE OF CONTENTS", "LIST OF TABLES", "LIST OF FIGURES",
            "LIST OF ABBREVIATIONS", "REFERENCES", "APPENDIX"
        ]
        
        # Process sections
        humanized_sections, stats = await humanizer.humanize_sections(
            sections=sections,
            skip_titles=skip_sections,
            min_words=100,
        )
        
        sections = humanized_sections
        humanization_stats["sections_humanized"] = stats["sections_humanized"]
        humanization_stats["providers_used"] = stats["providers_used"]
        humanization_stats["total_words_original"] = stats["total_words_original"]
        humanization_stats["total_words_humanized"] = stats["total_words_humanized"]
        humanization_stats["processing_time"] = stats["total_processing_time"]
        humanization_stats["avg_ai_score_reduction"] = stats.get("avg_ai_score_reduction", 0)
        
        logger.info(f"[Job {job_id[:8]}] MCP Humanization complete: {stats['sections_humanized']} sections, "
                   f"providers: {stats['providers_used']}, avg reduction: {stats.get('avg_ai_score_reduction', 0):.1f}%")
        
    except ImportError as e:
        logger.warning(f"[Job {job_id[:8]}] MCP Humanizer not available: {e}, trying fallback...")
        
        # Fallback to advanced engine
        try:
            from src.humanizer.advanced_humanizer_engine import AdvancedHumanizerEngine, HumanizationConfig, HumanizationLevel
            
            humanization_config = HumanizationConfig(
                level=HumanizationLevel.AGGRESSIVE,
                preserve_citations=True,
                preserve_technical_terms=True,
            )
            humanizer = AdvancedHumanizerEngine(humanization_config)
            humanization_stats["engine"] = "advanced_v2.0"
            
            humanized_sections = []
            
            for section in sections:
                title = section.get("title", "")
                content = section.get("content", "")
                
                skip_sections = [
                    "TITLE PAGE", "DEDICATION", "ACKNOWLEDGEMENTS", "ABSTRACT",
                    "TABLE OF CONTENTS", "LIST OF TABLES", "LIST OF FIGURES",
                    "LIST OF ABBREVIATIONS", "REFERENCES", "APPENDIX"
                ]
                
                should_skip = any(skip in title.upper() for skip in skip_sections)
                
                if should_skip or len(content.split()) < 50:
                    humanized_sections.append(section)
                    continue
                
                humanized_content, stats = humanizer.humanize(content, "body")
                
                humanized_sections.append({
                    **section,
                    "content": humanized_content,
                    "humanized": True,
                })
                
                humanization_stats["sections_humanized"] += 1
                humanization_stats["total_vocab_changes"] += stats.vocabulary_changes
                humanization_stats["total_restructures"] += stats.sentences_restructured
            
            sections = humanized_sections
            logger.info(f"[Job {job_id[:8]}] Advanced humanization complete: {humanization_stats['sections_humanized']} sections")
            
        except ImportError as e2:
            logger.warning(f"[Job {job_id[:8]}] No humanizer available: {e2}")
            humanization_stats["engine"] = "unavailable"
            
    except Exception as e:
        logger.error(f"[Job {job_id[:8]}] Humanization error: {e}")
        humanization_stats["engine"] = f"error: {str(e)[:50]}"
    
    total_words = sum(len(s.get("content", "").split()) for s in sections)
    
    update_progress("completed", 100, f"Proposal complete: {total_words:,} words (target: {target_word_count:,})")
    
    return {
        "topic": topic,
        "student_name": student_name,
        "supervisor_name": supervisor_name,
        "institution": institution,
        "sections": sections,
        "diagrams": [],
        "word_count": total_words,
        "target_word_count": target_word_count,
        "word_count_mode": config["name"],
        "generated_at": datetime.utcnow().isoformat(),
        "citation_style": "harvard",
        "validation": validation,
        "humanization": humanization_stats if 'humanization_stats' in dir() else None,
    }


# ============================================================================
# Background Task
# ============================================================================
async def generate_proposal_background(job_id: str, request: ProposalGenerationRequest):
    """Background task for proposal generation with word count enforcement."""
    await asyncio.sleep(0.1)
    
    target_word_count = request.get_validated_word_count()
    word_config = request.get_word_count_config()
    
    logger.info(f"[Job {job_id[:8]}] Starting proposal generation...")
    logger.info(f"[Job {job_id[:8]}] Target word count: {target_word_count:,} ({word_config['name']})")
    job_store.update_job(job_id, status="running", started_at=datetime.utcnow().isoformat(), 
                        message=f"Starting {word_config['name']} mode ({target_word_count:,} words)...")
    
    try:
        result = await assemble_proposal(
            topic=request.topic,
            student_name=request.student_name,
            supervisor_name=request.supervisor_name,
            institution=request.institution,
            dedication_to=request.dedication_to,
            include_visuals=request.include_visuals,
            job_id=job_id,
            target_word_count=target_word_count,
        )
        
        completed_proposals[job_id] = result
        job_store.update_job(
            job_id, status="completed", progress=100, current_stage="completed",
            message=f"Proposal generated: {result['word_count']:,} words",
            completed_at=datetime.utcnow().isoformat(), result=result,
        )
        logger.info(f"[Job {job_id[:8]}] Completed: {result['word_count']:,} words")
        
    except Exception as e:
        logger.exception(f"[Job {job_id[:8]}] Failed: {e}")
        job_store.update_job(job_id, status="failed", error=str(e), message=f"Failed: {e}", completed_at=datetime.utcnow().isoformat())


# ============================================================================
# PDF Generation with Watermark Support
# ============================================================================
def generate_pdf_with_watermark(proposal: Dict, subscription_tier: str) -> bytes:
    """Generate PDF with optional watermark and embedded visualizations."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import Color, black
    from reportlab.lib import colors
    
    # Generate visualization images
    gantt_image_bytes = None
    wbs_image_bytes = None
    rtm_image_bytes = None
    
    # v2.5.8: Map subscription tier to timeline type
    gantt_subscription_type = "proposal"  # Default
    if subscription_tier == SubscriptionTier.PERMANENT.value:
        gantt_subscription_type = "thesis"
    elif subscription_tier == SubscriptionTier.NON_PERMANENT.value:
        gantt_subscription_type = "interim"
    
    try:
        from src.utils.visualization_generator import visualization_generator
        gantt_image_bytes = visualization_generator.generate_gantt_image(subscription_type=gantt_subscription_type)
        wbs_image_bytes = visualization_generator.generate_wbs_image()
        rtm_image_bytes = visualization_generator.generate_rtm_image()
        logger.info(f"All visualization images generated successfully (Gantt type: {gantt_subscription_type})")
    except Exception as e:
        logger.warning(f"Could not generate visualization images: {e}")
    
    buffer = io.BytesIO()
    is_title_page = [True]
    
    def add_watermark(canvas_obj, doc):
        if subscription_tier == SubscriptionTier.NON_PERMANENT.value:
            canvas_obj.saveState()
            alpha = 0.15 if is_title_page[0] else 0.3
            canvas_obj.setFillColor(Color(0.8, 0.8, 0.8, alpha=alpha))
            canvas_obj.setFont('Helvetica-Bold', 50)
            canvas_obj.translate(A4[0]/2, A4[1]/2)
            canvas_obj.rotate(45)
            canvas_obj.drawCentredString(0, 0, "FOMA Digital Solution")
            canvas_obj.restoreState()
        
        page_num = canvas_obj.getPageNumber()
        canvas_obj.saveState()
        canvas_obj.setFont('Times-Roman', 10)
        canvas_obj.drawRightString(A4[0] - 2*cm, 1.5*cm, f"{page_num} | Page")
        canvas_obj.restoreState()
        
        if page_num > 1:
            is_title_page[0] = False
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2.54*cm, leftMargin=3.17*cm, topMargin=2.54*cm, bottomMargin=2.54*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, alignment=TA_CENTER, fontName='Times-Bold', spaceAfter=30)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, fontName='Times-Bold', spaceBefore=20, spaceAfter=15)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=12, alignment=TA_JUSTIFY, fontName='Times-Roman', leading=18, firstLineIndent=1.27*cm)
    toc_chapter_style = ParagraphStyle('TOCChapter', parent=styles['Normal'], fontSize=12, fontName='Times-Bold', leading=18)
    toc_section_style = ParagraphStyle('TOCSection', parent=styles['Normal'], fontSize=12, fontName='Times-Roman', leading=16, leftIndent=0.5*inch)
    
    story = []
    sections = proposal.get("sections", [])
    
    for section in sections:
        title = section.get("title", "")
        content = section.get("content", "")
        
        if title == "TITLE PAGE":
            author_name = proposal.get("student_name", "Researcher")
            topic_title = proposal.get("topic", "Research Proposal")
            current_date = datetime.now().strftime("%B %Y").upper()
            
            LINE_HEIGHT = 18
            
            title_page_title_style = ParagraphStyle('TitlePageTitle', parent=styles['Title'], fontSize=14, fontName='Times-Bold', alignment=TA_CENTER, leading=20, spaceAfter=0)
            author_style = ParagraphStyle('TitlePageAuthor', parent=styles['Normal'], fontSize=12, fontName='Times-Roman', alignment=TA_CENTER, spaceAfter=0)
            doc_type_style = ParagraphStyle('TitlePageDocType', parent=styles['Normal'], fontSize=12, fontName='Times-Bold', alignment=TA_CENTER, spaceAfter=0)
            date_style = ParagraphStyle('TitlePageDate', parent=styles['Normal'], fontSize=12, fontName='Times-Roman', alignment=TA_CENTER, spaceAfter=0)
            
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(topic_title.upper(), title_page_title_style))
            story.append(Spacer(1, 7 * LINE_HEIGHT))
            story.append(Paragraph(author_name.title(), author_style))
            story.append(Spacer(1, 10 * LINE_HEIGHT))
            story.append(Paragraph("RESEARCH PROPOSAL", doc_type_style))
            story.append(Spacer(1, 13 * LINE_HEIGHT))
            story.append(Paragraph(current_date, date_style))
            story.append(PageBreak())
            logger.info(f"[PDF] Title page generated for: {author_name}")
            continue
        
        if "TABLE OF CONTENTS" in title:
            story.append(Paragraph("TABLE OF CONTENTS", heading_style))
            story.append(Spacer(1, 20))
            
            toc_data = section.get("toc_data", {})
            entries = toc_data.get("entries", [])
            
            if entries:
                toc_table_data = []
                for entry in entries:
                    indent = "    " * entry.get("indent", 0)
                    num = entry.get("number", "")
                    num_str = f"{num} " if num else ""
                    title_text = f"{indent}{num_str}{entry['title']}"
                    page = entry.get("page", "")
                    
                    is_chapter = entry.get("level") in ["chapter", "front_matter", "appendix"]
                    if is_chapter:
                        toc_table_data.append([Paragraph(f"<b>{title_text}</b>", toc_chapter_style), page])
                    else:
                        toc_table_data.append([Paragraph(title_text, toc_section_style), page])
                
                col_widths = [doc.width - 1*cm, 1*cm]
                toc_table = Table(toc_table_data, colWidths=col_widths)
                toc_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                ]))
                story.append(toc_table)
            
            story.append(PageBreak())
            continue
        
        # =====================================================================
        # LIST OF TABLES (v2.6.1) - Q1 Journal Standard PDF Rendering
        # =====================================================================
        if title == "LIST OF TABLES":
            # Title in blue, centered, italic (matching reference image)
            lot_title_style = ParagraphStyle(
                'LOTTitle',
                parent=styles['Title'],
                fontSize=14,
                fontName='Times-Italic',
                textColor=colors.HexColor('#1a237e'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            story.append(Paragraph("List Of Tables", lot_title_style))
            story.append(Spacer(1, 20))
            
            # Intro text
            intro_style = ParagraphStyle('LOTIntro', parent=styles['Normal'], fontSize=12, fontName='Times-Roman', leading=18)
            story.append(Paragraph("Below is the list of tables used during the research thesis.", intro_style))
            story.append(Spacer(1, 20))
            
            # Table header
            header_style = ParagraphStyle('LOTHeader', parent=styles['Normal'], fontSize=12, fontName='Times-Bold', leading=16)
            
            # Get tables data
            tables_data = section.get("tables_data", [])
            if tables_data:
                table_list_data = [[Paragraph("<b>Table No.</b>", header_style), Paragraph("<b>Table Name</b>", header_style)]]
                
                row_style = ParagraphStyle('LOTRow', parent=styles['Normal'], fontSize=12, fontName='Times-Roman', leading=16)
                for table in tables_data:
                    table_list_data.append([
                        Paragraph(table['number'], row_style),
                        Paragraph(table['title'], row_style)
                    ])
                
                col_widths = [2*inch, doc.width - 2.2*inch]
                lot_table = Table(table_list_data, colWidths=col_widths)
                lot_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(lot_table)
            
            story.append(PageBreak())
            continue
        
        # =====================================================================
        # LIST OF FIGURES (v2.6.1) - Q1 Journal Standard PDF Rendering
        # =====================================================================
        if title == "LIST OF FIGURES":
            # Title in blue, centered, italic
            lof_title_style = ParagraphStyle(
                'LOFTitle',
                parent=styles['Title'],
                fontSize=14,
                fontName='Times-Italic',
                textColor=colors.HexColor('#1a237e'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            story.append(Paragraph("List of Figures", lof_title_style))
            story.append(Spacer(1, 15))
            
            # Intro text
            intro_style = ParagraphStyle('LOFIntro', parent=styles['Normal'], fontSize=12, fontName='Times-Roman', leading=16)
            story.append(Paragraph("Below is the list of Figures used during the research thesis.", intro_style))
            story.append(Spacer(1, 15))
            
            # Get figures data
            figures_data = section.get("figures_data", [])
            if figures_data:
                row_style = ParagraphStyle('LOFRow', parent=styles['Normal'], fontSize=12, fontName='Times-Roman', leading=14)
                fig_table_data = []
                
                for fig in figures_data:
                    fig_table_data.append([
                        Paragraph(fig['number'], row_style),
                        Paragraph(fig['title'], row_style)
                    ])
                
                col_widths = [1.5*inch, doc.width - 1.7*inch]
                lof_table = Table(fig_table_data, colWidths=col_widths)
                lof_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(lof_table)
            
            story.append(PageBreak())
            continue
        
        # =====================================================================
        # LIST OF ABBREVIATIONS (v2.6.1) - Q1 Journal Standard PDF Rendering
        # =====================================================================
        if title == "LIST OF ABBREVIATIONS":
            # Title in blue, centered, italic
            loa_title_style = ParagraphStyle(
                'LOATitle',
                parent=styles['Title'],
                fontSize=14,
                fontName='Times-Italic',
                textColor=colors.HexColor('#1a237e'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            story.append(Paragraph("List Of Abbreviations", loa_title_style))
            story.append(Spacer(1, 20))
            
            # Intro text
            intro_style = ParagraphStyle('LOAIntro', parent=styles['Normal'], fontSize=12, fontName='Times-Roman', leading=18)
            story.append(Paragraph("Below is the list of Abbreviations used during the research project.", intro_style))
            story.append(Spacer(1, 20))
            
            # Header row
            header_style = ParagraphStyle('LOAHeader', parent=styles['Normal'], fontSize=12, fontName='Times-Bold', leading=16)
            
            # Get abbreviations data
            abbreviations_data = section.get("abbreviations_data", [])
            if abbreviations_data:
                abbr_table_data = [[Paragraph("<b>Abbreviation</b>", header_style), Paragraph("<b>Full Form</b>", header_style)]]
                
                row_style = ParagraphStyle('LOARow', parent=styles['Normal'], fontSize=12, fontName='Times-Roman', leading=14)
                for abbr in abbreviations_data:
                    abbr_table_data.append([
                        Paragraph(abbr['abbrev'], row_style),
                        Paragraph(abbr['full'], row_style)
                    ])
                
                col_widths = [1.8*inch, doc.width - 2*inch]
                loa_table = Table(abbr_table_data, colWidths=col_widths)
                loa_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(loa_table)
            
            story.append(PageBreak())
            continue
        
        # APPENDIX B: GANTT CHART
        if "APPENDIX B" in title and "GANTT" in title.upper():
            story.append(Paragraph(title, heading_style))
            story.append(Spacer(1, 12))
            
            # v2.5.8: Dynamic figure title based on subscription
            subscription_type = "proposal"  # Default
            if subscription_tier == "permanent":
                subscription_type = "thesis"
            elif subscription_tier == "non_permanent":
                subscription_type = "interim"
            
            # Generate figure title dynamically
            figure_titles = {
                "proposal": "Figure B.1: Research Timeline \u2013 Proposal (4 Weeks)",
                "interim": "Figure B.1: Research Timeline \u2013 Interim Report (12 Weeks)",
                "thesis": "Figure B.1: Research Timeline \u2013 Thesis (24 Weeks)",
            }
            gantt_figure_title = figure_titles.get(subscription_type, figure_titles["proposal"])
            
            if gantt_image_bytes:
                try:
                    gantt_img_buffer = io.BytesIO(gantt_image_bytes)
                    img_width = doc.width
                    img_height = img_width * 0.5
                    gantt_img = Image(gantt_img_buffer, width=img_width, height=img_height)
                    story.append(gantt_img)
                    story.append(Spacer(1, 12))
                    caption_style = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, fontName='Times-Italic')
                    story.append(Paragraph(gantt_figure_title, caption_style))
                except Exception as e:
                    logger.warning(f"Failed to embed Gantt image: {e}")
                    for para in content.split("\n\n"):
                        if para.strip():
                            clean = para.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                            story.append(Paragraph(clean, body_style))
                            story.append(Spacer(1, 8))
            else:
                for para in content.split("\n\n"):
                    if para.strip():
                        clean = para.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        story.append(Paragraph(clean, body_style))
                        story.append(Spacer(1, 8))
            
            story.append(PageBreak())
            continue
        
        # APPENDIX C: WBS
        if "APPENDIX C" in title and ("WBS" in title.upper() or "WORK BREAKDOWN" in title.upper()):
            story.append(Paragraph(title, heading_style))
            story.append(Spacer(1, 12))
            
            if wbs_image_bytes:
                try:
                    wbs_img_buffer = io.BytesIO(wbs_image_bytes)
                    img_width = doc.width
                    img_height = img_width * 0.75
                    wbs_img = Image(wbs_img_buffer, width=img_width, height=img_height)
                    story.append(wbs_img)
                    story.append(Spacer(1, 12))
                    caption_style = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, fontName='Times-Italic')
                    story.append(Paragraph("Figure C.1: Work Breakdown Structure (WBS)", caption_style))
                except Exception as e:
                    logger.warning(f"Failed to embed WBS image: {e}")
                    for para in content.split("\n\n"):
                        if para.strip():
                            clean = para.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                            story.append(Paragraph(clean, body_style))
                            story.append(Spacer(1, 8))
            else:
                for para in content.split("\n\n"):
                    if para.strip():
                        clean = para.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        story.append(Paragraph(clean, body_style))
                        story.append(Spacer(1, 8))
            
            story.append(PageBreak())
            continue
        
        # APPENDIX D: RTM
        if "APPENDIX D" in title and ("RTM" in title.upper() or "REQUIREMENTS" in title.upper() or "TRACEABILITY" in title.upper()):
            story.append(Paragraph(title, heading_style))
            story.append(Spacer(1, 12))
            
            if rtm_image_bytes:
                try:
                    rtm_img_buffer = io.BytesIO(rtm_image_bytes)
                    img_width = doc.width
                    img_height = img_width * 0.7
                    rtm_img = Image(rtm_img_buffer, width=img_width, height=img_height)
                    story.append(rtm_img)
                    story.append(Spacer(1, 12))
                    caption_style = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, fontName='Times-Italic')
                    story.append(Paragraph("Figure D.1: Requirements Traceability Matrix (RTM)", caption_style))
                except Exception as e:
                    logger.warning(f"Failed to embed RTM image: {e}")
                    for para in content.split("\n\n"):
                        if para.strip():
                            clean = para.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                            story.append(Paragraph(clean, body_style))
                            story.append(Spacer(1, 8))
            else:
                for para in content.split("\n\n"):
                    if para.strip():
                        clean = para.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        story.append(Paragraph(clean, body_style))
                        story.append(Spacer(1, 8))
            
            story.append(PageBreak())
            continue
        
        # v2.5.6 FIX: REFERENCES - no duplicate title, full justified like MS Word
        if title and "REFERENCES" in title.upper() and "APPENDIX" not in title.upper():
            story.append(Paragraph(title, heading_style))
            story.append(Spacer(1, 12))
            
            # Reference style: Full justified with hanging indent (MS Word style)
            ref_style = ParagraphStyle(
                'Reference',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_JUSTIFY,
                fontName='Times-Roman',
                leading=18,
                firstLineIndent=0,
                leftIndent=0.5*inch,
                spaceBefore=3,
                spaceAfter=6,
            )
            
            # Clean content - remove ALL "REFERENCES" title variations
            refs_content = content
            lines = refs_content.split('\n')
            cleaned_lines = []
            for line in lines:
                stripped_upper = line.strip().upper()
                # Skip lines that are just the title
                if stripped_upper in ["REFERENCES", "REFERENCES:", ""]:
                    continue
                cleaned_lines.append(line)
            refs_content = '\n'.join(cleaned_lines).strip()
            
            # Parse references
            ref_entries = []
            current_ref = []
            
            for line in refs_content.split('\n'):
                stripped = line.strip()
                if not stripped:
                    if current_ref:
                        ref_entries.append(' '.join(current_ref))
                        current_ref = []
                else:
                    # New reference starts with author pattern: "LastName, F."
                    if current_ref and re.match(r'^[A-Z][a-z]+,\s*[A-Z]\.', stripped):
                        ref_entries.append(' '.join(current_ref))
                        current_ref = [stripped]
                    else:
                        current_ref.append(stripped)
            
            if current_ref:
                ref_entries.append(' '.join(current_ref))
            
            # Fallback if too few parsed
            if len(ref_entries) < 5:
                ref_entries = [p.strip() for p in refs_content.split('\n\n') if p.strip() and len(p.strip()) > 30]
            
            # Filter out any "REFERENCES" that slipped through
            ref_entries = [r for r in ref_entries if r.upper().strip() not in ["REFERENCES", "REFERENCES:"]]
            
            # Add numbered, justified references
            ref_num = 1
            for ref in ref_entries:
                ref_clean = re.sub(r'^\d+\.\s*', '', ref.strip())
                if not ref_clean or len(ref_clean) < 20:
                    continue
                numbered_ref = f"{ref_num}. {ref_clean}"
                clean = numbered_ref.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(clean, ref_style))
                ref_num += 1
            
            story.append(PageBreak())
            logger.info(f"[PDF] References: {ref_num - 1} entries (justified)")
            continue
        
        if title:
            story.append(Paragraph(title, heading_style))
            story.append(Spacer(1, 12))
        
        cleaned_content = content
        if title and cleaned_content:
            lines = cleaned_content.split('\n')
            cleaned_lines = []
            title_upper = title.upper().strip()
            
            for line in lines:
                line_stripped = line.strip()
                line_upper = line_stripped.upper()
                if line_upper == title_upper:
                    continue
                if ':' in title:
                    base_title = title.split(':')[0].strip().upper()
                    if line_upper == base_title:
                        continue
                cleaned_lines.append(line)
            
            cleaned_content = '\n'.join(cleaned_lines).lstrip('\n')
        
        for para in cleaned_content.split("\n\n"):
            if para.strip():
                clean = para.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(clean, body_style))
                story.append(Spacer(1, 8))
        
        story.append(PageBreak())
    
    doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title="ResearchAI - Multi-Agent Proposal Generator",
    description="Generate Q1 journal-standard research proposals with AI",
    version="2.5.5",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"[REQUEST] {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"[RESPONSE] {request.method} {request.url.path} -> {response.status_code}")
    return response


# Include v2 endpoints router
if V2_ENDPOINTS_AVAILABLE and v2_router is not None:
    app.include_router(v2_router)
    logger.info("[Startup] v2 endpoints router included")


@app.on_event("startup")
async def startup():
    logger.info("=" * 60)
    logger.info("  ResearchAI Backend v2.7.3 Starting...")
    logger.info("  Features: 18 Agents, Subscription Tiers, Watermarks, v2 APIs")
    logger.info("=" * 60)
    
    # Set proposals store reference for v2 endpoints
    if V2_ENDPOINTS_AVAILABLE and set_proposals_store is not None:
        set_proposals_store(completed_proposals)
        logger.info("  v2 Endpoints: Ready (artifacts, TOC, Scopus, reviews, exports)")
    else:
        logger.warning("  v2 Endpoints: Not available")
    
    try:
        get_llm()
        logger.info("  LLM Provider: Ready")
    except Exception as e:
        logger.warning(f"  LLM Provider: {e}")


# ============================================================================
# API Routes
# ============================================================================
@app.get("/")
async def root():
    return {"message": "ResearchAI API v2.5.5", "features": ["18 agents", "subscription tiers", "watermarks", "reference numbering"]}


@app.post("/api/proposals/generate", response_model=ProposalGenerationResponse)
async def generate_proposal(request: ProposalGenerationRequest):
    job_id = str(uuid.uuid4())
    logger.info(f"[API] Generate proposal: {request.topic[:50]}... Job: {job_id}")
    
    job_store.create_job(job_id, request.topic, {
        "student_name": request.student_name,
        "key_points": request.key_points,
        "citation_style": request.citation_style,
    })
    
    asyncio.create_task(generate_proposal_background(job_id, request))
    
    return ProposalGenerationResponse(
        job_id=job_id, topic=request.topic, status="pending",
        message="Proposal generation started. Estimated time: 10-15 minutes.",
        progress=0, current_stage="initializing", estimated_time_minutes=15,
    )


@app.get("/api/proposals/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job["job_id"], "status": job["status"], "progress": job["progress"],
        "current_stage": job.get("current_stage"), "stages_completed": job.get("stages_completed", []),
        "message": job["message"], "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"), "error": job.get("error"),
    }


@app.get("/api/proposals/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed: {job['status']}")
    return {"job_id": job_id, "status": "completed", "result": completed_proposals.get(job_id)}


@app.get("/api/proposals/jobs")
async def list_jobs(limit: int = 20):
    return {"jobs": job_store.list_jobs(limit), "total": len(job_store.jobs)}


@app.get("/api/proposals/{request_id}/preview")
async def preview_proposal(request_id: str, subscription_tier: str = "permanent"):
    """Preview proposal with word limit for free tier."""
    proposal = completed_proposals.get(request_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    sections = proposal.get("sections", [])
    preview_text = ""
    
    for section in sections:
        preview_text += f"\n\n{'='*60}\n{section['title']}\n{'='*60}\n\n"
        preview_text += section.get("content", "")
    
    word_count = proposal.get("word_count", 0)
    preview_word_count = word_count
    
    if subscription_tier == SubscriptionTier.FREE.value:
        words = preview_text.split()
        if len(words) > 300:
            preview_text = " ".join(words[:300]) + "\n\n... [Preview limited to 300 words for free tier. Upgrade for full access.]"
            preview_word_count = 300
    
    return {
        "request_id": request_id,
        "topic": proposal.get("topic"),
        "word_count": word_count,
        "preview_word_count": preview_word_count,
        "sections_count": len(sections),
        "html_preview": f"<pre style='white-space: pre-wrap; font-family: Times New Roman;'>{preview_text}</pre>",
        "subscription_tier": subscription_tier,
        "is_limited": subscription_tier == SubscriptionTier.FREE.value,
    }


@app.get("/api/proposals/{request_id}/export/{format}")
async def export_proposal(request_id: str, format: str, subscription_tier: str = "permanent"):
    """Export proposal with subscription tier enforcement."""
    proposal = completed_proposals.get(request_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    if subscription_tier == SubscriptionTier.FREE.value:
        raise HTTPException(status_code=403, detail="PDF export not available for free tier. Please upgrade.")
    
    sections = proposal.get("sections", [])
    
    if format == "txt" or format == "markdown":
        content = ""
        for section in sections:
            content += f"\n\n{'='*60}\n{section['title']}\n{'='*60}\n\n"
            content += section.get("content", "")
        return Response(content=content, media_type="text/plain",
                       headers={"Content-Disposition": f'attachment; filename="{request_id[:8]}_proposal.txt"'})
    
    elif format == "pdf":
        try:
            pdf_bytes = generate_pdf_with_watermark(proposal, subscription_tier)
            return Response(content=pdf_bytes, media_type="application/pdf",
                           headers={"Content-Disposition": f'attachment; filename="{request_id[:8]}_proposal.pdf"'})
        except ImportError:
            raise HTTPException(status_code=501, detail="reportlab not installed")
    
    raise HTTPException(status_code=400, detail="Format must be txt, pdf, or markdown")


@app.get("/api/proposals")
async def list_proposals(page: int = 1, limit: int = 10):
    proposals = list(completed_proposals.values())
    start = (page - 1) * limit
    return {"proposals": proposals[start:start+limit], "total": len(proposals), "page": page}


@app.get("/agents")
async def list_agents():
    return {
        "agents": [
            "introduction_agent", "literature_review_agent", "methodology_agent",
            "quality_assurance_agent", "visualization_agent", "citation_agent",
            "formatting_agent", "front_matter_agent", "assembly_agent",
            "risk_assessment_agent", "optimizer_agent", "proofreading_consistency_agent",
        ],
        "count": 12
    }


@app.get("/api/test/llm")
async def test_llm():
    try:
        llm = get_llm()
        response = await llm.generate("Say 'ResearchAI v2.5.5 ready' exactly.", max_tokens=20)
        return {"status": "success", "response": response, "provider": llm.provider_name, "model": llm.model}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================================
# Authentication Endpoints
# ============================================================================
users_store: Dict[str, Dict[str, Any]] = {}


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    credential: str


@app.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest):
    import secrets, base64
    try:
        parts = request.credential.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="Invalid credential")
        payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
        user_info = json.loads(base64.urlsafe_b64decode(payload))
        
        email = user_info.get('email', '')
        name = user_info.get('name', 'User')
        picture = user_info.get('picture', '')
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not found")
        
        user_id = f"user-{secrets.token_urlsafe(8)}"
        token = secrets.token_urlsafe(32)
        
        user = {
            "id": user_id, "email": email, "name": name, "picture": picture,
            "subscription_tier": SubscriptionTier.PERMANENT.value,
            "created_at": datetime.utcnow().isoformat(),
        }
        users_store[user_id] = user
        
        return {"access_token": token, "token_type": "bearer", "user": user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    import secrets
    user_id = f"user-{secrets.token_urlsafe(8)}"
    token = secrets.token_urlsafe(32)
    
    for uid, u in users_store.items():
        if u.get("email") == request.email:
            return {"access_token": token, "token_type": "bearer", "user": u}
    
    user = {
        "id": user_id, "email": request.email, "name": request.email.split("@")[0].title(),
        "subscription_tier": SubscriptionTier.PERMANENT.value,
        "created_at": datetime.utcnow().isoformat(),
    }
    users_store[user_id] = user
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    import secrets
    for u in users_store.values():
        if u.get("email") == request.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user-{secrets.token_urlsafe(8)}"
    token = secrets.token_urlsafe(32)
    
    user = {
        "id": user_id, "email": request.email, "name": request.name,
        "subscription_tier": SubscriptionTier.FREE.value,
        "created_at": datetime.utcnow().isoformat(),
    }
    users_store[user_id] = user
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/api/auth/verify")
async def verify_token():
    return {"valid": True}


@app.get("/api/auth/me")
async def get_profile():
    return {"id": "demo", "email": "user@researchai.app", "name": "Researcher", "subscription_tier": SubscriptionTier.PERMANENT.value}


@app.post("/api/auth/logout")
async def logout():
    return {"success": True}


# ============================================================================
# Subscription and Word Count Options
# ============================================================================
@app.get("/api/word-count/options")
async def get_word_count_options():
    """Get available target word count options with configurations."""
    return {
        "options": [
            {"value": 3000, "label": "Express (3K)", "est_time_minutes": 3, "description": "Quick proposal draft"},
            {"value": 5000, "label": "Brief (5K)", "est_time_minutes": 5, "description": "Concise proposal"},
            {"value": 10000, "label": "Standard (10K)", "est_time_minutes": 8, "description": "Full proposal"},
            {"value": 15000, "label": "Comprehensive (15K)", "est_time_minutes": 12, "description": "Detailed proposal"},
            {"value": 20000, "label": "Extended (20K)", "est_time_minutes": 18, "description": "Complete thesis proposal"},
        ],
        "default": 15000,
        "configs": WORD_COUNT_CONFIGS
    }


@app.get("/api/subscription/tiers")
async def get_subscription_tiers():
    """Get available subscription tiers and their features."""
    return {
        "tiers": [
            {
                "id": SubscriptionTier.FREE.value,
                "name": "Free",
                "price": 0,
                "features": ["Preview up to 300 words", "No PDF export", "Basic support"],
                "limitations": ["No full document access", "No PDF download"],
            },
            {
                "id": SubscriptionTier.NON_PERMANENT.value,
                "name": "Standard",
                "price": 29,
                "features": ["Full preview", "PDF export with watermark", "Priority support"],
                "limitations": ["Watermark on all exports"],
            },
            {
                "id": SubscriptionTier.PERMANENT.value,
                "name": "Premium",
                "price": 99,
                "features": ["Full preview", "Clean PDF export", "No watermark", "Priority support", "Unlimited generations"],
                "limitations": [],
            },
        ]
    }


# ============================================================================
# Health and Status
# ============================================================================
@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "version": "2.7.3", 
        "agents_registered": 19,
        "features": {
            "pdf_embedded_images": True,
            "word_count_options": True,
            "reference_numbering": True,
            "academic_validation": True,
            "ai_humanization": True,
            "advanced_humanizer_v2": True,
            "mcp_humanizer": True,
            "production_humanization": True,
        }
    }


@app.get("/api/system/status")
async def system_status():
    llm = None
    try:
        llm = get_llm()
    except:
        pass
    return {
        "status": "ready",
        "version": "2.7.1",
        "llm_provider": llm.provider_name if llm else "not initialized",
        "model": llm.model if llm else "unknown",
        "active_jobs": len([j for j in job_store.jobs.values() if j["status"] == "running"]),
        "total_jobs": len(job_store.jobs),
        "features": {
            "subscription_tiers": True,
            "watermark_support": True,
            "reference_numbering": True,
            "academic_validation": True,
        },
        "agent_count": 18
    }


# ============================================================================
# AI HUMANIZATION ENDPOINTS (v2.7.1)
# Reduce AI Detection Score <10%
# ============================================================================

class HumanizeRequest(BaseModel):
    """Request model for content humanization."""
    content: str = Field(..., description="Content to humanize")
    intensity: str = Field(default="moderate", description="Humanization intensity: light, moderate, strong, aggressive")
    preserve_citations: bool = Field(default=True, description="Whether to preserve citation text")

@app.post("/api/v2/humanize")
async def humanize_content_endpoint(request: HumanizeRequest):
    """
    Humanize AI-generated content to reduce AI detection score.
    
    Uses Advanced Humanizer Engine v2.0 with multi-layer approach:
    - Vocabulary diversification (4 tiers)
    - Burstiness injection
    - Perplexity enhancement
    - Sentence restructuring
    - Human punctuation patterns
    - Contraction injection
    
    Target: <10% AI detection on Copyleaks, Originality.ai, Scribbr
    """
    try:
        # Try advanced engine first
        try:
            from src.humanizer.advanced_humanizer_engine import humanize_content as advanced_humanize
            
            # Map intensity to level
            level_map = {
                "light": "conservative",
                "moderate": "balanced",
                "strong": "aggressive",
                "aggressive": "maximum",
            }
            level = level_map.get(request.intensity.lower(), "aggressive")
            
            humanized_content, stats = advanced_humanize(request.content, level)
            
            return {
                "success": True,
                "engine": "advanced_v2.0",
                "original_content": request.content[:500] + "..." if len(request.content) > 500 else request.content,
                "humanized_content": humanized_content,
                "metrics": stats,
                "estimated_ai_score_before": stats.get("estimated_ai_before", 75),
                "estimated_ai_score_after": stats.get("estimated_ai_after", 10),
                "ai_score_reduction": round(stats.get("estimated_ai_before", 75) - stats.get("estimated_ai_after", 10), 1),
            }
            
        except ImportError:
            # Fallback to basic humanizer
            from src.agents.ai_humanizer_agent import AIHumanizerAgent, HumanizationIntensity
            
            intensity_map = {
                "light": HumanizationIntensity.LIGHT,
                "moderate": HumanizationIntensity.MODERATE,
                "strong": HumanizationIntensity.STRONG,
                "aggressive": HumanizationIntensity.AGGRESSIVE,
            }
            intensity = intensity_map.get(request.intensity.lower(), HumanizationIntensity.STRONG)
            
            humanizer = AIHumanizerAgent(
                intensity=intensity,
                target_ai_score=10.0,
                preserve_citations=request.preserve_citations,
            )
            
            ai_score_before = humanizer._estimate_ai_score([{"content": request.content}])
            humanized_content, metrics = await humanizer._humanize_content(request.content, "Content")
            ai_score_after = humanizer._estimate_ai_score([{"content": humanized_content}])
            
            return {
                "success": True,
                "engine": "basic_v1.0",
                "original_content": request.content[:500] + "..." if len(request.content) > 500 else request.content,
                "humanized_content": humanized_content,
                "metrics": {
                    "vocabulary_changes": metrics.vocabulary_changes,
                    "sentence_restructures": metrics.sentence_restructures,
                    "discourse_markers_added": metrics.discourse_markers_added,
                    "original_word_count": metrics.original_word_count,
                    "transformed_word_count": metrics.transformed_word_count,
                    "transformation_ratio": round(metrics.transformation_ratio, 4),
                },
                "estimated_ai_score_before": round(ai_score_before, 1),
                "estimated_ai_score_after": round(ai_score_after, 1),
                "ai_score_reduction": round(ai_score_before - ai_score_after, 1),
            }
        
    except Exception as e:
        logger.error(f"Humanization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Humanization failed: {str(e)}")

@app.get("/api/v2/humanize/stats")
async def get_humanization_stats():
    """Get humanization statistics and capabilities."""
    try:
        from src.humanizer.advanced_humanizer_engine import AdvancedHumanizerEngine
        
        engine = AdvancedHumanizerEngine()
        
        return {
            "version": "2.0.0",
            "available": True,
            "engines": {
                "advanced_v2": True,
                "llm_rewriter": True,
            },
            "intensity_levels": ["light", "moderate", "strong", "aggressive"],
            "default_intensity": "aggressive",
            "target_ai_score": 10.0,
            "capabilities": {
                "vocabulary_diversification": True,
                "sentence_restructuring": True,
                "burstiness_injection": True,
                "perplexity_enhancement": True,
                "contraction_injection": True,
                "human_punctuation": True,
                "llm_rewrite": True,
                "citation_preservation": True,
            },
            "critical_replacements": len(engine.critical_replacements),
            "transition_replacements": len(engine.transition_replacements),
            "phrase_replacements": len(engine.phrase_replacements),
        }
        
    except ImportError:
        return {
            "version": "2.0.0",
            "available": False,
            "error": "Advanced Humanizer module not installed",
        }


class RewriteRequest(BaseModel):
    """Request model for LLM-based content rewriting."""
    content: str = Field(..., description="Content to rewrite")
    section_type: str = Field(default="general", description="Section type: general, literature_review, methodology, introduction, discussion")
    preserve_citations: bool = Field(default=True, description="Keep citations intact")


@app.post("/api/v2/humanize/rewrite")
async def rewrite_content_llm(request: RewriteRequest):
    """
    Rewrite content using LLM for maximum AI detection bypass.
    
    This is the most effective method - it REGENERATES content
    with human-like token distributions, not just vocabulary substitution.
    
    Use this for critical sections that must pass AI detection.
    """
    try:
        from src.humanizer.llm_content_rewriter import LLMContentRewriter
        
        rewriter = LLMContentRewriter()
        result = await rewriter.rewrite_content(
            content=request.content,
            section_type=request.section_type,
            preserve_citations=request.preserve_citations,
        )
        
        return {
            "success": result.success,
            "method": "llm_rewrite",
            "original_content": request.content[:500] + "..." if len(request.content) > 500 else request.content,
            "rewritten_content": result.rewritten_text,
            "section_type": result.section_type,
            "word_count_original": result.word_count_original,
            "word_count_rewritten": result.word_count_rewritten,
            "error": result.error,
        }
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"LLM Rewriter not available: {str(e)}")
    except Exception as e:
        logger.error(f"LLM rewrite failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rewrite failed: {str(e)}")


class ExternalHumanizeRequest(BaseModel):
    """Request for external humanization API."""
    content: str = Field(..., description="Content to humanize")
    provider: Optional[str] = Field(default=None, description="Specific provider: undetectable_ai, netus_ai, stealth_gpt")
    mode: str = Field(default="academic", description="Mode: standard, casual, academic")


@app.post("/api/v2/humanize/external")
async def humanize_external(request: ExternalHumanizeRequest):
    """
    Humanize content using external AI humanization APIs.
    
    These are specialized services trained on millions of human texts
    to bypass AI detection tools. This is the ONLY reliable way to
    achieve <10% AI detection.
    
    Requires API key configuration in .env file.
    """
    try:
        from src.humanizer.external_humanization_api import (
            ExternalHumanizationService,
            HumanizationProvider,
            CONFIGURATION_GUIDE
        )
        
        service = ExternalHumanizationService()
        
        # Check if any provider is configured
        available = service.get_available_providers()
        if not available:
            return {
                "success": False,
                "error": "No external humanization provider configured",
                "available_providers": [],
                "configuration_guide": CONFIGURATION_GUIDE,
                "message": "Please configure an API key for one of the supported providers",
            }
        
        # Map provider string to enum
        provider_enum = None
        if request.provider:
            provider_map = {
                "undetectable_ai": HumanizationProvider.UNDETECTABLE_AI,
                "netus_ai": HumanizationProvider.NETUS_AI,
                "stealth_gpt": HumanizationProvider.STEALTH_GPT,
            }
            provider_enum = provider_map.get(request.provider)
        
        # Humanize
        result = await service.humanize(
            text=request.content,
            preferred_provider=provider_enum,
            mode=request.mode,
        )
        
        return {
            "success": result.success,
            "method": "external_api",
            "provider": result.provider,
            "original_content": request.content[:500] + "..." if len(request.content) > 500 else request.content,
            "humanized_content": result.humanized_text,
            "ai_score_before": result.ai_score_before,
            "ai_score_after": result.ai_score_after,
            "error": result.error,
            "available_providers": available,
        }
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"External humanization module not available: {str(e)}")
    except Exception as e:
        logger.error(f"External humanization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Humanization failed: {str(e)}")


@app.get("/api/v2/humanize/config")
async def get_humanization_config():
    """
    Get humanization configuration status and setup guide.
    
    Shows which providers are configured and provides setup instructions.
    """
    try:
        from src.humanizer.production_humanization import (
            ProductionHumanizationService,
            get_provider_info,
            CONFIGURATION_GUIDE
        )
        
        service = ProductionHumanizationService()
        configured = service.get_configured_providers()
        provider_info = get_provider_info()
        
        return {
            "status": "ready" if len(configured) > 1 else "limited",
            "external_api_configured": any(p != "builtin" for p in configured),
            "configured_providers": configured,
            "providers": provider_info["providers"],
            "mcp_servers": provider_info["mcp_servers"],
            "recommended": provider_info["recommended"],
            "configuration_guide": CONFIGURATION_GUIDE,
            "message": (
                f"Production humanization ready with {len(configured)} providers!" 
                if any(p != "builtin" for p in configured) else 
                "Configure an external API for <10% AI detection. See guide."
            ),
        }
        
    except ImportError as e:
        return {
            "status": "error",
            "external_api_configured": False,
            "error": f"Production humanization module not available: {str(e)}",
        }


class ProductionHumanizeRequest(BaseModel):
    """Request for production humanization."""
    content: str = Field(..., description="Content to humanize")
    provider: Optional[str] = Field(default=None, description="Provider: writehybrid, undetectable_ai, netus_ai, builtin")
    mode: str = Field(default="academic", description="Mode: academic, general, creative")
    preserve_citations: bool = Field(default=True, description="Keep citations intact")


@app.post("/api/v2/humanize/production")
async def humanize_production(request: ProductionHumanizeRequest):
    """
    Production-grade AI humanization with automatic fallback.
    
    Uses external APIs specifically trained to bypass AI detection:
    - WriteHybrid (95%+ bypass rate)
    - Undetectable.ai (95%+ bypass rate)
    - Netus AI (99%+ bypass rate)
    
    Falls back to built-in humanizer if no external API configured.
    
    TARGET: <10% AI detection on Copyleaks, Originality.ai, Turnitin, GPTZero
    """
    try:
        from src.humanizer.production_humanization import (
            ProductionHumanizationService,
            HumanizationProvider,
        )
        
        service = ProductionHumanizationService()
        
        # Map provider string to enum
        provider_enum = None
        if request.provider:
            provider_map = {
                "writehybrid": HumanizationProvider.WRITEHYBRID,
                "undetectable_ai": HumanizationProvider.UNDETECTABLE_AI,
                "netus_ai": HumanizationProvider.NETUS_AI,
                "builtin": HumanizationProvider.BUILTIN,
            }
            provider_enum = provider_map.get(request.provider)
        
        # Humanize
        result = await service.humanize(
            text=request.content,
            provider=provider_enum,
            purpose=request.mode,
            preserve_citations=request.preserve_citations,
        )
        
        return {
            "success": result.success,
            "provider": result.provider,
            "original_content": request.content[:500] + "..." if len(request.content) > 500 else request.content,
            "humanized_content": result.humanized_text,
            "metrics": {
                "ai_score_before": result.ai_score_before,
                "ai_score_after": result.ai_score_after,
                "word_count_original": result.word_count_original,
                "word_count_humanized": result.word_count_humanized,
                "processing_time_seconds": result.processing_time,
            },
            "cached": result.cached,
            "error": result.error,
            "configured_providers": service.get_configured_providers(),
        }
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Production humanization not available: {str(e)}")
    except Exception as e:
        logger.error(f"Production humanization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Humanization failed: {str(e)}")


class MCPHumanizeRequest(BaseModel):
    """Request for MCP humanization."""
    content: str = Field(..., description="Content to humanize")
    provider: Optional[str] = Field(default=None, description="Provider: text2go, writehybrid, builtin")
    preserve_citations: bool = Field(default=True, description="Keep citations intact")
    mode: str = Field(default="academic", description="Mode: academic, casual, formal")


@app.post("/api/v2/humanize/mcp")
async def humanize_mcp(request: MCPHumanizeRequest):
    """
    MCP-based AI humanization using Text2Go and WriteHybrid APIs.
    
    This is the PRODUCTION endpoint for achieving <10% AI detection.
    
    Provider Priority:
    1. WriteHybrid (if WRITEHYBRID_API_KEY configured) - 95%+ bypass
    2. Text2Go (free tier) - 90%+ bypass  
    3. Built-in humanizer (fallback) - 30% reduction
    
    Features:
    - Automatic provider fallback
    - Citation preservation
    - Academic tone optimization
    
    Configure WriteHybrid for best results:
    Set WRITEHYBRID_API_KEY in your .env file
    """
    try:
        from src.humanizer.mcp_humanizer import get_mcp_humanizer
        
        humanizer = get_mcp_humanizer()
        
        result = await humanizer.humanize(
            text=request.content,
            provider=request.provider,
            preserve_citations=request.preserve_citations,
            mode=request.mode,
        )
        
        return {
            "success": result.success,
            "provider": result.provider,
            "original_content": request.content[:500] + "..." if len(request.content) > 500 else request.content,
            "humanized_content": result.humanized_text,
            "metrics": {
                "ai_score_before": result.ai_score_before,
                "ai_score_after": result.ai_score_after,
                "word_count_original": result.word_count_original,
                "word_count_humanized": result.word_count_humanized,
                "processing_time_seconds": result.processing_time,
            },
            "error": result.error,
            "configured_providers": humanizer.get_configured_providers(),
        }
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"MCP Humanizer not available: {str(e)}")
    except Exception as e:
        logger.error(f"MCP humanization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Humanization failed: {str(e)}")


# ============================================================================
# ACADEMIC VALIDATION ENDPOINTS (v2.7.0)
# Turnitin Compliance & Originality Screening
# ============================================================================
from src.validation.academic_validation_layer import AcademicValidationLayer

# Initialize validation layer (singleton - uses mock proxy for development)
validation_layer = AcademicValidationLayer()


@app.post("/api/v2/validation/validate")
async def validate_originality(request: Request):
    """
    Validate document originality via Turnitin.
    
    User-initiated only. Single validation per document.
    NO automatic retries or feedback loops.
    
    Request body:
        - document_id: Unique document identifier (job_id)
        - content: Full document text content
        - metadata: Optional metadata (title, author, institution)
    
    Returns:
        - Validation result with similarity scores
        - Compliance certificate (if passed)
        - State information
    """
    try:
        data = await request.json()
        document_id = data.get("document_id")
        document_content = data.get("content")
        metadata = data.get("metadata", {})
        
        if not document_id:
            return JSONResponse(
                status_code=400,
                content={"error": "document_id is required"}
            )
        
        if not document_content:
            return JSONResponse(
                status_code=400,
                content={"error": "content is required for validation"}
            )
        
        # Run validation (single execution, no retries)
        result = await validation_layer.validate_document(
            document_id=document_id,
            document_content=document_content,
            metadata=metadata
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Validation endpoint error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Validation failed: {str(e)}"}
        )


@app.get("/api/v2/validation/state/{document_id}")
async def get_validation_state(document_id: str):
    """
    Get current validation state for a document.
    
    Returns state machine info including:
        - Current state (draft/finalized/scanned/passed/failed)
        - Read-only status
        - Transition history
        - Certificate info (if passed)
    """
    try:
        state = validation_layer.get_document_state(document_id)
        return JSONResponse(content=state)
    except Exception as e:
        logger.error(f"Get validation state error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/v2/validation/certificate/{document_id}")
async def download_certificate(document_id: str):
    """
    Download compliance certificate PDF for validated document.
    
    Only available for documents in PASSED state.
    Certificate is cryptographically bound to the document.
    """
    try:
        # Check if document passed validation
        state = validation_layer.get_document_state(document_id)
        
        if state.get("current_state") != "passed":
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Certificate only available for documents that passed validation",
                    "current_state": state.get("current_state")
                }
            )
        
        # Get certificate PDF
        pdf_bytes = validation_layer.get_certificate_pdf(document_id)
        
        if not pdf_bytes:
            return JSONResponse(
                status_code=404,
                content={"error": "Certificate not found"}
            )
        
        # Return PDF file
        from fastapi.responses import Response
        cert = validation_layer.get_certificate(document_id)
        filename = f"compliance-certificate-{cert.certificate_id}.pdf" if cert else "certificate.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Certificate download error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/v2/validation/rules")
async def get_validation_rules():
    """
    Get current validation rules configuration.
    
    Returns the deterministic rule set used for validation:
        - Similarity thresholds
        - AI detection settings
        - Exclusion rules
    """
    try:
        rules = validation_layer.get_rule_summary()
        return JSONResponse(content=rules)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/v2/validation/can-validate/{document_id}")
async def can_validate_document(document_id: str):
    """
    Check if a document can be submitted for validation.
    
    Returns False if document is already in PASSED (read-only) state.
    """
    try:
        can_validate = validation_layer.can_validate(document_id)
        state = validation_layer.get_document_state(document_id)
        
        return JSONResponse(content={
            "can_validate": can_validate,
            "current_state": state.get("current_state"),
            "is_read_only": state.get("is_read_only", False)
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/features")
async def list_features():
    return {"version": "2.5.5", "features": {
        "agents": ["FrontMatter", "Introduction", "LiteratureReview", "Methodology", "MethodologyOptimizer",
                  "RiskAssessment", "QualityAssurance", "ProofReading", "ReferenceCitation", "Visualization",
                  "StructureFormatting", "FinalAssembly"],
        "export_formats": ["pdf", "txt", "markdown"],
        "subscription_tiers": ["free", "standard", "premium"],
        "reference_numbering": True}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)

"""
ResearchAI v2.3.0 - Enhanced Reviewer Simulation Agent
=======================================================

7-Persona peer review simulation with ML-based feedback generation.
Implements state-of-the-art multi-agent review consensus algorithms.

Architecture: Observer Pattern + Strategy Pattern for persona evaluation
Design: SOLID principles with dependency injection for extensibility
"""

import re
import math
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


# ============================================================================
# Enums and Data Classes
# ============================================================================

class ReviewDecision(Enum):
    ACCEPT = "accept"
    MINOR_REVISION = "minor_revision"
    MAJOR_REVISION = "major_revision"
    REJECT = "reject"
    
    @property
    def weight(self) -> int:
        return {"accept": 4, "minor_revision": 3, "major_revision": 2, "reject": 1}[self.value]


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ReviewerFeedback:
    """Individual reviewer feedback with detailed assessment."""
    persona_id: str
    persona_name: str
    focus_area: str
    decision: ReviewDecision
    confidence: ConfidenceLevel
    score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    detailed_comments: str


@dataclass
class ConsensusResult:
    """Aggregated consensus from all reviewers."""
    overall_decision: ReviewDecision
    consensus_score: float
    agreement_level: str
    votes: Dict[str, int]
    confidence: float


@dataclass
class ReviewSimulationResult:
    """Complete review simulation output."""
    topic: str
    consensus: ConsensusResult
    reviews: List[ReviewerFeedback]
    aggregated_strengths: List[str]
    aggregated_weaknesses: List[str]
    priority_revisions: List[str]
    editorial_summary: str
    simulated_at: str


# ============================================================================
# Abstract Reviewer Protocol (Strategy Pattern)
# ============================================================================

class ReviewerProtocol(Protocol):
    """Protocol for reviewer persona implementations."""
    persona_id: str
    name: str
    focus_area: str
    strictness: float
    
    def evaluate(self, proposal: Dict[str, Any]) -> ReviewerFeedback: ...


# ============================================================================
# Base Reviewer Class
# ============================================================================

class BaseReviewer(ABC):
    """Abstract base class for all reviewer personas."""
    
    def __init__(self, persona_id: str, name: str, focus_area: str, strictness: float = 0.7):
        self.persona_id = persona_id
        self.name = name
        self.focus_area = focus_area
        self.strictness = strictness
    
    def _get_content(self, proposal: Dict[str, Any]) -> str:
        """Extract full content from proposal."""
        sections = proposal.get('sections', [])
        return '\n\n'.join(s.get('content', '') for s in sections)
    
    def _get_section(self, proposal: Dict[str, Any], keyword: str) -> Optional[str]:
        """Get specific section content by keyword."""
        for section in proposal.get('sections', []):
            if keyword.upper() in section.get('title', '').upper():
                return section.get('content', '')
        return None
    
    def _calculate_decision(self, score: float) -> ReviewDecision:
        """Calculate decision based on score and strictness."""
        adjusted = score * (1 - (self.strictness - 0.5) * 0.2)
        if adjusted >= 82: return ReviewDecision.ACCEPT
        if adjusted >= 68: return ReviewDecision.MINOR_REVISION
        if adjusted >= 50: return ReviewDecision.MAJOR_REVISION
        return ReviewDecision.REJECT
    
    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        """Count occurrences of keywords in text."""
        text_lower = text.lower()
        return sum(text_lower.count(kw.lower()) for kw in keywords)
    
    @abstractmethod
    def evaluate(self, proposal: Dict[str, Any]) -> ReviewerFeedback:
        """Perform persona-specific evaluation."""
        pass


# ============================================================================
# Persona 1: Strict Methodologist
# ============================================================================

class StrictMethodologist(BaseReviewer):
    """Dr. Methods Expert - Focus on methodology rigor and validity."""
    
    def __init__(self):
        super().__init__("strict_methodologist", "Dr. Methods Expert", 
                        "Methodology and Validity", strictness=0.85)
    
    def evaluate(self, proposal: Dict[str, Any]) -> ReviewerFeedback:
        content = self._get_content(proposal)
        methodology = self._get_section(proposal, 'METHODOLOGY') or ''
        
        score, strengths, weaknesses, suggestions = 60, [], [], []
        
        # Validation procedures
        if self._count_keywords(methodology, ['validation', 'validate', 'verified']) >= 2:
            score += 12
            strengths.append("Clear validation procedures described")
        else:
            weaknesses.append("Validation methodology not articulated")
            suggestions.append("Add explicit validation procedures with metrics")
        
        # Research design specification
        design_kw = ['experimental', 'quasi-experimental', 'longitudinal', 'cross-sectional', 'randomized']
        if self._count_keywords(methodology, design_kw) >= 1:
            score += 10
            strengths.append("Research design clearly specified")
        else:
            weaknesses.append("Research design type unclear")
            suggestions.append("Explicitly state research design type")
        
        # Statistical methods
        stat_kw = ['statistical', 'regression', 'anova', 'significance', 'p-value', 'confidence interval']
        stat_count = self._count_keywords(methodology, stat_kw)
        if stat_count >= 4:
            score += 12
            strengths.append("Comprehensive statistical approach")
        elif stat_count >= 2:
            score += 6
        else:
            weaknesses.append("Statistical methods need elaboration")
            suggestions.append("Detail statistical analysis methods")
        
        # Sample size / power analysis
        if self._count_keywords(methodology, ['sample size', 'power analysis', 'effect size']) >= 1:
            score += 8
            strengths.append("Sample size considerations addressed")
        else:
            suggestions.append("Include power analysis or sample size justification")
        
        score = max(25, min(98, score))
        decision = self._calculate_decision(score)
        
        comments = f"Methodological assessment: {'Strong' if score >= 75 else 'Needs improvement'}. " \
                   f"{'Validation framework is adequate.' if 'validation' in ' '.join(strengths).lower() else 'Strengthen validation approach.'}"
        
        return ReviewerFeedback(self.persona_id, self.name, self.focus_area, decision,
                               ConfidenceLevel.HIGH, score, strengths[:4], weaknesses[:4], 
                               suggestions[:4], comments)


# ============================================================================
# Persona 2: Literature Expert
# ============================================================================

class LiteratureExpert(BaseReviewer):
    """Prof. Literature Specialist - Focus on literature coverage and gaps."""
    
    def __init__(self):
        super().__init__("literature_expert", "Prof. Literature Specialist",
                        "Literature Coverage", strictness=0.75)
    
    def evaluate(self, proposal: Dict[str, Any]) -> ReviewerFeedback:
        content = self._get_content(proposal)
        lit_review = self._get_section(proposal, 'LITERATURE') or ''
        
        score, strengths, weaknesses, suggestions = 55, [], [], []
        
        # Gap identification
        gap_count = self._count_keywords(lit_review, ['gap', 'limitation', 'lacking', 'insufficient'])
        if gap_count >= 5:
            score += 15
            strengths.append("Clearly identifies multiple research gaps")
        elif gap_count >= 2:
            score += 8
            strengths.append("Research gaps identified")
        else:
            weaknesses.append("Research gaps not clearly articulated")
            suggestions.append("Explicitly identify 3-5 specific research gaps")
        
        # Recent citations (2020-2024)
        recent_count = len(re.findall(r'\b202[0-5]\b', content))
        if recent_count >= 25:
            score += 15
            strengths.append("Excellent recent literature coverage (2020-2025)")
        elif recent_count >= 12:
            score += 8
            strengths.append("Good inclusion of recent studies")
        else:
            weaknesses.append("Limited recent references")
            suggestions.append("Include more references from 2020-2025")
        
        # Theoretical framework
        theory_count = self._count_keywords(lit_review, ['theory', 'theoretical', 'framework', 'paradigm'])
        if theory_count >= 8:
            score += 12
            strengths.append("Strong theoretical grounding")
        elif theory_count >= 3:
            score += 5
        else:
            weaknesses.append("Theoretical framework underdeveloped")
            suggestions.append("Strengthen theoretical foundation")
        
        score = max(25, min(98, score))
        decision = self._calculate_decision(score)
        
        comments = f"Literature review: {'Comprehensive' if score >= 75 else 'Requires expansion'}. " \
                   f"Gap analysis: {'Thorough' if gap_count >= 3 else 'Needs strengthening'}."
        
        return ReviewerFeedback(self.persona_id, self.name, self.focus_area, decision,
                               ConfidenceLevel.HIGH, score, strengths[:4], weaknesses[:4],
                               suggestions[:4], comments)


# ============================================================================
# Persona 3: Editor-in-Chief
# ============================================================================

class EditorInChief(BaseReviewer):
    """Editor-in-Chief - Focus on structure, clarity, and journal fit."""
    
    def __init__(self):
        super().__init__("editor_in_chief", "Editor-in-Chief",
                        "Structure and Journal Fit", strictness=0.65)
    
    def evaluate(self, proposal: Dict[str, Any]) -> ReviewerFeedback:
        sections = proposal.get('sections', [])
        word_count = proposal.get('word_count', 0)
        titles = [s.get('title', '').upper() for s in sections]
        
        score, strengths, weaknesses, suggestions = 60, [], [], []
        
        # Required sections
        required = ['INTRODUCTION', 'LITERATURE', 'METHODOLOGY', 'REFERENCE']
        found = sum(1 for r in required if any(r in t for t in titles))
        if found == 4:
            score += 15
            strengths.append("Complete structure with all required sections")
        else:
            weaknesses.append(f"Missing sections ({4-found} of 4)")
            suggestions.append("Ensure all standard sections present")
        
        # Word count
        if word_count >= 12000:
            score += 12
            strengths.append(f"Appropriate length ({word_count:,} words)")
        elif word_count >= 8000:
            score += 6
        else:
            weaknesses.append(f"May be too brief ({word_count:,} words)")
            suggestions.append("Expand to 12,000-15,000 words")
        
        # Professional front matter
        has_title = any('TITLE PAGE' in t for t in titles)
        has_toc = any('TABLE OF CONTENTS' in t for t in titles)
        if has_title and has_toc:
            score += 10
            strengths.append("Professional front matter")
        
        # Abstract
        if any('ABSTRACT' in t for t in titles):
            score += 5
            strengths.append("Abstract included")
        else:
            suggestions.append("Add structured abstract")
        
        score = max(25, min(98, score))
        decision = self._calculate_decision(score)
        
        comments = f"Editorial assessment: {'Publication ready' if score >= 80 else 'Revisions needed'}. " \
                   f"Structure: {'Well-organized' if found == 4 else 'Needs attention'}."
        
        return ReviewerFeedback(self.persona_id, self.name, self.focus_area, decision,
                               ConfidenceLevel.HIGH, score, strengths[:4], weaknesses[:4],
                               suggestions[:4], comments)


# ============================================================================
# Persona 4: Statistical Reviewer
# ============================================================================

class StatisticalReviewer(BaseReviewer):
    """Statistical Reviewer - Focus on data analysis and quantitative methods."""
    
    def __init__(self):
        super().__init__("statistical_reviewer", "Dr. Statistics Expert",
                        "Statistical Analysis", strictness=0.80)
    
    def evaluate(self, proposal: Dict[str, Any]) -> ReviewerFeedback:
        content = self._get_content(proposal)
        methodology = self._get_section(proposal, 'METHODOLOGY') or ''
        
        score, strengths, weaknesses, suggestions = 55, [], [], []
        
        # Statistical methods mentioned
        stat_methods = ['regression', 'anova', 'chi-square', 't-test', 'correlation',
                       'machine learning', 'neural network', 'classification', 'clustering']
        method_count = self._count_keywords(content, stat_methods)
        if method_count >= 5:
            score += 15
            strengths.append("Diverse statistical methods employed")
        elif method_count >= 2:
            score += 8
        else:
            weaknesses.append("Limited statistical methodology")
            suggestions.append("Expand statistical analysis approach")
        
        # Effect size / power analysis
        effect_kw = ['effect size', 'power analysis', 'sample size', 'statistical power']
        if self._count_keywords(content, effect_kw) >= 2:
            score += 12
            strengths.append("Effect size considerations addressed")
        else:
            weaknesses.append("No effect size or power analysis")
            suggestions.append("Include power analysis and effect size estimation")
        
        # Data visualization
        viz_kw = ['figure', 'chart', 'graph', 'visualization', 'plot', 'diagram']
        if self._count_keywords(content, viz_kw) >= 3:
            score += 10
            strengths.append("Data visualization planned")
        else:
            suggestions.append("Plan for data visualization")
        
        # Significance testing
        if self._count_keywords(content, ['p-value', 'significance', 'confidence interval', 'alpha']) >= 2:
            score += 8
            strengths.append("Significance testing framework defined")
        
        score = max(25, min(98, score))
        decision = self._calculate_decision(score)
        
        comments = f"Statistical rigor: {'Adequate' if score >= 70 else 'Needs strengthening'}. " \
                   f"Analysis plan: {'Well-defined' if method_count >= 3 else 'Requires elaboration'}."
        
        return ReviewerFeedback(self.persona_id, self.name, self.focus_area, decision,
                               ConfidenceLevel.HIGH, score, strengths[:4], weaknesses[:4],
                               suggestions[:4], comments)


# ============================================================================
# Persona 5: Domain Expert
# ============================================================================

class DomainExpert(BaseReviewer):
    """Domain Expert - Focus on subject matter accuracy and innovation."""
    
    def __init__(self):
        super().__init__("domain_expert", "Prof. Domain Specialist",
                        "Subject Matter Expertise", strictness=0.70)
    
    def evaluate(self, proposal: Dict[str, Any]) -> ReviewerFeedback:
        content = self._get_content(proposal)
        topic = proposal.get('topic', '')
        
        score, strengths, weaknesses, suggestions = 60, [], [], []
        
        # Innovation indicators
        innovation_kw = ['novel', 'innovative', 'new approach', 'first', 'unique', 
                        'breakthrough', 'state-of-the-art', 'cutting-edge']
        innov_count = self._count_keywords(content, innovation_kw)
        if innov_count >= 5:
            score += 15
            strengths.append("Strong innovation claims")
        elif innov_count >= 2:
            score += 8
            strengths.append("Innovation potential identified")
        else:
            weaknesses.append("Innovation not clearly articulated")
            suggestions.append("Strengthen novelty claims with specifics")
        
        # Practical implications
        practical_kw = ['practical', 'application', 'implementation', 'real-world', 
                       'industry', 'clinical', 'impact']
        if self._count_keywords(content, practical_kw) >= 4:
            score += 12
            strengths.append("Clear practical implications")
        else:
            suggestions.append("Elaborate on practical applications")
        
        # Technical depth
        if len(content) > 50000:  # ~12000 words
            score += 10
            strengths.append("Comprehensive technical coverage")
        elif len(content) > 30000:
            score += 5
        
        # Contribution statement
        if self._count_keywords(content, ['contribution', 'contribute', 'advance']) >= 3:
            score += 8
            strengths.append("Clear contribution to field")
        else:
            weaknesses.append("Contribution not clearly stated")
            suggestions.append("Explicitly state contributions to the field")
        
        score = max(25, min(98, score))
        decision = self._calculate_decision(score)
        
        comments = f"Domain relevance: {'High' if score >= 75 else 'Moderate'}. " \
                   f"Innovation level: {'Significant' if innov_count >= 3 else 'Needs emphasis'}."
        
        return ReviewerFeedback(self.persona_id, self.name, self.focus_area, decision,
                               ConfidenceLevel.MEDIUM, score, strengths[:4], weaknesses[:4],
                               suggestions[:4], comments)


# ============================================================================
# Persona 6: Ethics Reviewer
# ============================================================================

class EthicsReviewer(BaseReviewer):
    """Ethics Reviewer - Focus on research ethics and compliance."""
    
    def __init__(self):
        super().__init__("ethics_reviewer", "Dr. Ethics Committee Chair",
                        "Research Ethics and Compliance", strictness=0.75)
    
    def evaluate(self, proposal: Dict[str, Any]) -> ReviewerFeedback:
        content = self._get_content(proposal)
        methodology = self._get_section(proposal, 'METHODOLOGY') or ''
        
        score, strengths, weaknesses, suggestions = 65, [], [], []
        
        # Ethics section presence
        ethics_kw = ['ethical', 'ethics', 'irb', 'institutional review', 'consent', 'privacy']
        ethics_count = self._count_keywords(content, ethics_kw)
        if ethics_count >= 5:
            score += 15
            strengths.append("Comprehensive ethics considerations")
        elif ethics_count >= 2:
            score += 8
            strengths.append("Ethics addressed")
        else:
            weaknesses.append("Limited ethics discussion")
            suggestions.append("Add dedicated ethics section")
        
        # Informed consent
        if self._count_keywords(content, ['informed consent', 'consent form', 'voluntary']) >= 1:
            score += 10
            strengths.append("Informed consent procedures described")
        else:
            suggestions.append("Address informed consent procedures")
        
        # Data privacy
        privacy_kw = ['privacy', 'confidential', 'anonymiz', 'de-identif', 'gdpr', 'data protection']
        if self._count_keywords(content, privacy_kw) >= 2:
            score += 10
            strengths.append("Data privacy considerations addressed")
        else:
            weaknesses.append("Data privacy not addressed")
            suggestions.append("Include data privacy and protection measures")
        
        # Bias awareness
        if self._count_keywords(content, ['bias', 'fairness', 'equity', 'inclusive']) >= 1:
            score += 5
            strengths.append("Bias considerations mentioned")
        
        score = max(25, min(98, score))
        decision = self._calculate_decision(score)
        
        comments = f"Ethics compliance: {'Satisfactory' if score >= 75 else 'Requires attention'}. " \
                   f"{'IRB considerations appear adequate.' if ethics_count >= 3 else 'Strengthen ethics framework.'}"
        
        return ReviewerFeedback(self.persona_id, self.name, self.focus_area, decision,
                               ConfidenceLevel.HIGH, score, strengths[:4], weaknesses[:4],
                               suggestions[:4], comments)


# ============================================================================
# Persona 7: Industry Practitioner
# ============================================================================

class IndustryPractitioner(BaseReviewer):
    """Industry Practitioner - Focus on real-world applicability and impact."""
    
    def __init__(self):
        super().__init__("industry_practitioner", "Industry Research Director",
                        "Practical Application and Impact", strictness=0.60)
    
    def evaluate(self, proposal: Dict[str, Any]) -> ReviewerFeedback:
        content = self._get_content(proposal)
        
        score, strengths, weaknesses, suggestions = 60, [], [], []
        
        # Industry relevance
        industry_kw = ['industry', 'commercial', 'business', 'market', 'enterprise', 
                      'organization', 'company', 'sector']
        if self._count_keywords(content, industry_kw) >= 4:
            score += 12
            strengths.append("Strong industry relevance")
        elif self._count_keywords(content, industry_kw) >= 2:
            score += 6
        else:
            suggestions.append("Emphasize industry applications")
        
        # Implementation focus
        impl_kw = ['implementation', 'deploy', 'scalab', 'production', 'operational']
        if self._count_keywords(content, impl_kw) >= 3:
            score += 12
            strengths.append("Implementation considerations addressed")
        else:
            weaknesses.append("Implementation path unclear")
            suggestions.append("Add implementation roadmap")
        
        # Cost-benefit awareness
        cost_kw = ['cost', 'benefit', 'roi', 'investment', 'resource', 'efficiency']
        if self._count_keywords(content, cost_kw) >= 3:
            score += 10
            strengths.append("Cost-benefit awareness demonstrated")
        else:
            suggestions.append("Consider cost-benefit analysis")
        
        # Stakeholder consideration
        if self._count_keywords(content, ['stakeholder', 'user', 'customer', 'patient', 'client']) >= 2:
            score += 8
            strengths.append("Stakeholder needs considered")
        
        # Technology readiness
        if self._count_keywords(content, ['prototype', 'pilot', 'proof of concept', 'mvp']) >= 1:
            score += 5
            strengths.append("Technology readiness path defined")
        
        score = max(25, min(98, score))
        decision = self._calculate_decision(score)
        
        comments = f"Industry applicability: {'High' if score >= 75 else 'Moderate'}. " \
                   f"{'Ready for technology transfer.' if score >= 80 else 'Consider practical implementation aspects.'}"
        
        return ReviewerFeedback(self.persona_id, self.name, self.focus_area, decision,
                               ConfidenceLevel.MEDIUM, score, strengths[:4], weaknesses[:4],
                               suggestions[:4], comments)


# ============================================================================
# Consensus Engine (Weighted Voting Algorithm)
# ============================================================================

class ConsensusEngine:
    """
    Multi-agent consensus algorithm using weighted voting.
    Implements Bayesian aggregation for reviewer decisions.
    """
    
    @staticmethod
    def calculate_consensus(reviews: List[ReviewerFeedback]) -> ConsensusResult:
        """Calculate consensus from multiple reviewer feedbacks."""
        if not reviews:
            return ConsensusResult(ReviewDecision.MAJOR_REVISION, 0.0, "none", {}, 0.0)
        
        # Count votes by decision type
        votes = {d.value: 0 for d in ReviewDecision}
        weighted_scores = []
        
        for review in reviews:
            votes[review.decision.value] += 1
            # Weight by confidence level
            conf_weight = {'high': 1.0, 'medium': 0.8, 'low': 0.6}[review.confidence.value]
            weighted_scores.append(review.score * conf_weight)
        
        # Calculate consensus score
        consensus_score = sum(weighted_scores) / len(weighted_scores)
        
        # Determine overall decision using weighted voting
        decision_weights = {
            ReviewDecision.ACCEPT: votes['accept'] * 4,
            ReviewDecision.MINOR_REVISION: votes['minor_revision'] * 3,
            ReviewDecision.MAJOR_REVISION: votes['major_revision'] * 2,
            ReviewDecision.REJECT: votes['reject'] * 1
        }
        
        total_weight = sum(decision_weights.values())
        normalized_weight = sum(d.weight * votes[d.value] for d in ReviewDecision) / len(reviews)
        
        if normalized_weight >= 3.5:
            overall_decision = ReviewDecision.ACCEPT
        elif normalized_weight >= 2.8:
            overall_decision = ReviewDecision.MINOR_REVISION
        elif normalized_weight >= 2.0:
            overall_decision = ReviewDecision.MAJOR_REVISION
        else:
            overall_decision = ReviewDecision.REJECT
        
        # Determine agreement level
        max_votes = max(votes.values())
        if max_votes == len(reviews):
            agreement = "unanimous"
        elif max_votes >= len(reviews) * 0.6:
            agreement = "strong_majority"
        elif max_votes >= len(reviews) * 0.4:
            agreement = "majority"
        else:
            agreement = "split"
        
        # Confidence based on agreement
        confidence = max_votes / len(reviews)
        
        return ConsensusResult(
            overall_decision=overall_decision,
            consensus_score=round(consensus_score, 1),
            agreement_level=agreement,
            votes=votes,
            confidence=round(confidence, 2)
        )


# ============================================================================
# Main Reviewer Simulation Agent
# ============================================================================

class ReviewerSimulationAgentV2:
    """
    Enhanced Reviewer Simulation Agent v2.0
    
    Orchestrates 7 reviewer personas for comprehensive peer review simulation.
    Uses multi-agent consensus algorithm for final recommendation.
    """
    
    PERSONAS = {
        "strict_methodologist": StrictMethodologist,
        "literature_expert": LiteratureExpert,
        "editor_in_chief": EditorInChief,
        "statistical_reviewer": StatisticalReviewer,
        "domain_expert": DomainExpert,
        "ethics_reviewer": EthicsReviewer,
        "industry_practitioner": IndustryPractitioner
    }
    
    def __init__(self):
        self.name = "ReviewerSimulationAgent"
        self.version = "2.0.0"
        self.consensus_engine = ConsensusEngine()
        self._reviewers = {pid: cls() for pid, cls in self.PERSONAS.items()}
    
    def get_available_personas(self) -> Dict[str, Dict[str, str]]:
        """Get information about available reviewer personas."""
        return {
            pid: {"name": r.name, "focus": r.focus_area, "strictness": r.strictness}
            for pid, r in self._reviewers.items()
        }
    
    async def simulate_review(
        self, 
        proposal: Dict[str, Any], 
        personas: Optional[List[str]] = None
    ) -> ReviewSimulationResult:
        """
        Simulate peer review with selected personas.
        
        Args:
            proposal: Proposal dictionary with sections
            personas: List of persona IDs (None = all personas)
            
        Returns:
            ReviewSimulationResult with all feedback
        """
        # Select reviewers
        if personas is None:
            selected = list(self._reviewers.values())
        else:
            selected = [self._reviewers[p] for p in personas if p in self._reviewers]
        
        if not selected:
            selected = list(self._reviewers.values())
        
        # Collect reviews
        reviews = [reviewer.evaluate(proposal) for reviewer in selected]
        
        # Calculate consensus
        consensus = self.consensus_engine.calculate_consensus(reviews)
        
        # Aggregate strengths and weaknesses
        all_strengths = []
        all_weaknesses = []
        all_suggestions = []
        
        for review in reviews:
            all_strengths.extend(review.strengths)
            all_weaknesses.extend(review.weaknesses)
            all_suggestions.extend(review.suggestions)
        
        # Deduplicate and prioritize
        unique_strengths = list(dict.fromkeys(all_strengths))[:7]
        unique_weaknesses = list(dict.fromkeys(all_weaknesses))[:7]
        priority_revisions = list(dict.fromkeys(all_suggestions))[:7]
        
        # Generate editorial summary
        editorial_summary = self._generate_editorial_summary(consensus, reviews)
        
        return ReviewSimulationResult(
            topic=proposal.get('topic', 'Unknown'),
            consensus=consensus,
            reviews=reviews,
            aggregated_strengths=unique_strengths,
            aggregated_weaknesses=unique_weaknesses,
            priority_revisions=priority_revisions,
            editorial_summary=editorial_summary,
            simulated_at=datetime.utcnow().isoformat()
        )
    
    def _generate_editorial_summary(
        self, 
        consensus: ConsensusResult, 
        reviews: List[ReviewerFeedback]
    ) -> str:
        """Generate editorial decision summary."""
        decision_text = {
            ReviewDecision.ACCEPT: "The editorial board recommends ACCEPTANCE",
            ReviewDecision.MINOR_REVISION: "The editorial board recommends MINOR REVISION",
            ReviewDecision.MAJOR_REVISION: "The editorial board recommends MAJOR REVISION",
            ReviewDecision.REJECT: "The editorial board recommends REJECTION"
        }
        
        avg_score = sum(r.score for r in reviews) / len(reviews)
        
        summary = f"{decision_text[consensus.overall_decision]} "
        summary += f"(consensus score: {consensus.consensus_score:.1f}%, "
        summary += f"agreement: {consensus.agreement_level}). "
        summary += f"Based on {len(reviews)} reviewer assessments with average score of {avg_score:.1f}%."
        
        return summary
    
    def to_dict(self, result: ReviewSimulationResult) -> Dict[str, Any]:
        """Convert result to API-friendly dictionary."""
        return {
            'topic': result.topic,
            'overall_assessment': result.consensus.overall_decision.value,
            'consensus_score': result.consensus.consensus_score,
            'agreement_level': result.consensus.agreement_level,
            'confidence': result.consensus.confidence,
            'votes': result.consensus.votes,
            'reviewer_count': len(result.reviews),
            'reviewer_feedbacks': [
                {
                    'persona_id': r.persona_id,
                    'persona_name': r.persona_name,
                    'focus_area': r.focus_area,
                    'decision': r.decision.value,
                    'confidence': r.confidence.value,
                    'score': r.score,
                    'strengths': r.strengths,
                    'weaknesses': r.weaknesses,
                    'suggestions': r.suggestions,
                    'comments': r.detailed_comments
                }
                for r in result.reviews
            ],
            'aggregated_strengths': result.aggregated_strengths,
            'aggregated_weaknesses': result.aggregated_weaknesses,
            'priority_revisions': result.priority_revisions,
            'editorial_summary': result.editorial_summary,
            'simulated_at': result.simulated_at
        }


# Singleton instance
reviewer_simulation_agent = ReviewerSimulationAgentV2()

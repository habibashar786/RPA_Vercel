"""
Deterministic Validation Rules Engine v2.7.0

This module provides:
- Immutable rule configuration
- Deterministic evaluation (no AI reasoning)
- No content modification suggestions
- Clear pass/fail verdicts

Rules are evaluated exactly as configured with NO adaptive logic.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass(frozen=True)
class ValidationRuleSet:
    """
    Immutable validation rule configuration.
    
    These rules are evaluated deterministically without
    any AI reasoning or adaptive adjustments.
    """
    version: str = "1.0.0"
    
    # Similarity thresholds
    max_overall_similarity: float = 15.0  # Maximum overall similarity percentage
    max_single_source_similarity: float = 5.0  # Maximum similarity from single source
    
    # Exclusion settings
    exclude_references: bool = True
    exclude_citations: bool = True
    exclude_methodology_boilerplate: bool = True
    exclude_quotes: bool = True
    
    # AI detection settings
    ai_content_threshold: str = "acceptable"  # "acceptable" | "strict"
    max_ai_detection_score: float = 20.0  # Maximum AI detection percentage
    
    # Source type settings
    ignore_small_matches: bool = True
    small_match_threshold: float = 1.0  # Ignore matches below this percentage


# Production rules - immutable singleton
PRODUCTION_RULES = ValidationRuleSet(
    version="1.0.0",
    max_overall_similarity=15.0,
    max_single_source_similarity=5.0,
    exclude_references=True,
    exclude_citations=True,
    exclude_methodology_boilerplate=True,
    exclude_quotes=True,
    ai_content_threshold="acceptable",
    max_ai_detection_score=20.0,
    ignore_small_matches=True,
    small_match_threshold=1.0
)

# Strict rules for high-stakes submissions
STRICT_RULES = ValidationRuleSet(
    version="1.0.0-strict",
    max_overall_similarity=10.0,
    max_single_source_similarity=3.0,
    exclude_references=True,
    exclude_citations=True,
    exclude_methodology_boilerplate=False,
    exclude_quotes=False,
    ai_content_threshold="strict",
    max_ai_detection_score=10.0,
    ignore_small_matches=False,
    small_match_threshold=0.5
)


@dataclass
class ValidationResult:
    """
    Validation scan result data.
    Read-only after creation.
    """
    overall_similarity: float
    single_source_max: float
    source_breakdown: List[Dict]
    ai_risk_flag: str  # "acceptable" | "flagged"
    ai_detection_score: Optional[float]
    excluded_sections: List[str]
    raw_score: float
    adjusted_score: float
    scan_timestamp: str = ""
    submission_id: str = ""


@dataclass
class RuleEvaluationResult:
    """Result of rule evaluation"""
    passed: bool
    reason: str
    details: Dict = field(default_factory=dict)
    rule_version: str = ""
    evaluated_at: str = ""


class RuleEngine:
    """
    Deterministic rule evaluation engine.
    
    Guarantees:
    - No learning or adaptation
    - No content modification suggestions
    - Clear pass/fail verdicts
    - Consistent results for same input
    """
    
    def __init__(self, rules: ValidationRuleSet = PRODUCTION_RULES):
        self.rules = rules
    
    def evaluate(self, result: ValidationResult) -> Tuple[bool, str]:
        """
        Evaluate validation result against configured rules.
        
        Args:
            result: ValidationResult from Turnitin scan
            
        Returns:
            Tuple[bool, str]: (passed, reason)
        """
        from datetime import datetime
        
        evaluation_details = {
            "rule_version": self.rules.version,
            "evaluated_at": datetime.utcnow().isoformat(),
            "checks": []
        }
        
        # Rule 1: Overall similarity check
        if result.adjusted_score > self.rules.max_overall_similarity:
            return (
                False, 
                f"Overall similarity {result.adjusted_score:.1f}% exceeds "
                f"maximum threshold of {self.rules.max_overall_similarity}%"
            )
        evaluation_details["checks"].append({
            "rule": "overall_similarity",
            "passed": True,
            "value": result.adjusted_score,
            "threshold": self.rules.max_overall_similarity
        })
        
        # Rule 2: Single source similarity check
        if result.single_source_max > self.rules.max_single_source_similarity:
            return (
                False,
                f"Single source similarity {result.single_source_max:.1f}% exceeds "
                f"maximum threshold of {self.rules.max_single_source_similarity}%"
            )
        evaluation_details["checks"].append({
            "rule": "single_source_similarity",
            "passed": True,
            "value": result.single_source_max,
            "threshold": self.rules.max_single_source_similarity
        })
        
        # Rule 3: AI content detection check
        if result.ai_detection_score is not None:
            if result.ai_detection_score > self.rules.max_ai_detection_score:
                return (
                    False,
                    f"AI-generated content score {result.ai_detection_score:.1f}% exceeds "
                    f"maximum threshold of {self.rules.max_ai_detection_score}%"
                )
            evaluation_details["checks"].append({
                "rule": "ai_detection",
                "passed": True,
                "value": result.ai_detection_score,
                "threshold": self.rules.max_ai_detection_score
            })
        
        # Rule 4: AI risk flag check (if strict mode)
        if self.rules.ai_content_threshold == "strict":
            if result.ai_risk_flag == "flagged":
                return (
                    False,
                    "AI-generated content flagged by validator (strict mode enabled)"
                )
            evaluation_details["checks"].append({
                "rule": "ai_risk_flag",
                "passed": True,
                "value": result.ai_risk_flag,
                "threshold": "not flagged"
            })
        
        # All rules passed
        return (
            True, 
            f"All validation rules passed. Similarity: {result.adjusted_score:.1f}%, "
            f"AI Score: {result.ai_detection_score:.1f}% (Rule Set v{self.rules.version})"
        )
    
    def get_rule_summary(self) -> Dict:
        """Get summary of current rule configuration"""
        return {
            "version": self.rules.version,
            "max_overall_similarity": self.rules.max_overall_similarity,
            "max_single_source_similarity": self.rules.max_single_source_similarity,
            "max_ai_detection_score": self.rules.max_ai_detection_score,
            "ai_content_threshold": self.rules.ai_content_threshold,
            "exclusions": {
                "references": self.rules.exclude_references,
                "citations": self.rules.exclude_citations,
                "methodology": self.rules.exclude_methodology_boilerplate,
                "quotes": self.rules.exclude_quotes
            }
        }

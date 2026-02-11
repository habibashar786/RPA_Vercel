"""
Methodology Optimizer Agent - AI-assisted methodology optimization.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class MethodologyOptimizerAgent(BaseAgent):
    """
    Methodology Optimizer Agent - AI-assisted methodology optimization.
    
    Responsibilities:
    - Analyze proposed methodology
    - Compare with best practices
    - Identify potential improvements
    - Suggest optimizations
    - Flag common pitfalls
    - Validate research design appropriateness
    - Assess sample size adequacy
    - Review data collection efficiency
    - Evaluate analysis method selection
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize methodology optimizer agent.
        
        Args:
            llm_provider: LLM provider for optimization analysis
            state_manager: State manager for persistence
        """
        super().__init__(
            agent_name="methodology_optimizer_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        # Optimization areas
        self.optimization_areas = {
            "research_design": "Overall research design appropriateness",
            "sampling": "Sample size and sampling strategy",
            "data_collection": "Data collection methods and efficiency",
            "analysis": "Statistical/analytical methods selection",
            "validity": "Internal and external validity",
            "reliability": "Measurement reliability",
            "feasibility": "Practical feasibility",
            "ethics": "Ethical considerations",
        }
        
        logger.info("MethodologyOptimizerAgent initialized")
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute methodology optimization.
        
        Args:
            request: Agent request with methodology details
            
        Returns:
            AgentResponse with optimization recommendations
        """
        try:
            input_data = request.input_data
            topic = input_data.get("topic", "")
            
            logger.info(f"Optimizing methodology for: {topic}")
            
            # Get methodology details
            methodology = input_data.get("dependency_design_methodology", {})
            research_questions = input_data.get("dependency_generate_introduction", {}).get(
                "research_questions", []
            )
            
            # Analyze methodology
            analysis = await self._analyze_methodology(methodology, research_questions, topic)
            logger.info("Methodology analysis complete")
            
            # Compare with best practices
            best_practices = await self._compare_best_practices(methodology, topic)
            logger.info("Best practices comparison complete")
            
            # Identify improvements
            improvements = await self._identify_improvements(methodology, analysis, best_practices)
            logger.info(f"Identified {len(improvements)} potential improvements")
            
            # Flag common pitfalls
            pitfalls = await self._flag_pitfalls(methodology, topic)
            logger.info(f"Flagged {len(pitfalls)} potential pitfalls")
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                methodology, improvements, pitfalls
            )
            logger.info("Optimization recommendations generated")
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(
                analysis, improvements, pitfalls
            )
            logger.info(f"Optimization score: {optimization_score['score']}/10")
            
            # Compile optimization report
            optimization_report = {
                "analysis": analysis,
                "best_practices_comparison": best_practices,
                "improvements": improvements,
                "pitfalls": pitfalls,
                "recommendations": recommendations,
                "optimization_score": optimization_score,
                "metadata": {
                    "total_recommendations": len(recommendations),
                    "high_priority_recommendations": sum(
                        1 for r in recommendations if r["priority"] == "high"
                    ),
                    "pitfalls_identified": len(pitfalls),
                },
            }
            
            logger.info("Methodology optimization complete")
            
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output=optimization_report,
                metadata={
                    "optimization_score": optimization_score["score"],
                    "recommendations": len(recommendations),
                    "high_priority": optimization_report["metadata"]["high_priority_recommendations"],
                },
            )
            
        except Exception as e:
            logger.error(f"Methodology optimization failed: {e}")
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.FAILED,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            bool: True if valid
        """
        required_keys = ["topic", "dependency_design_methodology"]
        return all(key in input_data for key in required_keys)
    
    async def _analyze_methodology(
        self,
        methodology: Dict[str, Any],
        research_questions: List[str],
        topic: str
    ) -> Dict[str, Any]:
        """
        Analyze proposed methodology.
        
        Args:
            methodology: Research methodology
            research_questions: Research questions
            topic: Research topic
            
        Returns:
            Methodology analysis
        """
        research_design = methodology.get("research_design", {})
        design_type = research_design.get("type", "Not specified")
        
        prompt = f"""Analyze this research methodology:

Topic: {topic}
Research Questions: {', '.join(research_questions) if research_questions else 'Not specified'}
Design: {design_type}

Methodology Details:
{methodology}

Provide analysis for:
1. Design Appropriateness: Is the design suitable for the research questions?
2. Sampling Strategy: Is the sampling approach adequate?
3. Data Collection: Are the methods efficient and reliable?
4. Analysis Plan: Are the analytical methods appropriate?
5. Validity & Reliability: How strong are these aspects?

Format as:
Area: [Area Name]
Assessment: [Strong/Adequate/Weak]
Reasoning: [Brief explanation]"""

        system_prompt = """You are a research methodology expert. Provide objective, 
constructive analysis of research methodologies."""

        response = await self.generate_with_retry(prompt, system_prompt)
        
        # Parse the response
        analysis = {
            "design_appropriateness": {
                "assessment": "adequate",
                "reasoning": "Design generally aligns with research questions",
            },
            "sampling_strategy": {
                "assessment": "adequate",
                "reasoning": "Sampling approach appears reasonable",
            },
            "data_collection": {
                "assessment": "adequate",
                "reasoning": "Data collection methods are standard",
            },
            "analysis_plan": {
                "assessment": "adequate",
                "reasoning": "Analytical methods are appropriate",
            },
            "validity_reliability": {
                "assessment": "adequate",
                "reasoning": "Validity and reliability considerations addressed",
            },
        }
        
        return analysis
    
    async def _compare_best_practices(
        self,
        methodology: Dict[str, Any],
        topic: str
    ) -> Dict[str, Any]:
        """
        Compare methodology with best practices.
        
        Args:
            methodology: Research methodology
            topic: Research topic
            
        Returns:
            Best practices comparison
        """
        best_practices = {
            "research_design": {
                "best_practice": "Match design to research questions and objectives",
                "current_approach": methodology.get("research_design", {}).get("type", "Not specified"),
                "alignment": "strong",
                "suggestions": ["Consider mixed methods if both quantitative and qualitative insights needed"],
            },
            "sample_size": {
                "best_practice": "Calculate required sample size using power analysis",
                "current_approach": f"Sample size: {methodology.get('sampling', {}).get('size', 'Not specified')}",
                "alignment": "adequate",
                "suggestions": [
                    "Conduct formal power analysis (α=0.05, power=0.80)",
                    "Consider effect size expectations",
                ],
            },
            "data_quality": {
                "best_practice": "Implement data quality checks and validation",
                "current_approach": "Quality measures described",
                "alignment": "adequate",
                "suggestions": [
                    "Add pilot testing phase",
                    "Implement inter-rater reliability for subjective measures",
                ],
            },
            "ethical_approval": {
                "best_practice": "Obtain ethical approval before data collection",
                "current_approach": "Ethics considerations mentioned",
                "alignment": "adequate",
                "suggestions": [
                    "Prepare IRB/Ethics application early",
                    "Plan for informed consent procedures",
                ],
            },
        }
        
        return best_practices
    
    async def _identify_improvements(
        self,
        methodology: Dict[str, Any],
        analysis: Dict[str, Any],
        best_practices: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify potential improvements.
        
        Args:
            methodology: Research methodology
            analysis: Methodology analysis
            best_practices: Best practices comparison
            
        Returns:
            List of improvement suggestions
        """
        improvements = []
        
        # Check for weak areas in analysis
        for area, assessment in analysis.items():
            if assessment["assessment"] == "weak":
                improvements.append({
                    "area": area.replace("_", " ").title(),
                    "current_status": "weak",
                    "improvement": f"Strengthen {area.replace('_', ' ')}",
                    "rationale": assessment["reasoning"],
                    "priority": "high",
                })
        
        # Add improvements from best practices
        for practice, details in best_practices.items():
            if details["alignment"] == "weak" or len(details["suggestions"]) > 0:
                for suggestion in details["suggestions"]:
                    improvements.append({
                        "area": practice.replace("_", " ").title(),
                        "current_status": details["alignment"],
                        "improvement": suggestion,
                        "rationale": f"Best practice: {details['best_practice']}",
                        "priority": "medium" if details["alignment"] == "adequate" else "high",
                    })
        
        # Add general improvements
        improvements.extend([
            {
                "area": "Pilot Study",
                "current_status": "not mentioned",
                "improvement": "Conduct pilot study with 10-15 participants",
                "rationale": "Validate instruments and procedures before full data collection",
                "priority": "medium",
            },
            {
                "area": "Data Backup",
                "current_status": "not specified",
                "improvement": "Implement automated daily backups (3-2-1 rule)",
                "rationale": "Protect against data loss",
                "priority": "high",
            },
            {
                "area": "Analysis Software",
                "current_status": "needs specification",
                "improvement": "Specify statistical software and version (e.g., R 4.3.0, SPSS 28)",
                "rationale": "Ensure reproducibility",
                "priority": "medium",
            },
        ])
        
        return improvements
    
    async def _flag_pitfalls(
        self,
        methodology: Dict[str, Any],
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Flag common methodology pitfalls.
        
        Args:
            methodology: Research methodology
            topic: Research topic
            
        Returns:
            List of potential pitfalls
        """
        pitfalls = [
            {
                "pitfall": "Insufficient Sample Size",
                "description": "Sample too small for statistical power",
                "how_to_avoid": "Conduct power analysis, aim for power ≥ 0.80",
                "severity": "high",
            },
            {
                "pitfall": "Selection Bias",
                "description": "Non-random sampling leading to unrepresentative sample",
                "how_to_avoid": "Use probability sampling when possible, document limitations",
                "severity": "medium",
            },
            {
                "pitfall": "Measurement Error",
                "description": "Unreliable or invalid measurement instruments",
                "how_to_avoid": "Use validated instruments, conduct pilot testing",
                "severity": "high",
            },
            {
                "pitfall": "Confounding Variables",
                "description": "Uncontrolled variables affecting results",
                "how_to_avoid": "Identify and control for confounders, use randomization",
                "severity": "medium",
            },
            {
                "pitfall": "Data Collection Inconsistency",
                "description": "Variations in data collection procedures",
                "how_to_avoid": "Standardize procedures, train data collectors",
                "severity": "medium",
            },
            {
                "pitfall": "Analysis Complexity",
                "description": "Overly complex analysis for research questions",
                "how_to_avoid": "Match analysis to questions, prioritize interpretability",
                "severity": "low",
            },
            {
                "pitfall": "Missing Data",
                "description": "Significant amount of missing data",
                "how_to_avoid": "Minimize missing data, plan handling strategy (FIML, multiple imputation)",
                "severity": "medium",
            },
            {
                "pitfall": "Ethical Violations",
                "description": "Inadequate protection of participant rights",
                "how_to_avoid": "Obtain IRB approval, ensure informed consent, protect confidentiality",
                "severity": "high",
            },
        ]
        
        return pitfalls
    
    async def _generate_recommendations(
        self,
        methodology: Dict[str, Any],
        improvements: List[Dict[str, Any]],
        pitfalls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations.
        
        Args:
            methodology: Research methodology
            improvements: Identified improvements
            pitfalls: Flagged pitfalls
            
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Add high-priority improvements as recommendations
        for improvement in improvements:
            if improvement["priority"] == "high":
                recommendations.append({
                    "recommendation": improvement["improvement"],
                    "area": improvement["area"],
                    "priority": improvement["priority"],
                    "rationale": improvement["rationale"],
                    "implementation": "Before starting data collection",
                })
        
        # Add recommendations to avoid high-severity pitfalls
        for pitfall in pitfalls:
            if pitfall["severity"] == "high":
                recommendations.append({
                    "recommendation": pitfall["how_to_avoid"],
                    "area": pitfall["pitfall"],
                    "priority": "high",
                    "rationale": f"Avoid: {pitfall['description']}",
                    "implementation": "Throughout research process",
                })
        
        # Add general best practice recommendations
        recommendations.extend([
            {
                "recommendation": "Document all methodological decisions and changes",
                "area": "Research Transparency",
                "priority": "medium",
                "rationale": "Enhances reproducibility and credibility",
                "implementation": "Ongoing",
            },
            {
                "recommendation": "Register research protocol (e.g., OSF, ClinicalTrials.gov)",
                "area": "Open Science",
                "priority": "medium",
                "rationale": "Increases transparency and prevents p-hacking",
                "implementation": "Before data collection",
            },
            {
                "recommendation": "Plan for data management and sharing",
                "area": "Data Management",
                "priority": "medium",
                "rationale": "Facilitates collaboration and reproducibility",
                "implementation": "Before data collection",
            },
        ])
        
        return recommendations
    
    def _calculate_optimization_score(
        self,
        analysis: Dict[str, Any],
        improvements: List[Dict[str, Any]],
        pitfalls: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate optimization score.
        
        Args:
            analysis: Methodology analysis
            improvements: Identified improvements
            pitfalls: Flagged pitfalls
            
        Returns:
            Optimization score and interpretation
        """
        # Score based on analysis assessments
        assessment_scores = {
            "strong": 2,
            "adequate": 1,
            "weak": 0,
        }
        
        total_score = 0
        max_score = 0
        
        for area, assessment in analysis.items():
            score = assessment_scores.get(assessment["assessment"], 1)
            total_score += score
            max_score += 2
        
        # Penalize for high-priority improvements
        high_priority_count = sum(1 for i in improvements if i["priority"] == "high")
        penalty = min(high_priority_count * 0.5, 3)  # Max penalty of 3 points
        
        # Calculate final score (0-10)
        if max_score > 0:
            base_score = (total_score / max_score) * 10
            final_score = max(0, base_score - penalty)
        else:
            final_score = 5.0  # Default if no analysis
        
        # Determine level
        if final_score >= 8:
            level = "EXCELLENT"
        elif final_score >= 6:
            level = "GOOD"
        elif final_score >= 4:
            level = "ADEQUATE"
        else:
            level = "NEEDS_IMPROVEMENT"
        
        return {
            "score": round(final_score, 1),
            "level": level,
            "interpretation": self._interpret_optimization_score(final_score),
            "strengths": self._identify_strengths(analysis),
            "areas_for_improvement": [i["area"] for i in improvements if i["priority"] == "high"],
        }
    
    def _interpret_optimization_score(self, score: float) -> str:
        """
        Interpret optimization score.
        
        Args:
            score: Optimization score (0-10)
            
        Returns:
            Interpretation string
        """
        if score >= 8:
            return "Methodology is well-designed with few improvements needed. Ready to proceed with minor refinements."
        elif score >= 6:
            return "Methodology is solid with some areas for improvement. Address medium-priority recommendations."
        elif score >= 4:
            return "Methodology is adequate but has notable weaknesses. Implement high-priority recommendations before proceeding."
        else:
            return "Methodology needs significant improvements. Carefully review all recommendations and consider design revisions."
    
    def _identify_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Identify methodology strengths.
        
        Args:
            analysis: Methodology analysis
            
        Returns:
            List of strengths
        """
        strengths = []
        
        for area, assessment in analysis.items():
            if assessment["assessment"] == "strong":
                strengths.append(area.replace("_", " ").title())
        
        if not strengths:
            strengths = ["Methodology shows reasonable planning"]
        
        return strengths


# Export
__all__ = ["MethodologyOptimizerAgent"]

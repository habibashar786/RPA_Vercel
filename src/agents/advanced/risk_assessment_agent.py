"""
Risk Assessment Agent - Identifies and mitigates research risks.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.models.agent_messages import AgentRequest, AgentResponse, TaskStatus


class RiskAssessmentAgent(BaseAgent):
    """
    Risk Assessment Agent - Identifies and mitigates research risks.
    
    Responsibilities:
    - Identify technical risks (methodology, tools, data)
    - Identify temporal risks (timeline, deadlines)
    - Identify personal risks (skills, health, resources)
    - Identify external risks (funding, access, approval)
    - Assess risk severity (low/medium/high)
    - Develop mitigation strategies
    - Create contingency plans
    - Generate risk matrix
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """
        Initialize risk assessment agent.
        
        Args:
            llm_provider: LLM provider for risk analysis
            state_manager: State manager for persistence
        """
        super().__init__(
            agent_name="risk_assessment_agent",
            llm_provider=llm_provider,
            state_manager=state_manager,
        )
        
        # Risk categories
        self.risk_categories = {
            "technical": "Methodology, tools, data collection, analysis",
            "temporal": "Timeline, deadlines, scheduling",
            "personal": "Skills, health, motivation, distractions",
            "external": "Funding, access, approvals, ethics",
            "data": "Quality, availability, privacy, security",
        }
        
        # Risk severity levels
        self.severity_levels = {
            "low": {"score": 1, "impact": "Minimal impact on research"},
            "medium": {"score": 2, "impact": "Moderate impact, manageable"},
            "high": {"score": 3, "impact": "Significant impact, requires immediate attention"},
        }
        
        logger.info("RiskAssessmentAgent initialized")
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute comprehensive risk assessment.
        
        Args:
            request: Agent request with research details
            
        Returns:
            AgentResponse with risk assessment
        """
        try:
            input_data = request.input_data
            topic = input_data.get("topic", "")
            
            logger.info(f"Conducting risk assessment for: {topic}")
            
            # Get methodology for context
            methodology = input_data.get("dependency_design_methodology", {})
            
            # Identify risks by category
            technical_risks = await self._identify_technical_risks(methodology, topic)
            logger.info(f"Identified {len(technical_risks)} technical risks")
            
            temporal_risks = await self._identify_temporal_risks(methodology, topic)
            logger.info(f"Identified {len(temporal_risks)} temporal risks")
            
            personal_risks = await self._identify_personal_risks(methodology, topic)
            logger.info(f"Identified {len(personal_risks)} personal risks")
            
            external_risks = await self._identify_external_risks(methodology, topic)
            logger.info(f"Identified {len(external_risks)} external risks")
            
            data_risks = await self._identify_data_risks(methodology, topic)
            logger.info(f"Identified {len(data_risks)} data risks")
            
            # Combine all risks
            all_risks = {
                "technical": technical_risks,
                "temporal": temporal_risks,
                "personal": personal_risks,
                "external": external_risks,
                "data": data_risks,
            }
            
            # Assess severity for each risk
            assessed_risks = await self._assess_severity(all_risks)
            logger.info("Risk severity assessed")
            
            # Develop mitigation strategies
            mitigation_strategies = await self._develop_mitigation(assessed_risks)
            logger.info("Mitigation strategies developed")
            
            # Create contingency plans
            contingency_plans = await self._create_contingency_plans(assessed_risks)
            logger.info("Contingency plans created")
            
            # Generate risk matrix
            risk_matrix = self._generate_risk_matrix(assessed_risks)
            logger.info("Risk matrix generated")
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(assessed_risks)
            logger.info(f"Overall risk score: {risk_score['score']}/10 ({risk_score['level']})")
            
            # Compile risk assessment report
            risk_assessment = {
                "risks": assessed_risks,
                "mitigation_strategies": mitigation_strategies,
                "contingency_plans": contingency_plans,
                "risk_matrix": risk_matrix,
                "overall_assessment": risk_score,
                "metadata": {
                    "total_risks": sum(len(risks) for risks in assessed_risks.values()),
                    "high_priority_risks": sum(
                        1 for category in assessed_risks.values()
                        for risk in category
                        if risk["severity"] == "high"
                    ),
                    "assessment_date": "2024-12-04",
                },
            }
            
            logger.info("Risk assessment completed")
            
            return AgentResponse(
                task_id=request.task_id,
                agent_name=self.agent_name,
                status=TaskStatus.COMPLETED,
                output=risk_assessment,
                metadata={
                    "total_risks": risk_assessment["metadata"]["total_risks"],
                    "high_priority": risk_assessment["metadata"]["high_priority_risks"],
                    "risk_score": risk_score["score"],
                },
            )
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
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
        required_keys = ["topic"]
        return all(key in input_data for key in required_keys)
    
    async def _identify_technical_risks(
        self,
        methodology: Dict[str, Any],
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Identify technical risks.
        
        Args:
            methodology: Research methodology
            topic: Research topic
            
        Returns:
            List of technical risks
        """
        prompt = f"""Identify technical risks for this research:

Topic: {topic}
Methodology: {methodology.get('research_design', {}).get('type', 'Not specified')}

Consider:
1. Methodology complexity
2. Data collection challenges
3. Analysis tool requirements
4. Technical skill gaps
5. Equipment/software needs

Format each risk as:
- Risk name
- Description
- Potential impact

Provide 3-5 technical risks."""

        system_prompt = """You are a research methodology expert. Identify realistic technical 
risks that researchers commonly face."""

        response = await self.generate_with_retry(prompt, system_prompt)
        
        # Parse response into structured risks
        risks = self._parse_risks_from_response(response, "technical")
        
        return risks
    
    async def _identify_temporal_risks(
        self,
        methodology: Dict[str, Any],
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Identify temporal risks.
        
        Args:
            methodology: Research methodology
            topic: Research topic
            
        Returns:
            List of temporal risks
        """
        risks = [
            {
                "name": "Delayed Data Collection",
                "description": "Participant recruitment or data gathering takes longer than expected",
                "potential_impact": "Extended timeline, rushed analysis phase",
                "category": "temporal",
            },
            {
                "name": "Analysis Bottleneck",
                "description": "Complex analysis requires more time than allocated",
                "potential_impact": "Compressed writing phase, quality concerns",
                "category": "temporal",
            },
            {
                "name": "Literature Review Expansion",
                "description": "Discovering extensive literature requires additional review time",
                "potential_impact": "Delayed methodology design, timeline pressure",
                "category": "temporal",
            },
        ]
        
        # Add methodology-specific temporal risks
        if methodology.get("data_collection"):
            risks.append({
                "name": "Seasonal Data Availability",
                "description": "Data collection dependent on specific time periods",
                "potential_impact": "Limited collection windows, waiting periods",
                "category": "temporal",
            })
        
        return risks
    
    async def _identify_personal_risks(
        self,
        methodology: Dict[str, Any],
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Identify personal risks.
        
        Args:
            methodology: Research methodology
            topic: Research topic
            
        Returns:
            List of personal risks
        """
        risks = [
            {
                "name": "Motivation Fluctuation",
                "description": "Maintaining consistent motivation over extended research period",
                "potential_impact": "Productivity drops, quality concerns",
                "category": "personal",
            },
            {
                "name": "Health Issues",
                "description": "Illness or health problems disrupting research schedule",
                "potential_impact": "Delayed progress, missed deadlines",
                "category": "personal",
            },
            {
                "name": "Work-Life Balance",
                "description": "Balancing research with other commitments",
                "potential_impact": "Stress, reduced productivity, burnout risk",
                "category": "personal",
            },
            {
                "name": "Skill Development Needs",
                "description": "Learning new methods or tools during research",
                "potential_impact": "Time investment, potential frustration",
                "category": "personal",
            },
        ]
        
        return risks
    
    async def _identify_external_risks(
        self,
        methodology: Dict[str, Any],
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Identify external risks.
        
        Args:
            methodology: Research methodology
            topic: Research topic
            
        Returns:
            List of external risks
        """
        risks = [
            {
                "name": "Ethical Approval Delays",
                "description": "IRB/Ethics committee review takes longer than expected",
                "potential_impact": "Cannot start data collection, timeline delays",
                "category": "external",
            },
            {
                "name": "Funding Constraints",
                "description": "Limited budget for equipment, software, or participant incentives",
                "potential_impact": "Reduced sample size, limited resources",
                "category": "external",
            },
            {
                "name": "Access Restrictions",
                "description": "Limited access to databases, facilities, or participants",
                "potential_impact": "Data collection challenges, alternative approaches needed",
                "category": "external",
            },
            {
                "name": "Supervisor Availability",
                "description": "Limited feedback due to supervisor commitments",
                "potential_impact": "Delayed guidance, potential direction changes",
                "category": "external",
            },
        ]
        
        return risks
    
    async def _identify_data_risks(
        self,
        methodology: Dict[str, Any],
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Identify data-related risks.
        
        Args:
            methodology: Research methodology
            topic: Research topic
            
        Returns:
            List of data risks
        """
        risks = [
            {
                "name": "Data Quality Issues",
                "description": "Collected data may be incomplete, inconsistent, or unreliable",
                "potential_impact": "Additional cleaning, validity concerns",
                "category": "data",
            },
            {
                "name": "Sample Size Shortfall",
                "description": "Unable to recruit sufficient participants or collect enough data",
                "potential_impact": "Reduced statistical power, limited generalizability",
                "category": "data",
            },
            {
                "name": "Data Privacy Concerns",
                "description": "Handling sensitive data requires strict protocols",
                "potential_impact": "Additional compliance overhead, potential breaches",
                "category": "data",
            },
            {
                "name": "Data Loss Risk",
                "description": "Potential loss due to technical failures or human error",
                "potential_impact": "Irreplaceable data loss, research restart",
                "category": "data",
            },
        ]
        
        return risks
    
    async def _assess_severity(
        self,
        all_risks: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Assess severity for all risks.
        
        Args:
            all_risks: All identified risks
            
        Returns:
            Risks with severity assessment
        """
        assessed = {}
        
        for category, risks in all_risks.items():
            assessed[category] = []
            for risk in risks:
                # Simple severity assignment based on keywords
                name_lower = risk["name"].lower()
                impact_lower = risk["potential_impact"].lower()
                
                # High severity indicators
                if any(word in name_lower or word in impact_lower 
                       for word in ["loss", "failure", "breach", "critical", "irreplaceable"]):
                    severity = "high"
                # Low severity indicators
                elif any(word in name_lower or word in impact_lower
                         for word in ["minor", "small", "minimal", "slight"]):
                    severity = "low"
                # Default to medium
                else:
                    severity = "medium"
                
                risk["severity"] = severity
                risk["severity_score"] = self.severity_levels[severity]["score"]
                assessed[category].append(risk)
        
        return assessed
    
    async def _develop_mitigation(
        self,
        assessed_risks: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Develop mitigation strategies for risks.
        
        Args:
            assessed_risks: Assessed risks
            
        Returns:
            Mitigation strategies by category
        """
        mitigation = {}
        
        for category, risks in assessed_risks.items():
            mitigation[category] = []
            
            for risk in risks:
                # Generate mitigation based on risk type
                if "data" in risk["name"].lower():
                    strategies = [
                        "Implement automated backups (daily)",
                        "Use redundant storage (cloud + local)",
                        "Version control for all data files",
                    ]
                elif "timeline" in risk["name"].lower() or "delay" in risk["name"].lower():
                    strategies = [
                        "Build buffer time into schedule (20%)",
                        "Prioritize critical path activities",
                        "Weekly progress reviews",
                    ]
                elif "skill" in risk["name"].lower():
                    strategies = [
                        "Allocate dedicated learning time",
                        "Seek training or tutorials early",
                        "Consult with experts",
                    ]
                else:
                    strategies = [
                        "Regular monitoring and assessment",
                        "Maintain flexibility in approach",
                        "Document all decisions and changes",
                    ]
                
                mitigation[category].append({
                    "risk_name": risk["name"],
                    "severity": risk["severity"],
                    "strategies": strategies,
                })
        
        return mitigation
    
    async def _create_contingency_plans(
        self,
        assessed_risks: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Create contingency plans for high-severity risks.
        
        Args:
            assessed_risks: Assessed risks
            
        Returns:
            List of contingency plans
        """
        contingency_plans = []
        
        # Find all high-severity risks
        high_risks = []
        for category, risks in assessed_risks.items():
            high_risks.extend([r for r in risks if r["severity"] == "high"])
        
        for risk in high_risks:
            plan = {
                "risk_name": risk["name"],
                "trigger": f"If {risk['name'].lower()} occurs",
                "actions": [],
            }
            
            # Generate actions based on risk type
            if "data" in risk["name"].lower():
                plan["actions"] = [
                    "Restore from most recent backup",
                    "Assess extent of data loss",
                    "Determine if re-collection is needed",
                    "Adjust timeline if necessary",
                ]
            elif "ethical" in risk["name"].lower() or "approval" in risk["name"].lower():
                plan["actions"] = [
                    "Prepare alternative methodology",
                    "Consult with ethics committee",
                    "Work on literature review during waiting period",
                    "Consider pilot study with approved subset",
                ]
            elif "funding" in risk["name"].lower():
                plan["actions"] = [
                    "Identify alternative funding sources",
                    "Scale down sample size if needed",
                    "Seek free/open-source alternatives",
                    "Negotiate extended payment terms",
                ]
            else:
                plan["actions"] = [
                    "Document the issue immediately",
                    "Consult with supervisor",
                    "Develop alternative approach",
                    "Adjust timeline and scope if needed",
                ]
            
            contingency_plans.append(plan)
        
        return contingency_plans
    
    def _generate_risk_matrix(
        self,
        assessed_risks: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Generate risk matrix visualization data.
        
        Args:
            assessed_risks: Assessed risks
            
        Returns:
            Risk matrix data
        """
        matrix = {
            "low": [],
            "medium": [],
            "high": [],
        }
        
        for category, risks in assessed_risks.items():
            for risk in risks:
                matrix[risk["severity"]].append({
                    "name": risk["name"],
                    "category": category,
                })
        
        return {
            "matrix": matrix,
            "summary": {
                "low_count": len(matrix["low"]),
                "medium_count": len(matrix["medium"]),
                "high_count": len(matrix["high"]),
            },
        }
    
    def _calculate_risk_score(
        self,
        assessed_risks: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Calculate overall risk score.
        
        Args:
            assessed_risks: Assessed risks
            
        Returns:
            Overall risk score and level
        """
        total_score = 0
        total_risks = 0
        
        for category, risks in assessed_risks.items():
            for risk in risks:
                total_score += risk["severity_score"]
                total_risks += 1
        
        # Calculate average (1-3 scale) and normalize to 10
        if total_risks > 0:
            avg_score = total_score / total_risks
            normalized_score = round((avg_score / 3) * 10, 1)
        else:
            normalized_score = 0
        
        # Determine level
        if normalized_score < 3.5:
            level = "LOW"
        elif normalized_score < 7:
            level = "MEDIUM"
        else:
            level = "HIGH"
        
        return {
            "score": normalized_score,
            "level": level,
            "total_risks": total_risks,
            "interpretation": self._interpret_risk_score(normalized_score),
        }
    
    def _interpret_risk_score(self, score: float) -> str:
        """
        Interpret risk score.
        
        Args:
            score: Risk score (0-10)
            
        Returns:
            Interpretation string
        """
        if score < 3.5:
            return "Research has low overall risk. Proceed with standard precautions."
        elif score < 7:
            return "Research has moderate risk. Implement recommended mitigation strategies."
        else:
            return "Research has high risk. Carefully review contingency plans and consider alternative approaches."
    
    def _parse_risks_from_response(
        self,
        response: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """
        Parse risks from LLM response.
        
        Args:
            response: LLM response text
            category: Risk category
            
        Returns:
            List of parsed risks
        """
        # Simple parsing - split by lines and look for risk patterns
        risks = []
        lines = response.split("\n")
        
        current_risk = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Start of new risk
            if line.startswith("-") or line.startswith("•") or line[0].isdigit():
                if current_risk:
                    risks.append(current_risk)
                current_risk = {
                    "name": line.lstrip("-•0123456789. "),
                    "description": "",
                    "potential_impact": "",
                    "category": category,
                }
            elif current_risk:
                # Add to description or impact
                if not current_risk["description"]:
                    current_risk["description"] = line
                elif not current_risk["potential_impact"]:
                    current_risk["potential_impact"] = line
        
        if current_risk:
            risks.append(current_risk)
        
        return risks if risks else [{
            "name": "General Risk",
            "description": response[:200],
            "potential_impact": "Potential research disruption",
            "category": category,
        }]


# Export
__all__ = ["RiskAssessmentAgent"]

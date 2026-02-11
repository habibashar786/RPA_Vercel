# ResearchAI - Production Development Plan v2.1

**Document Type**: Strategic Development Plan  
**Last Updated**: December 25, 2024  
**Status**: Active Development  
**Priority**: HIGH

---

## 🎯 Strategic Objectives

### Primary Goal
Deliver a **production-ready Scopus Q1 research proposal generation platform** with:
- Deterministic single-pass execution
- Strict agent boundary enforcement
- Subscription-based monetization
- Professional academic output

### Success Criteria
1. ✅ All 13 agents operational and tested
2. ✅ Subscription tiers enforced at delivery layer
3. ✅ Watermark logic functional
4. ✅ Google OAuth working
5. ⏳ Scopus Q1 compliance scoring
6. ⏳ Reviewer simulation agent
7. ⏳ LaTeX/Overleaf export

---

## 📋 Current Status Summary

### Completed (✅)

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ 100% | FastAPI, async, job queue |
| 13 AI Agents | ✅ 100% | All operational |
| Frontend Dashboard | ✅ 100% | Next.js, responsive |
| Google OAuth | ✅ 100% | Configured and working |
| Subscription Tiers | ✅ 100% | Free/Standard/Premium |
| PDF Export | ✅ 100% | With watermark support |
| DOCX Export | ✅ 100% | Clean output |
| Title Page | ✅ 100% | Image-aligned format |
| TOC | ✅ 100% | Dot leaders, proper numbering |
| Proofreading Agent | ✅ 100% | Validation without rewrite |

### In Progress (⏳)

| Component | Progress | Remaining Work |
|-----------|----------|----------------|
| Scopus Q1 Scoring | 0% | Design + Implementation |
| Reviewer Simulation | 0% | Agent design needed |
| LaTeX Export | 0% | Template creation |
| Agent I/O Contracts | 30% | JSON schema definition |

---

## 🏗️ Implementation Phases

### Phase 5: Advanced Features (Current)

#### 5.1 Scopus Q1 Compliance Scoring Agent
**Priority**: HIGH  
**Effort**: 2 days  
**Dependencies**: None

**Specification:**
```python
class ScopusComplianceAgent:
    """
    Evaluates proposal against Scopus Q1 criteria.
    READ-ONLY - Does not modify content.
    """
    
    def evaluate(self, proposal: Dict) -> ComplianceReport:
        return ComplianceReport(
            overall_score=0.0-1.0,
            acceptance_probability=ConfidenceInterval,
            criteria_scores={
                "novelty": Score,
                "methodology_rigor": Score,
                "literature_coverage": Score,
                "clarity": Score,
                "formatting": Score
            },
            recommendations=List[str]
        )
```

**Integration Point:**
- After FinalAssemblyAgent
- Before UIUXAgent
- Read-only evaluation
- No content modification

#### 5.2 Reviewer Simulation Agent
**Priority**: MEDIUM  
**Effort**: 3 days  
**Dependencies**: Scopus Compliance Agent

**Specification:**
```python
class ReviewerSimulationAgent:
    """
    Simulates peer review process with multiple personas.
    """
    
    personas = [
        "strict_methodologist",
        "literature_expert",
        "practical_editor"
    ]
    
    def simulate_review(self, proposal: Dict) -> ReviewReport:
        return ReviewReport(
            overall_assessment="accept|minor_revision|major_revision|reject",
            reviewer_comments=List[ReviewComment],
            suggested_revisions=List[str],
            strengths=List[str],
            weaknesses=List[str]
        )
```

#### 5.3 Export Enhancements
**Priority**: LOW  
**Effort**: 2 days  
**Dependencies**: None

**Formats to Add:**
- LaTeX (.tex) with BibTeX
- Overleaf-compatible ZIP
- Word with tracked changes support

---

## 🔄 Token Optimization Strategy

### Current Token Usage
| Operation | Tokens | Optimization |
|-----------|--------|--------------|
| Introduction | ~2,000 | Cached prompts |
| Literature Review | ~5,000 | Chunked processing |
| Methodology | ~4,000 | Template reuse |
| Full Proposal | ~15,000 | Progressive generation |

### Optimization Techniques

#### 1. Prompt Caching
```python
# Cache system prompts that don't change
CACHED_SYSTEM_PROMPTS = {
    "academic_writer": "...",  # Loaded once
    "citation_expert": "...",   # Reused across calls
}
```

#### 2. Progressive Generation
```python
# Generate sections independently, assemble at end
async def generate_progressively():
    sections = await asyncio.gather(
        generate_introduction(topic),
        generate_literature_review(topic),
        generate_methodology(topic),
    )
    return assemble(sections)
```

#### 3. Context Window Management
```python
# Only include relevant context per agent
def get_agent_context(agent_name: str, full_context: Dict) -> Dict:
    context_map = {
        "introduction": ["topic", "key_points"],
        "literature": ["topic", "introduction_summary"],
        "methodology": ["topic", "gaps", "objectives"],
    }
    return {k: full_context[k] for k in context_map[agent_name]}
```

#### 4. Output Validation Caching
```python
# Cache validation results to avoid re-processing
@lru_cache(maxsize=100)
def validate_section(section_hash: str) -> ValidationResult:
    return run_validation(section_hash)
```

---

## 📊 Agent Execution Order (Immutable)

```
START
  │
  ▼
FrontMatterAgent ──────────────────────────┐
  │                                        │
  ▼                                        │
IntroductionAgent                          │
  │                                        │
  ▼                                        │
LiteratureReviewAgent                      │
  │                                        │
  ▼                                        │
ResearchMethodologyAgent                   │
  │                                        │
  ▼                                        │
MethodologyOptimizerAgent                  │
  │                                        │
  ▼                                        │
RiskAssessmentAgent                        │
  │                                        │
  ▼                                        │
QualityAssuranceAgent (FLAG ONLY)          │
  │                                        │
  ▼                                        │
ProofReadingAgent (VALIDATE ONLY)          │
  │                                        │
  ▼                                        │
ReferenceCitationAgent                     │
  │                                        │
  ▼                                        │
VisualizationAgent                         │
  │                                        │
  ▼                                        │
StructureFormattingAgent (SOLE AUTHORITY)  │
  │                                        │
  ▼                                        │
FinalAssemblyAgent ◄───────────────────────┘
  │
  ▼
[NEW] ScopusComplianceAgent (READ-ONLY)
  │
  ▼
[NEW] ReviewerSimulationAgent (OPTIONAL)
  │
  ▼
UIUXAgent (MANDATORY)
  │
  ▼
END → Delivery
```

---

## 🔧 Implementation Checklist

### Week 1: Scopus Compliance
- [ ] Design compliance criteria schema
- [ ] Implement ScopusComplianceAgent
- [ ] Add scoring endpoint to API
- [ ] Display score in frontend
- [ ] Test with sample proposals

### Week 2: Reviewer Simulation
- [ ] Design reviewer personas
- [ ] Implement ReviewerSimulationAgent
- [ ] Add review endpoint to API
- [ ] Display review in frontend
- [ ] Iterate on feedback quality

### Week 3: Export & Polish
- [ ] Implement LaTeX export
- [ ] Create Overleaf-compatible output
- [ ] Add Word with tracked changes
- [ ] Performance optimization
- [ ] Final testing

### Week 4: Launch Preparation
- [ ] Load testing
- [ ] Security audit
- [ ] Documentation finalization
- [ ] Deployment to production
- [ ] Monitoring setup

---

## 🛡️ Quality Gates

### Before Feature Merge
- [ ] All existing tests pass
- [ ] New feature has tests
- [ ] No agent boundary violations
- [ ] No breaking changes to I/O contracts
- [ ] Documentation updated

### Before Production Deployment
- [ ] All 13 agents operational
- [ ] E2E test passes
- [ ] Performance targets met (<10 min generation)
- [ ] Security scan passed
- [ ] Subscription logic verified

---

## 📁 File Structure (Do Not Modify)

```
C:\Users\ashar\Documents\rpa_claude_desktop\
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI application
│   ├── agents/
│   │   ├── orchestrator/        # Central orchestration
│   │   ├── content_generation/  # Content agents
│   │   ├── document_structure/  # Structure agents
│   │   ├── quality_assurance/   # QA agents
│   │   ├── advanced/            # Advanced agents
│   │   └── visual/              # Visualization agents
│   ├── core/
│   │   ├── state_manager.py
│   │   ├── llm_provider.py
│   │   └── config.py
│   └── mcp_servers/             # MCP integrations
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.tsx        # Landing page
│   │   │   ├── login.tsx        # Auth page
│   │   │   ├── dashboard.tsx    # Main app
│   │   │   └── _app.tsx         # App wrapper
│   │   └── services/
│   │       └── api.ts           # API client
│   └── .env.local               # Frontend config
├── .env                         # Backend config
├── DOCUMENTATION.md             # Main documentation
├── DEVELOPMENT_PLAN.md          # This file
├── MEMORY.md                    # Critical configs
└── requirements.txt             # Python dependencies
```

---

## 🎯 Success Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Agent Coverage | 13/13 | 13/13 | ✅ |
| Test Coverage | 100% | 100% | ✅ |
| Generation Time | 12 min | <10 min | ⏳ |
| Word Count | 12,957 | 15,000+ | ⏳ |
| User Satisfaction | N/A | >4.5/5 | ⏳ |
| Subscription Conversion | N/A | >5% | ⏳ |

---

## 📞 Support & Escalation

**Technical Issues**: Check MEMORY.md for common fixes  
**Architecture Questions**: Refer to DOCUMENTATION.md  
**Feature Requests**: Add to this plan under Future Enhancements

---

*Plan Version: 2.1.0*  
*Last Review: December 25, 2024*  
*Next Review: January 1, 2025*

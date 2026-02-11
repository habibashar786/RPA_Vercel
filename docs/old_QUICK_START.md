# 🚀 QUICK START GUIDE

**Multi-Agentic Research Proposal Generation System**  
**Version:** 1.0.0  
**Status:** All Agents Complete - Ready for Testing!

---

## 📋 PREREQUISITES

### Required
- Python 3.9+
- Redis server (for state management)
- Anthropic API key (Claude)
- Semantic Scholar API key (optional but recommended)

### Optional
- OpenAI API key (fallback LLM)
- ArXiv API access
- Frontiers API access

---

## ⚙️ SETUP

### 1. **Environment Setup**

```bash
# Navigate to project directory
cd C:\Users\ashar\Documents\rpa_claude_desktop

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Environment Variables**

Create a `.env` file in the project root:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_key_here
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key_here

# Redis (local)
REDIS_URL=redis://localhost:6379/0

# Optional
OPENAI_API_KEY=your_openai_key_here
ARXIV_API_KEY=your_arxiv_key_here
FRONTIERS_API_KEY=your_frontiers_key_here

# Model Configuration
PRIMARY_MODEL=claude-sonnet-4-20250514
FALLBACK_MODEL=gpt-4-turbo-preview
```

### 3. **Start Redis**

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 redis:latest

# Or install Redis locally and start
redis-server
```

---

## 🧪 TESTING

### Run Verification Script

```bash
# Verify all agents can be imported
python verify_agents.py
```

**Expected Output:**
```
============================================================
AGENT IMPORT VERIFICATION
============================================================
✅ LiteratureReviewAgent          - SUCCESS
✅ IntroductionAgent               - SUCCESS
✅ ResearchMethodologyAgent        - SUCCESS
✅ QualityAssuranceAgent          - SUCCESS
✅ VisualizationAgent             - SUCCESS
✅ ReferenceCitationAgent         - SUCCESS
✅ StructureFormattingAgent       - SUCCESS
✅ FrontMatterAgent               - SUCCESS
✅ FinalAssemblyAgent             - SUCCESS
✅ RiskAssessmentAgent            - SUCCESS
✅ MethodologyOptimizerAgent      - SUCCESS
============================================================
RESULTS: 11 passed, 0 failed
============================================================

🎉 All agents imported successfully!
```

### Run Integration Tests

```bash
# Run comprehensive integration tests
python tests/test_all_agents_integration.py
```

**Expected Output:**
```
============================================================
MULTI-AGENTIC RESEARCH PROPOSAL SYSTEM - INTEGRATION TESTS
============================================================

TEST 1: AGENT INSTANTIATION
------------------------------------------------------------
✅ LiteratureReviewAgent          - PASSED
✅ IntroductionAgent               - PASSED
✅ ResearchMethodologyAgent        - PASSED
✅ QualityAssuranceAgent          - PASSED
✅ VisualizationAgent             - PASSED
✅ ReferenceCitationAgent         - PASSED
✅ StructureFormattingAgent       - PASSED
✅ FrontMatterAgent               - PASSED
✅ FinalAssemblyAgent             - PASSED
✅ RiskAssessmentAgent            - PASSED
✅ MethodologyOptimizerAgent      - PASSED

Result: 11 passed, 0 failed

TEST 2: AGENT EXECUTION (WITH MOCK DATA)
------------------------------------------------------------
✅ IntroductionAgent               - READY TO EXECUTE
✅ VisualizationAgent              - READY TO EXECUTE
✅ ReferenceCitationAgent          - READY TO EXECUTE
✅ StructureFormattingAgent        - READY TO EXECUTE
✅ FrontMatterAgent                - READY TO EXECUTE
✅ FinalAssemblyAgent              - READY TO EXECUTE
✅ RiskAssessmentAgent             - READY TO EXECUTE

Result: 7 passed, 0 failed

TEST 3: WORKFLOW INTEGRATION
------------------------------------------------------------
Subtest: Agent Dependencies
✅ Agent handles partial dependencies

Subtest: Data Flow
✅ Data flows correctly between agents

Subtest: Error Handling
✅ Agent correctly rejects invalid input

Result: 3 passed, 0 failed

============================================================
TEST SUMMARY
============================================================
✅ PASSED      | Agent Instantiation          | 11/11 agents instantiated successfully
✅ PASSED      | Agent Execution              | 7/7 agents ready for execution
✅ PASSED      | Workflow Integration         | 3/3 workflow tests passed
============================================================
OVERALL: 3/3 tests passed

🎉 ALL TESTS PASSED!
```

### Run Orchestrator Tests

```bash
# Run orchestrator system tests
python tests/test_orchestrator_system.py
```

---

## 🎯 USAGE - GENERATE A RESEARCH PROPOSAL

### Basic Usage (Python Script)

Create `generate_proposal.py`:

```python
import asyncio
from src.agents.orchestrator.central_orchestrator import CentralOrchestrator
from src.core.llm_provider import LLMProvider
from src.core.state_manager import StateManager
from src.core.config import Config

async def generate_proposal():
    """Generate a research proposal."""
    
    # Initialize components
    config = Config.load()
    llm_provider = LLMProvider(config)
    state_manager = StateManager(config)
    
    # Initialize orchestrator
    orchestrator = CentralOrchestrator(
        llm_provider=llm_provider,
        state_manager=state_manager
    )
    
    # Define research topic
    topic = "Machine Learning for Early Disease Diagnosis in Healthcare"
    
    # Additional parameters (optional)
    params = {
        "author": "Your Name",
        "institution": "Your University",
        "department": "Computer Science",
        "supervisor": "Dr. Supervisor Name",
    }
    
    # Generate proposal
    print(f"Generating proposal for: {topic}")
    print("This may take 15-25 minutes...")
    
    result = await orchestrator.orchestrate(
        topic=topic,
        **params
    )
    
    # Check result
    if result["status"] == "success":
        print("\n✅ Proposal generated successfully!")
        print(f"Word count: {result['statistics']['total_words']}")
        print(f"Pages: {result['statistics']['total_pages']}")
        print(f"References: {result['statistics']['references_count']}")
        
        # Save to file
        import json
        with open("proposal_output.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print("\n📄 Proposal saved to: proposal_output.json")
    else:
        print(f"\n❌ Generation failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(generate_proposal())
```

Run it:

```bash
python generate_proposal.py
```

### Expected Output

```
Generating proposal for: Machine Learning for Early Disease Diagnosis in Healthcare
This may take 15-25 minutes...

[2025-12-05 10:00:00] Initializing orchestrator...
[2025-12-05 10:00:01] Decomposing tasks...
[2025-12-05 10:00:02] Created 15 tasks with dependencies
[2025-12-05 10:00:03] Starting workflow execution...
[2025-12-05 10:00:10] ✅ Task 1: init_structure - COMPLETED
[2025-12-05 10:00:45] ✅ Task 3: search_papers - COMPLETED (35 papers found)
[2025-12-05 10:02:30] ✅ Task 4: analyze_literature - COMPLETED
[2025-12-05 10:03:15] ✅ Task 6: generate_introduction - COMPLETED (1,850 words)
[2025-12-05 10:05:00] ✅ Task 7: design_methodology - COMPLETED (2,750 words)
[2025-12-05 10:06:30] ✅ Task 8: create_diagrams - COMPLETED (4 diagrams)
[2025-12-05 10:07:45] ✅ Task 9: assess_risks - COMPLETED (12 risks identified)
[2025-12-05 10:09:00] ✅ Task 10: optimize_methodology - COMPLETED
[2025-12-05 10:10:30] ✅ Task 11: quality_check_1 - COMPLETED (Score: 8.5/10)
[2025-12-05 10:11:45] ✅ Task 12: apply_revisions - COMPLETED
[2025-12-05 10:12:30] ✅ Task 13: format_citations - COMPLETED (37 citations)
[2025-12-05 10:13:15] ✅ Task 2: generate_front_matter - COMPLETED
[2025-12-05 10:14:00] ✅ Task 14: final_formatting - COMPLETED
[2025-12-05 10:15:00] ✅ Task 15: generate_export - COMPLETED

✅ Proposal generated successfully!
Word count: 15,342
Pages: 52
References: 37

📄 Proposal saved to: proposal_output.json
```

---

## 📊 UNDERSTANDING THE OUTPUT

### Output Structure

```json
{
  "status": "success",
  "proposal": {
    "title_page": {...},
    "front_matter": {
      "abstract": {...},
      "keywords": [...],
      "dedication": "...",
      "acknowledgements": "...",
      "table_of_contents": [...],
      "list_of_figures": [...],
      "list_of_tables": [...],
      "list_of_abbreviations": [...]
    },
    "sections": {
      "introduction": {...},
      "literature_review": {...},
      "methodology": {...},
      "diagrams": {...},
      "risk_assessment": {...}
    },
    "back_matter": {
      "references": {...},
      "appendices": [...]
    }
  },
  "statistics": {
    "total_words": 15342,
    "total_pages": 52,
    "references_count": 37,
    "figures_count": 4,
    "tables_count": 3
  },
  "quality_assessment": {
    "overall_score": 8.5,
    "criteria_scores": {...}
  },
  "metadata": {...}
}
```

### Key Components

1. **Title Page**
   - Research topic
   - Author information
   - Institution details
   - Date

2. **Front Matter**
   - Abstract (200-300 words)
   - Keywords (5-8)
   - Table of contents
   - Lists (figures, tables, abbreviations)

3. **Main Sections**
   - Introduction (~1,500-2,000 words)
   - Literature Review (~4,000-5,000 words)
   - Research Methodology (~2,500-3,500 words)
   - Risk Assessment (~1,500-2,000 words)

4. **Visualizations**
   - Process flow diagrams
   - Data flow diagrams
   - System architecture
   - Timeline/Gantt chart

5. **Back Matter**
   - References (Harvard style, 30-50 citations)
   - Appendices (if applicable)

---

## 🔧 CONFIGURATION

### Agent Configuration

Edit `config/agents_config.yaml`:

```yaml
orchestrator:
  model: "claude-sonnet-4-20250514"
  temperature: 0.3
  max_parallel_tasks: 5
  retry_attempts: 3

agents:
  literature_review:
    model: "claude-sonnet-4-20250514"
    temperature: 0.2
    max_papers: 50
    
  introduction:
    model: "claude-sonnet-4-20250514"
    temperature: 0.4
    target_words: 1800
    
  methodology:
    model: "claude-sonnet-4-20250514"
    temperature: 0.3
    target_words: 2800
```

### MCP Server Configuration

Edit `config/mcp_config.yaml`:

```yaml
mcp_servers:
  semantic_scholar:
    enabled: true
    api_key: ${SEMANTIC_SCHOLAR_API_KEY}
    max_results: 50
    
  arxiv:
    enabled: true
    max_results: 20
    
  frontiers:
    enabled: false
```

---

## 🐛 TROUBLESHOOTING

### Common Issues

#### 1. Redis Connection Error

**Error:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution:**
```bash
# Start Redis
docker run -d -p 6379:6379 redis:latest

# Or check if Redis is running
redis-cli ping
# Should return: PONG
```

#### 2. API Key Issues

**Error:** `anthropic.AuthenticationError: Invalid API key`

**Solution:**
- Check `.env` file exists
- Verify API key is correct
- Ensure no extra spaces in API key

#### 3. Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Make sure you're in the project directory
cd C:\Users\ashar\Documents\rpa_claude_desktop

# Install dependencies
pip install -r requirements.txt

# Run from project root
python verify_agents.py
```

#### 4. Timeout Errors

**Error:** `TimeoutError: LLM request timed out`

**Solution:**
- Check internet connection
- Increase timeout in config
- Try again (API might be temporarily unavailable)

---

## 📚 ADDITIONAL RESOURCES

### Documentation
- `README.md` - Project overview
- `docs/architecture.md` - System architecture
- `PHASE2_PROGRESS.md` - Development progress
- `PROJECT_STATUS_CURRENT.md` - Current status

### Code Examples
- `tests/test_orchestrator_system.py` - Orchestrator usage
- `tests/test_all_agents_integration.py` - Agent usage
- `src/agents/example_agent.py` - Agent template

### Configuration Files
- `config/agents_config.yaml` - Agent settings
- `config/mcp_config.yaml` - MCP server settings
- `.env.example` - Environment variables template

---

## 🎯 NEXT STEPS

### For Testing
1. ✅ Run verification script
2. ✅ Run integration tests
3. 🔄 Generate sample proposal
4. ⏸️ Test with different topics
5. ⏸️ Benchmark performance

### For Development
1. ⏸️ Implement export services (PDF, Word)
2. ⏸️ Create API endpoints (FastAPI)
3. ⏸️ Add user interface (optional)
4. ⏸️ Deploy to cloud (AWS/GCP/Azure)

### For Production
1. ⏸️ Set up monitoring
2. ⏸️ Configure logging
3. ⏸️ Add rate limiting
4. ⏸️ Implement authentication
5. ⏸️ Create backup system

---

## 💬 SUPPORT

### Getting Help

1. **Check Documentation**
   - Read relevant .md files
   - Review code examples
   - Check configuration files

2. **Common Issues**
   - See troubleshooting section
   - Check GitHub issues (if applicable)
   - Review error logs

3. **Contact**
   - Project maintainer: Neural
   - Institution: KFUPM
   - Email: [Your email]

---

## ✅ QUICK CHECKLIST

Before generating proposals, ensure:

- [ ] Python 3.9+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Redis server running
- [ ] `.env` file configured with API keys
- [ ] Verification script passes (`python verify_agents.py`)
- [ ] Integration tests pass (`python tests/test_all_agents_integration.py`)

---

**System Status:** ✅ ALL AGENTS COMPLETE  
**Ready for:** Integration Testing & Proposal Generation  
**Next Milestone:** Export Services & API Layer

🚀 **Ready to generate research proposals!**

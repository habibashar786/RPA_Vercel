# Local Run Guide - Multi-Agentic Research Proposal System

This guide walks you through running the complete application locally before pushing to git.

## Prerequisites

- Python 3.11+ installed
- pip package manager
- Redis server (optional, for distributed state management)
- API keys for:
  - Anthropic Claude (primary LLM)
  - OpenAI GPT-4 (fallback)
  - Semantic Scholar API (optional)
  - arXiv API (free, no key required)

## Step 1: Environment Setup

### 1.1 Create Virtual Environment

```powershell
# PowerShell
python -m venv venv
venv\Scripts\Activate.ps1

# Or bash
python -m venv venv
source venv/Scripts/activate
```

### 1.2 Install Dependencies

**Option A: Fast Installation (Development)**
```powershell
pip install -r requirements-dev.txt
```

**Option B: Full Installation (Production)**
```powershell
pip install -r requirements.txt
```

### 1.3 Configure Environment

```powershell
# Copy example env file
Copy-Item .env.example .env

# Edit .env with your credentials
notepad .env
```

Add your API keys:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

## Step 2: Verify Agent Imports

This checks that all 11 agents load correctly:

```powershell
python verify_agents.py
```

**Expected Output:**
```
============================================================
AGENT IMPORT VERIFICATION
============================================================
[OK] BaseAgent                          - SUCCESS
[OK] LiteratureReviewAgent              - SUCCESS
[OK] IntroductionAgent                  - SUCCESS
[OK] ResearchMethodologyAgent           - SUCCESS
[OK] QualityAssuranceAgent              - SUCCESS
[OK] VisualizationAgent                 - SUCCESS
[OK] ReferenceCitationAgent             - SUCCESS
[OK] StructureFormattingAgent           - SUCCESS
[OK] FrontMatterAgent                   - SUCCESS
[OK] FinalAssemblyAgent                 - SUCCESS
[OK] RiskAssessmentAgent                - SUCCESS
[OK] MethodologyOptimizerAgent          - SUCCESS
[OK] CentralOrchestrator                - SUCCESS
[OK] TaskDecomposer                     - SUCCESS
[OK] WorkflowManager                    - SUCCESS
============================================================
RESULTS: 15 passed, 0 failed
============================================================

** ALL AGENTS IMPORTED SUCCESSFULLY! **
[OK] Project structure is correct
[OK] Ready for integration testing
```

## Step 3: Run Integration Tests

This verifies all agents can be instantiated, executed, and integrated:

```powershell
python tests/test_all_agents_integration.py
```

**Expected Output:**
```
================================================================================
MULTI-AGENTIC RESEARCH PROPOSAL SYSTEM - INTEGRATION TESTS
================================================================================

--------------------------------------------------------------------------------
TEST 1: AGENT INSTANTIATION
--------------------------------------------------------------------------------
[OK] LiteratureReviewAgent               - PASSED
[OK] IntroductionAgent                   - PASSED
[OK] ResearchMethodologyAgent            - PASSED
[OK] QualityAssuranceAgent               - PASSED
[OK] VisualizationAgent                  - PASSED
[OK] ReferenceCitationAgent              - PASSED
[OK] StructureFormattingAgent            - PASSED
[OK] FrontMatterAgent                    - PASSED
[OK] FinalAssemblyAgent                  - PASSED
[OK] RiskAssessmentAgent                 - PASSED
[OK] MethodologyOptimizerAgent           - PASSED

Result: 11 passed, 0 failed

--------------------------------------------------------------------------------
TEST 2: AGENT EXECUTION (WITH MOCK DATA)
--------------------------------------------------------------------------------
[OK] IntroductionAgent                   - READY TO EXECUTE
[OK] VisualizationAgent                  - READY TO EXECUTE
[OK] ReferenceCitationAgent              - READY TO EXECUTE
[OK] StructureFormattingAgent            - READY TO EXECUTE
[OK] FrontMatterAgent                    - READY TO EXECUTE
[OK] FinalAssemblyAgent                  - READY TO EXECUTE
[OK] RiskAssessmentAgent                 - READY TO EXECUTE

Result: 7 passed, 0 failed

--------------------------------------------------------------------------------
TEST 3: WORKFLOW INTEGRATION
--------------------------------------------------------------------------------

Subtest: Agent Dependencies
[OK] Agent handles partial dependencies

Subtest: Data Flow
[OK] Data flows correctly between agents

Subtest: Error Handling
[OK] Agent correctly rejects invalid input

Result: 3 passed, 0 failed

================================================================================
TEST SUMMARY
================================================================================
[OK]  PASSED    | Agent Instantiation            | 11/11 agents instantiated successfully
[OK]  PASSED    | Agent Execution                | 7/7 agents ready for execution
[OK]  PASSED    | Workflow Integration           | 3/3 workflow tests passed
================================================================================
OVERALL: 3/3 tests passed

** ALL TESTS PASSED! **

[OK] All 11 agents are working correctly
[OK] Workflow integration verified
[OK] System is ready for production use
================================================================================
```

## Step 4: Run Unit Tests

Run the example agent test to ensure test infrastructure works:

```powershell
pytest tests/test_example_agent.py -v
```

**Expected Output:**
```
============================= test session starts ==============================
platform win32 -- Python 3.11.9, pytest-7.4.3
collected 1 item

tests/test_example_agent.py::test_example_agent_process PASSED          [100%]

============================== 1 passed in 1.46s ===============================
```

## Step 5: Run All Tests with Coverage

Get detailed coverage metrics:

```powershell
pytest tests/ -v --cov=src --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

## Step 6: Check Code Quality

### Type Checking with mypy
```powershell
mypy src/ --ignore-missing-imports
```

### Code Formatting with black
```powershell
black src/ tests/
```

### Linting with pylint
```powershell
pylint src/agents/*.py --disable=all --enable=E,F
```

## Step 7: Manual System Test (Full Workflow)

Create a test script to run a complete proposal generation:

```powershell
# Create test_proposal_generation.py with:
# 1. Initialize CentralOrchestrator
# 2. Create AgentRequest with research topic
# 3. Run complete workflow
# 4. Save output to file
# 5. Verify proposal structure
```

**Topics to Test With:**
- "AI in Healthcare: Machine Learning for Disease Diagnosis"
- "Quantum Computing Applications in Drug Discovery"
- "Climate Change Impact on Marine Ecosystems"

## Step 8: API Server (When Ready)

```powershell
# Start FastAPI server (when api module is added)
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Then test endpoints:
```powershell
# Create proposal
Invoke-WebRequest -Uri "http://localhost:8000/api/proposals" `
  -Method POST `
  -ContentType "application/json" `
  -Body @{
    topic = "Your Research Topic"
    author = "Your Name"
  } | ConvertTo-Json

# Get proposal status
Invoke-WebRequest -Uri "http://localhost:8000/api/proposals/{workflow_id}" `
  -Method GET

# Get proposal output
Invoke-WebRequest -Uri "http://localhost:8000/api/proposals/{workflow_id}/output" `
  -Method GET
```

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution:** Ensure you're in the virtual environment and ran `pip install -r requirements-dev.txt`

### Issue: Redis connection error
**Solution:** Redis is optional. If not using distributed state, errors can be ignored or Redis can be installed:
```powershell
# Via Docker
docker run -d -p 6379:6379 redis

# Or install locally (Windows)
choco install redis
```

### Issue: API key not found
**Solution:** Check `.env` file contains valid keys with no quotes:
```
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Correct
ANTHROPIC_API_KEY="sk-ant-xxxxx"  # Incorrect (has quotes)
```

### Issue: Unicode encoding errors in output
**Solution:** Tests now use ASCII output. If still seeing errors, ensure UTF-8 encoding:
```powershell
# In PowerShell
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
```

## Validation Checklist

Before pushing to git, verify all of these pass:

- [ ] `python verify_agents.py` → All 15 imports successful
- [ ] `python tests/test_all_agents_integration.py` → All 3 tests pass
- [ ] `pytest tests/test_example_agent.py -v` → 1 passed
- [ ] `pytest tests/ --cov=src` → Coverage report generated
- [ ] All agents can handle mock data without errors
- [ ] No unhandled exceptions in logs
- [ ] Environment variables are set
- [ ] No sensitive data in code files
- [ ] All files use ASCII-safe output (no random emoji crashes)

## Success Criteria

✅ **System Ready for Git When:**
1. All 15 agents import without errors
2. Integration tests show 3/3 passing
3. No uncaught exceptions during test runs
4. Code structure follows documented patterns
5. All dependencies resolve cleanly
6. Documentation is accurate and complete

## Next Steps After Local Validation

Once all steps above pass:

1. Create a `git commit` with message: "Complete Phase 2: All agents working, tests passing"
2. Push to origin/main
3. Verify CI/CD pipeline triggers on GitHub
4. Monitor GitHub Actions for test results
5. Proceed to Phase 3: API Layer & Export Services

---

**Last Updated:** December 5, 2025  
**Status:** Ready for Local Testing ✅

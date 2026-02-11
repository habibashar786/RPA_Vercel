# Local Testing & Verification Guide

**Purpose**: Complete guide for running and testing the research proposal generation system locally before production deployment.

**Status**: Development Phase - Iterative Testing in Progress

---

## Quick Start: Verify Everything Works

### 1. Check Python & Virtual Environment (2 min)
```bash
cd C:\Users\ashar\Documents\rpa_claude_desktop

# Verify Python version
python --version  # Should be 3.11+

# Verify virtual environment active
# (you should see venv in your terminal prompt)
```

### 2. Run Quick Tests (5 min)
```bash
# Test 1: Check imports
python -c "from src.agents.orchestrator.central_orchestrator import CentralOrchestrator; print('✓ Imports OK')"

# Test 2: Run integration tests
python tests/test_all_agents_integration.py

# Test 3: Run example agent test
python -m pytest tests/test_example_agent.py -v
```

**Expected Result**: All 3/3 tests should PASS

---

## Comprehensive Local Testing

### Phase 1: Setup & Verification (15 min)

#### 1.1 Check Dependencies
```bash
# Verify all required packages
pip list | findstr "anthropic langchain redis pydantic pytest"

# Output should show:
# anthropic
# langchain  
# redis
# pydantic
# pytest
```

#### 1.2 Verify Redis Connection
```bash
# Check if Redis is running (should already be configured)
python -c "from src.core.state_manager import StateManager; sm = StateManager(); print('✓ Redis Connected')"
```

#### 1.3 Check Environment Configuration
```bash
# Verify config loads
python -c "from src.core.config import load_config; cfg = load_config(); print('✓ Config Loaded')"
```

---

### Phase 2: Unit & Integration Testing (20 min)

#### 2.1 Run All Tests with Coverage
```bash
# Run all tests with coverage report
pytest -v --cov=src --cov-report=html

# This generates:
# - Console output with test results
# - HTML report in htmlcov/index.html
# - Coverage metrics for all modules
```

#### 2.2 Test Individual Components
```bash
# Test just agent instantiation
python -m pytest tests/test_all_agents_integration.py::IntegrationTester.test_agent_instantiation -v

# Test just agent execution
python -m pytest tests/test_all_agents_integration.py::IntegrationTester.test_agent_execution -v

# Test just workflow integration
python -m pytest tests/test_all_agents_integration.py::IntegrationTester.test_workflow_integration -v
```

---

### Phase 3: Agent Testing (30 min)

#### 3.1 Test Individual Agents
```bash
# Python script to test each agent

import asyncio
from src.agents.content_generation.introduction_agent import IntroductionAgent
from src.models.agent_messages import AgentRequest

async def test_introduction_agent():
    agent = IntroductionAgent()
    
    # Test data
    request = AgentRequest(
        task_id="test_intro",
        agent_name="introduction_agent",
        action="execute",
        input_data={
            "topic": "AI in Healthcare",
            "key_points": ["ML applications", "Diagnosis improvement", "Patient outcomes"]
        }
    )
    
    # Test validation
    is_valid = await agent.validate_input(request.input_data)
    print(f"Validation: {is_valid}")
    
    # Note: execution requires LLM setup
    
asyncio.run(test_introduction_agent())
```

Save as `test_agent_manual.py` and run: `python test_agent_manual.py`

#### 3.2 Test MCP Servers
```bash
# Test Arxiv MCP
python -c "
from src.mcp_servers.arxiv_mcp import ArxivMCP
arxiv = ArxivMCP()
results = asyncio.run(arxiv.search('machine learning healthcare'))
print(f'Arxiv results: {len(results)} papers found')
"

# Test Semantic Scholar MCP
python -c "
from src.mcp_servers.semantic_scholar_mcp import SemanticScholarMCP
ss = SemanticScholarMCP()
results = asyncio.run(ss.search('deep learning diagnosis'))
print(f'Semantic Scholar results: {len(results)} papers found')
"
```

---

### Phase 4: Full Workflow Testing (60+ min)

#### 4.1 Test End-to-End Workflow
```bash
# Run complete system with test topic
python scripts/run_system.py --topic "Machine Learning for Disease Diagnosis in Healthcare"

# Monitor output for:
# - All 11 agents executing
# - State being saved to Redis
# - No errors or exceptions
# - Final proposal structure generated
```

#### 4.2 Monitor Execution
```bash
# In a separate terminal, watch Redis state
python -c "
import redis
r = redis.Redis(decode_responses=True)
import time

for i in range(30):
    keys = r.keys('workflow:*')
    print(f'[{i}] Workflows in Redis: {len(keys)}')
    time.sleep(1)
"
```

#### 4.3 Check Output Quality
```bash
# After workflow completes, check generated proposal
python -c "
from src.core.state_manager import StateManager
sm = StateManager()
keys = sm.redis_client.keys('task_output_*')
for key in keys[:5]:  # Show first 5 outputs
    value = sm.redis_client.get(key)
    print(f'{key}: {value[:100]}...')  # Show first 100 chars
"
```

---

### Phase 5: API Layer Testing (30 min)

#### 5.1 Start API Server
```bash
# Terminal 1: Start the API
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

#### 5.2 Test Health Endpoint
```bash
# Terminal 2: Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-12-05T..."}
```

#### 5.3 Test Proposal Generation Endpoint
```bash
# Test creating a new proposal
curl -X POST http://localhost:8000/proposals/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Quantum Computing Applications",
    "author": "Test User",
    "institution": "Test University"
  }'

# Expected response (after 1-5 min depending on LLM):
# {
#   "proposal_id": "...",
#   "status": "generating",
#   "topic": "Quantum Computing Applications",
#   ...
# }
```

#### 5.4 Check Proposal Status
```bash
# Get proposal status
curl http://localhost:8000/proposals/{proposal_id}

# Expected response:
# {
#   "proposal_id": "...",
#   "status": "completed",
#   "sections": {...}
# }
```

---

### Phase 6: Performance Testing (45 min)

#### 6.1 Memory Profiling
```bash
# Monitor memory usage during workflow
python -c "
import psutil
import asyncio
from src.agents.orchestrator.central_orchestrator import CentralOrchestrator

process = psutil.Process()

async def test_memory():
    orchestrator = CentralOrchestrator()
    initial_mem = process.memory_info().rss / 1024 / 1024  # MB
    
    # Run workflow
    proposal = await orchestrator.generate_proposal({
        'topic': 'Test for memory profiling'
    })
    
    final_mem = process.memory_info().rss / 1024 / 1024
    print(f'Memory used: {final_mem - initial_mem:.2f} MB')

asyncio.run(test_memory())
"
```

#### 6.2 Execution Time Profiling
```bash
# Measure total execution time
import time

start = time.time()
exit_code = asyncio.run(main())  # from scripts/run_system.py
elapsed = time.time() - start

print(f"Total execution time: {elapsed:.2f} seconds")
```

#### 6.3 Concurrent Request Testing
```bash
# Test multiple concurrent proposals via API
import asyncio
import aiohttp

async def test_concurrent():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(3):
            task = session.post(
                'http://localhost:8000/proposals/generate',
                json={'topic': f'Test Topic {i}'}
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        print(f"Submitted {len(results)} concurrent requests")

asyncio.run(test_concurrent())
```

---

### Phase 7: Error Handling Testing (30 min)

#### 7.1 Test Invalid Input
```bash
# Try invalid topic
python scripts/run_system.py --topic ""

# Expected: Validation error, clear error message
```

#### 7.2 Test Missing Dependencies
```bash
# Try simulating missing dependency
python -c "
from src.agents.document_structure.final_assembly_agent import FinalAssemblyAgent
import asyncio

async def test():
    agent = FinalAssemblyAgent()
    # Missing all required inputs
    is_valid = await agent.validate_input({})
    print(f'Validation result: {is_valid}')  # Should be False

asyncio.run(test())
"
```

#### 7.3 Test API Error Handling
```bash
# Test with invalid JSON
curl -X POST http://localhost:8000/proposals/generate \
  -H "Content-Type: application/json" \
  -d 'invalid json'

# Expected: 422 Unprocessable Entity with error details
```

---

## Testing Checklist

### Before Local Commit
- [ ] All imports resolve without errors
- [ ] 3/3 integration tests pass
- [ ] Example agent test passes
- [ ] No syntax errors detected
- [ ] Coverage report generated (check htmlcov/index.html)

### Before Feature Tests
- [ ] E2E workflow executes start-to-finish
- [ ] All 11 agents execute successfully
- [ ] Proposal output has all required sections
- [ ] State saved to Redis correctly
- [ ] No uncaught exceptions

### Before Performance Testing
- [ ] API server starts without errors
- [ ] Health endpoint responds
- [ ] Proposal generation endpoint works
- [ ] Status checking works
- [ ] Error handling works

### Before Production
- [ ] Memory usage acceptable (<500 MB)
- [ ] Execution time acceptable (<5 min)
- [ ] Concurrent requests handled (3+)
- [ ] Error scenarios handled gracefully
- [ ] All edge cases tested

---

## Troubleshooting

### Issue: Import Error - Module Not Found
```bash
# Solution:
python -m pip install -r requirements.txt --upgrade
# Then retry
```

### Issue: Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping
# Should respond: PONG

# If not running, start it:
redis-server
```

### Issue: LLM API Error
```bash
# Check API keys in .env file
cat .env | grep -i "key\|token"

# Verify keys are not expired
# Test API connection: python -c "from src.core.llm_provider import LLMProvider; LLMProvider().test_connection()"
```

### Issue: Tests Fail Randomly
```bash
# Could be async timing issue
# Solution: Increase timeout
pytest -v --timeout=30

# Or run tests sequentially instead of parallel
pytest -v -n 0
```

### Issue: Memory Leaks
```bash
# Monitor memory during long runs
import psutil
import gc

process = psutil.Process()
for i in range(10):
    gc.collect()
    mem = process.memory_info().rss / 1024 / 1024
    print(f"Iteration {i}: {mem:.2f} MB")
    time.sleep(1)
```

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Agent Instantiation | <100ms each | ✓ |
| Workflow Initialization | <1s | ? |
| Single Agent Execution | <10s | ? |
| Full Workflow (11 agents) | <5 min | ? |
| Proposal Generation | <10 min | ? |
| API Response Time | <100ms | ? |
| Memory Usage | <500 MB | ? |
| Concurrent Workflows | 3+ | ? |

---

## Logging & Debugging

### Enable Debug Logging
```bash
# Set log level to DEBUG in environment
set LOG_LEVEL=DEBUG
python scripts/run_system.py --topic "Test"

# Or in code:
from src.core.config import load_config
config = load_config()
config['log_level'] = 'DEBUG'
```

### View Logs
```bash
# Logs are written to:
# - Console (INFO and above)
# - logs/app.log (all levels)

tail -f logs/app.log
```

### Profile Code Execution
```bash
# Use Python profiler
python -m cProfile -s cumtime scripts/run_system.py --topic "Test" > profile.txt
cat profile.txt
```

---

## Next Steps After Verification

1. ✅ Run all quick tests (5 min)
2. ✅ Run integration tests (5 min)
3. 🔄 Run E2E workflow (60 min)
4. 🔄 Test each agent individually (30 min)
5. 🔄 Test API endpoints (30 min)
6. 🔄 Performance testing (45 min)
7. 🔄 Error handling (30 min)
8. ⏳ Documentation review
9. ⏳ Final QA sign-off
10. ⏳ Git push & CI/CD

---

**Last Updated**: 2024-12-05  
**Status**: Ready for local testing  
**Next Phase**: E2E workflow execution  
**Git Commit**: Hold until all quality checks pass

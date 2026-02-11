# Testing Guide

## Running the Tests

### Prerequisites

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set Up Environment:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. **Start Redis (Required for State Manager):**
```bash
# Option 1: Docker
docker run -d -p 6379:6379 redis:latest

# Option 2: Local Redis
redis-server
```

### Run Test Suite

```bash
# From project root
python tests/test_orchestrator_system.py
```

### Test Coverage

The test suite includes 10 tests:

1. **Import Modules** - Verify all modules load correctly
2. **TaskDecomposer** - Test task graph creation and DAG validation
3. **Configuration Loading** - Test YAML config loading
4. **LLM Provider** - Test LLM initialization and simple generation
5. **State Manager** - Test Redis workflows and shared data
6. **MCP Servers** - Test MCP server initialization
7. **Literature Review Agent** - Test agent creation and validation
8. **Central Orchestrator** - Test orchestrator setup and agent registration
9. **Task Graph Validation** - Test dependency resolution
10. **End-to-End Dry Run** - Test complete workflow without API calls

### Expected Output

```
TEST SUMMARY
============================================================
✅ Test 1: Import Modules: PASSED
✅ Test 2: TaskDecomposer: PASSED
✅ Test 3: Configuration Loading: PASSED
✅ Test 4: LLM Provider: PASSED (or skipped if no API key)
✅ Test 5: State Manager: PASSED
✅ Test 6: MCP Servers: PASSED
✅ Test 7: Literature Review Agent: PASSED
✅ Test 8: Central Orchestrator: PASSED
✅ Test 9: Task Graph Validation: PASSED
✅ Test 10: End-to-End Dry Run: PASSED

Total: 10 tests
Passed: 10 (100.0%)
Failed: 0 (0.0%)
============================================================
```

### Troubleshooting

**Issue:** Redis connection error
```
Solution: Make sure Redis is running on port 6379
```

**Issue:** Import errors
```
Solution: Install dependencies with pip install -r requirements.txt
```

**Issue:** API key warnings
```
Solution: Add ANTHROPIC_API_KEY to .env file (or tests will skip LLM tests)
```

### Logs

Test logs are saved to:
```
logs/test_{timestamp}.log
```

### Next Steps

After tests pass:
1. Try a full proposal generation (requires all API keys)
2. Build remaining agents (Introduction, Methodology, QA)
3. Create integration tests
4. Set up CI/CD pipeline

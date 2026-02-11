@echo off
REM Setup script for Multi-Agentic Research Proposal System (Windows)

echo ==================================
echo Setup: Research Proposal System
echo ==================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

echo Step 1: Installing minimal dependencies...
pip install loguru==0.7.2 pydantic==2.8.2 python-dotenv==1.0.1 pyyaml==6.0.2

echo.
echo Step 2: Installing LLM providers...
pip install anthropic==0.34.2 openai==1.42.0

echo.
echo Step 3: Installing utilities...
pip install httpx==0.27.2 requests==2.32.3 redis==5.0.8

echo.
echo Step 4: Installing academic APIs...
pip install semanticscholar==0.8.4 arxiv==2.1.3

echo.
echo Step 5: Installing testing framework...
pip install pytest==8.3.2 pytest-asyncio==0.24.0

echo.
echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo Next steps:
echo 1. Configure .env file with API keys
echo 2. Start Redis: docker run -d -p 6379:6379 redis:latest
echo 3. Run tests: python tests/test_all_agents_integration.py
echo.

pause

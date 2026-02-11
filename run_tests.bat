@echo off
REM ============================================================
REM RPA Claude Desktop - Complete Sequential Test Suite
REM Follows DOCUMENTATION.md - All Sequential Steps
REM ============================================================
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo RPA CLAUDE DESKTOP - COMPLETE SEQUENTIAL TEST SUITE
echo Date: %date% %time%
echo ============================================================
echo.

cd /d "%~dp0"

REM Create log file
set LOGFILE=test_results_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOGFILE=%LOGFILE: =0%

echo Log file: %LOGFILE%
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then run: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set mock mode environment variables
set LLM_MOCK=1
set USE_INMEMORY_STATE=1

echo [INFO] Environment Variables Set:
echo   LLM_MOCK=%LLM_MOCK%
echo   USE_INMEMORY_STATE=%USE_INMEMORY_STATE%
echo.

REM ============================================================
echo ============================================================
echo STEP 1: Running Sequential Tests (5 Phases)
echo ============================================================
echo.

python run_sequential_tests.py 2>&1 | tee -a %LOGFILE%
set STEP1_RESULT=%errorlevel%

if %STEP1_RESULT%==0 (
    echo.
    echo [OK] Sequential Tests PASSED
) else (
    echo.
    echo [WARN] Sequential Tests had issues - check output above
)

REM ============================================================
echo.
echo ============================================================
echo STEP 2: Running Mock E2E Test (All 11 Agents)
echo ============================================================
echo.

python test_e2e_mock.py 2>&1 | tee -a %LOGFILE%
set STEP2_RESULT=%errorlevel%

if %STEP2_RESULT%==0 (
    echo.
    echo [OK] Mock E2E Test PASSED
) else (
    echo.
    echo [WARN] Mock E2E Test had issues - check output above
)

REM ============================================================
echo.
echo ============================================================
echo STEP 3: Running Integration Tests
echo ============================================================
echo.

python tests\test_all_agents_integration.py 2>&1 | tee -a %LOGFILE%
set STEP3_RESULT=%errorlevel%

if %STEP3_RESULT%==0 (
    echo.
    echo [OK] Integration Tests PASSED
) else (
    echo.
    echo [WARN] Integration Tests had issues - check output above
)

REM ============================================================
echo.
echo ============================================================
echo STEP 4: Running Pytest Suite
echo ============================================================
echo.

pytest tests/ -v --tb=short 2>&1 | tee -a %LOGFILE%
set STEP4_RESULT=%errorlevel%

if %STEP4_RESULT%==0 (
    echo.
    echo [OK] Pytest Suite PASSED
) else (
    echo.
    echo [WARN] Pytest Suite had issues - check output above
)

REM ============================================================
echo.
echo ============================================================
echo STEP 5: Verifying Output Structure
echo ============================================================
echo.

python verify_output.py 2>&1 | tee -a %LOGFILE%

REM ============================================================
echo.
echo ============================================================
echo TEST SUITE SUMMARY
echo ============================================================
echo.
echo Step 1 - Sequential Tests:    %STEP1_RESULT%
echo Step 2 - Mock E2E Test:       %STEP2_RESULT%
echo Step 3 - Integration Tests:   %STEP3_RESULT%
echo Step 4 - Pytest Suite:        %STEP4_RESULT%
echo.
echo Log saved to: %LOGFILE%
echo.

REM Calculate overall result
set /a TOTAL_FAILURES=%STEP1_RESULT%+%STEP2_RESULT%+%STEP3_RESULT%+%STEP4_RESULT%

if %TOTAL_FAILURES%==0 (
    echo ============================================================
    echo [SUCCESS] ALL TESTS PASSED!
    echo ============================================================
    echo.
    echo Next Steps:
    echo   1. Run with real LLM:
    echo      set LLM_MOCK=0
    echo      python scripts\run_system.py --topic "Your Topic"
    echo.
    echo   2. Start API server:
    echo      uvicorn src.api.main:app --reload --port 8001
    echo.
) else (
    echo ============================================================
    echo [WARNING] Some tests had issues - review output above
    echo ============================================================
)

echo.
pause

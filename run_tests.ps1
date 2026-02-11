# ============================================================
# RPA Claude Desktop - Complete Sequential Test Suite
# PowerShell Version - Follows DOCUMENTATION.md
# ============================================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "RPA CLAUDE DESKTOP - COMPLETE SEQUENTIAL TEST SUITE" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Create log file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "test_results_$timestamp.log"

Write-Host "Log file: $logFile" -ForegroundColor Yellow
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv"
    Write-Host "Then run: .venv\Scripts\pip install -r requirements.txt"
    exit 1
}

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Set mock mode environment variables
$env:LLM_MOCK = "1"
$env:USE_INMEMORY_STATE = "1"

Write-Host "[INFO] Environment Variables Set:" -ForegroundColor Green
Write-Host "  LLM_MOCK=$env:LLM_MOCK"
Write-Host "  USE_INMEMORY_STATE=$env:USE_INMEMORY_STATE"
Write-Host ""

# Function to run test and capture result
function Run-Test {
    param (
        [string]$Name,
        [string]$Command
    )
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Name -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $output = & python -c "import sys; sys.exit(0)" 2>&1  # Dummy to ensure python works
    
    try {
        $result = Invoke-Expression $Command 2>&1 | Tee-Object -Append -FilePath $logFile
        $result | ForEach-Object { Write-Host $_ }
        $exitCode = $LASTEXITCODE
    }
    catch {
        Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
        $exitCode = 1
    }
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "[OK] $Name PASSED" -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "[WARN] $Name had issues - check output above" -ForegroundColor Yellow
    }
    
    Write-Host ""
    return $exitCode
}

# ============================================================
# STEP 1: Sequential Tests
# ============================================================
Write-Host ""
$step1 = 0
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "STEP 1: Running Sequential Tests (5 Phases)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

python run_sequential_tests.py 2>&1 | Tee-Object -Append -FilePath $logFile
$step1 = $LASTEXITCODE

if ($step1 -eq 0) {
    Write-Host "[OK] Sequential Tests PASSED" -ForegroundColor Green
} else {
    Write-Host "[WARN] Sequential Tests had issues" -ForegroundColor Yellow
}

# ============================================================
# STEP 2: Mock E2E Test
# ============================================================
Write-Host ""
$step2 = 0
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "STEP 2: Running Mock E2E Test (All 11 Agents)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

python test_e2e_mock.py 2>&1 | Tee-Object -Append -FilePath $logFile
$step2 = $LASTEXITCODE

if ($step2 -eq 0) {
    Write-Host "[OK] Mock E2E Test PASSED" -ForegroundColor Green
} else {
    Write-Host "[WARN] Mock E2E Test had issues" -ForegroundColor Yellow
}

# ============================================================
# STEP 3: Integration Tests
# ============================================================
Write-Host ""
$step3 = 0
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "STEP 3: Running Integration Tests" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

python tests\test_all_agents_integration.py 2>&1 | Tee-Object -Append -FilePath $logFile
$step3 = $LASTEXITCODE

if ($step3 -eq 0) {
    Write-Host "[OK] Integration Tests PASSED" -ForegroundColor Green
} else {
    Write-Host "[WARN] Integration Tests had issues" -ForegroundColor Yellow
}

# ============================================================
# STEP 4: Pytest Suite
# ============================================================
Write-Host ""
$step4 = 0
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "STEP 4: Running Pytest Suite" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

pytest tests/ -v --tb=short 2>&1 | Tee-Object -Append -FilePath $logFile
$step4 = $LASTEXITCODE

if ($step4 -eq 0) {
    Write-Host "[OK] Pytest Suite PASSED" -ForegroundColor Green
} else {
    Write-Host "[WARN] Pytest Suite had issues" -ForegroundColor Yellow
}

# ============================================================
# STEP 5: Verify Output
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "STEP 5: Verifying Output Structure" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

python verify_output.py 2>&1 | Tee-Object -Append -FilePath $logFile

# ============================================================
# SUMMARY
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TEST SUITE SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Step 1 - Sequential Tests:    $step1"
Write-Host "Step 2 - Mock E2E Test:       $step2"
Write-Host "Step 3 - Integration Tests:   $step3"
Write-Host "Step 4 - Pytest Suite:        $step4"
Write-Host ""
Write-Host "Log saved to: $logFile" -ForegroundColor Yellow
Write-Host ""

$totalFailures = $step1 + $step2 + $step3 + $step4

if ($totalFailures -eq 0) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "[SUCCESS] ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Run with real LLM:"
    Write-Host '     $env:LLM_MOCK="0"'
    Write-Host '     python scripts\run_system.py --topic "Your Topic"'
    Write-Host ""
    Write-Host "  2. Start API server:"
    Write-Host "     uvicorn src.api.main:app --reload --port 8001"
    Write-Host ""
} else {
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "[WARNING] Some tests had issues - review output above" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

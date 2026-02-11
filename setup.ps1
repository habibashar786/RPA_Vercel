# ============================================================
# RPA Claude Desktop - Quick Setup Script
# Run this to install dependencies and fix issues
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "RPA CLAUDE DESKTOP - QUICK SETUP" -ForegroundColor Cyan  
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "[INFO] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install minimal requirements first (fast)
Write-Host "[INFO] Installing minimal requirements..." -ForegroundColor Yellow
pip install -r requirements-minimal.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install minimal requirements" -ForegroundColor Red
    exit 1
}

# Verify key packages
Write-Host ""
Write-Host "[INFO] Verifying installed packages..." -ForegroundColor Yellow
$packages = @("pydantic", "pyyaml", "httpx", "redis", "anthropic", "openai", "fastapi", "pytest")

foreach ($pkg in $packages) {
    $result = python -c "import $pkg; print(f'$pkg: OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $pkg" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $pkg" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run tests: .\run_tests.ps1"
Write-Host "  2. Or run: python run_sequential_tests.py"
Write-Host ""

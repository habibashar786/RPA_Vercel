# ResearchAI - Start Servers Script
# Run this script to start both backend and frontend servers

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ResearchAI - Starting Servers" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path ".\src\api\main.py")) {
    Write-Host "Error: Please run this script from the rpa_claude_desktop directory" -ForegroundColor Red
    exit 1
}

# Create logs directory if it doesn't exist
if (-not (Test-Path ".\logs")) {
    New-Item -ItemType Directory -Path ".\logs" | Out-Null
}

# Create data/outputs directory if it doesn't exist
if (-not (Test-Path ".\data\outputs")) {
    New-Item -ItemType Directory -Path ".\data\outputs" -Force | Out-Null
}

Write-Host "[1/3] Activating Python virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "[2/3] Starting Backend Server (Port 8001)..." -ForegroundColor Yellow
Write-Host "       URL: http://localhost:8001" -ForegroundColor Gray
Write-Host "       Health: http://localhost:8001/health" -ForegroundColor Gray
Write-Host "       Docs: http://localhost:8001/docs" -ForegroundColor Gray
Write-Host ""

# Start backend in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; Write-Host 'Starting Backend...' -ForegroundColor Green; uvicorn src.api.main:app --reload --port 8001 --host 0.0.0.0"

# Wait for backend to start
Write-Host "       Waiting for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host "[3/3] Starting Frontend Server (Port 3000)..." -ForegroundColor Yellow
Write-Host "       URL: http://localhost:3000" -ForegroundColor Gray
Write-Host "       Dashboard: http://localhost:3000/dashboard" -ForegroundColor Gray
Write-Host ""

# Check if frontend directory exists
if (Test-Path ".\frontend") {
    # Start frontend in a new PowerShell window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; Write-Host 'Starting Frontend...' -ForegroundColor Green; npm run dev"
} else {
    Write-Host "Warning: Frontend directory not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Servers Starting..." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8001" -ForegroundColor White
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8001/docs" -ForegroundColor White
Write-Host ""
Write-Host "Test Endpoints:" -ForegroundColor Gray
Write-Host "  - LLM Test:      http://localhost:8001/api/test/llm" -ForegroundColor Gray
Write-Host "  - Academic Test: http://localhost:8001/api/test/academic-search" -ForegroundColor Gray
Write-Host "  - Health Check:  http://localhost:8001/health" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop servers" -ForegroundColor Yellow

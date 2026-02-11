#!/usr/bin/env pwsh
# Start backend with environment variables

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Research Proposal Backend..." -ForegroundColor Cyan
Write-Host "Setting environment variables..." -ForegroundColor Yellow

$env:LLM_MOCK = '1'
$env:USE_INMEMORY_STATE = '1'

Write-Host "✅ LLM_MOCK = 1" -ForegroundColor Green
Write-Host "✅ USE_INMEMORY_STATE = 1" -ForegroundColor Green

Write-Host "`nActivating Python virtual environment..." -ForegroundColor Yellow
cd C:\Users\ashar\Documents\rpa_claude_desktop
& .\.venv\Scripts\Activate.ps1

Write-Host ✅ Virtual environment activated -ForegroundColor Green
Write-Host "Starting Uvicorn on port 8001..." -ForegroundColor Yellow

python.exe -m uvicorn src.api.main:app --port 8001 --host 127.0.0.1 --log-level info

Write-Host "✅ Backend running!" -ForegroundColor Green
Write-Host "Visit: http://localhost:8001/health" -ForegroundColor Cyan

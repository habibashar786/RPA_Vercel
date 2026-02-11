#!/usr/bin/env pwsh
# Start backend with real LLM provider (no mock)

$ErrorActionPreference = "Stop"

function Load-DotEnv {
  param($Path)
  if (-not (Test-Path $Path)) { return }
  Get-Content $Path | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $kv = $_ -split '=', 2
    if ($kv.Length -eq 2) {
      $key = $kv[0].Trim()
      $val = $kv[1].Trim()
      if (-not [string]::IsNullOrWhiteSpace($key) -and -not (Test-Path Env:$key)) {
        Set-Item -Path Env:$key -Value $val
      }
    }
  }
}

Write-Host "🚀 Starting Research Proposal Backend (real LLM)..." -ForegroundColor Cyan

# Load .env if present to pick up keys
$dotenvPath = Join-Path $PSScriptRoot ".env"
Load-DotEnv -Path $dotenvPath

# Validate API keys
if (-not $env:ANTHROPIC_API_KEY -and -not $env:OPENAI_API_KEY) {
  Write-Host "❌ Missing ANTHROPIC_API_KEY and OPENAI_API_KEY. Set at least one before running." -ForegroundColor Red
  exit 1
}

# Basic runtime settings
$hostAddress = "127.0.0.1"
$port = 8001
$useInMemory = $env:USE_INMEMORY_STATE
if ([string]::IsNullOrWhiteSpace($useInMemory)) { $useInMemory = "1" }
$env:USE_INMEMORY_STATE = $useInMemory
$env:LLM_MOCK = "0"
# Force current Claude Sonnet model to avoid 404s
$env:DEFAULT_MODEL = "gpt-3.5-turbo"
$env:DEFAULT_LLM_PROVIDER = "openai"

Write-Host "✅ LLM_MOCK = 0 (real provider)" -ForegroundColor Green
Write-Host "✅ USE_INMEMORY_STATE = $useInMemory" -ForegroundColor Green
Write-Host "✅ DEFAULT_MODEL = $($env:DEFAULT_MODEL)" -ForegroundColor Green
Write-Host "✅ DEFAULT_LLM_PROVIDER = $($env:DEFAULT_LLM_PROVIDER)" -ForegroundColor Green

# Resolve venv python
$venvPython = Join-Path $PSScriptRoot ".venv" | Join-Path -ChildPath "Scripts" | Join-Path -ChildPath "python.exe"
if (-not (Test-Path $venvPython)) {
  Write-Host "⚠️  Could not find venv python at $venvPython; falling back to system python" -ForegroundColor Yellow
  $venvPython = "python"
}

# Change to repo root
Push-Location $PSScriptRoot

Write-Host ("Starting Uvicorn on http://{0}:{1} ..." -f $hostAddress, $port) -ForegroundColor Yellow
& $venvPython -m uvicorn src.api.main:app --host $hostAddress --port $port --log-level info

Pop-Location

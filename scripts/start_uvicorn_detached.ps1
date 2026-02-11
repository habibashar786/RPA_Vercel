# Start uvicorn in a detached process with mock LLM and in-memory state
param(
    [string]$ApiHost = '127.0.0.1',
    [int]$Port = 8001
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$logsDir = Join-Path $projectRoot '..\logs' | Resolve-Path -Relative -ErrorAction SilentlyContinue
if (-not (Test-Path "$projectRoot\..\logs")) { New-Item -Path "$projectRoot\..\logs" -ItemType Directory | Out-Null }
$logFile = Join-Path "$projectRoot\..\logs" 'uvicorn.log'

$env:PYTHONPATH = '.'
$env:USE_INMEMORY_STATE = '1'
$env:LLM_MOCK = '1'

$python = (Get-Command python).Source
$arguments = "-m uvicorn src.api.main:app --host $ApiHost --port $Port"

Write-Output "Starting uvicorn as detached process (host=$ApiHost port=$Port). Logging to: $logFile"

$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $python
$startInfo.Arguments = $arguments
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $startInfo
$null = $process.Start()

# Async copy streams to log file
$stdout = $process.StandardOutput
$stderr = $process.StandardError

Start-Job -ScriptBlock {
    param($outStream, $errStream, $logFile)
    while (-not $outStream.EndOfStream) {
        $line = $outStream.ReadLine()
        Add-Content -Path $logFile -Value $line
    }
    while (-not $errStream.EndOfStream) {
        $line = $errStream.ReadLine()
        Add-Content -Path $logFile -Value $line
    }
} -ArgumentList ($stdout, $stderr, $logFile) | Out-Null

Write-Output "Started pid=$($process.Id)"
Write-Output "Log file: $logFile"
Write-Output "Use 'Get-Content -Wait -Tail 50 $logFile' to tail logs."
@echo off
setlocal
cd /d C:\Users\ashar\Documents\rpa_claude_desktop
call .\.venv\Scripts\activate.bat
set LLM_MOCK=1
set USE_INMEMORY_STATE=1
start "ResearchAI Backend" cmd /k "uvicorn src.api.main:app --host 127.0.0.1 --port 8001 --log-level info"

#!/usr/bin/env python
"""Simple backend runner that stays alive."""
import os
import sys
import subprocess

# Set mock mode
os.environ['LLM_MOCK'] = '1'

# Run uvicorn in a subprocess
proc = subprocess.Popen([
    sys.executable, '-m', 'uvicorn',
    'src.api.main:app',
    '--host', '127.0.0.1',
    '--port', '8000',
    '--log-level', 'info'
], cwd=os.path.dirname(os.path.abspath(__file__)))

try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
    proc.wait()

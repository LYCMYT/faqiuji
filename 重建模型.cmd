@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First install Python 3.12 and dependencies. See README_DELIVERY.md.
  exit /b 1
)
".venv\Scripts\python.exe" tools\rebuild.py
pause

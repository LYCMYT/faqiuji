@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tools\serve_viewer.py --open
) else (
  py -3 tools\serve_viewer.py --open
)

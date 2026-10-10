@echo off
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" scripts\start_app.py
) else (
    python scripts\start_app.py
)
pause

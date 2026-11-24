@echo off
cd /d "%~dp0"
if exist "..\runtime\python.exe" (
    "..\runtime\python.exe" run.py
    goto end
)
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py
    goto end
)
echo Installing this project's dependencies into .venv...
python --version
if errorlevel 1 goto missing
python -m venv .venv
if errorlevel 1 goto missing
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto end
".venv\Scripts\python.exe" run.py
goto end
:missing
echo Python 3.11+ is required for the source ZIP. Use the Windows-ready suite for a bundled runtime.
:end
pause

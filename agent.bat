@echo off
setlocal
:: Store the directory where this batch file is located
set "AGENT_DIR=%~dp0"

:: Force UTF-8 encoding so emojis (e.g. 🤖) don't crash the console
set PYTHONIOENCODING=utf-8

:: Start the agent using the virtual environment's Python, passing all arguments
"%AGENT_DIR%\..\.venv\Scripts\python.exe" "%AGENT_DIR%\main.py" --cwd "%CD%" %*

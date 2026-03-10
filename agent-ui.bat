@echo off
setlocal
:: Store the directory where this batch file is located
set "AGENT_DIR=%~dp0"

:: Force UTF-8 encoding
set PYTHONIOENCODING=utf-8

:: Start the streamlit app using the virtual environment's Python, passing all arguments
"%AGENT_DIR%\..\.venv\Scripts\python.exe" -m streamlit run "%AGENT_DIR%\app_ui.py" %*

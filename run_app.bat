@echo off
title EventDhara AI Image Metadata Studio
color 0B
echo =======================================================
echo     EventDhara AI Image Metadata Studio Launcher
echo =======================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please install Python 3.10+ and make sure to check "Add Python to PATH".
    pause
    exit /b 1
)

:: Ensure dependencies are installed
echo [1/2] Checking required Python packages...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Encountered an issue checking packages. Proceeding anyway...
)

:: Launch Streamlit
echo [2/2] Launching EventDhara Streamlit Studio...
echo.
echo Application will open in your default browser at http://localhost:8501
echo Press Ctrl+C in this terminal window to stop the server.
echo.
python -m streamlit run app.py

pause

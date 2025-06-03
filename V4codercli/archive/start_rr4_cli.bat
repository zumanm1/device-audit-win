@echo off
REM RR4 CLI Interactive Startup Manager - Windows Launcher
REM Cross-platform Python startup script for Windows 10/11

echo.
echo 🚀 Starting RR4 CLI Interactive Startup Manager (Windows)...
echo ==============================================================

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org and try again
    echo.
    pause
    exit /b 1
)

REM Check if the startup script exists
if not exist "start_rr4_cli.py" (
    echo ❌ ERROR: start_rr4_cli.py not found
    echo Please ensure you're in the V4codercli directory
    echo.
    pause
    exit /b 1
)

REM Run the interactive startup manager
python start_rr4_cli.py

echo.
echo 👋 Thank you for using RR4 CLI!
pause 
@echo off
REM V4CODERCLI - Cross-Platform Network State Collector CLI
REM Windows Startup Script
REM Compatible with Windows 10/11

echo.
echo ===============================================================================
echo                   V4CODERCLI - Network State Collector CLI
echo                          Windows Startup Script v1.0.1
echo ===============================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python version: %PYTHON_VERSION%

REM Change to script directory
cd /d "%~dp0"
echo ✅ Working directory: %CD%

REM Check if requirements are installed
echo.
echo Checking dependencies...
python -c "import click, paramiko, netmiko, nornir" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Some dependencies are missing. Installing requirements...
    python -m pip install -r requirements-minimal.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ All dependencies are available
)

REM Check for configuration files
if not exist ".env-t" if not exist "rr4-complete-enchanced-v4-cli.env-t" (
    echo.
    echo ⚠️  Configuration file not found
    echo Creating default configuration...
    copy "rr4-complete-enchanced-v4-cli.env-t" ".env-t" >nul 2>&1
)

echo.
echo ===============================================================================
echo                              STARTUP OPTIONS
echo ===============================================================================
echo.
echo 1. First-time setup wizard (Recommended for new users)
echo 2. Interactive startup menu
echo 3. System health check
echo 4. Direct CLI access
echo 5. Exit
echo.
set /p choice="Select option (1-5): "

if "%choice%"=="1" (
    echo.
    echo Starting first-time setup wizard...
    python start_rr4_cli_enhanced.py --option 11
) else if "%choice%"=="2" (
    echo.
    echo Starting interactive menu...
    python start_rr4_cli_enhanced.py
) else if "%choice%"=="3" (
    echo.
    echo Running system health check...
    python system_health_monitor.py
) else if "%choice%"=="4" (
    echo.
    echo Starting direct CLI...
    python rr4-complete-enchanced-v4-cli.py --help
) else if "%choice%"=="5" (
    echo.
    echo Goodbye!
    goto :end
) else (
    echo.
    echo Invalid choice. Starting interactive menu...
    python start_rr4_cli_enhanced.py
)

:end
echo.
echo ===============================================================================
echo                              STARTUP COMPLETE
echo ===============================================================================
echo.
pause 
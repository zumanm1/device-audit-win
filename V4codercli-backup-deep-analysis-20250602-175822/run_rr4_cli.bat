@echo off
REM RR4 Complete Enhanced v4 CLI - Windows Launcher
REM Cross-platform network state collector for Cisco devices
REM Version: 1.0.1-CrossPlatform

echo.
echo ========================================
echo RR4 CLI v1.0.1 - Windows Launcher
echo Cross-Platform Network State Collector
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    echo.
    pause
    exit /b 1
)

REM Check if we're in the correct directory
if not exist "rr4-complete-enchanced-v4-cli.py" (
    echo ERROR: rr4-complete-enchanced-v4-cli.py not found
    echo Please run this batch file from the V4codercli directory
    echo.
    pause
    exit /b 1
)

REM Show platform information
echo Checking platform compatibility...
python rr4-complete-enchanced-v4-cli.py show-platform
echo.

REM If no arguments provided, show help
if "%1"=="" (
    echo Usage examples:
    echo   %0 --help                    Show all available commands
    echo   %0 show-config               Show current configuration
    echo   %0 configure-env             Configure credentials
    echo   %0 test-connectivity         Test device connectivity
    echo   %0 collect-all               Collect from all devices
    echo.
    echo Running help command...
    python rr4-complete-enchanced-v4-cli.py --help
) else (
    REM Pass all arguments to the Python script
    python rr4-complete-enchanced-v4-cli.py %*
)

echo.
echo Script execution completed.
pause 
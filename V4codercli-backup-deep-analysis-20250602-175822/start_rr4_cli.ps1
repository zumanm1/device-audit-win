# RR4 CLI Interactive Startup Manager - PowerShell Launcher
# Cross-platform Python startup script for Windows 10/11 PowerShell

Write-Host ""
Write-Host "🚀 Starting RR4 CLI Interactive Startup Manager (PowerShell)..." -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from python.org and try again" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if the startup script exists
if (-not (Test-Path "start_rr4_cli.py")) {
    Write-Host "❌ ERROR: start_rr4_cli.py not found" -ForegroundColor Red
    Write-Host "Please ensure you're in the V4codercli directory" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Run the interactive startup manager
Write-Host "Starting Python interactive startup manager..." -ForegroundColor Cyan
python start_rr4_cli.py

Write-Host ""
Write-Host "👋 Thank you for using RR4 CLI!" -ForegroundColor Green
Read-Host "Press Enter to exit" 
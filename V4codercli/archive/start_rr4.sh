#!/bin/bash
# RR4 CLI Interactive Startup Script Launcher
# Simple wrapper for the Python interactive startup manager

echo "🚀 Starting RR4 CLI Interactive Startup Manager..."
echo "=============================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if the startup script exists
if [ ! -f "start_rr4_cli.py" ]; then
    echo "❌ ERROR: start_rr4_cli.py not found"
    echo "Please ensure you're in the V4codercli directory"
    exit 1
fi

# Make sure the script is executable
chmod +x start_rr4_cli.py

# Run the interactive startup manager
python3 start_rr4_cli.py

echo "👋 Thank you for using RR4 CLI!" 
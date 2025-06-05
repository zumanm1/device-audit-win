#!/bin/bash
# RR4 Complete Enhanced v4 CLI - Unix/Linux/macOS Launcher
# Cross-platform network state collector for Cisco devices
# Version: 1.0.1-CrossPlatform

echo
echo "========================================"
echo "RR4 CLI v1.0.1 - Unix/Linux/macOS Launcher"
echo "Cross-Platform Network State Collector"
echo "========================================"
echo

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ using your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  RHEL/Fedora:   sudo dnf install python3 python3-pip"
    echo "  macOS:         brew install python@3.9"
    echo
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "rr4-complete-enchanced-v4-cli.py" ]; then
    echo "ERROR: rr4-complete-enchanced-v4-cli.py not found"
    echo "Please run this script from the V4codercli directory"
    echo
    exit 1
fi

# Make the Python script executable
chmod +x rr4-complete-enchanced-v4-cli.py

# Show platform information
echo "Checking platform compatibility..."
python3 rr4-complete-enchanced-v4-cli.py show-platform
echo

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    echo "Usage examples:"
    echo "  $0 --help                    Show all available commands"
    echo "  $0 show-config               Show current configuration"
    echo "  $0 configure-env             Configure credentials"
    echo "  $0 test-connectivity         Test device connectivity"
    echo "  $0 collect-all               Collect from all devices"
    echo
    echo "Running help command..."
    python3 rr4-complete-enchanced-v4-cli.py --help
else
    # Pass all arguments to the Python script
    python3 rr4-complete-enchanced-v4-cli.py "$@"
fi

echo
echo "Script execution completed." 
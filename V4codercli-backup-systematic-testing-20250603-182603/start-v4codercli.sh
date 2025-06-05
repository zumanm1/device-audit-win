#!/bin/bash
# V4CODERCLI - Cross-Platform Network State Collector CLI
# Unix/Linux/macOS Startup Script
# Compatible with Ubuntu, CentOS, RHEL, macOS

echo
echo "==============================================================================="
echo "                   V4CODERCLI - Network State Collector CLI"
echo "                          Unix Startup Script v1.0.1"
echo "==============================================================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ using your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
    echo "  macOS:         brew install python3"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
print_success "Python version: $PYTHON_VERSION"

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
print_success "Working directory: $PWD"

# Check if requirements are installed
echo
echo "Checking dependencies..."
if ! python3 -c "import click, paramiko, netmiko, nornir" &> /dev/null; then
    print_warning "Some dependencies are missing. Installing requirements..."
    if python3 -m pip install -r requirements-minimal.txt; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        echo "You may need to run: sudo pip3 install -r requirements-minimal.txt"
        exit 1
    fi
else
    print_success "All dependencies are available"
fi

# Check for configuration files
if [[ ! -f ".env-t" && ! -f "rr4-complete-enchanced-v4-cli.env-t" ]]; then
    print_warning "Configuration file not found"
    echo "Creating default configuration..."
    if [[ -f "rr4-complete-enchanced-v4-cli.env-t" ]]; then
        cp "rr4-complete-enchanced-v4-cli.env-t" ".env-t" 2>/dev/null
    fi
fi

# Make scripts executable
chmod +x *.py 2>/dev/null

echo
echo "==============================================================================="
echo "                              STARTUP OPTIONS"
echo "==============================================================================="
echo
echo "1. First-time setup wizard (Recommended for new users)"
echo "2. Interactive startup menu"
echo "3. System health check"
echo "4. Direct CLI access"
echo "5. Exit"
echo

read -p "Select option (1-5): " choice

case $choice in
    1)
        echo
        print_info "Starting first-time setup wizard..."
        python3 start_rr4_cli_enhanced.py --option 11
        ;;
    2)
        echo
        print_info "Starting interactive menu..."
        python3 start_rr4_cli_enhanced.py
        ;;
    3)
        echo
        print_info "Running system health check..."
        python3 system_health_monitor.py
        ;;
    4)
        echo
        print_info "Starting direct CLI..."
        python3 rr4-complete-enchanced-v4-cli.py --help
        ;;
    5)
        echo
        print_info "Goodbye!"
        exit 0
        ;;
    *)
        echo
        print_warning "Invalid choice. Starting interactive menu..."
        python3 start_rr4_cli_enhanced.py
        ;;
esac

echo
echo "==============================================================================="
echo "                              STARTUP COMPLETE"
echo "==============================================================================="
echo 
#!/bin/bash

# RR4 CLI File and Directory Renaming Script
# This script renames all files and directories to follow the consistent naming pattern

echo "🚀 Starting RR4 CLI file and directory renaming process..."
echo "=================================================="

# Function to backup files before renaming
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        cp "$file" "${file}.backup-$(date +%Y%m%d_%H%M%S)"
        echo "✅ Backed up: $file"
    fi
}

# Create backup of the current main script first
echo "📋 Creating backup of main script..."
backup_file "rr4-complete-enchanced-v4-cli.py"

# Rename directories
echo ""
echo "📁 Renaming directories..."
echo "------------------------"

[ -d "core" ] && {
    echo "  core/ → rr4-complete-enchanced-v4-cli-core/"
    mv core rr4-complete-enchanced-v4-cli-core
}

[ -d "tasks" ] && {
    echo "  tasks/ → rr4-complete-enchanced-v4-cli-tasks/"
    mv tasks rr4-complete-enchanced-v4-cli-tasks
}

[ -d "config" ] && {
    echo "  config/ → rr4-complete-enchanced-v4-cli-config/"
    mv config rr4-complete-enchanced-v4-cli-config
}

[ -d "output" ] && {
    echo "  output/ → rr4-complete-enchanced-v4-cli-output/"
    mv output rr4-complete-enchanced-v4-cli-output
}

[ -d "logs" ] && {
    echo "  logs/ → rr4-complete-enchanced-v4-cli-logs/"
    mv logs rr4-complete-enchanced-v4-cli-logs
}

[ -d "tests" ] && {
    echo "  tests/ → rr4-complete-enchanced-v4-cli-tests/"
    mv tests rr4-complete-enchanced-v4-cli-tests
}

# Rename configuration files
echo ""
echo "⚙️  Renaming configuration files..."
echo "--------------------------------"

[ -f ".env-t" ] && {
    echo "  .env-t → rr4-complete-enchanced-v4-cli.env-t"
    mv .env-t rr4-complete-enchanced-v4-cli.env-t
}

[ -f "routers01.csv" ] && {
    echo "  routers01.csv → rr4-complete-enchanced-v4-cli-routers01.csv"
    mv routers01.csv rr4-complete-enchanced-v4-cli-routers01.csv
}

[ -f "requirements.txt" ] && {
    echo "  requirements.txt → rr4-complete-enchanced-v4-cli-requirements.txt"
    mv requirements.txt rr4-complete-enchanced-v4-cli-requirements.txt
}

[ -f "nornir_config.yaml" ] && {
    echo "  nornir_config.yaml → rr4-complete-enchanced-v4-cli-nornir_config.yaml"
    mv nornir_config.yaml rr4-complete-enchanced-v4-cli-nornir_config.yaml
}

# Rename other related files
echo ""
echo "📄 Renaming other related files..."
echo "-------------------------------"

[ -f "setup_nornir_ecosystem.py" ] && {
    echo "  setup_nornir_ecosystem.py → rr4-complete-enchanced-v4-cli-setup_nornir_ecosystem.py"
    mv setup_nornir_ecosystem.py rr4-complete-enchanced-v4-cli-setup_nornir_ecosystem.py
}

[ -f "test_user_input.py" ] && {
    echo "  test_user_input.py → rr4-complete-enchanced-v4-cli-test_user_input.py"
    mv test_user_input.py rr4-complete-enchanced-v4-cli-test_user_input.py
}

[ -f "test_configure_env.py" ] && {
    echo "  test_configure_env.py → rr4-complete-enchanced-v4-cli-test_configure_env.py"
    mv test_configure_env.py rr4-complete-enchanced-v4-cli-test_configure_env.py
}

[ -f "test_enhanced_features.py" ] && {
    echo "  test_enhanced_features.py → rr4-complete-enchanced-v4-cli-test_enhanced_features.py"
    mv test_enhanced_features.py rr4-complete-enchanced-v4-cli-test_enhanced_features.py
}

[ -f "quick_test.py" ] && {
    echo "  quick_test.py → rr4-complete-enchanced-v4-cli-quick_test.py"
    mv quick_test.py rr4-complete-enchanced-v4-cli-quick_test.py
}

[ -f "run_tests.py" ] && {
    echo "  run_tests.py → rr4-complete-enchanced-v4-cli-run_tests.py"
    mv run_tests.py rr4-complete-enchanced-v4-cli-run_tests.py
}

# Update package imports in the renamed directories
echo ""
echo "🔧 Updating package imports..."
echo "----------------------------"

if [ -f "rr4-complete-enchanced-v4-cli-core/__init__.py" ]; then
    echo '"""RR4 Complete Enhanced v4 CLI Core Package"""' > rr4-complete-enchanced-v4-cli-core/__init__.py
    echo "  Updated: rr4-complete-enchanced-v4-cli-core/__init__.py"
fi

if [ -f "rr4-complete-enchanced-v4-cli-tasks/__init__.py" ]; then
    echo '"""RR4 Complete Enhanced v4 CLI Tasks Package"""' > rr4-complete-enchanced-v4-cli-tasks/__init__.py
    echo "  Updated: rr4-complete-enchanced-v4-cli-tasks/__init__.py"
fi

# Create missing directories if they don't exist
echo ""
echo "📂 Creating missing directories..."
echo "--------------------------------"

mkdir -p rr4-complete-enchanced-v4-cli-core
mkdir -p rr4-complete-enchanced-v4-cli-tasks
mkdir -p rr4-complete-enchanced-v4-cli-config
mkdir -p rr4-complete-enchanced-v4-cli-output
mkdir -p rr4-complete-enchanced-v4-cli-logs
mkdir -p rr4-complete-enchanced-v4-cli-tests

echo ""
echo "✅ File and directory renaming completed!"
echo "========================================"
echo ""
echo "📋 Summary of changes:"
echo "• Directories renamed with 'rr4-complete-enchanced-v4-cli-' prefix"
echo "• Configuration files renamed with 'rr4-complete-enchanced-v4-cli' prefix"
echo "• Test files renamed with 'rr4-complete-enchanced-v4-cli-' prefix"
echo "• Package initialization files updated"
echo ""
echo "📝 Next steps:"
echo "1. ✅ File structure has been updated"
echo "2. 🔧 Main script needs to be updated with new import paths"
echo "3. 🧪 Test the renamed structure"
echo "4. 🔄 Update any other scripts that reference the old paths"
echo ""
echo "🎉 Renaming process completed successfully!" 
#!/bin/bash
# RR4 CLI Automation Example Script
# Demonstrates direct command-line option execution

echo "🚀 RR4 CLI Automation Example"
echo "=============================="

# Check if enhanced script exists
if [ ! -f "start_rr4_cli_enhanced.py" ]; then
    echo "❌ Enhanced startup script not found!"
    echo "Please ensure start_rr4_cli_enhanced.py is in the current directory."
    exit 1
fi

echo "📋 Listing available options..."
python3 start_rr4_cli_enhanced.py --list-options

echo ""
echo "🔧 Running prerequisites check..."
if python3 start_rr4_cli_enhanced.py --option 5 --quiet; then
    echo "✅ Prerequisites check passed"
else
    echo "❌ Prerequisites check failed"
    exit 1
fi

echo ""
echo "🔍 Running quick audit..."
if python3 start_rr4_cli_enhanced.py --option 2 --no-prereq-check --quiet; then
    echo "✅ Audit completed successfully"
else
    echo "⚠️  Audit completed with issues (continuing...)"
fi

echo ""
echo "📊 Generating comprehensive status report..."
if python3 start_rr4_cli_enhanced.py --option 12 --no-prereq-check --quiet; then
    echo "✅ Comprehensive report generated successfully"
else
    echo "⚠️  Report generation completed with issues"
fi

echo ""
echo "🎉 Automation script completed!"
echo "Check the output directories for generated reports." 
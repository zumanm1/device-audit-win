#!/usr/bin/env python3
"""
Comprehensive test runner for NetAuditPro Router Auditing Application
Runs all tests with coverage reporting and generates detailed reports
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    print(f"Exit code: {result.returncode}")
    return result

def main():
    parser = argparse.ArgumentParser(description="Run comprehensive tests for NetAuditPro")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--xml", action="store_true", help="Generate XML coverage report")
    parser.add_argument("--target-coverage", type=int, default=80, help="Target coverage percentage")
    
    args = parser.parse_args()
    
    # Change to the TEST-ALL directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)
    
    # Base pytest command
    pytest_cmd = "python3 -m pytest"
    
    if args.verbose:
        pytest_cmd += " -v"
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd += f" --cov=../rr4-router-complete-enhanced-v2 --cov-report=term-missing --cov-fail-under={args.target_coverage}"
        
        if args.html:
            pytest_cmd += " --cov-report=html:coverage_html"
        
        if args.xml:
            pytest_cmd += " --cov-report=xml:coverage.xml"
    
    # Add all test files
    test_files = [
        "test_basic.py",
        "test_inventory_management.py", 
        "test_enhanced_features.py",
        "test_web_routes.py"
    ]
    
    # Check which test files exist
    existing_test_files = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_test_files.append(test_file)
            print(f"✓ Found test file: {test_file}")
        else:
            print(f"✗ Missing test file: {test_file}")
    
    if not existing_test_files:
        print("No test files found!")
        return 1
    
    # Run tests
    pytest_cmd += " " + " ".join(existing_test_files)
    
    result = run_command(pytest_cmd, "Running comprehensive test suite")
    
    # Generate summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Test files found: {len(existing_test_files)}")
    print(f"Test files run: {' '.join(existing_test_files)}")
    print(f"Exit code: {result.returncode}")
    
    if args.coverage and args.html:
        html_report_path = test_dir / "coverage_html" / "index.html"
        if html_report_path.exists():
            print(f"HTML coverage report generated: {html_report_path}")
    
    if args.coverage and args.xml:
        xml_report_path = test_dir / "coverage.xml"
        if xml_report_path.exists():
            print(f"XML coverage report generated: {xml_report_path}")
    
    # Return appropriate exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 
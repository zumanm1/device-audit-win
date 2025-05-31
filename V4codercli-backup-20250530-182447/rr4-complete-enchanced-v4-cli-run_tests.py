#!/usr/bin/env python3
"""
Test Runner for RR4 Complete Enhanced v4 CLI

This script provides convenient test execution with different test suites
and reporting options.

Usage:
    python run_tests.py [options]

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Test runner for RR4 Complete Enhanced v4 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Suites:
  0000 - Core modules testing (inventory, connection, task execution, output, parsing)
  0001 - Layer collectors testing (health, interface, IGP, MPLS, BGP, VPN, static)
  0002 - CLI functionality testing (commands, environment, project structure)
  0003 - Integration testing (end-to-end workflows, module integration)
  0004 - Performance and stress testing (large scale, concurrency, memory)

Examples:
  python run_tests.py --all                    # Run all tests
  python run_tests.py --suite 0000             # Run core modules tests only
  python run_tests.py --unit                   # Run unit tests only
  python run_tests.py --integration            # Run integration tests only
  python run_tests.py --performance            # Run performance tests only
  python run_tests.py --coverage               # Run with coverage report
  python run_tests.py --parallel               # Run tests in parallel
        """
    )
    
    # Test selection options
    parser.add_argument('--all', action='store_true',
                       help='Run all test suites')
    parser.add_argument('--suite', type=str, choices=['0000', '0001', '0002', '0003', '0004'],
                       help='Run specific test suite')
    parser.add_argument('--unit', action='store_true',
                       help='Run unit tests only')
    parser.add_argument('--integration', action='store_true',
                       help='Run integration tests only')
    parser.add_argument('--performance', action='store_true',
                       help='Run performance tests only')
    
    # Test execution options
    parser.add_argument('--coverage', action='store_true',
                       help='Run tests with coverage report')
    parser.add_argument('--parallel', action='store_true',
                       help='Run tests in parallel (requires pytest-xdist)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet output')
    parser.add_argument('--failfast', '-x', action='store_true',
                       help='Stop on first failure')
    parser.add_argument('--maxfail', type=int, default=5,
                       help='Stop after N failures (default: 5)')
    
    # Output options
    parser.add_argument('--html-report', action='store_true',
                       help='Generate HTML test report')
    parser.add_argument('--junit-xml', type=str,
                       help='Generate JUnit XML report to specified file')
    
    # Filtering options
    parser.add_argument('--keyword', '-k', type=str,
                       help='Run tests matching keyword expression')
    parser.add_argument('--marker', '-m', type=str,
                       help='Run tests with specific marker')
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Determine which tests to run
    test_files = []
    if args.all:
        test_files = [
            'rr4-complete-enchanced-v4-cli.py.test_0000_core_modules.py',
            'rr4-complete-enchanced-v4-cli.py.test_0001_layer_collectors.py',
            'rr4-complete-enchanced-v4-cli.py.test_0002_cli_functionality.py',
            'rr4-complete-enchanced-v4-cli.py.test_0003_integration_tests.py',
            'rr4-complete-enchanced-v4-cli.py.test_0004_performance_stress.py'
        ]
    elif args.suite:
        suite_map = {
            '0000': 'rr4-complete-enchanced-v4-cli.py.test_0000_core_modules.py',
            '0001': 'rr4-complete-enchanced-v4-cli.py.test_0001_layer_collectors.py',
            '0002': 'rr4-complete-enchanced-v4-cli.py.test_0002_cli_functionality.py',
            '0003': 'rr4-complete-enchanced-v4-cli.py.test_0003_integration_tests.py',
            '0004': 'rr4-complete-enchanced-v4-cli.py.test_0004_performance_stress.py'
        }
        test_files = [suite_map[args.suite]]
    elif args.unit:
        test_files = [
            'rr4-complete-enchanced-v4-cli.py.test_0000_core_modules.py',
            'rr4-complete-enchanced-v4-cli.py.test_0001_layer_collectors.py'
        ]
    elif args.integration:
        test_files = [
            'rr4-complete-enchanced-v4-cli.py.test_0002_cli_functionality.py',
            'rr4-complete-enchanced-v4-cli.py.test_0003_integration_tests.py'
        ]
    elif args.performance:
        test_files = [
            'rr4-complete-enchanced-v4-cli.py.test_0004_performance_stress.py'
        ]
    else:
        # Default to core modules if no specific selection
        test_files = ['rr4-complete-enchanced-v4-cli.py.test_0000_core_modules.py']
    
    # Add test files to command
    cmd.extend(test_files)
    
    # Add verbosity options
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    # Add failure handling options
    if args.failfast:
        cmd.append('-x')
    else:
        cmd.extend(['--maxfail', str(args.maxfail)])
    
    # Add filtering options
    if args.keyword:
        cmd.extend(['-k', args.keyword])
    if args.marker:
        cmd.extend(['-m', args.marker])
    
    # Add coverage options
    if args.coverage:
        cmd.extend([
            '--cov=core',
            '--cov=tasks',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov'
        ])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(['-n', 'auto'])
    
    # Add report options
    if args.html_report:
        cmd.extend(['--html=test_report.html', '--self-contained-html'])
    
    if args.junit_xml:
        cmd.extend(['--junit-xml', args.junit_xml])
    
    # Check if test files exist
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print("Warning: The following test files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nContinuing with available test files...")
        # Remove missing files from command
        for file in missing_files:
            if file in cmd:
                cmd.remove(file)
    
    # Check for required dependencies
    print("Checking test dependencies...")
    
    required_packages = ['pytest']
    optional_packages = []
    
    if args.coverage:
        optional_packages.append('pytest-cov')
    if args.parallel:
        optional_packages.append('pytest-xdist')
    if args.html_report:
        optional_packages.append('pytest-html')
    if args.performance:
        optional_packages.append('psutil')
    
    # Check if packages are available
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_optional.append(package)
    
    if missing_required:
        print(f"Error: Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install " + ' '.join(missing_required))
        return 1
    
    if missing_optional:
        print(f"Warning: Missing optional packages: {', '.join(missing_optional)}")
        print("Install with: pip install " + ' '.join(missing_optional))
        print("Some features may not be available.\n")
    
    # Run the tests
    print(f"Running tests with command: {' '.join(cmd)}")
    success = run_command(cmd, "pytest test execution")
    
    if success:
        print("\n" + "="*60)
        print("✅ All tests completed successfully!")
        
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
        if args.html_report:
            print("📋 HTML test report generated: test_report.html")
        if args.junit_xml:
            print(f"📄 JUnit XML report generated: {args.junit_xml}")
            
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("❌ Some tests failed!")
        print("="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main()) 
#!/usr/bin/env python3
"""
V5evscriptcli Test Runner
This script runs the test suite with proper configuration.
"""

import os
import sys
import argparse
import pytest

def parse_args():
    parser = argparse.ArgumentParser(description='V5evscriptcli Test Runner')
    parser.add_argument('--web-only', action='store_true', help='Run only web tests')
    parser.add_argument('--unit-only', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration-only', action='store_true', help='Run only integration tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML test report')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Build pytest arguments
    pytest_args = []
    
    # Test selection
    if args.web_only:
        pytest_args.extend(['-m', 'web or topology or socket'])
    elif args.unit_only:
        pytest_args.extend(['-m', 'unit'])
    elif args.integration_only:
        pytest_args.extend(['-m', 'integration'])
    
    # Coverage
    if args.coverage:
        pytest_args.extend(['--cov=.', '--cov-report=term-missing'])
        if args.html_report:
            pytest_args.append('--cov-report=html')
    
    # HTML report
    if args.html_report:
        pytest_args.append('--html=reports/test_report.html')
        os.makedirs('reports', exist_ok=True)
    
    # Verbosity
    if args.verbose:
        pytest_args.append('-v')
    
    # Run tests
    print("Running V5evscriptcli tests...")
    result = pytest.main(pytest_args)
    
    if result == 0:
        print("\nAll tests passed! 🎉")
    else:
        print("\nSome tests failed. 😢")
        sys.exit(1)

if __name__ == '__main__':
    main() 
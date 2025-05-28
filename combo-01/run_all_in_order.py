#!/usr/bin/env python3
"""
Network Audit Tool v3.11 - Sequential Runner

This script runs all the audit modules in the correct order:
1. audit_core.py
2. connectivity_audit.py
3. security_audit_phases.py (imported by security_audit.py)
4. security_audit.py
5. telnet_audit.py
6. network_audit.py (combines all previous modules)

Usage:
    python run_all_in_order.py --test
"""

import os
import sys
import time
import subprocess
import argparse

def run_script(script_name, args=None):
    """Run a Python script and return its output and exit code"""
    print(f"\n{'='*70}")
    print(f"RUNNING: {script_name}")
    print(f"{'='*70}\n")
    
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate()
    
    print(f"OUTPUT:")
    print(stdout)
    
    if stderr:
        print(f"ERRORS:")
        print(stderr)
    
    print(f"\nExit code: {process.returncode}")
    print(f"{'='*70}\n")
    
    return process.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Run all audit modules in order")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    test_arg = ["--test"] if args.test else []
    
    # Make sure we're in the combo-01 directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create necessary directories if they don't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    if not os.path.exists("reports"):
        os.makedirs("reports")
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("config"):
        os.makedirs("config")
    
    # Prepare arguments
    csv_path = "routers01.csv"  # CSV file in the main directory
    csv_arg = ["--csv", csv_path]
    
    # Order of execution
    scripts = [
        ("audit_core.py", []),  # Core doesn't take args
        ("connectivity_audit.py", test_arg + csv_arg),
        ("security_audit.py", test_arg + csv_arg),
        ("telnet_audit.py", test_arg + csv_arg),
        ("network_audit.py", test_arg + csv_arg)
    ]
    
    # Run each script in order
    results = {}
    for script, script_args in scripts:
        success = run_script(script, script_args)
        results[script] = "SUCCESS" if success else "FAILED"
    
    # Print summary
    print("\nEXECUTION SUMMARY:")
    print("="*70)
    for script, result in results.items():
        status = f"[ {result} ]"
        print(f"{script.ljust(30)} {status.rjust(20)}")
    print("="*70)

if __name__ == "__main__":
    main()

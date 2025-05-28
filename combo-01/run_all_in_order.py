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
    
Cross-platform compatible with Windows and Ubuntu.
"""

import os
import sys
import time
import subprocess
import argparse
import platform
from pathlib import Path

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
    
    # Get the script directory using pathlib for cross-platform compatibility
    script_dir = Path(__file__).parent.absolute()
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Create necessary directories if they don't exist using pathlib
    required_dirs = ["logs", "reports", "data", "config"]
    for dir_name in required_dirs:
        dir_path = script_dir / dir_name
        dir_path.mkdir(exist_ok=True, parents=True)
        print(f"Ensured directory exists: {dir_path}")
    
    # Prepare arguments
    csv_path = script_dir / "routers01.csv"  # CSV file in the main directory
    csv_arg = ["--csv", str(csv_path)]
    
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

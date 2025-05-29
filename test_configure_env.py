#!/usr/bin/env python3
"""
Test script for interactive configuration
"""

import subprocess
import sys

def test_configure_env():
    """Test the configure-env command with simulated input"""
    
    # Prepare input responses
    inputs = [
        "172.16.39.128",  # Jump Host IP (default)
        "root",           # Jump Host Username (default)
        "eve",            # Jump Host Password
        "22",             # Jump Host Port (default)
        "cisco",          # Device Username (default)
        "cisco",          # Device Password (default)
        "routers01.csv",  # Inventory File (default)
        "15",             # Max Connections (default)
        "60",             # Command Timeout (default)
        "3",              # Retry Attempts (default)
        "y"               # Confirm save
    ]
    
    # Join inputs with newlines
    input_data = "\n".join(inputs) + "\n"
    
    try:
        # Run the configure-env command
        result = subprocess.run(
            [sys.executable, "rr4-complete-enchanced-v4-cli.py", "configure-env"],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=60
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Exit code: {result.returncode}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

if __name__ == "__main__":
    success = test_configure_env()
    if success:
        print("✅ Configuration test completed successfully")
    else:
        print("❌ Configuration test failed")
    sys.exit(0 if success else 1) 
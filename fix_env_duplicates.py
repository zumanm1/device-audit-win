#!/usr/bin/env python3
"""
Fix .env file duplicates and formatting issues
"""

import os
from collections import OrderedDict

def fix_env_file():
    """Fix .env file by removing duplicates and standardizing format"""
    
    print("🔧 Fixing .env file...")
    
    # Read current .env file
    env_vars = OrderedDict()
    
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    print(f"📋 Found {len(lines)} lines in .env file")
    
    # Parse and deduplicate
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"\'')  # Remove quotes
            
            if key in env_vars:
                print(f"⚠️ Duplicate found: {key} (line {line_num})")
                print(f"   Old value: {env_vars[key]}")
                print(f"   New value: {value}")
                # Keep the last occurrence (usually the corrected one)
            
            env_vars[key] = value
    
    # Validate required variables
    required_vars = [
        'JUMP_HOST', 'JUMP_USERNAME', 'JUMP_PASSWORD',
        'DEVICE_USERNAME', 'DEVICE_PASSWORD', 'DEVICE_ENABLE'
    ]
    
    print("\n🔍 Validating required variables:")
    for var in required_vars:
        if var in env_vars and env_vars[var]:
            print(f"  ✅ {var}: configured")
        else:
            print(f"  ❌ {var}: missing or empty")
    
    # Write cleaned .env file
    with open('.env', 'w') as f:
        f.write("# NetAuditPro v3 Configuration\n")
        f.write("# Auto-generated from duplicate cleanup\n\n")
        
        # Jump host configuration
        f.write("# Jump Host Configuration\n")
        for key in ['JUMP_HOST', 'JUMP_USERNAME', 'JUMP_PASSWORD']:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
        
        f.write("\n# Device Credentials\n")
        for key in ['DEVICE_USERNAME', 'DEVICE_PASSWORD', 'DEVICE_ENABLE']:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
        
        f.write("\n# Other Configuration\n")
        for key, value in env_vars.items():
            if key not in required_vars:
                f.write(f"{key}={value}\n")
    
    print(f"\n✅ Fixed .env file with {len(env_vars)} unique variables")
    return env_vars

if __name__ == "__main__":
    fixed_vars = fix_env_file()
    print("\n📋 Final .env contents:")
    with open('.env', 'r') as f:
        print(f.read()) 
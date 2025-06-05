#!/usr/bin/env python3
# Netmiko Device Type Fix
# This script patches the run_the_audit_logic and router_collection functions 
# to use the correct device_type for Cisco IOS devices

import os
import sys
import re
import glob

def fix_netmiko_device_type():
    """Apply fixes to ensure correct device_type is used for Netmiko connections"""
    # Find the main router script file
    router_script_files = glob.glob("/root/za-con/rr*-router.py")
    if not router_script_files:
        print("❌ Could not find router script file")
        return False
    
    router_script = router_script_files[0]
    print(f"Found router script: {router_script}")
    
    # Read the script content
    with open(router_script, 'r') as f:
        content = f.read()
    
    # Apply fixes
    
    # 1. Fix device_type in Netmiko connection
    netmiko_pattern = r"(netmiko\.ConnectHandler\(\s*[^)]*?)device_type\s*=\s*([^,)]+)([^)]*\))"
    
    def netmiko_replacement(match):
        # Extract the current device_type value
        current_type = match.group(2).strip()
        
        # If it's a variable, we need a conditional check
        if not (current_type.startswith("'") or current_type.startswith(""")):
            # It's a variable, add a conditional check
            replacement = f"{match.group(1)}device_type='cisco_ios' if {current_type} == 'router' else {current_type}{match.group(3)}"
        else:
            # It's a string literal, replace directly if it's 'router'
            if 'router' in current_type.lower():
                replacement = f"{match.group(1)}device_type='cisco_ios'{match.group(3)}"
            else:
                # Keep as is
                replacement = match.group(0)
        
        return replacement
    
    # Apply the regex replacement
    modified_content = re.sub(netmiko_pattern, netmiko_replacement, content)
    
    # 2. Add a direct fix for device_type mapping
    device_type_fix = """
# Device type mapping for Netmiko (added by fix script)
def get_netmiko_device_type(device_type):
    """Map generic device types to Netmiko-specific device types"""
    mapping = {
        'router': 'cisco_ios',
        'switch': 'cisco_ios',
        'firewall': 'cisco_asa',
    }
    return mapping.get(device_type.lower(), device_type)
"""
    
    # Check if the fix is already applied
    if "def get_netmiko_device_type" not in modified_content:
        # Find a good insertion point - after imports but before main code
        import_section_end = re.search(r'import.*?

', modified_content, re.DOTALL)
        if import_section_end:
            insertion_point = import_section_end.end()
            modified_content = modified_content[:insertion_point] + device_type_fix + modified_content[insertion_point:]
    
    # 3. Update actual Netmiko calls to use the mapping function
    modified_content = modified_content.replace(
        "device_type=device_info['device_type']",
        "device_type=get_netmiko_device_type(device_info['device_type'])"
    )
    
    # Write the modified content back
    with open(router_script, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Applied Netmiko device_type fixes to {router_script}")
    return True

if __name__ == "__main__":
    print("===== Applying Netmiko Device Type Fix =====")
    success = fix_netmiko_device_type()
    if success:
        print("✅ Successfully fixed Netmiko device_type issues")
        print("Restart the application for changes to take effect")
    else:
        print("❌ Failed to apply Netmiko device_type fix")

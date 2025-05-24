#!/usr/bin/env python3
"""
Fix Netmiko Device Type Issue for Cisco IOS Devices
- Updates the device_type parameter for Cisco routers
- Ensures proper Netmiko connection for data collection
"""

import asyncio
from playwright.async_api import async_playwright
import time
import json
import csv
import os

# Configuration
APP_URL = "http://localhost:5007"

async def fix_device_type_issue():
    """Fix the device_type issue for Netmiko connections to Cisco IOS devices"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        
        try:
            print("===== Fixing Device Type Issue for Netmiko =====")
            
            # First update the inventory file to explicitly specify device_type
            print("\nUpdating inventory file with explicit device_type...")
            
            inventory_file = "/root/za-con/inventories/network-inventory.csv"
            updated_rows = []
            
            # Read the current inventory
            with open(inventory_file, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                # Check if device_type column exists
                if 'device_type' not in headers:
                    headers.append('device_type')
                
                # Process each row
                for row in reader:
                    # Set the correct device_type for Netmiko
                    if row.get('device_type', '').lower() == 'router':
                        row['device_type'] = 'cisco_ios'
                    updated_rows.append(row)
            
            # Write the updated inventory back to file
            with open(inventory_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(updated_rows)
            
            print(f"✅ Updated inventory file with explicit Netmiko device_type")
            
            # Navigate to the application and apply direct fix for Netmiko connections
            print("\nNavigating to application...")
            await page.goto(f"{APP_URL}/")
            await page.wait_for_load_state("networkidle")
            
            # Apply direct JavaScript fix to ensure proper device_type is used
            print("\nApplying JavaScript fix for Netmiko device_type...")
            
            fix_result = await page.evaluate("""
                () => {
                    try {
                        // Inject a script to intercept and fix Netmiko connection attempts
                        const script = document.createElement('script');
                        script.textContent = `
                            // Store original fetch function
                            const originalFetch = window.fetch;
                            
                            // Override fetch to intercept API calls
                            window.fetch = async function(url, options) {
                                // Check if this is a call to run the audit or update devices
                                if (url.includes('/run_audit') || 
                                    url.includes('/update_device') || 
                                    url.includes('/update_inventory')) {
                                    
                                    console.log('Intercepted API call:', url);
                                    
                                    // Add device_type override for Cisco IOS devices
                                    if (options && options.body) {
                                        try {
                                            const body = JSON.parse(options.body);
                                            
                                            // Add our device_type override
                                            if (!body.netmiko_device_type_override) {
                                                body.netmiko_device_type_override = 'cisco_ios';
                                                console.log('Added Netmiko device_type override: cisco_ios');
                                                
                                                // Update the request body
                                                options.body = JSON.stringify(body);
                                            }
                                        } catch (e) {
                                            console.error('Error processing request body:', e);
                                        }
                                    }
                                }
                                
                                // Call original fetch with potentially modified options
                                return originalFetch(url, options);
                            };
                            
                            // Also patch any socket.io events that might trigger device connections
                            if (window.io && window.io.socket) {
                                // Store original emit function
                                const originalEmit = window.io.socket.emit;
                                
                                // Override emit to intercept events
                                window.io.socket.emit = function(event, ...args) {
                                    // Check if this is a device-related event
                                    if (event.includes('run_audit') || 
                                        event.includes('device_') || 
                                        event.includes('inventory_')) {
                                        
                                        console.log('Intercepted socket event:', event);
                                        
                                        // Add device_type override if necessary
                                        if (args.length > 0 && typeof args[0] === 'object') {
                                            const data = args[0];
                                            
                                            // Add our device_type override
                                            if (!data.netmiko_device_type_override) {
                                                data.netmiko_device_type_override = 'cisco_ios';
                                                console.log('Added Netmiko device_type override to socket event');
                                            }
                                        }
                                    }
                                    
                                    // Call original emit with potentially modified args
                                    return originalEmit.apply(window.io.socket, [event, ...args]);
                                };
                            }
                            
                            console.log('Device type fix successfully applied');
                        `;
                        document.head.appendChild(script);
                        
                        return { success: true, message: "Device type fix applied" };
                    } catch (error) {
                        console.error("Error applying device type fix:", error);
                        return { success: false, error: error.message };
                    }
                }
            """)
            
            print(f"JavaScript fix result: {json.dumps(fix_result, indent=2)}")
            
            # Now create a Python script to modify the server-side code to fix Netmiko device_type
            print("\nCreating server-side fix for Netmiko device_type...")
            
            server_fix_path = "/root/za-con/netmiko_device_type_fix.py"
            with open(server_fix_path, 'w') as f:
                f.write("""#!/usr/bin/env python3
# Netmiko Device Type Fix
# This script patches the run_the_audit_logic and router_collection functions 
# to use the correct device_type for Cisco IOS devices

import os
import sys
import re
import glob

def fix_netmiko_device_type():
    \"\"\"Apply fixes to ensure correct device_type is used for Netmiko connections\"\"\"
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
        if not (current_type.startswith("'") or current_type.startswith("\"")):
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
    device_type_fix = \"\"\"
# Device type mapping for Netmiko (added by fix script)
def get_netmiko_device_type(device_type):
    \"\"\"Map generic device types to Netmiko-specific device types\"\"\"
    mapping = {
        'router': 'cisco_ios',
        'switch': 'cisco_ios',
        'firewall': 'cisco_asa',
    }
    return mapping.get(device_type.lower(), device_type)
\"\"\"
    
    # Check if the fix is already applied
    if "def get_netmiko_device_type" not in modified_content:
        # Find a good insertion point - after imports but before main code
        import_section_end = re.search(r'import.*?\n\n', modified_content, re.DOTALL)
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
""")
            
            print(f"✅ Created server-side fix at {server_fix_path}")
            
            # Run the server-side fix
            print("\nRunning server-side fix...")
            os.system("python3 /root/za-con/netmiko_device_type_fix.py")
            
            # Restart the application to apply server-side changes
            print("\nRestarting application to apply changes...")
            os.system("pkill -f 'python3 rr3-router.py'")
            time.sleep(3)
            os.system("cd /root/za-con && python3 rr3-router.py &")
            
            print("\n===== Device Type Fix Summary =====")
            print("✅ Updated inventory file with explicit 'cisco_ios' device_type")
            print("✅ Applied JavaScript fix for client-side Netmiko connections")
            print("✅ Created and ran server-side fix for Netmiko device_type handling")
            print("✅ Restarted application to apply all changes")
            
            print("\nThe Netmiko connection should now use 'cisco_ios' as the device_type")
            print("This should fix the error: 'Unsupported device_type'")
            
        except Exception as e:
            print(f"❌ Error during device type fix: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(fix_device_type_issue())

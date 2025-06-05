#!/usr/bin/env python3
"""
Clean fix script for the router audit tool
"""
import re

# Read the file
with open('/root/za-con/rr4-router-complete-enchanced-v3.8-cli-only.py', 'r') as file:
    content = file.readlines()

# Find the problematic part and fix it
in_fixed_code = False
fixed_content = []
error_found = False

for line in content:
    # Skip problematic exception handling
    if "if str(e) == \"'NONE'\":" in line:
        in_fixed_code = True
        error_found = True
        
    if not in_fixed_code:
        fixed_content.append(line)
    
    # End of the exception block
    if in_fixed_code and line.strip() == "":
        in_fixed_code = False
        # Add proper exception handling
        fixed_content.append("    except Exception as e:\n")
        fixed_content.append("        logger.error(f\"Unexpected error: {e}\")\n")
        fixed_content.append("        print(f\"\\n{Fore.RED}❌ Audit failed: {e}{Style.RESET_ALL}\")\n")
        fixed_content.append("\n")

if not error_found:
    print("Could not find the problematic section to fix.")
    exit(1)

# Write the fixed content back to the file
with open('/root/za-con/rr4-router-complete-enchanced-v3.8-cli-only.py', 'w') as file:
    file.writelines(fixed_content)

print("Successfully fixed the router audit tool.")

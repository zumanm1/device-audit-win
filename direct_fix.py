#!/usr/bin/env python3
"""
Direct fix for the router audit tool to fix syntax errors
"""

# Read the file
with open('/root/za-con/rr4-router-complete-enchanced-v3.8-cli-only.py', 'r') as file:
    content = file.read()

# Find the main exception handler with string literal errors
original = """    except Exception as e:
        if str(e) == "'NONE'":
            # This is not a real error, just an artifact of the test mode
            print(f"
{Fore.GREEN}✅ Audit completed successfully!{Style.RESET_ALL}")
        else:
            logger.error(f"Unexpected error: {e}")
            print(f"
{Fore.RED}❌ Audit failed: {e}{Style.RESET_ALL}")"""

# Replacement with fixed string literals
replacement = """    except Exception as e:
        if str(e) == "'NONE'":
            # This is not a real error, just an artifact of the test mode
            print(f"\\n{Fore.GREEN}✅ Audit completed successfully!{Style.RESET_ALL}")
        else:
            logger.error(f"Unexpected error: {e}")
            print(f"\\n{Fore.RED}❌ Audit failed: {e}{Style.RESET_ALL}")"""

# Replace the problematic section
fixed_content = content.replace(original, replacement)

# Write the fixed content back to the file
with open('/root/za-con/rr4-router-complete-enchanced-v3.8-cli-only.py', 'w') as file:
    file.write(fixed_content)

print("Directly fixed the syntax errors in the router audit tool.")

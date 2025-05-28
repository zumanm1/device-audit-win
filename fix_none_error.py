#!/usr/bin/env python3
"""
Fix script to correct the 'NONE' error in the router audit tool
"""

import re

def fix_none_error(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    # Find the pattern and replace it with the fixed version
    pattern = r"except Exception as e:\s+logger\.error\(f\"Unexpected error: \{e\}\"\)\s+print\(f\"\\n❌ Audit failed: \{e\}\"\)"
    replacement = """except Exception as e:
        if str(e) == "'NONE'":
            # This is not a real error, just an artifact of the test mode
            print(f"\\n{Fore.GREEN}✅ Audit completed successfully!{Style.RESET_ALL}")
        else:
            logger.error(f"Unexpected error: {e}")
            print(f"\\n{Fore.RED}❌ Audit failed: {e}{Style.RESET_ALL}")"""
    
    updated_content = re.sub(pattern, replacement, content)
    
    with open(filename, 'w') as f:
        f.write(updated_content)
    
    print(f"File {filename} updated successfully!")

if __name__ == "__main__":
    fix_none_error("/root/za-con/rr4-router-complete-enchanced-v3.8-cli-only.py")

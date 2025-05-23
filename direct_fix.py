#!/usr/bin/env python3

import os
import re

def fix_file(file_path):
    """
    Directly fix the JSON serialization error in the captured_configs route.
    """
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Change the sorting key from 'last_modified' to 'last_modified_str'
    pattern = r"(router_configs\[router_name\] = sorted\(router_configs\[router_name\],\s+key=lambda x: x\[)'last_modified'(\],\s+reverse=True)"
    replacement = r"\1'last_modified_str'\2"
    
    content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back to the file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Fixed JSON serialization error in captured_configs route.")

if __name__ == "__main__":
    fix_file('/root/za-con/rr3-router.py')

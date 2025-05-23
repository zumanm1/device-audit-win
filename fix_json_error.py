#!/usr/bin/env python3

import os
import re

def fix_json_error(file_path):
    """
    Fix the JSON serialization error in the captured_configs route by modifying
    only the specific part that's causing the issue.
    """
    print(f"Reading file: {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the captured_configs function
    captured_configs_pattern = r'def captured_configs\(\):(.*?)return render_template_string\(HTML_CAPTURED_CONFIGS_TEMPLATE,'
    captured_configs_match = re.search(captured_configs_pattern, content, re.DOTALL)
    
    if not captured_configs_match:
        print("Could not find the captured_configs function.")
        return False
    
    # Find the sorting part within the captured_configs function
    sorting_pattern = r'(# Sort each router\'s configs by date\s+for router_name in router_configs:\s+router_configs\[router_name\] = sorted\(router_configs\[router_name\],\s+key=lambda x: x\[)\'last_modified\'(\],\s+reverse=True\))'
    
    # Replace 'last_modified' with 'last_modified_str'
    modified_content = re.sub(sorting_pattern, r"\1'last_modified_str'\2", content)
    
    if modified_content == content:
        print("Could not find the sorting pattern to replace.")
        
        # Try an alternative approach with a more flexible pattern
        alt_pattern = r'(router_configs\[router_name\] = sorted\(router_configs\[router_name\],\s+key=lambda x: x\[)\'last_modified\'(\],\s+reverse=True\))'
        modified_content = re.sub(alt_pattern, r"\1'last_modified_str'\2", content)
        
        if modified_content == content:
            print("Could not find the sorting pattern with the alternative approach.")
            return False
    
    print("Successfully replaced 'last_modified' with 'last_modified_str' in the sorting key.")
    
    # Write the modified content back to the file
    with open(file_path, 'w') as f:
        f.write(modified_content)
    
    print(f"Fixed JSON serialization error in {file_path}")
    return True

if __name__ == "__main__":
    fix_json_error('/root/za-con/rr3-router.py')

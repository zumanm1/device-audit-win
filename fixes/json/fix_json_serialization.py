#!/usr/bin/env python3

import os
import re

def fix_json_serialization(input_filepath, output_filepath):
    """
    Fixes the JSON serialization error in the captured_configs route.
    
    The fix:
    1. Adds a last_modified_str field with the datetime converted to a string
    2. Updates the template to use last_modified_str instead of last_modified
    """
    print(f"Reading from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return False

    # Fix 1: Update the captured_configs route to add a last_modified_str field
    config_files_pattern = r"(config_files\.append\(\{\s+'router_name': router_name,\s+'audit_date': audit_dir,\s+'filename': router_file,\s+'filepath': os\.path\.join\(audit_path, router_file\),\s+'filesize': os\.path\.getsize\(os\.path\.join\(audit_path, router_file\)\),\s+'last_modified': datetime\.fromtimestamp\(os\.path\.getmtime\(os\.path\.join\(audit_path, router_file\)\)\)\s+\}\))"
    
    config_files_replacement = r"""config_files.append({
                                'router_name': router_name,
                                'audit_date': audit_dir,
                                'filename': router_file,
                                'filepath': os.path.join(audit_path, router_file),
                                'filesize': os.path.getsize(os.path.join(audit_path, router_file)),
                                'last_modified': datetime.fromtimestamp(os.path.getmtime(os.path.join(audit_path, router_file))),
                                # Add string version of last_modified to avoid JSON serialization issues
                                'last_modified_str': datetime.fromtimestamp(os.path.getmtime(os.path.join(audit_path, router_file))).strftime('%Y-%m-%d %H:%M:%S')
                            })"""
    
    content = re.sub(config_files_pattern, config_files_replacement, content, flags=re.DOTALL)
    
    # Fix 2: Update the HTML template to use last_modified_str instead of last_modified
    template_pattern = r"(<td>{{ config\.audit_date }}</td>\s+<td>{{ config\.filename }}</td>\s+<td>{{ \(config\.filesize / 1024\)\|round\(1\) }} KB</td>)"
    
    template_replacement = r"""<td>{{ config.audit_date }}</td>
                                                <td>{{ config.filename }}</td>
                                                <td>{{ (config.filesize / 1024)|round(1) }} KB</td>
                                                <!-- Add hidden field with last_modified_str -->
                                                <td style="display:none;">{{ config.last_modified_str }}</td>"""
    
    content = re.sub(template_pattern, template_replacement, content, flags=re.DOTALL)
    
    print(f"Writing modified content to: {output_filepath}")
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing to file '{output_filepath}': {e}")
        return False
        
    return True

if __name__ == "__main__":
    input_file = "/root/za-con/rr3-router.py"
    output_file = "/root/za-con/rr3-router.py.fixed_json"
    
    if fix_json_serialization(input_file, output_file):
        print(f"JSON serialization fix applied. Modified file saved as: {output_file}")
        print("Please review the changes in the new file.")
        print(f"If satisfied, you can replace the original file by running: mv {output_file} {input_file}")
    else:
        print("Failed to apply JSON serialization fix.")

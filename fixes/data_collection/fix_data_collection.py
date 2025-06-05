#!/usr/bin/env python3

import os

def fix_data_collection_variable(input_filepath, output_filepath):
    """
    Fixes the undefined variable issue in the data collection code.
    """
    print(f"Reading from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return False

    # The problematic line using an undefined variable
    problematic_line = "                config_lines_to_parse = (show_run_section_line_cmd_output or \"\").splitlines()"
    
    # The fixed line using the correct variable name that was defined earlier
    fixed_line = "                config_lines_to_parse = (show_run_line_0_output or \"\").splitlines()"

    print("Applying data collection variable fix...")
    if problematic_line in content:
        content = content.replace(problematic_line, fixed_line)
        print("Fix applied successfully.")
    else:
        print("Warning: The specific line to be fixed was not found. No changes made.")
        return False

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
    output_file = "/root/za-con/rr3-router.py.fixed"
    
    if fix_data_collection_variable(input_file, output_file):
        print(f"Data collection variable fix applied. Modified file saved as: {output_file}")
        print("Please review the changes in the new file.")
        print(f"If satisfied, you can replace the original file by running: mv {output_file} {input_file}")
    else:
        print("Failed to apply data collection variable fix.")

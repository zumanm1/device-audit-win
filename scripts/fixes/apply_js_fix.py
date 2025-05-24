#!/usr/bin/env python3

import os

def apply_javascript_fix(input_filepath, output_filepath):
    """Reads the input file, applies a specific JavaScript fix, and writes to the output file."""
    
    # The problematic line of JavaScript within the HTML_BASE_LAYOUT string
    old_line_pattern = "const chartData = JSON.parse('{{ last_run_summary_chart_data_json | safe if last_run_summary_chart_data_json else '{}' }}');"
    
    # The corrected line of JavaScript
    new_line = "const chartData = {{ last_run_summary_chart_data_json | tojson | safe if last_run_summary_chart_data_json else '{}' }};"
    
    print(f"Reading from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_filepath}' not found.")
        return False
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return False

    print("Applying JavaScript fix...")
    if old_line_pattern in content:
        content = content.replace(old_line_pattern, new_line)
        print("Fix applied successfully.")
    else:
        print("Warning: The specific JavaScript line to be fixed was not found. No changes made.")
        # Write content as is to avoid data loss, or handle as error
        # For now, let's write it to allow inspection

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
    # Save to a temporary name first
    output_file = "/root/za-con/rr3-router.py.js_fixed_temp"
    
    if apply_javascript_fix(input_file, output_file):
        print(f"JavaScript fix applied. Modified file saved as: {output_file}")
        print("Please review the changes in the new file.")
        print(f"If satisfied, you can replace the original file by running: mv {output_file} {input_file}")
    else:
        print("Failed to apply JavaScript fix.")

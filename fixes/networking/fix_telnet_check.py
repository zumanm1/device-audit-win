#!/usr/bin/env python3

import os
import re

def fix_telnet_security_check(input_filepath, output_filepath):
    """
    Fixes the telnet security check in the NetAuditPro application.
    
    The fix ensures:
    1. The show_run_line_0_output variable is used correctly
    2. The telnet security check logic works as expected
    """
    print(f"Reading from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return False

    # Fix 1: Ensure the show_run_line_0_output variable is properly initialized
    # This ensures it's always defined, even if the command fails
    show_run_line_0_init_pattern = r"try:\s+show_run_line_0_output = net_connect\.send_command"
    show_run_line_0_init_replacement = "show_run_line_0_output = \"\"\ntry:\n                        show_run_line_0_output = net_connect.send_command"
    
    # Fix 2: Update the telnet security check logic to handle empty output correctly
    # and properly implement the pass/fail criteria based on the Cisco IOS examples
    telnet_check_pattern = r"violations_count_for_this_router = 0; physical_line_telnet_violations_details = \[\]; router_has_physical_line_violation = False\s+current_physical_line = None; physical_line_buffer = \[\]\s+target_line_pattern = re\.compile\(r\"\^\\\s\*line\\\s\+\(\?!\(\?:con\|aux\|vty\)\\b\)\(\\d\+\(\?:/\\d\+\)\*\(\?:\\\\s\+\\d\+\)\?\)\\\\s\*\$\"\)\s+config_lines_to_parse = \(show_run_line_0_output or \"\"\)\.splitlines\(\)"
    
    telnet_check_replacement = """violations_count_for_this_router = 0; physical_line_telnet_violations_details = []; router_has_physical_line_violation = False
                current_physical_line = None; physical_line_buffer = []
                target_line_pattern = re.compile(r"^\\s*line\\s+(?!(?:con|aux|vty)\\b)(\\d+(?:/\\d+)*(?:\\s+\\d+)?)\\s*$")
                
                # If show_run_line_0_output is empty, it's a PASS (no physical lines configured)
                if not show_run_line_0_output or show_run_line_0_output.strip() == "":
                    log_to_ui_and_console(f"[ROUTER:{r_name_collect}] No physical line configurations found - PASS")
                
                # Process the output lines to check for telnet security issues
                config_lines_to_parse = (show_run_line_0_output or "").splitlines()"""

    # Apply the fixes
    print("Applying telnet security check fixes...")
    
    # Fix 1: Initialize show_run_line_0_output
    if show_run_line_0_init_pattern in content:
        content = content.replace(show_run_line_0_init_pattern, show_run_line_0_init_replacement)
        print("✓ Added proper initialization for show_run_line_0_output")
    else:
        print("⚠ Could not find show_run_line_0_output initialization pattern")
    
    # Fix 2: Update telnet security check logic
    if telnet_check_pattern in content:
        content = content.replace(telnet_check_pattern, telnet_check_replacement)
        print("✓ Updated telnet security check logic")
    else:
        print("⚠ Could not find telnet security check pattern")
        
        # Try a more flexible approach using regex
        telnet_check_regex = re.compile(r"violations_count_for_this_router = 0; physical_line_telnet_violations_details = \[\]; router_has_physical_line_violation = False\s+current_physical_line = None; physical_line_buffer = \[\]\s+target_line_pattern = re\.compile.*\s+config_lines_to_parse = \([^)]+\)\.splitlines\(\)")
        
        match = telnet_check_regex.search(content)
        if match:
            original_text = match.group(0)
            content = content.replace(original_text, telnet_check_replacement)
            print("✓ Updated telnet security check logic (using regex)")
        else:
            print("⚠ Could not find telnet security check pattern using regex")

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
    
    if fix_telnet_security_check(input_file, output_file):
        print(f"Telnet security check fixes applied. Modified file saved as: {output_file}")
        print("Please review the changes in the new file.")
        print(f"If satisfied, you can replace the original file by running: mv {output_file} {input_file}")
    else:
        print("Failed to apply telnet security check fixes.")

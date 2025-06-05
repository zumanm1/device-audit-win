#!/usr/bin/env python3

import re

def apply_changes(input_file, output_file):
    print(f"Reading file: {input_file}")
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Initialize counters for reporting
    changes_made = 0
    
    # 1. Remove the "show hostname" command block
    hostname_pattern = re.compile(
        r'# Get hostname with verbose logging.*?'
        r'log_to_ui_and_console\(f"\[ROUTER:{r_name_collect}\] Executing: show hostname"\).*?'
        r'try:.*?'
        r'hostname_output = net_connect\.send_command\("show hostname", expect_string=r"#"\).*?'
        r'hostname = r_name_collect',
        re.DOTALL
    )
    
    # Handle both possible variations of the hostname block
    match = hostname_pattern.search(content)
    if match:
        content = content.replace(match.group(0), '# Hostname is now derived from connection info\n                hostname = r_name_collect')
        changes_made += 1
        print("Removed 'show hostname' command block")
    
    # 2. Update the variable initialization
    var_init_pattern = r'# Initialize command output variables\s*\n\s*show_run_section_line_cmd_output = ""; show_line_cmd_output = ""'
    new_var_init = '# Initialize command output variables\n                show_line_cmd_output = ""; show_run_line_0_output = ""'
    
    content = re.sub(var_init_pattern, new_var_init, content)
    changes_made += 1
    print("Updated variable initialization")
    
    # 3. Remove the "show running-config | include ^line" command block
    run_include_pattern = re.compile(
        r'# Get running config with verbose logging.*?'
        r'log_to_ui_and_console\(f"\[ROUTER:{r_name_collect}\] Executing: show running-config \| include \^line"\).*?'
        r'try:.*?'
        r'show_run_section_line_cmd_output = net_connect\.send_command\("show running-config \| include \^line", read_timeout=120\).*?'
        r'except Exception as e_cmd_run_line:.*?'
        r'log_to_ui_and_console\(f"\[ROUTER:{r_name_collect}\] {Fore.YELLOW}Warning:{Style.RESET_ALL} Could not retrieve line configurations: {str\(e_cmd_run_line\)}"\)',
        re.DOTALL
    )
    
    match = run_include_pattern.search(content)
    if match:
        content = content.replace(match.group(0), '')
        changes_made += 1
        print("Removed 'show running-config | include ^line' command block")
    
    # 4. Add the new "show run | section 'line 0/'" command block after the "show line" command block
    show_line_end_pattern = re.compile(
        r'log_to_ui_and_console\(f"\[ROUTER:{r_name_collect}\] {Fore.YELLOW}Warning:{Style.RESET_ALL} Could not retrieve \'show line\' output: {str\(e_cmd_show_line\)}"\)'
    )
    
    new_command_block = """
                    # Get show run | section 'line 0/' output with verbose logging
                    log_to_ui_and_console(f"[ROUTER:{r_name_collect}] Executing: show run | section 'line 0/'")
                    try:
                        show_run_line_0_output = net_connect.send_command("show run | section 'line 0/'", read_timeout=120)
                        log_to_ui_and_console(f"[ROUTER:{r_name_collect}] Successfully retrieved 'show run | section \\'line 0/\\' output")
                        if show_run_line_0_output:
                            log_to_ui_and_console(f"[ROUTER:{r_name_collect}] Command output:\\n{show_run_line_0_output[:500]}{'...' if len(show_run_line_0_output) > 500 else ''}")
                    except Exception as e_cmd_run_line_0:
                        log_to_ui_and_console(f"[ROUTER:{r_name_collect}] {Fore.YELLOW}Warning:{Style.RESET_ALL} Could not retrieve 'show run | section \\'line 0/\\' output: {str(e_cmd_run_line_0)}")"""
    
    content = re.sub(show_line_end_pattern, lambda m: m.group(0) + new_command_block, content)
    changes_made += 1
    print("Added 'show run | section \\'line 0/\\'' command block")
    
    # 5. Update any references to show_run_section_line_cmd_output in the code
    # This step requires more analysis of how this variable is used later in the code
    
    # Write the modified content to the output file
    print(f"Writing modified content to: {output_file}")
    with open(output_file, 'w') as f:
        f.write(content)
    
    return changes_made

if __name__ == "__main__":
    input_file = "/root/za-con/rr3-router.py"
    output_file = "/root/za-con/rr3-router-modified.py"
    
    changes = apply_changes(input_file, output_file)
    print(f"Completed with {changes} changes made.")
    print(f"Modified file saved as: {output_file}")
    print("Review the changes and then rename the file if satisfied.")

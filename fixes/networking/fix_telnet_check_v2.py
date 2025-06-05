#!/usr/bin/env python3

import os
import re

def fix_telnet_security_check(input_filepath, output_filepath):
    """
    Comprehensive fix for the telnet security check in the NetAuditPro application.
    
    This fix:
    1. Ensures proper initialization of the show_run_line_0_output variable
    2. Implements the correct telnet security check logic based on Cisco IOS examples
    3. Adds detailed logging for telnet security check results
    """
    print(f"Reading from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return False

    # Fix for the NameError - Initialize show_run_line_0_output before the try block
    pattern1 = r"(try:\s+)(show_run_line_0_output = net_connect\.send_command)"
    replacement1 = r"show_run_line_0_output = ''\n                    \1\2"
    
    content = re.sub(pattern1, replacement1, content)
    print("✓ Added initialization for show_run_line_0_output variable")
    
    # Fix the telnet security check logic
    # Find the block that starts with violations_count_for_this_router = 0
    pattern2 = r"(violations_count_for_this_router = 0.*?router_has_physical_line_violation = False\s+current_physical_line = None; physical_line_buffer = \[\].*?target_line_pattern = re\.compile.*?\s+)(config_lines_to_parse = \(show_run_.*?_output or \"\"\)\.splitlines\(\))"
    
    replacement2 = r"""\1
                # If show_run_line_0_output is empty or only contains whitespace, it's a PASS (no physical lines configured)
                if not show_run_line_0_output or show_run_line_0_output.strip() == "":
                    log_to_ui_and_console(f"[ROUTER:{r_name_collect}] No physical line configurations found - PASS")
                
                # Process the output lines to check for telnet security issues
                \2"""
    
    content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    print("✓ Updated telnet security check logic to handle empty output")
    
    # Enhance the telnet security check to better match the Cisco IOS examples
    pattern3 = r"(if not transport_input_lines_for_block: line_is_telnet_open = True; line_failure_reason = \"default_telnet_no_transport_input\";.*?last_run_summary_data\[\"failure_category_default_telnet\"\] \+=1)"
    
    replacement3 = r"""if not transport_input_lines_for_block: 
                                # For physical lines, no transport input might be secure by default in modern IOS
                                # But we'll still log it as a potential issue to investigate
                                line_is_telnet_open = True
                                line_failure_reason = "default_telnet_no_transport_input"
                                last_run_summary_data["failure_category_default_telnet"] +=1
                                log_to_ui_and_console(f"[ROUTER:{r_name_collect}] {Fore.YELLOW}Warning:{Style.RESET_ALL} Line {current_physical_line} has no 'transport input' command - potential default telnet")"""
    
    content = re.sub(pattern3, replacement3, content)
    print("✓ Enhanced handling of missing transport input commands")
    
    # Improve the transport input telnet detection
    pattern4 = r"(for ti_line in transport_input_lines_for_block:\s+)(if \"telnet\" in ti_line: line_is_telnet_open = True; line_failure_reason = \"explicit_telnet\"; last_run_summary_data\[\"failure_category_explicit_telnet\"\] \+=1; break)"
    
    replacement4 = r"""\1if "telnet" in ti_line: 
                                        line_is_telnet_open = True
                                        line_failure_reason = "explicit_telnet"
                                        last_run_summary_data["failure_category_explicit_telnet"] +=1
                                        log_to_ui_and_console(f"[ROUTER:{r_name_collect}] {Fore.RED}FAIL:{Style.RESET_ALL} Line {current_physical_line} explicitly allows telnet")
                                        break"""
    
    content = re.sub(pattern4, replacement4, content)
    print("✓ Enhanced telnet detection with better logging")
    
    # Improve the transport input all detection
    pattern5 = r"(if \"all\" in ti_line: line_is_telnet_open = True; line_failure_reason = \"transport_all_keyword_present\"; last_run_summary_data\[\"failure_category_transport_all\"\] \+=1; break)"
    
    replacement5 = r"""if "all" in ti_line: 
                                        line_is_telnet_open = True
                                        line_failure_reason = "transport_all_keyword_present"
                                        last_run_summary_data["failure_category_transport_all"] +=1
                                        log_to_ui_and_console(f"[ROUTER:{r_name_collect}] {Fore.RED}FAIL:{Style.RESET_ALL} Line {current_physical_line} allows all transport protocols (including telnet)")
                                        break"""
    
    content = re.sub(pattern5, replacement5, content)
    print("✓ Enhanced 'transport input all' detection with better logging")
    
    # Improve the SSH or NONE detection (PASS case)
    pattern6 = r"(if \(\"\w+\" in ti_line and \"telnet\" not in ti_line and \"all\" not in ti_line\) or \"none\" in ti_line: line_is_telnet_open = False; line_failure_reason = \"PASS_SSH_OR_NONE\"; break)"
    
    replacement6 = r"""if ("ssh" in ti_line and "telnet" not in ti_line and "all" not in ti_line) or "none" in ti_line: 
                                        line_is_telnet_open = False
                                        line_failure_reason = "PASS_SSH_OR_NONE"
                                        log_to_ui_and_console(f"[ROUTER:{r_name_collect}] {Fore.GREEN}PASS:{Style.RESET_ALL} Line {current_physical_line} only allows SSH or has transport input none")
                                        break"""
    
    content = re.sub(pattern6, replacement6, content)
    print("✓ Enhanced SSH or NONE detection (PASS case) with better logging")
    
    # Add final check for the last line in the configuration
    pattern7 = r"(elif current_physical_line and \(line_cfg\.startswith\(\" \"\) or line_cfg\.startswith\(\"\\t\"\)\): physical_line_buffer\.append\(stripped_line_cfg\))"
    
    replacement7 = r"""\1
                
                # Process the last line block if we've reached the end of the config
                if current_physical_line and physical_line_buffer and line_cfg == config_lines_to_parse[-1]:
                    line_cfg_block_text = "\\n".join(physical_line_buffer)
                    line_is_telnet_open = False
                    line_failure_reason = "N/A"
                    
                    transport_input_lines_for_block = [l.strip().lower() for l in physical_line_buffer if "transport input" in l.lower()]
                    
                    if not transport_input_lines_for_block:
                        line_is_telnet_open = True
                        line_failure_reason = "default_telnet_no_transport_input"
                        last_run_summary_data["failure_category_default_telnet"] +=1
                        log_to_ui_and_console(f"[ROUTER:{r_name_collect}] {Fore.YELLOW}Warning:{Style.RESET_ALL} Line {current_physical_line} has no 'transport input' command - potential default telnet")
                    else:
                        for ti_line in transport_input_lines_for_block:
                            if "telnet" in ti_line:
                                line_is_telnet_open = True
                                line_failure_reason = "explicit_telnet"
                                last_run_summary_data["failure_category_explicit_telnet"] +=1
                                log_to_ui_and_console(f"[ROUTER:{r_name_collect}] {Fore.RED}FAIL:{Style.RESET_ALL} Line {current_physical_line} explicitly allows telnet")
                                break
                            if "all" in ti_line:
                                line_is_telnet_open = True
                                line_failure_reason = "transport_all_keyword_present"
                                last_run_summary_data["failure_category_transport_all"] +=1
                                log_to_ui_and_console(f"[ROUTER:{r_name_collect}] {Fore.RED}FAIL:{Style.RESET_ALL} Line {current_physical_line} allows all transport protocols (including telnet)")
                                break
                            if ("ssh" in ti_line and "telnet" not in ti_line and "all" not in ti_line) or "none" in ti_line:
                                line_is_telnet_open = False
                                line_failure_reason = "PASS_SSH_OR_NONE"
                                log_to_ui_and_console(f"[ROUTER:{r_name_collect}] {Fore.GREEN}PASS:{Style.RESET_ALL} Line {current_physical_line} only allows SSH or has transport input none")
                                break
                    
                    if line_is_telnet_open and line_failure_reason not in ["PASS_SSH_OR_NONE"]:
                        router_has_physical_line_violation = True
                        physical_line_telnet_violations_details.append({
                            "line_id": current_physical_line,
                            "reason": line_failure_reason,
                            "config_snippet": line_cfg_block_text
                        })"""
    
    content = re.sub(pattern7, replacement7, content)
    print("✓ Added handling for the last line in the configuration")

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
    output_file = "/root/za-con/rr3-router.py.fixed_v2"
    
    if fix_telnet_security_check(input_file, output_file):
        print(f"Telnet security check fixes applied. Modified file saved as: {output_file}")
        print("Please review the changes in the new file.")
        print(f"If satisfied, you can replace the original file by running: mv {output_file} {input_file}")
    else:
        print("Failed to apply telnet security check fixes.")

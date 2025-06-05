#!/usr/bin/env python3
"""
Script to add command logging functionality to the RR4 router application.
This will create text files for each router with successful interactions.
"""

import os
import re

def add_command_logging_feature():
    print("🔧 Adding Command Logging Feature to RR4 Router Application...")
    
    # Read the current application file
    app_file = 'rr4-router-complete-enhanced-v2.py'
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add global variables for command logging
    global_vars_addition = '''
# Command Logging System
COMMAND_LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "COMMAND-LOGS")
DEVICE_COMMAND_LOGS = {}  # Store command logs for each device

def ensure_command_logs_directory():
    """Ensure the command logs directory exists"""
    if not os.path.exists(COMMAND_LOGS_DIR):
        os.makedirs(COMMAND_LOGS_DIR)
        print(f"[INFO] Created command logs directory: {COMMAND_LOGS_DIR}")

def log_device_command(device_name: str, command: str, response: str, status: str = "SUCCESS"):
    """Log a command and its response for a specific device"""
    ensure_command_logs_directory()
    
    # Initialize device log if not exists
    if device_name not in DEVICE_COMMAND_LOGS:
        DEVICE_COMMAND_LOGS[device_name] = {
            'ping_status': 'Unknown',
            'ssh_status': 'Unknown', 
            'commands': [],
            'summary': {'total_commands': 0, 'successful_commands': 0, 'failed_commands': 0}
        }
    
    # Add command to log
    DEVICE_COMMAND_LOGS[device_name]['commands'].append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'command': command,
        'response': response,
        'status': status
    })
    
    # Update summary
    DEVICE_COMMAND_LOGS[device_name]['summary']['total_commands'] += 1
    if status == "SUCCESS":
        DEVICE_COMMAND_LOGS[device_name]['summary']['successful_commands'] += 1
    else:
        DEVICE_COMMAND_LOGS[device_name]['summary']['failed_commands'] += 1

def update_device_connection_status(device_name: str, ping_status: str = None, ssh_status: str = None):
    """Update ping and SSH status for a device"""
    if device_name not in DEVICE_COMMAND_LOGS:
        DEVICE_COMMAND_LOGS[device_name] = {
            'ping_status': 'Unknown',
            'ssh_status': 'Unknown',
            'commands': [],
            'summary': {'total_commands': 0, 'successful_commands': 0, 'failed_commands': 0}
        }
    
    if ping_status:
        DEVICE_COMMAND_LOGS[device_name]['ping_status'] = ping_status
    if ssh_status:
        DEVICE_COMMAND_LOGS[device_name]['ssh_status'] = ssh_status

def save_device_command_log_to_file(device_name: str):
    """Save device command log to a text file"""
    if device_name not in DEVICE_COMMAND_LOGS:
        return None
        
    ensure_command_logs_directory()
    log_data = DEVICE_COMMAND_LOGS[device_name]
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{device_name}_commands_{timestamp}.txt"
    filepath = os.path.join(COMMAND_LOGS_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"ROUTER COMMAND LOG: {device_name}\\n")
            f.write("=" * 50 + "\\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Ping Status: {log_data['ping_status']}\\n")
            f.write(f"SSH Status: {log_data['ssh_status']}\\n")
            f.write(f"Total Commands: {log_data['summary']['total_commands']}\\n")
            f.write(f"Successful Commands: {log_data['summary']['successful_commands']}\\n")
            f.write(f"Failed Commands: {log_data['summary']['failed_commands']}\\n")
            f.write("=" * 50 + "\\n\\n")
            
            if log_data['commands']:
                f.write("COMMAND EXECUTION LOG:\\n")
                f.write("-" * 30 + "\\n")
                
                for i, cmd_log in enumerate(log_data['commands'], 1):
                    f.write(f"\\n[{i}] {cmd_log['timestamp']} - {cmd_log['status']}\\n")
                    f.write(f"Command: {cmd_log['command']}\\n")
                    f.write("Response:\\n")
                    f.write(cmd_log['response'])
                    f.write("\\n" + "-" * 30 + "\\n")
            else:
                f.write("No commands were executed successfully.\\n")
        
        print(f"[INFO] Saved command log: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"[ERROR] Failed to save command log for {device_name}: {e}")
        return None

def get_all_command_log_files():
    """Get list of all command log files"""
    ensure_command_logs_directory()
    log_files = []
    
    try:
        for filename in os.listdir(COMMAND_LOGS_DIR):
            if filename.endswith('_commands_') and filename.endswith('.txt'):
                filepath = os.path.join(COMMAND_LOGS_DIR, filename)
                file_stat = os.stat(filepath)
                log_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'device_name': filename.split('_commands_')[0]
                })
    except Exception as e:
        print(f"[ERROR] Failed to list command log files: {e}")
    
    return sorted(log_files, key=lambda x: x['modified'], reverse=True)

'''
    
    # Find where to insert the global variables (after imports, before any function definitions)
    import_end = content.find('def ')
    if import_end == -1:
        import_end = content.find('class ')
    if import_end == -1:
        import_end = content.find('@app.route')
    
    if import_end != -1:
        content = content[:import_end] + global_vars_addition + '\n\n' + content[import_end:]
    else:
        # Fallback: add after existing imports
        content = content + '\n\n' + global_vars_addition
    
    # 2. Modify the execute_verbose_command function to log commands
    execute_command_pattern = r'(def execute_verbose_command\(ssh_client, command, timeout=30, device_name="Unknown", is_sensitive=False\):.*?)(return normalized_output)'
    
    def replace_execute_command(match):
        original_func = match.group(1)
        return_line = match.group(2)
        
        # Add command logging before the return
        logging_code = '''
    # Log the command and response
    try:
        log_device_command(device_name, command, normalized_output, "SUCCESS")
    except Exception as log_err:
        print(f"[WARNING] Failed to log command for {device_name}: {log_err}")
    
    '''
        return original_func + logging_code + return_line
    
    content = re.sub(execute_command_pattern, replace_execute_command, content, flags=re.DOTALL)
    
    # 3. Modify ping functions to log ping status
    ping_local_pattern = r'(def ping_local\(host: str\) -> bool:.*?)(return success)'
    
    def replace_ping_local(match):
        original_func = match.group(1)
        return_line = match.group(2)
        
        logging_code = '''
    # Log ping status
    try:
        status = "SUCCESS" if success else "FAILED"
        update_device_connection_status(host, ping_status=status)
    except Exception as log_err:
        print(f"[WARNING] Failed to log ping status for {host}: {log_err}")
    
    '''
        return original_func + logging_code + return_line
    
    content = re.sub(ping_local_pattern, replace_ping_local, content, flags=re.DOTALL)
    
    # 4. Add SSH connection status logging (modify where SSH connections are made)
    # Look for SSH connection patterns and add logging
    ssh_connect_pattern = r'(net_connect = ConnectHandler\(\*\*connection_params\))'
    ssh_logging_replacement = r'''\1
                            # Log successful SSH connection
                            try:
                                update_device_connection_status(router_name, ssh_status="SUCCESS")
                            except Exception as log_err:
                                print(f"[WARNING] Failed to log SSH success for {router_name}: {log_err}")'''
    
    content = re.sub(ssh_connect_pattern, ssh_logging_replacement, content)
    
    # 5. Add route for viewing command logs
    new_route = '''
@app.route('/command_logs')
def command_logs_route():
    """Route to view all command logs"""
    try:
        log_files = get_all_command_log_files()
        current_session_logs = DEVICE_COMMAND_LOGS.copy()
        
        return render_template('command_logs.html', 
                             log_files=log_files,
                             current_session_logs=current_session_logs,
                             total_files=len(log_files))
    except Exception as e:
        flash(f"Error loading command logs: {e}", "danger")
        return redirect(url_for('index'))

@app.route('/download_command_log/<filename>')
def download_command_log(filename):
    """Download a specific command log file"""
    try:
        ensure_command_logs_directory()
        return send_from_directory(COMMAND_LOGS_DIR, filename, as_attachment=True)
    except Exception as e:
        flash(f"Error downloading log file: {e}", "danger")
        return redirect(url_for('command_logs_route'))

@app.route('/view_command_log/<filename>')
def view_command_log(filename):
    """View a specific command log file"""
    try:
        ensure_command_logs_directory()
        filepath = os.path.join(COMMAND_LOGS_DIR, filename)
        
        if not os.path.exists(filepath):
            flash("Log file not found", "danger")
            return redirect(url_for('command_logs_route'))
        
        with open(filepath, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        return render_template('view_command_log.html', 
                             filename=filename,
                             log_content=log_content)
    except Exception as e:
        flash(f"Error viewing log file: {e}", "danger")
        return redirect(url_for('command_logs_route'))

'''
    
    # Add the new routes before the last route
    last_route_pattern = r'(@app\.route\(\'/enhanced_summary\'\).*?return jsonify.*?\n)'
    content = re.sub(last_route_pattern, r'\1' + new_route, content, flags=re.DOTALL)
    
    # 6. Modify the audit completion to save command logs
    audit_completion_pattern = r'(# Generate final summary report.*?)(\s+audit_status = "Completed")'
    
    def replace_audit_completion(match):
        original_code = match.group(1)
        status_line = match.group(2)
        
        logging_completion = '''
        # Save command logs for all devices
        try:
            for device_name in DEVICE_COMMAND_LOGS:
                log_file = save_device_command_log_to_file(device_name)
                if log_file:
                    log_to_ui_and_console(f"[INFO] Saved command log: {os.path.basename(log_file)}")
        except Exception as log_err:
            log_to_ui_and_console(f"[WARNING] Failed to save command logs: {log_err}")
'''
        
        return original_code + logging_completion + status_line
    
    content = re.sub(audit_completion_pattern, replace_audit_completion, content, flags=re.DOTALL)
    
    # Write the modified content back to the file
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully added command logging functionality!")
    return True

if __name__ == "__main__":
    add_command_logging_feature() 
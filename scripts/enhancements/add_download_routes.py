#!/usr/bin/env python3

# This script adds download routes for router configurations

import re

# Read the original file
with open('/root/za-con/rr3-router.py', 'r') as f:
    content = f.read()

# Check if the download routes already exist
if "def download_config(" not in content and "def download_all_configs(" not in content:
    # Define the download routes
    download_routes = """
@app.route('/download_config/<audit_date>/<filename>')
def download_config(audit_date, filename):
    """Download a specific router configuration file"""
    try:
        # Security check to ensure the path is within our report directory
        report_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), BASE_DIR_NAME)
        full_path = os.path.join(report_base_dir, audit_date, filename)
        
        # Prevent path traversal attacks
        if not os.path.normpath(full_path).startswith(os.path.normpath(report_base_dir)):
            return "Invalid file path", 400
        
        if not os.path.exists(full_path):
            return "File not found", 404
        
        # Read the file content
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Create a response with the file content
        response = make_response(content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500

@app.route('/download_all_configs/<router_name>')
def download_all_configs(router_name):
    """Download all configurations for a specific router"""
    try:
        report_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), BASE_DIR_NAME)
        
        # Find all configuration files for this router
        config_files = []
        for audit_dir in sorted(os.listdir(report_base_dir), reverse=True):
            audit_path = os.path.join(report_base_dir, audit_dir)
            if os.path.isdir(audit_path):
                for router_file in os.listdir(audit_path):
                    if (router_file.endswith('.conf') or router_file.endswith('.cfg') or 'running-config' in router_file) and \
                       (router_name in router_file or router_name == os.path.splitext(router_file)[0].replace('-running-config', '')):
                        config_files.append({
                            'audit_date': audit_dir,
                            'filename': router_file,
                            'filepath': os.path.join(audit_path, router_file)
                        })
        
        if not config_files:
            return "No configuration files found for this router", 404
        
        # Create a combined text file with all configurations
        combined_content = ""
        for config in sorted(config_files, key=lambda x: x['audit_date'], reverse=True):
            with open(config['filepath'], 'r') as f:
                file_content = f.read()
            
            combined_content += f"===== {config['filename']} ({config['audit_date']}) =====\\n\\n"
            combined_content += file_content
            combined_content += "\\n\\n" + "="*80 + "\\n\\n"
        
        # Create a response with the combined content
        response = make_response(combined_content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename={router_name}_all_configs.txt'
        
        return response
    except Exception as e:
        return f"Error downloading all configurations: {str(e)}", 500
"""

    # Find the view_config route to insert the download routes after it
    view_config_pattern = r"@app\.route\('/view_config/<audit_date>/<filename>'\)\s+def view_config\(audit_date, filename\):.*?return render_template_string\(HTML_VIEW_CONFIG_TEMPLATE,.*?\)"
    view_config_match = re.search(view_config_pattern, content, re.DOTALL)
    
    if view_config_match:
        # Insert the download routes after the view_config route
        insert_position = view_config_match.end()
        modified_content = content[:insert_position] + download_routes + content[insert_position:]
        
        # Write the modified content back to the file
        with open('/root/za-con/rr3-router.py', 'w') as f:
            f.write(modified_content)
        
        print("Download routes added successfully.")
    else:
        print("Could not find the view_config route to insert download routes after.")
else:
    print("Download routes already exist in the file.")

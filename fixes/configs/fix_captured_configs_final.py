#!/usr/bin/env python3

import os
import re

def fix_captured_configs_route(input_filepath, output_filepath):
    """
    Comprehensive fix for the captured_configs route:
    1. Fixes the JSON serialization error by adding a string version of datetime objects
    2. Adds download functionality for individual router configs and all configs
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
    print("✓ Added last_modified_str field to avoid JSON serialization issues")
    
    # Fix 2: Add download routes for router configurations
    download_routes = """
@app.route('/download_config/<audit_date>/<filename>')
def download_config(audit_date, filename):
    \"\"\"Download a specific router configuration file\"\"\"
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
    \"\"\"Download all configurations for a specific router\"\"\"
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
    
    # Find the position to insert the download routes (after the view_config route)
    view_config_pattern = r"@app\.route\('/view_config/<audit_date>/<filename>'\)\s+def view_config\(audit_date, filename\):.*?return render_template_string\(HTML_VIEW_CONFIG_TEMPLATE,.*?\)"
    view_config_match = re.search(view_config_pattern, content, re.DOTALL)
    
    if view_config_match:
        insert_position = view_config_match.end()
        content = content[:insert_position] + download_routes + content[insert_position:]
        print("✓ Added download routes for router configurations")
    else:
        print("⚠ Could not find view_config route to insert download routes")
    
    # Fix 3: Update the HTML_CAPTURED_CONFIGS_TEMPLATE to include download buttons
    template_pattern = r"(<td>{{ config\.audit_date }}</td>\s+<td>{{ config\.filename }}</td>\s+<td>{{ \(config\.filesize / 1024\)\|round\(1\) }} KB</td>\s+<td>\s+<a href=\"/view_config/{{ config\.audit_date }}/{{ config\.filename }}\" class=\"btn btn-sm btn-primary\">\s+<i class=\"fas fa-eye\"></i> View\s+</a>\s+</td>)"
    
    template_replacement = r"""<td>{{ config.audit_date }}</td>
                                                <td>{{ config.filename }}</td>
                                                <td>{{ (config.filesize / 1024)|round(1) }} KB</td>
                                                <td>
                                                    <div class="btn-group">
                                                        <a href="/view_config/{{ config.audit_date }}/{{ config.filename }}" class="btn btn-sm btn-primary">
                                                            <i class="fas fa-eye"></i> View
                                                        </a>
                                                        <a href="/download_config/{{ config.audit_date }}/{{ config.filename }}" class="btn btn-sm btn-success">
                                                            <i class="fas fa-download"></i> Download
                                                        </a>
                                                    </div>
                                                </td>"""
    
    content = re.sub(template_pattern, template_replacement, content, flags=re.DOTALL)
    
    # Fix 4: Add "Download All Configs" button for each router
    router_section_pattern = r"(<div id=\"collapse{{ loop\.index }}\" class=\"collapse {% if loop\.first %}show{% endif %}\" aria-labelledby=\"heading{{ loop\.index }}\" data-parent=\"#routerConfigsAccordion\">\s+<div class=\"card-body\">)"
    
    router_section_replacement = r"""\1
                            <div class="mb-3">
                                <a href="/download_all_configs/{{ router_name }}" class="btn btn-success">
                                    <i class="fas fa-download"></i> Download All {{ router_name }} Configs
                                </a>
                            </div>"""
    
    content = re.sub(router_section_pattern, router_section_replacement, content, flags=re.DOTALL)
    print("✓ Updated HTML template to include download buttons")
    
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
    output_file = "/root/za-con/rr3-router.py.fixed_final"
    
    if fix_captured_configs_route(input_file, output_file):
        print(f"Captured configs route fixes applied. Modified file saved as: {output_file}")
        print("Please review the changes in the new file.")
        print(f"If satisfied, you can replace the original file by running: mv {output_file} {input_file}")
    else:
        print("Failed to apply captured configs route fixes.")

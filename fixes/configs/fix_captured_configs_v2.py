#!/usr/bin/env python3

import os
import re

def fix_captured_configs_route(input_filepath, output_filepath):
    """
    Fixes the JSON serialization error in the captured_configs route and adds download options.
    
    The fix:
    1. Converts datetime objects to strings before JSON serialization
    2. Adds download options for individual router configs and all configs
    3. Updates the HTML template to include download buttons
    """
    print(f"Reading from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return False

    # Fix 1: Update the captured_configs route to convert datetime objects to strings
    captured_configs_pattern = r"(def captured_configs\(\).*?return render_template_string\(HTML_CAPTURED_CONFIGS_TEMPLATE,\s+router_configs=router_configs,\s+sorted_router_names=sorted_router_names,.*?APP_PORT=APP_CONFIG\.get\('PORT', 5007\)\))"
    
    captured_configs_replacement = '''def captured_configs():
    """Display captured configurations for each router"""
    global APP_CONFIG, current_audit_progress, audit_status, last_run_summary_data
    
    report_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), BASE_DIR_NAME)
    config_files = []
    
    # Find all configuration files from past audits
    try:
        # Check if the reports directory exists
        if os.path.exists(report_base_dir):
            # Get a list of subdirectories (audit timestamps)
            for audit_dir in sorted(os.listdir(report_base_dir), reverse=True):
                audit_path = os.path.join(report_base_dir, audit_dir)
                if os.path.isdir(audit_path):
                    # Scan for router config files in this audit
                    for router_file in os.listdir(audit_path):
                        if router_file.endswith('.conf') or router_file.endswith('.cfg') or 'running-config' in router_file:
                            router_name = os.path.splitext(router_file)[0]
                            router_name = router_name.replace('-running-config', '')
                            
                            # Get file stats
                            file_path = os.path.join(audit_path, router_file)
                            file_size = os.path.getsize(file_path)
                            last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                            
                            # Add to the list of config files
                            config_files.append({
                                'router_name': router_name,
                                'audit_date': audit_dir,
                                'filename': router_file,
                                'filepath': file_path,
                                'filesize': file_size,
                                'last_modified': last_modified,
                                # Convert datetime to string to avoid JSON serialization issues
                                'last_modified_str': last_modified.strftime('%Y-%m-%d %H:%M:%S')
                            })
    except Exception as e:
        print(f"Error scanning for config files: {e}")
        
    # Group config files by router name
    router_configs = {}
    for config in config_files:
        router_name = config['router_name']
        if router_name not in router_configs:
            router_configs[router_name] = []
        router_configs[router_name].append(config)
    
    # Sort each router's configs by date
    for router_name in router_configs:
        router_configs[router_name] = sorted(router_configs[router_name], 
                                           key=lambda x: x['last_modified'], 
                                           reverse=True)
    
    # Sort routers alphabetically
    sorted_router_names = sorted(router_configs.keys())
    
    return render_template_string(HTML_CAPTURED_CONFIGS_TEMPLATE, 
                          router_configs=router_configs,
                          sorted_router_names=sorted_router_names,
                          current_audit_progress=current_audit_progress,
                          audit_status=audit_status,
                          last_run_summary=last_run_summary_data,
                          APP_PORT=APP_CONFIG.get('PORT', 5007))'''
    
    content = re.sub(captured_configs_pattern, captured_configs_replacement, content, flags=re.DOTALL)
    print("✓ Updated captured_configs route to handle datetime objects")
    
    # Fix 2: Add download routes for router configurations
    download_routes_code = '''
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
'''
    
    # Find the position to insert the download routes (after the view_config route)
    view_config_pattern = r"@app\.route\('/view_config/<audit_date>/<filename>'\)\s+def view_config\(audit_date, filename\):.*?return render_template_string\(HTML_VIEW_CONFIG_TEMPLATE,.*?\)"
    view_config_match = re.search(view_config_pattern, content, re.DOTALL)
    
    if view_config_match:
        insert_position = view_config_match.end()
        content = content[:insert_position] + download_routes_code + content[insert_position:]
        print("✓ Added download routes for router configurations")
    else:
        print("⚠ Could not find view_config route to insert download routes")
    
    # Fix 3: Update the HTML_CAPTURED_CONFIGS_TEMPLATE to include download buttons
    html_template_pattern = r"(HTML_CAPTURED_CONFIGS_TEMPLATE = \"\"\".*?<td>\s+<a href=\"/view_config/{{ config\.audit_date }}/{{ config\.filename }}\" class=\"btn btn-sm btn-primary\">\s+<i class=\"fas fa-eye\"></i> View\s+</a>\s+</td>)"
    
    html_template_replacement = '''HTML_CAPTURED_CONFIGS_TEMPLATE = """{% extends "base_layout.html" %}
{% block content %}
<div class="container mt-4">
    <h2><i class="fas fa-file-code"></i> Captured Router Configurations</h2>
    
    <div class="card mb-4">
        <div class="card-header bg-primary text-white">
            <h5><i class="fas fa-info-circle"></i> About Router Configurations</h5>
        </div>
        <div class="card-body">
            <p>This page displays all captured router configurations from previous audit runs. You can view the configuration files for each router and compare changes over time.</p>
        </div>
    </div>
    
    {% if sorted_router_names|length > 0 %}
        <div class="accordion" id="routerConfigsAccordion">
            {% for router_name in sorted_router_names %}
                <div class="card">
                    <div class="card-header" id="heading{{ loop.index }}">
                        <h2 class="mb-0">
                            <button class="btn btn-link btn-block text-left" type="button" data-toggle="collapse" data-target="#collapse{{ loop.index }}" aria-expanded="{% if loop.first %}true{% else %}false{% endif %}" aria-controls="collapse{{ loop.index }}">
                                <i class="fas fa-router mr-2"></i> {{ router_name }}
                                <span class="badge badge-info ml-2">{{ router_configs[router_name]|length }} configs</span>
                            </button>
                        </h2>
                    </div>
                    
                    <div id="collapse{{ loop.index }}" class="collapse {% if loop.first %}show{% endif %}" aria-labelledby="heading{{ loop.index }}" data-parent="#routerConfigsAccordion">
                        <div class="card-body">
                            <div class="mb-3">
                                <a href="/download_all_configs/{{ router_name }}" class="btn btn-success">
                                    <i class="fas fa-download"></i> Download All {{ router_name }} Configs
                                </a>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Filename</th>
                                            <th>Size</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for config in router_configs[router_name] %}
                                            <tr>
                                                <td>{{ config.audit_date }}</td>
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
                                                </td>
                                            </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>
    {% else %}
        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i> No router configurations have been captured yet. Run an audit to collect router configurations.
        </div>
    {% endif %}
</div>
{% endblock %}
"""'''
    
    content = re.sub(html_template_pattern, html_template_replacement, content, flags=re.DOTALL)
    print("✓ Updated HTML template to include download buttons")
    
    # Fix 4: Update the HTML_VIEW_CONFIG_TEMPLATE to include a download button
    view_config_template_pattern = r"(HTML_VIEW_CONFIG_TEMPLATE = \"\"\".*?<button class=\"btn btn-sm btn-outline-light\" id=\"btn-copy-config\">\s+<i class=\"fas fa-copy\"></i> Copy\s+</button>)"
    
    view_config_template_replacement = '''HTML_VIEW_CONFIG_TEMPLATE = """
{% extends "base_layout.html" %}
{% block content %}
<div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2><i class="fas fa-file-code"></i> Router Configuration</h2>
        <a href="/captured_configs" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> Back to All Configs
        </a>
    </div>
    
    <div class="card mb-4">
        <div class="card-header bg-primary text-white">
            <div class="d-flex justify-content-between align-items-center">
                <h5><i class="fas fa-info-circle"></i> Configuration Details</h5>
            </div>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Router:</strong> {{ router_name }}</p>
                    <p><strong>Filename:</strong> {{ filename }}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Last Modified:</strong> {{ last_modified.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                    <p><strong>Size:</strong> {{ (filesize / 1024)|round(1) }} KB</p>
                </div>
            </div>
            <div class="mt-3">
                <a href="/download_config/{{ audit_date }}/{{ filename }}" class="btn btn-success">
                    <i class="fas fa-download"></i> Download Configuration
                </a>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header bg-dark text-white">
            <div class="d-flex justify-content-between align-items-center">
                <h5><i class="fas fa-code"></i> Configuration Content</h5>
                <div>
                    <button class="btn btn-sm btn-outline-light" id="btn-copy-config">
                        <i class="fas fa-copy"></i> Copy
                    </button>'''
    
    content = re.sub(view_config_template_pattern, view_config_template_replacement, content, flags=re.DOTALL)
    print("✓ Updated view config template to include download button")

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
    output_file = "/root/za-con/rr3-router.py.fixed_captured_configs"
    
    if fix_captured_configs_route(input_file, output_file):
        print(f"Captured configs route fixes applied. Modified file saved as: {output_file}")
        print("Please review the changes in the new file.")
        print(f"If satisfied, you can replace the original file by running: mv {output_file} {input_file}")
    else:
        print("Failed to apply captured configs route fixes.")

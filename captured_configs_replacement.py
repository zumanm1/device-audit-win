
@app.route('/captured_configs')
def captured_configs():
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
                            
                            # Add to the list of config files
                            file_path = os.path.join(audit_path, router_file)
                            file_size = os.path.getsize(file_path)
                            last_modified_timestamp = os.path.getmtime(file_path)
                            
                            # Store the timestamp as a string to avoid JSON serialization issues
                            last_modified_str = datetime.fromtimestamp(last_modified_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            
                            config_files.append({
                                'router_name': router_name,
                                'audit_date': audit_dir,
                                'filename': router_file,
                                'filepath': file_path,
                                'filesize': file_size,
                                'last_modified_str': last_modified_str
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
                                           key=lambda x: x['last_modified_str'], 
                                           reverse=True)
    
    # Sort routers alphabetically
    sorted_router_names = sorted(router_configs.keys())
    
    return render_template_string(HTML_CAPTURED_CONFIGS_TEMPLATE, 
                          router_configs=router_configs,
                          sorted_router_names=sorted_router_names,
                          current_audit_progress=current_audit_progress,
                          audit_status=audit_status,
                          last_run_summary=last_run_summary_data,
                          APP_PORT=APP_CONFIG.get('PORT', 5007))

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
                    if (router_file.endswith('.conf') or router_file.endswith('.cfg') or 'running-config' in router_file) and                        (router_name in router_file or router_name == os.path.splitext(router_file)[0].replace('-running-config', '')):
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
            
            combined_content += f"===== {config['filename']} ({config['audit_date']}) =====\n\n"
            combined_content += file_content
            combined_content += "\n\n" + "="*80 + "\n\n"
        
        # Create a response with the combined content
        response = make_response(combined_content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename={router_name}_all_configs.txt'
        
        return response
    except Exception as e:
        return f"Error downloading all configurations: {str(e)}", 500

#!/usr/bin/env python3
"""
Script to add navigation bar to the RR4 router application templates.
"""

import os
import re

def add_navigation_to_templates():
    print("🧭 Adding Navigation Bar to RR4 Router Application...")
    
    # Define the navigation bar HTML
    navigation_html = '''<nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
    <div class="container-fluid">
        <a class="navbar-brand" href="/"><i class="fas fa-network-wired"></i> Router Audit & Terminal Pro</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav me-auto">
                <li class="nav-item">
                    <a class="nav-link" href="/"><i class="fas fa-home"></i> Home</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/settings"><i class="fas fa-cogs"></i> Settings</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/manage_inventories"><i class="fas fa-tasks"></i> Manage Inventories</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/command_logs"><i class="fas fa-terminal"></i> Command Logs</a>
                </li>
            </ul>
            <span class="navbar-text">
                <span class="badge bg-info">Port: {{ port }}</span>
            </span>
        </div>
    </div>
</nav>'''

    # Update the index_page.html template
    template_file = 'templates/index_page.html'
    
    if os.path.exists(template_file):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the h1 header with navigation bar
        header_pattern = r'<div class="container-fluid">\s*<h1 class="text-center mb-4">[^<]*</h1>'
        new_header = f'''<div class="container-fluid">
        {navigation_html}'''
        
        content = re.sub(header_pattern, new_header, content, flags=re.DOTALL)
        
        # Update Bootstrap version to support data-bs-toggle
        content = content.replace('bootstrap@5.1.3', 'bootstrap@5.3.0')
        
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Updated {template_file} with navigation bar")
    
    return True

def create_command_logs_template():
    """Create the command logs template"""
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Command Logs - Router Audit & Terminal Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-card { 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .log-preview {
            max-height: 150px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
            <div class="container-fluid">
                <a class="navbar-brand" href="/"><i class="fas fa-network-wired"></i> Router Audit & Terminal Pro</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/"><i class="fas fa-home"></i> Home</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/settings"><i class="fas fa-cogs"></i> Settings</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/manage_inventories"><i class="fas fa-tasks"></i> Manage Inventories</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link active" href="/command_logs"><i class="fas fa-terminal"></i> Command Logs</a>
                        </li>
                    </ul>
                    <span class="navbar-text">
                        <span class="badge bg-info">Port: {{ port }}</span>
                    </span>
                </div>
            </div>
        </nav>
        
        <h1><i class="fas fa-terminal"></i> Command Logs Management</h1>
        <p class="lead">View and manage router command execution logs</p>
        
        <!-- Summary Cards -->
        <div class="row">
            <div class="col-md-3">
                <div class="card status-card bg-primary text-white">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-file-alt"></i> Total Log Files</h5>
                        <h2>{{ total_files }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card status-card bg-success text-white">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-server"></i> Devices Logged</h5>
                        <h2>{{ current_session_logs.keys()|length }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card status-card bg-info text-white">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-terminal"></i> Commands Executed</h5>
                        <h2>{% set total_commands = 0 %}{% for device in current_session_logs.values() %}{% set total_commands = total_commands + device.summary.total_commands %}{% endfor %}{{ total_commands }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card status-card bg-warning text-dark">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-chart-line"></i> Success Rate</h5>
                        <h2>{% set total_commands = 0 %}{% set successful_commands = 0 %}{% for device in current_session_logs.values() %}{% set total_commands = total_commands + device.summary.total_commands %}{% set successful_commands = successful_commands + device.summary.successful_commands %}{% endfor %}{% if total_commands > 0 %}{{ "%.1f" | format((successful_commands / total_commands * 100)) }}%{% else %}0%{% endif %}</h2>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Current Session Logs -->
        {% if current_session_logs %}
        <div class="row">
            <div class="col-md-12">
                <div class="card status-card">
                    <div class="card-header bg-success text-white">
                        <h5><i class="fas fa-clock"></i> Current Session Logs</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            {% for device_name, device_log in current_session_logs.items() %}
                            <div class="col-md-6 mb-3">
                                <div class="card">
                                    <div class="card-header">
                                        <strong>{{ device_name }}</strong>
                                        <span class="badge {% if device_log.ping_status == 'SUCCESS' %}bg-success{% else %}bg-danger{% endif %} ms-2">
                                            Ping: {{ device_log.ping_status }}
                                        </span>
                                        <span class="badge {% if device_log.ssh_status == 'SUCCESS' %}bg-success{% else %}bg-danger{% endif %}">
                                            SSH: {{ device_log.ssh_status }}
                                        </span>
                                    </div>
                                    <div class="card-body">
                                        <p><strong>Commands:</strong> {{ device_log.summary.total_commands }} 
                                           ({{ device_log.summary.successful_commands }} successful, {{ device_log.summary.failed_commands }} failed)</p>
                                        {% if device_log.commands %}
                                        <h6>Latest Commands:</h6>
                                        <div class="log-preview bg-light p-2 rounded">
                                            {% for cmd in device_log.commands[-3:] %}
                                            <small><strong>[{{ cmd.timestamp }}]</strong> {{ cmd.command }}<br>
                                            <span class="text-muted">{{ cmd.response[:100] }}{% if cmd.response|length > 100 %}...{% endif %}</span><br><br></small>
                                            {% endfor %}
                                        </div>
                                        {% endif %}
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- Saved Log Files -->
        <div class="row">
            <div class="col-md-12">
                <div class="card status-card">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-folder-open"></i> Saved Command Log Files</h5>
                    </div>
                    <div class="card-body">
                        {% if log_files %}
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Device</th>
                                        <th>Filename</th>
                                        <th>Size</th>
                                        <th>Modified</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for log_file in log_files %}
                                    <tr>
                                        <td><strong>{{ log_file.device_name }}</strong></td>
                                        <td>{{ log_file.filename }}</td>
                                        <td>{{ "%.1f" | format(log_file.size / 1024) }} KB</td>
                                        <td>{{ log_file.modified }}</td>
                                        <td>
                                            <a href="{{ url_for('view_command_log', filename=log_file.filename) }}" class="btn btn-sm btn-info">
                                                <i class="fas fa-eye"></i> View
                                            </a>
                                            <a href="{{ url_for('download_command_log', filename=log_file.filename) }}" class="btn btn-sm btn-success">
                                                <i class="fas fa-download"></i> Download
                                            </a>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        {% else %}
                        <div class="text-center text-muted">
                            <i class="fas fa-folder-open fa-3x mb-3"></i>
                            <p>No command log files found. Run an audit to generate logs.</p>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    os.makedirs('templates', exist_ok=True)
    with open('templates/command_logs.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("✅ Created templates/command_logs.html")

def create_view_command_log_template():
    """Create the view command log template"""
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Command Log - Router Audit & Terminal Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .log-content {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            white-space: pre-wrap;
            max-height: 600px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
            <div class="container-fluid">
                <a class="navbar-brand" href="/"><i class="fas fa-network-wired"></i> Router Audit & Terminal Pro</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/"><i class="fas fa-home"></i> Home</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/settings"><i class="fas fa-cogs"></i> Settings</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/manage_inventories"><i class="fas fa-tasks"></i> Manage Inventories</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link active" href="/command_logs"><i class="fas fa-terminal"></i> Command Logs</a>
                        </li>
                    </ul>
                    <span class="navbar-text">
                        <span class="badge bg-info">Port: {{ port }}</span>
                    </span>
                </div>
            </div>
        </nav>
        
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-file-alt"></i> Command Log: {{ filename }}</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <a href="{{ url_for('command_logs_route') }}" class="btn btn-secondary">
                                <i class="fas fa-arrow-left"></i> Back to Command Logs
                            </a>
                            <a href="{{ url_for('download_command_log', filename=filename) }}" class="btn btn-success">
                                <i class="fas fa-download"></i> Download
                            </a>
                        </div>
                        <div class="log-content">{{ log_content }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    with open('templates/view_command_log.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("✅ Created templates/view_command_log.html")

if __name__ == "__main__":
    add_navigation_to_templates()
    create_command_logs_template()
    create_view_command_log_template()
    print("🎉 Navigation bar and command log templates added successfully!") 
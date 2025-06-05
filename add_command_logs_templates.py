#!/usr/bin/env python3
"""
Script to add command logs templates to the main application
"""

import re

def add_command_logs_templates():
    """Add command logs templates to the main application file"""
    
    # Read the main application file
    with open('rr4-router-complete-enhanced-v2.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the command logs templates
    command_logs_template = '''
# Command Logs Templates
HTML_COMMAND_LOGS_TEMPLATE = r"""{% extends "base_layout.html" %}

{% block title %}Command Logs - Router Audit & Terminal Pro{% endblock %}

{% block head_extra %}
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
{% endblock %}

{% block content %}
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
                                <span class="badge {% if device_log.ping_status == 'SUCCESS' %}badge-success{% else %}badge-danger{% endif %} ml-2">
                                    Ping: {{ device_log.ping_status }}
                                </span>
                                <span class="badge {% if device_log.ssh_status == 'SUCCESS' %}badge-success{% else %}badge-danger{% endif %}">
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
{% endblock %}"""

HTML_VIEW_COMMAND_LOG_TEMPLATE = r"""{% extends "base_layout.html" %}

{% block title %}View Command Log - Router Audit & Terminal Pro{% endblock %}

{% block head_extra %}
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
{% endblock %}

{% block content %}
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
{% endblock %}"""
'''
    
    # Find the location to insert the templates (before app.jinja_loader)
    insert_pattern = r'(app\.jinja_loader = DictLoader\(\{)'
    
    if re.search(insert_pattern, content):
        # Insert the templates before the DictLoader
        content = re.sub(insert_pattern, command_logs_template + r'\n\1', content)
        
        # Update the DictLoader to include the new templates
        old_dict_pattern = r'(app\.jinja_loader = DictLoader\(\{\s*TEMPLATE_BASE_NAME: HTML_BASE_LAYOUT, TEMPLATE_INDEX_NAME: HTML_INDEX_PAGE,\s*TEMPLATE_SETTINGS_NAME: HTML_SETTINGS_TEMPLATE_CONTENT, TEMPLATE_VIEW_JSON_NAME: HTML_VIEW_JSON_TEMPLATE_CONTENT,\s*TEMPLATE_EDIT_INVENTORY_NAME: HTML_EDIT_INVENTORY_TEMPLATE_CONTENT\s*\}\))'
        
        new_dict_content = '''app.jinja_loader = DictLoader({
    TEMPLATE_BASE_NAME: HTML_BASE_LAYOUT, TEMPLATE_INDEX_NAME: HTML_INDEX_PAGE,
    TEMPLATE_SETTINGS_NAME: HTML_SETTINGS_TEMPLATE_CONTENT, TEMPLATE_VIEW_JSON_NAME: HTML_VIEW_JSON_TEMPLATE_CONTENT,
    TEMPLATE_EDIT_INVENTORY_NAME: HTML_EDIT_INVENTORY_TEMPLATE_CONTENT,
    "command_logs.html": HTML_COMMAND_LOGS_TEMPLATE, "view_command_log.html": HTML_VIEW_COMMAND_LOG_TEMPLATE
})'''
        
        content = re.sub(old_dict_pattern, new_dict_content, content, flags=re.MULTILINE | re.DOTALL)
        
        # Write the updated content back to the file
        with open('rr4-router-complete-enhanced-v2.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Successfully added command logs templates to the application")
        return True
    else:
        print("❌ Could not find DictLoader pattern in the application file")
        return False

if __name__ == "__main__":
    add_command_logs_templates() 
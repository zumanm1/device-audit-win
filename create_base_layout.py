#!/usr/bin/env python3
"""
Script to create a base layout template with navigation for the router application.
"""

import os
import re

def create_base_layout_template():
    print("🏗️ Creating Base Layout Template...")
    
    base_layout_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Router Audit & Terminal Pro{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-card { 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .audit-log {
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        .device-status-up { color: #28a745; }
        .device-status-down { color: #dc3545; }
        .log-preview {
            max-height: 150px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
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
        {% block extra_styles %}{% endblock %}
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- Navigation Bar -->
        <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
            <div class="container-fluid">
                <a class="navbar-brand" href="/"><i class="fas fa-network-wired"></i> Router Audit & Terminal Pro</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link {% block nav_home %}{% endblock %}" href="/"><i class="fas fa-home"></i> Home</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% block nav_settings %}{% endblock %}" href="/settings"><i class="fas fa-cogs"></i> Settings</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% block nav_inventories %}{% endblock %}" href="/manage_inventories"><i class="fas fa-tasks"></i> Manage Inventories</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% block nav_command_logs %}{% endblock %}" href="/command_logs"><i class="fas fa-terminal"></i> Command Logs</a>
                        </li>
                    </ul>
                    <span class="navbar-text">
                        <span class="badge bg-info">Port: {{ port }}</span>
                    </span>
                </div>
            </div>
        </nav>
        
        <!-- Flash Messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <!-- Main Content -->
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>'''

    os.makedirs('templates', exist_ok=True)
    with open('templates/base_layout.html', 'w', encoding='utf-8') as f:
        f.write(base_layout_content)
    
    print("✅ Created templates/base_layout.html")

def update_embedded_templates():
    print("🔧 Updating embedded templates in the main application...")
    
    app_file = 'rr4-router-complete-enhanced-v2.py'
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update settings template to use new navigation blocks
    settings_template_replacement = '''HTML_SETTINGS_TEMPLATE_CONTENT = """
{% extends "base_layout.html" %}
{% block title %}Settings - Router Audit & Terminal Pro{% endblock %}
{% block nav_settings %}active{% endblock %}
{% block content %}
<h1><i class="fas fa-cogs"></i> Application Settings</h1>
<p class="lead">Configure jump host details, default device credentials, and global inventory settings.</p>

<div class="card mt-4">
    <div class="card-header"><h4><i class="fas fa-server"></i> Jump Host & Device Credentials</h4></div>
    <div class="card-body">
        <form method="POST" action="{{ url_for('settings_route') }}">
            <h5>Jump Host Configuration</h5>
            <div class="row">
                <div class="col-md-6"><label for="jump_host" class="form-label">Jump Host IP/Hostname:</label><input type="text" class="form-control" id="jump_host" name="jump_host" value="{{ config.JUMP_HOST }}"></div>
                <div class="col-md-6"><label for="jump_ping_path" class="form-label">Jump Host Ping Executable Path:</label><input type="text" class="form-control" id="jump_ping_path" name="jump_ping_path" value="{{ config.JUMP_PING_PATH }}" placeholder="e.g., /bin/ping"></div>
            </div>
            <div class="row mt-3">
                <div class="col-md-6"><label for="jump_username" class="form-label">Jump Host Username:</label><input type="text" class="form-control" id="jump_username" name="jump_username" value="{{ config.JUMP_USERNAME }}"></div>
                <div class="col-md-6"><label for="jump_password" class="form-label">Jump Host Password:</label><input type="password" class="form-control" id="jump_password" name="jump_password" placeholder="Leave blank to keep current"><small class="form-text text-muted">Passwords stored in .env file.</small></div>
            </div>
            <hr>
            <h5>Default Device Credentials (used if not in inventory)</h5>
            <div class="row">
                <div class="col-md-4"><label for="device_username" class="form-label">Default Device Username:</label><input type="text" class="form-control" id="device_username" name="device_username" value="{{ config.DEVICE_USERNAME }}"></div>
                <div class="col-md-4"><label for="device_password" class="form-label">Default Device Password:</label><input type="password" class="form-control" id="device_password" name="device_password" placeholder="Leave blank to keep current"></div>
                <div class="col-md-4"><label for="device_enable_password" class="form-label">Default Device Enable Password:</label><input type="password" class="form-control" id="device_enable_password" name="device_enable_password" placeholder="Leave blank or empty to clear"></div>
            </div>
            <hr>
             <h5>Global Inventory Settings</h5>
             <div class="mb-3">
                <label class="form-label">Inventory Format:</label>
                <p class="form-control-static">CSV (.csv) <small class="text-muted">- The application now exclusively uses CSV format for inventories</small></p>
            </div>
            <button type="submit" class="btn btn-primary mt-3"><i class="fas fa-save"></i> Save All Settings</button>
        </form>
    </div>
</div>
{% endblock %}
"""'''

    # Update inventory template to use new navigation blocks
    inventory_template_replacement = '''HTML_EDIT_INVENTORY_TEMPLATE_CONTENT = """
{% extends "base_layout.html" %}
{% block title %}Manage Inventories{% endblock %}
{% block nav_inventories %}active{% endblock %}
{% block content %}
<h1><i class="fas fa-tasks"></i> Manage Inventory Files</h1>
<p class="lead">Upload new inventory files (YAML or CSV), select an existing file to be active, edit content, or export the current active inventory to CSV.</p>

<div class="card mt-4">
    <div class="card-header"><h4><i class="fas fa-list-alt"></i> Active Inventory & Available Files</h4></div>
    <div class="card-body">
        <form method="POST" action="{{ url_for('manage_inventories_route') }}">
            <input type="hidden" name="action" value="set_active">
            <div class="row align-items-end">
                <div class="col-md-8">
                    <label for="active_inventory_file_manage" class="form-label"><strong>Current Active Inventory:</strong> {{ active_inventory }} (Format: {{ active_inventory_format.upper() }})</label>
                    <br>
                    <label for="active_inventory_file_manage" class="form-label">Select an inventory file to make active:</label>
                    <select class="form-control" id="active_inventory_file_manage" name="active_inventory_file_manage">
                        {% for inv_file in inventories %}
                        <option value="{{ inv_file }}" {% if inv_file == active_inventory %}selected{% endif %}>{{ inv_file }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-4">
                     <button type="submit" class="btn btn-info w-100"><i class="fas fa-check-circle"></i> Set as Active</button>
                </div>
            </div>
        </form>
        <hr>
        <a href="{{ url_for('export_inventory_csv_route') }}" class="btn btn-success mt-2"><i class="fas fa-file-csv"></i> Export Current Active Inventory to CSV</a>
    </div>
</div>

<div class="card mt-4">
    <div class="card-header"><h4><i class="fas fa-upload"></i> Upload New Inventory File</h4></div>
    <div class="card-body">
        <form method="POST" action="{{ url_for('manage_inventories_route') }}" enctype="multipart/form-data">
            <input type="hidden" name="action" value="upload">
            <div class="mb-3">
                <label for="inventory_file_upload_manage" class="form-label">Upload CSV (.csv) inventory file:</label>
                <input type="file" class="form-control" id="inventory_file_upload_manage" name="inventory_file_upload_manage" accept=".csv">
                <small class="form-text text-muted">
                    File will be validated and versioned (e.g., inventory-list-v01.csv). 
                    If valid, it will be set as active.
                </small>
            </div>
            <button type="submit" class="btn btn-success"><i class="fas fa-cloud-upload-alt"></i> Upload and Set Active</button>
        </form>
    </div>
</div>

<div class="card mt-4">
    <div class="card-header">
        <h4><i class="fas fa-file-alt"></i> Edit Current Active Inventory ({{ active_inventory }} - CSV)</h4>
    </div>
    <div class="card-body">
        <ul class="nav nav-tabs" id="editorTabs" role="tablist">
            <li class="nav-item">
                <a class="nav-link active" id="csv-tab" data-bs-toggle="tab" href="#csv-editor" role="tab" aria-controls="csv-editor" aria-selected="true">Table View</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="raw-tab" data-bs-toggle="tab" href="#raw-editor" role="tab" aria-controls="raw-editor" aria-selected="false">Raw CSV</a>
            </li>
        </ul>
        
        <div class="tab-content" id="editorTabsContent">
            <!-- CSV Table Editor Tab -->
            <div class="tab-pane fade show active" id="csv-editor" role="tabpanel" aria-labelledby="csv-tab">
                <form id="csvTableForm" method="POST" action="{{ url_for('edit_active_inventory_content_route') }}">
                    <input type="hidden" name="inventory_content_edit" id="csv-data-hidden">
                    
                    <div class="table-responsive mt-3">
                        <table class="table table-bordered table-hover" id="csvTable">
                            <thead id="csvTableHeader">
                                <!-- Headers will be populated by JavaScript -->
                            </thead>
                            <tbody id="csvTableBody">
                                <!-- Rows will be populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="btn-toolbar mb-3">
                        <div class="btn-group me-2">
                            <button type="button" class="btn btn-sm btn-success" id="addRowBtn"><i class="fas fa-plus-circle"></i> Add Row</button>
                            <button type="button" class="btn btn-sm btn-warning" id="addColumnBtn"><i class="fas fa-columns"></i> Add Column</button>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary mt-3"><i class="fas fa-save"></i> Save Changes</button>
                    <a href="{{ url_for('index') }}" class="btn btn-secondary mt-3">Cancel</a>
                </form>
            </div>
            
            <!-- Raw CSV Editor Tab -->
            <div class="tab-pane fade" id="raw-editor" role="tabpanel" aria-labelledby="raw-tab">
                <form method="POST" action="{{ url_for('edit_active_inventory_content_route') }}">
                    <div class="mb-3 mt-3">
                        <textarea class="form-control" id="raw_inventory_content_edit" name="inventory_content_edit" rows="20" placeholder="Loading CSV content...">{{ current_inventory_content_raw }}</textarea>
                        <small class="form-text text-muted">CSV format with header row. Changes will be saved as a new CSV version.</small>
                    </div>
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Save Changes</button>
                    <a href="{{ url_for('index') }}" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block extra_scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Parse the raw CSV data into an array of arrays
    const csvData = parseCSV('{{ current_inventory_content_raw|replace("\\n", "\\\\n")|replace("'", "\\\\'") | safe }}');
    
    // Populate the CSV table
    populateCSVTable(csvData);
    
    // Add event listeners for the buttons
    document.getElementById('addRowBtn').addEventListener('click', addRow);
    document.getElementById('addColumnBtn').addEventListener('click', addColumn);
    
    // Add event listener to the form to prepare the CSV data before submission
    document.getElementById('csvTableForm').addEventListener('submit', function(e) {
        prepareCSVData();
    });
});

// Parse CSV string into array of arrays
function parseCSV(csvString) {
    // Simple parser for well-formed CSV
    const lines = csvString.trim().split('\\\\n');
    const result = [];
    
    for (let i = 0; i < lines.length; i++) {
        // Handle line with quoted fields correctly
        const row = [];
        let inQuote = false;
        let currentValue = '';
        
        for (let j = 0; j < lines[i].length; j++) {
            const char = lines[i][j];
            
            if (char === '"' && (j === 0 || lines[i][j-1] !== '\\\\')) {
                inQuote = !inQuote;
            } else if (char === ',' && !inQuote) {
                row.push(currentValue);
                currentValue = '';
            } else {
                currentValue += char;
            }
        }
        
        row.push(currentValue); // Add the last field
        result.push(row);
    }
    
    return result;
}

// Populate the CSV table with data
function populateCSVTable(csvData) {
    const header = document.getElementById('csvTableHeader');
    const body = document.getElementById('csvTableBody');
    
    // Clear existing content
    header.innerHTML = '';
    body.innerHTML = '';
    
    if (csvData.length === 0) return;
    
    // Create header row
    const headerRow = document.createElement('tr');
    csvData[0].forEach((headerText, index) => {
        const th = document.createElement('th');
        th.textContent = headerText;
        th.innerHTML += '<button type="button" class="btn btn-sm btn-danger ms-2 delete-column" data-column="' + index + '"><i class="fas fa-times"></i></button>';
        headerRow.appendChild(th);
    });
    // Add action column
    const actionTh = document.createElement('th');
    actionTh.textContent = 'Actions';
    headerRow.appendChild(actionTh);
    header.appendChild(headerRow);
    
    // Create data rows
    for (let i = 1; i < csvData.length; i++) {
        const row = document.createElement('tr');
        csvData[i].forEach((cellData, index) => {
            const td = document.createElement('td');
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control form-control-sm';
            input.value = cellData;
            input.dataset.row = i;
            input.dataset.col = index;
            td.appendChild(input);
            row.appendChild(td);
        });
        
        // Add delete button
        const actionTd = document.createElement('td');
        actionTd.innerHTML = '<button type="button" class="btn btn-sm btn-danger delete-row" data-row="' + i + '"><i class="fas fa-trash"></i></button>';
        row.appendChild(actionTd);
        body.appendChild(row);
    }
    
    // Add event listeners for delete buttons
    document.querySelectorAll('.delete-row').forEach(btn => {
        btn.addEventListener('click', deleteRow);
    });
    document.querySelectorAll('.delete-column').forEach(btn => {
        btn.addEventListener('click', deleteColumn);
    });
}

function addRow() {
    const table = document.getElementById('csvTable');
    const tbody = table.querySelector('tbody');
    const headerCount = table.querySelector('thead tr').children.length - 1; // Subtract action column
    
    const newRow = document.createElement('tr');
    for (let i = 0; i < headerCount; i++) {
        const td = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control form-control-sm';
        input.dataset.row = tbody.children.length + 1;
        input.dataset.col = i;
        td.appendChild(input);
        newRow.appendChild(td);
    }
    
    // Add delete button
    const actionTd = document.createElement('td');
    actionTd.innerHTML = '<button type="button" class="btn btn-sm btn-danger delete-row" data-row="' + (tbody.children.length + 1) + '"><i class="fas fa-trash"></i></button>';
    newRow.appendChild(actionTd);
    tbody.appendChild(newRow);
    
    // Re-attach event listeners
    newRow.querySelector('.delete-row').addEventListener('click', deleteRow);
}

function addColumn() {
    const headerName = prompt('Enter column header name:');
    if (!headerName) return;
    
    const table = document.getElementById('csvTable');
    const headerRow = table.querySelector('thead tr');
    const rows = table.querySelectorAll('tbody tr');
    
    // Add header
    const newTh = document.createElement('th');
    newTh.textContent = headerName;
    newTh.innerHTML += '<button type="button" class="btn btn-sm btn-danger ms-2 delete-column" data-column="' + (headerRow.children.length - 1) + '"><i class="fas fa-times"></i></button>';
    headerRow.insertBefore(newTh, headerRow.lastElementChild);
    
    // Add empty cells to existing rows
    rows.forEach((row, rowIndex) => {
        const newTd = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control form-control-sm';
        input.dataset.row = rowIndex + 1;
        input.dataset.col = headerRow.children.length - 2;
        newTd.appendChild(input);
        row.insertBefore(newTd, row.lastElementChild);
    });
    
    // Re-attach event listeners
    newTh.querySelector('.delete-column').addEventListener('click', deleteColumn);
}

function deleteRow(event) {
    if (confirm('Are you sure you want to delete this row?')) {
        event.target.closest('tr').remove();
    }
}

function deleteColumn(event) {
    const columnIndex = parseInt(event.target.closest('button').dataset.column);
    if (confirm('Are you sure you want to delete this column?')) {
        const table = document.getElementById('csvTable');
        
        // Remove header
        table.querySelector('thead tr').children[columnIndex].remove();
        
        // Remove cells from all rows
        table.querySelectorAll('tbody tr').forEach(row => {
            if (row.children[columnIndex]) {
                row.children[columnIndex].remove();
            }
        });
    }
}

function prepareCSVData() {
    const table = document.getElementById('csvTable');
    const rows = [];
    
    // Get headers
    const headerRow = [];
    table.querySelectorAll('thead th').forEach((th, index) => {
        if (index < table.querySelectorAll('thead th').length - 1) { // Skip action column
            headerRow.push(th.textContent.replace(/\\\\s*×\\\\s*$/, '').trim()); // Remove delete button text
        }
    });
    rows.push(headerRow);
    
    // Get data rows
    table.querySelectorAll('tbody tr').forEach(row => {
        const dataRow = [];
        row.querySelectorAll('input').forEach(input => {
            dataRow.push(input.value);
        });
        if (dataRow.length > 0) {
            rows.push(dataRow);
        }
    });
    
    // Convert to CSV string
    const csvString = rows.map(row => 
        row.map(cell => 
            cell.includes(',') || cell.includes('"') || cell.includes('\\\\n') 
                ? '"' + cell.replace(/"/g, '""') + '"' 
                : cell
        ).join(',')
    ).join('\\\\n');
    
    document.getElementById('csv-data-hidden').value = csvString;
}
</script>
{% endblock %}
"""'''

    # Replace the templates in the content
    content = re.sub(r'HTML_SETTINGS_TEMPLATE_CONTENT = """.*?"""', settings_template_replacement, content, flags=re.DOTALL)
    content = re.sub(r'HTML_EDIT_INVENTORY_TEMPLATE_CONTENT = """.*?"""', inventory_template_replacement, content, flags=re.DOTALL)
    
    # Write the updated content back
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated embedded templates with navigation")

def update_index_template():
    print("🏠 Updating index template...")
    
    # Update index_page.html to extend base layout
    index_template_content = '''{% extends "base_layout.html" %}
{% block title %}Network Audit Dashboard - Router Audit & Terminal Pro{% endblock %}
{% block nav_home %}active{% endblock %}
{% block content %}
        
        <!-- Enhanced Status Cards -->
        <div class="row">
            <div class="col-md-3">
                <div class="card status-card bg-primary text-white">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-server"></i> Total Devices</h5>
                        <h2>{{ device_summary.total_devices }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card status-card bg-success text-white">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-check-circle"></i> UP Devices</h5>
                        <h2>{{ device_summary.up_devices }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card status-card bg-danger text-white">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-times-circle"></i> DOWN Devices</h5>
                        <h2>{{ device_summary.down_devices }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card status-card bg-info text-white">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-chart-line"></i> Success Rate</h5>
                        <h2>{% if device_summary.total_devices > 0 %}{{ "%.1f" | format((device_summary.up_devices / device_summary.total_devices * 100)) }}%{% else %}0%{% endif %}</h2>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Device Status Details -->
        <div class="row">
            <div class="col-md-6">
                <div class="card status-card">
                    <div class="card-header bg-success text-white">
                        <h5><i class="fas fa-check"></i> Operational Devices</h5>
                    </div>
                    <div class="card-body">
                        {% if device_summary.up_device_list %}
                            {% for device in device_summary.up_device_list %}
                                <span class="badge bg-success me-2 mb-2">
                                    <i class="fas fa-circle device-status-up"></i> {{ device }}
                                </span>
                            {% endfor %}
                        {% else %}
                            <p class="text-muted">No devices are currently operational.</p>
                        {% endif %}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card status-card">
                    <div class="card-header bg-danger text-white">
                        <h5><i class="fas fa-exclamation-triangle"></i> Down Devices</h5>
                    </div>
                    <div class="card-body">
                        {% if device_summary.down_device_list %}
                            {% for device in device_summary.down_device_list %}
                                <span class="badge bg-danger me-2 mb-2">
                                    <i class="fas fa-circle device-status-down"></i> {{ device }}
                                </span>
                            {% endfor %}
                        {% else %}
                            <p class="text-success">All devices are operational! 🎉</p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Audit Controls -->
        <div class="row">
            <div class="col-md-12">
                <div class="card status-card">
                    <div class="card-header">
                        <h5><i class="fas fa-play-circle"></i> Audit Controls</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Status:</strong> 
                            <span class="badge {% if audit_status == 'Completed' %}bg-success{% elif audit_status == 'Running' %}bg-warning{% else %}bg-secondary{% endif %}">
                                {{ audit_status }}
                            </span>
                        </p>
                        <p><strong>Active Inventory:</strong> {{ active_inventory_file }}</p>
                        
                        <form method="POST" action="{{ url_for('start_audit_route') }}" class="d-inline">
                            <button type="submit" class="btn btn-primary" {% if audit_status == 'Running' %}disabled{% endif %}>
                                <i class="fas fa-play"></i> Run Audit
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Audit Logs -->
        <div class="row">
            <div class="col-md-12">
                <div class="card status-card">
                    <div class="card-header">
                        <h5><i class="fas fa-terminal"></i> Audit Logs</h5>
                    </div>
                    <div class="card-body">
                        <div class="audit-log bg-dark text-light p-3 rounded">
                            {% for log in logs %}
                                <div>{{ log }}</div>
                            {% else %}
                                <div class="text-muted">No logs available. Start an audit to see real-time logs.</div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
{% endblock %}
{% block extra_scripts %}
    <script>
        // Auto-refresh every 5 seconds during audit
        {% if audit_status == 'Running' %}
        setTimeout(function() {
            location.reload();
        }, 5000);
        {% endif %}
    </script>
{% endblock %}'''

    with open('templates/index_page.html', 'w', encoding='utf-8') as f:
        f.write(index_template_content)
    
    print("✅ Updated templates/index_page.html")

if __name__ == "__main__":
    create_base_layout_template()
    update_embedded_templates()
    update_index_template()
    print("🎉 Base layout with navigation successfully created!") 
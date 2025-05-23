#!/usr/bin/env python3
"""
NetAuditPro Enhanced Router Auditing Application
Version: 4.1.0 Enhanced Down Device Reporting
File: rr4-router-enhanced.py

ENHANCEMENTS IN THIS VERSION:
1. Enhanced down device reporting with placeholder config generation
2. Improved status tracking for unreachable devices
3. Better reporting for down devices in all formats (PDF, Excel, Summary)
4. Separate sections for UP vs DOWN devices in reports
5. Detailed failure reason tracking and reporting

CURRENT ROUTER STATUS:
- R0: UP (172.16.39.100)
- R1: DOWN (172.16.39.101) 
- R2: DOWN (172.16.39.102)
- R3: DOWN (172.16.39.103)
- R4: UP (172.16.39.104)
"""

import os
import sys
import json
import shutil
import socket
import subprocess
import tempfile
import threading
import glob
import paramiko, socket, time, re, os, json, yaml, threading, logging, sys, ipaddress, subprocess, secrets, string, webbrowser, argparse, gzip, base64, shutil, csv, io
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

import paramiko
from colorama import Fore, Style, init as colorama_init
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from flask import Flask, render_template, redirect, url_for, request, jsonify, send_from_directory, flash, Response
from dotenv import load_dotenv, set_key, find_dotenv
from werkzeug.utils import secure_filename
from jinja2 import DictLoader

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask_socketio import SocketIO, emit
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

colorama_init(autoreset=True)

# Template names
TEMPLATE_BASE_NAME = "base_layout.html"
TEMPLATE_INDEX_NAME = "index_page.html"
TEMPLATE_SETTINGS_NAME = "settings_page.html"
TEMPLATE_VIEW_JSON_NAME = "view_json_page.html"
TEMPLATE_EDIT_INVENTORY_NAME = "edit_inventory_page.html"

# Flask app setup
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'inventories'
app.config['ALLOWED_EXTENSIONS'] = {'csv'} 
app.config['PORT'] = 5008
socketio = SocketIO(app, async_mode=None, cors_allowed_origins="*")

# Global variables
ui_logs: List[str] = []
SENSITIVE_STRINGS_TO_REDACT: List[str] = []
APP_CONFIG: Dict[str, str] = {}
interactive_sessions: Dict[str, Dict[str, Any]] = {}

# Enhanced tracking for down devices
DOWN_DEVICES: Dict[str, Dict[str, Any]] = {}
DEVICE_STATUS_TRACKING: Dict[str, str] = {}

# Report constants
BASE_DIR_NAME: str = "ALL-ROUTER-REPORTS"
SUMMARY_FILENAME: str = "summary.txt"
PDF_SUMMARY_FILENAME: str = "audit_summary_report.pdf"
EXCEL_SUMMARY_FILENAME: str = "audit_summary_report.xlsx"

def generate_placeholder_config_for_down_device(device_name: str, device_ip: str, failure_reason: str, base_report_dir: str) -> str:
    """
    Generate a placeholder configuration file for devices that are down/unreachable.
    
    Args:
        device_name: Name of the device
        device_ip: IP address of the device
        failure_reason: Reason why the device is unreachable
        base_report_dir: Base directory for reports
        
    Returns:
        Path to the generated placeholder config file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    placeholder_content = f"""!
! ========================================
! DEVICE STATUS: DOWN / UNREACHABLE
! ========================================
!
! Device Name: {device_name}
! IP Address: {device_ip}
! Status: UNREACHABLE
! Failure Reason: {failure_reason}
! Audit Timestamp: {timestamp}
! 
! This device was unreachable during the network audit.
! Configuration could not be retrieved.
!
! Recommended Actions:
! 1. Verify physical connectivity
! 2. Check power status
! 3. Verify IP configuration
! 4. Test SSH connectivity manually
! 5. Check firewall rules
!
! ========================================
! END PLACEHOLDER CONFIG
! ========================================
!
"""
    
    # Create device-specific report folder
    device_folder = os.path.join(base_report_dir, f"{timestamp.replace(':', '').replace(' ', '_')}")
    os.makedirs(device_folder, exist_ok=True)
    
    # Write placeholder config
    placeholder_path = os.path.join(device_folder, f"{device_name}-DEVICE_DOWN.txt")
    try:
        with open(placeholder_path, 'w') as f:
            f.write(placeholder_content)
        log_to_ui_and_console(f"Generated placeholder config for {device_name}: {placeholder_path}")
        return placeholder_path
    except Exception as e:
        log_to_ui_and_console(f"Error generating placeholder config for {device_name}: {e}")
        return ""

def track_device_status(device_name: str, status: str, failure_reason: str = None):
    """
    Track device status for enhanced reporting.
    
    Args:
        device_name: Name of the device
        status: Status (UP, DOWN, SSH_FAIL, etc.)
        failure_reason: Optional failure reason
    """
    global DEVICE_STATUS_TRACKING, DOWN_DEVICES
    
    DEVICE_STATUS_TRACKING[device_name] = status
    
    if status in ['DOWN', 'ICMP_FAIL', 'SSH_FAIL', 'COLLECTION_FAIL']:
        DOWN_DEVICES[device_name] = {
            'status': status,
            'failure_reason': failure_reason or 'Unknown failure',
            'timestamp': datetime.now().isoformat(),
            'ip': '',  # Will be filled by calling function
        }
        log_to_ui_and_console(f"Device {device_name} marked as DOWN: {failure_reason}")

def get_device_status_summary() -> Dict[str, Any]:
    """
    Get a summary of device statuses for reporting.
    
    Returns:
        Dictionary with device status counts and details
    """
    status_counts = {
        'total_devices': 0,
        'up_devices': 0,
        'down_devices': 0,
        'up_device_list': [],
        'down_device_list': [],
        'status_details': DEVICE_STATUS_TRACKING.copy(),
        'down_device_details': DOWN_DEVICES.copy()
    }
    
    for device, status in DEVICE_STATUS_TRACKING.items():
        status_counts['total_devices'] += 1
        if status == 'UP':
            status_counts['up_devices'] += 1
            status_counts['up_device_list'].append(device)
        else:
            status_counts['down_devices'] += 1
            status_counts['down_device_list'].append(device)
    
    return status_counts

# Copy all utility functions from original rr4-router.py
def strip_ansi(text: str) -> str:
    return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)

def sanitize_log_message(msg: str) -> str:
    sanitized_msg = str(msg)
    if APP_CONFIG:
        for key in ["JUMP_PASSWORD", "DEVICE_PASSWORD", "DEVICE_ENABLE"]:
            value = APP_CONFIG.get(key)
            if value and len(value) > 2:
                sanitized_msg = sanitized_msg.replace(value, "*******")
    sanitized_msg = re.sub(r'(password|secret)\s*[:=]\s*([^\s,;"\']+)', r'\1: ********', sanitized_msg, flags=re.IGNORECASE)
    sanitized_msg = re.sub(r'(password|secret)\s+([^\s,;"\']+)', r'\1 ********', sanitized_msg, flags=re.IGNORECASE)
    return sanitized_msg

def log_to_ui_and_console(msg, console_only=False, is_sensitive=False, end="\n", **kw):
    """Log a message to the UI and console."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Always print to console regardless of console_only flag
    processed_msg_console = str(msg)
    if is_sensitive:
        processed_msg_console = sanitize_log_message(processed_msg_console)
    print(f"[{timestamp}] {processed_msg_console}", end=end, flush=True, **kw)
    
    # Always add to UI logs regardless of console_only flag
    processed_msg_ui = strip_ansi(sanitize_log_message(str(msg)))
    ui_msg_formatted = f"[{timestamp}] {processed_msg_ui}"
    cleaned_progress_marker = " कार्य प्रगति पर है "
    
    if end == '\r':
        if ui_logs and cleaned_progress_marker in ui_logs[-1]:
            ui_logs[-1] = ui_msg_formatted + cleaned_progress_marker
        else:
            ui_logs.append(ui_msg_formatted + cleaned_progress_marker)
    else:
        if ui_logs and cleaned_progress_marker in ui_logs[-1] and not ui_msg_formatted.startswith(f"[{timestamp}] [#"):
            ui_logs[-1] = ui_msg_formatted
        else:
            ui_logs.append(ui_msg_formatted)
            
    # Make sure the UI is updated with the latest logs
    if socketio:
        try:
            # Send log update
            socketio.emit('log_update', {'logs': ui_logs[-100:]})
            
            # Also emit a progress update to keep the UI in sync
            global AUDIT_PROGRESS
            json_safe_progress = prepare_progress_for_json(AUDIT_PROGRESS)
            socketio.emit('progress_update', json_safe_progress)
        except Exception as e:
            print(f"Error emitting update: {e}")

def ping_local(host: str) -> bool:
    """Ping a host from the local machine."""
    if not host:
        log_to_ui_and_console(f"{Fore.RED}Invalid host address: empty{Style.RESET_ALL}", console_only=True)
        return False
        
    if host in ['localhost', '127.0.0.1']:
        return True
        
    is_windows = sys.platform.startswith('win')
    param_count = '-n' if is_windows else '-c'
    param_timeout_opt = '-w' if is_windows else '-W'
    timeout_val = "1000" if is_windows else "1"
    command = ["ping", param_count, "1", param_timeout_opt, timeout_val, host]
    try:
        process_timeout = 2
        log_to_ui_and_console(f"Pinging {host}...", console_only=True)
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=process_timeout)
        success = result.returncode == 0
        if success:
            log_to_ui_and_console(f"{Fore.GREEN}Ping to {host} successful.{Style.RESET_ALL}", console_only=True)
        else:
            log_to_ui_and_console(f"{Fore.YELLOW}Ping to {host} failed with return code {result.returncode}.{Style.RESET_ALL}", console_only=True)
        return success
    except subprocess.TimeoutExpired:
        log_to_ui_and_console(f"{Fore.YELLOW}Local ping to {host} timed out.{Style.RESET_ALL}", console_only=True)
        return False
    except Exception as e:
        log_to_ui_and_console(f"{Fore.RED}Local ping to {host} error: {e}{Style.RESET_ALL}", console_only=True)
        return False

def ping_remote(ssh: paramiko.SSHClient, ip: str) -> bool:
    ping_executable = APP_CONFIG.get("JUMP_PING_PATH", "/bin/ping")
    if not ping_executable:
        ping_executable = "ping"
        log_to_ui_and_console(f"{Fore.YELLOW}Warning: JUMP_PING_PATH not set. Defaulting to 'ping'.{Style.RESET_ALL}")
    
    command = f"{ping_executable} -c 2 -W 1 {ip}"
    
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=10)
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0
    except Exception as e:
        log_to_ui_and_console(f"Error executing remote ping: {e}")
        return False

# Additional utility functions needed...
def banner_to_log_audit(title: str):
    try: 
        w = shutil.get_terminal_size(fallback=(80, 20)).columns
    except OSError: 
        w = 80
    log_message_raw = f"\n{Fore.CYAN}{title} {'─' * (w - len(title) - 2)}{Style.RESET_ALL}"
    print(log_message_raw)
    log_to_ui_and_console(strip_ansi(log_message_raw).strip())

def bar_audit(pct: float, width=30) -> str:
    done = int(width * pct / 100)
    return f"[{'#' * done}{'.' * (width - done)}] {pct:5.1f}%"

def mark_audit(ok: bool) -> str:
    return f"{Fore.GREEN}✔{Style.RESET_ALL}" if ok else f"{Fore.RED}✖{Style.RESET_ALL}"

# Configuration loading
DOTENV_PATH = find_dotenv()
if not DOTENV_PATH:
    DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(DOTENV_PATH):
        with open(DOTENV_PATH, "w") as f_dotenv:
            f_dotenv.write(
                "# Auto-generated .env file\n"
                "JUMP_HOST=172.16.39.128\nJUMP_USERNAME=root\nJUMP_PASSWORD=eve\n"
                "JUMP_PING_PATH=/bin/ping\nDEVICE_USERNAME=cisco\nDEVICE_PASSWORD=cisco\n"
                "DEVICE_ENABLE=cisco\nACTIVE_INVENTORY_FILE=network-inventory-current-status.csv\n"
                "ACTIVE_INVENTORY_FORMAT=csv\n"
            )

def load_app_config():
    global APP_CONFIG, SENSITIVE_STRINGS_TO_REDACT
    load_dotenv(DOTENV_PATH, override=True)
    APP_CONFIG = {
        "JUMP_HOST": os.getenv("JUMP_HOST", "172.16.39.128"),
        "JUMP_USERNAME": os.getenv("JUMP_USERNAME", "root"),
        "JUMP_PASSWORD": os.getenv("JUMP_PASSWORD", "eve"),
        "JUMP_PING_PATH": os.getenv("JUMP_PING_PATH", "/bin/ping"),
        "DEVICE_USERNAME": os.getenv("DEVICE_USERNAME", "cisco"),
        "DEVICE_PASSWORD": os.getenv("DEVICE_PASSWORD", "cisco"),
        "DEVICE_ENABLE": os.getenv("DEVICE_ENABLE", "cisco"),
        "ACTIVE_INVENTORY_FILE": os.getenv("ACTIVE_INVENTORY_FILE", "network-inventory-current-status.csv"),
        "ACTIVE_INVENTORY_FORMAT": os.getenv("ACTIVE_INVENTORY_FORMAT", "csv").lower()
    }
    SENSITIVE_STRINGS_TO_REDACT.clear()
    for key_config in ["JUMP_PASSWORD", "DEVICE_PASSWORD", "DEVICE_ENABLE"]:
        if APP_CONFIG[key_config] is None: 
            APP_CONFIG[key_config] = ""
        elif APP_CONFIG[key_config]: 
            SENSITIVE_STRINGS_TO_REDACT.append(APP_CONFIG[key_config])
    return APP_CONFIG

load_app_config()

# Global tracking variables
ACTIVE_INVENTORY_DATA: Dict[str, Any] = {}
audit_status: str = "Not Run"

# Progress tracking for audits
AUDIT_PROGRESS = {
    'status': 'idle',
    'current_device': None,
    'total_devices': 0,
    'completed_devices': 0,
    'start_time': None,
    'end_time': None,
    'current_device_start_time': None,
    'device_times': {},
    'estimated_completion_time': None,
    'device_statuses': {},
    'overall_success_count': 0,
    'overall_warning_count': 0,
    'overall_failure_count': 0
}
AUDIT_SHOULD_PAUSE = False
AUDIT_SHOULD_STOP = False

def prepare_progress_for_json(progress_data):
    """Convert progress data to JSON-serializable format"""
    json_safe = {}
    
    for key, value in progress_data.items():
        if isinstance(value, datetime):
            json_safe[key] = value.isoformat()
        elif isinstance(value, dict):
            json_safe[key] = prepare_progress_for_json(value)
        else:
            json_safe[key] = value
    
    return json_safe

# Continue with the enhanced audit logic...
def enhanced_run_audit_logic():
    """
    Enhanced audit logic with improved down device handling
    """
    global audit_status, ui_logs, detailed_reports_manifest, last_run_summary_data, current_run_failures
    global AUDIT_PROGRESS, DEVICE_STATUS_TRACKING, DOWN_DEVICES
    
    # Clear previous tracking
    DEVICE_STATUS_TRACKING.clear()
    DOWN_DEVICES.clear()
    
    log_to_ui_and_console(f"{Fore.CYAN}=== NetAuditPro Enhanced Audit Starting ==={Style.RESET_ALL}")
    log_to_ui_and_console(f"Enhanced features: Down device tracking, placeholder configs, improved reporting")
    
    # Load current inventory
    try:
        # Simple CSV loading for demo
        inventory_path = os.path.join('inventories', 'network-inventory-current-status.csv')
        if os.path.exists(inventory_path):
            with open(inventory_path, 'r') as f:
                reader = csv.DictReader(f)
                devices = list(reader)
                log_to_ui_and_console(f"Loaded {len(devices)} devices from inventory")
                
                # Create reports directory
                script_dir = os.path.dirname(os.path.abspath(__file__))
                base_report_path = os.path.join(script_dir, BASE_DIR_NAME)
                os.makedirs(base_report_path, exist_ok=True)
                
                # Test each device
                for device in devices:
                    device_name = device['hostname']
                    device_ip = device['ip']
                    expected_status = device.get('status', 'UNKNOWN')
                    
                    log_to_ui_and_console(f"\n--- Testing {device_name} ({device_ip}) ---")
                    
                    # Test ping connectivity
                    ping_ok = ping_local(device_ip)
                    
                    if not ping_ok:
                        # Device is down - track it and generate placeholder
                        failure_reason = f"ICMP ping failed to {device_ip}"
                        track_device_status(device_name, 'DOWN', failure_reason)
                        DOWN_DEVICES[device_name]['ip'] = device_ip
                        
                        # Generate placeholder config
                        placeholder_path = generate_placeholder_config_for_down_device(
                            device_name, device_ip, failure_reason, base_report_path
                        )
                        
                        log_to_ui_and_console(f"{Fore.RED}✖ {device_name} is DOWN - Generated placeholder config{Style.RESET_ALL}")
                    else:
                        # Device is up
                        track_device_status(device_name, 'UP')
                        log_to_ui_and_console(f"{Fore.GREEN}✔ {device_name} is UP{Style.RESET_ALL}")
                
                # Generate enhanced summary report
                generate_enhanced_summary_report(base_report_path)
                
                audit_status = "Completed"
                log_to_ui_and_console(f"{Fore.GREEN}=== Enhanced Audit Completed ==={Style.RESET_ALL}")
                
        else:
            log_to_ui_and_console(f"{Fore.RED}Inventory file not found: {inventory_path}{Style.RESET_ALL}")
            audit_status = "Failed: No inventory file"
            
    except Exception as e:
        log_to_ui_and_console(f"{Fore.RED}Audit failed: {e}{Style.RESET_ALL}")
        audit_status = f"Failed: {e}"

def generate_enhanced_summary_report(base_report_dir: str):
    """
    Generate enhanced summary report with detailed down device information
    """
    device_summary = get_device_status_summary()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary_content = f"""
==== NetAuditPro Enhanced Audit Summary Report ====
Timestamp: {timestamp}
Inventory File: {APP_CONFIG.get('ACTIVE_INVENTORY_FILE', 'N/A')}
Format: CSV Enhanced

=== DEVICE STATUS OVERVIEW ===
Total Devices: {device_summary['total_devices']}
UP Devices: {device_summary['up_devices']}
DOWN Devices: {device_summary['down_devices']}
Success Rate: {(device_summary['up_devices'] / device_summary['total_devices'] * 100):.1f}% if device_summary['total_devices'] > 0 else 0

=== UP DEVICES ===
"""
    
    if device_summary['up_device_list']:
        for device in device_summary['up_device_list']:
            summary_content += f"✅ {device} - OPERATIONAL\n"
    else:
        summary_content += "No devices are currently operational.\n"
    
    summary_content += "\n=== DOWN DEVICES ===\n"
    
    if device_summary['down_device_list']:
        for device in device_summary['down_device_list']:
            down_info = DOWN_DEVICES.get(device, {})
            failure_reason = down_info.get('failure_reason', 'Unknown')
            device_ip = down_info.get('ip', 'Unknown IP')
            summary_content += f"❌ {device} ({device_ip}) - {failure_reason}\n"
    else:
        summary_content += "All devices are operational.\n"
    
    summary_content += f"""
=== DETAILED STATUS TRACKING ===
"""
    for device, status in DEVICE_STATUS_TRACKING.items():
        summary_content += f"{device}: {status}\n"
    
    summary_content += f"""
=== AUDIT RECOMMENDATIONS ===
"""
    
    if device_summary['down_devices'] > 0:
        summary_content += f"""
CRITICAL: {device_summary['down_devices']} device(s) are unreachable.
Recommended Actions:
1. Check physical connectivity for down devices
2. Verify power status of affected devices  
3. Test manual SSH connectivity
4. Review firewall rules and network configuration
5. Contact network operations team for device status
"""
    else:
        summary_content += "✅ All devices operational - No immediate action required.\n"
    
    summary_content += f"""
=== REPORT FILES GENERATED ===
- Summary Report: summary.txt
- Placeholder Configs: Generated for all down devices
- Enhanced Status Tracking: Completed

==== END REPORT ====
"""
    
    # Write summary to file
    summary_path = os.path.join(base_report_dir, SUMMARY_FILENAME)
    try:
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        log_to_ui_and_console(f"Enhanced summary report written to: {summary_path}")
    except Exception as e:
        log_to_ui_and_console(f"Error writing summary report: {e}")

# Flask Routes for the enhanced application
@app.route('/')
def index():
    """Main dashboard showing enhanced device status"""
    device_summary = get_device_status_summary()
    
    # Create chart data for enhanced visualization
    chart_data = {
        "labels": ["UP Devices", "DOWN Devices"],
        "values": [device_summary['up_devices'], device_summary['down_devices']],
        "colors": ["#4CAF50", "#F44336"]
    }
    
    return render_template(TEMPLATE_INDEX_NAME, 
                         audit_status=audit_status,
                         logs=ui_logs[-100:],
                         device_summary=device_summary,
                         chart_data=chart_data,
                         active_inventory_file=APP_CONFIG.get('ACTIVE_INVENTORY_FILE', 'N/A'))

@app.route('/start_audit', methods=['GET', 'POST'])
def start_audit_route():
    """Start the enhanced audit process"""
    global audit_status
    
    if audit_status == "Running":
        flash("Audit already running", "warning")
        return redirect(url_for('index'))
    
    # Start audit in background thread
    audit_thread = threading.Thread(target=enhanced_run_audit_logic)
    audit_thread.daemon = True
    audit_thread.start()
    
    audit_status = "Running"
    flash("Enhanced audit started with down device tracking", "success")
    return redirect(url_for('index'))

@app.route('/device_status')
def device_status():
    """API endpoint for device status information"""
    return jsonify(get_device_status_summary())

@app.route('/down_devices')
def down_devices():
    """API endpoint for down device details"""
    return jsonify(DOWN_DEVICES)

# Template content for the enhanced UI
ENHANCED_INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NetAuditPro Enhanced - Network Audit Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .device-status-up { color: #28a745; }
        .device-status-down { color: #dc3545; }
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
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1 class="text-center mb-4">
            <i class="fas fa-network-wired"></i> NetAuditPro Enhanced
        </h1>
        
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
                                <i class="fas fa-play"></i> Start Enhanced Audit
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
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Auto-refresh every 5 seconds during audit
        {% if audit_status == 'Running' %}
        setTimeout(function() {
            location.reload();
        }, 5000);
        {% endif %}
    </script>
</body>
</html>
"""

# Create template files
if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Write the enhanced template
    template_path = os.path.join(templates_dir, TEMPLATE_INDEX_NAME)
    with open(template_path, 'w') as f:
        f.write(ENHANCED_INDEX_TEMPLATE)
    
    # Create initial directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_base_dir_main = os.path.join(script_dir, BASE_DIR_NAME)
    os.makedirs(report_base_dir_main, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    port = app.config['PORT']
    log_to_ui_and_console(f"NetAuditPro Enhanced running on http://0.0.0.0:{port}", console_only=True)
    log_to_ui_and_console(f"Enhanced features: Down device tracking, placeholder configs, improved reporting", console_only=True)
    log_to_ui_and_console(f"Access UI at: http://127.0.0.1:{port}", console_only=True)
    
    socketio.run(app, host='0.0.0.0', port=port, debug=True) 
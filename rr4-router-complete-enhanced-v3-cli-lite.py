#!/usr/bin/env python3
"""
NetAuditPro CLI Lite - AUX Telnet Security Audit Tool
Version: 3.0.0-CLI-LITE
File: rr4-router-complete-enhanced-v3-cli-lite.py

🚀 NETAUDITPRO CLI LITE - AUX TELNET SECURITY AUDIT 🚀
Focus: Command-line interface for AUX Line Telnet Configuration Security Assessment

CORE PHILOSOPHY: "CLI-First, Maximum Security Impact"
# ✅ Single-file CLI deployment with no web dependencies
# ✅ Cross-platform support (Windows + Linux + macOS)
# ✅ Interactive credential prompts with secure defaults
# ✅ Real-time progress display in terminal with colors
# ✅ Same audit engine as v3 web version
# ✅ CSV/JSON export capabilities
# ✅ Professional console reporting with statistics

SECURITY AUDIT FOCUS:
- Execute: show running-config | include ^hostname|^line aux |^ transport input
- Parse hostname, AUX line configuration, and transport input settings
- Identify telnet security risks on AUX ports
- Generate compliance reports in CSV/JSON format

CLI ENHANCEMENTS:
- Interactive credential management with defaults
- Real-time terminal progress indicators
- Colored output for better readability
- Command-line argument support
- Graceful interruption handling (Ctrl+C)
- Memory optimization and performance monitoring

ARCHITECTURE HIGHLIGHTS:
- Paramiko for secure SSH connectivity via jump host
- Colorama for cross-platform colored terminal output
- argparse for command-line argument parsing
- getpass for secure password input
- CSV/JSON for data export and reporting
- Cross-platform path handling and OS-specific configurations

EXTERNAL FILES (Minimal):
- inventories/routers01.csv (Device inventory)
- COMMAND-LOGS/ (Command outputs and findings)
- REPORTS/ (Generated CSV/JSON reports)
- .env (Configuration file)

DEPLOYMENT:
1. python3 rr4-router-complete-enhanced-v3-cli-lite.py
2. Follow interactive prompts for credentials
3. Specify inventory file or use default
4. Monitor real-time progress in terminal
5. Review audit results and export reports
"""

# ====================================================================
# IMPORTS & DEPENDENCIES
# ====================================================================

import os
import sys
import json
import csv
import re
import time
import socket
import tempfile
import threading
import platform
import subprocess
import signal
import argparse
import getpass
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from functools import wraps

# Networking and SSH
import paramiko

# Environment and configuration
from dotenv import load_dotenv, set_key, find_dotenv, dotenv_values

# Terminal colors and formatting
from colorama import Fore, Style, Back, init as colorama_init

# Initialize colorama for cross-platform colored output
colorama_init(autoreset=True)

# ====================================================================
# GLOBAL CONFIGURATION & CONSTANTS
# ====================================================================

# Application configuration
APP_VERSION = "v3.0.0-CLI-LITE"
APP_NAME = "NetAuditPro CLI Lite - AUX Telnet Security Audit"
DEFAULT_PORT = 22

# Cross-platform path configuration
BASE_DIR_NAME = "REPORTS"
COMMAND_LOGS_DIR_NAME = "COMMAND-LOGS"
SUMMARY_FILENAME = "audit_summary.txt"
INVENTORY_DIR = "inventories"
DEFAULT_CSV_FILENAME = "routers01.csv"

# Performance Constants
MAX_CONCURRENT_CONNECTIONS = 5
CONNECTION_POOL_SIZE = 3
MEMORY_THRESHOLD_MB = 200
MAX_LOG_ENTRIES = 100

# Cross-platform detection and configuration
PLATFORM = platform.system().lower()
IS_WINDOWS = PLATFORM == 'windows'
IS_LINUX = PLATFORM == 'linux'
IS_MACOS = PLATFORM == 'darwin'

# Platform-specific configurations
if IS_WINDOWS:
    PING_CMD = ["ping", "-n", "1", "-w", "3000"]
    NEWLINE = "\r\n"
    PATH_ENCODING = "utf-8"
    MAX_PATH_LENGTH = 260
else:
    PING_CMD = ["ping", "-c", "1", "-W", "3"]
    NEWLINE = "\n"
    PATH_ENCODING = "utf-8"
    MAX_PATH_LENGTH = 4096

# Core Cisco AUX Telnet Audit Commands
CORE_COMMANDS = {
    'show_line': 'show line',
    'aux_telnet_audit': 'show running-config | include ^hostname|^line aux|^ transport input|^ login|^ exec-timeout',
    'vty_telnet_audit': 'show running-config | include ^line vty|^ transport input|^ login|^ exec-timeout',
    'con_telnet_audit': 'show running-config | include ^line con|^ transport input|^ login|^ exec-timeout',
    'show_version': 'show version',
    'show_running_config': 'show running-config'
}

# Environment configuration
load_dotenv()
DOTENV_PATH = find_dotenv() or '.env'

# ====================================================================
# GLOBAL VARIABLES
# ====================================================================

# Application state
audit_status = "Idle"
audit_paused = False
audit_start_time = None
audit_completion_time = None

# Data storage
device_results = {}
command_logs = {}
audit_results_summary = {
    "total_devices": 0,
    "successful_devices": 0,
    "failed_devices": 0,
    "telnet_enabled_count": 0,
    "high_risk_devices": 0
}

# Configuration
app_config = {}
active_inventory_data = {"data": []}

# Progress tracking
current_device_index = 0
total_devices = 0
device_status_tracking = {}

# Interrupt handling
interrupted = False

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def get_script_directory() -> str:
    """Get the directory where the script is located"""
    return os.path.dirname(os.path.abspath(__file__))

def get_safe_path(*paths) -> str:
    """Create a safe cross-platform path"""
    return os.path.join(*paths)

def ensure_path_exists(path: str, is_file: bool = False) -> str:
    """Ensure a path exists, creating directories if necessary"""
    if is_file:
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    else:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    return path

def validate_filename(filename: str) -> str:
    """Validate and sanitize filename for cross-platform compatibility"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    global interrupted
    interrupted = True
    print(f"\n{Fore.YELLOW}⚠️ Interrupt received. Gracefully stopping audit...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Please wait for current device to complete...{Style.RESET_ALL}")

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)

# ====================================================================
# LOGGING AND OUTPUT FUNCTIONS
# ====================================================================

def log_message(msg: str, level: str = "INFO", color: str = None) -> None:
    """Log message to console with optional color"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Color mapping
    color_map = {
        "INFO": Fore.WHITE,
        "SUCCESS": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "DEBUG": Fore.CYAN
    }
    
    if color:
        msg_color = color
    else:
        msg_color = color_map.get(level, Fore.WHITE)
    
    print(f"{Fore.BLUE}[{timestamp}]{Style.RESET_ALL} {msg_color}{msg}{Style.RESET_ALL}")

def log_success(msg: str) -> None:
    """Log success message"""
    log_message(msg, "SUCCESS")

def log_warning(msg: str) -> None:
    """Log warning message"""
    log_message(msg, "WARNING")

def log_error(msg: str) -> None:
    """Log error message"""
    log_message(msg, "ERROR")

def log_debug(msg: str) -> None:
    """Log debug message"""
    log_message(msg, "DEBUG")

def print_banner():
    """Print application banner"""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  {Fore.YELLOW}🚀 NetAuditPro CLI Lite - AUX Telnet Security Audit {APP_VERSION}{Fore.CYAN}           ║
║                                                                              ║
║  {Fore.WHITE}Command-line interface for network device security auditing{Fore.CYAN}                ║
║  {Fore.WHITE}Focus: AUX/VTY/CON telnet configuration assessment{Fore.CYAN}                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_progress_bar(current: int, total: int, device_name: str = "", width: int = 50):
    """Print a progress bar in the terminal"""
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100
    
    filled = int(width * current // total) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)
    
    print(f"\r{Fore.CYAN}Progress: {Fore.YELLOW}[{bar}] {percentage:.1f}% ({current}/{total}){Style.RESET_ALL} {Fore.WHITE}{device_name}{Style.RESET_ALL}", end='', flush=True)

def print_summary_statistics():
    """Print audit summary statistics"""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📊 AUDIT SUMMARY STATISTICS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    
    total = audit_results_summary.get("total_devices", 0)
    successful = audit_results_summary.get("successful_devices", 0)
    failed = audit_results_summary.get("failed_devices", 0)
    violations = audit_results_summary.get("telnet_enabled_count", 0)
    high_risk = audit_results_summary.get("high_risk_devices", 0)
    
    print(f"{Fore.WHITE}📋 Total Devices Processed: {Fore.CYAN}{total}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Successful Audits: {Fore.CYAN}{successful}{Style.RESET_ALL}")
    print(f"{Fore.RED}❌ Failed Audits: {Fore.CYAN}{failed}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚠️ Telnet Violations: {Fore.CYAN}{violations}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🚨 High Risk Devices: {Fore.CYAN}{high_risk}{Style.RESET_ALL}")
    
    if total > 0:
        success_rate = (successful / total) * 100
        print(f"{Fore.WHITE}📈 Success Rate: {Fore.CYAN}{success_rate:.1f}%{Style.RESET_ALL}")
    
    # Timing information
    if audit_start_time and audit_completion_time:
        duration = audit_completion_time - audit_start_time
        print(f"{Fore.WHITE}⏱️ Total Duration: {Fore.CYAN}{format_duration(duration)}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

# ====================================================================
# CONFIGURATION MANAGEMENT
# ====================================================================

def load_app_config():
    """Load application configuration from environment variables and .env file"""
    global app_config
    
    # 1. Initialize with defaults or system environment variables
    app_config = {
        "JUMP_HOST": os.getenv('JUMP_HOST', '172.16.39.128'), 
        "JUMP_USERNAME": os.getenv('JUMP_USERNAME', 'root'), 
        "JUMP_PASSWORD": os.getenv('JUMP_PASSWORD', 'eve'), 
        "DEVICE_USERNAME": os.getenv('DEVICE_USERNAME', 'cisco'), 
        "DEVICE_PASSWORD": os.getenv('DEVICE_PASSWORD', 'cisco'), 
        "DEVICE_ENABLE": os.getenv('DEVICE_ENABLE', ''),
        "INVENTORY_FILE": os.getenv('INVENTORY_FILE', DEFAULT_CSV_FILENAME) 
    }
    
    log_debug("Initial configuration (defaults/system env vars):")
    for key, value in app_config.items():
        if "PASSWORD" not in key.upper() and "ENABLE" not in key.upper():
            log_debug(f"  {key}: {value}")

    # 2. Override with values from .env file if it exists
    dotenv_path_to_check = get_safe_path(get_script_directory(), '.env')
    log_debug(f"Checking for .env file at: {dotenv_path_to_check}")

    if os.path.exists(dotenv_path_to_check):
        log_debug(f"Found .env file at: {dotenv_path_to_check}. Loading values using dotenv_values.")
        
        env_file_values = dotenv_values(dotenv_path_to_check)
        
        log_debug(f"Values read from .env file using dotenv_values: {env_file_values}")

        keys_to_override_from_env_file = ["JUMP_HOST", "JUMP_USERNAME", "DEVICE_USERNAME", "INVENTORY_FILE"]
        for key in keys_to_override_from_env_file:
            if key in env_file_values and env_file_values[key] is not None:
                app_config[key] = env_file_values[key]
                log_debug(f"  Overridden from .env: {key} = {app_config[key]}")
            else:
                log_debug(f"  Key '{key}' not found in .env or its value is None. Keeping: {app_config.get(key)}")
    else:
        log_debug(f".env file not found at {dotenv_path_to_check}. Using defaults or system env vars.")

    log_debug("Final configuration after attempting .env load:")
    for key, value in app_config.items():
        if "PASSWORD" not in key.upper() and "ENABLE" not in key.upper():
            log_debug(f"  {key}: {value}")

def prompt_for_credentials():
    """Interactively prompt user for credentials with defaults"""
    print(f"\n{Fore.YELLOW}🔐 CREDENTIAL CONFIGURATION{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    # Jump host configuration
    print(f"\n{Fore.WHITE}Jump Host Configuration:{Style.RESET_ALL}")
    
    current_jump_host = app_config.get("JUMP_HOST", "172.16.39.128")
    jump_host = input(f"{Fore.CYAN}Jump Host IP [{current_jump_host}]: {Style.RESET_ALL}").strip()
    if not jump_host:
        jump_host = current_jump_host
    
    current_jump_user = app_config.get("JUMP_USERNAME", "root")
    jump_username = input(f"{Fore.CYAN}Jump Host Username [{current_jump_user}]: {Style.RESET_ALL}").strip()
    if not jump_username:
        jump_username = current_jump_user
    
    # Secure password input
    jump_password = getpass.getpass(f"{Fore.CYAN}Jump Host Password: {Style.RESET_ALL}")
    if not jump_password:
        jump_password = app_config.get("JUMP_PASSWORD", "eve")
    
    # Device credentials
    print(f"\n{Fore.WHITE}Cisco Device Credentials:{Style.RESET_ALL}")
    
    current_device_user = app_config.get("DEVICE_USERNAME", "cisco")
    device_username = input(f"{Fore.CYAN}Device Username [{current_device_user}]: {Style.RESET_ALL}").strip()
    if not device_username:
        device_username = current_device_user
    
    device_password = getpass.getpass(f"{Fore.CYAN}Device Password: {Style.RESET_ALL}")
    if not device_password:
        device_password = app_config.get("DEVICE_PASSWORD", "cisco")
    
    device_enable = getpass.getpass(f"{Fore.CYAN}Device Enable Password (optional): {Style.RESET_ALL}")
    
    # Update configuration
    app_config.update({
        "JUMP_HOST": jump_host,
        "JUMP_USERNAME": jump_username,
        "JUMP_PASSWORD": jump_password,
        "DEVICE_USERNAME": device_username,
        "DEVICE_PASSWORD": device_password,
        "DEVICE_ENABLE": device_enable
    })
    
    # Save to .env file
    save_config_to_env()
    
    log_success("Credentials configured successfully")

def save_config_to_env():
    """Save configuration to .env file"""
    try:
        env_path = get_safe_path(get_script_directory(), '.env')
        
        # Only save non-sensitive configuration
        with open(env_path, 'w') as f:
            f.write(f"JUMP_HOST={app_config.get('JUMP_HOST', '')}\n")
            f.write(f"JUMP_USERNAME={app_config.get('JUMP_USERNAME', '')}\n")
            f.write(f"DEVICE_USERNAME={app_config.get('DEVICE_USERNAME', '')}\n")
            f.write(f"INVENTORY_FILE={app_config.get('INVENTORY_FILE', '')}\n")
            f.write("# Passwords are not saved for security reasons\n")
            f.write("# JUMP_PASSWORD=\n")
            f.write("# DEVICE_PASSWORD=\n")
            f.write("# DEVICE_ENABLE=\n")
        
        log_debug(f"Configuration saved to {env_path}")
    except Exception as e:
        log_warning(f"Could not save configuration to .env file: {e}")

def validate_credentials():
    """Validate that all required credentials are provided"""
    required_fields = ["JUMP_HOST", "JUMP_USERNAME", "JUMP_PASSWORD", "DEVICE_USERNAME", "DEVICE_PASSWORD"]
    
    missing_fields = []
    for field in required_fields:
        if not app_config.get(field):
            missing_fields.append(field)
    
    if missing_fields:
        log_error(f"Missing required credentials: {', '.join(missing_fields)}")
        return False
    
    return True

# ====================================================================
# INVENTORY MANAGEMENT
# ====================================================================

def get_inventory_path(filename: str = None) -> str:
    """Get the full path to inventory file"""
    if not filename:
        filename = app_config.get("INVENTORY_FILE", DEFAULT_CSV_FILENAME)
    
    # Check if it's an absolute path
    if os.path.isabs(filename):
        return filename
    
    # Check in current directory first
    if os.path.exists(filename):
        return filename
    
    # Check in inventories subdirectory
    inventory_path = get_safe_path(get_script_directory(), INVENTORY_DIR, filename)
    if os.path.exists(inventory_path):
        return inventory_path
    
    # Return the inventories path even if it doesn't exist (for creation)
    return inventory_path

def load_inventory(filename: str = None) -> bool:
    """Load device inventory from CSV file"""
    global active_inventory_data, total_devices
    
    inventory_path = get_inventory_path(filename)
    
    if not os.path.exists(inventory_path):
        log_error(f"Inventory file not found: {inventory_path}")
        return False
    
    try:
        devices = []
        with open(inventory_path, 'r', newline='', encoding='utf-8') as csvfile:
            # Detect delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            for row_num, row in enumerate(reader, start=2):
                # Map CSV columns to standard format
                device = map_csv_columns(row)
                
                # Validate required fields
                if not device.get("ip_address"):
                    log_warning(f"Row {row_num}: Missing IP address, skipping")
                    continue
                
                # Set default hostname if not provided
                if not device.get("hostname"):
                    device["hostname"] = f"Device_{device['ip_address'].replace('.', '_')}"
                
                devices.append(device)
        
        active_inventory_data["data"] = devices
        total_devices = len(devices)
        
        log_success(f"Loaded {total_devices} devices from {inventory_path}")
        return True
        
    except Exception as e:
        log_error(f"Error loading inventory file: {e}")
        return False

def map_csv_columns(device_data: Dict[str, str]) -> Dict[str, str]:
    """Map CSV columns to standardized device data format"""
    # Common column name mappings
    column_mappings = {
        'ip': 'ip_address',
        'ip_address': 'ip_address',
        'management_ip': 'ip_address',
        'host': 'ip_address',
        'hostname': 'hostname',
        'name': 'hostname',
        'device_name': 'hostname',
        'model': 'cisco_model',
        'cisco_model': 'cisco_model',
        'device_type': 'device_type',
        'type': 'device_type',
        'description': 'description',
        'desc': 'description'
    }
    
    mapped_device = {}
    
    # Map known columns
    for csv_col, std_col in column_mappings.items():
        if csv_col in device_data and device_data[csv_col]:
            mapped_device[std_col] = device_data[csv_col].strip()
    
    # Set defaults
    if 'device_type' not in mapped_device:
        mapped_device['device_type'] = 'cisco_ios'
    
    # Copy any unmapped columns
    for key, value in device_data.items():
        if key.lower() not in column_mappings and value:
            mapped_device[key] = value.strip()
    
    return mapped_device

def prompt_for_inventory():
    """Prompt user for inventory file selection"""
    print(f"\n{Fore.YELLOW}📋 INVENTORY FILE SELECTION{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    default_path = get_inventory_path()
    current_file = app_config.get("INVENTORY_FILE", DEFAULT_CSV_FILENAME)
    
    print(f"{Fore.WHITE}Current inventory file: {Fore.CYAN}{current_file}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Default path: {Fore.CYAN}{default_path}{Style.RESET_ALL}")
    
    choice = input(f"\n{Fore.CYAN}Use default inventory file? [Y/n]: {Style.RESET_ALL}").strip().lower()
    
    if choice in ['n', 'no']:
        custom_path = input(f"{Fore.CYAN}Enter inventory file path: {Style.RESET_ALL}").strip()
        if custom_path:
            app_config["INVENTORY_FILE"] = custom_path
    
    return load_inventory()

# ====================================================================
# NETWORK FUNCTIONS (Ported from v3)
# ====================================================================

def ping_host(host: str) -> bool:
    """Test local connectivity to host using ping"""
    try:
        result = subprocess.run(
            PING_CMD + [host],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False

def ping_remote_device(ssh_client: paramiko.SSHClient, target_ip: str) -> bool:
    """Test remote connectivity via jump host using ping"""
    try:
        if IS_WINDOWS:
            ping_cmd = f"ping -n 1 -w 3000 {target_ip}"
        else:
            ping_cmd = f"ping -c 1 -W 3 {target_ip}"
        
        log_debug(f"Pinging {target_ip} via jump host...")
        stdin, stdout, stderr = ssh_client.exec_command(ping_cmd, timeout=15)
        exit_status = stdout.channel.recv_exit_status()
        
        return exit_status == 0
        
    except Exception as e:
        log_debug(f"Ping failed for {target_ip}: {e}")
        return False

def establish_jump_host_connection() -> Optional[paramiko.SSHClient]:
    """Establish SSH connection to jump host"""
    jump_host = app_config.get("JUMP_HOST")
    jump_username = app_config.get("JUMP_USERNAME")
    jump_password = app_config.get("JUMP_PASSWORD")
    
    if not all([jump_host, jump_username, jump_password]):
        log_error("Jump host credentials not configured")
        return None
    
    try:
        log_message(f"🔗 Connecting to jump host {jump_host}...")
        
        # Test local connectivity first
        if not ping_host(jump_host):
            log_warning(f"Jump host {jump_host} not reachable via local ping - continuing anyway")
        
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect with timeout
        ssh_client.connect(
            hostname=jump_host,
            port=22,
            username=jump_username,
            password=jump_password,
            timeout=30,
            auth_timeout=30,
            banner_timeout=30
        )
        
        log_success(f"Connected to jump host {jump_host}")
        return ssh_client
        
    except paramiko.AuthenticationException:
        log_error(f"Authentication failed for jump host {jump_host}")
        return None
    except paramiko.SSHException as e:
        log_error(f"SSH connection failed to jump host {jump_host}: {e}")
        return None
    except Exception as e:
        log_error(f"Failed to connect to jump host {jump_host}: {e}")
        return None

def connect_to_device_via_jump_host(ssh_client: paramiko.SSHClient, device_ip: str, device_username: str, device_password: str) -> Optional[paramiko.SSHClient]:
    """Connect to device via jump host SSH tunnel"""
    try:
        log_debug(f"Opening SSH tunnel to device {device_ip}")
        
        # Test connectivity via jump host first
        if not ping_remote_device(ssh_client, device_ip):
            log_warning(f"Device {device_ip} not reachable via jump host ping - continuing anyway")
        
        # Create transport for tunnel
        transport = ssh_client.get_transport()
        if not transport:
            log_error("No transport available from jump host connection")
            return None
        
        # Open channel for SSH tunnel
        dest_addr = (device_ip, 22)
        local_addr = ('127.0.0.1', 0)  # Let system choose port
        channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
        
        if not channel:
            log_error(f"Failed to open SSH tunnel to {device_ip}")
            return None
        
        # Create new SSH client for device connection
        device_ssh = paramiko.SSHClient()
        device_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect through the tunnel
        device_ssh.connect(
            hostname=device_ip,
            port=22,
            username=device_username,
            password=device_password,
            sock=channel,
            timeout=30,
            auth_timeout=30,
            banner_timeout=30
        )
        
        log_success(f"Connected to device {device_ip} via SSH tunnel")
        return device_ssh
        
    except paramiko.AuthenticationException:
        log_error(f"Authentication failed for device {device_ip}")
        return None
    except paramiko.SSHException as e:
        log_error(f"SSH connection failed to device {device_ip}: {e}")
        return None
    except Exception as e:
        log_error(f"Failed to connect to device {device_ip}: {e}")
        return None

def execute_command_on_device(ssh_client: paramiko.SSHClient, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
    """Execute command on device and return success, stdout, stderr"""
    try:
        log_debug(f"Executing command: {command}")
        
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
        
        # Read output
        stdout_data = stdout.read().decode('utf-8', errors='ignore')
        stderr_data = stderr.read().decode('utf-8', errors='ignore')
        exit_status = stdout.channel.recv_exit_status()
        
        success = exit_status == 0
        
        if success:
            log_debug(f"Command executed successfully")
        else:
            log_debug(f"Command failed with exit status {exit_status}")
        
        return success, stdout_data, stderr_data
        
    except Exception as e:
        log_error(f"Failed to execute command '{command}': {e}")
        return False, "", str(e)

def execute_core_commands_on_device(ssh_client: paramiko.SSHClient, device_info: Dict[str, str]) -> Dict[str, Any]:
    """Execute core audit commands on device using interactive shell"""
    device_ip = device_info.get('ip_address', 'unknown')
    hostname = device_info.get('hostname', 'unknown')
    
    results = {
        'device_ip': device_ip,
        'hostname': hostname,
        'timestamp': datetime.now().isoformat(),
        'commands': {},
        'audit_findings': {},
        'success': False,
        'error_message': ''
    }
    
    try:
        log_message(f"🔍 Executing audit commands on {hostname} ({device_ip})")
        
        # Open interactive shell
        shell = ssh_client.invoke_shell()
        shell.settimeout(30)
        
        # Wait for initial prompt and clear it
        time.sleep(2)
        shell.recv(4096)  # Clear initial output
        
        # Send terminal length 0 to disable paging
        shell.send("terminal length 0\n")
        time.sleep(1)
        shell.recv(4096)  # Clear command echo
        
        # Execute each core command
        for cmd_name, command in CORE_COMMANDS.items():
            log_debug(f"Executing {cmd_name}: {command}")
            
            try:
                # Send command
                shell.send(f"{command}\n")
                time.sleep(2)  # Wait for command execution
                
                # Read output
                output = ""
                while shell.recv_ready():
                    chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                    output += chunk
                    time.sleep(0.1)
                
                # Clean up output (remove command echo and prompt)
                lines = output.split('\n')
                cleaned_lines = []
                skip_next = False
                
                for line in lines:
                    # Skip command echo line
                    if command in line and not skip_next:
                        skip_next = True
                        continue
                    # Skip prompt lines
                    if line.strip().endswith('#') or line.strip().endswith('>'):
                        continue
                    # Skip empty lines at start/end
                    if line.strip():
                        cleaned_lines.append(line)
                
                cleaned_output = '\n'.join(cleaned_lines)
                
                results['commands'][cmd_name] = {
                    'command': command,
                    'success': True,
                    'stdout': cleaned_output,
                    'stderr': '',
                    'timestamp': datetime.now().isoformat()
                }
                
                log_debug(f"Command {cmd_name} completed successfully")
                
            except Exception as cmd_error:
                log_warning(f"Command {cmd_name} failed on {hostname}: {cmd_error}")
                results['commands'][cmd_name] = {
                    'command': command,
                    'success': False,
                    'stdout': '',
                    'stderr': str(cmd_error),
                    'timestamp': datetime.now().isoformat()
                }
        
        # Close shell
        shell.close()
        
        # Parse audit findings
        results['audit_findings'] = parse_audit_findings(results['commands'])
        results['success'] = True
        
        log_success(f"Audit completed for {hostname} ({device_ip})")
        
    except Exception as e:
        error_msg = f"Audit failed for {hostname} ({device_ip}): {e}"
        log_error(error_msg)
        results['error_message'] = error_msg
    
    return results

def parse_audit_findings(command_results: Dict[str, Any]) -> Dict[str, Any]:
    """Parse command outputs to extract audit findings"""
    findings = {
        'hostname': 'unknown',
        'aux_telnet_enabled': False,
        'vty_telnet_enabled': False,
        'con_telnet_enabled': False,
        'telnet_violations': [],
        'risk_level': 'LOW',
        'compliance_status': 'COMPLIANT'
    }
    
    try:
        # Combine all command outputs for comprehensive parsing
        all_output = ""
        for cmd_name, cmd_result in command_results.items():
            if cmd_result.get('success') and cmd_result.get('stdout'):
                all_output += cmd_result['stdout'] + "\n"
        
        # Parse hostname from any command output
        hostname_patterns = [
            r'^hostname\s+(\S+)',  # From running-config
            r'^(\S+)#',            # From command prompt
            r'(\S+)>',             # From user mode prompt
        ]
        
        for pattern in hostname_patterns:
            hostname_match = re.search(pattern, all_output, re.MULTILINE)
            if hostname_match:
                findings['hostname'] = hostname_match.group(1)
                break
        
        # Parse AUX line configuration
        aux_patterns = [
            r'line aux.*?(?=line|\Z)',  # AUX line block
            r'line aux.*?transport input\s+(\S+)',  # Direct transport input
        ]
        
        for pattern in aux_patterns:
            aux_match = re.search(pattern, all_output, re.DOTALL | re.IGNORECASE)
            if aux_match:
                aux_config = aux_match.group(0)
                if 'transport input telnet' in aux_config.lower() or 'transport input all' in aux_config.lower():
                    findings['aux_telnet_enabled'] = True
                    findings['telnet_violations'].append('AUX line has telnet transport enabled')
                break
        
        # Parse VTY line configuration
        vty_patterns = [
            r'line vty.*?(?=line|\Z)',  # VTY line block
            r'line vty.*?transport input\s+(\S+)',  # Direct transport input
        ]
        
        for pattern in vty_patterns:
            vty_match = re.search(pattern, all_output, re.DOTALL | re.IGNORECASE)
            if vty_match:
                vty_config = vty_match.group(0)
                if 'transport input telnet' in vty_config.lower() or 'transport input all' in vty_config.lower():
                    findings['vty_telnet_enabled'] = True
                    findings['telnet_violations'].append('VTY line has telnet transport enabled')
                break
        
        # Parse Console line configuration
        con_patterns = [
            r'line con.*?(?=line|\Z)',  # Console line block
            r'line con.*?transport input\s+(\S+)',  # Direct transport input
        ]
        
        for pattern in con_patterns:
            con_match = re.search(pattern, all_output, re.DOTALL | re.IGNORECASE)
            if con_match:
                con_config = con_match.group(0)
                if 'transport input telnet' in con_config.lower() or 'transport input all' in con_config.lower():
                    findings['con_telnet_enabled'] = True
                    findings['telnet_violations'].append('Console line has telnet transport enabled')
                break
        
        # Additional check for any telnet references in the output
        if 'transport input telnet' in all_output.lower():
            # More specific parsing if general telnet found
            telnet_lines = [line for line in all_output.split('\n') if 'transport input telnet' in line.lower()]
            for line in telnet_lines:
                if 'aux' in line.lower() and not findings['aux_telnet_enabled']:
                    findings['aux_telnet_enabled'] = True
                    findings['telnet_violations'].append('AUX line has telnet transport enabled')
                elif 'vty' in line.lower() and not findings['vty_telnet_enabled']:
                    findings['vty_telnet_enabled'] = True
                    findings['telnet_violations'].append('VTY line has telnet transport enabled')
                elif 'con' in line.lower() and not findings['con_telnet_enabled']:
                    findings['con_telnet_enabled'] = True
                    findings['telnet_violations'].append('Console line has telnet transport enabled')
        
        # Determine risk level based on violations
        violation_count = len(findings['telnet_violations'])
        if violation_count >= 2:
            findings['risk_level'] = 'HIGH'
            findings['compliance_status'] = 'NON_COMPLIANT'
        elif violation_count == 1:
            findings['risk_level'] = 'MEDIUM'
            findings['compliance_status'] = 'NON_COMPLIANT'
        else:
            findings['risk_level'] = 'LOW'
            findings['compliance_status'] = 'COMPLIANT'
        
        # Log parsing results for debugging
        log_debug(f"Parsed hostname: {findings['hostname']}")
        log_debug(f"AUX telnet enabled: {findings['aux_telnet_enabled']}")
        log_debug(f"VTY telnet enabled: {findings['vty_telnet_enabled']}")
        log_debug(f"CON telnet enabled: {findings['con_telnet_enabled']}")
        log_debug(f"Violations: {findings['telnet_violations']}")
        log_debug(f"Risk level: {findings['risk_level']}")
        
    except Exception as e:
        log_error(f"Error parsing audit findings: {e}")
    
    return findings

def audit_single_device(device_info: Dict[str, str], jump_ssh: paramiko.SSHClient) -> Dict[str, Any]:
    """Audit a single device"""
    global current_device_index, device_status_tracking
    
    device_ip = device_info.get('ip_address', device_info.get('management_ip', 'unknown'))
    hostname = device_info.get('hostname', f"Device_{device_ip.replace('.', '_')}")
    
    current_device_index += 1
    
    # Update progress
    if not interrupted:
        print_progress_bar(current_device_index, total_devices, hostname)
    
    device_status_tracking[device_ip] = {
        'hostname': hostname,
        'status': 'CONNECTING',
        'start_time': time.time()
    }
    
    result = {
        'device_ip': device_ip,
        'hostname': hostname,
        'success': False,
        'error_message': '',
        'audit_findings': {},
        'commands': {},
        'timestamp': datetime.now().isoformat()
    }
    
    device_ssh = None
    
    try:
        if interrupted:
            result['error_message'] = 'Audit interrupted by user'
            return result
        
        # Connect to device
        device_username = app_config.get('DEVICE_USERNAME')
        device_password = app_config.get('DEVICE_PASSWORD')
        
        device_ssh = connect_to_device_via_jump_host(jump_ssh, device_ip, device_username, device_password)
        
        if not device_ssh:
            result['error_message'] = f'Failed to connect to device {device_ip}'
            device_status_tracking[device_ip]['status'] = 'FAILED'
            return result
        
        device_status_tracking[device_ip]['status'] = 'AUDITING'
        
        # Execute audit commands
        audit_result = execute_core_commands_on_device(device_ssh, device_info)
        
        # Update result with audit data
        result.update(audit_result)
        device_status_tracking[device_ip]['status'] = 'COMPLETED' if result['success'] else 'FAILED'
        
    except Exception as e:
        error_msg = f"Unexpected error auditing {hostname} ({device_ip}): {e}"
        log_error(error_msg)
        result['error_message'] = error_msg
        device_status_tracking[device_ip]['status'] = 'FAILED'
    
    finally:
        # Clean up device connection
        if device_ssh:
            try:
                device_ssh.close()
            except:
                pass
        
        device_status_tracking[device_ip]['end_time'] = time.time()
    
    return result

def run_complete_audit() -> bool:
    """Run complete audit on all devices in inventory"""
    global audit_status, audit_start_time, audit_completion_time, device_results, interrupted
    global audit_results_summary
    
    if not active_inventory_data.get("data"):
        log_error("No devices in inventory to audit")
        return False
    
    devices = active_inventory_data["data"]
    audit_status = "Running"
    audit_start_time = time.time()
    
    log_message(f"🚀 Starting audit of {len(devices)} devices...")
    
    # Establish jump host connection
    jump_ssh = establish_jump_host_connection()
    if not jump_ssh:
        log_error("Failed to establish jump host connection")
        audit_status = "Failed"
        return False
    
    try:
        # Initialize results tracking
        audit_results_summary.update({
            "total_devices": len(devices),
            "successful_devices": 0,
            "failed_devices": 0,
            "telnet_enabled_count": 0,
            "high_risk_devices": 0
        })
        
        # Process devices
        for i, device in enumerate(devices):
            if interrupted:
                log_warning("Audit interrupted by user")
                break
            
            device_ip = device.get('ip_address', device.get('management_ip', 'unknown'))
            
            # Audit device
            result = audit_single_device(device, jump_ssh)
            device_results[device_ip] = result
            
            # Update summary statistics
            if result['success']:
                audit_results_summary["successful_devices"] += 1
                
                # Check for telnet violations
                findings = result.get('audit_findings', {})
                if findings.get('telnet_violations'):
                    audit_results_summary["telnet_enabled_count"] += 1
                
                if findings.get('risk_level') == 'HIGH':
                    audit_results_summary["high_risk_devices"] += 1
            else:
                audit_results_summary["failed_devices"] += 1
        
        audit_completion_time = time.time()
        audit_status = "Completed" if not interrupted else "Interrupted"
        
        log_success(f"Audit completed. Processed {audit_results_summary['successful_devices']}/{audit_results_summary['total_devices']} devices successfully")
        
        return True
        
    except Exception as e:
        log_error(f"Audit failed: {e}")
        audit_status = "Failed"
        return False
    
    finally:
        # Clean up jump host connection
        if jump_ssh:
            try:
                jump_ssh.close()
            except:
                pass

# ====================================================================
# REPORTING AND EXPORT FUNCTIONS
# ====================================================================

def save_audit_results_to_csv(filename: str = None) -> bool:
    """Save audit results to CSV file"""
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_results_{timestamp}.csv"
        
        # Ensure reports directory exists
        reports_dir = get_safe_path(get_script_directory(), BASE_DIR_NAME)
        ensure_path_exists(reports_dir)
        
        csv_path = get_safe_path(reports_dir, filename)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'device_ip', 'hostname', 'success', 'timestamp',
                'aux_telnet_enabled', 'vty_telnet_enabled', 'con_telnet_enabled',
                'telnet_violations_count', 'risk_level', 'compliance_status',
                'error_message'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for device_ip, result in device_results.items():
                findings = result.get('audit_findings', {})
                
                row = {
                    'device_ip': device_ip,
                    'hostname': result.get('hostname', 'unknown'),
                    'success': result.get('success', False),
                    'timestamp': result.get('timestamp', ''),
                    'aux_telnet_enabled': findings.get('aux_telnet_enabled', False),
                    'vty_telnet_enabled': findings.get('vty_telnet_enabled', False),
                    'con_telnet_enabled': findings.get('con_telnet_enabled', False),
                    'telnet_violations_count': len(findings.get('telnet_violations', [])),
                    'risk_level': findings.get('risk_level', 'UNKNOWN'),
                    'compliance_status': findings.get('compliance_status', 'UNKNOWN'),
                    'error_message': result.get('error_message', '')
                }
                
                writer.writerow(row)
        
        log_success(f"Audit results saved to CSV: {csv_path}")
        return True
        
    except Exception as e:
        log_error(f"Failed to save CSV results: {e}")
        return False

def save_audit_results_to_json(filename: str = None) -> bool:
    """Save audit results to JSON file"""
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_results_{timestamp}.json"
        
        # Ensure reports directory exists
        reports_dir = get_safe_path(get_script_directory(), BASE_DIR_NAME)
        ensure_path_exists(reports_dir)
        
        json_path = get_safe_path(reports_dir, filename)
        
        # Prepare comprehensive results
        export_data = {
            'audit_metadata': {
                'version': APP_VERSION,
                'timestamp': datetime.now().isoformat(),
                'audit_start_time': audit_start_time,
                'audit_completion_time': audit_completion_time,
                'duration_seconds': audit_completion_time - audit_start_time if audit_completion_time and audit_start_time else 0,
                'status': audit_status
            },
            'summary': audit_results_summary,
            'device_results': device_results,
            'configuration': {
                'jump_host': app_config.get('JUMP_HOST'),
                'jump_username': app_config.get('JUMP_USERNAME'),
                'device_username': app_config.get('DEVICE_USERNAME'),
                'inventory_file': app_config.get('INVENTORY_FILE')
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, default=str)
        
        log_success(f"Audit results saved to JSON: {json_path}")
        return True
        
    except Exception as e:
        log_error(f"Failed to save JSON results: {e}")
        return False

def save_command_logs() -> bool:
    """Save detailed command logs for each device"""
    try:
        # Ensure command logs directory exists
        logs_dir = get_safe_path(get_script_directory(), COMMAND_LOGS_DIR_NAME)
        ensure_path_exists(logs_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for device_ip, result in device_results.items():
            if not result.get('commands'):
                continue
            
            hostname = result.get('hostname', f"Device_{device_ip.replace('.', '_')}")
            log_filename = f"{hostname}_{device_ip}_{timestamp}.txt"
            log_path = get_safe_path(logs_dir, log_filename)
            
            with open(log_path, 'w', encoding='utf-8') as logfile:
                logfile.write(f"NetAuditPro CLI Lite - Command Log\n")
                logfile.write(f"Device: {hostname} ({device_ip})\n")
                logfile.write(f"Timestamp: {result.get('timestamp', '')}\n")
                logfile.write(f"Success: {result.get('success', False)}\n")
                logfile.write("=" * 80 + "\n\n")
                
                # Write command outputs
                for cmd_name, cmd_result in result['commands'].items():
                    logfile.write(f"Command: {cmd_name}\n")
                    logfile.write(f"Executed: {cmd_result.get('command', '')}\n")
                    logfile.write(f"Success: {cmd_result.get('success', False)}\n")
                    logfile.write(f"Timestamp: {cmd_result.get('timestamp', '')}\n")
                    logfile.write("-" * 40 + "\n")
                    logfile.write("STDOUT:\n")
                    logfile.write(cmd_result.get('stdout', ''))
                    logfile.write("\n" + "-" * 40 + "\n")
                    if cmd_result.get('stderr'):
                        logfile.write("STDERR:\n")
                        logfile.write(cmd_result.get('stderr', ''))
                        logfile.write("\n" + "-" * 40 + "\n")
                    logfile.write("\n")
                
                # Write audit findings
                findings = result.get('audit_findings', {})
                if findings:
                    logfile.write("AUDIT FINDINGS:\n")
                    logfile.write("=" * 40 + "\n")
                    for key, value in findings.items():
                        logfile.write(f"{key}: {value}\n")
        
        log_success(f"Command logs saved to {logs_dir}")
        return True
        
    except Exception as e:
        log_error(f"Failed to save command logs: {e}")
        return False

def generate_audit_summary_report() -> bool:
    """Generate a comprehensive audit summary report"""
    try:
        # Ensure reports directory exists
        reports_dir = get_safe_path(get_script_directory(), BASE_DIR_NAME)
        ensure_path_exists(reports_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = get_safe_path(reports_dir, f"audit_summary_{timestamp}.txt")
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("NetAuditPro CLI Lite - Audit Summary Report\n")
            f.write("=" * 60 + "\n\n")
            
            # Metadata
            f.write(f"Version: {APP_VERSION}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Jump Host: {app_config.get('JUMP_HOST')}\n")
            f.write(f"Inventory File: {app_config.get('INVENTORY_FILE')}\n")
            
            if audit_start_time and audit_completion_time:
                duration = audit_completion_time - audit_start_time
                f.write(f"Audit Duration: {format_duration(duration)}\n")
            
            f.write(f"Audit Status: {audit_status}\n\n")
            
            # Summary Statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 30 + "\n")
            total = audit_results_summary.get("total_devices", 0)
            successful = audit_results_summary.get("successful_devices", 0)
            failed = audit_results_summary.get("failed_devices", 0)
            violations = audit_results_summary.get("telnet_enabled_count", 0)
            high_risk = audit_results_summary.get("high_risk_devices", 0)
            
            f.write(f"Total Devices: {total}\n")
            f.write(f"Successful Audits: {successful}\n")
            f.write(f"Failed Audits: {failed}\n")
            f.write(f"Telnet Violations: {violations}\n")
            f.write(f"High Risk Devices: {high_risk}\n")
            
            if total > 0:
                success_rate = (successful / total) * 100
                f.write(f"Success Rate: {success_rate:.1f}%\n")
            
            f.write("\n")
            
            # Device Details
            f.write("DEVICE AUDIT RESULTS\n")
            f.write("-" * 30 + "\n")
            
            for device_ip, result in device_results.items():
                hostname = result.get('hostname', 'unknown')
                success = result.get('success', False)
                findings = result.get('audit_findings', {})
                
                f.write(f"\nDevice: {hostname} ({device_ip})\n")
                f.write(f"Status: {'SUCCESS' if success else 'FAILED'}\n")
                
                if success:
                    f.write(f"Risk Level: {findings.get('risk_level', 'UNKNOWN')}\n")
                    f.write(f"Compliance: {findings.get('compliance_status', 'UNKNOWN')}\n")
                    
                    violations = findings.get('telnet_violations', [])
                    if violations:
                        f.write("Violations:\n")
                        for violation in violations:
                            f.write(f"  - {violation}\n")
                    else:
                        f.write("No telnet violations found\n")
                else:
                    error_msg = result.get('error_message', 'Unknown error')
                    f.write(f"Error: {error_msg}\n")
        
        log_success(f"Audit summary report saved: {summary_path}")
        return True
        
    except Exception as e:
        log_error(f"Failed to generate summary report: {e}")
        return False

# ====================================================================
# MAIN CLI FUNCTIONS
# ====================================================================

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} {APP_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Interactive mode with prompts
  %(prog)s --inventory routers.csv  # Use specific inventory file
  %(prog)s --config                 # Configure credentials only
  %(prog)s --quiet                  # Minimal output
  %(prog)s --verbose                # Detailed output
        """
    )
    
    parser.add_argument(
        '--inventory', '-i',
        help='Path to device inventory CSV file',
        default=None
    )
    
    parser.add_argument(
        '--config', '-c',
        action='store_true',
        help='Configure credentials and exit'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output (errors only)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output (debug messages)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} {APP_VERSION}'
    )
    
    return parser.parse_args()

def main():
    """Main CLI application entry point"""
    global interrupted
    
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Print banner
        if not args.quiet:
            print_banner()

        # Load configuration
        load_app_config()
        
        # Handle configuration-only mode
        if args.config:
            prompt_for_credentials()
            log_success("Configuration completed. Exiting.")
            return 0
        
        # Prompt for credentials if not provided
        if not validate_credentials():
            if not args.quiet:
                print(f"\n{Fore.YELLOW}Credentials not found or incomplete.{Style.RESET_ALL}")
            prompt_for_credentials()
        
        # Load inventory
        if args.inventory:
            app_config["INVENTORY_FILE"] = args.inventory
        
        if not load_inventory():
            if not prompt_for_inventory():
                log_error("Could not load inventory file. Exiting.")
                return 1
        
        # Validate we have devices to audit
        if total_devices == 0:
            log_error("No devices found in inventory. Exiting.")
            return 1
        
        # Display pre-audit summary
        if not args.quiet:
            print(f"\n{Fore.CYAN}📋 AUDIT PREPARATION{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Devices to audit: {Fore.CYAN}{total_devices}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Jump host: {Fore.CYAN}{app_config.get('JUMP_HOST')}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Inventory file: {Fore.CYAN}{app_config.get('INVENTORY_FILE')}{Style.RESET_ALL}")
        
        # Confirm before starting
        if not args.quiet:
            confirm = input(f"\n{Fore.YELLOW}Start audit? [Y/n]: {Style.RESET_ALL}").strip().lower()
            if confirm in ['n', 'no']:
                log_message("Audit cancelled by user.")
                return 0
        
        # Start audit
        log_message("🚀 Starting NetAuditPro CLI Lite audit...")
        
        # Run the complete audit
        audit_success = run_complete_audit()
        
        # Generate reports if audit completed (successfully or with some failures)
        if audit_success or device_results:
            log_message("📊 Generating audit reports...")
            
            # Save results in multiple formats
            save_audit_results_to_csv()
            save_audit_results_to_json()
            save_command_logs()
            generate_audit_summary_report()
            
            log_success("All audit reports generated successfully")
        
        if not args.quiet:
            print()  # New line after progress bar
            print_summary_statistics()
        
        # Return appropriate exit code
        if interrupted:
            return 130  # Standard exit code for SIGINT
        elif audit_success:
            return 0
        else:
            return 1
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Audit interrupted by user{Style.RESET_ALL}")
        return 130
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
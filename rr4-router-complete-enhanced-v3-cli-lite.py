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
    # Windows-specific terminal settings
    import msvcrt
    def get_char():
        return msvcrt.getch().decode('utf-8')
else:
    PING_CMD = ["ping", "-c", "1", "-W", "3"]
    NEWLINE = "\n"
    PATH_ENCODING = "utf-8"
    MAX_PATH_LENGTH = 4096
    # Unix-specific terminal settings
    import termios, tty
    def get_char():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.cbreak(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# Enhanced cross-platform path handling
def get_user_home_dir() -> str:
    """Get user home directory in a cross-platform way"""
    return os.path.expanduser("~")

def get_temp_dir() -> str:
    """Get temporary directory in a cross-platform way"""
    return tempfile.gettempdir()

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
DOTENV_PATH = find_dotenv() or '.env-t'  # Changed to use .env-t file

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

# Configuration - Remove hardcoded credentials
app_config = {}
active_inventory_data = {"data": []}

# Progress tracking
current_device_index = 0
total_devices = 0
device_status_tracking = {}

# Interrupt handling
interrupted = False

# Default credentials (not hardcoded in config)
DEFAULT_CREDENTIALS = {
    "JUMP_HOST": "172.16.39.128",
    "JUMP_USERNAME": "root",
    "JUMP_PASSWORD": "eve",
    "DEVICE_USERNAME": "cisco",
    "DEVICE_PASSWORD": "cisco"
}

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

def mask_password(password: str) -> str:
    """Mask password for logging purposes"""
    if not password:
        return ""
    if len(password) <= 2:
        return "*" * len(password)
    return password[0] + "*" * (len(password) - 2) + password[-1]

def get_env_file_path() -> str:
    """Get the path to the .env-t file"""
    return get_safe_path(get_script_directory(), '.env-t')

def validate_ip_address(ip: str) -> bool:
    """Validate IP address format"""
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not 0 <= int(part) <= 255:
                return False
        return True
    except (ValueError, AttributeError):
        return False

def validate_hostname(hostname: str) -> bool:
    """Validate hostname format"""
    if not hostname or len(hostname) > 253:
        return False
    # Check for valid characters
    import re
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, hostname))

def check_network_connectivity() -> bool:
    """Check basic network connectivity"""
    try:
        # Try to resolve a common DNS name
        socket.gethostbyname('google.com')
        return True
    except socket.gaierror:
        return False

def validate_port(port: str) -> bool:
    """Validate port number"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False

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

# Global debug level
DEBUG_LEVEL = 0  # 0=INFO, 1=DEBUG, 2=VERBOSE, 3=TRACE

def set_debug_level(level: int):
    """Set global debug level"""
    global DEBUG_LEVEL
    DEBUG_LEVEL = level

def log_message(msg: str, level: str = "INFO", color: str = None, debug_level: int = 0) -> None:
    """Enhanced log message with debug levels"""
    if debug_level > DEBUG_LEVEL:
        return
        
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
    
    # Color mapping with more options
    color_map = {
        "INFO": Fore.WHITE,
        "SUCCESS": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "DEBUG": Fore.CYAN,
        "TRACE": Fore.MAGENTA,
        "NETWORK": Fore.BLUE,
        "SECURITY": Fore.YELLOW
    }
    
    if color:
        msg_color = color
    else:
        msg_color = color_map.get(level, Fore.WHITE)
    
    # Add debug level indicator
    level_indicator = ""
    if DEBUG_LEVEL >= 1:
        level_indicator = f"[{level}] "
    
    print(f"{Fore.BLUE}[{timestamp}]{Style.RESET_ALL} {level_indicator}{msg_color}{msg}{Style.RESET_ALL}")

def log_success(msg: str, debug_level: int = 0) -> None:
    """Log success message with debug level"""
    log_message(f"✅ {msg}", "SUCCESS", debug_level=debug_level)

def log_warning(msg: str, debug_level: int = 0) -> None:
    """Log warning message with debug level"""
    log_message(f"⚠️ {msg}", "WARNING", debug_level=debug_level)

def log_error(msg: str, debug_level: int = 0) -> None:
    """Log error message with debug level"""
    log_message(f"❌ {msg}", "ERROR", debug_level=debug_level)

def log_debug(msg: str, debug_level: int = 1) -> None:
    """Log debug message with debug level"""
    log_message(f"🔍 {msg}", "DEBUG", debug_level=debug_level)

def log_trace(msg: str, debug_level: int = 2) -> None:
    """Log trace message for detailed debugging"""
    log_message(f"🔬 {msg}", "TRACE", debug_level=debug_level)

def log_network(msg: str, debug_level: int = 1) -> None:
    """Log network-related message"""
    log_message(f"🌐 {msg}", "NETWORK", debug_level=debug_level)

def log_security(msg: str, debug_level: int = 0) -> None:
    """Log security-related message"""
    log_message(f"🔒 {msg}", "SECURITY", debug_level=debug_level)

def log_performance(msg: str, debug_level: int = 1) -> None:
    """Log performance-related message"""
    log_message(f"⚡ {msg}", "DEBUG", debug_level=debug_level)

def log_function_entry(func_name: str, args: dict = None, debug_level: int = 2) -> None:
    """Log function entry for debugging"""
    args_str = ""
    if args and DEBUG_LEVEL >= 3:
        # Mask sensitive data in args
        safe_args = {}
        for key, value in args.items():
            if any(sensitive in key.lower() for sensitive in ['password', 'pass', 'secret', 'key']):
                safe_args[key] = mask_password(str(value))
            else:
                safe_args[key] = str(value)[:100]  # Truncate long values
        args_str = f" with args: {safe_args}"
    log_trace(f"→ Entering {func_name}{args_str}", debug_level)

def log_function_exit(func_name: str, result: str = None, debug_level: int = 2) -> None:
    """Log function exit for debugging"""
    result_str = f" -> {result}" if result else ""
    log_trace(f"← Exiting {func_name}{result_str}", debug_level)

def log_exception(func_name: str, exception: Exception, debug_level: int = 0) -> None:
    """Log exception with full details"""
    import traceback
    log_error(f"Exception in {func_name}: {type(exception).__name__}: {exception}", debug_level)
    if DEBUG_LEVEL >= 2:
        log_trace(f"Full traceback:\n{traceback.format_exc()}", debug_level)

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
    """Print an enhanced progress bar in the terminal with ETA"""
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100
    
    filled = int(width * current // total) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)
    
    # Calculate ETA if we have timing information
    eta_str = ""
    if hasattr(print_progress_bar, 'start_time') and current > 0:
        elapsed = time.time() - print_progress_bar.start_time
        if current < total:
            avg_time_per_device = elapsed / current
            remaining_devices = total - current
            eta_seconds = avg_time_per_device * remaining_devices
            eta_str = f" | ETA: {format_duration(eta_seconds)}"
    elif current == 1:
        # Initialize timing on first device
        print_progress_bar.start_time = time.time()
    
    # Enhanced progress display
    status_icons = {
        'connecting': '🔗',
        'auditing': '🔍',
        'completed': '✅',
        'failed': '❌'
    }
    
    print(f"\r{Fore.CYAN}Progress: {Fore.YELLOW}[{bar}] {percentage:.1f}% ({current}/{total}){eta_str}{Style.RESET_ALL} {Fore.WHITE}{device_name}{Style.RESET_ALL}", end='', flush=True)

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
        
        # Add recommendations based on results
        if success_rate < 50:
            print(f"{Fore.RED}⚠️ Low success rate detected. Check network connectivity and credentials.{Style.RESET_ALL}")
        elif violations > 0:
            print(f"{Fore.YELLOW}⚠️ Security violations found. Review telnet configurations.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}✅ Good audit results. Network appears secure.{Style.RESET_ALL}")
    
    # Timing information
    if audit_start_time and audit_completion_time:
        duration = audit_completion_time - audit_start_time
        print(f"{Fore.WHITE}⏱️ Total Duration: {Fore.CYAN}{format_duration(duration)}{Style.RESET_ALL}")
        
        if total > 0:
            avg_time = duration / total
            print(f"{Fore.WHITE}⏱️ Average Time per Device: {Fore.CYAN}{format_duration(avg_time)}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

def handle_connection_failure(device_ip: str, error: str) -> Dict[str, Any]:
    """Handle connection failures gracefully with detailed error information"""
    error_categories = {
        'timeout': ['timeout', 'timed out', 'connection timeout'],
        'auth': ['authentication', 'auth', 'permission denied', 'invalid credentials'],
        'network': ['network unreachable', 'no route to host', 'connection refused'],
        'ssh': ['ssh', 'protocol error', 'key exchange'],
        'unknown': []
    }
    
    error_lower = error.lower()
    error_type = 'unknown'
    
    for category, keywords in error_categories.items():
        if any(keyword in error_lower for keyword in keywords):
            error_type = category
            break
    
    # Provide specific recommendations based on error type
    recommendations = {
        'timeout': 'Check network connectivity and firewall rules',
        'auth': 'Verify username and password credentials',
        'network': 'Check device IP address and network routing',
        'ssh': 'Verify SSH service is running on the device',
        'unknown': 'Check device accessibility and configuration'
    }
    
    return {
        'device_ip': device_ip,
        'error_type': error_type,
        'error_message': error,
        'recommendation': recommendations.get(error_type, 'Contact network administrator'),
        'timestamp': datetime.now().isoformat()
    }

def check_system_resources() -> Dict[str, Any]:
    """Check system resources and provide warnings if needed"""
    import psutil
    
    try:
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        warnings = []
        
        if cpu_percent > 80:
            warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
        
        if memory.percent > 80:
            warnings.append(f"High memory usage: {memory.percent:.1f}%")
        
        if disk.percent > 90:
            warnings.append(f"Low disk space: {disk.percent:.1f}% used")
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'warnings': warnings
        }
    except ImportError:
        log_debug("psutil not available, skipping system resource check")
        return {'warnings': []}
    except Exception as e:
        log_debug(f"Error checking system resources: {e}")
        return {'warnings': []}

# ====================================================================
# CONFIGURATION MANAGEMENT
# ====================================================================

def load_app_config():
    """Load application configuration from .env-t file with comprehensive debugging"""
    global app_config
    
    log_function_entry("load_app_config")
    
    # 1. Initialize with empty config (no hardcoded credentials)
    app_config = {}
    log_debug("Initialized empty app_config")
    
    # 2. Check for .env-t file
    env_file_path = get_env_file_path()
    log_debug(f"Checking for .env-t file at: {env_file_path}")

    if os.path.exists(env_file_path):
        log_success(f"Found .env-t file at: {env_file_path}")
        
        try:
            # Check file permissions
            file_stat = os.stat(env_file_path)
            file_size = file_stat.st_size
            file_mode = oct(file_stat.st_mode)[-3:]
            log_debug(f"File size: {file_size} bytes, permissions: {file_mode}")
            
            # Load from .env-t file
            log_trace("Reading .env-t file contents")
            env_file_values = dotenv_values(env_file_path)
            log_debug(f"Raw values from .env-t: {len(env_file_values)} entries")
            
            # Log non-sensitive values for debugging
            for key, value in env_file_values.items():
                if value is not None:
                    if "PASSWORD" in key.upper():
                        log_trace(f"Found credential key: {key} = [MASKED]")
                    else:
                        log_trace(f"Found config key: {key} = {value}")
            
            # Load all credential values from .env-t
            loaded_count = 0
            for key in ["JUMP_HOST", "JUMP_USERNAME", "JUMP_PASSWORD", "DEVICE_USERNAME", "DEVICE_PASSWORD", "INVENTORY_FILE"]:
                if key in env_file_values and env_file_values[key] is not None and env_file_values[key].strip():
                    app_config[key] = env_file_values[key].strip()
                    loaded_count += 1
                    if "PASSWORD" in key:
                        log_debug(f"Loaded from .env-t: {key} = {mask_password(app_config[key])}")
                    else:
                        log_debug(f"Loaded from .env-t: {key} = {app_config[key]}")
                else:
                    log_warning(f"Key '{key}' not found or empty in .env-t file")
            
            log_success(f"Loaded {loaded_count} configuration values from .env-t")
            
            # Set default inventory file if not specified
            if "INVENTORY_FILE" not in app_config:
                app_config["INVENTORY_FILE"] = DEFAULT_CSV_FILENAME
                log_debug(f"Set default inventory file: {DEFAULT_CSV_FILENAME}")
                
        except Exception as e:
            log_exception("load_app_config", e)
            log_error(f"Error reading .env-t file: {e}")
    else:
        log_warning(f".env-t file not found at {env_file_path}")
        log_debug("Will prompt for credentials during execution")

    # 3. Override with system environment variables if they exist (for flexibility)
    env_override_count = 0
    for key in ["JUMP_HOST", "JUMP_USERNAME", "JUMP_PASSWORD", "DEVICE_USERNAME", "DEVICE_PASSWORD", "INVENTORY_FILE"]:
        env_value = os.getenv(key)
        if env_value and env_value.strip():
            old_value = app_config.get(key, "")
            app_config[key] = env_value.strip()
            env_override_count += 1
            if "PASSWORD" in key:
                log_debug(f"Overridden from system env: {key} = {mask_password(app_config[key])}")
            else:
                log_debug(f"Overridden from system env: {key} = {app_config[key]}")
            
            if old_value and old_value != app_config[key]:
                log_trace(f"Value changed from .env-t to system env for {key}")

    if env_override_count > 0:
        log_debug(f"Applied {env_override_count} system environment overrides")
    else:
        log_trace("No system environment overrides found")

    # 4. Validate configuration completeness
    required_keys = ["JUMP_HOST", "JUMP_USERNAME", "JUMP_PASSWORD", "DEVICE_USERNAME", "DEVICE_PASSWORD"]
    missing_keys = [key for key in required_keys if not app_config.get(key)]
    
    if missing_keys:
        log_warning(f"Missing configuration keys: {missing_keys}")
        log_debug("User will be prompted for missing credentials")
    else:
        log_success("All required configuration keys are present")

    # 5. Log final configuration summary
    log_debug("Final configuration summary:")
    for key, value in app_config.items():
        if "PASSWORD" in key:
            log_trace(f"  {key}: {mask_password(value)}")
        else:
            log_trace(f"  {key}: {value}")
    
    log_function_exit("load_app_config", f"Loaded {len(app_config)} config items")

def prompt_for_credentials():
    """Interactively prompt user for credentials with defaults"""
    print(f"\n{Fore.YELLOW}🔐 CREDENTIAL CONFIGURATION{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    # Jump host configuration
    print(f"\n{Fore.WHITE}Jump Host Configuration:{Style.RESET_ALL}")
    
    # Get current values or use defaults
    current_jump_host = app_config.get("JUMP_HOST", DEFAULT_CREDENTIALS["JUMP_HOST"])
    
    # Validate jump host IP with retry
    while True:
        jump_host = input(f"{Fore.CYAN}Jump Host IP [{current_jump_host}]: {Style.RESET_ALL}").strip()
        if not jump_host:
            jump_host = current_jump_host
        
        if validate_ip_address(jump_host) or validate_hostname(jump_host):
            break
        else:
            print(f"{Fore.RED}❌ Invalid IP address or hostname format. Please try again.{Style.RESET_ALL}")
    
    current_jump_user = app_config.get("JUMP_USERNAME", DEFAULT_CREDENTIALS["JUMP_USERNAME"])
    jump_username = input(f"{Fore.CYAN}Jump Host Username [{current_jump_user}]: {Style.RESET_ALL}").strip()
    if not jump_username:
        jump_username = current_jump_user
    
    # Secure password input with default
    current_jump_pass = app_config.get("JUMP_PASSWORD", "")
    if current_jump_pass:
        jump_password = getpass.getpass(f"{Fore.CYAN}Jump Host Password [current: {mask_password(current_jump_pass)}]: {Style.RESET_ALL}")
        if not jump_password:
            jump_password = current_jump_pass
    else:
        jump_password = getpass.getpass(f"{Fore.CYAN}Jump Host Password [{DEFAULT_CREDENTIALS['JUMP_PASSWORD']}]: {Style.RESET_ALL}")
        if not jump_password:
            jump_password = DEFAULT_CREDENTIALS["JUMP_PASSWORD"]
    
    # Device credentials
    print(f"\n{Fore.WHITE}Cisco Device Credentials:{Style.RESET_ALL}")
    
    current_device_user = app_config.get("DEVICE_USERNAME", DEFAULT_CREDENTIALS["DEVICE_USERNAME"])
    device_username = input(f"{Fore.CYAN}Device Username [{current_device_user}]: {Style.RESET_ALL}").strip()
    if not device_username:
        device_username = current_device_user
    
    # Secure password input with default
    current_device_pass = app_config.get("DEVICE_PASSWORD", "")
    if current_device_pass:
        device_password = getpass.getpass(f"{Fore.CYAN}Device Password [current: {mask_password(current_device_pass)}]: {Style.RESET_ALL}")
        if not device_password:
            device_password = current_device_pass
    else:
        device_password = getpass.getpass(f"{Fore.CYAN}Device Password [{DEFAULT_CREDENTIALS['DEVICE_PASSWORD']}]: {Style.RESET_ALL}")
        if not device_password:
            device_password = DEFAULT_CREDENTIALS["DEVICE_PASSWORD"]
    
    # Update configuration
    app_config.update({
        "JUMP_HOST": jump_host,
        "JUMP_USERNAME": jump_username,
        "JUMP_PASSWORD": jump_password,
        "DEVICE_USERNAME": device_username,
        "DEVICE_PASSWORD": device_password
    })
    
    # Test connectivity if requested
    print(f"\n{Fore.YELLOW}🔍 Connection Test (Optional){Style.RESET_ALL}")
    test_conn = input(f"{Fore.CYAN}Test jump host connectivity? [y/N]: {Style.RESET_ALL}").strip().lower()
    if test_conn in ['y', 'yes']:
        print(f"{Fore.CYAN}Testing connectivity to {jump_host}...{Style.RESET_ALL}")
        if ping_host(jump_host):
            log_success(f"✅ Jump host {jump_host} is reachable")
        else:
            log_warning(f"⚠️ Jump host {jump_host} is not reachable via ping")
    
    # Save to .env-t file
    save_config_to_env()
    
    log_success("Credentials configured successfully")

def save_config_to_env():
    """Save configuration to .env-t file"""
    try:
        env_path = get_env_file_path()
        
        # Save all configuration including passwords to .env-t file
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# NetAuditPro CLI Lite Configuration File\n")
            f.write("# This file contains sensitive credentials - keep secure\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("# Jump Host Configuration\n")
            f.write(f"JUMP_HOST={app_config.get('JUMP_HOST', '')}\n")
            f.write(f"JUMP_USERNAME={app_config.get('JUMP_USERNAME', '')}\n")
            f.write(f"JUMP_PASSWORD={app_config.get('JUMP_PASSWORD', '')}\n\n")
            
            f.write("# Device Credentials\n")
            f.write(f"DEVICE_USERNAME={app_config.get('DEVICE_USERNAME', '')}\n")
            f.write(f"DEVICE_PASSWORD={app_config.get('DEVICE_PASSWORD', '')}\n\n")
            
            f.write("# Inventory Configuration\n")
            f.write(f"INVENTORY_FILE={app_config.get('INVENTORY_FILE', DEFAULT_CSV_FILENAME)}\n")
        
        log_debug(f"Configuration saved to {env_path}")
        log_success(f"Credentials saved to {env_path}")
    except Exception as e:
        log_warning(f"Could not save configuration to .env-t file: {e}")

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
        
        # Suggest creating a sample inventory file
        create_sample = input(f"{Fore.CYAN}Create a sample inventory file? [y/N]: {Style.RESET_ALL}").strip().lower()
        if create_sample in ['y', 'yes']:
            create_sample_inventory(inventory_path)
            return load_inventory(filename)  # Retry loading
        return False
    
    try:
        devices = []
        invalid_rows = []
        
        with open(inventory_path, 'r', newline='', encoding='utf-8') as csvfile:
            # Detect delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            try:
                delimiter = sniffer.sniff(sample).delimiter
            except csv.Error:
                delimiter = ','  # Default to comma
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # Validate CSV headers
            required_headers = ['ip_address', 'hostname']
            available_headers = [h.lower().strip() for h in reader.fieldnames if h]
            
            # Check for common variations of required headers
            ip_headers = ['ip', 'ip_address', 'management_ip', 'host']
            hostname_headers = ['hostname', 'name', 'device_name']
            
            has_ip = any(h in available_headers for h in ip_headers)
            has_hostname = any(h in available_headers for h in hostname_headers)
            
            if not has_ip:
                log_error(f"CSV file missing IP address column. Expected one of: {', '.join(ip_headers)}")
                return False
            
            for row_num, row in enumerate(reader, start=2):
                # Map CSV columns to standard format
                device = map_csv_columns(row)
                
                # Validate required fields
                if not device.get("ip_address"):
                    invalid_rows.append(f"Row {row_num}: Missing IP address")
                    continue
                
                # Validate IP address format
                if not validate_ip_address(device["ip_address"]):
                    invalid_rows.append(f"Row {row_num}: Invalid IP address format: {device['ip_address']}")
                    continue
                
                # Set default hostname if not provided
                if not device.get("hostname"):
                    device["hostname"] = f"Device_{device['ip_address'].replace('.', '_')}"
                
                devices.append(device)
        
        # Report validation results
        if invalid_rows:
            log_warning(f"Found {len(invalid_rows)} invalid rows:")
            for error in invalid_rows[:5]:  # Show first 5 errors
                log_warning(f"  {error}")
            if len(invalid_rows) > 5:
                log_warning(f"  ... and {len(invalid_rows) - 5} more errors")
        
        if not devices:
            log_error("No valid devices found in inventory file")
            return False
        
        active_inventory_data["data"] = devices
        total_devices = len(devices)
        
        log_success(f"Loaded {total_devices} valid devices from {inventory_path}")
        if invalid_rows:
            log_warning(f"Skipped {len(invalid_rows)} invalid entries")
        
        return True
        
    except Exception as e:
        log_error(f"Error loading inventory file: {e}")
        return False

def create_sample_inventory(file_path: str) -> bool:
    """Create a sample inventory file"""
    try:
        # Ensure directory exists
        ensure_path_exists(file_path, is_file=True)
        
        sample_data = [
            ['ip_address', 'hostname', 'device_type', 'description'],
            ['192.168.1.1', 'Router-01', 'cisco_ios', 'Main Gateway Router'],
            ['192.168.1.2', 'Switch-01', 'cisco_ios', 'Core Switch'],
            ['192.168.1.3', 'Router-02', 'cisco_ios', 'Backup Router'],
        ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(sample_data)
        
        log_success(f"Sample inventory file created: {file_path}")
        log_message("Please edit the file with your actual device information")
        return True
        
    except Exception as e:
        log_error(f"Failed to create sample inventory file: {e}")
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
    """Establish SSH connection to jump host with comprehensive debugging"""
    jump_host = app_config.get("JUMP_HOST")
    jump_username = app_config.get("JUMP_USERNAME")
    jump_password = app_config.get("JUMP_PASSWORD")
    
    log_function_entry("establish_jump_host_connection", {
        "jump_host": jump_host,
        "jump_username": jump_username,
        "jump_password": "***MASKED***"
    })
    
    if not all([jump_host, jump_username, jump_password]):
        missing = []
        if not jump_host: missing.append("JUMP_HOST")
        if not jump_username: missing.append("JUMP_USERNAME") 
        if not jump_password: missing.append("JUMP_PASSWORD")
        log_error(f"Jump host credentials not configured. Missing: {missing}")
        log_function_exit("establish_jump_host_connection", "Failed - missing credentials")
        return None
    
    log_network(f"Attempting connection to jump host {jump_host} as user {jump_username}")
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        attempt_start_time = time.time()
        log_debug(f"Connection attempt {attempt}/{max_retries} to {jump_host}")
        
        try:
            # Test local connectivity first
            log_trace("Testing local connectivity to jump host")
            ping_start = time.time()
            ping_result = ping_host(jump_host)
            ping_duration = time.time() - ping_start
            
            if ping_result:
                log_network(f"Jump host {jump_host} is reachable via ping ({ping_duration:.2f}s)")
            else:
                log_warning(f"Jump host {jump_host} not reachable via local ping ({ping_duration:.2f}s) - continuing anyway")
            
            # Create SSH client with enhanced settings
            log_trace("Creating SSH client with enhanced settings")
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Enhanced connection parameters
            connect_params = {
                'hostname': jump_host,
                'port': 22,
                'username': jump_username,
                'password': jump_password,
                'timeout': 30,
                'auth_timeout': 30,
                'banner_timeout': 30,
                'look_for_keys': False,  # Don't look for SSH keys
                'allow_agent': False,    # Don't use SSH agent
            }
            
            log_trace(f"SSH connection parameters: {dict((k, v if k != 'password' else '***MASKED***') for k, v in connect_params.items())}")
            
            # Connect with timeout
            connect_start = time.time()
            log_debug(f"Initiating SSH connection to {jump_host}:22")
            ssh_client.connect(**connect_params)
            connect_duration = time.time() - connect_start
            log_performance(f"SSH connection established in {connect_duration:.2f}s")
            
            # Test the connection by executing a simple command
            log_trace("Testing connection with echo command")
            test_start = time.time()
            stdin, stdout, stderr = ssh_client.exec_command('echo "Connection test"', timeout=10)
            test_result = stdout.read().decode('utf-8').strip()
            test_duration = time.time() - test_start
            
            if "Connection test" in test_result:
                total_duration = time.time() - attempt_start_time
                log_success(f"Connected to jump host {jump_host} (total time: {total_duration:.2f}s)")
                log_performance(f"Connection test completed in {test_duration:.2f}s")
                log_function_exit("establish_jump_host_connection", "Success")
                return ssh_client
            else:
                raise Exception(f"Connection test failed - unexpected response: '{test_result}'")
                
        except paramiko.AuthenticationException as e:
            attempt_duration = time.time() - attempt_start_time
            log_error(f"Authentication failed for jump host {jump_host} (attempt {attempt}, {attempt_duration:.2f}s)")
            log_trace(f"Authentication exception details: {e}")
            if attempt == max_retries:
                log_error("All authentication attempts failed. Please check credentials.")
                log_function_exit("establish_jump_host_connection", "Failed - authentication")
                return None
            log_debug(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            
        except paramiko.SSHException as e:
            attempt_duration = time.time() - attempt_start_time
            log_error(f"SSH connection failed to jump host {jump_host} (attempt {attempt}, {attempt_duration:.2f}s): {e}")
            log_trace(f"SSH exception details: {type(e).__name__}: {e}")
            if attempt == max_retries:
                log_function_exit("establish_jump_host_connection", "Failed - SSH error")
                return None
            log_debug(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            
        except Exception as e:
            attempt_duration = time.time() - attempt_start_time
            log_error(f"Failed to connect to jump host {jump_host} (attempt {attempt}, {attempt_duration:.2f}s): {e}")
            log_exception("establish_jump_host_connection", e)
            if attempt == max_retries:
                log_function_exit("establish_jump_host_connection", "Failed - general error")
                return None
            log_debug(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    log_function_exit("establish_jump_host_connection", "Failed - max retries exceeded")
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
                'jump_password': mask_password(app_config.get('JUMP_PASSWORD', '')),
                'device_username': app_config.get('DEVICE_USERNAME'),
                'device_password': mask_password(app_config.get('DEVICE_PASSWORD', '')),
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
            f.write(f"Jump Username: {app_config.get('JUMP_USERNAME')}\n")
            f.write(f"Jump Password: {mask_password(app_config.get('JUMP_PASSWORD', ''))}\n")
            f.write(f"Device Username: {app_config.get('DEVICE_USERNAME')}\n")
            f.write(f"Device Password: {mask_password(app_config.get('DEVICE_PASSWORD', ''))}\n")
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
    """Parse command-line arguments with enhanced debugging options"""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} {APP_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Interactive mode with prompts
  %(prog)s --inventory routers.csv  # Use specific inventory file
  %(prog)s --config                 # Configure credentials only
  %(prog)s --quiet                  # Minimal output (errors only)
  %(prog)s --verbose                # Verbose output (info + debug)
  %(prog)s --debug                  # Debug output (info + debug + trace)
  %(prog)s --trace                  # Maximum debug output (all levels)
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
    
    # Debug level options (mutually exclusive)
    debug_group = parser.add_mutually_exclusive_group()
    
    debug_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output (errors only) - Debug level 0'
    )
    
    debug_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output (info + debug) - Debug level 1'
    )
    
    debug_group.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Debug output (info + debug + trace) - Debug level 2'
    )
    
    debug_group.add_argument(
        '--trace', '-t',
        action='store_true',
        help='Maximum debug output (all levels) - Debug level 3'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} {APP_VERSION}'
    )
    
    return parser.parse_args()

def main():
    """Main CLI application entry point with enhanced debugging"""
    global interrupted
    
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Set debug level based on arguments
        if args.trace:
            set_debug_level(3)
            log_debug("Debug level set to TRACE (3)")
        elif args.debug:
            set_debug_level(2)
            log_debug("Debug level set to DEBUG (2)")
        elif args.verbose:
            set_debug_level(1)
            log_debug("Debug level set to VERBOSE (1)")
        elif args.quiet:
            set_debug_level(-1)  # Even less than INFO
        else:
            set_debug_level(0)  # Default INFO level
        
        log_function_entry("main", {"debug_level": DEBUG_LEVEL, "args": vars(args)})
        
        # Print banner
        if not args.quiet:
            print_banner()
        
        log_debug(f"NetAuditPro CLI Lite {APP_VERSION} starting")
        log_debug(f"Platform: {PLATFORM}, Python: {sys.version}")
        log_debug(f"Working directory: {os.getcwd()}")

        # Load configuration
        log_debug("Loading application configuration")
        load_app_config()
        
        # Handle configuration-only mode
        if args.config:
            log_debug("Configuration-only mode requested")
            prompt_for_credentials()
            log_success("Configuration completed. Exiting.")
            log_function_exit("main", "Config mode completed")
            return 0
        
        # Prompt for credentials if not provided
        log_debug("Validating credentials")
        if not validate_credentials():
            if not args.quiet:
                print(f"\n{Fore.YELLOW}Credentials not found or incomplete.{Style.RESET_ALL}")
            log_debug("Credentials incomplete, prompting user")
            prompt_for_credentials()
        else:
            log_debug("All required credentials are available")
        
        # Load inventory
        if args.inventory:
            log_debug(f"Custom inventory file specified: {args.inventory}")
            app_config["INVENTORY_FILE"] = args.inventory
        
        log_debug("Loading device inventory")
        if not load_inventory():
            log_debug("Inventory loading failed, prompting user")
            if not prompt_for_inventory():
                log_error("Could not load inventory file. Exiting.")
                log_function_exit("main", "Failed - no inventory")
                return 1
        
        # Validate we have devices to audit
        if total_devices == 0:
            log_error("No devices found in inventory. Exiting.")
            log_function_exit("main", "Failed - no devices")
            return 1
        
        log_success(f"Ready to audit {total_devices} devices")
        
        # Display pre-audit summary
        if not args.quiet:
            print(f"\n{Fore.CYAN}📋 AUDIT PREPARATION{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Devices to audit: {Fore.CYAN}{total_devices}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Jump host: {Fore.CYAN}{app_config.get('JUMP_HOST')}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Jump username: {Fore.CYAN}{app_config.get('JUMP_USERNAME')}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Jump password: {Fore.CYAN}{mask_password(app_config.get('JUMP_PASSWORD', ''))}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Device username: {Fore.CYAN}{app_config.get('DEVICE_USERNAME')}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Device password: {Fore.CYAN}{mask_password(app_config.get('DEVICE_PASSWORD', ''))}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Inventory file: {Fore.CYAN}{app_config.get('INVENTORY_FILE')}{Style.RESET_ALL}")
        
        # Confirm before starting
        if not args.quiet:
            confirm = input(f"\n{Fore.YELLOW}Start audit? [Y/n]: {Style.RESET_ALL}").strip().lower()
            if confirm in ['n', 'no']:
                log_message("Audit cancelled by user.")
                log_function_exit("main", "User cancelled")
                return 0
        
        # Start audit
        log_message("🚀 Starting NetAuditPro CLI Lite audit...")
        audit_start_time = time.time()
        
        # Run the complete audit
        log_debug("Starting complete audit process")
        audit_success = run_complete_audit()
        audit_end_time = time.time()
        
        log_performance(f"Total audit time: {format_duration(audit_end_time - audit_start_time)}")
        
        # Generate reports if audit completed (successfully or with some failures)
        if audit_success or device_results:
            log_message("📊 Generating audit reports...")
            
            # Save results in multiple formats
            report_start = time.time()
            save_audit_results_to_csv()
            save_audit_results_to_json()
            save_command_logs()
            generate_audit_summary_report()
            report_end = time.time()
            
            log_performance(f"Report generation time: {format_duration(report_end - report_start)}")
            log_success("All audit reports generated successfully")
        
        if not args.quiet:
            print()  # New line after progress bar
            print_summary_statistics()
        
        # Return appropriate exit code
        exit_code = 0
        if interrupted:
            exit_code = 130  # Standard exit code for SIGINT
            log_debug("Exiting with SIGINT code")
        elif audit_success:
            exit_code = 0
            log_debug("Exiting with success code")
        else:
            exit_code = 1
            log_debug("Exiting with failure code")
        
        log_function_exit("main", f"Exit code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Audit interrupted by user{Style.RESET_ALL}")
        log_debug("Keyboard interrupt received")
        log_function_exit("main", "Interrupted")
        return 130
    except Exception as e:
        log_exception("main", e)
        log_error(f"Unexpected error: {e}")
        log_function_exit("main", "Exception")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
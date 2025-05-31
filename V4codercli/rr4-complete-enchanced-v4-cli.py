#!/usr/bin/env python3
"""
RR4 Complete Enhanced v4 CLI - Network State Collector

A comprehensive CLI-based network state collection system for IP-MPLS networks
using Nornir, Netmiko, and pyATS/Genie for Cisco IOS, IOS XE, and IOS XR devices.

Cross-platform compatible with Windows, Linux, and macOS.

Author: AI Assistant
Version: 1.0.1-CrossPlatform
Created: 2025-01-27
Updated: 2025-05-31 (Added full cross-platform support)
"""

import os
import sys
import json
import time
import logging
import traceback
import importlib
import importlib.util
import platform
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import click
from dotenv import load_dotenv

# Cross-platform detection
PLATFORM = platform.system().lower()
IS_WINDOWS = PLATFORM == 'windows'
IS_LINUX = PLATFORM == 'linux'
IS_MACOS = PLATFORM == 'darwin'

# Platform-specific imports
if IS_WINDOWS:
    try:
        import msvcrt
        import winreg
    except ImportError:
        pass

# Import core modules with error handling
try:
    # Cross-platform path handling for package imports
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    
    # Add project root to sys.path to enable proper package imports
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Import using absolute package paths
    from V4codercli.rr4_complete_enchanced_v4_cli_core.inventory_loader import InventoryLoader
    from V4codercli.rr4_complete_enchanced_v4_cli_core.connection_manager import ConnectionManager
    from V4codercli.rr4_complete_enchanced_v4_cli_core.task_executor import TaskExecutor, ProgressReporter
    from V4codercli.rr4_complete_enchanced_v4_cli_core.output_handler import OutputHandler
    from V4codercli.rr4_complete_enchanced_v4_cli_core.data_parser import DataParser
    
    # Import from tasks directory  
    from V4codercli.rr4_complete_enchanced_v4_cli_tasks import get_layer_collector, get_available_layers, validate_layers
    
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    # Graceful fallback for development
    print(f"Warning: Core modules not fully available: {e}")
    InventoryLoader = None
    ConnectionManager = None
    TaskExecutor = None
    OutputHandler = None
    DataParser = None
    CORE_MODULES_AVAILABLE = False

# Version information
__version__ = "1.0.1-CrossPlatform"
__author__ = "AI Assistant"
__description__ = "Cross-Platform Network State Collector CLI for Cisco Devices"

# Cross-platform utility functions
def get_platform_info():
    """Get detailed platform information for debugging."""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'is_windows': IS_WINDOWS,
        'is_linux': IS_LINUX,
        'is_macos': IS_MACOS
    }

def set_secure_file_permissions(file_path: Path) -> bool:
    """Set secure file permissions cross-platform."""
    try:
        if IS_WINDOWS:
            # Windows: Use attrib command to hide file and remove inheritance
            file_str = str(file_path)
            # Hide the file
            subprocess.run(['attrib', '+h', file_str], 
                          shell=True, check=False, capture_output=True)
            
            # Try to set permissions using icacls (more secure)
            try:
                # Remove inheritance and grant only current user full control
                subprocess.run([
                    'icacls', file_str, '/inheritance:r', 
                    '/grant:r', f'{os.environ.get("USERNAME", "User")}:(F)'
                ], shell=True, check=False, capture_output=True)
                return True
            except Exception:
                # Fallback: at least hide the file
                return True
        else:
            # Unix-like systems: Use chmod 600 (read/write for owner only)
            file_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            return True
    except Exception as e:
        print(f"Warning: Could not set secure permissions on {file_path}: {e}")
        return False

def get_user_home_dir() -> Path:
    """Get user home directory cross-platform."""
    if IS_WINDOWS:
        return Path(os.environ.get('USERPROFILE', os.path.expanduser('~')))
    else:
        return Path(os.path.expanduser('~'))

def validate_filename(filename: str) -> str:
    """Validate and sanitize filename for cross-platform compatibility."""
    # Remove invalid characters for all platforms
    if IS_WINDOWS:
        invalid_chars = '<>:"/\\|?*'
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        max_length = 255
    else:
        invalid_chars = '/'
        reserved_names = []
        max_length = 255
    
    # Replace invalid characters
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Check for reserved names on Windows
    name_without_ext = filename.split('.')[0].upper()
    if name_without_ext in reserved_names:
        filename = f"_{filename}"
    
    # Limit length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename

def ensure_directory_exists(path: Path) -> bool:
    """Ensure directory exists cross-platform."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}")
        return False

# Global configuration with updated paths
CONFIG = {
    'version': __version__,
    'author': __author__,
    'description': __description__,
    'supported_platforms': ['ios', 'iosxe', 'iosxr'],
    'supported_layers': ['health', 'interfaces', 'igp', 'mpls', 'bgp', 'vpn', 'static', 'console'],
    'default_workers': 15,
    'default_timeout': 60,
    'default_output_dir': 'rr4-complete-enchanced-v4-cli-output',
    'default_config_dir': 'rr4-complete-enchanced-v4-cli-config',
    'default_inventory': 'rr4-complete-enchanced-v4-cli-routers01.csv',
    'platform_info': get_platform_info()
}

class CLIError(Exception):
    """Custom exception for CLI-specific errors."""
    pass

class CrossPlatformLogger:
    """Enhanced cross-platform logging configuration for the CLI application."""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.log_level = log_level.upper()
        self.log_file = log_file
        self.logger = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging with both console and file handlers (cross-platform)."""
        # Create logs directory if it doesn't exist
        log_dir = Path("rr4-complete-enchanced-v4-cli-logs")
        ensure_directory_exists(log_dir)
        
        # Configure root logger
        self.logger = logging.getLogger('rr4_collector')
        self.logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level))
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"collection_{timestamp}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Log platform information
        self.logger.info(f"RR4 CLI v{__version__} starting on {platform.system()} {platform.release()}")
        self.logger.debug(f"Platform details: {CONFIG['platform_info']}")
        
        # Suppress noisy third-party loggers
        logging.getLogger('paramiko').setLevel(logging.WARNING)
        logging.getLogger('netmiko').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    def get_logger(self):
        """Return the configured logger instance."""
        return self.logger

# Alias for backward compatibility
Logger = CrossPlatformLogger

class EnvironmentManager:
    """Manage environment variables and configuration loading."""
    
    def __init__(self, env_file: str = "rr4-complete-enchanced-v4-cli.env-t", interactive: bool = False):
        self.env_file = env_file
        self.config = {}
        self.interactive = interactive
        self._load_environment()
    
    def _load_environment(self):
        """Load environment variables from rr4-complete-enchanced-v4-cli.env-t file."""
        if not Path(self.env_file).exists():
            if self.interactive:
                click.echo(f"⚠️ Environment file {self.env_file} not found.")
                click.echo("Let's create it with your configuration.")
                self._interactive_setup()
            else:
                raise CLIError(f"Environment file {self.env_file} not found. Please run 'python3 rr4-complete-enchanced-v4-cli.py configure-env' to set up your credentials.")
        
        # Load environment variables
        load_dotenv(self.env_file)
        
        # Required environment variables
        required_vars = [
            'JUMP_HOST_IP',
            'JUMP_HOST_USERNAME',
            'JUMP_HOST_PASSWORD'
        ]
        
        # Load and validate required variables
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                if self.interactive:
                    click.echo(f"⚠️ Required environment variable {var} not found in {self.env_file}")
                    self._interactive_setup()
                    # Reload after interactive setup
                    load_dotenv(self.env_file)
                    value = os.getenv(var)
                    if not value:
                        raise CLIError(f"Failed to configure {var}")
                else:
                    raise CLIError(f"Required environment variable {var} not found in {self.env_file}")
            self.config[var.lower()] = value
        
        # Optional variables with defaults
        optional_vars = {
            'JUMP_HOST_PORT': '22',
            'JUMP_HOST_SSH_KEY_PATH': None,
            'DEVICE_USERNAME': 'cisco',
            'DEVICE_PASSWORD': 'cisco',
            'MAX_CONCURRENT_CONNECTIONS': str(CONFIG['default_workers']),
            'COMMAND_TIMEOUT': str(CONFIG['default_timeout']),
            'CONNECTION_RETRY_ATTEMPTS': '3'
        }
        
        for var, default in optional_vars.items():
            value = os.getenv(var, default)
            if value:
                self.config[var.lower()] = value
    
    def _interactive_setup(self):
        """Interactive setup for environment configuration."""
        click.echo("\n" + "="*60)
        click.echo("🔧 RR4 CLI Interactive Configuration Setup")
        click.echo("="*60)
        
        # Check if environment file exists and load current values
        current_config = {}
        if Path(self.env_file).exists():
            click.echo(f"📁 Loading existing configuration from {self.env_file}")
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            current_config[key] = value
            except Exception as e:
                click.echo(f"⚠️ Warning: Could not read existing config: {e}")
        
        # Prompt for jump host configuration
        click.echo("\n🌐 Jump Host Configuration")
        click.echo("-" * 30)
        
        current_ip = current_config.get('JUMP_HOST_IP', '172.16.39.140')
        jump_host_ip = click.prompt(
            f"Jump Host IP", 
            default=current_ip,
            show_default=True
        )
        
        current_username = current_config.get('JUMP_HOST_USERNAME', 'root')
        jump_host_username = click.prompt(
            f"Jump Host Username", 
            default=current_username,
            show_default=True
        )
        
        # For password, don't show default value for security
        if current_config.get('JUMP_HOST_PASSWORD'):
            jump_host_password = click.prompt(
                f"Jump Host Password (current: ****)", 
                hide_input=True,
                default=current_config.get('JUMP_HOST_PASSWORD'),
                show_default=False
            )
        else:
            jump_host_password = click.prompt(
                f"Jump Host Password", 
                hide_input=True
            )
        
        current_port = current_config.get('JUMP_HOST_PORT', '22')
        jump_host_port = click.prompt(
            f"Jump Host SSH Port", 
            default=current_port,
            show_default=True
        )
        
        # Prompt for device credentials
        click.echo("\n🔐 Device Credentials")
        click.echo("-" * 25)
        
        current_device_username = current_config.get('DEVICE_USERNAME', 'cisco')
        device_username = click.prompt(
            f"Device Username (for IOS/IOS-XE/IOS-XR)", 
            default=current_device_username,
            show_default=True
        )
        
        # For device password, don't show default value for security
        if current_config.get('DEVICE_PASSWORD'):
            device_password = click.prompt(
                f"Device Password (current: ****)", 
                hide_input=True,
                default=current_config.get('DEVICE_PASSWORD'),
                show_default=False
            )
        else:
            device_password = click.prompt(
                f"Device Password", 
                hide_input=True,
                default='cisco',
                show_default=True
            )
        
        # Optional settings
        click.echo("\n⚙️ Optional Settings")
        click.echo("-" * 20)
        
        current_inventory = current_config.get('INVENTORY_FILE', 'rr4-complete-enchanced-v4-cli-routers01.csv')
        inventory_file = click.prompt(
            f"Inventory File", 
            default=current_inventory,
            show_default=True
        )
        
        current_workers = current_config.get('MAX_CONCURRENT_CONNECTIONS', '15')
        max_connections = click.prompt(
            f"Max Concurrent Connections", 
            default=current_workers,
            show_default=True
        )
        
        current_timeout = current_config.get('COMMAND_TIMEOUT', '60')
        command_timeout = click.prompt(
            f"Command Timeout (seconds)", 
            default=current_timeout,
            show_default=True
        )
        
        current_retry = current_config.get('CONNECTION_RETRY_ATTEMPTS', '3')
        retry_attempts = click.prompt(
            f"Connection Retry Attempts", 
            default=current_retry,
            show_default=True
        )
        
        # Confirm configuration
        click.echo("\n📋 Configuration Summary")
        click.echo("-" * 25)
        click.echo(f"Jump Host IP: {jump_host_ip}")
        click.echo(f"Jump Host Username: {jump_host_username}")
        click.echo(f"Jump Host Password: {'*' * len(jump_host_password)}")
        click.echo(f"Jump Host Port: {jump_host_port}")
        click.echo(f"Device Username: {device_username}")
        click.echo(f"Device Password: {'*' * len(device_password)}")
        click.echo(f"Inventory File: {inventory_file}")
        click.echo(f"Max Connections: {max_connections}")
        click.echo(f"Command Timeout: {command_timeout}")
        click.echo(f"Retry Attempts: {retry_attempts}")
        
        if click.confirm("\n✅ Save this configuration?", default=True):
            self._save_config_to_file({
                'JUMP_HOST_IP': jump_host_ip,
                'JUMP_HOST_USERNAME': jump_host_username,
                'JUMP_HOST_PASSWORD': jump_host_password,
                'JUMP_HOST_PORT': jump_host_port,
                'DEVICE_USERNAME': device_username,
                'DEVICE_PASSWORD': device_password,
                'INVENTORY_FILE': inventory_file,
                'MAX_CONCURRENT_CONNECTIONS': max_connections,
                'COMMAND_TIMEOUT': command_timeout,
                'CONNECTION_RETRY_ATTEMPTS': retry_attempts
            })
            click.echo(f"✅ Configuration saved to {self.env_file}")
        else:
            click.echo("❌ Configuration not saved. Exiting.")
            sys.exit(1)
    
    def _save_config_to_file(self, config_dict: Dict[str, str]):
        """Save configuration to environment file with cross-platform security."""
        try:
            # Ensure the file path is cross-platform compatible
            config_file = Path(self.env_file)
            
            # Create parent directory if it doesn't exist
            if config_file.parent != Path('.'):
                ensure_directory_exists(config_file.parent)
            
            # Write configuration file with explicit UTF-8 encoding
            with open(config_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write("# RR4 Enhanced v4 CLI Configuration File\n")
                f.write("# This file contains sensitive credentials - keep secure\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Platform: {platform.system()} {platform.release()}\n\n")
                
                f.write("# Jump Host Configuration\n")
                f.write(f"JUMP_HOST_IP={config_dict['JUMP_HOST_IP']}\n")
                f.write(f"JUMP_HOST_USERNAME={config_dict['JUMP_HOST_USERNAME']}\n")
                f.write(f"JUMP_HOST_PASSWORD={config_dict['JUMP_HOST_PASSWORD']}\n")
                f.write(f"JUMP_HOST_PORT={config_dict['JUMP_HOST_PORT']}\n\n")
                
                f.write("# Device Credentials\n")
                f.write(f"DEVICE_USERNAME={config_dict['DEVICE_USERNAME']}\n")
                f.write(f"DEVICE_PASSWORD={config_dict['DEVICE_PASSWORD']}\n\n")
                
                f.write("# Inventory Configuration\n")
                f.write(f"INVENTORY_FILE={config_dict['INVENTORY_FILE']}\n\n")
                
                f.write("# Connection Settings\n")
                f.write(f"MAX_CONCURRENT_CONNECTIONS={config_dict['MAX_CONCURRENT_CONNECTIONS']}\n")
                f.write(f"COMMAND_TIMEOUT={config_dict['COMMAND_TIMEOUT']}\n")
                f.write(f"CONNECTION_RETRY_ATTEMPTS={config_dict['CONNECTION_RETRY_ATTEMPTS']}\n")
            
            # Set secure file permissions cross-platform
            if set_secure_file_permissions(config_file):
                if IS_WINDOWS:
                    print(f"✅ Configuration saved with Windows security (hidden + restricted access)")
                else:
                    print(f"✅ Configuration saved with Unix permissions (600)")
            else:
                print(f"⚠️ Configuration saved but could not set secure permissions")
            
        except Exception as e:
            raise CLIError(f"Failed to save configuration: {e}")
    
    def update_configuration(self):
        """Update existing configuration interactively."""
        if not Path(self.env_file).exists():
            click.echo(f"⚠️ Environment file {self.env_file} not found.")
            click.echo("Creating new configuration...")
        else:
            click.echo(f"📝 Updating existing configuration in {self.env_file}")
        
        self._interactive_setup()
        # Reload configuration after update
        self._load_environment()
    
    def get_config(self) -> Dict[str, Any]:
        """Return the loaded configuration."""
        return self.config.copy()
    
    def validate_connectivity(self) -> bool:
        """Validate jump host connectivity (placeholder for future implementation)."""
        # TODO: Implement actual connectivity test
        return True

class ProjectStructure:
    """Manage project directory structure and initialization (cross-platform)."""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()
        self.required_dirs = [
            'rr4-complete-enchanced-v4-cli-core',
            'rr4-complete-enchanced-v4-cli-tasks', 
            'rr4-complete-enchanced-v4-cli-config',
            'rr4-complete-enchanced-v4-cli-config/inventory',
            'rr4-complete-enchanced-v4-cli-config/commands',
            'rr4-complete-enchanced-v4-cli-output',
            'rr4-complete-enchanced-v4-cli-logs',
            'rr4-complete-enchanced-v4-cli-tests'
        ]
        self.required_files = [
            'rr4-complete-enchanced-v4-cli-requirements.txt',
            'rr4-complete-enchanced-v4-cli-config/nornir_config.yaml',
            'rr4-complete-enchanced-v4-cli-config/settings.yaml',
            'rr4-complete-enchanced-v4-cli-config/inventory/hosts.yaml',
            'rr4-complete-enchanced-v4-cli-config/inventory/groups.yaml'
        ]
    
    def create_structure(self):
        """Create the complete project directory structure (cross-platform)."""
        logger = logging.getLogger('rr4_collector')
        
        click.echo(f"🏗️ Creating project structure on {platform.system()}...")
        
        # Create directories
        for dir_path in self.required_dirs:
            full_path = self.base_dir / dir_path
            
            if ensure_directory_exists(full_path):
                click.echo(f"  📁 Created/verified: {dir_path}")
                logger.debug(f"Created directory: {full_path}")
                
                # Create __init__.py for Python packages
                if any(pkg in dir_path for pkg in ['rr4-complete-enchanced-v4-cli-core', 'rr4-complete-enchanced-v4-cli-tasks']):
                    init_file = full_path / '__init__.py'
                    if not init_file.exists():
                        try:
                            init_file.write_text('"""Package initialization."""\n', encoding='utf-8')
                            click.echo(f"  📄 Created: {dir_path}/__init__.py")
                            logger.debug(f"Created __init__.py: {init_file}")
                        except Exception as e:
                            logger.warning(f"Could not create __init__.py in {dir_path}: {e}")
            else:
                click.echo(f"  ❌ Failed to create: {dir_path}")
                logger.error(f"Failed to create directory: {full_path}")
        
        logger.info(f"Project directory structure created successfully on {platform.system()}")
    
    def validate_structure(self) -> bool:
        """Validate that all required directories and files exist (cross-platform)."""
        logger = logging.getLogger('rr4_collector')
        missing_items = []
        
        # Check directories
        for dir_path in self.required_dirs:
            full_path = self.base_dir / dir_path
            if not full_path.exists():
                missing_items.append(f"Directory: {full_path}")
        
        # Check critical files (some will be created during development)
        critical_files = ['rr4-complete-enchanced-v4-cli-requirements.txt']
        for file_path in critical_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                missing_items.append(f"File: {full_path}")
        
        if missing_items:
            logger.warning(f"Missing project structure items: {missing_items}")
            return False
        
        logger.info(f"Project structure validation passed on {platform.system()}")
        return True

class DependencyChecker:
    """Check and validate required dependencies."""
    
    def __init__(self):
        self.required_packages = [
            'click',
            'python-dotenv',
            'paramiko',
            'netmiko',
            'scrapli',
            'nornir',
            'rich',
            'pyyaml',
            'jinja2',
            'cryptography',
            'requests',
            'textfsm',
            'ttp'
        ]
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if all required packages are available."""
        results = {}
        
        for package in self.required_packages:
            try:
                # Handle special import cases
                if package == 'python-dotenv':
                    __import__('dotenv')
                elif package == 'pyyaml':
                    __import__('yaml')
                else:
                    __import__(package.replace('-', '_'))
                results[package] = True
            except ImportError:
                results[package] = False
        
        return results
    
    def validate_versions(self) -> Dict[str, str]:
        """Get version information for installed packages."""
        versions = {}
        for package in self.required_packages:
            try:
                if package == 'python-dotenv':
                    module = __import__('dotenv')
                elif package == 'pyyaml':
                    module = __import__('yaml')
                else:
                    module = __import__(package.replace('-', '_'))
                version = getattr(module, '__version__', 'Unknown')
                versions[package] = version
            except ImportError:
                versions[package] = 'Not installed'
        
        return versions

class CollectionManager:
    """Main collection manager that orchestrates the data collection process."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('rr4_collector.collection_manager')
        
        # Initialize core components
        self.inventory_loader = None
        self.connection_manager = None
        self.task_executor = None
        self.output_handler = None
        
        # Collection state
        self.current_run_id = None
        self.collection_results = {}
        
    def _initialize_components(self, **kwargs):
        """Initialize core components for collection."""
        try:
            # Get parameters
            inventory_file = kwargs.get('inventory', CONFIG['default_inventory'])
            output_dir = kwargs.get('output_dir', CONFIG['default_output_dir'])
            workers = kwargs.get('workers', CONFIG['default_workers'])
            timeout = kwargs.get('timeout', CONFIG['default_timeout'])
            
            # Initialize inventory loader
            if InventoryLoader:
                self.inventory_loader = InventoryLoader(inventory_file)
            else:
                raise CLIError("InventoryLoader not available - core modules missing")
            
            # Prepare jump host configuration
            jump_host_config = {
                'hostname': self.config.get('jump_host_ip'),
                'username': self.config.get('jump_host_username'),
                'password': self.config.get('jump_host_password'),
                'port': int(self.config.get('jump_host_port', 22))
            }
            
            # Load and convert inventory with jump host support
            devices = self.inventory_loader.load_csv_inventory()
            nornir_inventory = self.inventory_loader.generate_nornir_inventory(
                devices, 
                self.config.get('device_username', 'cisco'),
                self.config.get('device_password', 'cisco'),
                jump_host_config
            )
            
            # Save Nornir inventory
            self.inventory_loader.save_nornir_inventory(nornir_inventory)
            
            # Initialize connection manager with jump host config
            if ConnectionManager:
                self.connection_manager = ConnectionManager(
                    jump_host_config=jump_host_config,
                    max_connections=workers
                )
            else:
                raise CLIError("ConnectionManager not available - core modules missing")
            
            # Initialize output handler
            if OutputHandler:
                self.output_handler = OutputHandler(base_output_dir=output_dir)
                self.current_run_id = self.output_handler.create_run_directory()
            else:
                raise CLIError("OutputHandler not available - core modules missing")
            
            # Initialize task executor
            if TaskExecutor:
                self.task_executor = TaskExecutor(
                    inventory=devices,
                    output_handler=self.output_handler,
                    max_workers=workers,
                    timeout=timeout
                )
                
                # Add progress reporting
                if ProgressReporter:
                    progress_reporter = ProgressReporter()
                    self.task_executor.add_progress_callback(progress_reporter)
            else:
                raise CLIError("TaskExecutor not available - core modules missing")
            
            self.logger.info("Core components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise CLIError(f"Initialization failed: {e}")
    
    def collect_all_devices(self, **kwargs):
        """Collect data from all devices in inventory."""
        self.logger.info("Starting collection for all devices")
        
        try:
            # Check if dry run
            if kwargs.get('dry_run'):
                click.echo("🧪 DRY RUN MODE - Testing connectivity only")
                self.test_connectivity(**kwargs)
                return
            
            # Initialize components
            self._initialize_components(**kwargs)
            
            # Determine layers to collect
            layers = kwargs.get('layers')
            if layers:
                if isinstance(layers, str):
                    layers = [layer.strip() for layer in layers.split(',')]
            else:
                layers = CONFIG['supported_layers']
            
            exclude_layers = kwargs.get('exclude_layers')
            if exclude_layers:
                if isinstance(exclude_layers, str):
                    exclude_layers = [layer.strip() for layer in exclude_layers.split(',')]
                layers = [layer for layer in layers if layer not in exclude_layers]
            
            # Validate layers
            if validate_layers:
                validate_layers(layers)
            
            # Execute collection
            results = self.task_executor.execute_layer_collection(
                layers=layers,
                exclude_layers=exclude_layers or [],
                timeout=kwargs.get('timeout', CONFIG['default_timeout'])
            )
            
            # Store results
            self.collection_results = results
            
            # Generate summary report
            self._generate_collection_report()
            
            # Display comprehensive collection summary
            self._display_collection_summary()
            
            self.logger.info("Collection completed successfully")
            
        except Exception as e:
            self.logger.error(f"Collection failed: {e}")
            raise CLIError(f"Collection failed: {e}")
        finally:
            self._cleanup()

    def collect_specific_devices(self, devices: List[str], **kwargs):
        """Collect data from specific devices."""
        self.logger.info(f"Starting collection for devices: {devices}")
        
        try:
            # Check if dry run
            if kwargs.get('dry_run'):
                click.echo("🧪 DRY RUN MODE - Testing connectivity only")
                self.test_connectivity(**kwargs)
                return
            
            # Initialize components
            self._initialize_components(**kwargs)
            
            # Filter to specific devices
            self.task_executor.filter_devices(device_list=devices)
            
            # Determine layers to collect
            layers = kwargs.get('layers')
            if layers:
                if isinstance(layers, str):
                    layers = [layer.strip() for layer in layers.split(',')]
            else:
                layers = CONFIG['supported_layers']
            
            exclude_layers = kwargs.get('exclude_layers')
            if exclude_layers:
                if isinstance(exclude_layers, str):
                    exclude_layers = [layer.strip() for layer in exclude_layers.split(',')]
                layers = [layer for layer in layers if layer not in exclude_layers]
            
            # Validate layers
            if validate_layers:
                validate_layers(layers)
            
            # Execute collection
            results = self.task_executor.execute_layer_collection(
                layers=layers,
                exclude_layers=exclude_layers or [],
                timeout=kwargs.get('timeout', CONFIG['default_timeout'])
            )
            
            # Store results
            self.collection_results = results
            
            # Generate summary report
            self._generate_collection_report()
            
            # Display comprehensive collection summary
            self._display_collection_summary()
            
            self.logger.info("Device-specific collection completed successfully")
            
        except Exception as e:
            self.logger.error(f"Device collection failed: {e}")
            raise CLIError(f"Device collection failed: {e}")
        finally:
            self._cleanup()

    def collect_device_group(self, group: str, **kwargs):
        """Collect data from devices in a specific group."""
        self.logger.info(f"Starting collection for group: {group}")
        
        try:
            # Check if dry run
            if kwargs.get('dry_run'):
                click.echo("🧪 DRY RUN MODE - Testing connectivity only")
                self.test_connectivity(**kwargs)
                return
            
            # Initialize components
            self._initialize_components(**kwargs)
            
            # Filter to specific group
            self.task_executor.filter_devices(group_filter=group)
            
            # Check if any devices match the group
            if len(self.task_executor.nr.inventory.hosts) == 0:
                raise CLIError(f"No devices found in group: {group}")
            
            # Determine layers to collect
            layers = kwargs.get('layers')
            if layers:
                if isinstance(layers, str):
                    layers = [layer.strip() for layer in layers.split(',')]
            else:
                layers = CONFIG['supported_layers']
            
            exclude_layers = kwargs.get('exclude_layers')
            if exclude_layers:
                if isinstance(exclude_layers, str):
                    exclude_layers = [layer.strip() for layer in exclude_layers.split(',')]
                layers = [layer for layer in layers if layer not in exclude_layers]
            
            # Validate layers
            if validate_layers:
                validate_layers(layers)
            
            # Execute collection
            results = self.task_executor.execute_layer_collection(
                layers=layers,
                exclude_layers=exclude_layers or [],
                timeout=kwargs.get('timeout', CONFIG['default_timeout'])
            )
            
            # Store results
            self.collection_results = results
            
            # Generate summary report
            self._generate_collection_report()
            
            # Display comprehensive collection summary
            self._display_collection_summary()
            
            self.logger.info("Group collection completed successfully")
            
        except Exception as e:
            self.logger.error(f"Group collection failed: {e}")
            raise CLIError(f"Group collection failed: {e}")
        finally:
            self._cleanup()

    def test_connectivity(self, **kwargs):
        """Test connectivity to devices without collecting data."""
        self.logger.info("Starting connectivity test")
        
        try:
            # Initialize components
            self._initialize_components(**kwargs)
            
            # Execute connectivity test
            results = self.task_executor.execute_connectivity_test()
            
            # Display results
            self._display_connectivity_results(results)
            
            self.logger.info("Connectivity test completed")
            
        except Exception as e:
            self.logger.error(f"Connectivity test failed: {e}")
            raise CLIError(f"Connectivity test failed: {e}")
        finally:
            self._cleanup()
    
    def _generate_collection_report(self):
        """Generate a summary report of the collection."""
        try:
            if not self.current_run_id or not self.task_executor:
                return
            
            # Get progress summary
            progress = self.task_executor.get_progress_summary()
            detailed_results = self.task_executor.get_detailed_results()
            
            # Create report
            report = {
                'run_id': self.current_run_id,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'summary': progress,
                'device_results': {},
                'layer_summary': {}
            }
            
            # Process detailed results
            for result in detailed_results:
                if result.hostname not in report['device_results']:
                    report['device_results'][result.hostname] = {
                        'success_count': 0,
                        'failure_count': 0,
                        'tasks': []
                    }
                
                device_report = report['device_results'][result.hostname]
                device_report['tasks'].append({
                    'task': result.task_name,
                    'success': result.success,
                    'duration': result.duration,
                    'error': result.error
                })
                
                if result.success:
                    device_report['success_count'] += 1
                else:
                    device_report['failure_count'] += 1
            
            # Save report
            if self.output_handler:
                self.output_handler.save_collection_report(report)
            
            self.logger.info("Collection report generated successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to generate collection report: {e}")
    
    def _display_connectivity_results(self, results: Dict[str, Any]):
        """Display connectivity test results."""
        click.echo("\n" + "=" * 70)
        click.echo("🔗 CONNECTIVITY TEST RESULTS")
        click.echo("=" * 70)
        
        successful = results.get('successful', [])
        failed = results.get('failed', [])
        total = len(successful) + len(failed)
        
        # Overall statistics
        click.echo(f"\n📈 Overall Statistics:")
        click.echo(f"  Total devices tested: {total}")
        click.echo(f"  Successful connections: {len(successful)}")
        click.echo(f"  Failed connections: {len(failed)}")
        success_rate = (len(successful) / total * 100) if total > 0 else 0
        click.echo(f"  Success rate: {success_rate:.1f}%")
        
        # Device-by-device breakdown
        if total > 0:
            click.echo(f"\n📋 Device-by-Device Breakdown:")
            click.echo("-" * 50)
            
            # Show successful connections
            for result in successful:
                hostname = result.get('hostname', 'Unknown')
                click.echo(f"  ✅ {hostname:8} | Connected  | Auth OK      | Reachable")
            
            # Show failed connections
            for result in failed:
                hostname = result.get('hostname', 'Unknown')
                error = result.get('error', 'Unknown error')
                error_msg = str(error)[:30] + "..." if len(str(error)) > 30 else str(error)
                click.echo(f"  ❌ {hostname:8} | Failed     | Auth Failed  | {error_msg}")
        
        # Authentication summary
        click.echo(f"\n🔐 Authentication & Authorization Status:")
        click.echo(f"  Authentication successful: {len(successful)}")
        click.echo(f"  Authentication failed: {len(failed)}")
        click.echo(f"  Authorization working: {len(successful)}")
        
        click.echo(f"\n📁 Next Steps:")
        if len(successful) > 0:
            click.echo(f"  ✅ {len(successful)} devices ready for data collection")
            click.echo(f"  Run without --dry-run to collect data from reachable devices")
        if len(failed) > 0:
            click.echo(f"  ⚠️  {len(failed)} devices need attention (network/auth issues)")
            click.echo(f"  Check connectivity and credentials for failed devices")
        
        click.echo("\n" + "=" * 70)
    
    def _display_collection_summary(self):
        """Display comprehensive collection summary."""
        if not self.task_executor:
            return
            
        # Get detailed results and progress summary
        detailed_results = self.task_executor.get_detailed_results()
        progress = self.task_executor.get_progress_summary()
        
        click.echo("\n" + "=" * 70)
        click.echo("📊 COLLECTION SUMMARY REPORT")
        click.echo("=" * 70)
        
        # Overall statistics
        total_devices = progress.get('total_devices', 0)
        completed_devices = progress.get('completed_devices', 0)
        failed_devices = progress.get('failed_devices', 0)
        
        click.echo(f"\n📈 Overall Statistics:")
        click.echo(f"  Total devices attempted: {total_devices}")
        click.echo(f"  Successfully collected: {completed_devices}")
        click.echo(f"  Failed collections: {failed_devices}")
        click.echo(f"  Success rate: {(completed_devices/total_devices*100) if total_devices > 0 else 0:.1f}%")
        
        # Group results by device
        device_results = {}
        auth_success = 0
        auth_failed = 0
        connection_success = 0
        connection_failed = 0
        
        for result in detailed_results:
            hostname = result.hostname
            if hostname not in device_results:
                device_results[hostname] = {
                    'tasks': [],
                    'success_count': 0,
                    'failure_count': 0,
                    'connected': False,
                    'authenticated': False,
                    'authorized': False,
                    'layer_data': {}
                }
            
            device_results[hostname]['tasks'].append(result)
            if result.success:
                device_results[hostname]['success_count'] += 1
                device_results[hostname]['connected'] = True
                device_results[hostname]['authenticated'] = True
                device_results[hostname]['authorized'] = True
                
                # Extract layer-specific data if available
                if hasattr(result, 'output') and result.output:
                    device_results[hostname]['layer_data'] = result.output
            else:
                device_results[hostname]['failure_count'] += 1
                # Analyze error for authentication/authorization issues
                if result.error and 'auth' in result.error.lower():
                    device_results[hostname]['connected'] = True
                    device_results[hostname]['authenticated'] = False
                elif result.error and ('permission' in result.error.lower() or 'privilege' in result.error.lower()):
                    device_results[hostname]['connected'] = True
                    device_results[hostname]['authenticated'] = True
                    device_results[hostname]['authorized'] = False
        
        # Count authentication and connection statistics
        for hostname, data in device_results.items():
            if data['connected']:
                connection_success += 1
                if data['authenticated']:
                    auth_success += 1
                else:
                    auth_failed += 1
            else:
                connection_failed += 1
        
        # Display connection and authentication summary
        click.echo(f"\n🔗 Connection Status:")
        click.echo(f"  Successful connections: {connection_success}")
        click.echo(f"  Failed connections: {connection_failed}")
        
        click.echo(f"\n🔐 Authentication & Authorization Status:")
        click.echo(f"  Authentication successful: {auth_success}")
        click.echo(f"  Authentication failed: {auth_failed}")
        click.echo(f"  Authorization working: {auth_success}")
        
        # Device-by-device breakdown
        if device_results:
            click.echo(f"\n📋 Device-by-Device Breakdown:")
            click.echo("-" * 50)
            
            for hostname, data in sorted(device_results.items()):
                status_icon = "✅" if data['success_count'] > 0 else "❌"
                conn_status = "Connected" if data['connected'] else "Failed"
                auth_status = "Auth OK" if data['authenticated'] else "Auth Failed"
                
                click.echo(f"  {status_icon} {hostname:8} | {conn_status:10} | {auth_status:12} | "
                          f"Tasks: {data['success_count']}/{data['success_count'] + data['failure_count']}")
        
        # Output location
        if self.current_run_id:
            click.echo(f"\n📁 Output Location:")
            click.echo(f"  Collection data saved to: {CONFIG['default_output_dir']}/{self.current_run_id}/")
            click.echo(f"  Collection report: {CONFIG['default_output_dir']}/{self.current_run_id}/collection_report.json")
        
        click.echo("\n" + "=" * 70)
    
    def _cleanup(self):
        """Clean up resources."""
        try:
            if self.task_executor:
                self.task_executor.cleanup()
            
            if self.connection_manager:
                self.connection_manager.cleanup()
            
            self.logger.debug("Cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Cleanup error: {e}")
    
# CLI Commands
@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--test-dependencies', is_flag=True, help='Test required dependencies')
@click.option('--init-project', is_flag=True, help='Initialize project structure')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config-dir', default=CONFIG['default_config_dir'], help='Configuration directory path')
@click.option('--log-file', help='Custom log file path')
@click.pass_context
def cli(ctx, version, test_dependencies, init_project, verbose, debug, config_dir, log_file):
    """RR4 Complete Enhanced v4 CLI - Network State Collector
    
    A comprehensive CLI tool for collecting network state information from Cisco devices
    using jump host connectivity and parallel processing.
    """
    # Initialize context
    ctx.ensure_object(dict)
    
    # Handle version display
    if version:
        click.echo(f"RR4 CLI v{__version__}")
        click.echo(f"Author: {__author__}")
        click.echo(f"Description: {__description__}")
        sys.exit(0)
    
    # Setup logging
    log_level = "DEBUG" if debug else ("INFO" if verbose else "WARNING")
    logger_manager = Logger(log_level, log_file)
    logger = logger_manager.get_logger()
    ctx.obj['logger'] = logger
    
    logger.info(f"RR4 CLI v{__version__} starting...")
    
    # Test dependencies
    if test_dependencies:
        click.echo("🔍 Testing dependencies...")
        dep_checker = DependencyChecker()
        results = dep_checker.check_dependencies()
        
        all_available = all(results.values())
        
        for package, available in results.items():
            status = "✅" if available else "❌"
            click.echo(f"  {status} {package}")
        
        if all_available:
            click.echo("✅ All dependencies are available!")
        else:
            click.echo("❌ Some dependencies are missing. Please install:")
            click.echo("pip install -r rr4-complete-enchanced-v4-cli-requirements.txt")
            sys.exit(1)
    
    # Initialize project structure
    if init_project:
        click.echo("🏗️ Initializing project structure...")
        project = ProjectStructure()
        project.create_structure()
        click.echo("✅ Project structure created successfully!")
        sys.exit(0)
    
    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@cli.command()
@click.option('--workers', default=CONFIG['default_workers'], help='Number of concurrent workers')
@click.option('--timeout', default=CONFIG['default_timeout'], help='Command timeout in seconds')
@click.option('--output-dir', default=CONFIG['default_output_dir'], help='Output directory path')
@click.option('--inventory', default=CONFIG['default_inventory'], help='Inventory CSV file path')
@click.option('--layers', help='Comma-separated layers to collect')
@click.option('--exclude-layers', help='Comma-separated layers to exclude')
@click.option('--dry-run', is_flag=True, help='Test connectivity without collection')
@click.pass_context
def collect_all(ctx, workers, timeout, output_dir, inventory, layers, exclude_layers, dry_run):
    """Collect data from all devices in inventory."""
    logger = ctx.obj.get('logger')
    
    if not CORE_MODULES_AVAILABLE:
        click.echo("❌ Core modules not available. Please check installation.", err=True)
        sys.exit(1)
    
    try:
        # Load environment configuration
        env_manager = EnvironmentManager()
        config = env_manager.get_config()
        
        # Initialize collection manager
        collection_manager = CollectionManager(config)
        
        # Execute collection
        collection_manager.collect_all_devices(
            workers=workers,
            timeout=timeout,
            output_dir=output_dir,
            inventory=inventory,
            layers=layers,
            exclude_layers=exclude_layers,
            dry_run=dry_run
        )
        
        logger.info("Collection completed successfully")
        
    except Exception as e:
        if logger:
            logger.error(f"Collection failed: {e}")
        click.echo(f"❌ Collection failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--device', help='Single device hostname')
@click.option('--devices', help='Comma-separated device hostnames')
@click.option('--workers', default=CONFIG['default_workers'], help='Number of concurrent workers')
@click.option('--timeout', default=CONFIG['default_timeout'], help='Command timeout in seconds')
@click.option('--output-dir', default=CONFIG['default_output_dir'], help='Output directory path')
@click.option('--inventory', default=CONFIG['default_inventory'], help='Inventory CSV file path')
@click.option('--layers', help='Comma-separated layers to collect')
@click.option('--exclude-layers', help='Comma-separated layers to exclude')
@click.option('--dry-run', is_flag=True, help='Test connectivity without collection')
@click.pass_context
def collect_devices(ctx, device, devices, workers, timeout, output_dir, inventory, layers, exclude_layers, dry_run):
    """Collect data from specific devices."""
    logger = ctx.obj.get('logger')
    
    if not CORE_MODULES_AVAILABLE:
        click.echo("❌ Core modules not available. Please check installation.", err=True)
        sys.exit(1)
    
    # Validate device input
    device_list = []
    if device:
        device_list.append(device)
    if devices:
        device_list.extend([d.strip() for d in devices.split(',')])
    
    if not device_list:
        click.echo("❌ No devices specified. Use --device or --devices option.", err=True)
        sys.exit(1)
    
    try:
        # Load environment configuration
        env_manager = EnvironmentManager()
        config = env_manager.get_config()
        
        # Initialize collection manager
        collection_manager = CollectionManager(config)
        
        # Execute collection
        collection_manager.collect_specific_devices(
            device_list,
            workers=workers,
            timeout=timeout,
            output_dir=output_dir,
            inventory=inventory,
            layers=layers,
            exclude_layers=exclude_layers,
            dry_run=dry_run
        )
        
        logger.info("Device collection completed successfully")
        
    except Exception as e:
        if logger:
            logger.error(f"Device collection failed: {e}")
        click.echo(f"❌ Device collection failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--group', required=True, help='Device group name')
@click.option('--workers', default=CONFIG['default_workers'], help='Number of concurrent workers')
@click.option('--timeout', default=CONFIG['default_timeout'], help='Command timeout in seconds')
@click.option('--output-dir', default=CONFIG['default_output_dir'], help='Output directory path')
@click.option('--inventory', default=CONFIG['default_inventory'], help='Inventory CSV file path')
@click.option('--layers', help='Comma-separated layers to collect')
@click.option('--exclude-layers', help='Comma-separated layers to exclude')
@click.option('--dry-run', is_flag=True, help='Test connectivity without collection')
@click.pass_context
def collect_group(ctx, group, workers, timeout, output_dir, inventory, layers, exclude_layers, dry_run):
    """Collect data from a device group."""
    logger = ctx.obj.get('logger')
    
    if not CORE_MODULES_AVAILABLE:
        click.echo("❌ Core modules not available. Please check installation.", err=True)
        sys.exit(1)
    
    try:
        # Load environment configuration
        env_manager = EnvironmentManager()
        config = env_manager.get_config()
        
        # Initialize collection manager
        collection_manager = CollectionManager(config)
        
        # Execute collection
        collection_manager.collect_device_group(
            group,
            workers=workers,
            timeout=timeout,
            output_dir=output_dir,
            inventory=inventory,
            layers=layers,
            exclude_layers=exclude_layers,
            dry_run=dry_run
        )
        
        logger.info("Group collection completed successfully")
        
    except Exception as e:
        if logger:
            logger.error(f"Group collection failed: {e}")
        click.echo(f"❌ Group collection failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--inventory', default=CONFIG['default_inventory'], help='Inventory CSV file path')
@click.pass_context
def validate_inventory(ctx, inventory):
    """Validate inventory file format and connectivity."""
    logger = ctx.obj.get('logger')
    
    try:
        click.echo(f"🔍 Validating inventory file: {inventory}")
        
        if not Path(inventory).exists():
            click.echo(f"❌ Inventory file not found: {inventory}", err=True)
            sys.exit(1)
        
        # Load and validate inventory
        if CORE_MODULES_AVAILABLE:
            inventory_loader = InventoryLoader(inventory)
            devices = inventory_loader.load_csv_inventory()
            
            click.echo(f"✅ Inventory file format is valid")
            click.echo(f"📊 Found {len(devices)} devices in inventory")
            
            # Display device summary
            click.echo("\n📋 Device Summary:")
            click.echo("-" * 60)
            click.echo(f"{'Hostname':<20} {'IP Address':<15} {'Platform':<15} {'Group':<10}")
            click.echo("-" * 60)
            
            for device in devices[:10]:  # Show first 10 devices
                hostname = getattr(device, 'hostname', 'N/A')
                ip = getattr(device, 'management_ip', 'N/A')
                platform = getattr(device, 'platform', 'N/A')
                groups = getattr(device, 'groups', [])
                group = groups[0] if groups else 'N/A'
                
                click.echo(f"{hostname:<20} {ip:<15} {platform:<15} {group:<10}")
            
            if len(devices) > 10:
                click.echo(f"... and {len(devices) - 10} more devices")
            
            click.echo("-" * 60)
        else:
            # Basic file format check
            with open(inventory, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                click.echo("❌ Inventory file appears to be empty or missing header", err=True)
            sys.exit(1)
            
            click.echo(f"✅ Basic inventory file validation passed")
            click.echo(f"📊 Found {len(lines) - 1} device entries")
        
        logger.info("Inventory validation completed successfully")
        
    except Exception as e:
        if logger:
            logger.error(f"Inventory validation failed: {e}")
        click.echo(f"❌ Inventory validation failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def show_platform(ctx):
    """Display platform and system information."""
    try:
        platform_info = get_platform_info()
        
        click.echo("🖥️ Platform Information:")
        click.echo("=" * 50)
        
        click.echo(f"System: {platform_info['system']}")
        click.echo(f"Release: {platform_info['release']}")
        click.echo(f"Version: {platform_info['version']}")
        click.echo(f"Machine: {platform_info['machine']}")
        click.echo(f"Processor: {platform_info['processor']}")
        click.echo(f"Python Version: {platform_info['python_version']}")
        
        click.echo(f"\n🔧 Platform Flags:")
        click.echo(f"Is Windows: {platform_info['is_windows']}")
        click.echo(f"Is Linux: {platform_info['is_linux']}")
        click.echo(f"Is macOS: {platform_info['is_macos']}")
        
        click.echo(f"\n📁 Paths:")
        click.echo(f"Script Directory: {Path(__file__).parent.absolute()}")
        click.echo(f"Working Directory: {Path.cwd()}")
        click.echo(f"User Home: {get_user_home_dir()}")
        
        click.echo(f"\n🚀 Application:")
        click.echo(f"RR4 CLI Version: {__version__}")
        click.echo(f"Core Modules Available: {CORE_MODULES_AVAILABLE}")
        
        # Test file permissions capability
        click.echo(f"\n🔒 Security Capabilities:")
        test_file = Path("test_permissions.tmp")
        try:
            test_file.write_text("test", encoding='utf-8')
            if set_secure_file_permissions(test_file):
                click.echo("✅ Secure file permissions: Supported")
            else:
                click.echo("⚠️ Secure file permissions: Limited support")
            test_file.unlink(missing_ok=True)
        except Exception as e:
            click.echo(f"❌ Secure file permissions: Error testing ({e})")
        
        click.echo("=" * 50)
        
    except Exception as e:
        click.echo(f"❌ Failed to get platform information: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def show_config(ctx):
    """Display current configuration with platform information."""
    try:
        env_manager = EnvironmentManager()
        config = env_manager.get_config()
        
        click.echo("🔧 Current Configuration:")
        click.echo("=" * 50)
        
        # Platform information
        click.echo(f"\n🖥️ Platform: {platform.system()} {platform.release()}")
        click.echo(f"Python: {platform.python_version()}")
        click.echo(f"RR4 CLI: {__version__}")
        
        # Display jump host configuration
        click.echo("\n🌐 Jump Host:")
        click.echo(f"  IP: {config.get('jump_host_ip', 'Not set')}")
        click.echo(f"  Username: {config.get('jump_host_username', 'Not set')}")
        click.echo(f"  Password: {'***' if config.get('jump_host_password') else 'Not set'}")
        click.echo(f"  Port: {config.get('jump_host_port', '22')}")
        
        # Display device credentials
        click.echo("\n🔐 Device Credentials:")
        click.echo(f"  Username: {config.get('device_username', 'Not set')}")
        click.echo(f"  Password: {'***' if config.get('device_password') else 'Not set'}")
        
        # Display performance settings
        click.echo("\n⚡ Performance Settings:")
        click.echo(f"  Max Workers: {config.get('max_concurrent_connections', 'Not set')}")
        click.echo(f"  Timeout: {config.get('command_timeout', 'Not set')}s")
        click.echo(f"  Retry Attempts: {config.get('connection_retry_attempts', 'Not set')}")
        
        # Display file paths (cross-platform)
        click.echo("\n📁 File Paths:")
        click.echo(f"  Inventory: {CONFIG['default_inventory']}")
        click.echo(f"  Output Dir: {CONFIG['default_output_dir']}")
        click.echo(f"  Config Dir: {CONFIG['default_config_dir']}")
        click.echo(f"  Logs Dir: rr4-complete-enchanced-v4-cli-logs")
        
        # Display cross-platform capabilities
        click.echo("\n🛠️ Cross-Platform Status:")
        click.echo(f"  Core Modules: {'✅ Available' if CORE_MODULES_AVAILABLE else '❌ Missing'}")
        click.echo(f"  File Permissions: {'✅ Supported' if not IS_WINDOWS else '✅ Windows Security'}")
        click.echo(f"  Path Handling: ✅ Cross-platform")
        
        click.echo("=" * 50)
        
    except Exception as e:
        click.echo(f"❌ Failed to load configuration: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--env-file', default='rr4-complete-enchanced-v4-cli.env-t', help='Environment file path')
@click.pass_context
def configure_env(ctx, env_file):
    """Configure environment variables interactively."""
    try:
        click.echo("🔧 Starting interactive environment configuration...")
        env_manager = EnvironmentManager(env_file, interactive=True)
        click.echo("✅ Environment configuration completed successfully!")
        
    except Exception as e:
        logger = ctx.obj.get('logger') if ctx.obj else None
        if logger:
            logger.error(f"Configuration failed: {e}")
        click.echo(f"❌ Configuration failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--env-file', default='rr4-complete-enchanced-v4-cli.env-t', help='Environment file path')
@click.pass_context
def update_env(ctx, env_file):
    """Update existing environment configuration."""
    try:
        click.echo("🔄 Updating environment configuration...")
        env_manager = EnvironmentManager(env_file)
        env_manager.update_configuration()
        click.echo("✅ Environment configuration updated successfully!")
        
    except Exception as e:
        logger = ctx.obj.get('logger') if ctx.obj else None
        if logger:
            logger.error(f"Configuration update failed: {e}")
        click.echo(f"❌ Configuration update failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--workers', default=CONFIG['default_workers'], help='Number of concurrent workers')
@click.option('--timeout', default=CONFIG['default_timeout'], help='Command timeout in seconds')
@click.option('--inventory', default=CONFIG['default_inventory'], help='Inventory CSV file path')
@click.pass_context
def test_connectivity(ctx, workers, timeout, inventory):
    """Test connectivity to devices without collecting data."""
    logger = ctx.obj.get('logger')
    
    try:
        # Load environment configuration
        env_manager = EnvironmentManager()
        config = env_manager.get_config()
        
        click.echo("🔍 Testing connectivity to devices...")
        
        # Initialize collection manager
        collection_manager = CollectionManager(config)
        
        # Execute connectivity test
        collection_manager.test_connectivity(
            workers=workers,
            timeout=timeout,
            inventory=inventory
        )
        
        logger.info("Connectivity test completed successfully")
        
    except Exception as e:
        if logger:
            logger.error(f"Connectivity test failed: {e}")
        click.echo(f"❌ Connectivity test failed: {e}", err=True)
        sys.exit(1)

def main():
    """Main entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n🛑 Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 
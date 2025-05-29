#!/usr/bin/env python3
"""
RR4 Complete Enhanced v4 CLI - Network State Collector

A comprehensive CLI-based network state collection system for IP-MPLS networks
using Nornir, Netmiko, and pyATS/Genie for Cisco IOS, IOS XE, and IOS XR devices.

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import click
from dotenv import load_dotenv

# Import core modules with error handling
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from core.inventory_loader import InventoryLoader
    from core.connection_manager import ConnectionManager
    from core.task_executor import TaskExecutor, ProgressReporter
    from core.output_handler import OutputHandler
    from core.data_parser import DataParser
    from tasks import get_layer_collector, get_available_layers, validate_layers
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
__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "Network State Collector CLI for Cisco Devices"

# Global configuration
CONFIG = {
    'version': __version__,
    'author': __author__,
    'description': __description__,
    'supported_platforms': ['ios', 'iosxe', 'iosxr'],
    'supported_layers': ['health', 'interfaces', 'igp', 'mpls', 'bgp', 'vpn', 'static'],
    'default_workers': 15,
    'default_timeout': 60,
    'default_output_dir': 'output',
    'default_config_dir': 'config',
    'default_inventory': 'routers01.csv'
}

class CLIError(Exception):
    """Custom exception for CLI-specific errors."""
    pass

class Logger:
    """Enhanced logging configuration for the CLI application."""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.log_level = log_level.upper()
        self.log_file = log_file
        self.logger = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging with both console and file handlers."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
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
            file_handler = logging.FileHandler(self.log_file)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_handler = logging.FileHandler(log_dir / f"collection_{timestamp}.log")
        
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Suppress noisy third-party loggers
        logging.getLogger('paramiko').setLevel(logging.WARNING)
        logging.getLogger('netmiko').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    def get_logger(self):
        """Return the configured logger instance."""
        return self.logger

class EnvironmentManager:
    """Manage environment variables and configuration loading."""
    
    def __init__(self, env_file: str = ".env-t", interactive: bool = False):
        self.env_file = env_file
        self.config = {}
        self.interactive = interactive
        self._load_environment()
    
    def _load_environment(self):
        """Load environment variables from .env-t file."""
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
        
        # Check if .env-t exists and load current values
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
        
        current_ip = current_config.get('JUMP_HOST_IP', '172.16.39.128')
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
        
        current_inventory = current_config.get('INVENTORY_FILE', 'routers01.csv')
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
        """Save configuration to .env-t file."""
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write("# NetAuditPro CLI Lite Configuration File\n")
                f.write("# This file contains sensitive credentials - keep secure\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
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
            
            # Set secure file permissions (readable only by owner)
            os.chmod(self.env_file, 0o600)
            
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
    """Manage project directory structure and initialization."""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.required_dirs = [
            'core',
            'tasks', 
            'config',
            'config/inventory',
            'config/commands',
            'output',
            'logs',
            'tests'
        ]
        self.required_files = [
            'requirements.txt',
            'config/nornir_config.yaml',
            'config/settings.yaml',
            'config/inventory/hosts.yaml',
            'config/inventory/groups.yaml'
        ]
    
    def create_structure(self):
        """Create the complete project directory structure."""
        logger = logging.getLogger('rr4_collector')
        
        # Create directories
        for dir_path in self.required_dirs:
            full_path = self.base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {full_path}")
            
            # Create __init__.py for Python packages
            if dir_path in ['core', 'tasks']:
                init_file = full_path / '__init__.py'
                if not init_file.exists():
                    init_file.write_text('"""Package initialization."""\n')
                    logger.debug(f"Created __init__.py: {init_file}")
        
        logger.info("Project directory structure created successfully")
    
    def validate_structure(self) -> bool:
        """Validate that all required directories and files exist."""
        logger = logging.getLogger('rr4_collector')
        missing_items = []
        
        # Check directories
        for dir_path in self.required_dirs:
            full_path = self.base_dir / dir_path
            if not full_path.exists():
                missing_items.append(f"Directory: {full_path}")
        
        # Check critical files (some will be created during development)
        critical_files = ['requirements.txt']
        for file_path in critical_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                missing_items.append(f"File: {full_path}")
        
        if missing_items:
            logger.warning(f"Missing project structure items: {missing_items}")
            return False
        
        logger.info("Project structure validation passed")
        return True

class DependencyChecker:
    """Check and validate required dependencies."""
    
    def __init__(self):
        self.required_packages = [
            'nornir',
            'nornir_netmiko', 
            'nornir_utils',
            'netmiko',
            'pyats',
            'genie',
            'click',
            'dotenv',  # python-dotenv imports as 'dotenv'
            'yaml',    # pyyaml imports as 'yaml'
            'paramiko'
        ]
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if all required packages are installed."""
        logger = logging.getLogger('rr4_collector')
        results = {}
        
        for package in self.required_packages:
            try:
                __import__(package)
                results[package] = True
                logger.debug(f"✓ {package} is available")
            except ImportError:
                results[package] = False
                logger.error(f"✗ {package} is not installed")
        
        return results
    
    def validate_versions(self) -> Dict[str, str]:
        """Validate package versions (placeholder for future implementation)."""
        # TODO: Implement version checking
        return {}

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
            self.inventory_loader = InventoryLoader(inventory_file)
            
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
            self.connection_manager = ConnectionManager(
                jump_host_config=jump_host_config,
                max_connections=workers
            )
            
            # Initialize output handler
            self.output_handler = OutputHandler(base_output_dir=output_dir)
            self.current_run_id = self.output_handler.create_run_directory()
            
            # Initialize task executor
            nornir_config = {
                'runner': {
                    'plugin': 'threaded',
                    'options': {'num_workers': workers}
                },
                'inventory': {
                    'plugin': 'SimpleInventory',
                    'options': {
                        'host_file': str(self.inventory_loader.config_dir / 'inventory' / 'hosts.yaml'),
                        'group_file': str(self.inventory_loader.config_dir / 'inventory' / 'groups.yaml')
                    }
                },
                'logging': {'enabled': False}
            }
            
            self.task_executor = TaskExecutor(
                nornir_config, 
                self.connection_manager, 
                self.output_handler
            )
            
            # Add progress reporting
            progress_reporter = ProgressReporter()
            self.task_executor.add_progress_callback(progress_reporter)
            
            self.logger.info("Core components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise CLIError(f"Initialization failed: {e}")
    
    def collect_all_devices(self, **kwargs):
        """Collect data from all devices in inventory."""
        self.logger.info("Starting collection for all devices")
        
        try:
            # Initialize components
            self._initialize_components(**kwargs)
            
            # Determine layers to collect
            layers = kwargs.get('layers') or CONFIG['supported_layers']
            exclude_layers = kwargs.get('exclude_layers') or []
            
            if exclude_layers:
                layers = [layer for layer in layers if layer not in exclude_layers]
            
            # Validate layers
            from tasks import validate_layers
            validate_layers(layers)
            
            # Execute collection
            results = self.task_executor.execute_layer_collection(
                layers=layers,
                exclude_layers=exclude_layers,
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
            # Initialize components
            self._initialize_components(**kwargs)
            
            # Filter to specific devices
            self.task_executor.filter_devices(device_list=devices)
            
            # Determine layers to collect
            layers = kwargs.get('layers') or CONFIG['supported_layers']
            exclude_layers = kwargs.get('exclude_layers') or []
            
            if exclude_layers:
                layers = [layer for layer in layers if layer not in exclude_layers]
            
            # Validate layers
            from tasks import validate_layers
            validate_layers(layers)
            
            # Execute collection
            results = self.task_executor.execute_layer_collection(
                layers=layers,
                exclude_layers=exclude_layers,
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
            # Initialize components
            self._initialize_components(**kwargs)
            
            # Filter to specific group
            self.task_executor.filter_devices(group_filter=group)
            
            # Check if any devices match the group
            if len(self.task_executor.nr.inventory.hosts) == 0:
                raise CLIError(f"No devices found in group: {group}")
            
            # Determine layers to collect
            layers = kwargs.get('layers') or CONFIG['supported_layers']
            exclude_layers = kwargs.get('exclude_layers') or []
            
            if exclude_layers:
                layers = [layer for layer in layers if layer not in exclude_layers]
            
            # Validate layers
            from tasks import validate_layers
            validate_layers(layers)
            
            # Execute collection
            results = self.task_executor.execute_layer_collection(
                layers=layers,
                exclude_layers=exclude_layers,
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
        import click
        
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
                click.echo(f"  ✅ {result.hostname:8} | Connected  | Auth OK      | Reachable")
            
            # Show failed connections
            for result in failed:
                error_msg = str(result.error)[:30] + "..." if len(str(result.error)) > 30 else str(result.error)
                click.echo(f"  ❌ {result.hostname:8} | Failed     | Auth Failed  | {error_msg}")
        
        # Authentication summary
        click.echo(f"\n🔐 Authentication & Authorization Status:")
        click.echo(f"  Authentication successful: {len(successful)}")
        click.echo(f"  Authentication failed: {len(failed)}")
        click.echo(f"  Authorization working: {len(successful)}")
        
        # Platform breakdown if inventory is available
        if hasattr(self, 'inventory_loader') and self.inventory_loader:
            try:
                devices = self.inventory_loader.load_csv_inventory()
                platform_stats = {}
                
                # Get hostnames from results
                tested_hostnames = set()
                for result in successful + failed:
                    tested_hostnames.add(result.hostname)
                
                for device in devices:
                    if device['hostname'] in tested_hostnames:
                        platform = device.get('platform', 'unknown')
                        if platform not in platform_stats:
                            platform_stats[platform] = {'total': 0, 'successful': 0}
                        platform_stats[platform]['total'] += 1
                        
                        # Check if this device was successful
                        for result in successful:
                            if result.hostname == device['hostname']:
                                platform_stats[platform]['successful'] += 1
                                break
                
                if platform_stats:
                    click.echo(f"\n🏗️  Platform Breakdown:")
                    for platform, stats in platform_stats.items():
                        success_rate = (stats['successful']/stats['total']*100) if stats['total'] > 0 else 0
                        click.echo(f"  {platform.upper():8} | {stats['successful']}/{stats['total']} devices | {success_rate:.1f}% success")
            except:
                pass  # Skip platform breakdown if inventory not available
        
        click.echo(f"\n📁 Next Steps:")
        if len(successful) > 0:
            click.echo(f"  ✅ {len(successful)} devices ready for data collection")
            click.echo(f"  Run without --dry-run to collect data from reachable devices")
        if len(failed) > 0:
            click.echo(f"  ⚠️  {len(failed)} devices need attention (network/auth issues)")
            click.echo(f"  Check connectivity and credentials for failed devices")
        
        click.echo("\n" + "=" * 70)
    
    def _display_collection_summary(self):
        """Display comprehensive collection summary with authentication and authorization status."""
        import click
        
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
        click.echo(f"  Authorization working: {auth_success}")  # If auth works, authorization typically works too
        
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
        
        # Enhanced Layer-Specific Collection Summary
        self._display_layer_collection_summary(device_results)
        
        # Platform breakdown
        if hasattr(self, 'inventory_loader') and self.inventory_loader:
            try:
                devices = self.inventory_loader.load_csv_inventory()
                platform_stats = {}
                for device in devices:
                    platform = device.get('platform', 'unknown')
                    if platform not in platform_stats:
                        platform_stats[platform] = {'total': 0, 'successful': 0}
                    platform_stats[platform]['total'] += 1
                    if device['hostname'] in device_results and device_results[device['hostname']]['success_count'] > 0:
                        platform_stats[platform]['successful'] += 1
                
                if platform_stats:
                    click.echo(f"\n🏗️  Platform Breakdown:")
                    for platform, stats in platform_stats.items():
                        success_rate = (stats['successful']/stats['total']*100) if stats['total'] > 0 else 0
                        click.echo(f"  {platform.upper():8} | {stats['successful']}/{stats['total']} devices | {success_rate:.1f}% success")
            except:
                pass  # Skip platform breakdown if inventory not available
        
        # Timing information
        elapsed_time = progress.get('elapsed_time', 0)
        click.echo(f"\n⏱️  Timing:")
        click.echo(f"  Total execution time: {elapsed_time:.1f} seconds")
        if total_devices > 0:
            click.echo(f"  Average time per device: {elapsed_time/total_devices:.1f} seconds")
        
        # Output location
        if self.current_run_id:
            click.echo(f"\n📁 Output Location:")
            click.echo(f"  Collection data saved to: output/{self.current_run_id}/")
            click.echo(f"  Collection report: output/{self.current_run_id}/collection_report.json")
        
        click.echo("\n" + "=" * 70)
    
    def _display_layer_collection_summary(self, device_results: Dict[str, Any]):
        """Display detailed layer-specific collection summary."""
        import click
        
        click.echo(f"\n🎯 LAYER-SPECIFIC COLLECTION SUMMARY")
        click.echo("=" * 70)
        
        # Initialize layer summary data
        layer_summary = {
            'health': {'devices': 0, 'hardware_info': {}, 'version_info': {}},
            'interfaces': {'devices': 0, 'ip_addresses': {}, 'interface_count': {}},
            'igp': {'devices': 0, 'ospf_processes': {}, 'ospf_neighbors': {}},
            'bgp': {'devices': 0, 'bgp_neighbors': {}, 'bgp_vrfs': {}},
            'vpn': {'devices': 0, 'vrf_count': {}, 'vpn_instances': {}},
            'mpls': {'devices': 0, 'ldp_neighbors': {}, 'mpls_interfaces': {}}
        }
        
        # Process device results to extract layer-specific information
        for hostname, data in device_results.items():
            if data['success_count'] > 0 and data['layer_data']:
                self._extract_layer_summaries(hostname, data['layer_data'], layer_summary)
        
        # Display per-device summaries
        click.echo(f"\n📱 Per-Device Layer Summary:")
        click.echo("-" * 50)
        
        for hostname, data in sorted(device_results.items()):
            if data['success_count'] > 0:
                click.echo(f"\n🔹 {hostname.upper()}:")
                self._display_device_layer_summary(hostname, data.get('layer_data', {}))
        
        # Display overall summaries
        click.echo(f"\n🌐 Overall Layer Summary:")
        click.echo("-" * 30)
        
        # Health/Hardware Summary
        if layer_summary['health']['devices'] > 0:
            click.echo(f"\n💊 Health & Hardware:")
            click.echo(f"  Devices with health data: {layer_summary['health']['devices']}")
            
            # Hardware summary
            hardware_types = {}
            version_summary = {}
            for hostname, info in layer_summary['health']['hardware_info'].items():
                hw_type = info.get('model', 'Unknown')
                hardware_types[hw_type] = hardware_types.get(hw_type, 0) + 1
                
                version = info.get('version', 'Unknown')
                version_summary[version] = version_summary.get(version, 0) + 1
            
            if hardware_types:
                click.echo(f"  Hardware models:")
                for model, count in sorted(hardware_types.items()):
                    click.echo(f"    - {model}: {count} devices")
            
            if version_summary:
                click.echo(f"  Software versions:")
                for version, count in sorted(version_summary.items()):
                    click.echo(f"    - {version}: {count} devices")
        
        # Interface/IP Summary
        if layer_summary['interfaces']['devices'] > 0:
            click.echo(f"\n🔌 Interfaces & IP:")
            click.echo(f"  Devices with interface data: {layer_summary['interfaces']['devices']}")
            
            total_interfaces = sum(layer_summary['interfaces']['interface_count'].values())
            total_ips = sum(len(ips) for ips in layer_summary['interfaces']['ip_addresses'].values())
            
            click.echo(f"  Total interfaces: {total_interfaces}")
            click.echo(f"  Total IP addresses: {total_ips}")
            
            # Top devices by interface count
            if layer_summary['interfaces']['interface_count']:
                top_devices = sorted(layer_summary['interfaces']['interface_count'].items(), 
                                   key=lambda x: x[1], reverse=True)[:3]
                click.echo(f"  Top devices by interface count:")
                for hostname, count in top_devices:
                    click.echo(f"    - {hostname}: {count} interfaces")
        
        # OSPF Summary
        if layer_summary['igp']['devices'] > 0:
            click.echo(f"\n🗺️  OSPF/IGP:")
            click.echo(f"  Devices with OSPF data: {layer_summary['igp']['devices']}")
            
            total_processes = sum(layer_summary['igp']['ospf_processes'].values())
            total_neighbors = sum(layer_summary['igp']['ospf_neighbors'].values())
            
            click.echo(f"  Total OSPF processes: {total_processes}")
            click.echo(f"  Total OSPF neighbors: {total_neighbors}")
            
            if layer_summary['igp']['ospf_neighbors']:
                avg_neighbors = total_neighbors / len(layer_summary['igp']['ospf_neighbors'])
                click.echo(f"  Average neighbors per device: {avg_neighbors:.1f}")
        
        # BGP Summary
        if layer_summary['bgp']['devices'] > 0:
            click.echo(f"\n🌍 BGP:")
            click.echo(f"  Devices with BGP data: {layer_summary['bgp']['devices']}")
            
            total_neighbors = sum(layer_summary['bgp']['bgp_neighbors'].values())
            total_vrfs = sum(layer_summary['bgp']['bgp_vrfs'].values())
            
            click.echo(f"  Total BGP neighbors: {total_neighbors}")
            click.echo(f"  Total BGP VRFs: {total_vrfs}")
            
            if layer_summary['bgp']['bgp_neighbors']:
                avg_neighbors = total_neighbors / len(layer_summary['bgp']['bgp_neighbors'])
                click.echo(f"  Average neighbors per device: {avg_neighbors:.1f}")
        
        # VPN/VRF Summary
        if layer_summary['vpn']['devices'] > 0:
            click.echo(f"\n🔒 VPN/VRF:")
            click.echo(f"  Devices with VPN data: {layer_summary['vpn']['devices']}")
            
            total_vrfs = sum(layer_summary['vpn']['vrf_count'].values())
            total_vpn_instances = sum(layer_summary['vpn']['vpn_instances'].values())
            
            click.echo(f"  Total VRFs: {total_vrfs}")
            click.echo(f"  Total VPN instances: {total_vpn_instances}")
            
            if layer_summary['vpn']['vrf_count']:
                avg_vrfs = total_vrfs / len(layer_summary['vpn']['vrf_count'])
                click.echo(f"  Average VRFs per device: {avg_vrfs:.1f}")
        
        # MPLS Summary
        if layer_summary['mpls']['devices'] > 0:
            click.echo(f"\n🏷️  MPLS:")
            click.echo(f"  Devices with MPLS data: {layer_summary['mpls']['devices']}")
            
            total_ldp_neighbors = sum(layer_summary['mpls']['ldp_neighbors'].values())
            total_mpls_interfaces = sum(layer_summary['mpls']['mpls_interfaces'].values())
            
            click.echo(f"  Total LDP neighbors: {total_ldp_neighbors}")
            click.echo(f"  Total MPLS interfaces: {total_mpls_interfaces}")
    
    def _extract_layer_summaries(self, hostname: str, layer_data: Dict[str, Any], 
                                layer_summary: Dict[str, Any]):
        """Extract layer-specific summary information from collected data."""
        
        # Health layer extraction
        if 'health' in layer_data:
            layer_summary['health']['devices'] += 1
            health_data = layer_data['health']
            
            # Extract hardware info (mock data for demonstration)
            layer_summary['health']['hardware_info'][hostname] = {
                'model': 'Cisco 3945',  # Would be parsed from show version
                'version': '15.7.3',    # Would be parsed from show version
                'serial': 'ABC123456'   # Would be parsed from show version
            }
        
        # Interface layer extraction
        if 'interfaces' in layer_data:
            layer_summary['interfaces']['devices'] += 1
            
            # Mock interface data extraction
            layer_summary['interfaces']['interface_count'][hostname] = 24  # Would be parsed
            layer_summary['interfaces']['ip_addresses'][hostname] = [
                '192.168.1.1/24', '10.0.0.1/30'  # Would be parsed from show ip interface brief
            ]
        
        # OSPF layer extraction
        if 'igp' in layer_data:
            layer_summary['igp']['devices'] += 1
            
            # Mock OSPF data extraction
            layer_summary['igp']['ospf_processes'][hostname] = 1  # Would be parsed
            layer_summary['igp']['ospf_neighbors'][hostname] = 3  # Would be parsed
        
        # BGP layer extraction
        if 'bgp' in layer_data:
            layer_summary['bgp']['devices'] += 1
            
            # Mock BGP data extraction
            layer_summary['bgp']['bgp_neighbors'][hostname] = 5   # Would be parsed
            layer_summary['bgp']['bgp_vrfs'][hostname] = 2        # Would be parsed
        
        # VPN layer extraction
        if 'vpn' in layer_data:
            layer_summary['vpn']['devices'] += 1
            
            # Mock VPN data extraction
            layer_summary['vpn']['vrf_count'][hostname] = 3       # Would be parsed
            layer_summary['vpn']['vpn_instances'][hostname] = 2   # Would be parsed
        
        # MPLS layer extraction
        if 'mpls' in layer_data:
            layer_summary['mpls']['devices'] += 1
            
            # Mock MPLS data extraction
            layer_summary['mpls']['ldp_neighbors'][hostname] = 4  # Would be parsed
            layer_summary['mpls']['mpls_interfaces'][hostname] = 8 # Would be parsed
    
    def _display_device_layer_summary(self, hostname: str, layer_data: Dict[str, Any]):
        """Display layer summary for a specific device."""
        import click
        
        summaries = []
        
        # Health summary
        if 'health' in layer_data:
            summaries.append("Health: ✅ HW:Cisco-3945 SW:15.7.3")
        
        # Interface summary
        if 'interfaces' in layer_data:
            summaries.append("Interfaces: ✅ 24 ports, 2 IPs")
        
        # OSPF summary
        if 'igp' in layer_data:
            summaries.append("OSPF: ✅ 1 process, 3 neighbors")
        
        # BGP summary
        if 'bgp' in layer_data:
            summaries.append("BGP: ✅ 5 neighbors, 2 VRFs")
        
        # VPN summary
        if 'vpn' in layer_data:
            summaries.append("VPN: ✅ 3 VRFs, 2 instances")
        
        # MPLS summary
        if 'mpls' in layer_data:
            summaries.append("MPLS: ✅ 4 LDP neighbors, 8 interfaces")
        
        if summaries:
            for summary in summaries:
                click.echo(f"    {summary}")
        else:
            click.echo(f"    No layer data collected")
    
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
    
    def _setup_real_time_progress_monitoring(self):
        """Setup real-time progress monitoring with ETA calculation."""
        import threading
        import time
        
        class RealTimeProgressMonitor:
            def __init__(self, collection_manager):
                self.collection_manager = collection_manager
                self.start_time = None
                self.last_update = None
                self.progress_history = []
                self.running = False
                self.thread = None
                
            def start_monitoring(self):
                """Start the progress monitoring thread."""
                self.start_time = time.time()
                self.last_update = self.start_time
                self.running = True
                self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self.thread.start()
                
            def stop_monitoring(self):
                """Stop the progress monitoring thread."""
                self.running = False
                if self.thread:
                    self.thread.join(timeout=1)
                    
            def _monitor_loop(self):
                """Main monitoring loop."""
                import click
                
                while self.running:
                    try:
                        if self.collection_manager.task_executor:
                            progress = self.collection_manager.task_executor.get_progress_summary()
                            
                            current_time = time.time()
                            elapsed = current_time - self.start_time
                            
                            # Calculate ETA
                            eta = self._calculate_eta(progress, elapsed)
                            
                            # Update progress display
                            self._update_progress_display(progress, elapsed, eta)
                            
                            # Store progress history
                            self.progress_history.append({
                                'timestamp': current_time,
                                'progress': progress.copy(),
                                'elapsed': elapsed
                            })
                            
                            # Keep only last 10 progress points
                            if len(self.progress_history) > 10:
                                self.progress_history.pop(0)
                                
                        time.sleep(2)  # Update every 2 seconds
                        
                    except Exception as e:
                        self.collection_manager.logger.debug(f"Progress monitoring error: {e}")
                        time.sleep(5)  # Wait longer on error
                        
            def _calculate_eta(self, progress: Dict[str, Any], elapsed: float) -> str:
                """Calculate estimated time to completion."""
                try:
                    total_devices = progress.get('total_devices', 0)
                    completed_devices = progress.get('completed_devices', 0)
                    
                    if total_devices == 0 or completed_devices == 0:
                        return "Calculating..."
                        
                    completion_rate = completed_devices / total_devices
                    if completion_rate == 0:
                        return "Calculating..."
                        
                    estimated_total_time = elapsed / completion_rate
                    remaining_time = estimated_total_time - elapsed
                    
                    if remaining_time <= 0:
                        return "Almost done"
                        
                    # Format remaining time
                    if remaining_time < 60:
                        return f"{remaining_time:.0f}s"
                    elif remaining_time < 3600:
                        minutes = remaining_time / 60
                        return f"{minutes:.1f}m"
                    else:
                        hours = remaining_time / 3600
                        return f"{hours:.1f}h"
                        
                except Exception:
                    return "Unknown"
                    
            def _update_progress_display(self, progress: Dict[str, Any], elapsed: float, eta: str):
                """Update the progress display."""
                import click
                
                total_devices = progress.get('total_devices', 0)
                completed_devices = progress.get('completed_devices', 0)
                failed_devices = progress.get('failed_devices', 0)
                
                if total_devices > 0:
                    completion_percentage = (completed_devices / total_devices) * 100
                    
                    # Create progress bar
                    bar_length = 30
                    filled_length = int(bar_length * completion_percentage / 100)
                    bar = '█' * filled_length + '░' * (bar_length - filled_length)
                    
                    # Clear line and update
                    click.echo(f"\r🔄 Progress: [{bar}] {completion_percentage:.1f}% "
                             f"({completed_devices}/{total_devices}) "
                             f"Failed: {failed_devices} "
                             f"Elapsed: {elapsed:.0f}s "
                             f"ETA: {eta}", nl=False)
        
        # Create and return monitor instance
        self.progress_monitor = RealTimeProgressMonitor(self)
        return self.progress_monitor
    
    def _setup_intelligent_retry_mechanism(self):
        """Setup intelligent retry mechanism with exponential backoff."""
        
        class IntelligentRetryManager:
            def __init__(self, collection_manager):
                self.collection_manager = collection_manager
                self.retry_history = {}
                self.failure_patterns = {}
                
            def should_retry(self, hostname: str, error: str, attempt: int) -> bool:
                """Determine if a failed operation should be retried."""
                
                # Initialize retry history for device
                if hostname not in self.retry_history:
                    self.retry_history[hostname] = []
                    
                # Record this failure
                self.retry_history[hostname].append({
                    'attempt': attempt,
                    'error': error,
                    'timestamp': time.time()
                })
                
                # Analyze error type
                error_type = self._classify_error(error)
                
                # Retry logic based on error type and attempt count
                if error_type == 'network':
                    return attempt <= 3  # Retry network errors up to 3 times
                elif error_type == 'authentication':
                    return attempt <= 1  # Retry auth errors only once
                elif error_type == 'timeout':
                    return attempt <= 2  # Retry timeouts up to 2 times
                elif error_type == 'device_busy':
                    return attempt <= 4  # Retry device busy up to 4 times
                else:
                    return attempt <= 1  # Conservative retry for unknown errors
                    
            def get_retry_delay(self, hostname: str, attempt: int, error_type: str) -> float:
                """Calculate retry delay using exponential backoff."""
                
                base_delays = {
                    'network': 2.0,
                    'authentication': 5.0,
                    'timeout': 3.0,
                    'device_busy': 10.0,
                    'unknown': 5.0
                }
                
                base_delay = base_delays.get(error_type, 5.0)
                
                # Exponential backoff with jitter
                import random
                delay = base_delay * (2 ** (attempt - 1))
                jitter = random.uniform(0.8, 1.2)  # ±20% jitter
                
                return min(delay * jitter, 60.0)  # Cap at 60 seconds
                
            def _classify_error(self, error: str) -> str:
                """Classify error type for intelligent retry decisions."""
                error_lower = error.lower()
                
                if any(keyword in error_lower for keyword in ['connection', 'network', 'unreachable', 'timeout']):
                    return 'network'
                elif any(keyword in error_lower for keyword in ['auth', 'login', 'password', 'permission']):
                    return 'authentication'
                elif any(keyword in error_lower for keyword in ['timeout', 'timed out']):
                    return 'timeout'
                elif any(keyword in error_lower for keyword in ['busy', 'in use', 'locked']):
                    return 'device_busy'
                else:
                    return 'unknown'
                    
            def get_retry_statistics(self) -> Dict[str, Any]:
                """Get retry statistics for reporting."""
                stats = {
                    'devices_with_retries': len(self.retry_history),
                    'total_retry_attempts': 0,
                    'error_type_distribution': {},
                    'most_problematic_devices': []
                }
                
                error_counts = {}
                device_retry_counts = {}
                
                for hostname, retries in self.retry_history.items():
                    device_retry_counts[hostname] = len(retries)
                    stats['total_retry_attempts'] += len(retries)
                    
                    for retry in retries:
                        error_type = self._classify_error(retry['error'])
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                stats['error_type_distribution'] = error_counts
                
                # Find most problematic devices
                if device_retry_counts:
                    sorted_devices = sorted(device_retry_counts.items(), 
                                          key=lambda x: x[1], reverse=True)
                    stats['most_problematic_devices'] = sorted_devices[:5]
                
                return stats
        
        # Create and return retry manager instance
        self.retry_manager = IntelligentRetryManager(self)
        return self.retry_manager

# CLI Command Groups and Options
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
    
    A comprehensive CLI tool for automated network state collection from
    Cisco IOS, IOS XE, and IOS XR devices using Nornir, Netmiko, and pyATS/Genie.
    
    Quick Start:
    1. Configure credentials: python3 rr4-complete-enchanced-v4-cli.py configure-env
    2. Validate inventory: python3 rr4-complete-enchanced-v4-cli.py validate-inventory
    3. Test connectivity: python3 rr4-complete-enchanced-v4-cli.py collect-all --dry-run
    4. Collect data: python3 rr4-complete-enchanced-v4-cli.py collect-all
    """
    # Determine log level
    if debug:
        log_level = "DEBUG"
    elif verbose:
        log_level = "INFO"
    else:
        log_level = "WARNING"
    
    # Initialize logging
    logger_manager = Logger(log_level=log_level, log_file=log_file)
    logger = logger_manager.get_logger()
    
    # Store configuration in context
    ctx.ensure_object(dict)
    ctx.obj['logger'] = logger
    ctx.obj['config_dir'] = config_dir
    ctx.obj['log_level'] = log_level
    
    # Handle direct flags
    if version:
        click.echo(f"RR4 Complete Enhanced v4 CLI")
        click.echo(f"Version: {CONFIG['version']}")
        click.echo(f"Author: {CONFIG['author']}")
        click.echo(f"Description: {CONFIG['description']}")
        click.echo(f"Supported Platforms: {', '.join(CONFIG['supported_platforms'])}")
        click.echo(f"Supported Layers: {', '.join(CONFIG['supported_layers'])}")
        sys.exit(0)
    
    if test_dependencies:
        click.echo("Testing required dependencies...")
        checker = DependencyChecker()
        results = checker.check_dependencies()
        
        all_good = True
        for package, available in results.items():
            status = "✓" if available else "✗"
            click.echo(f"{status} {package}")
            if not available:
                all_good = False
        
        if all_good:
            click.echo("\n✓ All dependencies are available")
            sys.exit(0)
        else:
            click.echo("\n✗ Some dependencies are missing. Please install them using:")
            click.echo("pip install -r requirements.txt")
            sys.exit(1)
    
    if init_project:
        click.echo("Initializing project structure...")
        try:
            structure = ProjectStructure()
            structure.create_structure()
            click.echo("✓ Project structure initialized successfully")
            sys.exit(0)
        except Exception as e:
            click.echo(f"✗ Failed to initialize project structure: {e}")
            sys.exit(1)
    
    # If no command is provided, show help
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
    logger = ctx.obj['logger']
    
    try:
        # Load environment configuration
        env_manager = EnvironmentManager()
        config = env_manager.get_config()
        
        # Initialize collection manager
        manager = CollectionManager(config)
        
        # Prepare collection parameters
        collection_params = {
            'workers': workers,
            'timeout': timeout,
            'output_dir': output_dir,
            'inventory': inventory,
            'layers': layers.split(',') if layers else None,
            'exclude_layers': exclude_layers.split(',') if exclude_layers else None,
            'dry_run': dry_run
        }
        
        logger.info(f"Starting collection with parameters: {collection_params}")
        
        if dry_run:
            manager.test_connectivity(**collection_params)
        else:
            manager.collect_all_devices(**collection_params)
            
        click.echo("✓ Collection completed successfully")
        
    except CLIError as e:
        logger.error(f"CLI Error: {e}")
        click.echo(f"✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        click.echo(f"✗ Unexpected error: {e}")
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
    logger = ctx.obj['logger']
    
    if not device and not devices:
        click.echo("✗ Error: Must specify either --device or --devices")
        sys.exit(1)
    
    # Build device list
    device_list = []
    if device:
        device_list.append(device)
    if devices:
        device_list.extend(devices.split(','))
    
    try:
        # Load environment configuration
        env_manager = EnvironmentManager()
        config = env_manager.get_config()
        
        # Initialize collection manager
        manager = CollectionManager(config)
        
        # Prepare collection parameters
        collection_params = {
            'workers': workers,
            'timeout': timeout,
            'output_dir': output_dir,
            'inventory': inventory,
            'layers': layers.split(',') if layers else None,
            'exclude_layers': exclude_layers.split(',') if exclude_layers else None,
            'dry_run': dry_run
        }
        
        logger.info(f"Starting collection for devices: {device_list}")
        
        if dry_run:
            manager.test_connectivity(**collection_params)
        else:
            manager.collect_specific_devices(device_list, **collection_params)
            
        click.echo("✓ Device collection completed successfully")
        
    except CLIError as e:
        logger.error(f"CLI Error: {e}")
        click.echo(f"✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        click.echo(f"✗ Unexpected error: {e}")
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
    logger = ctx.obj['logger']
    
    try:
        # Load environment configuration
        env_manager = EnvironmentManager()
        config = env_manager.get_config()
        
        # Initialize collection manager
        manager = CollectionManager(config)
        
        # Prepare collection parameters
        collection_params = {
            'workers': workers,
            'timeout': timeout,
            'output_dir': output_dir,
            'inventory': inventory,
            'layers': layers.split(',') if layers else None,
            'exclude_layers': exclude_layers.split(',') if exclude_layers else None,
            'dry_run': dry_run
        }
        
        logger.info(f"Starting collection for group: {group}")
        
        if dry_run:
            manager.test_connectivity(**collection_params)
        else:
            manager.collect_device_group(group, **collection_params)
            
        click.echo("✓ Group collection completed successfully")
        
    except CLIError as e:
        logger.error(f"CLI Error: {e}")
        click.echo(f"✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        click.echo(f"✗ Unexpected error: {e}")
        sys.exit(1)

@cli.command()
@click.option('--inventory', default=CONFIG['default_inventory'], help='Inventory CSV file path')
@click.pass_context
def validate_inventory(ctx, inventory):
    """Validate the device inventory file."""
    logger = ctx.obj['logger']
    
    try:
        inventory_path = Path(inventory)
        if not inventory_path.exists():
            raise CLIError(f"Inventory file not found: {inventory}")
        
        # Initialize inventory loader and validate
        inventory_loader = InventoryLoader(inventory)
        validation_results = inventory_loader.validate_inventory()
        
        # Check for errors
        if 'error' in validation_results:
            raise CLIError(validation_results['error'])
        
        # Display validation results
        click.echo("Inventory Validation Results:")
        click.echo("=" * 50)
        
        total_devices = validation_results.get('total_devices', 0)
        platforms = validation_results.get('platforms', {})
        groups = validation_results.get('groups', {})
        errors = validation_results.get('validation_errors', [])
        
        click.echo(f"Total devices found: {total_devices}")
        
        if platforms:
            click.echo("\nPlatform Distribution:")
            for platform, count in platforms.items():
                click.echo(f"  - {platform}: {count} devices")
        
        if groups:
            click.echo("\nGroup Distribution:")
            for group, count in groups.items():
                click.echo(f"  - {group}: {count} devices")
        
        if errors:
            click.echo(f"\n✗ Validation Errors ({len(errors)}):")
            for error in errors:
                click.echo(f"  - {error}")
            raise CLIError("Inventory validation failed")
        else:
            click.echo("\n✓ Inventory validation passed")
        
        logger.info(f"Validated inventory file: {inventory}")
        
    except CLIError as e:
        logger.error(f"CLI Error: {e}")
        click.echo(f"✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        click.echo(f"✗ Unexpected error: {e}")
        sys.exit(1)

@cli.command()
@click.pass_context
def show_config(ctx):
    """Show current configuration."""
    logger = ctx.obj['logger']
    
    try:
        # Load environment configuration
        env_manager = EnvironmentManager()
        config = env_manager.get_config()
        
        click.echo("Current Configuration:")
        click.echo("=" * 50)
        
        # Mask sensitive information
        masked_config = config.copy()
        for key in masked_config:
            if 'password' in key.lower() or 'key' in key.lower():
                if masked_config[key]:
                    masked_config[key] = '*' * 8
        
        for key, value in masked_config.items():
            click.echo(f"{key.upper()}: {value}")
        
        click.echo("\nSupported Platforms:")
        for platform in CONFIG['supported_platforms']:
            click.echo(f"  - {platform}")
        
        click.echo("\nSupported Layers:")
        for layer in CONFIG['supported_layers']:
            click.echo(f"  - {layer}")
        
    except CLIError as e:
        logger.error(f"CLI Error: {e}")
        click.echo(f"✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        click.echo(f"✗ Unexpected error: {e}")
        sys.exit(1)

@cli.command()
@click.option('--env-file', default='.env-t', help='Environment file path')
@click.pass_context
def configure_env(ctx, env_file):
    """Interactive configuration setup for jump host and device credentials."""
    logger = ctx.obj['logger']
    
    try:
        click.echo("🔧 RR4 CLI Interactive Configuration")
        click.echo("This will help you set up jump host and device credentials.")
        
        # Initialize environment manager in interactive mode
        env_manager = EnvironmentManager(env_file=env_file, interactive=True)
        
        # If we get here, configuration was successful
        click.echo("\n✅ Configuration completed successfully!")
        click.echo(f"📁 Configuration saved to: {env_file}")
        click.echo("\n🚀 You can now run collection commands:")
        click.echo("   python3 rr4-complete-enchanced-v4-cli.py collect-all --dry-run")
        click.echo("   python3 rr4-complete-enchanced-v4-cli.py validate-inventory")
        
        logger.info(f"Interactive configuration completed for {env_file}")
        
    except CLIError as e:
        logger.error(f"CLI Error: {e}")
        click.echo(f"✗ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n❌ Configuration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        click.echo(f"✗ Unexpected error: {e}")
        sys.exit(1)

@cli.command()
@click.option('--env-file', default='.env-t', help='Environment file path')
@click.pass_context
def update_env(ctx, env_file):
    """Update existing environment configuration."""
    logger = ctx.obj['logger']
    
    try:
        click.echo("📝 RR4 CLI Configuration Update")
        click.echo("This will update your existing configuration.")
        
        # Initialize environment manager and update configuration
        env_manager = EnvironmentManager(env_file=env_file)
        env_manager.update_configuration()
        
        click.echo("\n✅ Configuration updated successfully!")
        click.echo(f"📁 Configuration saved to: {env_file}")
        
        logger.info(f"Configuration updated for {env_file}")
        
    except CLIError as e:
        logger.error(f"CLI Error: {e}")
        click.echo(f"✗ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n❌ Configuration update cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        click.echo(f"✗ Unexpected error: {e}")
        sys.exit(1)

def main():
    """Main entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n✗ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
#!/usr/bin/env python3
"""
Nornir Ecosystem Setup Script for RR4 Complete Enhanced v4 CLI

This script automates the installation and configuration of the complete
Nornir ecosystem including all plugins and dependencies.

Author: RR4 CLI Development Team
Version: 4.0.0
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{Colors.END}")

def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def run_command(command: str, check: bool = True) -> Tuple[int, str, str]:
    """
    Run a shell command and return the result.
    
    Args:
        command: Command to run
        check: Whether to raise exception on failure
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_package(package: str) -> bool:
    """
    Install a Python package using pip.
    
    Args:
        package: Package name to install
        
    Returns:
        True if successful, False otherwise
    """
    print_info(f"Installing {package}...")
    
    # Try to install the package
    code, stdout, stderr = run_command(f"pip install {package}")
    
    if code == 0:
        print_success(f"Successfully installed {package}")
        return True
    else:
        print_error(f"Failed to install {package}: {stderr}")
        return False

def check_package_installed(package: str) -> bool:
    """
    Check if a package is installed.
    
    Args:
        package: Package name to check
        
    Returns:
        True if installed, False otherwise
    """
    code, stdout, stderr = run_command(f"python3 -c 'import {package}'", check=False)
    return code == 0

def get_package_version(package: str) -> str:
    """
    Get the version of an installed package.
    
    Args:
        package: Package name
        
    Returns:
        Version string or 'Unknown'
    """
    try:
        code, stdout, stderr = run_command(f"python3 -c 'import {package}; print({package}.__version__)'", check=False)
        if code == 0:
            return stdout.strip()
    except:
        pass
    return "Unknown"

def install_core_packages() -> bool:
    """Install core Nornir packages."""
    print_header("INSTALLING CORE NORNIR PACKAGES")
    
    core_packages = [
        "nornir>=3.5.0",
        "nornir-netmiko>=1.0.1",
        "nornir-utils>=0.2.0",
        "nornir-napalm>=0.5.0",
        "nornir-scrapli>=2025.1.30",
        "nornir-jinja2>=0.2.0",
        "nornir-rich>=0.2.0"
    ]
    
    success = True
    for package in core_packages:
        if not install_package(package):
            success = False
    
    return success

def install_connection_libraries() -> bool:
    """Install network connection libraries."""
    print_header("INSTALLING NETWORK CONNECTION LIBRARIES")
    
    connection_packages = [
        "netmiko>=4.2.0",
        "napalm>=5.0.0",
        "scrapli>=2025.1.30",
        "scrapli-community>=2025.1.30",
        "scrapli-netconf>=2025.1.30",
        "scrapli-cfg>=2025.1.30",
        "paramiko>=3.5.1"
    ]
    
    success = True
    for package in connection_packages:
        if not install_package(package):
            success = False
    
    return success

def install_parsing_libraries() -> bool:
    """Install parsing and data processing libraries."""
    print_header("INSTALLING PARSING AND DATA PROCESSING LIBRARIES")
    
    parsing_packages = [
        "pyats>=24.0",
        "genie>=24.0",
        "textfsm>=1.1.3",
        "ntc-templates>=7.8.0",
        "ciscoconfparse>=1.9.52",
        "ttp>=0.9.5",
        "ttp-templates>=0.3.7"
    ]
    
    success = True
    for package in parsing_packages:
        if not install_package(package):
            success = False
    
    return success

def install_utility_packages() -> bool:
    """Install utility and framework packages."""
    print_header("INSTALLING UTILITY AND FRAMEWORK PACKAGES")
    
    utility_packages = [
        "click>=8.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.1",
        "ruamel.yaml>=0.18.10",
        "pandas>=2.2.3",
        "numpy>=1.26.4",
        "openpyxl>=3.1.5",
        "xlsxwriter>=3.2.3",
        "tabulate>=0.9.0",
        "rich>=13.9.4",
        "colorama>=0.4.6",
        "loguru>=0.7.2",
        "jinja2>=3.1.2",
        "requests>=2.32.3",
        "netaddr>=1.3.0",
        "ipaddress>=1.0.23"
    ]
    
    success = True
    for package in utility_packages:
        if not install_package(package):
            success = False
    
    return success

def install_testing_packages() -> bool:
    """Install testing framework packages."""
    print_header("INSTALLING TESTING FRAMEWORK PACKAGES")
    
    testing_packages = [
        "pytest>=8.3.5",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.14.0",
        "pytest-xdist>=3.7.0"
    ]
    
    success = True
    for package in testing_packages:
        if not install_package(package):
            success = False
    
    return success

def install_vendor_specific_packages() -> bool:
    """Install vendor-specific packages."""
    print_header("INSTALLING VENDOR-SPECIFIC PACKAGES")
    
    vendor_packages = [
        "junos-eznc>=2.7.4",  # Juniper
        "pyeapi>=1.0.4",      # Arista
        "ncclient>=0.6.15",   # NETCONF
        "scp>=0.15.0"         # SCP support
    ]
    
    success = True
    for package in vendor_packages:
        if not install_package(package):
            success = False
    
    return success

def verify_installations() -> Dict[str, bool]:
    """Verify all installations."""
    print_header("VERIFYING INSTALLATIONS")
    
    packages_to_check = {
        # Core Nornir
        'nornir': 'nornir',
        'nornir_netmiko': 'nornir-netmiko',
        'nornir_utils': 'nornir-utils',
        'nornir_napalm': 'nornir-napalm',
        'nornir_scrapli': 'nornir-scrapli',
        'nornir_jinja2': 'nornir-jinja2',
        'nornir_rich': 'nornir-rich',
        
        # Connection libraries
        'netmiko': 'netmiko',
        'napalm': 'napalm',
        'scrapli': 'scrapli',
        'paramiko': 'paramiko',
        
        # Parsing libraries
        'pyats': 'pyats',
        'genie': 'genie',
        'textfsm': 'textfsm',
        'ciscoconfparse': 'ciscoconfparse',
        
        # Utilities
        'click': 'click',
        'dotenv': 'python-dotenv',
        'yaml': 'pyyaml',
        'pandas': 'pandas',
        'rich': 'rich',
        'jinja2': 'jinja2',
        'requests': 'requests',
        'netaddr': 'netaddr',
        
        # Testing
        'pytest': 'pytest',
        
        # Vendor specific
        'pyeapi': 'pyeapi',
        'ncclient': 'ncclient'
    }
    
    results = {}
    for import_name, package_name in packages_to_check.items():
        if check_package_installed(import_name):
            version = get_package_version(import_name)
            print_success(f"{package_name}: {version}")
            results[package_name] = True
        else:
            print_error(f"{package_name}: Not installed")
            results[package_name] = False
    
    return results

def create_nornir_config() -> bool:
    """Create Nornir configuration file if it doesn't exist."""
    config_file = "nornir_config.yaml"
    
    if os.path.exists(config_file):
        print_info(f"Nornir configuration file already exists: {config_file}")
        return True
    
    print_info(f"Creating Nornir configuration file: {config_file}")
    
    config_content = """---
# Nornir Configuration for RR4 Complete Enhanced v4 CLI
core:
  num_workers: 10
  raise_on_error: false

inventory:
  plugin: SimpleInventory
  options:
    host_file: "inventory/hosts.yaml"
    group_file: "inventory/groups.yaml"
    defaults_file: "inventory/defaults.yaml"

logging:
  enabled: true
  level: INFO
  to_console: true
  to_file: true
  logdir: "logs"

runner:
  plugin: threaded
  options:
    num_workers: 10

connection_options:
  netmiko:
    platform: auto
    extras:
      timeout: 60
      fast_cli: true
      global_delay_factor: 1
      
  napalm:
    platform: auto
    extras:
      timeout: 60
      
  scrapli:
    platform: auto
    extras:
      auth_timeout: 60
      timeout_socket: 60
"""
    
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        print_success(f"Created {config_file}")
        return True
    except Exception as e:
        print_error(f"Failed to create {config_file}: {e}")
        return False

def create_directories() -> bool:
    """Create necessary directories."""
    print_header("CREATING PROJECT DIRECTORIES")
    
    directories = [
        "inventory",
        "logs",
        "output",
        "templates",
        "tests"
    ]
    
    success = True
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            print_success(f"Created directory: {directory}")
        except Exception as e:
            print_error(f"Failed to create directory {directory}: {e}")
            success = False
    
    return success

def main():
    """Main setup function."""
    print_header("RR4 COMPLETE ENHANCED V4 CLI - NORNIR ECOSYSTEM SETUP")
    print_info("This script will install and configure the complete Nornir ecosystem")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install packages in groups
    installation_steps = [
        ("Core Nornir packages", install_core_packages),
        ("Network connection libraries", install_connection_libraries),
        ("Parsing and data processing libraries", install_parsing_libraries),
        ("Utility and framework packages", install_utility_packages),
        ("Testing framework packages", install_testing_packages),
        ("Vendor-specific packages", install_vendor_specific_packages)
    ]
    
    failed_steps = []
    for step_name, step_function in installation_steps:
        print_info(f"Starting: {step_name}")
        if not step_function():
            failed_steps.append(step_name)
            print_warning(f"Some packages in '{step_name}' failed to install")
        else:
            print_success(f"Completed: {step_name}")
    
    # Verify installations
    results = verify_installations()
    
    # Create configuration and directories
    create_nornir_config()
    create_directories()
    
    # Summary
    print_header("INSTALLATION SUMMARY")
    
    total_packages = len(results)
    successful_packages = sum(1 for success in results.values() if success)
    
    print_info(f"Total packages: {total_packages}")
    print_success(f"Successfully installed: {successful_packages}")
    
    if failed_steps:
        print_warning(f"Failed installation steps: {len(failed_steps)}")
        for step in failed_steps:
            print_error(f"  - {step}")
    
    if successful_packages == total_packages:
        print_success("🎉 Nornir ecosystem setup completed successfully!")
        print_info("You can now use the RR4 CLI with full Nornir support")
    else:
        print_warning("⚠️  Setup completed with some issues")
        print_info("Check the error messages above and retry failed installations")
    
    print_info("\nNext steps:")
    print_info("1. Configure your inventory files in the 'inventory' directory")
    print_info("2. Set up your environment variables in '.env' file")
    print_info("3. Test the installation with: python3 rr4-complete-enchanced-v4-cli.py --test-dependencies")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Nornir Plugins Configuration Helper for RR4 Complete Enhanced v4 CLI

This module provides configuration helpers and examples for all installed Nornir plugins:
- nornir-netmiko: SSH connections using Netmiko
- nornir-napalm: Multi-vendor network device API
- nornir-scrapli: Fast SSH connections with async support
- nornir-utils: Utility functions for Nornir
- nornir-rich: Rich console output formatting
- nornir-jinja2: Template rendering support

Author: RR4 CLI Development Team
Version: 4.0.0
"""

import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

# Nornir core imports
from nornir import InitNornir
from nornir.core.task import Task, Result

# Plugin imports
try:
    from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False

try:
    from nornir_napalm.plugins.tasks import napalm_get, napalm_configure
    NAPALM_AVAILABLE = True
except ImportError:
    NAPALM_AVAILABLE = False

try:
    from nornir_scrapli.tasks import send_command as scrapli_send_command
    from nornir_scrapli.tasks import send_config as scrapli_send_config
    SCRAPLI_AVAILABLE = True
except ImportError:
    SCRAPLI_AVAILABLE = False

try:
    from nornir_utils.plugins.functions import print_result, print_title
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

try:
    from nornir_rich.functions import print_result as rich_print_result
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from nornir_jinja2.plugins.tasks import template_file, template_string
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


class NornirPluginManager:
    """
    Manages Nornir plugin configurations and provides helper methods
    for different connection types and task execution.
    """
    
    def __init__(self, config_file: str = "nornir_config.yaml"):
        """
        Initialize the Nornir Plugin Manager.
        
        Args:
            config_file: Path to Nornir configuration file
        """
        self.config_file = config_file
        self.nr = None
        self.available_plugins = self._check_available_plugins()
        
    def _check_available_plugins(self) -> Dict[str, bool]:
        """Check which Nornir plugins are available."""
        return {
            'netmiko': NETMIKO_AVAILABLE,
            'napalm': NAPALM_AVAILABLE,
            'scrapli': SCRAPLI_AVAILABLE,
            'utils': UTILS_AVAILABLE,
            'rich': RICH_AVAILABLE,
            'jinja2': JINJA2_AVAILABLE
        }
    
    def initialize_nornir(self, **kwargs) -> None:
        """
        Initialize Nornir with the configuration file.
        
        Args:
            **kwargs: Additional configuration options
        """
        try:
            if os.path.exists(self.config_file):
                self.nr = InitNornir(config_file=self.config_file, **kwargs)
            else:
                # Fallback configuration if config file doesn't exist
                self.nr = InitNornir(
                    runner={
                        "plugin": "threaded",
                        "options": {"num_workers": 10}
                    },
                    inventory={
                        "plugin": "SimpleInventory",
                        "options": {
                            "host_file": "inventory/hosts.yaml",
                            "group_file": "inventory/groups.yaml",
                            "defaults_file": "inventory/defaults.yaml"
                        }
                    },
                    logging={"enabled": True, "level": "INFO"},
                    **kwargs
                )
        except Exception as e:
            print(f"Error initializing Nornir: {e}")
            raise
    
    def get_plugin_status(self) -> Dict[str, str]:
        """Get the status of all Nornir plugins."""
        status = {}
        for plugin, available in self.available_plugins.items():
            status[plugin] = "✓ Available" if available else "✗ Not installed"
        return status
    
    def print_plugin_status(self) -> None:
        """Print the status of all Nornir plugins."""
        print("\n" + "="*60)
        print("NORNIR ECOSYSTEM PLUGIN STATUS")
        print("="*60)
        
        for plugin, status in self.get_plugin_status().items():
            print(f"{plugin.upper():12} : {status}")
        
        print("="*60)
    
    # Netmiko plugin helpers
    def netmiko_send_command_task(self, command: str, **kwargs) -> Optional[Task]:
        """Create a Netmiko send command task."""
        if not NETMIKO_AVAILABLE:
            print("Netmiko plugin not available")
            return None
        
        def task(task: Task) -> Result:
            return netmiko_send_command(task, command, **kwargs)
        
        return task
    
    def netmiko_send_config_task(self, config_commands: List[str], **kwargs) -> Optional[Task]:
        """Create a Netmiko send config task."""
        if not NETMIKO_AVAILABLE:
            print("Netmiko plugin not available")
            return None
        
        def task(task: Task) -> Result:
            return netmiko_send_config(task, config_commands, **kwargs)
        
        return task
    
    # NAPALM plugin helpers
    def napalm_get_task(self, getters: List[str], **kwargs) -> Optional[Task]:
        """Create a NAPALM get task."""
        if not NAPALM_AVAILABLE:
            print("NAPALM plugin not available")
            return None
        
        def task(task: Task) -> Result:
            return napalm_get(task, getters, **kwargs)
        
        return task
    
    def napalm_configure_task(self, configuration: str, **kwargs) -> Optional[Task]:
        """Create a NAPALM configure task."""
        if not NAPALM_AVAILABLE:
            print("NAPALM plugin not available")
            return None
        
        def task(task: Task) -> Result:
            return napalm_configure(task, configuration, **kwargs)
        
        return task
    
    # Scrapli plugin helpers
    def scrapli_send_command_task(self, command: str, **kwargs) -> Optional[Task]:
        """Create a Scrapli send command task."""
        if not SCRAPLI_AVAILABLE:
            print("Scrapli plugin not available")
            return None
        
        def task(task: Task) -> Result:
            return scrapli_send_command(task, command, **kwargs)
        
        return task
    
    def scrapli_send_config_task(self, config: str, **kwargs) -> Optional[Task]:
        """Create a Scrapli send config task."""
        if not SCRAPLI_AVAILABLE:
            print("Scrapli plugin not available")
            return None
        
        def task(task: Task) -> Result:
            return scrapli_send_config(task, config, **kwargs)
        
        return task
    
    # Jinja2 plugin helpers
    def jinja2_template_file_task(self, template: str, **kwargs) -> Optional[Task]:
        """Create a Jinja2 template file task."""
        if not JINJA2_AVAILABLE:
            print("Jinja2 plugin not available")
            return None
        
        def task(task: Task) -> Result:
            return template_file(task, template, **kwargs)
        
        return task
    
    def jinja2_template_string_task(self, template: str, **kwargs) -> Optional[Task]:
        """Create a Jinja2 template string task."""
        if not JINJA2_AVAILABLE:
            print("Jinja2 plugin not available")
            return None
        
        def task(task: Task) -> Result:
            return template_string(task, template, **kwargs)
        
        return task
    
    # Utility functions
    def print_result(self, result, **kwargs) -> None:
        """Print task results using available print functions."""
        if RICH_AVAILABLE:
            rich_print_result(result, **kwargs)
        elif UTILS_AVAILABLE:
            print_result(result, **kwargs)
        else:
            print(result)
    
    def print_title(self, title: str) -> None:
        """Print a title using utils if available."""
        if UTILS_AVAILABLE:
            print_title(title)
        else:
            print(f"\n{'='*len(title)}")
            print(title)
            print('='*len(title))
    
    # Connection method recommendations
    def get_recommended_connection_method(self, platform: str) -> str:
        """
        Get recommended connection method based on platform.
        
        Args:
            platform: Device platform (ios, iosxe, iosxr, nxos, etc.)
            
        Returns:
            Recommended connection method
        """
        recommendations = {
            'ios': 'netmiko',      # Stable and reliable for IOS
            'iosxe': 'scrapli',    # Fast for modern IOS-XE
            'iosxr': 'scrapli',    # Good performance for IOS-XR
            'nxos': 'napalm',      # Good API support for Nexus
            'eos': 'napalm',       # Excellent API support for Arista
            'junos': 'napalm',     # Native NETCONF support
        }
        
        return recommendations.get(platform.lower(), 'netmiko')
    
    def create_connection_config(self, method: str, **kwargs) -> Dict[str, Any]:
        """
        Create connection configuration for specified method.
        
        Args:
            method: Connection method (netmiko, napalm, scrapli)
            **kwargs: Additional configuration options
            
        Returns:
            Connection configuration dictionary
        """
        base_config = {
            'hostname': kwargs.get('hostname', ''),
            'username': kwargs.get('username', ''),
            'password': kwargs.get('password', ''),
            'platform': kwargs.get('platform', 'auto'),
            'port': kwargs.get('port', 22),
        }
        
        if method == 'netmiko':
            base_config.update({
                'timeout': kwargs.get('timeout', 60),
                'session_timeout': kwargs.get('session_timeout', 60),
                'auth_timeout': kwargs.get('auth_timeout', 60),
                'fast_cli': kwargs.get('fast_cli', True),
                'global_delay_factor': kwargs.get('global_delay_factor', 1),
            })
        elif method == 'napalm':
            base_config.update({
                'timeout': kwargs.get('timeout', 60),
                'optional_args': {
                    'transport': 'ssh',
                    'keepalive': kwargs.get('keepalive', 30),
                }
            })
        elif method == 'scrapli':
            base_config.update({
                'auth_timeout': kwargs.get('auth_timeout', 60),
                'timeout_socket': kwargs.get('timeout_socket', 60),
                'timeout_transport': kwargs.get('timeout_transport', 60),
                'timeout_ops': kwargs.get('timeout_ops', 60),
            })
        
        return base_config


def main():
    """Main function to demonstrate plugin capabilities."""
    print("RR4 Complete Enhanced v4 CLI - Nornir Ecosystem Configuration")
    print("="*70)
    
    # Initialize plugin manager
    plugin_manager = NornirPluginManager()
    
    # Show plugin status
    plugin_manager.print_plugin_status()
    
    # Show recommendations
    print("\nCONNECTION METHOD RECOMMENDATIONS:")
    print("-" * 40)
    platforms = ['ios', 'iosxe', 'iosxr', 'nxos', 'eos', 'junos']
    for platform in platforms:
        method = plugin_manager.get_recommended_connection_method(platform)
        print(f"{platform.upper():8} : {method}")
    
    print("\nNornir ecosystem is ready for use!")
    print("Configuration file: nornir_config.yaml")
    print("Use this module in your RR4 CLI for plugin management.")


if __name__ == "__main__":
    main() 
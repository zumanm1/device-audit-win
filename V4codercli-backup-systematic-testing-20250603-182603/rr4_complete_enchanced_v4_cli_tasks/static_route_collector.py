#!/usr/bin/env python3
"""
Static Route Layer Collector for RR4 Complete Enhanced v4 CLI

This module collects static routing information from network devices including:
- Global static routes and default routes
- VRF-specific static routes
- Administrative distances and metrics
- Next-hop reachability
- Route tracking and BFD integration
- Static route redistribution

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rr4-complete-enchanced-v4-cli-core'))

import logging
import time
from typing import Dict, Any, List
from rr4_complete_enchanced_v4_cli_core.data_parser import DataParser
from rr4_complete_enchanced_v4_cli_core.output_handler import OutputHandler
from .base_collector import BaseCollector
from dataclasses import dataclass

@dataclass
class StaticRouteCommands:
    """Static route layer command definitions by platform."""
    
    ios_commands = [
        "show ip route static",
        "show ipv6 route static",
        "show running-config | include ip route"
    ]
    
    iosxe_commands = [
        "show ip route static",
        "show ipv6 route static", 
        "show running-config | include ip route"
    ]
    
    iosxr_commands = [
        "show route static",
        "show route ipv6 static",
        "show running-config router static"
    ]

class StaticRouteCollector(BaseCollector):
    """Collect static route information from network devices."""
    
    def __init__(self, device_type: str = 'cisco_ios'):
        """Initialize the static route collector."""
        self.data_parser = DataParser()
        self.commands_data = StaticRouteCommands()
        super().__init__(device_type)
    
    def _get_device_commands(self) -> Dict[str, List[str]]:
        """Get the list of commands for each device type.
        
        Returns:
            Dict mapping device types to lists of commands
        """
        return {
            'cisco_ios': self.commands_data.ios_commands,
            'cisco_iosxe': self.commands_data.iosxe_commands,
            'cisco_iosxr': self.commands_data.iosxr_commands
        }
    
    def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                          output_handler: OutputHandler) -> Dict[str, Any]:
        """Collect static route layer data from device."""
        commands = self._get_device_commands()[platform]
        
        results = {
            'hostname': hostname,
            'platform': platform,
            'layer': 'static',
            'timestamp': time.time(),
            'success_count': 0,
            'failure_count': 0,
            'commands_executed': [],
            'commands_failed': [],
            'data': {},
            'static_routes_count': 0
        }
        
        self.logger.info(f"Starting static route collection for {hostname} ({platform})")
        
        for command in commands:
            try:
                if hasattr(connection, 'send_command'):
                    self.logger.debug(f"Executing command: {command}")
                    
                    output = connection.send_command(command, read_timeout=60)
                    
                    # Store output using OutputHandler's correct method signature
                    output_handler.save_command_output(
                        hostname,   # positional: hostname
                        'static',   # positional: layer
                        command,    # positional: command
                        output      # positional: output
                    )
                    
                    # Parse output if possible
                    parsed_data = self.data_parser.parse_output(command, output, platform)
                    
                    results['data'][command] = {
                        'raw_output': output,
                        'parsed_data': parsed_data,
                        'success': True
                    }
                    results['success_count'] += 1
                    results['commands_executed'].append(command)
                    
                    self.logger.debug(f"Successfully executed: {command}")
                    
                else:
                    self.logger.error(f"Connection does not support send_command method")
                    results['failure_count'] += 1
                    results['commands_failed'].append(command)
                    
            except Exception as e:
                self.logger.error(f"Command failed: {command} - {e}")
                results['failure_count'] += 1
                results['commands_failed'].append(command)
                results['data'][command] = {
                    'error': str(e),
                    'success': False
                }
        
        # Calculate success rate
        total_commands = len(commands)
        if total_commands > 0:
            results['success_rate'] = (results['success_count'] / total_commands) * 100
        else:
            results['success_rate'] = 0
        
        self.logger.info(f"Static route collection completed for {hostname}: "
                        f"{results['success_count']}/{total_commands} commands successful "
                        f"({results['success_rate']:.1f}%)")
        
        return results
    
    def _sanitize_command_name(self, command: str) -> str:
        """Convert command to safe filename."""
        filename = command.replace(' ', '_').replace('|', '_pipe_')
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-'))
        return filename
    
    def get_layer_info(self) -> Dict[str, Any]:
        """Get information about this collector layer."""
        return {
            'name': 'static',
            'description': 'Static routing configuration and status data collection',
            'categories': [
                'Global Static Routes',
                'VRF Static Routes',
                'Default Routes'
            ],
            'platforms_supported': ['ios', 'iosxe', 'iosxr'],
            'estimated_time': '1-3 minutes per device'
        } 
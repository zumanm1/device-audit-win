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
from data_parser import DataParser
from output_handler import OutputHandler

class StaticRouteCollector:
    """Collect static routing information from network devices."""
    
    def __init__(self):
        self.logger = logging.getLogger('rr4_collector.static_collector')
        self.data_parser = DataParser()
    
    def get_commands_for_platform(self, platform: str) -> List[str]:
        """Get static route commands for specific platform."""
        platform_lower = platform.lower()
        
        if platform_lower == 'ios':
            return self._get_ios_commands()
        elif platform_lower == 'iosxe':
            return self._get_iosxe_commands()
        elif platform_lower == 'iosxr':
            return self._get_iosxr_commands()
        else:
            self.logger.warning(f"Unknown platform {platform}, using IOS commands")
            return self._get_ios_commands()
    
    def _get_ios_commands(self) -> List[str]:
        """IOS static route commands."""
        return [
            "show ip route static",
            "show ip route static detail",
            "show ip route 0.0.0.0",
            "show ip route summary",
            "show ip route vrf all static",
            "show running-config | include ip route"
        ]
    
    def _get_iosxe_commands(self) -> List[str]:
        """IOS XE static route commands."""
        return [
            "show ip route static",
            "show ip route static detail",
            "show ip route 0.0.0.0",
            "show ip route summary",
            "show ip route vrf all static",
            "show running-config | include ip route"
        ]
    
    def _get_iosxr_commands(self) -> List[str]:
        """IOS XR static route commands."""
        return [
            "show route static",
            "show route static detail", 
            "show route 0.0.0.0/0",
            "show route summary",
            "show route vrf all static",
            "show running-config router static"
        ]
    
    def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                          output_handler: OutputHandler) -> Dict[str, Any]:
        """Collect static route layer data from device."""
        commands = self.get_commands_for_platform(platform)
        
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
                    
                    # Store output with command-based filename
                    filename = self._sanitize_command_name(command)
                    output_handler.save_command_output(
                        output_dir=output_handler.base_output_dir / output_handler.collection_metadata.collection_id / hostname / 'static',
                        command=command,
                        output=output,
                        hostname=hostname,
                        layer='static',
                        platform=platform
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
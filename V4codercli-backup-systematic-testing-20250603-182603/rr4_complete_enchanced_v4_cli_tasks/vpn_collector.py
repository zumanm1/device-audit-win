#!/usr/bin/env python3
"""
VPN Layer Collector for RR4 Complete Enhanced v4 CLI

This module collects VPN-related information from network devices including:
- VRF definitions and route targets
- L3VPN routing tables and BGP information
- L2VPN services and pseudowires
- VPN service instances and bridge domains
- VPN interface assignments
- Import/export policies

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
from dataclasses import dataclass
from rr4_complete_enchanced_v4_cli_core.data_parser import DataParser
from rr4_complete_enchanced_v4_cli_core.output_handler import OutputHandler
from .base_collector import BaseCollector

@dataclass
class VPNCommands:
    """VPN layer command definitions by platform."""
    
    ios_commands = [
        "show ip vrf",
        "show ip vrf detail",
        "show ip route vrf all",
        "show mpls l3vpn vrf all"
    ]
    
    iosxe_commands = [
        "show ip vrf",
        "show ip vrf detail",
        "show ip route vrf all",
        "show mpls l3vpn vrf all"
    ]
    
    iosxr_commands = [
        "show vrf all",
        "show vrf all detail",
        "show route vrf all",
        "show l3vpn"
    ]

class VPNCollector(BaseCollector):
    """Collect VPN information from network devices."""
    
    def __init__(self, device_type: str = 'cisco_ios'):
        """Initialize the VPN collector."""
        self.data_parser = DataParser()
        self.commands_data = VPNCommands()
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
        """Collect VPN layer data from device."""
        commands = self._get_device_commands()[platform]
        
        results = {
            'hostname': hostname,
            'platform': platform,
            'layer': 'vpn',
            'timestamp': time.time(),
            'success_count': 0,
            'failure_count': 0,
            'commands_executed': [],
            'commands_failed': [],
            'data': {},
            'vrfs_discovered': [],
            'l2vpn_services': []
        }
        
        self.logger.info(f"Starting VPN collection for {hostname} ({platform})")
        
        for command in commands:
            try:
                if hasattr(connection, 'send_command'):
                    self.logger.debug(f"Executing command: {command}")
                    
                    # Set timeout based on command type
                    timeout = self._get_command_timeout(command)
                    
                    output = connection.send_command(command, read_timeout=timeout)
                    
                    # Store output using OutputHandler's correct method signature
                    output_handler.save_command_output(
                        hostname,   # positional: hostname
                        'vpn',      # positional: layer
                        command,    # positional: command
                        output      # positional: output
                    )
                    
                    # Parse output if possible
                    parsed_data = self.data_parser.parse_output(command, output, platform)
                    
                    # Extract VRF information if this is a VRF-related command
                    if 'vrf' in command.lower():
                        vrfs = self._extract_vrf_names(output, platform)
                        results['vrfs_discovered'].extend(vrfs)
                    
                    # Extract L2VPN service information
                    if any(l2_keyword in command.lower() for l2_keyword in ['l2vpn', 'xconnect', 'bridge-domain']):
                        services = self._extract_l2vpn_services(output, platform)
                        results['l2vpn_services'].extend(services)
                    
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
        
        # Remove duplicates from discovered lists
        results['vrfs_discovered'] = list(set(results['vrfs_discovered']))
        results['l2vpn_services'] = list(set(results['l2vpn_services']))
        
        # Calculate success rate
        total_commands = len(commands)
        if total_commands > 0:
            results['success_rate'] = (results['success_count'] / total_commands) * 100
        else:
            results['success_rate'] = 0
        
        self.logger.info(f"VPN collection completed for {hostname}: "
                        f"{results['success_count']}/{total_commands} commands successful "
                        f"({results['success_rate']:.1f}%) - "
                        f"Found {len(results['vrfs_discovered'])} VRFs, "
                        f"{len(results['l2vpn_services'])} L2VPN services")
        
        return results
    
    def _get_command_timeout(self, command: str) -> int:
        """Get appropriate timeout for command."""
        # Commands that might take longer
        long_commands = [
            'show ip route vrf all',
            'show route vrf all',
            'show ip bgp vpnv4 unicast all',
            'show bgp vpnv4 unicast',
            'show ip cef vrf all',
            'show cef vrf all'
        ]
        
        if any(long_cmd in command for long_cmd in long_commands):
            return 180  # 3 minutes for large routing tables
        else:
            return 90
    
    def _sanitize_command_name(self, command: str) -> str:
        """Convert command to safe filename."""
        # Replace spaces and special characters
        filename = command.replace(' ', '_').replace('|', '_pipe_')
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-'))
        return filename
    
    def _extract_vrf_names(self, output: str, platform: str) -> List[str]:
        """Extract VRF names from command output."""
        vrfs = []
        try:
            lines = output.split('\n')
            for line in lines:
                # Basic VRF name extraction - can be enhanced with platform-specific parsing
                if platform.lower() == 'iosxr':
                    if 'VRF:' in line:
                        vrf_name = line.split('VRF:')[1].strip().split()[0]
                        vrfs.append(vrf_name)
                else:
                    # IOS/IOS XE format
                    if len(line.split()) > 0 and not line.startswith(' ') and not line.startswith('Name'):
                        vrf_name = line.split()[0]
                        if vrf_name and vrf_name not in ['Name', 'Interfaces', 'Protocol']:
                            vrfs.append(vrf_name)
        except Exception as e:
            self.logger.debug(f"Error extracting VRF names: {e}")
        
        return vrfs
    
    def _extract_l2vpn_services(self, output: str, platform: str) -> List[str]:
        """Extract L2VPN service names from command output."""
        services = []
        try:
            lines = output.split('\n')
            for line in lines:
                # Basic service name extraction - can be enhanced with platform-specific parsing
                if 'vc-id' in line.lower() or 'xconnect' in line.lower():
                    parts = line.split()
                    if len(parts) > 1:
                        services.append(f"xconnect_{parts[0]}")
                elif 'bridge-domain' in line.lower() and platform.lower() == 'iosxr':
                    parts = line.split()
                    if len(parts) > 1:
                        services.append(f"bd_{parts[1]}")
        except Exception as e:
            self.logger.debug(f"Error extracting L2VPN services: {e}")
        
        return services
    
    def get_layer_info(self) -> Dict[str, Any]:
        """Get information about this collector layer."""
        return {
            'name': 'vpn',
            'description': 'L3VPN and L2VPN service data collection',
            'categories': [
                'VRF Definitions',
                'L3VPN Routing Tables',
                'BGP VPNv4/VPNv6',
                'L2VPN Services',
                'Pseudowires and Xconnects',
                'Bridge Domains',
                'Service Instances'
            ],
            'platforms_supported': ['ios', 'iosxe', 'iosxr'],
            'estimated_time': '3-8 minutes per device'
        } 
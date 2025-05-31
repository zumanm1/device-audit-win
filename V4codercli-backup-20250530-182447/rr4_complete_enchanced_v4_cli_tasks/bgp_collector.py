#!/usr/bin/env python3
"""
BGP Layer Collector for RR4 Complete Enhanced v4 CLI

This module collects BGP-related information from network devices including:
- BGP process information and summary
- BGP neighbor relationships and status
- BGP routing tables (IPv4, IPv6, VPNv4)
- BGP route-maps and policies
- BGP communities and AS paths

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
from .base_collector import BaseCollector

class BGPCollector(BaseCollector):
    """Collector for BGP routing protocol."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('rr4_collector.bgp_collector')
        self.data_parser = DataParser()
    
    def _get_device_commands(self) -> Dict[str, List[str]]:
        """Get BGP commands for each platform."""
        commands = {
            'cisco_ios': [
                'show ip bgp summary',
                'show ip bgp neighbors',
                'show ip bgp neighbors | include BGP neighbor|BGP state',
                'show ip bgp',
                'show ip bgp ipv4 unicast summary',
                'show ip bgp ipv4 unicast neighbors',
                'show ip bgp ipv4 unicast',
                'show ip bgp vpnv4 all summary',
                'show ip bgp vpnv4 all neighbors',
                'show ip bgp vpnv4 all',
                'show bgp ipv6 unicast summary',
                'show bgp ipv6 unicast neighbors',
                'show bgp ipv6 unicast',
                'show running-config | section router bgp'
            ],
            'cisco_iosxe': [
                'show ip bgp summary',
                'show ip bgp neighbors',
                'show ip bgp neighbors | include BGP neighbor|BGP state',
                'show ip bgp',
                'show ip bgp ipv4 unicast summary',
                'show ip bgp ipv4 unicast neighbors',
                'show ip bgp ipv4 unicast',
                'show ip bgp vpnv4 all summary',
                'show ip bgp vpnv4 all neighbors',
                'show ip bgp vpnv4 all',
                'show bgp ipv6 unicast summary',
                'show bgp ipv6 unicast neighbors',
                'show bgp ipv6 unicast',
                'show running-config | section router bgp'
            ],
            'cisco_iosxr': [
                'show bgp summary',
                'show bgp neighbors',
                'show bgp neighbors | include BGP neighbor|BGP state',
                'show bgp',
                'show bgp ipv4 unicast summary',
                'show bgp ipv4 unicast neighbors',
                'show bgp ipv4 unicast',
                'show bgp vpnv4 unicast summary',
                'show bgp vpnv4 unicast neighbors',
                'show bgp vpnv4 unicast',
                'show bgp ipv6 unicast summary',
                'show bgp ipv6 unicast neighbors',
                'show bgp ipv6 unicast',
                'show running-config router bgp'
            ]
        }
        return commands

    def process_output(self, outputs: Dict[str, str]) -> Dict[str, Any]:
        """Process BGP command outputs."""
        try:
            processed_data = {
                'ipv4_unicast': {
                    'enabled': False,
                    'neighbors': 0,
                    'established': 0,
                    'prefixes': 0
                },
                'ipv6_unicast': {
                    'enabled': False,
                    'neighbors': 0,
                    'established': 0,
                    'prefixes': 0
                },
                'vpnv4_unicast': {
                    'enabled': False,
                    'neighbors': 0,
                    'established': 0,
                    'prefixes': 0
                },
                'details': {}
            }

            # Process each command output
            for command, output in outputs.items():
                if not output:
                    continue

                # Store raw output
                processed_data['details'][command] = output

                # Process IPv4 unicast data
                if 'show ip bgp summary' in command or 'show bgp ipv4 unicast summary' in command:
                    if 'BGP router identifier' in output:
                        processed_data['ipv4_unicast']['enabled'] = True
                        # Count neighbors and established sessions
                        neighbors = [l for l in output.splitlines() if any(str(i) in l for i in range(10))]
                        processed_data['ipv4_unicast']['neighbors'] = len(neighbors)
                        processed_data['ipv4_unicast']['established'] = len([n for n in neighbors if any(state in n for state in ['0', '1', '2', '3', '4', '5'])])

                # Process IPv6 unicast data
                elif 'show bgp ipv6 unicast summary' in command:
                    if 'BGP router identifier' in output:
                        processed_data['ipv6_unicast']['enabled'] = True
                        # Count neighbors and established sessions
                        neighbors = [l for l in output.splitlines() if ':' in l]  # IPv6 addresses contain colons
                        processed_data['ipv6_unicast']['neighbors'] = len(neighbors)
                        processed_data['ipv6_unicast']['established'] = len([n for n in neighbors if any(state in n for state in ['0', '1', '2', '3', '4', '5'])])

                # Process VPNv4 unicast data
                elif 'show ip bgp vpnv4 all summary' in command or 'show bgp vpnv4 unicast summary' in command:
                    if 'BGP router identifier' in output:
                        processed_data['vpnv4_unicast']['enabled'] = True
                        # Count neighbors and established sessions
                        neighbors = [l for l in output.splitlines() if any(str(i) in l for i in range(10))]
                        processed_data['vpnv4_unicast']['neighbors'] = len(neighbors)
                        processed_data['vpnv4_unicast']['established'] = len([n for n in neighbors if any(state in n for state in ['0', '1', '2', '3', '4', '5'])])

                # Count prefixes
                if 'show ip bgp' in command and not any(x in command for x in ['summary', 'neighbors', 'vpnv4']):
                    processed_data['ipv4_unicast']['prefixes'] = len([l for l in output.splitlines() if '*>' in l])
                elif 'show bgp ipv6 unicast' in command and 'summary' not in command and 'neighbors' not in command:
                    processed_data['ipv6_unicast']['prefixes'] = len([l for l in output.splitlines() if '*>' in l])
                elif 'show ip bgp vpnv4 all' in command and not any(x in command for x in ['summary', 'neighbors']):
                    processed_data['vpnv4_unicast']['prefixes'] = len([l for l in output.splitlines() if '*>' in l])

            return processed_data

        except Exception as e:
            self.logger.error(f"Failed to process BGP outputs: {e}")
            raise
    
    def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                          output_handler: OutputHandler) -> Dict[str, Any]:
        """Collect BGP layer data from device."""
        commands = self._get_device_commands()[platform]
        
        results = {
            'hostname': hostname,
            'platform': platform,
            'layer': 'bgp',
            'timestamp': time.time(),
            'success_count': 0,
            'failure_count': 0,
            'commands_executed': [],
            'commands_failed': [],
            'data': {},
            'bgp_neighbors_count': 0,
            'bgp_routes_count': 0
        }
        
        self.logger.info(f"Starting BGP collection for {hostname} ({platform})")
        
        for command in commands:
            try:
                if hasattr(connection, 'send_command'):
                    self.logger.debug(f"Executing command: {command}")
                    
                    # Set timeout based on command type
                    timeout = self._get_command_timeout(command)
                    
                    output = connection.send_command(command, read_timeout=timeout)
                    
                    # Store output with command-based filename
                    filename = self._sanitize_command_name(command)
                    output_handler.save_command_output(
                        output_dir=output_handler.base_output_dir / output_handler.collection_metadata.collection_id / hostname / 'bgp',
                        command=command,
                        output=output,
                        hostname=hostname,
                        layer='bgp',
                        platform=platform
                    )
                    
                    # Parse output if possible
                    parsed_data = self.data_parser.parse_output(command, output, platform)
                    
                    # Analyze BGP information
                    self._analyze_bgp_output(command, output, results)
                    
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
                # Some BGP commands might fail if BGP is not configured
                if self._is_bgp_not_configured_error(str(e)):
                    self.logger.debug(f"BGP not configured: {command} - {e}")
                else:
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
        
        self.logger.info(f"BGP collection completed for {hostname}: "
                        f"{results['success_count']}/{total_commands} commands successful "
                        f"({results['success_rate']:.1f}%) - "
                        f"BGP neighbors: {results['bgp_neighbors_count']}, "
                        f"BGP routes: {results['bgp_routes_count']}")
        
        return results
    
    def _get_command_timeout(self, command: str) -> int:
        """Get appropriate timeout for command."""
        # Commands that might take much longer (large routing tables)
        very_long_commands = [
            'show ip bgp',
            'show bgp',
            'show ip bgp neighbors received-routes',
            'show ip bgp neighbors advertised-routes'
        ]
        
        # Commands that might take longer
        long_commands = [
            'show ip bgp summary',
            'show bgp summary',
            'show ip bgp neighbors',
            'show bgp neighbors'
        ]
        
        if any(long_cmd in command for long_cmd in very_long_commands):
            return 300  # 5 minutes for very large BGP tables
        elif any(long_cmd in command for long_cmd in long_commands):
            return 120  # 2 minutes for neighbor information
        else:
            return 60   # 1 minute for other commands
    
    def _sanitize_command_name(self, command: str) -> str:
        """Convert command to safe filename."""
        # Replace spaces and special characters
        filename = command.replace(' ', '_').replace('|', '_pipe_')
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-'))
        return filename
    
    def _analyze_bgp_output(self, command: str, output: str, results: Dict[str, Any]) -> None:
        """Analyze command output to extract BGP information."""
        try:
            if 'summary' in command.lower():
                # Count neighbors from summary
                lines = output.split('\n')
                neighbor_count = 0
                for line in lines:
                    # Look for neighbor entries (IP addresses followed by AS numbers)
                    if line.strip() and not line.startswith('BGP') and not line.startswith('Neighbor'):
                        parts = line.split()
                        if len(parts) >= 3:
                            # Check if first part looks like an IP address
                            first_part = parts[0]
                            if '.' in first_part and len(first_part.split('.')) == 4:
                                neighbor_count += 1
                results['bgp_neighbors_count'] = max(results['bgp_neighbors_count'], neighbor_count)
            
            elif 'show ip bgp' == command.strip() or 'show bgp' == command.strip():
                # Count routes from BGP table
                lines = output.split('\n')
                route_count = 0
                for line in lines:
                    # Look for route entries (lines starting with network prefixes or *)
                    if line.strip() and (line.startswith('*') or line.startswith('>')):
                        route_count += 1
                results['bgp_routes_count'] = max(results['bgp_routes_count'], route_count)
                        
        except Exception as e:
            self.logger.debug(f"Error analyzing BGP output for {command}: {e}")
    
    def _is_bgp_not_configured_error(self, error_message: str) -> bool:
        """Check if error indicates BGP is not configured."""
        not_configured_indicators = [
            'Invalid input detected',
            'No BGP',
            'BGP not active',
            'not configured',
            'not enabled'
        ]
        
        error_lower = error_message.lower()
        return any(indicator.lower() in error_lower for indicator in not_configured_indicators)
    
    def get_layer_info(self) -> Dict[str, Any]:
        """Get information about this collector layer."""
        return {
            'name': 'bgp',
            'description': 'Border Gateway Protocol data collection',
            'categories': [
                'BGP Process Information',
                'BGP Neighbors and Peering',
                'BGP Routing Tables',
                'BGP Route Policies',
                'BGP Communities and Attributes',
                'BGP Path Information'
            ],
            'platforms_supported': ['ios', 'iosxe', 'iosxr'],
            'estimated_time': '3-10 minutes per device (depending on table size)'
        } 
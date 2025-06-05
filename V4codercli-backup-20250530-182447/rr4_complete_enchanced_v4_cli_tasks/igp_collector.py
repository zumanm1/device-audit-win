#!/usr/bin/env python3
"""
IGP Layer Collector for RR4 Complete Enhanced v4 CLI

This module collects IGP (Interior Gateway Protocol) information from network devices including:
- OSPF process information, neighbors, and database
- EIGRP topology, neighbors, and metrics
- IS-IS neighbors, database, and topology
- Redistribution and routing policies
- Area and AS configurations

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import logging
import time
from typing import Dict, Any, List
from rr4_complete_enchanced_v4_cli_core.data_parser import DataParser
from rr4_complete_enchanced_v4_cli_core.output_handler import OutputHandler
from .base_collector import BaseCollector

class IGPCollector(BaseCollector):
    """Collector for IGP routing protocols (OSPF, ISIS, EIGRP)."""
    
    def __init__(self, connection: Any = None):
        """Initialize IGP collector.
        
        Args:
            connection: Network device connection object
        """
        super().__init__(connection)
        self.logger = logging.getLogger('rr4_collector.igp_collector')
        self.data_parser = DataParser()
    
    def collect(self) -> Dict[str, Any]:
        """Collect IGP data from device."""
        if not self.connection:
            raise ValueError("No connection provided")
            
        # Get device info
        platform = self._get_device_platform()
        hostname = self._get_device_hostname()
        
        # Create output handler
        output_handler = OutputHandler()
        
        return self.collect_layer_data(self.connection, hostname, platform, output_handler)
    
    def _get_device_platform(self) -> str:
        """Get device platform from connection."""
        if hasattr(self.connection, 'device_type'):
            platform = self.connection.device_type
            if 'cisco_ios' in platform:
                return 'ios'
            elif 'cisco_xr' in platform:
                return 'iosxr'
            else:
                return platform
        return 'ios'  # Default to IOS
    
    def _get_device_hostname(self) -> str:
        """Get device hostname from connection."""
        if hasattr(self.connection, 'host'):
            return self.connection.host
        return 'unknown'
    
    def get_commands_for_platform(self, platform: str) -> List[str]:
        """Get IGP commands for specific platform."""
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
        """IOS IGP commands."""
        return [
            # OSPF Commands
            "show ip ospf",
            "show ip ospf interface",
            "show ip ospf neighbor",
            "show ip ospf neighbor detail",
            "show ip ospf database",
            "show ip ospf database router",
            "show ip ospf database network",
            "show ip ospf database summary",
            "show ip ospf database external",
            "show ip ospf border-routers",
            "show ip ospf virtual-links",
            
            # EIGRP Commands
            "show ip eigrp neighbors",
            "show ip eigrp neighbors detail",
            "show ip eigrp topology",
            "show ip eigrp topology active",
            "show ip eigrp interfaces",
            "show ip eigrp interfaces detail",
            "show ip eigrp traffic",
            
            # IS-IS Commands (if configured)
            "show isis neighbors",
            "show isis neighbors detail", 
            "show isis database",
            "show isis database detail",
            "show isis topology",
            "show isis interface",
            
            # General routing commands
            "show ip protocols",
            "show ip route summary",
            "show running-config | section router"
        ]
    
    def _get_iosxe_commands(self) -> List[str]:
        """IOS XE IGP commands."""
        return [
            # OSPF Commands
            "show ip ospf",
            "show ip ospf interface",
            "show ip ospf neighbor", 
            "show ip ospf neighbor detail",
            "show ip ospf database",
            "show ip ospf database router",
            "show ip ospf database network",
            "show ip ospf database summary",
            "show ip ospf database external",
            "show ip ospf border-routers",
            "show ip ospf virtual-links",
            "show ip ospf statistics",
            
            # EIGRP Commands
            "show ip eigrp neighbors",
            "show ip eigrp neighbors detail",
            "show ip eigrp topology",
            "show ip eigrp topology active",
            "show ip eigrp interfaces",
            "show ip eigrp interfaces detail",
            "show ip eigrp traffic",
            
            # IS-IS Commands
            "show isis neighbors",
            "show isis neighbors detail",
            "show isis database",
            "show isis database detail", 
            "show isis topology",
            "show isis interface",
            
            # General routing commands
            "show ip protocols",
            "show ip route summary",
            "show running-config | section router"
        ]
    
    def _get_iosxr_commands(self) -> List[str]:
        """IOS XR IGP commands."""
        return [
            # OSPF Commands
            "show ospf",
            "show ospf interface",
            "show ospf neighbor",
            "show ospf neighbor detail",
            "show ospf database",
            "show ospf database router",
            "show ospf database network",
            "show ospf database summary",
            "show ospf database external",
            "show ospf border-routers",
            "show ospf virtual-links",
            "show ospf statistics",
            
            # IS-IS Commands
            "show isis",
            "show isis interface",
            "show isis neighbors",
            "show isis neighbors detail",
            "show isis database",
            "show isis database detail",
            "show isis topology",
            "show isis statistics",
            
            # General routing commands
            "show protocols",
            "show route summary",
            "show running-config router"
        ]
    
    def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                          output_handler: OutputHandler) -> Dict[str, Any]:
        """Collect IGP layer data from device."""
        commands = self.get_commands_for_platform(platform)
        
        results = {
            'hostname': hostname,
            'platform': platform,
            'layer': 'igp',
            'timestamp': time.time(),
            'success_count': 0,
            'failure_count': 0,
            'commands_executed': [],
            'commands_failed': [],
            'data': {},
            'protocols_detected': [],
            'neighbor_count': {'ospf': 0, 'eigrp': 0, 'isis': 0}
        }
        
        self.logger.info(f"Starting IGP collection for {hostname} ({platform})")
        
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
                        output_dir=output_handler.base_output_dir / output_handler.collection_metadata.collection_id / hostname / 'igp',
                        command=command,
                        output=output,
                        hostname=hostname,
                        layer='igp',
                        platform=platform
                    )
                    
                    # Parse output if possible
                    parsed_data = self.data_parser.parse_output(command, output, platform)
                    
                    # Analyze the output for IGP information
                    self._analyze_igp_output(command, output, results)
                    
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
                # Some commands might fail if protocol is not configured
                if self._is_protocol_not_configured_error(str(e)):
                    self.logger.debug(f"Protocol not configured: {command} - {e}")
                else:
                    self.logger.error(f"Command failed: {command} - {e}")
                
                results['failure_count'] += 1
                results['commands_failed'].append(command)
                results['data'][command] = {
                    'error': str(e),
                    'success': False
                }
        
        # Remove duplicates from protocols detected
        results['protocols_detected'] = list(set(results['protocols_detected']))
        
        # Calculate success rate
        total_commands = len(commands)
        if total_commands > 0:
            results['success_rate'] = (results['success_count'] / total_commands) * 100
        else:
            results['success_rate'] = 0
        
        # Create summary
        total_neighbors = sum(results['neighbor_count'].values())
        
        self.logger.info(f"IGP collection completed for {hostname}: "
                        f"{results['success_count']}/{total_commands} commands successful "
                        f"({results['success_rate']:.1f}%) - "
                        f"Protocols: {', '.join(results['protocols_detected'])} - "
                        f"Total neighbors: {total_neighbors}")
        
        return results 
    
    def _get_command_timeout(self, command: str) -> int:
        """Get appropriate timeout for command."""
        # Commands that might take longer
        long_commands = [
            'show ip ospf database',
            'show ospf database',
            'show isis database',
            'show ip eigrp topology',
            'show isis topology'
        ]
        
        if any(long_cmd in command for long_cmd in long_commands):
            return 120
        else:
            return 60
    
    def _sanitize_command_name(self, command: str) -> str:
        """Convert command to safe filename."""
        # Replace spaces and special characters
        filename = command.replace(' ', '_').replace('|', '_pipe_')
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-'))
        return filename
    
    def _analyze_igp_output(self, command: str, output: str, results: Dict[str, Any]) -> None:
        """Analyze command output to extract IGP information."""
        try:
            # Detect active protocols
            if 'ospf' in command.lower():
                if 'Router ID' in output or 'Process ID' in output:
                    results['protocols_detected'].append('OSPF')
                    # Count OSPF neighbors
                    if 'neighbor' in command.lower():
                        neighbor_count = output.count('Full')  # OSPF Full state
                        results['neighbor_count']['ospf'] = max(results['neighbor_count']['ospf'], neighbor_count)
            
            elif 'eigrp' in command.lower():
                if 'AS(' in output or 'EIGRP-IPv4' in output:
                    results['protocols_detected'].append('EIGRP')
                    # Count EIGRP neighbors
                    if 'neighbor' in command.lower():
                        lines = output.split('\n')
                        neighbor_count = len([line for line in lines if line.strip() and not line.startswith('IP-EIGRP')])
                        results['neighbor_count']['eigrp'] = max(results['neighbor_count']['eigrp'], neighbor_count)
            
            elif 'isis' in command.lower():
                if 'IS-IS Router:' in output or 'System Id' in output:
                    results['protocols_detected'].append('IS-IS')
                    # Count IS-IS neighbors
                    if 'neighbor' in command.lower():
                        neighbor_count = output.count('Up')  # IS-IS Up state
                        results['neighbor_count']['isis'] = max(results['neighbor_count']['isis'], neighbor_count)
                        
        except Exception as e:
            self.logger.debug(f"Error analyzing IGP output for {command}: {e}")
    
    def _is_protocol_not_configured_error(self, error_message: str) -> bool:
        """Check if error indicates protocol is not configured."""
        not_configured_indicators = [
            'Invalid input detected',
            'No OSPF',
            'No EIGRP',
            'No IS-IS',
            'not configured',
            'not enabled'
        ]
        
        error_lower = error_message.lower()
        return any(indicator.lower() in error_lower for indicator in not_configured_indicators)
    
    def get_layer_info(self) -> Dict[str, Any]:
        """Get information about this collector layer."""
        return {
            'name': 'igp',
            'description': 'Interior Gateway Protocol data collection (OSPF, EIGRP, IS-IS)',
            'categories': [
                'OSPF Process and Areas',
                'OSPF Neighbors and Database',
                'EIGRP Topology and Neighbors',
                'IS-IS Neighbors and Database',
                'Routing Protocol Redistribution',
                'IGP Metrics and Timers'
            ],
            'platforms_supported': ['ios', 'iosxe', 'iosxr'],
            'estimated_time': '2-4 minutes per device'
        } 

    def _get_device_commands(self) -> Dict[str, List[str]]:
        """Get IGP commands for each platform."""
        commands = {
            'cisco_ios': [
                # OSPF Commands
                'show ip ospf',
                'show ip ospf interface',
                'show ip ospf neighbor',
                'show ip ospf neighbor detail',
                'show ip ospf database',
                'show ip ospf database router',
                'show ip ospf database network',
                'show ip ospf database summary',
                'show ip ospf database external',
                'show ip ospf border-routers',
                'show ip ospf virtual-links',
                # EIGRP Commands
                'show ip eigrp neighbors',
                'show ip eigrp neighbors detail',
                'show ip eigrp topology',
                'show ip eigrp topology active',
                'show ip eigrp interfaces',
                'show ip eigrp interfaces detail',
                'show ip eigrp traffic',
                # ISIS Commands
                'show isis neighbors',
                'show isis neighbors detail',
                'show isis database',
                'show isis database detail',
                'show isis topology',
                'show isis interface',
                # General
                'show ip protocols',
                'show ip route summary',
                'show running-config | section router'
            ],
            'cisco_iosxe': [
                # OSPF Commands
                'show ip ospf',
                'show ip ospf interface',
                'show ip ospf neighbor',
                'show ip ospf neighbor detail',
                'show ip ospf database',
                'show ip ospf database router',
                'show ip ospf database network',
                'show ip ospf database summary',
                'show ip ospf database external',
                'show ip ospf border-routers',
                'show ip ospf virtual-links',
                'show ip ospf statistics',
                # EIGRP Commands
                'show ip eigrp neighbors',
                'show ip eigrp neighbors detail',
                'show ip eigrp topology',
                'show ip eigrp topology active',
                'show ip eigrp interfaces',
                'show ip eigrp interfaces detail',
                'show ip eigrp traffic',
                # ISIS Commands
                'show isis neighbors',
                'show isis neighbors detail',
                'show isis database',
                'show isis database detail',
                'show isis topology',
                'show isis interface',
                # General
                'show ip protocols',
                'show ip route summary',
                'show running-config | section router'
            ],
            'cisco_iosxr': [
                # OSPF Commands
                'show ospf',
                'show ospf interface',
                'show ospf neighbor',
                'show ospf neighbor detail',
                'show ospf database',
                'show ospf database router',
                'show ospf database network',
                'show ospf database summary',
                'show ospf database external',
                'show ospf border-routers',
                'show ospf virtual-links',
                'show ospf statistics',
                # ISIS Commands
                'show isis neighbors',
                'show isis neighbors detail',
                'show isis database',
                'show isis database detail',
                'show isis topology',
                'show isis interface',
                # General
                'show route protocol',
                'show route summary',
                'show running-config router'
            ]
        }
        return commands

    def process_output(self, outputs: Dict[str, str]) -> Dict[str, Any]:
        """Process IGP command outputs."""
        try:
            processed_data = {
                'ospf': {
                    'enabled': False,
                    'neighbors': 0,
                    'areas': 0,
                    'interfaces': 0
                },
                'isis': {
                    'enabled': False,
                    'neighbors': 0,
                    'areas': 0,
                    'interfaces': 0
                },
                'eigrp': {
                    'enabled': False,
                    'neighbors': 0,
                    'interfaces': 0
                },
                'details': {}
            }

            # Process each command output
            for command, output in outputs.items():
                if not output:
                    continue

                # Store raw output
                processed_data['details'][command] = output

                # Process OSPF data
                if 'show ip ospf' in command:
                    if 'Routing Process' in output:
                        processed_data['ospf']['enabled'] = True
                        # Count areas
                        processed_data['ospf']['areas'] = len([l for l in output.splitlines() if 'Area' in l])
                elif 'show ip ospf neighbor' in command and not 'detail' in command:
                    processed_data['ospf']['neighbors'] = len([l for l in output.splitlines() if 'FULL' in l])
                elif 'show ip ospf interface' in command:
                    processed_data['ospf']['interfaces'] = len([l for l in output.splitlines() if 'line protocol' in l])

                # Process ISIS data
                elif 'show isis neighbors' in command and not 'detail' in command:
                    if len(output.strip()) > 0:
                        processed_data['isis']['enabled'] = True
                        processed_data['isis']['neighbors'] = len([l for l in output.splitlines() if 'Up' in l])
                elif 'show isis interface' in command:
                    processed_data['isis']['interfaces'] = len([l for l in output.splitlines() if 'circuit' in l.lower()])

                # Process EIGRP data
                elif 'show ip eigrp neighbors' in command and not 'detail' in command:
                    if len(output.strip()) > 0:
                        processed_data['eigrp']['enabled'] = True
                        processed_data['eigrp']['neighbors'] = len([l for l in output.splitlines() if 'Up' in l])
                elif 'show ip eigrp interfaces' in command and not 'detail' in command:
                    processed_data['eigrp']['interfaces'] = len([l for l in output.splitlines() if 'Xmit Queue' in l])

            return processed_data

        except Exception as e:
            self.logger.error(f"Failed to process IGP outputs: {e}")
            raise 
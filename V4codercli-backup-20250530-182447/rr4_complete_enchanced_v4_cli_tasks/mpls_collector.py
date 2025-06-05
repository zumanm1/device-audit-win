#!/usr/bin/env python3
"""
MPLS Layer Collector for RR4 Complete Enhanced v4 CLI

This module collects MPLS information from network devices including:
- LDP/TDP neighbor information
- Label information base
- MPLS forwarding table
- MPLS interface configuration
- MPLS traffic engineering
- Segment routing configuration

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
from rr4_complete_enchanced_v4_cli_core.output_handler import OutputHandler, CollectionMetadata
from datetime import datetime
from .base_collector import BaseCollector

class MPLSCollector(BaseCollector):
    """Collector for MPLS configuration and state data."""
    
    def __init__(self, connection: Any = None):
        """Initialize MPLS collector.
        
        Args:
            connection: Network device connection object
        """
        super().__init__(connection)
        self.logger = logging.getLogger('rr4_collector.mpls_collector')
        self.data_parser = DataParser()
    
    def collect(self) -> Dict[str, Any]:
        """Collect MPLS data from device."""
        if not self.connection:
            raise ValueError("No connection provided")
            
        # Get device info
        platform = self._get_device_platform()
        hostname = self._get_device_hostname()
        
        # Create output handler and set collection metadata
        output_handler = OutputHandler()
        collection_metadata = CollectionMetadata(
            collection_id=f"mpls_{int(time.time())}",
            start_time=datetime.now().isoformat(),
            total_devices=1,
            layers_collected=['mpls']
        )
        output_handler.collection_metadata = collection_metadata
        
        # Create device directory structure
        device_dir = output_handler.base_output_dir / collection_metadata.collection_id / hostname / 'mpls'
        device_dir.mkdir(parents=True, exist_ok=True)
        
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
        """Get MPLS commands for specific platform."""
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
        """IOS MPLS commands."""
        return [
            # LDP/TDP Commands
            "show mpls ldp neighbor",
            "show mpls ldp neighbor detail",
            "show mpls ldp bindings",
            "show mpls ldp parameters",
            "show mpls ldp discovery",
            "show mpls ldp interface",
            
            # Label Information
            "show mpls forwarding-table",
            "show mpls forwarding-table detail",
            "show mpls label range",
            "show mpls interfaces",
            "show mpls interfaces detail",
            
            # Traffic Engineering
            "show mpls traffic-eng tunnels",
            "show mpls traffic-eng tunnels summary",
            "show mpls traffic-eng topology",
            "show mpls traffic-eng link-management",
            "show mpls traffic-eng link-management bandwidth-allocation",
            
            # Segment Routing
            "show segment-routing mpls",
            "show segment-routing mpls lb",
            "show segment-routing mpls connected-prefix-sid-map",
            
            # General MPLS
            "show running-config | section mpls",
            "show mpls ldp capabilities",
            "show mpls memory"
        ]
    
    def _get_iosxe_commands(self) -> List[str]:
        """IOS XE MPLS commands."""
        return [
            # LDP Commands
            "show mpls ldp neighbor",
            "show mpls ldp neighbor detail",
            "show mpls ldp bindings",
            "show mpls ldp capabilities",
            "show mpls ldp discovery",
            "show mpls ldp interface",
            "show mpls ldp parameters",
            
            # Label Information
            "show mpls forwarding-table",
            "show mpls forwarding-table detail",
            "show mpls label range",
            "show mpls interfaces",
            "show mpls interfaces detail",
            
            # Traffic Engineering
            "show mpls traffic-eng tunnels",
            "show mpls traffic-eng tunnels summary",
            "show mpls traffic-eng topology",
            "show mpls traffic-eng link-management",
            "show mpls traffic-eng link-management bandwidth-allocation",
            
            # Segment Routing
            "show segment-routing mpls",
            "show segment-routing mpls lb",
            "show segment-routing mpls connected-prefix-sid-map",
            "show segment-routing mpls state",
            
            # General MPLS
            "show running-config | section mpls",
            "show mpls ldp capabilities",
            "show mpls memory",
            "show mpls infrastructure lfd clients"
        ]
    
    def _get_iosxr_commands(self) -> List[str]:
        """IOS XR MPLS commands."""
        return [
            # LDP Commands
            "show mpls ldp neighbor",
            "show mpls ldp neighbor detail", 
            "show mpls ldp bindings",
            "show mpls ldp capabilities",
            "show mpls ldp discovery",
            "show mpls ldp interface",
            "show mpls ldp parameters",
            
            # Label Information
            "show mpls forwarding",
            "show mpls forwarding detail",
            "show mpls label range",
            "show mpls interfaces",
            "show mpls interfaces detail",
            
            # Traffic Engineering
            "show mpls traffic-eng tunnels",
            "show mpls traffic-eng tunnels summary",
            "show mpls traffic-eng topology",
            "show mpls traffic-eng link-management",
            "show mpls traffic-eng link-management bandwidth-allocation",
            
            # Segment Routing
            "show segment-routing mpls",
            "show segment-routing mpls label-block",
            "show segment-routing mpls mapping-server",
            "show segment-routing mpls state",
            
            # General MPLS
            "show running-config mpls",
            "show mpls ldp capabilities",
            "show mpls memory",
            "show mpls forwarding label-security interface"
        ]
    
    def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                          output_handler: OutputHandler) -> Dict[str, Any]:
        """Collect MPLS layer data from device."""
        commands = self.get_commands_for_platform(platform)
        
        results = {
            'hostname': hostname,
            'platform': platform,
            'layer': 'mpls',
            'timestamp': time.time(),
            'success_count': 0,
            'failure_count': 0,
            'commands_executed': [],
            'commands_failed': [],
            'data': {},
            'protocols_detected': [],
            'neighbor_count': {'ldp': 0, 'te': 0, 'sr': 0},
            'success': True  # Initialize success flag
        }
        
        self.logger.info(f"Starting MPLS collection for {hostname} ({platform})")
        
        # Create output directory
        output_dir = output_handler.base_output_dir / output_handler.collection_metadata.collection_id / hostname / 'mpls'
        output_dir.mkdir(parents=True, exist_ok=True)
        
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
                        output_dir=output_dir,
                        command=command,
                        output=output,
                        hostname=hostname,
                        layer='mpls',
                        platform=platform
                    )
                    
                    # Parse output if possible
                    parsed_data = self.data_parser.parse_output(command, output, platform)
                    
                    # Analyze the output for MPLS information
                    self._analyze_mpls_output(command, output, results)
                    
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
                    results['success'] = False
                    
            except Exception as e:
                # Some commands might fail if protocol is not configured
                if self._is_protocol_not_configured_error(str(e)):
                    self.logger.debug(f"Protocol not configured: {command} - {e}")
                else:
                self.logger.error(f"Command failed: {command} - {e}")
                    results['success'] = False
                
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
        
        self.logger.info(f"MPLS collection completed for {hostname}: "
                        f"{results['success_count']}/{total_commands} commands successful "
                        f"({results['success_rate']:.1f}%) - "
                        f"Protocols: {', '.join(results['protocols_detected'])} - "
                        f"Total neighbors: {total_neighbors}")
        
        return results
    
    def _get_command_timeout(self, command: str) -> int:
        """Get appropriate timeout for command."""
        # Commands that might take longer
        long_commands = [
            'show mpls ldp bindings',
            'show mpls forwarding-table',
            'show mpls traffic-eng topology',
            'show segment-routing'
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
    
    def _analyze_mpls_output(self, command: str, output: str, results: Dict[str, Any]) -> None:
        """Analyze command output to extract MPLS information."""
        try:
            # Detect active protocols
            if 'ldp' in command.lower():
                if any(pattern in output for pattern in ['Peer LDP Ident', 'TCP connection', 'LDP discovery sources']):
                    results['protocols_detected'].append('LDP')
                    # Count LDP neighbors
                    if 'neighbor' in command.lower():
                        neighbor_count = len([line for line in output.split('\n') 
                                           if 'Peer LDP Ident' in line])
                        results['neighbor_count']['ldp'] = max(
                            results['neighbor_count']['ldp'], 
                            neighbor_count
                        )
            
            elif 'traffic-eng' in command.lower():
                if any(pattern in output for pattern in ['Admin: up', 'Destination:', 'Tunnel', 'Path: valid']):
                    results['protocols_detected'].append('MPLS-TE')
                    # Count TE tunnels
                    if 'tunnels' in command.lower():
                        tunnel_count = len([line for line in output.split('\n') 
                                         if any(state in line for state in ['Admin: up', 'Oper: up'])])
                        results['neighbor_count']['te'] = max(
                            results['neighbor_count']['te'], 
                            tunnel_count
                        )
            
            elif 'segment-routing' in command.lower():
                if any(pattern in output for pattern in ['Segment Routing Global Block', 'Connected-Prefix-SID', 'SRGB']):
                    results['protocols_detected'].append('SR-MPLS')
                    # Count SR mappings
                    if 'mapping' in command.lower() or 'Connected-Prefix-SID' in output:
                        mapping_count = len([line for line in output.split('\n') 
                                          if any(pattern in line for pattern in ['index', 'range', 'SID'])])
                        results['neighbor_count']['sr'] = max(
                            results['neighbor_count']['sr'], 
                            mapping_count
                        )
                        
        except Exception as e:
            self.logger.debug(f"Error analyzing MPLS output for {command}: {e}")
    
    def _is_protocol_not_configured_error(self, error_message: str) -> bool:
        """Check if error indicates protocol is not configured."""
        not_configured_indicators = [
            'Invalid input detected',
            'MPLS not enabled',
            'LDP not running',
            'MPLS TE not enabled',
            'not configured',
            'not enabled'
        ]
        
        error_lower = error_message.lower()
        return any(indicator.lower() in error_lower for indicator in not_configured_indicators)
    
    def get_layer_info(self) -> Dict[str, Any]:
        """Get information about this collector layer."""
        return {
            'name': 'mpls',
            'description': 'MPLS data collection (LDP, TE, SR)',
            'categories': [
                'LDP/TDP Neighbors and Bindings',
                'MPLS Forwarding and Labels',
                'Traffic Engineering Tunnels',
                'Segment Routing Configuration',
                'MPLS Interface Status',
                'Resource Allocation'
            ],
            'platforms_supported': ['ios', 'iosxe', 'iosxr'],
            'estimated_time': '2-4 minutes per device'
        }

    def _get_device_commands(self) -> Dict[str, List[str]]:
        """Get MPLS commands for each platform."""
        commands = {
            'cisco_ios': [
                'show mpls ldp neighbor',
                'show mpls ldp bindings',
                'show mpls forwarding-table',
                'show mpls traffic-eng tunnels',
                'show mpls traffic-eng topology',
                'show mpls label range',
                'show mpls interfaces',
                'show mpls ldp discovery',
                'show mpls ldp parameters',
                'show segment-routing mpls',
                'show segment-routing traffic-eng policy all',
                'show running-config | section mpls'
            ],
            'cisco_iosxe': [
                'show mpls ldp neighbor',
                'show mpls ldp bindings',
                'show mpls forwarding-table',
                'show mpls traffic-eng tunnels',
                'show mpls traffic-eng topology',
                'show mpls label range',
                'show mpls interfaces',
                'show mpls ldp discovery',
                'show mpls ldp parameters',
                'show segment-routing mpls',
                'show segment-routing traffic-eng policy all',
                'show running-config | section mpls'
            ],
            'cisco_iosxr': [
                'show mpls ldp neighbor',
                'show mpls ldp bindings',
                'show mpls forwarding',
                'show mpls traffic-eng tunnels',
                'show mpls traffic-eng topology',
                'show mpls label range',
                'show mpls interfaces',
                'show mpls ldp discovery',
                'show mpls ldp parameters',
                'show segment-routing mpls',
                'show segment-routing traffic-eng policy all',
                'show running-config | include mpls'
            ]
        }
        return commands

    def process_output(self, outputs: Dict[str, str]) -> Dict[str, Any]:
        """Process MPLS command outputs."""
        try:
            processed_data = {
                'ldp_neighbors': 0,
                'te_tunnels': 0,
                'sr_policies': 0,
                'label_bindings': 0,
                'interfaces': 0,
                'protocols': {
                    'ldp': False,
                    'te': False,
                    'sr': False
                },
                'details': {}
            }

            # Process each command output
            for command, output in outputs.items():
                if not output:
                    continue

                # Store raw output
                processed_data['details'][command] = output

                # Process LDP neighbors
                if 'show mpls ldp neighbor' in command and 'Peer LDP Ident' in output:
                    processed_data['ldp_neighbors'] = len([l for l in output.splitlines() if 'Peer LDP Ident' in l])
                    processed_data['protocols']['ldp'] = True

                # Process TE tunnels
                elif 'show mpls traffic-eng tunnels' in command:
                    if 'Signalled-Name' in output or 'TUNNEL ID' in output:
                        processed_data['te_tunnels'] = len([l for l in output.splitlines() if 'up' in l.lower()])
                        processed_data['protocols']['te'] = True

                # Process SR policies
                elif 'show segment-routing' in command:
                    if 'Policy name' in output or 'Policy ID' in output:
                        processed_data['sr_policies'] = len([l for l in output.splitlines() if 'active' in l.lower()])
                        processed_data['protocols']['sr'] = True

                # Process label bindings
                elif 'show mpls ldp bindings' in command:
                    processed_data['label_bindings'] = len([l for l in output.splitlines() if 'local binding' in l.lower()])

                # Process interfaces
                elif 'show mpls interfaces' in command:
                    processed_data['interfaces'] = len([l for l in output.splitlines() if 'Interface' in l])

            return processed_data

        except Exception as e:
            self.logger.error(f"Failed to process MPLS outputs: {e}")
            raise 
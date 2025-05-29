#!/usr/bin/env python3
"""
Inventory Loader Module for RR4 Complete Enhanced v4 CLI

This module handles loading device inventory from CSV files and converting
them to Nornir inventory format with proper platform detection and grouping.

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import csv
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class DeviceInfo:
    """Device information container."""
    hostname: str
    management_ip: str
    wan_ip: Optional[str] = None
    model_name: Optional[str] = None
    platform: Optional[str] = None
    device_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    groups: List[str] = None

    def __post_init__(self):
        if self.groups is None:
            self.groups = []

class InventoryLoader:
    """Load and convert CSV inventory to Nornir format."""
    
    def __init__(self, csv_file: str, config_dir: str = "config"):
        self.csv_file = Path(csv_file)
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger('rr4_collector.inventory')
        
        # Platform detection mapping
        self.platform_mapping = {
            'cisco 4431': 'iosxe',
            'cisco 4451': 'iosxe', 
            'cisco 4321': 'iosxe',
            'cisco 3945': 'ios',
            'cisco 2911': 'ios',
            'cisco asr': 'iosxr',
            'cisco ncs': 'iosxr',
            'cisco xrv': 'iosxr'
        }
        
        # Device type mapping for Netmiko
        self.device_type_mapping = {
            'ios': 'cisco_ios',
            'iosxe': 'cisco_xe',
            'iosxr': 'cisco_xr'
        }
    
    def load_csv_inventory(self) -> List[DeviceInfo]:
        """Load device information from CSV file."""
        if not self.csv_file.exists():
            raise FileNotFoundError(f"Inventory file not found: {self.csv_file}")
        
        devices = []
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Extract device information - handle both old and new CSV formats
                    hostname = row.get('hostname', '').strip()
                    
                    # Handle both 'ip_address' and 'management_ip' columns
                    management_ip = (row.get('ip_address', '') or row.get('management_ip', '')).strip()
                    
                    if not hostname or not management_ip:
                        self.logger.warning(f"Skipping incomplete row: {row}")
                        continue
                    
                    # Create device info with new CSV format support
                    device = DeviceInfo(
                        hostname=hostname,
                        management_ip=management_ip,
                        wan_ip=row.get('wan_ip', '').strip() or None,
                        model_name=row.get('model', '').strip() or row.get('model_name', '').strip() or None,
                        platform=row.get('platform', '').strip() or None,
                        device_type=row.get('device_type', '').strip() or None,
                        username=row.get('username', '').strip() or None,
                        password=row.get('password', '').strip() or None
                    )
                    
                    # Handle groups - can be comma-separated string or single group
                    groups_str = row.get('groups', '').strip()
                    if groups_str:
                        device.groups = [g.strip() for g in groups_str.split(',') if g.strip()]
                    else:
                        device.groups = []
                    
                    # Auto-detect platform if not provided
                    if not device.platform:
                        device.platform = self._detect_platform(device.model_name)
                    
                    # Auto-detect device type if not provided
                    if not device.device_type:
                        device.device_type = self.device_type_mapping.get(device.platform, 'cisco_ios')
                    
                    # Auto-assign additional groups based on hostname patterns
                    auto_groups = self._assign_groups(device.hostname)
                    device.groups.extend([g for g in auto_groups if g not in device.groups])
                    
                    # Ensure 'all_devices' group is always present
                    if 'all_devices' not in device.groups:
                        device.groups.append('all_devices')
                    
                    devices.append(device)
                    self.logger.debug(f"Loaded device: {device.hostname} ({device.platform}) - Groups: {device.groups}")
        
        except Exception as e:
            self.logger.error(f"Error loading CSV inventory: {e}")
            raise
        
        self.logger.info(f"Loaded {len(devices)} devices from inventory")
        return devices
    
    def _detect_platform(self, model_name: Optional[str]) -> str:
        """Detect platform based on model name."""
        if not model_name:
            return 'ios'  # Default fallback
        
        model_lower = model_name.lower()
        
        for pattern, platform in self.platform_mapping.items():
            if pattern in model_lower:
                return platform
        
        # Default to IOS if no match
        return 'ios'
    
    def _assign_groups(self, hostname: str) -> List[str]:
        """Assign device groups based on hostname patterns."""
        groups = ['all_devices']
        hostname_lower = hostname.lower()
        
        # Role-based grouping
        if 'core' in hostname_lower:
            groups.append('core_routers')
        elif 'edge' in hostname_lower:
            groups.append('edge_routers')
        elif 'branch' in hostname_lower:
            groups.append('branch_routers')
        elif 'pe' in hostname_lower:
            groups.append('pe_routers')
        elif 'p' in hostname_lower:
            groups.append('p_routers')
        
        # Location-based grouping (if pattern exists)
        if 'dc1' in hostname_lower:
            groups.append('datacenter1')
        elif 'dc2' in hostname_lower:
            groups.append('datacenter2')
        
        return groups
    
    def generate_nornir_inventory(self, devices: List[DeviceInfo], 
                                 default_username: str, default_password: str,
                                 jump_host_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate Nornir inventory structure with jump host support."""
        hosts = {}
        groups = {}
        
        # Collect all unique groups
        all_groups = set()
        for device in devices:
            all_groups.update(device.groups)
        
        # Create group definitions with jump host configuration
        for group in all_groups:
            group_config = {
                'platform': 'cisco',
                'connection_options': {
                    'netmiko': {
                        'platform': 'cisco_ios',  # Will be overridden per host
                        'extras': {
                            'timeout': 60,
                            'session_timeout': 300,
                            'global_delay_factor': 2
                        }
                    },
                    'napalm': {
                        'platform': 'ios',
                        'extras': {
                            'timeout': 60,
                            'optional_args': {
                                'transport': 'ssh',
                                'keepalive': 30
                            }
                        }
                    },
                    'scrapli': {
                        'platform': 'cisco_iosxe',
                        'extras': {
                            'auth_timeout': 60,
                            'timeout_socket': 60,
                            'timeout_transport': 60
                        }
                    }
                }
            }
            
            # Add jump host configuration if provided
            if jump_host_config:
                for conn_type in ['netmiko', 'napalm', 'scrapli']:
                    if conn_type in group_config['connection_options']:
                        group_config['connection_options'][conn_type]['extras'].update({
                            'ssh_config_file': None,
                            'sock': None,  # Will be set by connection manager
                            'use_keys': False,
                            'allow_agent': False
                        })
            
            groups[group] = group_config
        
        # Create host definitions
        for device in devices:
            # Map platform to connection-specific platforms
            netmiko_platform = device.device_type
            napalm_platform = {
                'ios': 'ios',
                'iosxe': 'ios',
                'iosxr': 'iosxr'
            }.get(device.platform, 'ios')
            scrapli_platform = {
                'ios': 'cisco_iosxe',
                'iosxe': 'cisco_iosxe', 
                'iosxr': 'cisco_iosxr'
            }.get(device.platform, 'cisco_iosxe')
            
            host_config = {
                'hostname': device.management_ip,
                'platform': device.platform,
                'groups': device.groups,
                'data': {
                    'management_ip': device.management_ip,
                    'wan_ip': device.wan_ip,
                    'model_name': device.model_name,
                    'device_type': device.device_type,
                    'vendor': 'cisco',
                    'os_version': 'unknown'
                },
                'connection_options': {
                    'netmiko': {
                        'platform': netmiko_platform,
                        'username': device.username or default_username,
                        'password': device.password or default_password,
                        'extras': {
                            'timeout': 60,
                            'session_timeout': 300,
                            'global_delay_factor': 2,
                            'fast_cli': True
                        }
                    },
                    'napalm': {
                        'platform': napalm_platform,
                        'username': device.username or default_username,
                        'password': device.password or default_password,
                        'extras': {
                            'timeout': 60,
                            'optional_args': {
                                'transport': 'ssh',
                                'keepalive': 30,
                                'ssh_strict': False
                            }
                        }
                    },
                    'scrapli': {
                        'platform': scrapli_platform,
                        'username': device.username or default_username,
                        'password': device.password or default_password,
                        'extras': {
                            'auth_timeout': 60,
                            'timeout_socket': 60,
                            'timeout_transport': 60,
                            'auth_strict_key': False
                        }
                    }
                }
            }
            
            # Add jump host configuration to each connection type if provided
            if jump_host_config:
                for conn_type in ['netmiko', 'napalm', 'scrapli']:
                    host_config['connection_options'][conn_type]['extras'].update({
                        'ssh_config_file': None,
                        'sock': None,  # Will be set by connection manager
                        'use_keys': False,
                        'allow_agent': False
                    })
            
            hosts[device.hostname] = host_config
        
        return {
            'hosts': hosts,
            'groups': groups
        }
    
    def save_nornir_inventory(self, inventory: Dict[str, Any]) -> None:
        """Save Nornir inventory to YAML files."""
        # Ensure inventory directory exists
        inventory_dir = self.config_dir / 'inventory'
        inventory_dir.mkdir(parents=True, exist_ok=True)
        
        # Save hosts.yaml
        hosts_file = inventory_dir / 'hosts.yaml'
        with open(hosts_file, 'w', encoding='utf-8') as file:
            yaml.dump(inventory['hosts'], file, default_flow_style=False, indent=2)
        
        # Save groups.yaml
        groups_file = inventory_dir / 'groups.yaml'
        with open(groups_file, 'w', encoding='utf-8') as file:
            yaml.dump(inventory['groups'], file, default_flow_style=False, indent=2)
        
        self.logger.info(f"Saved Nornir inventory to {inventory_dir}")
    
    def convert_csv_to_nornir(self, default_username: str, default_password: str,
                             jump_host_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Complete conversion from CSV to Nornir inventory."""
        # Load devices from CSV
        devices = self.load_csv_inventory()
        
        # Generate Nornir inventory with jump host support
        inventory = self.generate_nornir_inventory(devices, default_username, default_password, jump_host_config)
        
        # Save to files
        self.save_nornir_inventory(inventory)
        
        return inventory
    
    def validate_inventory(self) -> Dict[str, Any]:
        """Validate inventory file and return statistics."""
        try:
            devices = self.load_csv_inventory()
            
            stats = {
                'total_devices': len(devices),
                'platforms': {},
                'groups': {},
                'validation_errors': []
            }
            
            # Count platforms and groups
            for device in devices:
                # Platform stats
                platform = device.platform
                stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
                
                # Group stats
                for group in device.groups:
                    stats['groups'][group] = stats['groups'].get(group, 0) + 1
                
                # Validation checks
                if not device.management_ip:
                    stats['validation_errors'].append(f"{device.hostname}: Missing management IP")
                
                if not device.platform:
                    stats['validation_errors'].append(f"{device.hostname}: Unknown platform")
            
            return stats
            
        except Exception as e:
            return {
                'error': str(e),
                'validation_errors': [f"Failed to load inventory: {e}"]
            } 
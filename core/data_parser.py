#!/usr/bin/env python3
"""
Data Parser Module for RR4 Complete Enhanced v4 CLI

This module handles data parsing using pyATS/Genie parsers with fallback
mechanisms for unsupported commands and error handling.

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import re

# pyATS/Genie imports
try:
    from genie.libs.parser.utils import get_parser
    from genie.metaparser.util.exceptions import SchemaEmptyParserError, SchemaMissingKeyError
    from pyats.topology import Device
    GENIE_AVAILABLE = True
except ImportError:
    GENIE_AVAILABLE = False

@dataclass
class ParseResult:
    """Container for parsing results."""
    command: str
    success: bool
    parsed_data: Optional[Dict[str, Any]] = None
    raw_output: str = ""
    parser_used: str = ""
    error: Optional[str] = None
    parsing_time: float = 0.0

class DataParser:
    """Parse command output using pyATS/Genie with fallback mechanisms."""
    
    def __init__(self):
        self.logger = logging.getLogger('rr4_collector.data_parser')
        self.genie_available = GENIE_AVAILABLE
        
        if not self.genie_available:
            self.logger.warning("pyATS/Genie not available - only raw text output will be saved")
        
        # Command to parser mapping
        self.parser_mapping = self._initialize_parser_mapping()
        
        # Platform-specific command variations
        self.platform_commands = self._initialize_platform_commands()
    
    def _initialize_parser_mapping(self) -> Dict[str, str]:
        """Initialize mapping of commands to Genie parsers."""
        return {
            # Health layer
            'show version': 'show version',
            'show inventory': 'show inventory',
            'show processes cpu': 'show processes cpu',
            'show memory summary': 'show memory summary',
            'show environment all': 'show environment all',
            
            # Interface layer
            'show interfaces description': 'show interfaces description',
            'show ip interface brief': 'show ip interface brief',
            'show ipv6 interface brief': 'show ipv6 interface brief',
            'show interfaces': 'show interfaces',
            'show ip interface': 'show ip interface',
            'show arp': 'show arp',
            'show ipv6 neighbors': 'show ipv6 neighbors',
            'show lldp neighbors detail': 'show lldp neighbors detail',
            'show cdp neighbors detail': 'show cdp neighbors detail',
            
            # IGP layer
            'show ip ospf': 'show ip ospf',
            'show ip ospf interface brief': 'show ip ospf interface brief',
            'show ip ospf neighbor': 'show ip ospf neighbor',
            'show ip ospf database': 'show ip ospf database',
            
            # MPLS layer
            'show mpls interfaces': 'show mpls interfaces',
            'show mpls ldp discovery': 'show mpls ldp discovery',
            'show mpls ldp neighbor': 'show mpls ldp neighbor',
            'show mpls ldp bindings': 'show mpls ldp bindings',
            'show mpls forwarding-table': 'show mpls forwarding-table',
            'show ip cef': 'show ip cef',
            
            # BGP layer
            'show ip bgp summary': 'show ip bgp summary',
            'show ip bgp neighbors': 'show ip bgp neighbors',
            'show ip bgp': 'show ip bgp',
            'show bgp vpnv4 unicast summary': 'show bgp vpnv4 unicast summary',
            'show bgp vpnv4 unicast': 'show bgp vpnv4 unicast',
            
            # VPN layer
            'show vrf': 'show vrf',
            'show ip route vrf': 'show ip route vrf',
            'show ip cef vrf': 'show ip cef vrf',
            
            # Static routing
            'show ip route static': 'show ip route static'
        }
    
    def _initialize_platform_commands(self) -> Dict[str, Dict[str, str]]:
        """Initialize platform-specific command variations."""
        return {
            'ios': {
                'show ip interface brief': 'show ip interface brief',
                'show ipv6 interface brief': 'show ipv6 interface brief',
                'show ip ospf': 'show ip ospf',
                'show ip bgp summary': 'show ip bgp summary'
            },
            'iosxe': {
                'show ip interface brief': 'show ip interface brief',
                'show ipv6 interface brief': 'show ipv6 interface brief',
                'show ip ospf': 'show ip ospf',
                'show ip bgp summary': 'show ip bgp summary'
            },
            'iosxr': {
                'show ip interface brief': 'show ipv4 interface brief',
                'show ipv6 interface brief': 'show ipv6 interface brief',
                'show ip ospf': 'show ospf',
                'show ip bgp summary': 'show bgp ipv4 unicast summary'
            }
        }
    
    def parse_command_output(self, command: str, output: str, platform: str = 'ios') -> ParseResult:
        """Parse command output using appropriate parser."""
        import time
        start_time = time.time()
        
        result = ParseResult(
            command=command,
            success=False,
            raw_output=output
        )
        
        try:
            # Try Genie parsing first
            if self.genie_available:
                genie_result = self._parse_with_genie(command, output, platform)
                if genie_result.success:
                    result.success = True
                    result.parsed_data = genie_result.parsed_data
                    result.parser_used = "genie"
                    result.parsing_time = time.time() - start_time
                    return result
            
            # Fallback to basic text parsing
            text_result = self._parse_with_text_patterns(command, output)
            if text_result.success:
                result.success = True
                result.parsed_data = text_result.parsed_data
                result.parser_used = "text_patterns"
            else:
                # If all parsing fails, still mark as success with raw output
                result.success = True
                result.parsed_data = {"raw_output": output}
                result.parser_used = "raw_text"
            
        except Exception as e:
            self.logger.error(f"Parsing failed for command '{command}': {e}")
            result.error = str(e)
            result.parsed_data = {"raw_output": output, "error": str(e)}
            result.parser_used = "error_fallback"
        
        result.parsing_time = time.time() - start_time
        return result
    
    def _parse_with_genie(self, command: str, output: str, platform: str) -> ParseResult:
        """Parse output using Genie parsers."""
        result = ParseResult(command=command, success=False)
        
        try:
            # Get platform-specific command if available
            platform_command = self._get_platform_command(command, platform)
            
            # Create a mock device for Genie
            device = Device('mock_device', os=platform)
            
            # Get the appropriate parser
            parser_class = get_parser(platform_command, device)
            if not parser_class:
                self.logger.debug(f"No Genie parser found for: {platform_command}")
                return result
            
            # Parse the output
            parser = parser_class(device=device)
            parsed_data = parser.parse(output=output)
            
            if parsed_data:
                result.success = True
                result.parsed_data = parsed_data
                self.logger.debug(f"Successfully parsed with Genie: {command}")
            
        except (SchemaEmptyParserError, SchemaMissingKeyError) as e:
            self.logger.debug(f"Genie parser schema error for '{command}': {e}")
        except Exception as e:
            self.logger.debug(f"Genie parsing failed for '{command}': {e}")
        
        return result
    
    def _parse_with_text_patterns(self, command: str, output: str) -> ParseResult:
        """Parse output using text patterns and regex."""
        result = ParseResult(command=command, success=False)
        
        try:
            # Basic text parsing for common commands
            if 'show version' in command.lower():
                parsed_data = self._parse_show_version(output)
            elif 'show ip interface brief' in command.lower():
                parsed_data = self._parse_interface_brief(output)
            elif 'show ip bgp summary' in command.lower():
                parsed_data = self._parse_bgp_summary(output)
            elif 'show ip ospf neighbor' in command.lower():
                parsed_data = self._parse_ospf_neighbors(output)
            else:
                # Generic line-by-line parsing
                parsed_data = self._parse_generic_table(output)
            
            if parsed_data:
                result.success = True
                result.parsed_data = parsed_data
                self.logger.debug(f"Successfully parsed with text patterns: {command}")
        
        except Exception as e:
            self.logger.debug(f"Text pattern parsing failed for '{command}': {e}")
        
        return result
    
    def _get_platform_command(self, command: str, platform: str) -> str:
        """Get platform-specific command variation."""
        if platform in self.platform_commands:
            return self.platform_commands[platform].get(command, command)
        return command
    
    def _parse_show_version(self, output: str) -> Dict[str, Any]:
        """Parse show version output."""
        data = {}
        
        # Extract version information
        version_match = re.search(r'Version\s+([^\s,]+)', output, re.IGNORECASE)
        if version_match:
            data['version'] = version_match.group(1)
        
        # Extract hostname
        hostname_match = re.search(r'^(\S+)\s+uptime', output, re.MULTILINE)
        if hostname_match:
            data['hostname'] = hostname_match.group(1)
        
        # Extract uptime
        uptime_match = re.search(r'uptime is (.+)', output, re.IGNORECASE)
        if uptime_match:
            data['uptime'] = uptime_match.group(1)
        
        # Extract model
        model_match = re.search(r'cisco\s+(\S+)', output, re.IGNORECASE)
        if model_match:
            data['model'] = model_match.group(1)
        
        return data
    
    def _parse_interface_brief(self, output: str) -> Dict[str, Any]:
        """Parse interface brief output."""
        interfaces = {}
        
        lines = output.split('\n')
        for line in lines:
            # Skip header lines
            if 'Interface' in line or 'Protocol' in line or not line.strip():
                continue
            
            # Parse interface line
            parts = line.split()
            if len(parts) >= 6:
                interface = parts[0]
                ip_address = parts[1] if parts[1] != 'unassigned' else None
                method = parts[2] if len(parts) > 2 else None
                status = parts[4] if len(parts) > 4 else None
                protocol = parts[5] if len(parts) > 5 else None
                
                interfaces[interface] = {
                    'ip_address': ip_address,
                    'method': method,
                    'status': status,
                    'protocol': protocol
                }
        
        return {'interfaces': interfaces}
    
    def _parse_bgp_summary(self, output: str) -> Dict[str, Any]:
        """Parse BGP summary output."""
        data = {'neighbors': {}}
        
        lines = output.split('\n')
        in_neighbor_section = False
        
        for line in lines:
            # Look for neighbor section
            if 'Neighbor' in line and 'AS' in line:
                in_neighbor_section = True
                continue
            
            if in_neighbor_section and line.strip():
                parts = line.split()
                if len(parts) >= 5 and self._is_ip_address(parts[0]):
                    neighbor_ip = parts[0]
                    as_number = parts[2] if len(parts) > 2 else None
                    state = parts[-1] if parts else None
                    
                    data['neighbors'][neighbor_ip] = {
                        'as_number': as_number,
                        'state': state
                    }
        
        return data
    
    def _parse_ospf_neighbors(self, output: str) -> Dict[str, Any]:
        """Parse OSPF neighbors output."""
        neighbors = {}
        
        lines = output.split('\n')
        for line in lines:
            # Skip header lines
            if 'Neighbor ID' in line or 'Interface' in line or not line.strip():
                continue
            
            parts = line.split()
            if len(parts) >= 4 and self._is_ip_address(parts[0]):
                neighbor_id = parts[0]
                priority = parts[1] if len(parts) > 1 else None
                state = parts[2] if len(parts) > 2 else None
                interface = parts[5] if len(parts) > 5 else None
                
                neighbors[neighbor_id] = {
                    'priority': priority,
                    'state': state,
                    'interface': interface
                }
        
        return {'neighbors': neighbors}
    
    def _parse_generic_table(self, output: str) -> Dict[str, Any]:
        """Generic table parsing for unknown commands."""
        lines = output.split('\n')
        data = {
            'lines': [line.strip() for line in lines if line.strip()],
            'line_count': len([line for line in lines if line.strip()])
        }
        
        # Try to identify table structure
        if len(lines) > 2:
            # Look for header line
            potential_headers = []
            for i, line in enumerate(lines[:5]):  # Check first 5 lines
                if any(keyword in line.lower() for keyword in ['interface', 'neighbor', 'route', 'address']):
                    potential_headers.append((i, line.strip()))
            
            if potential_headers:
                data['potential_headers'] = potential_headers
        
        return data
    
    def _is_ip_address(self, text: str) -> bool:
        """Check if text is an IP address."""
        try:
            parts = text.split('.')
            if len(parts) == 4:
                return all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            pass
        return False
    
    def get_supported_commands(self, platform: str = 'ios') -> List[str]:
        """Get list of commands with Genie parser support."""
        if not self.genie_available:
            return []
        
        supported = []
        for command in self.parser_mapping.keys():
            platform_command = self._get_platform_command(command, platform)
            try:
                device = Device('test', os=platform)
                parser_class = get_parser(platform_command, device)
                if parser_class:
                    supported.append(command)
            except Exception:
                pass
        
        return supported
    
    def validate_parser_availability(self, commands: List[str], platform: str = 'ios') -> Dict[str, bool]:
        """Validate parser availability for a list of commands."""
        results = {}
        
        for command in commands:
            if not self.genie_available:
                results[command] = False
                continue
            
            try:
                platform_command = self._get_platform_command(command, platform)
                device = Device('test', os=platform)
                parser_class = get_parser(platform_command, device)
                results[command] = parser_class is not None
            except Exception:
                results[command] = False
        
        return results

class ParserRegistry:
    """Registry for managing custom parsers."""
    
    def __init__(self):
        self.custom_parsers: Dict[str, callable] = {}
        self.logger = logging.getLogger('rr4_collector.parser_registry')
    
    def register_parser(self, command_pattern: str, parser_function: callable) -> None:
        """Register a custom parser function."""
        self.custom_parsers[command_pattern] = parser_function
        self.logger.info(f"Registered custom parser for: {command_pattern}")
    
    def get_parser(self, command: str) -> Optional[callable]:
        """Get custom parser for command."""
        for pattern, parser in self.custom_parsers.items():
            if re.search(pattern, command, re.IGNORECASE):
                return parser
        return None
    
    def list_parsers(self) -> List[str]:
        """List all registered custom parsers."""
        return list(self.custom_parsers.keys()) 
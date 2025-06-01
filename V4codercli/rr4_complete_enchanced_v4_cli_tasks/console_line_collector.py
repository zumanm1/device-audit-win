#!/usr/bin/env python3
"""
Console Line Collector for RR4 Complete Enhanced v4 CLI

This module collects console line configuration information from Cisco network devices including:
- Show line output to discover available console lines
- Running configuration for each console line (x/y/z format)
- Line status and availability information
- Console line specific settings and configurations

Supports Cisco IOS routers with NM4 console cards.
Line numbering format: x/y/z where:
- x: 0 or 1 (slot)
- y: 0 or 1 (subslot)  
- z: 0 to 22 (port number)

Author: AI Assistant
Version: 1.0.1
Created: 2025-05-31
Updated: 2025-01-27 - Enhanced parsing for IOS/IOS XR formats
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rr4_complete_enchanced_v4_cli_core'))

import logging
import time
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from rr4_complete_enchanced_v4_cli_core.data_parser import DataParser
from rr4_complete_enchanced_v4_cli_core.output_handler import OutputHandler

@dataclass
class ConsoleLineCommands:
    """Console line command definitions by platform."""
    
    # Base commands for line discovery
    ios_base_commands = [
        "show line",
        "show running-config | include line",
        "show running-config | section line"
    ]
    
    iosxe_base_commands = [
        "show line",
        "show running-config | include line",
        "show running-config | section line"
    ]
    
    iosxr_base_commands = [
        "show line",
        "show running-config line",
        "show running-config | include \"line|aux|console\""
    ]

class ConsoleLineCollector:
    """Collect console line configuration information from network devices."""
    
    def __init__(self):
        self.logger = logging.getLogger('rr4_collector.console_line_collector')
        self.data_parser = DataParser()
        self.commands = ConsoleLineCommands()
        
        # Enhanced console line patterns for different platforms
        self.line_patterns = {
            'ios': {
                # Pattern for IOS show line output - looking for x/y/z in the "Int" column (last column)
                'line_with_int': r'^\s*\*?\s*(\d+)\s+(\d+)\s+(\w+)\s+.*?(\d+/\d+/\d+)\s*$',
                # Alternative pattern for lines with more spacing
                'line_with_spacing': r'^\s*\*?\s*(\d+)\s+(\d+)\s+(\w+)\s+.*?\s+(\d+/\d+/\d+)$',
                # Simple line without interface column
                'simple_line': r'^\s*\*?\s*(\d+)\s+(\d+)\s+(\w+)'
            },
            'iosxe': {
                'line_with_int': r'^\s*\*?\s*(\d+)\s+(\d+)\s+(\w+)\s+.*?(\d+/\d+/\d+)\s*$',
                'line_with_spacing': r'^\s*\*?\s*(\d+)\s+(\d+)\s+(\w+)\s+.*?\s+(\d+/\d+/\d+)$',
                'simple_line': r'^\s*\*?\s*(\d+)\s+(\d+)\s+(\w+)'
            },
            'iosxr': {
                # Pattern for IOS XR show line output - x/y/z appears in the "Tty" column (first column)
                'tty_line': r'^\s*(\d+/\d+/\d+)\s+(\d+)\s+(\w+)',
                'named_line': r'^\s*(con\d+|aux\d+|vty\d+)\s+(\d+)\s+(\w+)'
            }
        }
    
    def get_commands_for_platform(self, platform: str) -> List[str]:
        """Get console line commands for specific platform."""
        platform_lower = platform.lower()
        
        if platform_lower == 'ios':
            return self.commands.ios_base_commands.copy()
        elif platform_lower == 'iosxe':
            return self.commands.iosxe_base_commands.copy()
        elif platform_lower == 'iosxr':
            return self.commands.iosxr_base_commands.copy()
        else:
            self.logger.warning(f"Unknown platform {platform}, using IOS commands")
            return self.commands.ios_base_commands.copy()
    
    def parse_show_line_output(self, output: str, platform: str) -> List[Dict[str, Any]]:
        """Parse 'show line' output to extract console line information with enhanced platform support."""
        lines = []
        platform_lower = platform.lower()
        patterns = self.line_patterns.get(platform_lower, self.line_patterns['ios'])
        
        self.logger.debug(f"Parsing show line output for platform {platform}")
        
        for line_text in output.split('\n'):
            line_text = line_text.strip()
            if not line_text or 'Tty' in line_text or 'Line' in line_text or line_text.startswith('*'):
                continue
            
            # Skip header and separator lines
            if any(header in line_text.lower() for header in ['typ', 'tx/rx', 'modem', 'roty', 'acco', 'acci', 'uses', 'noise', 'overruns']):
                continue
                
            if 'not in async mode' in line_text.lower() or 'no hardware support' in line_text.lower():
                # Extract x/y/z ranges from text like "0/0/0-0/0/22, 0/1/0-0/1/22"
                range_matches = re.findall(r'(\d+/\d+/\d+)-(\d+/\d+/\d+)', line_text)
                for start_range, end_range in range_matches:
                    self.logger.info(f"Found line range: {start_range} to {end_range}")
                    # Add these as potential console lines
                    lines.extend(self._generate_line_range(start_range, end_range))
                continue
            
            # Try different patterns based on platform
            line_info = None
            
            if platform_lower == 'iosxr':
                # IOS XR format: Tty column contains x/y/z
                for pattern_name, pattern in patterns.items():
                    match = re.match(pattern, line_text)
                    if match:
                        if pattern_name == 'tty_line':
                            # x/y/z in Tty column
                            line_info = {
                                'line_number': match.group(2),
                                'line_type': match.group(3).lower(),
                                'line_id': match.group(1),  # x/y/z format
                                'tty_name': match.group(1),
                                'status': 'available',
                                'raw_line': line_text,
                                'platform': platform_lower
                            }
                        elif pattern_name == 'named_line':
                            # Named lines like con0, aux0, vty0
                            line_info = {
                                'line_number': match.group(2),
                                'line_type': match.group(3).lower(),
                                'line_id': match.group(1),
                                'tty_name': match.group(1),
                                'status': 'available',
                                'raw_line': line_text,
                                'platform': platform_lower
                            }
                        break
            else:
                # IOS/IOS XE format: x/y/z in Int column
                for pattern_name, pattern in patterns.items():
                    match = re.match(pattern, line_text)
                    if match:
                        if pattern_name == 'line_with_int' and len(match.groups()) >= 4:
                            # Line with interface column containing x/y/z
                            line_info = {
                                'line_number': match.group(1),
                                'tty_number': match.group(2),
                                'line_type': match.group(3).lower(),
                                'line_id': match.group(4),  # x/y/z format
                                'status': 'available',
                                'raw_line': line_text,
                                'platform': platform_lower
                            }
                        elif pattern_name == 'line_with_spacing' and len(match.groups()) >= 4:
                            # Line with more spacing and x/y/z at end
                            line_info = {
                                'line_number': match.group(1),
                                'tty_number': match.group(2),
                                'line_type': match.group(3).lower(),
                                'line_id': match.group(4),  # x/y/z format
                                'status': 'available',
                                'raw_line': line_text,
                                'platform': platform_lower
                            }
                        elif pattern_name == 'simple_line':
                            # Check if this line has x/y/z at the end manually
                            # Split the line and check the last column
                            parts = line_text.split()
                            line_id = ''
                            if len(parts) > 10:  # IOS lines have many columns
                                last_part = parts[-1]
                                if '/' in last_part and self.validate_line_format(last_part):
                                    line_id = last_part
                            
                            line_info = {
                                'line_number': match.group(1),
                                'tty_number': match.group(2),
                                'line_type': match.group(3).lower(),
                                'line_id': line_id,  # x/y/z format if found
                                'status': 'available',
                                'raw_line': line_text,
                                'platform': platform_lower
                            }
                        break
            
            if line_info:
                # Extract additional status information
                parts = line_text.split()
                if len(parts) > 5:
                    # Look for status indicators
                    for part in parts[4:]:
                        if part != '-' and part not in ['0', '0/0']:
                            line_info['additional_status'] = part
                            break
                
                lines.append(line_info)
                self.logger.debug(f"Parsed line: {line_info}")
        
        self.logger.info(f"Parsed {len(lines)} lines from show line output")
        return lines
    
    def _generate_line_range(self, start_range: str, end_range: str) -> List[Dict[str, Any]]:
        """Generate line entries for a range like 0/0/0-0/0/22."""
        lines = []
        
        # Parse start and end ranges
        start_match = re.match(r'(\d+)/(\d+)/(\d+)', start_range)
        end_match = re.match(r'(\d+)/(\d+)/(\d+)', end_range)
        
        if not start_match or not end_match:
            return lines
        
        start_x, start_y, start_z = map(int, start_match.groups())
        end_x, end_y, end_z = map(int, end_match.groups())
        
        # Generate all lines in the range
        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                z_start = start_z if (x == start_x and y == start_y) else 0
                z_end = end_z if (x == end_x and y == end_y) else 22
                
                for z in range(z_start, z_end + 1):
                    line_id = f"{x}/{y}/{z}"
                    lines.append({
                        'line_number': f"aux_{x}_{y}_{z}",
                        'line_type': 'aux',
                        'line_id': line_id,
                        'status': 'range_specified',
                        'raw_line': f"Range line {line_id}",
                        'platform': 'ios',
                        'from_range': True
                    })
        
        return lines
    
    def extract_console_lines(self, line_info: List[Dict[str, Any]]) -> List[str]:
        """Extract console line identifiers in x/y/z format with enhanced detection."""
        console_lines = []
        
        for line in line_info:
            line_id = line.get('line_id', '')
            line_type = line.get('line_type', '').lower()
            platform = line.get('platform', 'ios')
            
            # Enhanced detection for different scenarios
            valid_line = False
            
            # Check for x/y/z format in line_id
            if line_id and '/' in line_id and self.validate_line_format(line_id):
                valid_line = True
            
            # Additional checks for console-related lines
            if valid_line and line_type in ['aux', 'con', 'tty']:
                console_lines.append(line_id)
                self.logger.debug(f"Found console line: {line_id} (type: {line_type})")
        
        # Remove duplicates and sort
        unique_lines = sorted(set(console_lines))
        self.logger.info(f"Extracted {len(unique_lines)} unique console lines: {unique_lines}")
        return unique_lines
    
    def validate_line_format(self, line_id: str) -> bool:
        """Validate line ID is in correct x/y/z format with valid ranges."""
        pattern = r'^(\d+)/(\d+)/(\d+)$'
        match = re.match(pattern, line_id)
        
        if not match:
            return False
        
        x, y, z = map(int, match.groups())
        
        # Validate ranges: x:0-1, y:0-1, z:0-22
        if x in [0, 1] and y in [0, 1] and 0 <= z <= 22:
            return True
        
        return False
    
    def get_line_configuration_commands(self, console_lines: List[str], platform: str) -> List[str]:
        """Generate commands to get configuration for each console line with platform-specific formats."""
        commands = []
        platform_lower = platform.lower()
        
        for line_id in console_lines:
            if platform_lower == 'iosxr':
                # IOS XR uses different command format
                commands.append(f"show running-config line aux {line_id}")
                # Also try generic line command
                commands.append(f"show running-config | include \"line aux {line_id}\"")
            else:
                # IOS/IOS XE
                commands.append(f"show running-config | section \"line {line_id}\"")
                # Alternative command format
                commands.append(f"show running-config | include \"line {line_id}\"")
        
        return commands
    
    def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                          output_handler: OutputHandler) -> Dict[str, Any]:
        """Collect console line data for a device."""
        self.logger.info(f"Starting console line collection for {hostname} ({platform})")
        
        # Get base commands for platform
        base_commands = self.get_commands_for_platform(platform)
        
        # Create device directory structure
        run_dir = output_handler.base_output_dir / output_handler.collection_metadata.collection_id
        console_dir = output_handler.create_device_directory_structure(hostname, 'console')
        
        results = {
            'hostname': hostname,
            'platform': platform,
            'layer': 'console',
            'timestamp': datetime.now().isoformat(),
            'commands_executed': [],
            'commands_failed': [],
            'console_lines_discovered': [],
            'console_lines_configured': [],
            'total_commands': 0,
            'success_count': 0,
            'failure_count': 0,
            'show_line_output': '',
            'console_line_data': {}
        }
        
        # Phase 1: Execute base commands for line discovery
        show_line_output = ''
        for command in base_commands:
            try:
                self.logger.debug(f"Executing base command on {hostname}: {command}")
                
                command_result = self._execute_command_with_retry(connection, command, 30)
                
                if command_result['success']:
                    # Save raw output
                    output_handler.save_command_output(
                        hostname=hostname,
                        layer='console',
                        command=command,
                        output=command_result['output']
                    )
                    
                    if 'show line' in command:
                        show_line_output = command_result['output']
                        results['show_line_output'] = show_line_output
                    
                    results['commands_executed'].append({
                        'command': command,
                        'success': True,
                        'execution_time': command_result['execution_time'],
                        'output_size': len(command_result['output'])
                    })
                    results['success_count'] += 1
                    
                else:
                    results['commands_failed'].append({
                        'command': command,
                        'error': command_result['error']
                    })
                    results['failure_count'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error executing base command {command} on {hostname}: {e}")
                results['commands_failed'].append({
                    'command': command,
                    'error': str(e)
                })
                results['failure_count'] += 1
        
        # Phase 2: Parse show line output and discover console lines
        if show_line_output:
            try:
                line_info = self.parse_show_line_output(show_line_output, platform)
                console_lines = self.extract_console_lines(line_info)
                results['console_lines_discovered'] = console_lines
                
                self.logger.info(f"Discovered {len(console_lines)} console lines on {hostname}: {console_lines}")
                
                # Phase 3: Get configuration for each console line
                if console_lines:
                    line_config_commands = self.get_line_configuration_commands(console_lines, platform)
                    
                    for line_id, command in zip(console_lines, line_config_commands):
                        try:
                            self.logger.debug(f"Getting config for line {line_id} on {hostname}: {command}")
                            
                            command_result = self._execute_command_with_retry(connection, command, 20)
                            
                            if command_result['success']:
                                # Save raw output
                                output_handler.save_command_output(
                                    hostname=hostname,
                                    layer='console',
                                    command=command,
                                    output=command_result['output']
                                )
                                
                                # Store line configuration data
                                results['console_line_data'][line_id] = {
                                    'line_id': line_id,
                                    'configuration': command_result['output'],
                                    'command_used': command,
                                    'success': True
                                }
                                
                                results['console_lines_configured'].append(line_id)
                                
                                results['commands_executed'].append({
                                    'command': command,
                                    'success': True,
                                    'execution_time': command_result['execution_time'],
                                    'output_size': len(command_result['output']),
                                    'line_id': line_id
                                })
                                results['success_count'] += 1
                                
                            else:
                                self.logger.warning(f"Failed to get config for line {line_id} on {hostname}: {command_result['error']}")
                                results['console_line_data'][line_id] = {
                                    'line_id': line_id,
                                    'configuration': '',
                                    'command_used': command,
                                    'success': False,
                                    'error': command_result['error']
                                }
                                
                                results['commands_failed'].append({
                                    'command': command,
                                    'error': command_result['error'],
                                    'line_id': line_id
                                })
                                results['failure_count'] += 1
                        
                        except Exception as e:
                            self.logger.error(f"Error getting config for line {line_id} on {hostname}: {e}")
                            results['console_line_data'][line_id] = {
                                'line_id': line_id,
                                'configuration': '',
                                'command_used': command,
                                'success': False,
                                'error': str(e)
                            }
                            results['commands_failed'].append({
                                'command': command,
                                'error': str(e),
                                'line_id': line_id
                            })
                            results['failure_count'] += 1
                
            except Exception as e:
                self.logger.error(f"Error parsing show line output on {hostname}: {e}")
                results['commands_failed'].append({
                    'command': 'show line parsing',
                    'error': str(e)
                })
                results['failure_count'] += 1
        
        # Calculate totals and success rate
        results['total_commands'] = results['success_count'] + results['failure_count']
        if results['total_commands'] > 0:
            results['success_rate'] = (results['success_count'] / results['total_commands']) * 100
        else:
            results['success_rate'] = 0
        
        # Generate summary
        results['summary'] = {
            'total_lines_discovered': len(results['console_lines_discovered']),
            'total_lines_configured': len(results['console_lines_configured']),
            'configuration_success_rate': (len(results['console_lines_configured']) / max(1, len(results['console_lines_discovered']))) * 100,
            'commands_executed': results['success_count'],
            'commands_failed': results['failure_count'],
            'overall_success_rate': results['success_rate']
        }
        
        # Save structured output files
        self._save_console_line_outputs(hostname, results, console_dir)
        
        self.logger.info(f"Console line collection completed for {hostname}: "
                        f"Discovered {len(results['console_lines_discovered'])} lines, "
                        f"configured {len(results['console_lines_configured'])} lines")
        
        return results
    
    def _execute_command_with_retry(self, connection: Any, command: str, timeout: int,
                                   max_retries: int = 2) -> Dict[str, Any]:
        """Execute command with retry logic."""
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                if hasattr(connection, 'send_command'):
                    output = connection.send_command(command, read_timeout=timeout)
                    execution_time = time.time() - start_time
                    
                    return {
                        'success': True,
                        'output': output,
                        'execution_time': execution_time,
                        'attempt': attempt + 1
                    }
                else:
                    return {
                        'success': False,
                        'output': '',
                        'error': 'Connection object does not support send_command method',
                        'execution_time': 0,
                        'attempt': attempt + 1
                    }
                    
            except Exception as e:
                execution_time = time.time() - start_time
                
                if attempt < max_retries:
                    self.logger.warning(f"Command '{command}' failed on attempt {attempt + 1}, retrying...")
                    time.sleep(1)  # Brief delay before retry
                    continue
                else:
                    self.logger.error(f"Command '{command}' failed after {max_retries + 1} attempts: {e}")
                    return {
                        'success': False,
                        'output': '',
                        'error': str(e),
                        'execution_time': execution_time,
                        'attempt': attempt + 1
                    }
    
    def _save_console_line_outputs(self, hostname: str, results: Dict[str, Any], output_dir: str):
        """Save console line data in JSON and text formats."""
        try:
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # JSON output
            json_filename = f"{hostname}_console_lines.json"
            json_filepath = os.path.join(output_dir, json_filename)
            
            json_data = {
                'device': hostname,
                'timestamp': results['timestamp'],
                'platform': results['platform'],
                'show_line_output': results['show_line_output'],
                'console_lines': results['console_line_data'],
                'discovered_lines': results['console_lines_discovered'],
                'configured_lines': results['console_lines_configured'],
                'summary': results['summary']
            }
            
            with open(json_filepath, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            # Text output
            txt_filename = f"{hostname}_console_lines.txt"
            txt_filepath = os.path.join(output_dir, txt_filename)
            
            with open(txt_filepath, 'w') as f:
                f.write(f"Console Line Configuration Report\n")
                f.write(f"{'='*50}\n")
                f.write(f"Device: {hostname}\n")
                f.write(f"Platform: {results['platform']}\n")
                f.write(f"Timestamp: {results['timestamp']}\n")
                f.write(f"Total Lines Discovered: {len(results['console_lines_discovered'])}\n")
                f.write(f"Total Lines Configured: {len(results['console_lines_configured'])}\n")
                f.write(f"Success Rate: {results['summary']['overall_success_rate']:.1f}%\n\n")
                
                f.write(f"Discovered Console Lines:\n")
                f.write(f"{'-'*30}\n")
                for line_id in results['console_lines_discovered']:
                    f.write(f"  - {line_id}\n")
                f.write(f"\n")
                
                f.write(f"Show Line Output:\n")
                f.write(f"{'-'*20}\n")
                f.write(f"{results['show_line_output']}\n\n")
                
                f.write(f"Individual Line Configurations:\n")
                f.write(f"{'-'*35}\n")
                for line_id, line_data in results['console_line_data'].items():
                    f.write(f"\nLine {line_id}:\n")
                    f.write(f"Command: {line_data['command_used']}\n")
                    f.write(f"Success: {line_data['success']}\n")
                    if line_data['success']:
                        f.write(f"Configuration:\n{line_data['configuration']}\n")
                    else:
                        f.write(f"Error: {line_data.get('error', 'Unknown error')}\n")
                    f.write(f"{'-'*40}\n")
            
            self.logger.info(f"Console line outputs saved: {json_filepath}, {txt_filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving console line outputs for {hostname}: {e}")
    
    def get_console_line_summary(self, console_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for console line collection."""
        summary = {
            'device': console_data.get('hostname', 'unknown'),
            'platform': console_data.get('platform', 'unknown'),
            'collection_time': console_data.get('timestamp', ''),
            'lines_discovered': len(console_data.get('console_lines_discovered', [])),
            'lines_configured': len(console_data.get('console_lines_configured', [])),
            'total_commands': console_data.get('total_commands', 0),
            'successful_commands': console_data.get('success_count', 0),
            'failed_commands': console_data.get('failure_count', 0),
            'success_rate': console_data.get('success_rate', 0),
            'configuration_coverage': 0
        }
        
        if summary['lines_discovered'] > 0:
            summary['configuration_coverage'] = (summary['lines_configured'] / summary['lines_discovered']) * 100
        
        return summary 
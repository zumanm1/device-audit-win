#!/usr/bin/env python3
"""
Health Collector for RR4 Complete Enhanced v4 CLI

This module collects system health information including version, platform,
CPU, memory, environment, and logging data from network devices.

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from core.data_parser import DataParser
from core.output_handler import OutputHandler

@dataclass
class HealthCommands:
    """Health layer command definitions by platform."""
    
    ios_commands = [
        "show version",
        "show inventory",
        "show processes cpu history",
        "show memory summary",
        "show environment all",
        "show logging | include %",
        "show clock",
        "show users",
        "show processes memory sorted"
    ]
    
    iosxe_commands = [
        "show version",
        "show inventory",
        "show processes cpu history",
        "show memory summary",
        "show environment all",
        "show logging | include %",
        "show clock",
        "show users",
        "show processes memory sorted",
        "show platform hardware qfp active infrastructure bqs queue output default all"
    ]
    
    iosxr_commands = [
        "show version",
        "show platform",
        "show inventory",
        "show processes cpu history",
        "show memory summary detail",
        "show environment all",
        "show logging last 1000",
        "show clock",
        "show users",
        "admin show processes memory"
    ]

class HealthCollector:
    """Collect system health information from network devices."""
    
    def __init__(self):
        self.logger = logging.getLogger('rr4_collector.health_collector')
        self.data_parser = DataParser()
        self.commands = HealthCommands()
    
    def get_commands_for_platform(self, platform: str) -> List[str]:
        """Get health commands for specific platform."""
        platform_lower = platform.lower()
        
        if platform_lower == 'ios':
            return self.commands.ios_commands
        elif platform_lower == 'iosxe':
            return self.commands.iosxe_commands
        elif platform_lower == 'iosxr':
            return self.commands.iosxr_commands
        else:
            self.logger.warning(f"Unknown platform {platform}, using IOS commands")
            return self.commands.ios_commands
    
    def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                          output_handler: OutputHandler) -> Dict[str, Any]:
        """Collect health data for a device."""
        self.logger.info(f"Starting health collection for {hostname} ({platform})")
        
        # Get platform-specific commands
        commands = self.get_commands_for_platform(platform)
        
        # Create device directory structure
        run_dir = output_handler.base_output_dir / output_handler.collection_metadata.collection_id
        device_dirs = output_handler.create_device_directory_structure(run_dir, hostname)
        health_dir = device_dirs['health']
        
        results = {
            'hostname': hostname,
            'platform': platform,
            'layer': 'health',
            'commands_executed': [],
            'commands_failed': [],
            'total_commands': len(commands),
            'success_count': 0,
            'failure_count': 0
        }
        
        # Execute each command
        for command in commands:
            try:
                self.logger.debug(f"Executing command on {hostname}: {command}")
                
                # Execute command with appropriate timeout
                timeout = self._get_command_timeout(command)
                command_result = self._execute_command_with_retry(connection, command, timeout)
                
                if command_result['success']:
                    # Save raw output
                    output_result = output_handler.save_command_output(
                        output_dir=health_dir,
                        command=command,
                        output=command_result['output'],
                        hostname=hostname,
                        layer='health',
                        platform=platform
                    )
                    
                    # Parse output
                    parse_result = self.data_parser.parse_command_output(
                        command=command,
                        output=command_result['output'],
                        platform=platform
                    )
                    
                    # Save parsed output if successful
                    if parse_result.success and parse_result.parsed_data:
                        parsed_result = output_handler.save_parsed_output(
                            output_dir=health_dir,
                            command=command,
                            parsed_data=parse_result.parsed_data,
                            hostname=hostname,
                            layer='health',
                            platform=platform
                        )
                    
                    # Record success
                    results['commands_executed'].append({
                        'command': command,
                        'success': True,
                        'execution_time': command_result['execution_time'],
                        'output_size': len(command_result['output']),
                        'parsed': parse_result.success,
                        'parser_used': parse_result.parser_used
                    })
                    results['success_count'] += 1
                    
                else:
                    # Record failure
                    results['commands_failed'].append({
                        'command': command,
                        'error': command_result['error'],
                        'execution_time': command_result.get('execution_time', 0)
                    })
                    results['failure_count'] += 1
                    
                    self.logger.warning(f"Command failed on {hostname}: {command} - {command_result['error']}")
            
            except Exception as e:
                self.logger.error(f"Unexpected error executing {command} on {hostname}: {e}")
                results['commands_failed'].append({
                    'command': command,
                    'error': str(e),
                    'execution_time': 0
                })
                results['failure_count'] += 1
        
        # Calculate success rate
        results['success_rate'] = (results['success_count'] / results['total_commands']) * 100
        
        self.logger.info(f"Health collection completed for {hostname}: "
                        f"{results['success_count']}/{results['total_commands']} commands successful")
        
        return results
    
    def _execute_command_with_retry(self, connection: Any, command: str, timeout: int,
                                   max_retries: int = 2) -> Dict[str, Any]:
        """Execute command with retry logic."""
        from ..core.connection_manager import ConnectionManager
        
        for attempt in range(max_retries + 1):
            try:
                # Use connection manager's execute_command method
                if hasattr(connection, 'send_command'):
                    output = connection.send_command(command, read_timeout=timeout)
                    return {
                        'success': True,
                        'output': output,
                        'execution_time': 0,  # Approximate
                        'attempt': attempt + 1
                    }
                else:
                    # Fallback for different connection types
                    output = str(connection.execute_command(command, timeout))
                    return {
                        'success': True,
                        'output': output,
                        'execution_time': 0,
                        'attempt': attempt + 1
                    }
                    
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"Command attempt {attempt + 1} failed, retrying: {command}")
                    continue
                else:
                    return {
                        'success': False,
                        'error': str(e),
                        'execution_time': 0,
                        'attempt': attempt + 1
                    }
    
    def _get_command_timeout(self, command: str) -> int:
        """Get appropriate timeout for command."""
        # Commands that might take longer
        long_commands = [
            'show processes memory sorted',
            'show logging',
            'show environment all'
        ]
        
        for long_cmd in long_commands:
            if long_cmd in command.lower():
                return 120  # 2 minutes
        
        return 60  # Default 1 minute
    
    def validate_health_status(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate device health status based on collected data."""
        validation_results = {
            'overall_health': 'unknown',
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # Check command execution success rate
            success_rate = health_data.get('success_rate', 0)
            if success_rate < 80:
                validation_results['issues'].append(f"Low command success rate: {success_rate:.1f}%")
            elif success_rate < 95:
                validation_results['warnings'].append(f"Moderate command success rate: {success_rate:.1f}%")
            
            # Analyze specific command outputs
            for cmd_result in health_data.get('commands_executed', []):
                command = cmd_result['command']
                
                # Check for specific health indicators
                if 'show version' in command and cmd_result.get('parsed'):
                    # Could add version-specific checks here
                    pass
                
                if 'show processes cpu' in command:
                    # Could add CPU utilization checks here
                    pass
                
                if 'show memory' in command:
                    # Could add memory utilization checks here
                    pass
            
            # Determine overall health
            if not validation_results['issues']:
                if not validation_results['warnings']:
                    validation_results['overall_health'] = 'healthy'
                else:
                    validation_results['overall_health'] = 'warning'
            else:
                validation_results['overall_health'] = 'critical'
        
        except Exception as e:
            self.logger.error(f"Error validating health status: {e}")
            validation_results['issues'].append(f"Health validation error: {e}")
            validation_results['overall_health'] = 'unknown'
        
        return validation_results
    
    def get_health_summary(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health summary from collected data."""
        summary = {
            'hostname': health_data.get('hostname'),
            'platform': health_data.get('platform'),
            'collection_timestamp': health_data.get('collection_timestamp'),
            'command_statistics': {
                'total_commands': health_data.get('total_commands', 0),
                'successful_commands': health_data.get('success_count', 0),
                'failed_commands': health_data.get('failure_count', 0),
                'success_rate': health_data.get('success_rate', 0)
            },
            'health_validation': self.validate_health_status(health_data)
        }
        
        return summary 
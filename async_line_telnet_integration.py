#!/usr/bin/env python3
"""
Async Line Telnet Integration for NetAuditPro
==============================================

PRIMARY PURPOSE: Detect telnet enablement on async ports and report devices with telnet

Main Mission:
- Audit ONLY async ports for telnet enablement
- Report if devices have telnet-enabled async lines
- Support Cisco IOS and IOS XE router types
- Detect various telnet patterns and implicit telnet allowance

This module integrates with NetAuditPro to add focused telnet detection on:
- Slot 0 / PA 1 / channels 0-22 ("line 0/1/*")
- Slot 1 / PA 0 / channels 0-22 ("line 1/0/*")

All features support the primary objective of telnet detection and reporting.
"""

import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AsyncTelnetConfig:
    """Data structure focused on telnet detection on async lines."""
    line_id: str
    slot: int
    pa: int
    channel: int
    
    # Telnet detection (PRIMARY FOCUS)
    telnet_enabled: bool = False
    telnet_detection_method: str = "none"
    telnet_explicit: bool = False
    telnet_implicit: bool = False
    telnet_risk_level: str = "UNKNOWN"
    
    # Supporting configuration data
    login_method: str = "none"
    transport_input: List[str] = None
    transport_preferred: str = "none"
    access_class: str = "none"
    exec_enabled: bool = True
    rotary: str = "none"
    raw_config: List[str] = None

    def __post_init__(self):
        if self.transport_input is None:
            self.transport_input = []
        if self.raw_config is None:
            self.raw_config = []
        self._detect_telnet()

    def _detect_telnet(self):
        """Primary telnet detection logic."""
        self.telnet_enabled = False
        self.telnet_explicit = False
        self.telnet_implicit = False
        self.telnet_detection_method = "none"
        
        # Explicit telnet patterns
        if "telnet" in self.transport_input:
            self.telnet_enabled = True
            self.telnet_explicit = True
            self.telnet_detection_method = "transport_input_telnet"
        elif "all" in self.transport_input:
            self.telnet_enabled = True
            self.telnet_explicit = True
            self.telnet_detection_method = "transport_input_all"
        elif self.transport_preferred == "telnet":
            self.telnet_enabled = True
            self.telnet_explicit = True
            self.telnet_detection_method = "transport_preferred_telnet"
        
        # Implicit telnet (no SSH specified, default allows telnet)
        elif (not self._ssh_enabled() and 
              self.transport_input != ["none"] and 
              len(self.transport_input) == 0):
            self.telnet_enabled = True
            self.telnet_implicit = True
            self.telnet_detection_method = "implicit_default"
        
        # Set risk level
        if self.telnet_enabled:
            if self.login_method == "none":
                self.telnet_risk_level = "CRITICAL"
            elif self.access_class == "none":
                self.telnet_risk_level = "HIGH"
            else:
                self.telnet_risk_level = "MEDIUM"
        else:
            self.telnet_risk_level = "LOW"

    def _ssh_enabled(self) -> bool:
        """Check if SSH is enabled."""
        return "ssh" in self.transport_input

    @property
    def is_console_server(self) -> bool:
        """Check if this is a console server port."""
        return not self.exec_enabled and self.rotary != "none"

    @property
    def telnet_status(self) -> str:
        """Get telnet status for reporting."""
        if not self.telnet_enabled:
            return "NO_TELNET"
        
        status_map = {
            "transport_input_telnet": "EXPLICIT_TELNET",
            "transport_input_all": "EXPLICIT_ALL", 
            "transport_preferred_telnet": "PREFERRED_TELNET",
            "implicit_default": "IMPLICIT_TELNET"
        }
        
        return status_map.get(self.telnet_detection_method, "UNKNOWN_TELNET")


class RouterTypeDetector:
    """Detects router type for appropriate command selection."""
    
    @staticmethod
    def detect_from_output(output: str) -> Dict[str, str]:
        """Detect router type from show version or other output."""
        router_info = {
            'type': 'UNKNOWN',
            'version': 'UNKNOWN',
            'platform': 'UNKNOWN'
        }
        
        output_lower = output.lower()
        
        # Detect IOS XE
        if 'ios xe' in output_lower or 'iosxe' in output_lower:
            router_info['type'] = 'IOS_XE'
        # Detect Classic IOS
        elif 'cisco ios' in output_lower or 'internetwork operating system' in output_lower:
            router_info['type'] = 'IOS'
        
        # Extract version
        version_match = re.search(r'version\s+(\S+)', output_lower)
        if version_match:
            router_info['version'] = version_match.group(1)
        
        # Extract platform
        platform_patterns = [r'cisco (\w+)', r'(\d+) series', r'catalyst (\w+)']
        for pattern in platform_patterns:
            match = re.search(pattern, output_lower)
            if match:
                router_info['platform'] = match.group(1).upper()
                break
        
        return router_info


class AsyncTelnetCollector:
    """Collects async line configurations focused on telnet detection."""
    
    def __init__(self, sanitize_func=None):
        self.sanitize_func = sanitize_func or (lambda x: x)
        
    def get_telnet_audit_commands(self) -> List[str]:
        """Get commands needed for telnet auditing."""
        return [
            "show version",  # For router type detection
            "show running-config | section ^line 0/1/",  # Slot 0, PA 1
            "show running-config | section ^line 1/0/",  # Slot 1, PA 0
            "show run | include ^line [01]/[01]/"  # Quick verification
        ]
    
    def extract_async_telnet_data(self, command_outputs: Dict[str, str]) -> Dict[str, Any]:
        """Extract telnet-focused data from command outputs."""
        result = {
            'router_info': {},
            'telnet_analysis': {},
            'async_lines': {},
            'main_finding': 'NO_TELNET_DETECTED'
        }
        
        # Router type detection
        if 'show version' in command_outputs:
            result['router_info'] = RouterTypeDetector.detect_from_output(
                command_outputs['show version']
            )
        
        # Extract async line sections
        sections = {}
        if 'show running-config | section ^line 0/1/' in command_outputs:
            sections['0_1_lines'] = command_outputs['show running-config | section ^line 0/1/']
        if 'show running-config | section ^line 1/0/' in command_outputs:
            sections['1_0_lines'] = command_outputs['show running-config | section ^line 1/0/']
        
        # Parse for telnet detection
        telnet_lines = {}
        telnet_count = 0
        
        for section_name, section_data in sections.items():
            parsed_lines = self._parse_section_for_telnet(section_data)
            telnet_lines[section_name] = parsed_lines
            telnet_count += sum(1 for line in parsed_lines.values() if line.telnet_enabled)
        
        result['async_lines'] = telnet_lines
        result['telnet_analysis'] = self._analyze_telnet_findings(telnet_lines)
        
        # Set main finding
        if telnet_count > 0:
            result['main_finding'] = f'TELNET_DETECTED_ON_{telnet_count}_LINES'
        
        return result
    
    def _parse_section_for_telnet(self, section_text: str) -> Dict[str, AsyncTelnetConfig]:
        """Parse section output focusing on telnet detection."""
        lines = {}
        
        if not section_text.strip():
            return lines
        
        # Split by line blocks
        blocks = re.split(r'\n!\n', self.sanitize_func(section_text))
        
        for block in blocks:
            # Find line configuration
            line_match = re.search(r'^line (\d+/\d+/\d+)', block, re.MULTILINE)
            if not line_match:
                continue
                
            line_id = line_match.group(1)
            parts = line_id.split('/')
            
            if len(parts) != 3:
                continue
                
            try:
                slot, pa, channel = int(parts[0]), int(parts[1]), int(parts[2])
            except ValueError:
                continue
                
            # Create telnet-focused config
            config = AsyncTelnetConfig(
                line_id=line_id,
                slot=slot,
                pa=pa,
                channel=channel,
                raw_config=self.sanitize_func(block.strip()).split('\n')
            )
            
            # Parse for telnet detection
            for line in block.split('\n'):
                line = line.strip()
                
                # TELNET DETECTION (PRIMARY FOCUS)
                if line.startswith('transport input'):
                    config.transport_input = line.split()[2:]
                elif line.startswith('transport preferred'):
                    if len(line.split()) > 2:
                        config.transport_preferred = line.split()[2]
                elif line.startswith('transport telnet preferred'):
                    config.transport_preferred = "telnet"
                
                # Supporting data
                elif line.startswith('login authentication'):
                    config.login_method = line.split()[-1]
                elif line == 'login local':
                    config.login_method = 'local'
                elif line == 'login':
                    config.login_method = 'password'
                elif line == 'no login':
                    config.login_method = 'none'
                elif line == 'no exec':
                    config.exec_enabled = False
                elif line.startswith('access-class'):
                    if len(line.split()) >= 2:
                        config.access_class = line.split()[1]
                elif line.startswith('rotary'):
                    config.rotary = line.split()[-1]
                    
            lines[line_id] = config
            
        return lines
    
    def _analyze_telnet_findings(self, telnet_lines: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze telnet findings across all lines."""
        analysis = {
            'total_lines': 0,
            'telnet_enabled_count': 0,
            'telnet_disabled_count': 0,
            'risk_breakdown': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'detection_methods': {},
            'telnet_enabled_lines': [],
            'device_has_telnet': False
        }
        
        # Count all lines
        all_lines = {}
        for section_lines in telnet_lines.values():
            all_lines.update(section_lines)
        
        analysis['total_lines'] = len(all_lines)
        
        # Analyze each line
        for line_id, config in all_lines.items():
            if config.telnet_enabled:
                analysis['telnet_enabled_count'] += 1
                analysis['telnet_enabled_lines'].append({
                    'line_id': line_id,
                    'detection_method': config.telnet_detection_method,
                    'risk_level': config.telnet_risk_level,
                    'status': config.telnet_status
                })
                
                # Count detection methods
                method = config.telnet_detection_method
                analysis['detection_methods'][method] = analysis['detection_methods'].get(method, 0) + 1
            else:
                analysis['telnet_disabled_count'] += 1
            
            # Count risk levels
            analysis['risk_breakdown'][config.telnet_risk_level] += 1
        
        analysis['device_has_telnet'] = analysis['telnet_enabled_count'] > 0
        
        return analysis


class AsyncTelnetAuditor:
    """Main auditor for telnet detection on async lines - NetAuditPro integration."""
    
    def __init__(self, sanitize_func=None, log_func=None):
        self.sanitize_func = sanitize_func or (lambda x: x)
        self.log_func = log_func or print
        self.collector = AsyncTelnetCollector(sanitize_func)
        
    def audit_device_for_telnet(self, device_name: str, net_connect) -> Dict[str, Any]:
        """
        MAIN AUDIT FUNCTION - Audit device for telnet on async lines.
        
        Primary Purpose: Detect if this device has telnet enabled on async ports.
        """
        self.log_func(f"🎯 Auditing {device_name} for telnet on async lines")
        
        try:
            # Get required commands
            commands = self.collector.get_telnet_audit_commands()
            command_outputs = {}
            
            # Execute commands
            for cmd in commands:
                self.log_func(f"  📡 Executing: {cmd}")
                try:
                    output = net_connect.send_command(cmd, delay_factor=2)
                    command_outputs[cmd] = self.sanitize_func(output)
                except Exception as cmd_error:
                    self.log_func(f"  ⚠️ Command failed: {cmd} - {str(cmd_error)}")
                    command_outputs[cmd] = ""
            
            # Extract telnet data
            self.log_func(f"  🔍 Analyzing for telnet enablement...")
            telnet_data = self.collector.extract_async_telnet_data(command_outputs)
            
            # Generate results
            result = {
                'timestamp': datetime.now().isoformat(),
                'device_name': device_name,
                'main_purpose': 'DETECT_TELNET_ON_ASYNC_PORTS',
                'router_info': telnet_data['router_info'],
                'main_finding': telnet_data['main_finding'],
                'telnet_analysis': telnet_data['telnet_analysis'],
                'device_has_telnet': telnet_data['telnet_analysis']['device_has_telnet'],
                'recommendations': self._generate_telnet_recommendations(telnet_data),
                'raw_data': telnet_data['async_lines']  # Supporting data
            }
            
            # Log main finding
            if result['device_has_telnet']:
                telnet_count = result['telnet_analysis']['telnet_enabled_count']
                self.log_func(f"  🚨 TELNET DETECTED: {telnet_count} async lines have telnet enabled")
            else:
                self.log_func(f"  ✅ NO TELNET: Device has secure async line configuration")
            
            return result
            
        except Exception as e:
            error_msg = f"Telnet audit failed for {device_name}: {str(e)}"
            self.log_func(f"  ❌ {error_msg}")
            return {
                'device_name': device_name,
                'error': self.sanitize_func(error_msg),
                'device_has_telnet': None
            }
    
    def _generate_telnet_recommendations(self, telnet_data: Dict) -> List[str]:
        """Generate telnet-focused recommendations."""
        recommendations = []
        analysis = telnet_data['telnet_analysis']
        
        if analysis['device_has_telnet']:
            count = analysis['telnet_enabled_count']
            recommendations.append(f"🔴 URGENT: Disable telnet on {count} async lines")
            
            # Risk-specific recommendations
            critical = analysis['risk_breakdown']['CRITICAL']
            if critical > 0:
                recommendations.append(f"🚨 CRITICAL: Add authentication to {critical} telnet lines")
            
            high = analysis['risk_breakdown']['HIGH']
            if high > 0:
                recommendations.append(f"⚠️ HIGH: Add ACLs to {high} telnet lines")
        else:
            recommendations.append("✅ SECURE: No telnet on async lines - maintain this configuration")
        
        return recommendations


# Integration functions for NetAuditPro

def collect_async_telnet_data(net_connect, device_name: str, sanitize_func=None, log_func=None) -> Dict[str, Any]:
    """Main integration function - collect telnet data for async lines."""
    auditor = AsyncTelnetAuditor(sanitize_func, log_func)
    return auditor.audit_device_for_telnet(device_name, net_connect)


def format_telnet_summary(telnet_data: Dict[str, Any]) -> str:
    """Format telnet findings for NetAuditPro reports."""
    if 'error' in telnet_data:
        return f"Async Telnet Audit Error: {telnet_data['error']}"
    
    if telnet_data.get('device_has_telnet') is None:
        return "Async Telnet Audit: Unable to determine telnet status"
    
    device_name = telnet_data.get('device_name', 'Unknown')
    
    if telnet_data['device_has_telnet']:
        count = telnet_data['telnet_analysis']['telnet_enabled_count']
        return f"🚨 TELNET DETECTED: {device_name} has {count} async lines with telnet enabled"
    else:
        return f"✅ SECURE: {device_name} has no telnet on async lines"


def get_telnet_audit_commands() -> List[str]:
    """Get the commands needed for telnet auditing."""
    collector = AsyncTelnetCollector()
    return collector.get_telnet_audit_commands()


def is_device_telnet_compliant(telnet_data: Dict[str, Any]) -> bool:
    """Check if device is compliant (no telnet on async lines)."""
    return not telnet_data.get('device_has_telnet', True)


if __name__ == "__main__":
    print("🎯 Async Line Telnet Integration for NetAuditPro")
    print("Primary Purpose: Detect telnet enablement on async ports")
    print("Target: Slot 0/PA 1 and Slot 1/PA 0, channels 0-22")
    print("Focus: Report devices with telnet-enabled async lines") 
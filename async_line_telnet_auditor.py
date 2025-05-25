#!/usr/bin/env python3
"""
Async Line Telnet Auditor - Main Purpose: Detect Telnet on Async Ports
=====================================================================

PRIMARY OBJECTIVE: Audit async TTY lines to identify telnet enablement

Main Focus:
- Detect telnet on async lines (slot 0/PA 1 and slot 1/PA 0, channels 0-22)
- Report devices with telnet-enabled async ports
- Check for various telnet patterns in Cisco IOS/IOS XE

Telnet Detection Patterns:
- "transport input telnet"
- "transport telnet preferred" 
- "transport input all" (includes telnet)
- Missing SSH specification (implicit telnet allowed)
- Default transport settings

Router Type Support:
- Cisco IOS
- Cisco IOS XE
- Automatic detection and appropriate command usage

All other features support this main telnet detection functionality.
"""

import re
import sys
import json
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AsyncLineConfig:
    """Data structure for async line configuration - focused on telnet detection."""
    line_id: str
    slot: int
    pa: int
    channel: int
    login_method: str = "none"
    exec_enabled: bool = True
    timeout: str = "none"
    transport_input: List[str] = None
    transport_preferred: str = "none"
    access_class: str = "none"
    rotary: str = "none"
    speed: str = "none"
    flowcontrol: str = "none"
    autocommand: str = "none"
    privilege_level: str = "none"
    escape_char: str = "none"
    raw_config: List[str] = None
    
    # Telnet-specific analysis
    telnet_explicitly_enabled: bool = False
    telnet_implicitly_enabled: bool = False
    telnet_risk_level: str = "UNKNOWN"
    telnet_detection_method: str = "none"

    def __post_init__(self):
        if self.transport_input is None:
            self.transport_input = []
        if self.raw_config is None:
            self.raw_config = []
        self._analyze_telnet_configuration()

    def _analyze_telnet_configuration(self):
        """Comprehensive telnet detection analysis."""
        # Reset telnet flags
        self.telnet_explicitly_enabled = False
        self.telnet_implicitly_enabled = False
        self.telnet_detection_method = "none"
        
        # Explicit telnet enablement patterns
        if "telnet" in self.transport_input:
            self.telnet_explicitly_enabled = True
            if "ssh" in self.transport_input:
                self.telnet_detection_method = "transport_input_ssh_telnet"
            else:
                self.telnet_detection_method = "transport_input_telnet"
        elif "all" in self.transport_input:
            self.telnet_explicitly_enabled = True
            self.telnet_detection_method = "transport_input_all"
        elif self.transport_preferred == "telnet":
            self.telnet_explicitly_enabled = True
            self.telnet_detection_method = "transport_preferred_telnet"
        
        # Check for explicit disabling
        elif "none" in self.transport_input:
            # Explicitly disabled - no telnet
            self.telnet_detection_method = "transport_input_none"
        elif "ssh" in self.transport_input and "telnet" not in self.transport_input:
            # SSH-only configuration - no telnet
            self.telnet_detection_method = "transport_input_ssh_only"
        
        # Implicit telnet enablement (no transport input command at all)
        elif len(self.transport_input) == 0:
            # No transport input specified - may default to allow telnet
            self.telnet_implicitly_enabled = True
            self.telnet_detection_method = "implicit_default"
        
        # Set risk level based on telnet status and authentication
        if self.telnet_enabled:
            if self.login_method == "none":
                self.telnet_risk_level = "CRITICAL"
            elif self.access_class == "none":
                self.telnet_risk_level = "HIGH"
            else:
                self.telnet_risk_level = "MEDIUM"
        else:
            self.telnet_risk_level = "LOW"

    @property
    def telnet_enabled(self) -> bool:
        """Main telnet detection property - PRIMARY AUDIT FOCUS."""
        return self.telnet_explicitly_enabled or self.telnet_implicitly_enabled

    @property
    def ssh_enabled(self) -> bool:
        """Check if SSH is enabled in transport input."""
        return "ssh" in self.transport_input

    @property
    def is_console_server_port(self) -> bool:
        """Determine if this is a console server port (no exec + rotary)."""
        return not self.exec_enabled and self.rotary != "none"

    @property
    def telnet_status_summary(self) -> str:
        """Get telnet-focused status summary - MAIN REPORTING OUTPUT."""
        if not self.telnet_enabled:
            return "❌ NO TELNET"
        
        risk_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠", 
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        
        detection_info = {
            "transport_input_telnet": "explicit 'transport input telnet'",
            "transport_input_ssh_telnet": "explicit 'transport input ssh telnet'",
            "transport_input_all": "explicit 'transport input all'", 
            "transport_preferred_telnet": "explicit 'transport preferred telnet'",
            "implicit_default": "implicit (no transport input specified)"
        }
        
        risk_icon = risk_emoji.get(self.telnet_risk_level, "❓")
        detection_desc = detection_info.get(self.telnet_detection_method, "unknown method")
        
        return f"{risk_icon} TELNET ENABLED ({detection_desc}) - Risk: {self.telnet_risk_level}"


class RouterTypeDetector:
    """Detects Cisco router type (IOS vs IOS XE) for appropriate command usage."""
    
    @staticmethod
    def detect_router_type(show_version_output: str) -> Dict[str, str]:
        """Detect router type from show version output."""
        router_info = {
            'type': 'UNKNOWN',
            'version': 'UNKNOWN',
            'platform': 'UNKNOWN',
            'commands_supported': []
        }
        
        version_lower = show_version_output.lower()
        
        # Detect IOS XE
        if 'ios xe' in version_lower or 'iosxe' in version_lower:
            router_info['type'] = 'IOS_XE'
            router_info['commands_supported'] = [
                'show running-config | section ^line',
                'show run | include ^line'
            ]
        
        # Detect Classic IOS
        elif 'cisco ios software' in version_lower or 'internetwork operating system software' in version_lower:
            router_info['type'] = 'IOS'
            router_info['commands_supported'] = [
                'show running-config | section ^line',
                'show run | include ^line'
            ]
        
        # Extract version info
        version_match = re.search(r'version\s+(\S+)', version_lower)
        if version_match:
            router_info['version'] = version_match.group(1)
        
        # Extract platform info
        if 'cisco' in version_lower:
            platform_patterns = [
                r'cisco (\w+)',
                r'(\d+) series',
                r'catalyst (\w+)'
            ]
            for pattern in platform_patterns:
                match = re.search(pattern, version_lower)
                if match:
                    router_info['platform'] = match.group(1).upper()
                    break
        
        return router_info


class AsyncLineTelnetAuditor:
    """
    MAIN CLASS - Primary Purpose: Detect Telnet on Async Lines
    
    Core Mission: Identify devices with telnet-enabled async ports and report them.
    """
    
    def __init__(self):
        self.lines_0_1 = {}  # Slot 0, PA 1 lines
        self.lines_1_0 = {}  # Slot 1, PA 0 lines
        self.router_info = {}
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'main_purpose': 'DETECT TELNET ON ASYNC PORTS',
            'router_info': {},
            'telnet_summary': {},
            'telnet_enabled_devices': [],
            'detailed_telnet_analysis': [],
            'compliance_issues': [],
            'recommendations': [],
            'support_data': {}  # All other data supports main purpose
        }

    def parse_line_config_for_telnet(self, config_text: str, target_pattern: str) -> Dict[str, AsyncLineConfig]:
        """Parse async line configurations with FOCUS ON TELNET DETECTION."""
        lines = {}
        
        # Split by line blocks (separated by !)
        blocks = re.split(r'\n!\n', config_text)
        
        for block in blocks:
            # Look for line configuration blocks matching our pattern
            line_match = re.search(rf'^line ({target_pattern})', block, re.MULTILINE)
            if not line_match:
                continue
                
            line_id = line_match.group(1)
            
            # Parse slot/PA/channel from line ID
            parts = line_id.split('/')
            if len(parts) != 3:
                continue
                
            try:
                slot = int(parts[0])
                pa = int(parts[1]) 
                channel = int(parts[2])
            except ValueError:
                continue
                
            # Create async line config object
            config = AsyncLineConfig(
                line_id=line_id,
                slot=slot,
                pa=pa,
                channel=channel,
                raw_config=block.strip().split('\n')
            )
            
            # Parse configuration lines with ENHANCED TELNET DETECTION
            for line in block.split('\n'):
                line = line.strip()
                
                # TELNET DETECTION - PRIMARY FOCUS
                if line.startswith('transport input'):
                    transport_methods = line.split()[2:]
                    config.transport_input = transport_methods
                elif line.startswith('transport preferred'):
                    if len(line.split()) > 2:
                        config.transport_preferred = line.split()[2]
                elif line.startswith('transport telnet preferred'):
                    config.transport_preferred = "telnet"
                
                # Supporting configuration parsing
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
                elif line.startswith('exec-timeout'):
                    config.timeout = ' '.join(line.split()[1:])
                elif line.startswith('access-class'):
                    parts = line.split()
                    if len(parts) >= 2:
                        config.access_class = parts[1]
                elif line.startswith('rotary'):
                    config.rotary = line.split()[-1]
                elif line.startswith('speed'):
                    config.speed = line.split()[-1]
                elif line.startswith('flowcontrol'):
                    config.flowcontrol = ' '.join(line.split()[1:])
                elif line.startswith('autocommand'):
                    config.autocommand = ' '.join(line.split()[1:])
                elif line.startswith('privilege level'):
                    config.privilege_level = line.split()[-1]
                elif line.startswith('escape-character'):
                    config.escape_char = line.split()[-1]
                    
            lines[line_id] = config
            
        return lines

    def simulate_cisco_commands_with_router_detection(self, config_file: str = "dummy-router-configs") -> Dict[str, str]:
        """Simulate Cisco commands with router type detection."""
        try:
            with open(config_file, 'r') as f:
                full_config = f.read()
        except FileNotFoundError:
            print(f"Config file {config_file} not found!")
            return {}
            
        results = {}
        
        # Simulate router type detection
        self.router_info = RouterTypeDetector.detect_router_type(full_config)
        results['router_info'] = self.router_info
        
        # Main telnet detection commands
        section_0_1 = self._extract_section(full_config, r'^line 0/1/')
        results['section_0_1'] = section_0_1
        
        section_1_0 = self._extract_section(full_config, r'^line 1/0/')
        results['section_1_0'] = section_1_0
        
        # Quick verification command
        include_lines = self._extract_line_headers(full_config)
        results['include_lines'] = include_lines
        
        return results

    def _extract_section(self, config: str, pattern: str) -> str:
        """Extract sections matching the pattern (simulates IOS section command)."""
        lines = config.split('\n')
        result_lines = []
        in_section = False
        
        for line in lines:
            if re.match(pattern, line):
                in_section = True
                result_lines.append(line)
            elif in_section:
                if line.strip() == '!' or line.startswith('line '):
                    result_lines.append('!')
                    in_section = False
                    if line.startswith('line ') and not re.match(pattern, line):
                        continue
                else:
                    result_lines.append(line)
        
        return '\n'.join(result_lines)

    def _extract_line_headers(self, config: str) -> str:
        """Extract just the line headers for verification."""
        lines = config.split('\n')
        result_lines = []
        
        pattern = r'^line [01]/[01]/\d+$'
        
        for line in lines:
            if re.match(pattern, line.strip()):
                result_lines.append(line.strip())
                
        return '\n'.join(result_lines)

    def audit_async_lines_for_telnet(self, config_file: str = "dummy-router-configs") -> Dict[str, Any]:
        """
        MAIN AUDIT FUNCTION - Primary Purpose: Detect Telnet on Async Lines
        """
        print("🎯 ASYNC LINE TELNET AUDITOR - PRIMARY MISSION: DETECT TELNET")
        print("=" * 70)
        print("📋 Main Purpose: Audit async ports for telnet enablement")
        print("🔍 Target: Slot 0/PA 1 and Slot 1/PA 0, channels 0-22")
        print()
        
        # Router detection and command simulation
        print("🖥️  Detecting router type and simulating commands...")
        command_results = self.simulate_cisco_commands_with_router_detection(config_file)
        
        if not command_results:
            return self.audit_results
            
        self.audit_results['router_info'] = command_results['router_info']
        
        # Parse configurations with telnet focus
        print("🔧 Parsing async line configurations (TELNET FOCUS)...")
        self.lines_0_1 = self.parse_line_config_for_telnet(command_results['section_0_1'], r'0/1/\d+')
        self.lines_1_0 = self.parse_line_config_for_telnet(command_results['section_1_0'], r'1/0/\d+')
        
        # MAIN ANALYSIS - TELNET DETECTION
        self._analyze_telnet_enablement()
        self._generate_telnet_summary()
        self._check_compliance_for_telnet()
        self._generate_telnet_recommendations()
        
        return self.audit_results

    def _analyze_telnet_enablement(self):
        """CORE FUNCTION - Analyze telnet enablement across all async lines."""
        print("🌐 ANALYZING TELNET ENABLEMENT (PRIMARY OBJECTIVE)...")
        
        telnet_devices = []
        detailed_analysis = []
        
        # Analyze all lines for telnet
        all_lines = {**self.lines_0_1, **self.lines_1_0}
        
        for line_id, config in all_lines.items():
            if config.telnet_enabled:
                # Add to telnet-enabled devices list
                telnet_info = {
                    'line_id': line_id,
                    'slot_pa': f"{config.slot}/{config.pa}",
                    'channel': config.channel,
                    'telnet_detection_method': config.telnet_detection_method,
                    'telnet_explicitly_enabled': config.telnet_explicitly_enabled,
                    'telnet_implicitly_enabled': config.telnet_implicitly_enabled,
                    'risk_level': config.telnet_risk_level,
                    'transport_input': config.transport_input,
                    'login_method': config.login_method,
                    'access_class': config.access_class,
                    'is_console_server': config.is_console_server_port,
                    'status_summary': config.telnet_status_summary
                }
                telnet_devices.append(telnet_info)
                
            # Detailed analysis for all lines (supporting data)
            detailed_analysis.append({
                'line_id': line_id,
                'telnet_enabled': config.telnet_enabled,
                'telnet_status': config.telnet_status_summary,
                'detection_method': config.telnet_detection_method,
                'risk_level': config.telnet_risk_level
            })
        
        self.audit_results['telnet_enabled_devices'] = telnet_devices
        self.audit_results['detailed_telnet_analysis'] = detailed_analysis

    def _generate_telnet_summary(self):
        """Generate summary focused on telnet detection results."""
        total_0_1 = len(self.lines_0_1)
        total_1_0 = len(self.lines_1_0)
        total_lines = total_0_1 + total_1_0
        
        telnet_enabled_count = len(self.audit_results['telnet_enabled_devices'])
        
        # Count by risk level
        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        explicit_telnet = 0
        implicit_telnet = 0
        
        for device in self.audit_results['telnet_enabled_devices']:
            risk_counts[device['risk_level']] += 1
            if device['telnet_explicitly_enabled']:
                explicit_telnet += 1
            if device['telnet_implicitly_enabled']:
                implicit_telnet += 1
        
        self.audit_results['telnet_summary'] = {
            'main_finding': f"TELNET ENABLED ON {telnet_enabled_count} ASYNC LINES",
            'total_async_lines': total_lines,
            'slot_0_pa_1_lines': total_0_1,
            'slot_1_pa_0_lines': total_1_0,
            'telnet_enabled_count': telnet_enabled_count,
            'telnet_disabled_count': total_lines - telnet_enabled_count,
            'explicit_telnet_count': explicit_telnet,
            'implicit_telnet_count': implicit_telnet,
            'risk_breakdown': risk_counts,
            'device_has_telnet': telnet_enabled_count > 0,
            'audit_status': 'TELNET_FOUND' if telnet_enabled_count > 0 else 'NO_TELNET'
        }

    def _check_compliance_for_telnet(self):
        """Check compliance issues specifically related to telnet."""
        issues = []
        
        # Primary compliance check: Any telnet enabled?
        telnet_count = self.audit_results['telnet_summary']['telnet_enabled_count']
        if telnet_count > 0:
            issues.append(f"TELNET POLICY VIOLATION: {telnet_count} async lines have telnet enabled")
        
        # Check for critical risk telnet lines
        critical_count = self.audit_results['telnet_summary']['risk_breakdown']['CRITICAL']
        if critical_count > 0:
            issues.append(f"CRITICAL SECURITY RISK: {critical_count} telnet lines have no authentication")
        
        # Check for implicit telnet enablement
        implicit_count = self.audit_results['telnet_summary']['implicit_telnet_count']
        if implicit_count > 0:
            issues.append(f"IMPLICIT TELNET RISK: {implicit_count} lines may allow telnet by default")
        
        # Supporting compliance checks
        expected_channels = set(range(23))  # 0-22
        
        for slot_pa, lines_dict in [("0/1", self.lines_0_1), ("1/0", self.lines_1_0)]:
            found_channels = set(config.channel for config in lines_dict.values())
            missing = expected_channels - found_channels
            if missing:
                issues.append(f"Missing channels in {slot_pa}/*: {sorted(missing)}")
        
        self.audit_results['compliance_issues'] = issues

    def _generate_telnet_recommendations(self):
        """Generate recommendations focused on telnet security."""
        recommendations = []
        
        telnet_count = self.audit_results['telnet_summary']['telnet_enabled_count']
        
        if telnet_count > 0:
            recommendations.append(
                f"🔴 URGENT: Disable telnet on {telnet_count} async lines or implement SSH-only transport"
            )
        
        critical_count = self.audit_results['telnet_summary']['risk_breakdown']['CRITICAL']
        if critical_count > 0:
            recommendations.append(
                f"🚨 IMMEDIATE ACTION: Add authentication to {critical_count} telnet lines with no login"
            )
        
        high_count = self.audit_results['telnet_summary']['risk_breakdown']['HIGH']
        if high_count > 0:
            recommendations.append(
                f"⚠️ HIGH PRIORITY: Add access-class ACLs to {high_count} telnet lines"
            )
        
        implicit_count = self.audit_results['telnet_summary']['implicit_telnet_count']
        if implicit_count > 0:
            recommendations.append(
                f"🔍 REVIEW: Verify {implicit_count} lines with implicit telnet - add 'transport input ssh' if needed"
            )
        
        if telnet_count == 0:
            recommendations.append("✅ EXCELLENT: No telnet enabled on async lines - secure configuration")
        
        self.audit_results['recommendations'] = recommendations

    def print_telnet_focused_report(self):
        """Print report FOCUSED ON TELNET DETECTION - Main Purpose."""
        print("\n" + "=" * 80)
        print("📋 ASYNC LINE TELNET AUDIT REPORT")
        print("🎯 PRIMARY PURPOSE: DETECT TELNET ON ASYNC PORTS")
        print("=" * 80)
        
        # Router information
        router_info = self.audit_results['router_info']
        print(f"🖥️  Router Type: {router_info.get('type', 'UNKNOWN')}")
        print(f"📟 Platform: {router_info.get('platform', 'UNKNOWN')}")
        print(f"💾 Version: {router_info.get('version', 'UNKNOWN')}")
        print()
        
        # MAIN TELNET SUMMARY
        summary = self.audit_results['telnet_summary']
        print(f"🎯 MAIN FINDING: {summary['main_finding']}")
        print(f"📊 TELNET STATUS:")
        print(f"   • Total async lines audited: {summary['total_async_lines']}")
        print(f"   • Lines with TELNET ENABLED: {summary['telnet_enabled_count']} 🔴")
        print(f"   • Lines with telnet disabled: {summary['telnet_disabled_count']} ✅")
        print(f"   • Device has telnet: {'YES 🚨' if summary['device_has_telnet'] else 'NO ✅'}")
        print()
        
        # Risk breakdown
        risk_counts = summary['risk_breakdown']
        print(f"🚨 RISK BREAKDOWN:")
        print(f"   • CRITICAL risk: {risk_counts['CRITICAL']} (telnet + no auth)")
        print(f"   • HIGH risk: {risk_counts['HIGH']} (telnet + no ACL)")
        print(f"   • MEDIUM risk: {risk_counts['MEDIUM']} (telnet + auth)")
        print(f"   • LOW risk: {risk_counts['LOW']} (no telnet)")
        print()
        
        # Telnet detection breakdown
        print(f"🔍 TELNET DETECTION:")
        print(f"   • Explicit telnet: {summary['explicit_telnet_count']} (transport input telnet)")
        print(f"   • Implicit telnet: {summary['implicit_telnet_count']} (no SSH specified)")
        print()
        
        # TELNET-ENABLED DEVICES (Main Output)
        if self.audit_results['telnet_enabled_devices']:
            print(f"🌐 TELNET-ENABLED ASYNC LINES (PRIMARY FINDINGS):")
            print("-" * 80)
            for device in self.audit_results['telnet_enabled_devices']:
                print(f"   {device['status_summary']}")
                print(f"     └─ Line: {device['line_id']}, Method: {device['telnet_detection_method']}")
                print(f"        Auth: {device['login_method']}, ACL: {device['access_class']}")
                print()
        else:
            print("✅ NO TELNET-ENABLED ASYNC LINES FOUND - SECURE CONFIGURATION")
            print()
        
        # Compliance issues
        if self.audit_results['compliance_issues']:
            print(f"⚠️  COMPLIANCE ISSUES:")
            for issue in self.audit_results['compliance_issues']:
                print(f"   • {issue}")
            print()
        
        # Recommendations
        if self.audit_results['recommendations']:
            print(f"💡 RECOMMENDATIONS:")
            for rec in self.audit_results['recommendations']:
                print(f"   {rec}")
            print()
        
        print("=" * 80)

    def export_telnet_results(self, filename: str = None):
        """Export telnet audit results to JSON."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"async_telnet_audit_{timestamp}.json"
        
        # Convert AsyncLineConfig objects to dicts for JSON serialization
        export_data = self.audit_results.copy()
        export_data['support_data'] = {
            'detailed_configs': {
                'slot_0_pa_1': {k: asdict(v) for k, v in self.lines_0_1.items()},
                'slot_1_pa_0': {k: asdict(v) for k, v in self.lines_1_0.items()}
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"📄 Telnet audit results exported to: {filename}")


def main():
    """Main function - Execute telnet detection on async lines."""
    print("🎯 ASYNC LINE TELNET AUDITOR")
    print("Primary Mission: Detect telnet enablement on async ports")
    print("=" * 60)
    
    auditor = AsyncLineTelnetAuditor()
    
    # Run the telnet-focused audit
    results = auditor.audit_async_lines_for_telnet()
    
    # Print telnet-focused report
    auditor.print_telnet_focused_report()
    
    # Export results
    auditor.export_telnet_results()
    
    # Exit code based on telnet detection
    telnet_found = results['telnet_summary']['device_has_telnet']
    return 1 if telnet_found else 0  # 1 = telnet found (issue), 0 = no telnet (good)


if __name__ == "__main__":
    sys.exit(main()) 
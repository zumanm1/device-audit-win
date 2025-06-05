#!/usr/bin/env python3
"""
Async Line Auditor - Focus on specific slot/PA patterns
========================================================

This script specifically audits async TTY lines with the patterns:
- Slot 0 / PA 1 / channels 0-22 ("line 0/1/*")  
- Slot 1 / PA 0 / channels 0-22 ("line 1/0/*")

Key Features:
- Extracts async line configurations using the section command
- Identifies telnet-enabled lines
- Validates channel numbering (0-22)
- Checks security configurations (AAA, ACLs)
- Reports on rotary groups and speed settings
- Provides compliance auditing checklist

Commands used:
- show running-config | section ^line 0\/1\/
- show running-config | section ^line 1\/0\/
"""

import re
import sys
import json
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AsyncLineConfig:
    """Data structure for async line configuration."""
    line_id: str
    slot: int
    pa: int
    channel: int
    login_method: str = "none"
    exec_enabled: bool = True
    timeout: str = "none"
    transport_input: List[str] = None
    access_class: str = "none"
    rotary: str = "none"
    speed: str = "none"
    flowcontrol: str = "none"
    autocommand: str = "none"
    privilege_level: str = "none"
    escape_char: str = "none"
    raw_config: List[str] = None

    def __post_init__(self):
        if self.transport_input is None:
            self.transport_input = []
        if self.raw_config is None:
            self.raw_config = []

    @property
    def telnet_enabled(self) -> bool:
        """Check if telnet is enabled in transport input."""
        return "telnet" in self.transport_input or "all" in self.transport_input

    @property
    def ssh_enabled(self) -> bool:
        """Check if SSH is enabled in transport input."""
        return "ssh" in self.transport_input or "all" in self.transport_input

    @property
    def is_console_server_port(self) -> bool:
        """Determine if this is a console server port (no exec + rotary)."""
        return not self.exec_enabled and self.rotary != "none"


class AsyncLineAuditor:
    """Main auditor class for async line configurations."""
    
    def __init__(self):
        self.lines_0_1 = {}  # Slot 0, PA 1 lines
        self.lines_1_0 = {}  # Slot 1, PA 0 lines
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'findings': [],
            'compliance_issues': [],
            'telnet_enabled_lines': [],
            'recommendations': []
        }

    def parse_line_config(self, config_text: str, target_pattern: str) -> Dict[str, AsyncLineConfig]:
        """Parse async line configurations from show run output."""
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
            
            # Parse individual configuration lines
            for line in block.split('\n'):
                line = line.strip()
                
                # Login method
                if line.startswith('login authentication'):
                    config.login_method = line.split()[-1]
                elif line == 'login local':
                    config.login_method = 'local'
                elif line == 'login':
                    config.login_method = 'password'
                elif line == 'no login':
                    config.login_method = 'none'
                    
                # Exec settings
                elif line == 'no exec':
                    config.exec_enabled = False
                    
                # Timeout
                elif line.startswith('exec-timeout'):
                    config.timeout = ' '.join(line.split()[1:])
                    
                # Transport input
                elif line.startswith('transport input'):
                    transport_methods = line.split()[2:]
                    config.transport_input = transport_methods
                    
                # Access class
                elif line.startswith('access-class'):
                    parts = line.split()
                    if len(parts) >= 2:
                        config.access_class = parts[1]
                        
                # Rotary group
                elif line.startswith('rotary'):
                    config.rotary = line.split()[-1]
                    
                # Speed
                elif line.startswith('speed'):
                    config.speed = line.split()[-1]
                    
                # Flow control
                elif line.startswith('flowcontrol'):
                    config.flowcontrol = ' '.join(line.split()[1:])
                    
                # Autocommand
                elif line.startswith('autocommand'):
                    config.autocommand = ' '.join(line.split()[1:])
                    
                # Privilege level
                elif line.startswith('privilege level'):
                    config.privilege_level = line.split()[-1]
                    
                # Escape character
                elif line.startswith('escape-character'):
                    config.escape_char = line.split()[-1]
                    
            lines[line_id] = config
            
        return lines

    def simulate_cisco_commands(self, config_file: str = "dummy-router-configs") -> Dict[str, str]:
        """Simulate the Cisco IOS commands by parsing the config file."""
        try:
            with open(config_file, 'r') as f:
                full_config = f.read()
        except FileNotFoundError:
            print(f"Config file {config_file} not found!")
            return {}
            
        results = {}
        
        # Simulate: show running-config | section ^line 0\/1\/
        section_0_1 = self._extract_section(full_config, r'^line 0/1/')
        results['section_0_1'] = section_0_1
        
        # Simulate: show running-config | section ^line 1\/0\/
        section_1_0 = self._extract_section(full_config, r'^line 1/0/')
        results['section_1_0'] = section_1_0
        
        # Simulate: show run | include ^line [01]\/[01]\/
        include_lines = self._extract_line_headers(full_config)
        results['include_lines'] = include_lines
        
        return results

    def _extract_section(self, config: str, pattern: str) -> str:
        """Extract sections matching the pattern (simulates IOS section command)."""
        lines = config.split('\n')
        result_lines = []
        in_section = False
        
        for line in lines:
            # Check if line matches our pattern
            if re.match(pattern, line):
                in_section = True
                result_lines.append(line)
            elif in_section:
                # Continue until we hit a line starting with ! or another line command
                if line.strip() == '!' or line.startswith('line '):
                    result_lines.append('!')
                    in_section = False
                    if line.startswith('line ') and not re.match(pattern, line):
                        continue
                else:
                    result_lines.append(line)
        
        return '\n'.join(result_lines)

    def _extract_line_headers(self, config: str) -> str:
        """Extract just the line headers (simulates include command)."""
        lines = config.split('\n')
        result_lines = []
        
        pattern = r'^line [01]/[01]/\d+$'
        
        for line in lines:
            if re.match(pattern, line.strip()):
                result_lines.append(line.strip())
                
        return '\n'.join(result_lines)

    def audit_async_lines(self, config_file: str = "dummy-router-configs") -> Dict[str, Any]:
        """Main audit function."""
        print("🔍 Async Line Auditor - Focusing on slot/PA patterns 0/1/* and 1/0/*")
        print("=" * 70)
        
        # Simulate Cisco commands
        print("📡 Simulating Cisco IOS commands...")
        command_results = self.simulate_cisco_commands(config_file)
        
        if not command_results:
            return self.audit_results
            
        # Parse configurations
        print("🔧 Parsing async line configurations...")
        self.lines_0_1 = self.parse_line_config(command_results['section_0_1'], r'0/1/\d+')
        self.lines_1_0 = self.parse_line_config(command_results['section_1_0'], r'1/0/\d+')
        
        # Perform audit checks
        self._audit_channel_numbering()
        self._audit_telnet_enablement()
        self._audit_security_settings()
        self._audit_rotary_groups()
        self._audit_speed_and_flow()
        self._generate_summary()
        
        return self.audit_results

    def _audit_channel_numbering(self):
        """Verify channel numbers are 0-22."""
        print("🔢 Auditing channel numbering...")
        
        expected_channels = set(range(23))  # 0-22
        
        # Check 0/1/* lines
        found_0_1 = set(config.channel for config in self.lines_0_1.values())
        missing_0_1 = expected_channels - found_0_1
        extra_0_1 = found_0_1 - expected_channels
        
        # Check 1/0/* lines  
        found_1_0 = set(config.channel for config in self.lines_1_0.values())
        missing_1_0 = expected_channels - found_1_0
        extra_1_0 = found_1_0 - expected_channels
        
        if missing_0_1:
            self.audit_results['compliance_issues'].append(
                f"Missing channels in 0/1/*: {sorted(missing_0_1)}"
            )
            
        if extra_0_1:
            self.audit_results['compliance_issues'].append(
                f"Unexpected channels in 0/1/*: {sorted(extra_0_1)}"
            )
            
        if missing_1_0:
            self.audit_results['compliance_issues'].append(
                f"Missing channels in 1/0/*: {sorted(missing_1_0)}"
            )
            
        if extra_1_0:
            self.audit_results['compliance_issues'].append(
                f"Unexpected channels in 1/0/*: {sorted(extra_1_0)}"
            )

    def _audit_telnet_enablement(self):
        """Check where telnet is enabled."""
        print("🌐 Auditing telnet enablement...")
        
        telnet_lines = []
        
        # Check all lines for telnet
        for lines_dict, slot_pa in [(self.lines_0_1, "0/1"), (self.lines_1_0, "1/0")]:
            for line_id, config in lines_dict.items():
                if config.telnet_enabled:
                    telnet_info = {
                        'line_id': line_id,
                        'slot_pa': slot_pa,
                        'channel': config.channel,
                        'transport_input': config.transport_input,
                        'login_method': config.login_method,
                        'access_class': config.access_class,
                        'is_console_server': config.is_console_server_port
                    }
                    telnet_lines.append(telnet_info)
        
        self.audit_results['telnet_enabled_lines'] = telnet_lines
        
        # Add findings
        if telnet_lines:
            self.audit_results['findings'].append(
                f"Found {len(telnet_lines)} lines with telnet enabled"
            )
        else:
            self.audit_results['findings'].append("No lines with telnet enabled found")

    def _audit_security_settings(self):
        """Audit security configurations."""
        print("🔒 Auditing security settings...")
        
        security_issues = []
        
        for lines_dict, slot_pa in [(self.lines_0_1, "0/1"), (self.lines_1_0, "1/0")]:
            for line_id, config in lines_dict.items():
                # Check for no login with telnet enabled
                if config.telnet_enabled and config.login_method == "none":
                    security_issues.append(
                        f"Security Risk: {line_id} has telnet enabled but no login required"
                    )
                
                # Check for missing ACLs on management ports
                if config.login_method in ["local", "password"] and config.access_class == "none":
                    security_issues.append(
                        f"Security Warning: {line_id} has login enabled but no access-class ACL"
                    )
                
                # Check console server ports configuration
                if config.is_console_server_port and config.login_method != "none":
                    security_issues.append(
                        f"Config Issue: {line_id} appears to be console server port but has login enabled"
                    )
        
        self.audit_results['compliance_issues'].extend(security_issues)

    def _audit_rotary_groups(self):
        """Audit rotary group assignments."""
        print("🔄 Auditing rotary groups...")
        
        rotary_groups = {}
        
        for lines_dict, slot_pa in [(self.lines_0_1, "0/1"), (self.lines_1_0, "1/0")]:
            for line_id, config in lines_dict.items():
                if config.rotary != "none":
                    if config.rotary not in rotary_groups:
                        rotary_groups[config.rotary] = []
                    rotary_groups[config.rotary].append({
                        'line_id': line_id,
                        'slot_pa': slot_pa
                    })
        
        # Check for rotary group conflicts
        for group, lines in rotary_groups.items():
            slot_pas = set(line['slot_pa'] for line in lines)
            if len(slot_pas) > 1:
                self.audit_results['findings'].append(
                    f"Rotary group {group} spans multiple slot/PA combinations: {slot_pas}"
                )

    def _audit_speed_and_flow(self):
        """Audit speed and flow control settings."""
        print("⚡ Auditing speed and flow control...")
        
        speed_issues = []
        
        for lines_dict, slot_pa in [(self.lines_0_1, "0/1"), (self.lines_1_0, "1/0")]:
            for line_id, config in lines_dict.items():
                # Check for missing flow control on configured lines
                if (config.speed != "none" and config.speed != "" and 
                    config.flowcontrol == "none" and config.transport_input):
                    speed_issues.append(
                        f"Flow Control Warning: {line_id} has speed configured but no flow control"
                    )
        
        if speed_issues:
            self.audit_results['compliance_issues'].extend(speed_issues)

    def _generate_summary(self):
        """Generate audit summary."""
        total_0_1 = len(self.lines_0_1)
        total_1_0 = len(self.lines_1_0)
        total_telnet = len(self.audit_results['telnet_enabled_lines'])
        total_issues = len(self.audit_results['compliance_issues'])
        
        self.audit_results['summary'] = {
            'slot_0_pa_1_lines': total_0_1,
            'slot_1_pa_0_lines': total_1_0,
            'total_async_lines': total_0_1 + total_1_0,
            'telnet_enabled_count': total_telnet,
            'compliance_issues_count': total_issues,
            'expected_lines_per_slot': 23,  # channels 0-22
            'audit_status': 'PASS' if total_issues == 0 else 'ISSUES_FOUND'
        }

    def print_audit_report(self):
        """Print a formatted audit report."""
        print("\n" + "=" * 70)
        print("📋 ASYNC LINE AUDIT REPORT")
        print("=" * 70)
        
        # Summary
        summary = self.audit_results['summary']
        print(f"📊 SUMMARY:")
        print(f"   • Slot 0/PA 1 lines found: {summary['slot_0_pa_1_lines']}/23")
        print(f"   • Slot 1/PA 0 lines found: {summary['slot_1_pa_0_lines']}/23") 
        print(f"   • Total async lines: {summary['total_async_lines']}")
        print(f"   • Telnet-enabled lines: {summary['telnet_enabled_count']}")
        print(f"   • Compliance issues: {summary['compliance_issues_count']}")
        print(f"   • Audit Status: {summary['audit_status']}")
        
        # Telnet-enabled lines
        if self.audit_results['telnet_enabled_lines']:
            print(f"\n🌐 TELNET-ENABLED LINES:")
            for line in self.audit_results['telnet_enabled_lines']:
                status = "Console Server" if line['is_console_server'] else "Management"
                print(f"   • {line['line_id']} ({status}) - Login: {line['login_method']}, ACL: {line['access_class']}")
        
        # Compliance issues
        if self.audit_results['compliance_issues']:
            print(f"\n⚠️  COMPLIANCE ISSUES:")
            for issue in self.audit_results['compliance_issues']:
                print(f"   • {issue}")
        
        # Findings
        if self.audit_results['findings']:
            print(f"\n🔍 FINDINGS:")
            for finding in self.audit_results['findings']:
                print(f"   • {finding}")
        
        print("\n" + "=" * 70)

    def export_results(self, filename: str = None):
        """Export audit results to JSON."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"async_line_audit_{timestamp}.json"
        
        # Convert AsyncLineConfig objects to dicts for JSON serialization
        export_data = self.audit_results.copy()
        export_data['detailed_configs'] = {
            'slot_0_pa_1': {k: asdict(v) for k, v in self.lines_0_1.items()},
            'slot_1_pa_0': {k: asdict(v) for k, v in self.lines_1_0.items()}
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"📄 Audit results exported to: {filename}")


def main():
    """Main function to run the async line auditor."""
    auditor = AsyncLineAuditor()
    
    # Run the audit
    results = auditor.audit_async_lines()
    
    # Print report
    auditor.print_audit_report()
    
    # Export results
    auditor.export_results()
    
    return 0 if results['summary']['audit_status'] == 'PASS' else 1


if __name__ == "__main__":
    sys.exit(main()) 
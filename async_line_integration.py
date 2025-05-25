#!/usr/bin/env python3
"""
Async Line Integration for NetAuditPro
======================================

This module adds focused async line auditing capabilities to the NetAuditPro
router auditing application. It specifically targets:

- Slot 0 / PA 1 / channels 0-22 ("line 0/1/*")
- Slot 1 / PA 0 / channels 0-22 ("line 1/0/*")

Key Features:
- Extracts async line configs using section commands
- Identifies telnet-enabled lines with security analysis
- Validates channel numbering and slot/PA patterns
- Generates detailed reports for async line compliance
- Integrates with existing NetAuditPro workflow

Integration Points:
- Adds async line collection to the audit workflow
- Provides new report sections for async line analysis
- Extends the web UI with async line views
- Sanitizes all async line logs (no credentials exposed)
"""

import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AsyncLineConfig:
    """Data structure for async line configuration with security focus."""
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
    security_score: int = 0
    risk_level: str = "LOW"

    def __post_init__(self):
        if self.transport_input is None:
            self.transport_input = []
        if self.raw_config is None:
            self.raw_config = []
        self._calculate_security_score()

    def _calculate_security_score(self):
        """Calculate security score based on configuration."""
        score = 0
        
        # Base score for having any transport input
        if self.transport_input and self.transport_input != ["none"]:
            score += 10
            
        # Telnet enablement adds risk
        if self.telnet_enabled:
            score += 20
            
        # No authentication is high risk
        if self.login_method == "none" and self.telnet_enabled:
            score += 30
            
        # Missing ACL on authenticated lines
        if self.login_method in ["local", "password"] and self.access_class == "none":
            score += 15
            
        # High privilege level without proper security
        if self.privilege_level not in ["none", ""] and self.access_class == "none":
            score += 10
            
        self.security_score = score
        
        # Set risk level
        if score >= 40:
            self.risk_level = "HIGH"
        elif score >= 20:
            self.risk_level = "MEDIUM"
        else:
            self.risk_level = "LOW"

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

    @property
    def security_summary(self) -> str:
        """Get a human-readable security summary."""
        if self.is_console_server_port:
            return f"Console Server Port (Rotary {self.rotary})"
        elif self.telnet_enabled and self.login_method == "none":
            return "SECURITY RISK: Telnet with no authentication"
        elif self.telnet_enabled and self.access_class == "none":
            return "Security Warning: Telnet without ACL protection"
        elif self.telnet_enabled:
            return f"Secure Telnet: {self.login_method} auth, ACL: {self.access_class}"
        else:
            return "Transport disabled or SSH-only"


class AsyncLineCollector:
    """Collects async line configurations from router output."""
    
    def __init__(self, sanitize_func=None):
        self.sanitize_func = sanitize_func or (lambda x: x)
        
    def extract_async_sections(self, show_run_output: str) -> Dict[str, str]:
        """Extract async line sections from show running-config output."""
        sections = {}
        
        # Extract 0/1/* lines
        sections['0_1_lines'] = self._extract_section_by_pattern(
            show_run_output, r'^line 0/1/'
        )
        
        # Extract 1/0/* lines
        sections['1_0_lines'] = self._extract_section_by_pattern(
            show_run_output, r'^line 1/0/'
        )
        
        return sections
    
    def _extract_section_by_pattern(self, config: str, pattern: str) -> str:
        """Extract sections matching pattern (simulates IOS section command)."""
        lines = config.split('\n')
        result_lines = []
        in_section = False
        
        for line in lines:
            # Check if line matches our pattern
            if re.match(pattern, line.strip()):
                in_section = True
                result_lines.append(line)
            elif in_section:
                # Continue until we hit a line starting with ! or another line command
                if line.strip() == '!' or (line.startswith('line ') and not re.match(pattern, line.strip())):
                    result_lines.append('!')
                    in_section = False
                    if line.startswith('line ') and not re.match(pattern, line.strip()):
                        continue
                else:
                    result_lines.append(line)
        
        return self.sanitize_func('\n'.join(result_lines))
    
    def parse_async_config(self, section_text: str, target_pattern: str) -> Dict[str, AsyncLineConfig]:
        """Parse async line configurations from section output."""
        lines = {}
        
        # Split by line blocks (separated by !)
        blocks = re.split(r'\n!\n', section_text)
        
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
                raw_config=self.sanitize_func(block.strip()).split('\n')
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
                    config.autocommand = self.sanitize_func(' '.join(line.split()[1:]))
                    
                # Privilege level
                elif line.startswith('privilege level'):
                    config.privilege_level = line.split()[-1]
                    
                # Escape character
                elif line.startswith('escape-character'):
                    config.escape_char = line.split()[-1]
                    
            lines[line_id] = config
            
        return lines


class AsyncLineAuditor:
    """Main async line auditor integrated with NetAuditPro."""
    
    def __init__(self, sanitize_func=None, log_func=None):
        self.sanitize_func = sanitize_func or (lambda x: x)
        self.log_func = log_func or print
        self.collector = AsyncLineCollector(sanitize_func)
        self.results = {}
        
    def audit_device_async_lines(self, device_name: str, net_connect) -> Dict[str, Any]:
        """Audit async lines for a specific device."""
        self.log_func(f"🔍 Auditing async lines for {device_name}")
        
        try:
            # Get running configuration
            self.log_func(f"  📄 Retrieving running configuration...")
            show_run = net_connect.send_command("show running-config", delay_factor=2)
            
            # Extract async line sections
            self.log_func(f"  🔧 Extracting async line sections...")
            sections = self.collector.extract_async_sections(show_run)
            
            # Parse configurations
            lines_0_1 = self.collector.parse_async_config(sections['0_1_lines'], r'0/1/\d+')
            lines_1_0 = self.collector.parse_async_config(sections['1_0_lines'], r'1/0/\d+')
            
            # Perform analysis
            analysis = self._analyze_async_lines(lines_0_1, lines_1_0)
            
            # Store results
            self.results[device_name] = {
                'timestamp': datetime.now().isoformat(),
                'lines_0_1': {k: asdict(v) for k, v in lines_0_1.items()},
                'lines_1_0': {k: asdict(v) for k, v in lines_1_0.items()},
                'analysis': analysis,
                'raw_sections': sections
            }
            
            self.log_func(f"  ✅ Async line audit completed for {device_name}")
            return self.results[device_name]
            
        except Exception as e:
            error_msg = f"❌ Async line audit failed for {device_name}: {str(e)}"
            self.log_func(error_msg)
            return {'error': self.sanitize_func(error_msg)}
    
    def _analyze_async_lines(self, lines_0_1: Dict, lines_1_0: Dict) -> Dict[str, Any]:
        """Analyze async line configurations for compliance and security."""
        analysis = {
            'summary': {},
            'telnet_enabled': [],
            'security_risks': [],
            'compliance_issues': [],
            'recommendations': []
        }
        
        # Combine all lines for analysis
        all_lines = {**lines_0_1, **lines_1_0}
        
        # Summary statistics
        total_lines = len(all_lines)
        telnet_count = sum(1 for line in all_lines.values() if line.telnet_enabled)
        high_risk_count = sum(1 for line in all_lines.values() if line.risk_level == "HIGH")
        
        analysis['summary'] = {
            'total_async_lines': total_lines,
            'slot_0_pa_1_count': len(lines_0_1),
            'slot_1_pa_0_count': len(lines_1_0),
            'telnet_enabled_count': telnet_count,
            'high_risk_count': high_risk_count,
            'expected_per_slot': 23
        }
        
        # Analyze each line
        for line_id, config in all_lines.items():
            if config.telnet_enabled:
                analysis['telnet_enabled'].append({
                    'line_id': line_id,
                    'login_method': config.login_method,
                    'access_class': config.access_class,
                    'security_score': config.security_score,
                    'risk_level': config.risk_level,
                    'summary': config.security_summary
                })
                
            if config.risk_level == "HIGH":
                analysis['security_risks'].append({
                    'line_id': line_id,
                    'issue': config.security_summary,
                    'security_score': config.security_score
                })
        
        # Check compliance issues
        self._check_compliance(lines_0_1, lines_1_0, analysis)
        
        # Generate recommendations
        self._generate_recommendations(analysis)
        
        return analysis
    
    def _check_compliance(self, lines_0_1: Dict, lines_1_0: Dict, analysis: Dict):
        """Check for compliance issues."""
        issues = []
        
        # Check channel numbering (0-22)
        expected_channels = set(range(23))
        
        for slot_pa, lines_dict in [("0/1", lines_0_1), ("1/0", lines_1_0)]:
            found_channels = set(config.channel for config in lines_dict.values())
            missing = expected_channels - found_channels
            extra = found_channels - expected_channels
            
            if missing:
                issues.append(f"Missing channels in {slot_pa}/*: {sorted(missing)}")
            if extra:
                issues.append(f"Unexpected channels in {slot_pa}/*: {sorted(extra)}")
        
        # Check rotary group conflicts
        rotary_groups = {}
        for slot_pa, lines_dict in [("0/1", lines_0_1), ("1/0", lines_1_0)]:
            for config in lines_dict.values():
                if config.rotary != "none":
                    if config.rotary not in rotary_groups:
                        rotary_groups[config.rotary] = []
                    rotary_groups[config.rotary].append(slot_pa)
        
        for group, slots in rotary_groups.items():
            if len(set(slots)) > 1:
                issues.append(f"Rotary group {group} spans multiple slot/PA: {set(slots)}")
        
        analysis['compliance_issues'] = issues
    
    def _generate_recommendations(self, analysis: Dict):
        """Generate security and configuration recommendations."""
        recommendations = []
        
        if analysis['summary']['high_risk_count'] > 0:
            recommendations.append(
                "🔒 HIGH PRIORITY: Review high-risk lines with telnet but no authentication"
            )
        
        if analysis['summary']['telnet_enabled_count'] > 10:
            recommendations.append(
                "🔐 Consider migrating from telnet to SSH-only transport where possible"
            )
        
        if len(analysis['compliance_issues']) > 0:
            recommendations.append(
                "📋 Address compliance issues with channel numbering and rotary groups"
            )
        
        # Check for missing ACLs
        no_acl_count = sum(1 for line in analysis['telnet_enabled'] 
                          if line['access_class'] == "none")
        if no_acl_count > 0:
            recommendations.append(
                f"🛡️ Apply access-class ACLs to {no_acl_count} telnet-enabled lines"
            )
        
        analysis['recommendations'] = recommendations
    
    def generate_report(self, device_name: str) -> str:
        """Generate a formatted async line report for a device."""
        if device_name not in self.results:
            return f"No async line data available for {device_name}"
        
        data = self.results[device_name]
        if 'error' in data:
            return f"Async Line Audit Error: {data['error']}"
        
        analysis = data['analysis']
        report_lines = []
        
        # Header
        report_lines.append("=" * 60)
        report_lines.append(f"ASYNC LINE AUDIT REPORT - {device_name}")
        report_lines.append("=" * 60)
        
        # Summary
        summary = analysis['summary']
        report_lines.append("📊 SUMMARY:")
        report_lines.append(f"   • Total async lines: {summary['total_async_lines']}")
        report_lines.append(f"   • Slot 0/PA 1 lines: {summary['slot_0_pa_1_count']}/23")
        report_lines.append(f"   • Slot 1/PA 0 lines: {summary['slot_1_pa_0_count']}/23")
        report_lines.append(f"   • Telnet-enabled: {summary['telnet_enabled_count']}")
        report_lines.append(f"   • High-risk lines: {summary['high_risk_count']}")
        report_lines.append("")
        
        # Telnet-enabled lines
        if analysis['telnet_enabled']:
            report_lines.append("🌐 TELNET-ENABLED LINES:")
            for line in analysis['telnet_enabled']:
                risk_indicator = "🔴" if line['risk_level'] == "HIGH" else "🟡" if line['risk_level'] == "MEDIUM" else "🟢"
                report_lines.append(f"   {risk_indicator} {line['line_id']} - {line['summary']}")
            report_lines.append("")
        
        # Security risks
        if analysis['security_risks']:
            report_lines.append("⚠️ SECURITY RISKS:")
            for risk in analysis['security_risks']:
                report_lines.append(f"   🔴 {risk['line_id']}: {risk['issue']}")
            report_lines.append("")
        
        # Compliance issues
        if analysis['compliance_issues']:
            report_lines.append("📋 COMPLIANCE ISSUES:")
            for issue in analysis['compliance_issues']:
                report_lines.append(f"   • {issue}")
            report_lines.append("")
        
        # Recommendations
        if analysis['recommendations']:
            report_lines.append("💡 RECOMMENDATIONS:")
            for rec in analysis['recommendations']:
                report_lines.append(f"   {rec}")
            report_lines.append("")
        
        report_lines.append("=" * 60)
        
        return '\n'.join(report_lines)


# Integration functions for NetAuditPro

def collect_async_line_data(net_connect, device_name: str, sanitize_func=None, log_func=None) -> Dict[str, Any]:
    """Collect async line data for integration with NetAuditPro audit workflow."""
    auditor = AsyncLineAuditor(sanitize_func, log_func)
    return auditor.audit_device_async_lines(device_name, net_connect)


def generate_async_line_commands() -> List[str]:
    """Generate the list of commands needed for async line auditing."""
    return [
        "show running-config | section ^line 0/1/",
        "show running-config | section ^line 1/0/",
        "show run | include ^line [01]/[01]/"
    ]


def format_async_line_summary(async_data: Dict[str, Any]) -> str:
    """Format async line data for inclusion in NetAuditPro reports."""
    if 'error' in async_data:
        return f"Async Line Audit: {async_data['error']}"
    
    analysis = async_data.get('analysis', {})
    summary = analysis.get('summary', {})
    
    lines = [
        "Async Line Summary:",
        f"  • Total lines: {summary.get('total_async_lines', 0)}",
        f"  • Telnet-enabled: {summary.get('telnet_enabled_count', 0)}",
        f"  • High-risk: {summary.get('high_risk_count', 0)}"
    ]
    
    return '\n'.join(lines)


if __name__ == "__main__":
    # Demo mode - test with dummy configs
    print("🔧 Async Line Integration Demo")
    print("This module integrates with NetAuditPro for focused async line auditing")
    print("Targets: Slot 0/PA 1 and Slot 1/PA 0, channels 0-22")
    print("Focus: Telnet enablement and security compliance") 
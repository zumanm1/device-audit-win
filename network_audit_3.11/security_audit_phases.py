#!/usr/bin/env python3
"""
Security Audit Phases Module (v3.11)
Implements the 5 core security audit phases used by the security_audit.py module
"""

import os
import sys
import time
import re
import socket
import subprocess
import json

# Import core functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from audit_core import Fore, Style, AuditResult
except ImportError as e:
    print(f"Error importing audit_core module: {e}")
    print("Make sure audit_core.py is in the same directory.")
    sys.exit(1)

# Set up module constants
SECURITY_CHECKS = {
    "telnet_enabled": {
        "description": "Checks if Telnet is enabled on any line",
        "severity": "critical",
        "recommendation": "Disable Telnet and use SSH with strong authentication",
        "reference": "NIST SP 800-53: AC-17, IA-2"
    },
    "weak_passwords": {
        "description": "Checks for weak or default passwords",
        "severity": "critical",
        "recommendation": "Implement strong password policy with minimum complexity requirements",
        "reference": "NIST SP 800-53: IA-5"
    },
    "unused_accounts": {
        "description": "Checks for unused user accounts",
        "severity": "medium",
        "recommendation": "Remove unused accounts to reduce attack surface",
        "reference": "NIST SP 800-53: AC-2"
    },
    "insecure_services": {
        "description": "Checks for insecure or unnecessary services",
        "severity": "high",
        "recommendation": "Disable unnecessary services to reduce attack surface",
        "reference": "NIST SP 800-53: CM-7"
    },
    "unsecured_interfaces": {
        "description": "Checks for unsecured interfaces",
        "severity": "high",
        "recommendation": "Secure all interfaces with appropriate access controls",
        "reference": "NIST SP 800-53: AC-4"
    }
}

# Phase 1: Connectivity Verification
def execute_phase1_connectivity(device, test_mode=False):
    """
    Verify basic network connectivity to the device
    Returns a tuple of (success, details, error)
    """
    ip = device.get('ip')
    hostname = device.get('hostname')
    
    if test_mode:
        # In test mode, simulate results based on IP pattern
        success = int(ip.split('.')[-1]) % 10 != 0  # Simulate failure for IPs ending in 0
        
        details = {
            'method': 'ICMP ping (simulated)',
            'response_time_ms': 15.7 if success else None
        }
        
        error = None if success else "Simulated connectivity failure"
        
        return (success, details, error)
    
    # Use ping to check connectivity
    try:
        # Determine the ping command based on OS
        if sys.platform == "win32":
            ping_cmd = ["ping", "-n", "4", "-w", "2000", ip]
        else:
            ping_cmd = ["ping", "-c", "4", "-W", "2", ip]
        
        # Execute ping command
        result = subprocess.run(ping_cmd, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                text=True)
        
        success = result.returncode == 0
        output = result.stdout
        
        if success:
            # Extract response time
            if sys.platform == "win32":
                rtt_match = re.search(r"Average = (\d+)ms", output)
                rtt = float(rtt_match.group(1)) if rtt_match else None
            else:
                rtt_match = re.search(r"min/avg/max(?:/mdev)? = [\d.]+/([\d.]+)/", output)
                rtt = float(rtt_match.group(1)) if rtt_match else None
            
            details = {
                'method': 'ICMP ping',
                'response_time_ms': rtt
            }
            error = None
        else:
            details = {
                'method': 'ICMP ping',
                'response_time_ms': None
            }
            error = "ICMP ping failed"
        
        return (success, details, error)
        
    except Exception as e:
        return (False, {'method': 'ICMP ping'}, str(e))

# Phase 2: Authentication Testing
def execute_phase2_authentication(device, connection=None, test_mode=False):
    """
    Test authentication to the device
    If connection is provided, uses that existing connection
    Otherwise attempts to establish a new connection
    
    Returns a tuple of (success, connection, details, error)
    """
    if test_mode:
        # In test mode, simulate results
        success = device.get('hostname', '').lower() != 'firewall.example.com'  # Simulate failure for firewalls
        
        details = {
            'method': 'SSH authentication (simulated)',
            'protocol': 'SSH',
            'username': device.get('username', 'admin')
        }
        
        error = None if success else "Simulated authentication failure"
        
        return (success, None, details, error)
    
    if connection:
        # Connection already established
        return (True, connection, {
            'method': 'Using existing connection',
            'protocol': 'SSH',
            'username': device.get('username')
        }, None)
    
    # Try to establish SSH connection
    try:
        # Configure device connection parameters
        device_params = {
            'device_type': device.get('device_type', 'cisco_ios'),
            'ip': device.get('ip'),
            'username': device.get('username'),
            'password': device.get('password'),
            'secret': device.get('secret'),
            'port': 22,
            'timeout': 10
        }
        
        # Try to connect
        from netmiko import ConnectHandler
        from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
        
        conn = ConnectHandler(**device_params)
        
        # Enter enable mode if needed
        if device.get('device_type') in ['cisco_ios', 'cisco_xe', 'cisco_xr', 'cisco_nxos']:
            conn.enable()
        
        return (True, conn, {
            'method': 'SSH authentication',
            'protocol': 'SSH',
            'username': device.get('username')
        }, None)
        
    except NetmikoTimeoutException:
        return (False, None, {
            'method': 'SSH authentication',
            'protocol': 'SSH',
            'username': device.get('username')
        }, "Connection timed out")
        
    except NetmikoAuthenticationException:
        return (False, None, {
            'method': 'SSH authentication',
            'protocol': 'SSH',
            'username': device.get('username')
        }, "Authentication failed")
        
    except Exception as e:
        return (False, None, {
            'method': 'SSH authentication',
            'protocol': 'SSH',
            'username': device.get('username')
        }, str(e))

# Phase 3: Configuration Audit
def execute_phase3_config_audit(device, connection, test_mode=False):
    """
    Collect and audit device configuration
    Returns a tuple of (success, config_data, details, error)
    """
    hostname = device.get('hostname')
    
    if test_mode:
        # In test mode, generate sample configuration data
        config_data = {
            'running_config': f"! Simulated running configuration for {hostname}\n" +
                            "!\nversion 15.7\nno service pad\n" +
                            "service timestamps debug datetime msec\n" +
                            "service timestamps log datetime msec\n" +
                            "no service password-encryption\n" +
                            "!\nhostname " + hostname + "\n" +
                            "!\nline vty 0 4\n transport input telnet ssh\n" +
                            " login local\n!\nend",
            'interfaces': [
                {'name': 'GigabitEthernet0/0', 'status': 'up', 'ip': '192.168.1.1'},
                {'name': 'GigabitEthernet0/1', 'status': 'down', 'ip': None}
            ],
            'version': '15.7',
            'users': ['admin', 'backup'],
            'services': ['telnet', 'ssh', 'http']
        }
        
        details = {
            'commands_executed': ['show running-config', 'show interfaces', 'show version'],
            'config_size_bytes': len(config_data['running_config'])
        }
        
        return (True, config_data, details, None)
    
    if not connection:
        return (False, None, {}, "No connection available for configuration audit")
    
    try:
        # Collect configuration data
        config_data = {}
        
        # Get running configuration
        config_data['running_config'] = connection.send_command("show running-config")
        
        # Get interface information
        interface_output = connection.send_command("show interfaces")
        
        # Get version information
        version_output = connection.send_command("show version")
        
        # Extract basic data for interfaces and version
        # This is simplified - a real implementation would parse the outputs thoroughly
        config_data['interfaces'] = []
        for interface_match in re.finditer(r'(\S+) is (up|down)', interface_output):
            interface_name = interface_match.group(1)
            status = interface_match.group(2)
            
            # Look for IP address
            ip_match = re.search(r'Internet address is (\S+)', 
                                 interface_output[interface_match.start():interface_match.start()+500])
            ip = ip_match.group(1) if ip_match else None
            
            config_data['interfaces'].append({
                'name': interface_name,
                'status': status,
                'ip': ip
            })
        
        # Extract version information
        version_match = re.search(r'Version ([\d.]+)', version_output)
        config_data['version'] = version_match.group(1) if version_match else 'Unknown'
        
        # Extract user information
        config_data['users'] = []
        for user_match in re.finditer(r'username (\S+)', config_data['running_config']):
            config_data['users'].append(user_match.group(1))
        
        # Determine enabled services
        config_data['services'] = []
        if re.search(r'transport input.*telnet', config_data['running_config']):
            config_data['services'].append('telnet')
        if re.search(r'transport input.*ssh', config_data['running_config']):
            config_data['services'].append('ssh')
        if re.search(r'ip http server', config_data['running_config']):
            config_data['services'].append('http')
        if re.search(r'ip http secure-server', config_data['running_config']):
            config_data['services'].append('https')
        
        details = {
            'commands_executed': ['show running-config', 'show interfaces', 'show version'],
            'config_size_bytes': len(config_data['running_config'])
        }
        
        return (True, config_data, details, None)
        
    except Exception as e:
        return (False, None, {'commands_attempted': ['show running-config', 'show interfaces', 'show version']}, str(e))

# Phase 4: Risk Assessment
def execute_phase4_risk_assessment(device, config_data, test_mode=False):
    """
    Assess security risks based on device configuration
    Returns a tuple of (success, findings, details, error)
    """
    if test_mode or not config_data:
        # In test mode or if no config data, generate sample findings
        if test_mode:
            # Generate consistent test findings based on hostname
            hostname = device.get('hostname', '').lower()
            has_telnet = 'router' in hostname
            has_weak_password = 'switch' in hostname
            has_unused_account = hostname.endswith('1.example.com')
            has_insecure_service = 'firewall' in hostname
        else:
            # If no config data but not in test mode, assume all risks present
            has_telnet = has_weak_password = has_unused_account = has_insecure_service = True
        
        findings = {}
        
        if has_telnet:
            findings['telnet_enabled'] = {
                'status': 'critical',
                'details': 'Telnet service is enabled on VTY lines',
                'recommendation': SECURITY_CHECKS['telnet_enabled']['recommendation']
            }
        
        if has_weak_password:
            findings['weak_passwords'] = {
                'status': 'critical',
                'details': 'Weak or default passwords detected',
                'recommendation': SECURITY_CHECKS['weak_passwords']['recommendation']
            }
        
        if has_unused_account:
            findings['unused_accounts'] = {
                'status': 'medium',
                'details': 'Potentially unused accounts detected',
                'recommendation': SECURITY_CHECKS['unused_accounts']['recommendation']
            }
        
        if has_insecure_service:
            findings['insecure_services'] = {
                'status': 'high',
                'details': 'Insecure or unnecessary services enabled',
                'recommendation': SECURITY_CHECKS['insecure_services']['recommendation']
            }
        
        details = {
            'checks_performed': list(SECURITY_CHECKS.keys()),
            'issues_found': len(findings)
        }
        
        return (True, findings, details, None)
    
    # Perform real risk assessment based on collected configuration
    try:
        findings = {}
        running_config = config_data.get('running_config', '')
        
        # Check 1: Telnet enabled
        if 'telnet' in config_data.get('services', []):
            findings['telnet_enabled'] = {
                'status': 'critical',
                'details': 'Telnet service is enabled on VTY lines',
                'recommendation': SECURITY_CHECKS['telnet_enabled']['recommendation'],
                'reference': SECURITY_CHECKS['telnet_enabled']['reference']
            }
        
        # Check 2: Weak passwords
        if 'no service password-encryption' in running_config:
            findings['weak_passwords'] = {
                'status': 'critical',
                'details': 'Passwords are not encrypted in the configuration',
                'recommendation': SECURITY_CHECKS['weak_passwords']['recommendation'],
                'reference': SECURITY_CHECKS['weak_passwords']['reference']
            }
        
        # Check 3: Insecure services
        insecure_services = []
        if 'ip http server' in running_config and 'ip http secure-server' not in running_config:
            insecure_services.append('HTTP without HTTPS')
        
        if 'snmp-server community public' in running_config:
            insecure_services.append('SNMP with public community')
        
        if insecure_services:
            findings['insecure_services'] = {
                'status': 'high',
                'details': f"Insecure services enabled: {', '.join(insecure_services)}",
                'recommendation': SECURITY_CHECKS['insecure_services']['recommendation'],
                'reference': SECURITY_CHECKS['insecure_services']['reference']
            }
        
        # Check 4: Unsecured interfaces
        unsecured_interfaces = []
        for interface in config_data.get('interfaces', []):
            if interface.get('status') == 'up':
                interface_name = interface.get('name', '')
                if not re.search(rf'{re.escape(interface_name)}.*access-group', running_config):
                    unsecured_interfaces.append(interface_name)
        
        if unsecured_interfaces:
            findings['unsecured_interfaces'] = {
                'status': 'high',
                'details': f"Interfaces without ACLs: {', '.join(unsecured_interfaces)}",
                'recommendation': SECURITY_CHECKS['unsecured_interfaces']['recommendation'],
                'reference': SECURITY_CHECKS['unsecured_interfaces']['reference']
            }
        
        details = {
            'checks_performed': list(SECURITY_CHECKS.keys()),
            'issues_found': len(findings)
        }
        
        return (True, findings, details, None)
        
    except Exception as e:
        return (False, {}, {'checks_attempted': list(SECURITY_CHECKS.keys())}, str(e))

# Phase 5: Reporting and Recommendations
def execute_phase5_reporting(device, phase_results, test_mode=False):
    """
    Generate a final report with security recommendations
    Returns a tuple of (success, report_data, details, error)
    """
    hostname = device.get('hostname')
    ip = device.get('ip')
    
    # Extract results from previous phases
    connectivity_result = phase_results.get('connectivity', (False, {}, "Phase not executed"))
    authentication_result = phase_results.get('authentication', (False, None, {}, "Phase not executed"))
    config_audit_result = phase_results.get('config_audit', (False, None, {}, "Phase not executed"))
    risk_assessment_result = phase_results.get('risk_assessment', (False, {}, {}, "Phase not executed"))
    
    # Create report data structure
    report_data = {
        'device': {
            'hostname': hostname,
            'ip': ip,
            'device_type': device.get('device_type', 'Unknown')
        },
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'summary': {
            'connectivity': connectivity_result[0],
            'authentication': authentication_result[0],
            'config_audit': config_audit_result[0],
            'risk_assessment': risk_assessment_result[0]
        },
        'risk_findings': risk_assessment_result[1] if risk_assessment_result[0] else {},
        'recommendations': []
    }
    
    # Generate recommendations based on findings
    if report_data['risk_findings']:
        for check_id, finding in report_data['risk_findings'].items():
            report_data['recommendations'].append({
                'priority': len(report_data['recommendations']) + 1,
                'text': finding.get('recommendation', SECURITY_CHECKS.get(check_id, {}).get('recommendation', '')),
                'severity': finding.get('status', 'medium'),
                'reference': finding.get('reference', SECURITY_CHECKS.get(check_id, {}).get('reference', ''))
            })
    
    # Add standard recommendations if none were generated
    if not report_data['recommendations']:
        if report_data['summary']['connectivity'] and report_data['summary']['authentication']:
            report_data['recommendations'].append({
                'priority': 1,
                'text': "Implement regular security audits and monitoring",
                'severity': 'medium',
                'reference': "NIST SP 800-53: CA-7"
            })
    
    details = {
        'report_type': 'security',
        'findings_count': len(report_data['risk_findings']),
        'recommendations_count': len(report_data['recommendations'])
    }
    
    return (True, report_data, details, None)

# Main function to execute all 5 phases for a device
def execute_all_phases(device, test_mode=False):
    """Execute all 5 phases of the security audit for a single device"""
    audit_result = AuditResult(
        device_info={
            'hostname': device.get('hostname'),
            'ip': device.get('ip'),
            'device_type': device.get('device_type', 'Unknown')
        },
        audit_type="security"
    )
    
    phase_results = {}
    connection = None
    
    # Phase 1: Connectivity Verification
    print(f"  {Fore.CYAN}⏳ Phase 1: Connectivity Verification{Style.RESET_ALL}")
    success, details, error = execute_phase1_connectivity(device, test_mode)
    phase_results['connectivity'] = (success, details, error)
    
    audit_result.add_phase_result(
        'connectivity', 
        'Success' if success else 'Failed',
        details,
        error
    )
    
    if success:
        print(f"  {Fore.GREEN}✓ Phase 1: Connectivity successful{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}✗ Phase 1: Connectivity failed: {error}{Style.RESET_ALL}")
    
    # Phase 2: Authentication Testing (only if connectivity successful)
    if success:
        print(f"  {Fore.CYAN}⏳ Phase 2: Authentication Testing{Style.RESET_ALL}")
        success, connection, details, error = execute_phase2_authentication(device, None, test_mode)
        phase_results['authentication'] = (success, connection, details, error)
        
        audit_result.add_phase_result(
            'authentication', 
            'Success' if success else 'Failed',
            details,
            error
        )
        
        if success:
            print(f"  {Fore.GREEN}✓ Phase 2: Authentication successful{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}✗ Phase 2: Authentication failed: {error}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.YELLOW}⚠ Phase 2: Authentication skipped due to connectivity failure{Style.RESET_ALL}")
        phase_results['authentication'] = (False, None, {}, "Skipped due to connectivity failure")
        audit_result.add_phase_result(
            'authentication', 
            'Skipped',
            {},
            "Skipped due to connectivity failure"
        )
    
    # Phase 3: Configuration Audit (only if authentication successful)
    if phase_results['authentication'][0]:
        print(f"  {Fore.CYAN}⏳ Phase 3: Configuration Audit{Style.RESET_ALL}")
        success, config_data, details, error = execute_phase3_config_audit(
            device, 
            phase_results['authentication'][1],
            test_mode
        )
        phase_results['config_audit'] = (success, config_data, details, error)
        
        audit_result.add_phase_result(
            'config_audit', 
            'Success' if success else 'Failed',
            details,
            error
        )
        
        if success:
            print(f"  {Fore.GREEN}✓ Phase 3: Configuration audit successful{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}✗ Phase 3: Configuration audit failed: {error}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.YELLOW}⚠ Phase 3: Configuration audit skipped due to authentication failure{Style.RESET_ALL}")
        phase_results['config_audit'] = (False, None, {}, "Skipped due to authentication failure")
        audit_result.add_phase_result(
            'config_audit', 
            'Skipped',
            {},
            "Skipped due to authentication failure"
        )
    
    # Phase 4: Risk Assessment (try even if config audit failed)
    print(f"  {Fore.CYAN}⏳ Phase 4: Risk Assessment{Style.RESET_ALL}")
    config_data = phase_results['config_audit'][1] if phase_results['config_audit'][0] else None
    success, findings, details, error = execute_phase4_risk_assessment(device, config_data, test_mode)
    phase_results['risk_assessment'] = (success, findings, details, error)
    
    audit_result.add_phase_result(
        'risk_assessment', 
        'Success' if success else 'Failed',
        details,
        error
    )
    
    if success:
        print(f"  {Fore.GREEN}✓ Phase 4: Risk assessment successful{Style.RESET_ALL}")
        if findings:
            print(f"    {Fore.YELLOW}⚠ Found {len(findings)} potential security issues{Style.RESET_ALL}")
            for check_id, finding in findings.items():
                severity_color = {
                    'critical': Fore.RED,
                    'high': Fore.RED,
                    'medium': Fore.YELLOW,
                    'low': Fore.CYAN
                }.get(finding.get('status', 'medium'), Fore.YELLOW)
                
                print(f"    {severity_color}• {check_id}: {finding.get('details')}{Style.RESET_ALL}")
        else:
            print(f"    {Fore.GREEN}✓ No security issues found{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}✗ Phase 4: Risk assessment failed: {error}{Style.RESET_ALL}")
    
    # Phase 5: Reporting and Recommendations
    print(f"  {Fore.CYAN}⏳ Phase 5: Reporting and Recommendations{Style.RESET_ALL}")
    success, report_data, details, error = execute_phase5_reporting(device, phase_results, test_mode)
    phase_results['reporting'] = (success, report_data, details, error)
    
    audit_result.add_phase_result(
        'reporting', 
        'Success' if success else 'Failed',
        details,
        error
    )
    
    if success:
        print(f"  {Fore.GREEN}✓ Phase 5: Reporting successful{Style.RESET_ALL}")
        
        # Add recommendations to audit result
        for recommendation in report_data.get('recommendations', []):
            audit_result.add_recommendation(
                recommendation.get('text', ''),
                recommendation.get('severity', 'medium'),
                recommendation.get('reference', '')
            )
            
            severity_color = {
                'critical': Fore.RED,
                'high': Fore.RED,
                'medium': Fore.YELLOW,
                'low': Fore.CYAN
            }.get(recommendation.get('severity', 'medium'), Fore.YELLOW)
            
            print(f"    {severity_color}• Recommendation: {recommendation.get('text')}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}✗ Phase 5: Reporting failed: {error}{Style.RESET_ALL}")
    
    # Close connection if it was opened
    if connection and not test_mode:
        try:
            connection.disconnect()
        except:
            pass
    
    return audit_result

# Main execution - this only runs when the module is executed directly
if __name__ == "__main__":
    print(f"{Fore.CYAN}Security Audit Phases Module v{VERSION}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}This module provides phase functions for the security audit process.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}It should not be run directly - import it in other modules instead.{Style.RESET_ALL}")

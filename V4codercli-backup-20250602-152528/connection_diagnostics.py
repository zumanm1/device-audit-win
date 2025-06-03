#!/usr/bin/env python3
"""
Connection Diagnostics for V4codercli
Comprehensive connectivity troubleshooting for EVE-NG and production environments
"""

import subprocess
import socket
import json
import csv
from pathlib import Path
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    """Print a formatted header."""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.WHITE}{title:^70}{Colors.END}")
    print(f"{Colors.CYAN}{'='*70}{Colors.END}")

def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

class RouterConnectivityDiagnostics:
    """Comprehensive router connectivity diagnostics."""
    
    def __init__(self):
        self.results = {}
        self.ssh_config_path = Path(__file__).parent / "cisco_ssh_config"
        self.common_ports = [22, 23, 80, 443, 830, 8080]
        self.common_credentials = [
            ('cisco', 'cisco'),
            ('admin', 'admin'),
            ('admin', ''),
            ('root', 'root'),
            ('user', 'user'),
            ('lab', 'lab123'),
            ('eve', 'eve')
        ]
    
    def discover_network_devices(self, network="172.16.39.0/24"):
        """Discover devices in the network."""
        print_info(f"Discovering devices in network {network}")
        
        try:
            # Run nmap to discover hosts
            cmd = ['nmap', '-sn', network]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            devices = []
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Nmap scan report for' in line:
                        # Extract IP address
                        parts = line.split()
                        if len(parts) >= 5:
                            ip = parts[-1].strip('()')
                            if ip.startswith('172.16.39.'):
                                devices.append(ip)
                
                print_success(f"Discovered {len(devices)} devices")
                return devices
            else:
                print_error("Network discovery failed")
                return []
                
        except Exception as e:
            print_error(f"Network discovery error: {e}")
            return []
    
    def scan_device_ports(self, host, ports=None):
        """Scan ports on a device."""
        if ports is None:
            ports = self.common_ports
        
        print_info(f"Scanning ports on {host}")
        
        try:
            port_list = ','.join(map(str, ports))
            cmd = ['nmap', '-p', port_list, host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            open_ports = []
            filtered_ports = []
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if '/tcp' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            port = parts[0].split('/')[0]
                            state = parts[1]
                            if state == 'open':
                                open_ports.append(int(port))
                            elif state == 'filtered':
                                filtered_ports.append(int(port))
                
                return {
                    'open': open_ports,
                    'filtered': filtered_ports,
                    'host': host
                }
            else:
                print_error(f"Port scan failed for {host}")
                return {'open': [], 'filtered': [], 'host': host}
                
        except Exception as e:
            print_error(f"Port scan error for {host}: {e}")
            return {'open': [], 'filtered': [], 'host': host}
    
    def test_ssh_with_algorithms(self, host, username, password, port=22):
        """Test SSH connection with various algorithm combinations."""
        print_info(f"Testing SSH to {host}:{port} as {username}")
        
        # Multiple algorithm combinations to try
        algorithm_sets = [
            # Modern algorithms first
            {
                'kex': 'diffie-hellman-group14-sha256,diffie-hellman-group16-sha512',
                'ciphers': 'aes128-ctr,aes192-ctr,aes256-ctr',
                'macs': 'hmac-sha2-256,hmac-sha2-512'
            },
            # Legacy algorithms
            {
                'kex': 'diffie-hellman-group1-sha1,diffie-hellman-group14-sha1',
                'ciphers': 'aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc',
                'macs': 'hmac-sha1,hmac-sha1-96'
            },
            # Very old algorithms
            {
                'kex': 'diffie-hellman-group1-sha1',
                'ciphers': '3des-cbc,aes128-cbc',
                'macs': 'hmac-sha1'
            }
        ]
        
        for i, alg_set in enumerate(algorithm_sets):
            try:
                print_info(f"Trying algorithm set {i+1}/3...")
                
                ssh_cmd = [
                    'sshpass', '-p', password,
                    'ssh',
                    '-F', str(self.ssh_config_path),
                    '-p', str(port),
                    '-o', 'ConnectTimeout=10',
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    '-o', f'KexAlgorithms=+{alg_set["kex"]}',
                    '-o', f'Ciphers=+{alg_set["ciphers"]}',
                    '-o', f'MACs=+{alg_set["macs"]}',
                    '-o', 'HostKeyAlgorithms=+ssh-rsa,ssh-dss',
                    f'{username}@{host}',
                    'show version | include Software'
                ]
                
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    print_success(f"SSH successful with algorithm set {i+1}")
                    return {
                        'success': True,
                        'algorithm_set': i+1,
                        'algorithms': alg_set,
                        'output': result.stdout.strip(),
                        'username': username,
                        'host': host,
                        'port': port
                    }
                else:
                    error_msg = result.stderr.strip()
                    if 'Connection refused' in error_msg:
                        print_error(f"SSH connection refused on {host}:{port}")
                        break
                    elif 'Connection timed out' in error_msg:
                        print_error(f"SSH connection timeout on {host}:{port}")
                        break
                    else:
                        print_warning(f"Algorithm set {i+1} failed: {error_msg[:100]}")
                        
            except subprocess.TimeoutExpired:
                print_warning(f"SSH timeout with algorithm set {i+1}")
                continue
            except Exception as e:
                print_warning(f"SSH error with algorithm set {i+1}: {e}")
                continue
        
        return {
            'success': False,
            'host': host,
            'port': port,
            'username': username,
            'error': 'All algorithm sets failed'
        }
    
    def test_telnet_connection(self, host, username, password, port=23):
        """Test Telnet connection if SSH fails."""
        print_info(f"Testing Telnet to {host}:{port}")
        
        try:
            # Simple telnet test using expect-like functionality
            import pexpect
            
            try:
                child = pexpect.spawn(f'telnet {host} {port}', timeout=10)
                
                # Look for login prompt
                index = child.expect(['Username:', 'login:', 'Password:', pexpect.TIMEOUT], timeout=10)
                
                if index in [0, 1]:  # Username prompt
                    child.sendline(username)
                    child.expect(['Password:', pexpect.TIMEOUT], timeout=5)
                    child.sendline(password)
                elif index == 2:  # Password prompt only
                    child.sendline(password)
                
                # Look for command prompt
                child.expect(['>', '#', pexpect.TIMEOUT], timeout=10)
                
                # Send test command
                child.sendline('show version | include Software')
                child.expect(['>', '#', pexpect.TIMEOUT], timeout=5)
                
                output = child.before.decode('utf-8')
                child.close()
                
                print_success(f"Telnet connection successful to {host}")
                return {
                    'success': True,
                    'protocol': 'telnet',
                    'host': host,
                    'port': port,
                    'username': username,
                    'output': output
                }
                
            except pexpect.exceptions.TIMEOUT:
                print_error(f"Telnet timeout on {host}:{port}")
                return {'success': False, 'error': 'timeout'}
            except pexpect.exceptions.EOF:
                print_error(f"Telnet connection closed by {host}")
                return {'success': False, 'error': 'connection closed'}
                
        except ImportError:
            print_warning("pexpect not available, installing...")
            try:
                subprocess.run(['pip3', 'install', 'pexpect'], check=True)
                print_success("pexpect installed, please run again")
            except:
                print_error("Could not install pexpect automatically")
            return {'success': False, 'error': 'pexpect not available'}
        except Exception as e:
            print_error(f"Telnet error: {e}")
            return {'success': False, 'error': str(e)}
    
    def diagnose_device(self, host):
        """Comprehensive diagnosis of a single device."""
        print_header(f"Diagnosing Device: {host}")
        
        device_result = {
            'host': host,
            'reachable': False,
            'ports': {},
            'connections': {},
            'working_credentials': [],
            'protocols': []
        }
        
        # Step 1: Check if host is reachable
        try:
            result = subprocess.run(['ping', '-c', '2', '-W', '3', host], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                device_result['reachable'] = True
                print_success(f"Host {host} is reachable via ping")
            else:
                print_info(f"Host {host} doesn't respond to ping (may be filtered)")
        except:
            print_warning(f"Ping test failed for {host}")
        
        # Step 2: Port scan
        port_results = self.scan_device_ports(host)
        device_result['ports'] = port_results
        
        if port_results['open']:
            print_success(f"Open ports found: {port_results['open']}")
        if port_results['filtered']:
            print_warning(f"Filtered ports: {port_results['filtered']}")
        
        # Step 3: Test connections on open ports
        for port in port_results['open']:
            if port == 22:  # SSH
                for username, password in self.common_credentials:
                    ssh_result = self.test_ssh_with_algorithms(host, username, password, port)
                    if ssh_result['success']:
                        device_result['working_credentials'].append((username, password))
                        device_result['protocols'].append('ssh')
                        device_result['connections']['ssh'] = ssh_result
                        print_success(f"SSH working with {username}/{password}")
                        break
                        
            elif port == 23:  # Telnet
                for username, password in self.common_credentials:
                    telnet_result = self.test_telnet_connection(host, username, password, port)
                    if telnet_result['success']:
                        device_result['working_credentials'].append((username, password))
                        device_result['protocols'].append('telnet')
                        device_result['connections']['telnet'] = telnet_result
                        print_success(f"Telnet working with {username}/{password}")
                        break
        
        return device_result
    
    def generate_v4cli_config(self, results):
        """Generate configuration for V4codercli based on diagnosis results."""
        print_header("Generating V4codercli Configuration")
        
        working_devices = []
        for result in results:
            if result['working_credentials']:
                working_devices.append(result)
        
        if not working_devices:
            print_error("No working devices found - cannot generate V4codercli config")
            return None
        
        # Generate devices.csv for V4codercli
        csv_file = Path('devices_diagnosed.csv')
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['device_name', 'ip_address', 'username', 'password', 'device_type', 'protocol'])
            
            for i, device in enumerate(working_devices):
                host = device['host']
                username, password = device['working_credentials'][0]  # Use first working credential
                protocol = device['protocols'][0]  # Use first working protocol
                device_name = f"Router_{host.split('.')[-1]}"
                device_type = "cisco_ios"  # Default assumption
                
                writer.writerow([device_name, host, username, password, device_type, protocol])
        
        print_success(f"Generated {csv_file} with {len(working_devices)} working devices")
        
        # Generate SSH config for legacy devices
        if any('ssh' in device['protocols'] for device in working_devices):
            self.generate_ssh_config()
        
        # Generate connection recommendations
        self.generate_connection_recommendations(working_devices)
        
        return csv_file
    
    def generate_ssh_config(self):
        """Generate optimized SSH configuration."""
        config_content = """# Optimized SSH Configuration for Cisco Devices
# Generated by V4codercli Connection Diagnostics

Host cisco-* 172.16.39.*
    # Legacy algorithm support for older Cisco devices
    KexAlgorithms +diffie-hellman-group1-sha1,diffie-hellman-group14-sha1,diffie-hellman-group14-sha256
    Ciphers +aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc,aes128-ctr,aes192-ctr,aes256-ctr
    MACs +hmac-sha1,hmac-sha1-96,hmac-sha2-256,hmac-sha2-512
    HostKeyAlgorithms +ssh-rsa,ssh-dss,rsa-sha2-256,rsa-sha2-512
    
    # Connection optimization
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ConnectTimeout 15
    ServerAliveInterval 30
    ServerAliveCountMax 3
    
    # Authentication settings
    PreferredAuthentications password,keyboard-interactive
    PasswordAuthentication yes
    PubkeyAuthentication no
    
    # Protocol settings
    Protocol 2
    
    # Disable features that may cause issues
    RequestTTY yes
    ForwardAgent no
    ForwardX11 no
    
    # Logging for debugging
    LogLevel INFO
"""
        
        with open('cisco_ssh_config_optimized', 'w') as f:
            f.write(config_content)
        
        print_success("Generated optimized SSH configuration: cisco_ssh_config_optimized")
    
    def generate_connection_recommendations(self, working_devices):
        """Generate connection recommendations."""
        print_header("Connection Recommendations")
        
        ssh_devices = [d for d in working_devices if 'ssh' in d['protocols']]
        telnet_devices = [d for d in working_devices if 'telnet' in d['protocols']]
        
        if ssh_devices:
            print_success(f"SSH Protocol: {len(ssh_devices)} devices")
            print_info("- Use enhanced SSH configuration for legacy algorithm support")
            print_info("- V4codercli will work with these devices")
            
        if telnet_devices:
            print_warning(f"Telnet Protocol: {len(telnet_devices)} devices")
            print_info("- Consider enabling SSH on these devices for better security")
            print_info("- V4codercli can be configured to use Telnet if needed")
        
        print_info("\nNext Steps:")
        print_info("1. Use the generated devices_diagnosed.csv file")
        print_info("2. Update V4codercli connection settings")
        print_info("3. Test with: python3 start_rr4_cli_enhanced.py --option 6")

def main():
    """Main function."""
    print_header("V4codercli Connection Diagnostics")
    print_info("Comprehensive router connectivity analysis for EVE-NG environments")
    
    diagnostics = RouterConnectivityDiagnostics()
    
    # Discover devices
    devices = diagnostics.discover_network_devices()
    
    if not devices:
        print_error("No devices discovered. Check network configuration.")
        return False
    
    # Focus on the specific routers mentioned by user
    target_devices = ['172.16.39.115', '172.16.39.116', '172.16.39.117']
    
    # Add any other discovered devices that look like routers
    for device in devices:
        if device.startswith('172.16.39.') and device not in target_devices:
            # Skip management IPs like .1, .2, .254
            last_octet = int(device.split('.')[-1])
            if last_octet not in [1, 2, 140, 254]:  # Skip gateway, host IPs
                target_devices.append(device)
    
    print_info(f"Testing {len(target_devices)} target devices")
    
    # Diagnose each device
    results = []
    for device in target_devices[:10]:  # Limit to first 10 for time
        try:
            result = diagnostics.diagnose_device(device)
            results.append(result)
        except KeyboardInterrupt:
            print_warning("Diagnostic interrupted by user")
            break
        except Exception as e:
            print_error(f"Error diagnosing {device}: {e}")
    
    # Generate configuration
    config_file = diagnostics.generate_v4cli_config(results)
    
    # Summary
    working_count = len([r for r in results if r['working_credentials']])
    total_count = len(results)
    
    print_header("DIAGNOSTIC SUMMARY")
    print_info(f"Total devices tested: {total_count}")
    print_success(f"Working devices: {working_count}")
    
    if working_count > 0:
        print_success("Router connectivity issues have been resolved!")
        print_info("V4codercli can now connect to the working devices.")
        return True
    else:
        print_error("No working router connections found.")
        print_warning("Check device configurations and network access.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\nDiagnostics interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1) 
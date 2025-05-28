#!/usr/bin/env python3
"""
Network Audit Tool - Connectivity Audit Module (v3.11)

This module focuses specifically on network connectivity testing:
- ICMP ping testing
- TCP port connectivity testing
- Traceroute analysis
- DNS resolution verification
- Basic latency and packet loss measurement

It can be run independently or as part of the comprehensive audit framework.
"""

import os
import sys
import csv
import time
import socket
import ipaddress
import subprocess
import datetime
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import core functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from audit_core import (
        VERSION, ensure_directories, setup_logging, CredentialManager, 
        prompt_for_master_password, AuditResult, AuditReport,
        Fore, Style, colorama_available
    )
except ImportError as e:
    print(f"Error importing audit_core module: {e}")
    print("Make sure audit_core.py is in the same directory.")
    sys.exit(1)

# Set up module-specific constants
MODULE_NAME = "Connectivity Audit"
AUDIT_TYPE = "connectivity"

# Configure logger
logger, log_file = setup_logging(f"connectivity_audit_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
if not logger:
    print("Failed to set up logging. Exiting.")
    sys.exit(1)

class ConnectivityAuditor:
    """Handles connectivity auditing for network devices"""
    
    def __init__(self, test_mode=False):
        """Initialize the connectivity auditor"""
        self.test_mode = test_mode
        self.devices = []
        self.results = []
        self.timestamp = datetime.datetime.now()
        
        # Print banner
        self.print_banner()
    
    def print_banner(self):
        """Print the module banner"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}NETWORK AUDIT TOOL - {MODULE_NAME} v{VERSION}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        if self.test_mode:
            print(f"{Fore.YELLOW}Running in TEST MODE with simulated responses{Style.RESET_ALL}")
        print(f"Started at: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log file: {log_file}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    def load_devices_from_csv(self, csv_file):
        """Load devices from a CSV file"""
        try:
            if not os.path.exists(csv_file):
                logger.error(f"CSV file not found: {csv_file}")
                print(f"{Fore.RED}Error: CSV file not found: {csv_file}{Style.RESET_ALL}")
                return False
            
            with open(csv_file, 'r') as f:
                # Read the first line to check the format
                header = f.readline().strip()
                f.seek(0)  # Reset file position
                
                # Check if this is routers01.csv format
                is_routers01_format = 'management_ip' in header and 'model_name' in header
                
                if is_routers01_format:
                    logger.info(f"Detected routers01.csv format")
                    print(f"{Fore.GREEN}Detected routers01.csv format{Style.RESET_ALL}")
                
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    # For routers01.csv format
                    if is_routers01_format:
                        if 'hostname' not in row or 'management_ip' not in row:
                            logger.warning(f"Skipping row in routers01.csv: missing required fields")
                            continue
                        
                        # Add device with routers01.csv specific field mapping
                        self.devices.append({
                            'hostname': row['hostname'],
                            'ip': row['management_ip'],
                            'description': f"WAN IP: {row.get('wan_ip', 'N/A')}",
                            'check_ports': [22, 23, 80, 443],  # Default ports to check
                            'dns_check': True,
                            'device_type': 'cisco_ios',
                            'username': 'admin',
                            'password': 'cisco123',
                            'secret': 'cisco123',
                            'model': row.get('model_name', 'Unknown')
                        })
                    # For standard format
                    else:
                        if 'hostname' not in row or 'ip' not in row:
                            logger.warning(f"Skipping row in CSV: missing required fields")
                            continue
                        
                        self.devices.append({
                            'hostname': row['hostname'],
                            'ip': row['ip'],
                            'description': row.get('description', ''),
                            'check_ports': [int(p.strip()) for p in row.get('check_ports', '22,23,80,443').split(',') if p.strip()],
                            'dns_check': row.get('dns_check', 'false').lower() == 'true',
                            'device_type': row.get('device_type', 'cisco_ios'),
                            'username': row.get('username', 'admin'),
                            'password': row.get('password', 'cisco123'),
                            'secret': row.get('secret', 'cisco123'),
                            'model': row.get('model', 'Unknown')
                        })
            
            if not self.devices:
                logger.warning(f"No valid devices found in {csv_file}")
                print(f"{Fore.YELLOW}Warning: No valid devices found in {csv_file}{Style.RESET_ALL}")
                if self.test_mode:
                    self.create_test_devices()
                    return True
                return False
            
            logger.info(f"Loaded {len(self.devices)} devices from {csv_file}")
            print(f"{Fore.GREEN}Successfully loaded {len(self.devices)} devices from {csv_file}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading devices from CSV: {e}")
            print(f"{Fore.RED}Error loading devices from CSV: {e}{Style.RESET_ALL}")
            if self.test_mode:
                self.create_test_devices()
                return True
            return False
    
    def create_test_devices(self):
        """Create sample test devices for test mode"""
        logger.info("Test mode: Creating sample test data for devices")
        print(f"{Fore.YELLOW}Test mode: Creating sample test data{Style.RESET_ALL}")
        
        # Define sample test devices
        self.devices = [
            {'hostname': 'router1.example.com', 'ip': '192.168.1.1', 'description': 'Core Router', 
             'check_ports': [22, 80, 443], 'dns_check': True},
            {'hostname': 'router2.example.com', 'ip': '192.168.1.2', 'description': 'Distribution Router', 
             'check_ports': [22, 23, 80], 'dns_check': True},
            {'hostname': 'switch1.example.com', 'ip': '192.168.1.10', 'description': 'Access Switch', 
             'check_ports': [22, 23], 'dns_check': False},
            {'hostname': 'switch2.example.com', 'ip': '192.168.1.11', 'description': 'Access Switch', 
             'check_ports': [22, 23], 'dns_check': False},
            {'hostname': 'firewall.example.com', 'ip': '192.168.1.254', 'description': 'Edge Firewall', 
             'check_ports': [22, 443, 8443], 'dns_check': True}
        ]
        
        # Create a sample CSV file for reference
        sample_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 'data', 'sample_devices.csv')
        try:
            with open(sample_csv, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['hostname', 'ip', 'description', 'check_ports', 'dns_check'])
                writer.writeheader()
                for device in self.devices:
                    writer.writerow({
                        'hostname': device['hostname'],
                        'ip': device['ip'],
                        'description': device['description'],
                        'check_ports': ','.join(str(p) for p in device['check_ports']),
                        'dns_check': 'true' if device['dns_check'] else 'false'
                    })
            logger.info(f"Created sample device CSV file: {sample_csv}")
            print(f"{Fore.GREEN}Created sample device CSV file: {sample_csv}{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Error creating sample CSV: {e}")
        
        print(f"Using {len(self.devices)} sample test devices:")
        for device in self.devices:
            print(f"  - {device['hostname']} ({device['ip']}) - {device['description']}")
        
        return True
    
    def check_ping(self, ip, count=4, timeout=2):
        """Test connectivity to a device with ICMP ping
        Cross-platform compatible with Windows and Ubuntu"""
        if self.test_mode:
            # In test mode, simulate results based on IP pattern
            success = int(ip.split('.')[-1]) % 10 != 0  # Simulate failure for IPs ending in 0
            rtt_min, rtt_avg, rtt_max = 10.2, 15.7, 22.3
            packet_loss = 0 if success else 100
            ttl = 64
            
            return {
                'success': success,
                'packets_sent': count,
                'packets_received': count if success else 0,
                'packet_loss_percent': packet_loss,
                'rtt_min_ms': rtt_min if success else None,
                'rtt_avg_ms': rtt_avg if success else None,
                'rtt_max_ms': rtt_max if success else None,
                'ttl': ttl if success else None
            }
        
        try:
            # Determine platform for correct ping command format
            platform_system = platform.system().lower()
            
            # Different ping command parameters based on OS
            if platform_system == "windows":
                # Windows ping uses -n for count and -w for timeout in milliseconds
                ping_cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), ip]
            elif platform_system in ["linux", "darwin"]:  # Linux or macOS
                # Linux/Unix ping uses -c for count and -W for timeout in seconds
                ping_cmd = ["ping", "-c", str(count), "-W", str(timeout), ip]
            else:
                # Default to Linux-style for other OSes
                logger.warning(f"Unrecognized OS: {platform_system}, using Linux-style ping command")
                ping_cmd = ["ping", "-c", str(count), "-W", str(timeout), ip]
                
            # Log the ping command being used
            logger.debug(f"Running ping command: {' '.join(ping_cmd)}")
            
            # Execute ping command
            result = subprocess.run(ping_cmd, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
            
            # Parse ping output
            output = result.stdout
            
            # Initialize result values
            success = result.returncode == 0
            packets_sent = count
            packets_received = 0
            packet_loss = 100
            rtt_min = rtt_avg = rtt_max = None
            ttl = None
            error_msg = None
            
            # Log the ping output for debugging
            logger.debug(f"Ping output for {ip}:\n{output}")
            
            # Parse packet statistics based on OS
            platform_system = platform.system().lower()
            
            if platform_system == "windows":
                # Windows ping output parsing
                if "Packets: Sent = " in output:
                    stats_line = re.search(r"Packets: Sent = (\d+), Received = (\d+), Lost = (\d+) \((\d+)% loss\)", output)
                    if stats_line:
                        packets_sent = int(stats_line.group(1))
                        packets_received = int(stats_line.group(2))
                        packet_loss = int(stats_line.group(4))
                
                if "Minimum = " in output:
                    # Handle both integer and decimal formats in Windows output
                    rtt_line = re.search(r"Minimum = ([\d.]+)ms, Maximum = ([\d.]+)ms, Average = ([\d.]+)ms", output)
                    if rtt_line:
                        rtt_min = float(rtt_line.group(1))
                        rtt_max = float(rtt_line.group(2))
                        rtt_avg = float(rtt_line.group(3))
                
                # Extract TTL from Windows output
                ttl_match = re.search(r"TTL=(\d+)", output)
                if ttl_match:
                    ttl = int(ttl_match.group(1))
                    
                # Check for specific Windows error messages
                if "could not find host" in output.lower() or "could not resolve target" in output.lower():
                    error_msg = "Could not resolve hostname"
                elif "Request timed out" in output:
                    error_msg = "Request timed out"
                    
            elif platform_system in ["linux", "darwin"]:  # Linux or macOS
                # Linux/Unix ping output parsing
                if "packets transmitted" in output:
                    stats_line = re.search(r"(\d+) packets transmitted, (\d+) received.+?([\d.]+)% packet loss", output)
                    if stats_line:
                        packets_sent = int(stats_line.group(1))
                        packets_received = int(stats_line.group(2))
                        packet_loss = float(stats_line.group(3))
                
                if "min/avg/max" in output:
                    rtt_line = re.search(r"min/avg/max(?:/mdev)? = ([\d.]+)/([\d.]+)/([\d.]+)", output)
                    if rtt_line:
                        rtt_min = float(rtt_line.group(1))
                        rtt_avg = float(rtt_line.group(2))
                        rtt_max = float(rtt_line.group(3))
                
                # Extract TTL from Linux/Unix output
                ttl_match = re.search(r"ttl=(\d+)", output, re.IGNORECASE)
                if ttl_match:
                    ttl = int(ttl_match.group(1))
                    
                # Check for specific Linux error messages
                if "unknown host" in output.lower():
                    error_msg = "Unknown host"
                elif "Name or service not known" in output:
                    error_msg = "Name or service not known"
                elif "100% packet loss" in output:
                    error_msg = "100% packet loss"
            else:
                # Generic parsing for other platforms
                logger.warning(f"Using generic ping output parsing for platform: {platform_system}")
                # Try both Windows and Linux patterns
                stats_line = re.search(r"(\d+) packets transmitted, (\d+) received.+?([\d.]+)% packet loss", output)
                if stats_line:
                    packets_sent = int(stats_line.group(1))
                    packets_received = int(stats_line.group(2))
                    packet_loss = float(stats_line.group(3))
                else:
                    # Try Windows pattern
                    stats_line = re.search(r"Packets: Sent = (\d+), Received = (\d+), Lost = (\d+) \((\d+)% loss\)", output)
                    if stats_line:
                        packets_sent = int(stats_line.group(1))
                        packets_received = int(stats_line.group(2))
                        packet_loss = int(stats_line.group(4))
            
            return {
                'success': success,
                'packets_sent': packets_sent,
                'packets_received': packets_received,
                'packet_loss_percent': packet_loss,
                'rtt_min_ms': rtt_min,
                'rtt_avg_ms': rtt_avg,
                'rtt_max_ms': rtt_max,
                'ttl': ttl,
                'error': error_msg
            }
            
        except Exception as e:
            logger.error(f"Error performing ping to {ip}: {e}")
            return {
                'success': False,
                'error': str(e),
                'packets_sent': count,
                'packets_received': 0,
                'packet_loss_percent': 100,
                'rtt_min_ms': None,
                'rtt_avg_ms': None,
                'rtt_max_ms': None,
                'ttl': None
            }
    
    def check_port(self, ip, port, timeout=2, retries=2, retry_delay=1):
        """
        Check if a TCP port is open on the target device
        
        Args:
            ip (str): IP address to check
            port (int): Port number to check
            timeout (int): Connection timeout in seconds
            retries (int): Number of retry attempts
            retry_delay (float): Delay between retries in seconds
            
        Returns:
            dict: Result dictionary with port status information
        """
        if self.test_mode:
            # In test mode, simulate results
            # Common ports are usually open, others are random
            common_ports = [22, 80, 443, 8080, 8443]
            success = port in common_ports
            
            return {
                'port': port,
                'open': success,
                'response_time_ms': 12.5 if success else None,
                'error': None if success else "Connection refused",
                'retries': 0
            }
        
        # Initialize retry counter
        retry_count = 0
        last_error = None
        
        # Try multiple times if configured
        while retry_count <= retries:
            sock = None
            try:
                # Create socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                # Record start time
                start_time = time.time()
                
                # Attempt to connect
                result = sock.connect_ex((ip, port))
                
                # Calculate response time
                response_time = (time.time() - start_time) * 1000  # convert to milliseconds
                
                # Check result
                if result == 0:
                    logger.info(f"Port {port} on {ip} is open (response time: {response_time:.2f} ms)")
                    return {
                        'port': port,
                        'open': True,
                        'response_time_ms': response_time,
                        'error': None,
                        'retries': retry_count
                    }
                else:
                    # If we have retries left, try again
                    last_error = os.strerror(result)
                    logger.debug(f"Port {port} check failed on attempt {retry_count+1}/{retries+1}: {last_error}")
                    retry_count += 1
                    
                    # If we have retries left, wait and continue
                    if retry_count <= retries:
                        time.sleep(retry_delay)
                        continue
                    
                    # Otherwise return the error
                    logger.info(f"Port {port} on {ip} is closed after {retry_count} attempts: {last_error}")
                    return {
                        'port': port,
                        'open': False,
                        'response_time_ms': None,
                        'error': last_error,
                        'retries': retry_count - 1
                    }
            
            except socket.timeout:
                last_error = "Connection timed out"
                logger.debug(f"Port {port} check timed out on attempt {retry_count+1}/{retries+1}")
                retry_count += 1
                
                # If we have retries left, wait and continue
                if retry_count <= retries:
                    time.sleep(retry_delay)
                    continue
                
                logger.info(f"Port {port} on {ip} timed out after {retry_count} attempts")
                return {
                    'port': port,
                    'open': False,
                    'response_time_ms': None,
                    'error': "Connection timed out",
                    'retries': retry_count - 1
                }
                
            except socket.gaierror:
                # DNS resolution error - no point in retrying
                logger.info(f"DNS resolution error for {ip}:{port}")
                return {
                    'port': port,
                    'open': False,
                    'response_time_ms': None,
                    'error': "DNS resolution failed",
                    'retries': retry_count
                }
                
            except ConnectionRefusedError:
                # Connection actively refused - port is definitely closed
                logger.info(f"Connection refused for {ip}:{port}")
                return {
                    'port': port,
                    'open': False,
                    'response_time_ms': None,
                    'error': "Connection refused",
                    'retries': retry_count
                }
                
            except Exception as e:
                last_error = str(e)
                logger.debug(f"Port {port} check failed with exception on attempt {retry_count+1}/{retries+1}: {last_error}")
                retry_count += 1
                
                # If we have retries left, wait and continue
                if retry_count <= retries:
                    time.sleep(retry_delay)
                    continue
                
                logger.info(f"Port {port} on {ip} check failed after {retry_count} attempts: {last_error}")
                return {
                    'port': port,
                    'open': False,
                    'response_time_ms': None,
                    'error': last_error,
                    'retries': retry_count - 1
                }
            finally:
                # Properly close the socket if it exists
                if sock:
                    try:
                        sock.close()
                    except Exception as e:
                        logger.debug(f"Error closing socket: {e}")
                        pass
    
    def check_dns(self, hostname, expected_ip=None):
        """Check if a hostname resolves to the expected IP address"""
        if self.test_mode:
            # In test mode, simulate DNS results
            resolved = True
            actual_ip = expected_ip or f"192.168.1.{hash(hostname) % 254 + 1}"
            
            return {
                'hostname': hostname,
                'resolved': resolved,
                'ip': actual_ip,
                'matches_expected': expected_ip is None or actual_ip == expected_ip,
                'error': None
            }
        
        try:
            # Resolve hostname
            info = socket.getaddrinfo(hostname, None)
            ip_addresses = [addr[4][0] for addr in info]
            
            # Get first IPv4 address
            actual_ip = next((ip for ip in ip_addresses if ':' not in ip), None)
            
            if not actual_ip:
                return {
                    'hostname': hostname,
                    'resolved': False,
                    'ip': None,
                    'matches_expected': False,
                    'error': "No IPv4 address found"
                }
            
            return {
                'hostname': hostname,
                'resolved': True,
                'ip': actual_ip,
                'matches_expected': expected_ip is None or actual_ip == expected_ip,
                'error': None
            }
        except Exception as e:
            return {
                'hostname': hostname,
                'resolved': False,
                'ip': None,
                'matches_expected': False,
                'error': str(e)
            }
    
    def audit_device(self, device):
        """Perform a comprehensive connectivity audit for a single device"""
        hostname = device['hostname']
        ip = device['ip']
        
        logger.info(f"Starting connectivity audit for {hostname} ({ip})")
        print(f"\n{Fore.CYAN}Auditing device: {hostname} ({ip}){Style.RESET_ALL}")
        
        # Create an audit result
        device_info = {
            'hostname': hostname,
            'ip': ip,
            'description': device.get('description', '')
        }
        
        audit_result = AuditResult(device_info, AUDIT_TYPE)
        
        # Phase 1: ICMP Ping Test
        print(f"  {Fore.CYAN}⏳ Testing ICMP connectivity...{Style.RESET_ALL}")
        ping_result = self.check_ping(ip)
        
        ping_status = "Success" if ping_result['success'] else "Failed"
        ping_details = {
            'packets_sent': ping_result['packets_sent'],
            'packets_received': ping_result['packets_received'],
            'packet_loss_percent': ping_result['packet_loss_percent']
        }
        
        if ping_result['success']:
            ping_details.update({
                'rtt_min_ms': ping_result['rtt_min_ms'],
                'rtt_avg_ms': ping_result['rtt_avg_ms'],
                'rtt_max_ms': ping_result['rtt_max_ms'],
                'ttl': ping_result['ttl']
            })
            print(f"  {Fore.GREEN}✓ ICMP ping successful{Style.RESET_ALL}")
            print(f"    - RTT min/avg/max: {ping_result['rtt_min_ms']}/{ping_result['rtt_avg_ms']}/{ping_result['rtt_max_ms']} ms")
            print(f"    - Packet loss: {ping_result['packet_loss_percent']}%")
        else:
            error_message = ping_result.get('error', 'Unknown error')
            ping_details['error'] = error_message
            print(f"  {Fore.RED}✗ ICMP ping failed: {error_message}{Style.RESET_ALL}")
        
        # Add ping result to audit
        audit_result.add_phase_result('icmp_ping', ping_status, ping_details)
        
        # Phase 2: TCP Port Testing
        print(f"  {Fore.CYAN}⏳ Testing TCP ports...{Style.RESET_ALL}")
        port_results = []
        
        for port in device['check_ports']:
            port_result = self.check_port(ip, port)
            port_results.append(port_result)
            
            if port_result['open']:
                retry_info = ""
                if port_result.get('retries', 0) > 0:
                    retry_info = f" after {port_result['retries']+1} attempts"
                print(f"    {Fore.GREEN}✓ Port {port} open{retry_info} (response time: {port_result['response_time_ms']:.2f} ms){Style.RESET_ALL}")
            else:
                retry_info = ""
                if port_result.get('retries', 0) > 0:
                    retry_info = f" after {port_result['retries']+1} attempts"
                print(f"    {Fore.RED}✗ Port {port} closed{retry_info} ({port_result['error']}){Style.RESET_ALL}")
        
        # Determine overall port check status
        open_ports = [r for r in port_results if r['open']]
        port_status = "Success" if open_ports else "Failed"
        port_details = {
            'ports_checked': len(port_results),
            'ports_open': len(open_ports),
            'open_ports': [r['port'] for r in open_ports]
        }
        
        # Add port results to audit
        audit_result.add_phase_result('tcp_ports', port_status, port_details)
        
        # Phase 3: DNS Resolution (if enabled)
        if device['dns_check']:
            print(f"  {Fore.CYAN}⏳ Testing DNS resolution...{Style.RESET_ALL}")
            dns_result = self.check_dns(hostname, ip)
            
            dns_status = "Success" if dns_result['resolved'] else "Failed"
            dns_details = {
                'hostname': hostname,
                'resolved_ip': dns_result['ip'],
                'matches_expected': dns_result['matches_expected']
            }
            
            if dns_result['error']:
                dns_details['error'] = dns_result['error']
            
            if dns_result['resolved']:
                if dns_result['matches_expected']:
                    print(f"    {Fore.GREEN}✓ DNS resolution successful: {hostname} -> {dns_result['ip']}{Style.RESET_ALL}")
                else:
                    print(f"    {Fore.YELLOW}⚠ DNS resolution returned unexpected IP: {dns_result['ip']} (expected {ip}){Style.RESET_ALL}")
            else:
                print(f"    {Fore.RED}✗ DNS resolution failed: {dns_result['error']}{Style.RESET_ALL}")
            
            # Add DNS result to audit
            audit_result.add_phase_result('dns_resolution', dns_status, dns_details)
        
        # Add recommendations based on findings
        if not ping_result['success']:
            audit_result.add_recommendation(
                "Device is not responding to ICMP ping. Check firewall settings or device status.",
                severity="high"
            )
        
        if not open_ports:
            audit_result.add_recommendation(
                "No open TCP ports found. Verify device is operational and accessible.",
                severity="high"
            )
        
        # SSH security recommendation
        if 23 in device['check_ports'] and any(r['port'] == 23 and r['open'] for r in port_results):
            audit_result.add_recommendation(
                "Telnet (port 23) is open. Consider disabling Telnet and using SSH for secure access.",
                severity="critical",
                reference="NIST SP 800-53: IA-2, AC-17"
            )
        
        # DNS mismatch recommendation
        if device['dns_check'] and dns_result['resolved'] and not dns_result['matches_expected']:
            audit_result.add_recommendation(
                f"DNS hostname resolves to {dns_result['ip']} but device is configured with IP {ip}. Update DNS records.",
                severity="medium"
            )
        
        logger.info(f"Completed connectivity audit for {hostname} ({ip})")
        self.results.append(audit_result)
        return audit_result
    
    def run_audit(self):
        """Run the connectivity audit for all devices"""
        if not self.devices:
            logger.error("No devices to audit")
            print(f"{Fore.RED}Error: No devices to audit. Please load devices first.{Style.RESET_ALL}")
            return False
        
        start_time = time.time()
        print(f"{Fore.CYAN}Starting connectivity audit for {len(self.devices)} devices...{Style.RESET_ALL}")
        logger.info(f"Starting connectivity audit for {len(self.devices)} devices")
        
        # Use ThreadPoolExecutor for parallel auditing
        with ThreadPoolExecutor(max_workers=min(10, len(self.devices))) as executor:
            future_to_device = {executor.submit(self.audit_device, device): device for device in self.devices}
            
            for future in as_completed(future_to_device):
                device = future_to_device[future]
                try:
                    result = future.result()
                    logger.info(f"Completed audit for {device['hostname']} ({device['ip']})")
                except Exception as e:
                    logger.error(f"Error auditing {device['hostname']} ({device['ip']}): {e}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed connectivity audit in {elapsed_time:.2f} seconds")
        print(f"\n{Fore.CYAN}Completed connectivity audit in {elapsed_time:.2f} seconds{Style.RESET_ALL}")
        
        return True
    
    def generate_reports(self):
        """Generate reports for the audit results"""
        if not self.results:
            logger.warning("No audit results to report")
            print(f"{Fore.YELLOW}Warning: No audit results to report{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.CYAN}Generating audit reports...{Style.RESET_ALL}")
        
        # Create a report
        report = AuditReport(self.results)
        
        # Generate all report formats
        report_files = report.generate_all_reports()
        
        # Print summary
        report.print_summary()
        
        return True


def main():
    """Main entry point for the connectivity audit module"""
    parser = argparse.ArgumentParser(description=f"Network Audit Tool - {MODULE_NAME} v{VERSION}")
    parser.add_argument("-t", "--test", action="store_true", help="Run in test mode with simulated responses")
    parser.add_argument("-c", "--csv", type=str, default="devices.csv", help="CSV file with device details")
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    # Create the auditor
    auditor = ConnectivityAuditor(test_mode=args.test)
    
    # Load devices
    if not auditor.load_devices_from_csv(args.csv):
        if not args.test:
            print(f"{Fore.RED}Failed to load devices. Exiting.{Style.RESET_ALL}")
            return 1
    
    # Run the audit
    if not auditor.run_audit():
        print(f"{Fore.RED}Failed to run audit. Exiting.{Style.RESET_ALL}")
        return 1
    
    # Generate reports
    auditor.generate_reports()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

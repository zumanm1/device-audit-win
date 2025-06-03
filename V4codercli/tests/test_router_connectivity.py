#!/usr/bin/env python3
"""
Router Connectivity Tester for V4codercli
Tests ping, SSH connectivity, and authentication for Cisco devices
Handles legacy SSH algorithm compatibility
"""

import subprocess
import socket
import time
import os
import sys
from pathlib import Path
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.WHITE}{title:^60}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")

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

def test_ping(host, count=3, timeout=5):
    """
    Test ICMP ping connectivity to a host.
    
    Args:
        host (str): Target host IP or hostname
        count (int): Number of ping packets
        timeout (int): Timeout in seconds
        
    Returns:
        dict: Test results with success status and details
    """
    print_info(f"Testing ping to {host}")
    
    try:
        # Run ping command
        cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        
        if result.returncode == 0:
            # Parse ping statistics
            lines = result.stdout.split('\n')
            stats_line = [line for line in lines if 'packet loss' in line]
            
            if stats_line:
                loss_info = stats_line[0]
                print_success(f"Ping to {host}: SUCCESS")
                print(f"   {loss_info.strip()}")
                return {
                    'success': True,
                    'host': host,
                    'details': loss_info.strip(),
                    'output': result.stdout
                }
            else:
                print_success(f"Ping to {host}: SUCCESS (no stats)")
                return {
                    'success': True,
                    'host': host,
                    'details': 'Ping successful',
                    'output': result.stdout
                }
        else:
            print_error(f"Ping to {host}: FAILED")
            print(f"   Error: {result.stderr.strip()}")
            return {
                'success': False,
                'host': host,
                'details': result.stderr.strip(),
                'output': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print_error(f"Ping to {host}: TIMEOUT")
        return {
            'success': False,
            'host': host,
            'details': 'Ping timeout',
            'output': ''
        }
    except Exception as e:
        print_error(f"Ping to {host}: ERROR - {str(e)}")
        return {
            'success': False,
            'host': host,
            'details': str(e),
            'output': ''
        }

def test_ssh_port(host, port=22, timeout=5):
    """
    Test SSH port connectivity using socket.
    
    Args:
        host (str): Target host
        port (int): SSH port (default 22)
        timeout (int): Connection timeout
        
    Returns:
        dict: Test results
    """
    print_info(f"Testing SSH port {port} on {host}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print_success(f"SSH port {port} on {host}: OPEN")
            return {
                'success': True,
                'host': host,
                'port': port,
                'details': f'Port {port} is open'
            }
        else:
            print_error(f"SSH port {port} on {host}: CLOSED")
            return {
                'success': False,
                'host': host,
                'port': port,
                'details': f'Port {port} is closed or filtered'
            }
            
    except Exception as e:
        print_error(f"SSH port test to {host}:{port}: ERROR - {str(e)}")
        return {
            'success': False,
            'host': host,
            'port': port,
            'details': str(e)
        }

def test_ssh_auth(host, username, password, timeout=10):
    """
    Test SSH authentication using legacy-compatible configuration.
    
    Args:
        host (str): Target host
        username (str): SSH username
        password (str): SSH password
        timeout (int): Connection timeout
        
    Returns:
        dict: Test results
    """
    print_info(f"Testing SSH authentication to {host} as {username}")
    
    # Path to our custom SSH config
    ssh_config_path = Path(__file__).parent / "cisco_ssh_config"
    
    try:
        # Create SSH command with legacy algorithm support
        ssh_cmd = [
            'ssh',
            '-F', str(ssh_config_path),
            '-o', 'ConnectTimeout=10',
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'KexAlgorithms=+diffie-hellman-group1-sha1,diffie-hellman-group14-sha1',
            '-o', 'Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc',
            '-o', 'MACs=+hmac-sha1,hmac-sha1-96',
            '-o', 'HostKeyAlgorithms=+ssh-rsa,ssh-dss',
            f'{username}@{host}',
            'show version | include Software'
        ]
        
        print_info(f"Attempting SSH connection with legacy algorithms...")
        
        # Use sshpass if available for password authentication
        if password:
            try:
                # Check if sshpass is available
                subprocess.run(['which', 'sshpass'], check=True, capture_output=True)
                ssh_cmd = ['sshpass', '-p', password] + ssh_cmd
                print_info("Using sshpass for password authentication")
            except subprocess.CalledProcessError:
                print_warning("sshpass not available, will attempt interactive auth")
        
        # Execute SSH command
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            print_success(f"SSH authentication to {host}: SUCCESS")
            print(f"   Command output: {result.stdout.strip()}")
            return {
                'success': True,
                'host': host,
                'username': username,
                'details': 'Authentication successful',
                'output': result.stdout.strip()
            }
        else:
            error_msg = result.stderr.strip()
            if 'no matching key exchange method' in error_msg:
                print_error(f"SSH to {host}: KEY EXCHANGE FAILURE")
                print_warning("Device requires legacy SSH algorithms")
            elif 'Permission denied' in error_msg:
                print_error(f"SSH to {host}: AUTHENTICATION FAILED")
                print_warning("Check username/password credentials")
            else:
                print_error(f"SSH to {host}: CONNECTION FAILED")
            
            print(f"   Error: {error_msg}")
            return {
                'success': False,
                'host': host,
                'username': username,
                'details': error_msg,
                'output': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print_error(f"SSH to {host}: TIMEOUT")
        return {
            'success': False,
            'host': host,
            'username': username,
            'details': 'SSH connection timeout',
            'output': ''
        }
    except Exception as e:
        print_error(f"SSH to {host}: ERROR - {str(e)}")
        return {
            'success': False,
            'host': host,
            'username': username,
            'details': str(e),
            'output': ''
        }

def test_single_device(device_info):
    """
    Test connectivity to a single device.
    
    Args:
        device_info (dict): Device information with host, username, password
        
    Returns:
        dict: Complete test results for the device
    """
    host = device_info['host']
    username = device_info.get('username', 'cisco')
    password = device_info.get('password', 'cisco')
    
    print_header(f"Testing Device: {host}")
    
    results = {
        'host': host,
        'ping': None,
        'ssh_port': None,
        'ssh_auth': None,
        'overall_status': 'UNKNOWN'
    }
    
    # Test 1: Ping connectivity
    ping_result = test_ping(host)
    results['ping'] = ping_result
    
    if not ping_result['success']:
        print_warning(f"Skipping SSH tests for {host} - ping failed")
        results['overall_status'] = 'PING_FAILED'
        return results
    
    # Test 2: SSH port connectivity
    ssh_port_result = test_ssh_port(host)
    results['ssh_port'] = ssh_port_result
    
    if not ssh_port_result['success']:
        print_warning(f"Skipping SSH auth test for {host} - port closed")
        results['overall_status'] = 'SSH_PORT_CLOSED'
        return results
    
    # Test 3: SSH authentication
    ssh_auth_result = test_ssh_auth(host, username, password)
    results['ssh_auth'] = ssh_auth_result
    
    # Determine overall status
    if ssh_auth_result['success']:
        results['overall_status'] = 'SUCCESS'
        print_success(f"Device {host}: ALL TESTS PASSED")
    elif ping_result['success'] and ssh_port_result['success']:
        results['overall_status'] = 'AUTH_FAILED'
        print_warning(f"Device {host}: Connectivity OK, Authentication failed")
    else:
        results['overall_status'] = 'CONNECTIVITY_FAILED'
        print_error(f"Device {host}: Connectivity issues")
    
    return results

def install_sshpass():
    """Install sshpass if not available."""
    try:
        subprocess.run(['which', 'sshpass'], check=True, capture_output=True)
        print_info("sshpass is already installed")
        return True
    except subprocess.CalledProcessError:
        print_info("Installing sshpass for password authentication...")
        try:
            # Try different package managers
            for cmd in [['apt-get', 'update', '&&', 'apt-get', 'install', '-y', 'sshpass'],
                       ['yum', 'install', '-y', 'sshpass'],
                       ['dnf', 'install', '-y', 'sshpass']]:
                try:
                    subprocess.run(cmd, check=True, capture_output=True, shell=True)
                    print_success("sshpass installed successfully")
                    return True
                except subprocess.CalledProcessError:
                    continue
            
            print_warning("Could not install sshpass automatically")
            return False
        except Exception as e:
            print_warning(f"Failed to install sshpass: {e}")
            return False

def generate_connectivity_report(results):
    """Generate a comprehensive connectivity report."""
    print_header("CONNECTIVITY TEST SUMMARY")
    
    total_devices = len(results)
    successful_devices = len([r for r in results if r['overall_status'] == 'SUCCESS'])
    
    print(f"\n{Colors.BOLD}Overall Results:{Colors.END}")
    print(f"  Total devices tested: {total_devices}")
    print(f"  Successful connections: {successful_devices}")
    print(f"  Success rate: {(successful_devices/total_devices*100):.1f}%")
    
    print(f"\n{Colors.BOLD}Device Status Breakdown:{Colors.END}")
    
    status_counts = {}
    for result in results:
        status = result['overall_status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        if status == 'SUCCESS':
            print_success(f"{status}: {count} devices")
        elif status in ['PING_FAILED', 'CONNECTIVITY_FAILED']:
            print_error(f"{status}: {count} devices")
        else:
            print_warning(f"{status}: {count} devices")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.END}")
    for result in results:
        host = result['host']
        status = result['overall_status']
        
        if status == 'SUCCESS':
            print_success(f"{host}: Ready for RR4 CLI")
        elif status == 'AUTH_FAILED':
            print_warning(f"{host}: Check credentials (ping/SSH port OK)")
        elif status == 'SSH_PORT_CLOSED':
            print_error(f"{host}: SSH service not available")
        elif status == 'PING_FAILED':
            print_error(f"{host}: Network connectivity issue")
        else:
            print_error(f"{host}: {status}")
    
    return successful_devices, total_devices

def main():
    """Main function to run connectivity tests."""
    print_header("RR4 CLI - Router Connectivity Tester")
    print_info("Testing connectivity to Cisco devices with legacy SSH support")
    
    # Install sshpass if needed
    install_sshpass()
    
    # Default test devices based on your environment
    test_devices = [
        {
            'host': '172.16.39.115',
            'username': 'cisco',
            'password': 'cisco'
        },
        {
            'host': '172.16.39.116', 
            'username': 'cisco',
            'password': 'cisco'
        },
        {
            'host': '172.16.39.117',
            'username': 'cisco',
            'password': 'cisco'
        }
    ]
    
    # Check if inventory file exists
    inventory_file = Path('devices.csv')
    if inventory_file.exists():
        print_info(f"Loading devices from {inventory_file}")
        # Add inventory loading logic here if needed
    
    print_info(f"Testing {len(test_devices)} devices...")
    
    # Test devices in parallel for faster execution
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_single_device, device): device for device in test_devices}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                device = futures[future]
                print_error(f"Error testing {device['host']}: {e}")
                results.append({
                    'host': device['host'],
                    'overall_status': 'ERROR',
                    'ping': None,
                    'ssh_port': None,
                    'ssh_auth': None
                })
    
    # Generate final report
    successful, total = generate_connectivity_report(results)
    
    # Provide recommendations
    print_header("RECOMMENDATIONS")
    
    if successful == total:
        print_success("All devices are ready for RR4 CLI data collection!")
        print_info("You can now run the RR4 CLI with confidence.")
    else:
        print_warning("Some devices have connectivity issues:")
        print_info("1. Check network connectivity for failed ping tests")
        print_info("2. Verify SSH service is enabled on devices")
        print_info("3. Confirm username/password credentials")
        print_info("4. Ensure devices support SSH version 2")
        
        # Check for common SSH issues
        auth_failed = [r for r in results if r['overall_status'] == 'AUTH_FAILED']
        if auth_failed:
            print_warning("For authentication failures, try:")
            print_info("  - Default Cisco credentials: cisco/cisco")
            print_info("  - Admin credentials: admin/admin")
            print_info("  - Check if AAA authentication is configured")
    
    return successful == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1) 
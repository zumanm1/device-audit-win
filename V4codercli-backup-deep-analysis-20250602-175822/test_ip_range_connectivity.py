#!/usr/bin/env python3
"""
Test IP Range 172.16.39.100 to 172.16.39.120 Connectivity
Quick connectivity test for specific IP range using existing V4codercli infrastructure
"""

import subprocess
import socket
import time
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def test_ping(host, timeout=3):
    """Test ping connectivity to a host."""
    try:
        cmd = ['ping', '-c', '1', '-W', str(timeout), host]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
        
        if result.returncode == 0:
            return {'success': True, 'host': host, 'status': 'UP'}
        else:
            return {'success': False, 'host': host, 'status': 'DOWN'}
            
    except subprocess.TimeoutExpired:
        return {'success': False, 'host': host, 'status': 'TIMEOUT'}
    except Exception as e:
        return {'success': False, 'host': host, 'status': f'ERROR: {str(e)}'}

def test_ssh_port(host, port=22, timeout=3):
    """Test SSH port connectivity using socket."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return {'success': True, 'host': host, 'port': port, 'status': 'OPEN'}
        else:
            return {'success': False, 'host': host, 'port': port, 'status': 'CLOSED/FILTERED'}
            
    except Exception as e:
        return {'success': False, 'host': host, 'port': port, 'status': f'ERROR: {str(e)}'}

def test_ssh_auth(host, username='cisco', password='cisco', timeout=10):
    """Test SSH authentication using legacy-compatible configuration."""
    ssh_config_path = Path(__file__).parent / "cisco_ssh_config"
    
    try:
        # Create SSH command with legacy algorithm support
        ssh_cmd = [
            'ssh',
            '-F', str(ssh_config_path) if ssh_config_path.exists() else '/dev/null',
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
        
        # Try with sshpass if available
        try:
            subprocess.run(['which', 'sshpass'], check=True, capture_output=True)
            ssh_cmd = ['sshpass', '-p', password] + ssh_cmd
        except subprocess.CalledProcessError:
            # sshpass not available, will try without password
            pass
        
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            return {
                'success': True,
                'host': host,
                'username': username,
                'status': 'AUTH_SUCCESS',
                'output': result.stdout.strip()[:100]  # First 100 chars
            }
        else:
            error_msg = result.stderr.strip()
            if 'no matching key exchange method' in error_msg:
                status = 'KEY_EXCHANGE_FAILED'
            elif 'Permission denied' in error_msg:
                status = 'AUTH_FAILED'
            elif 'Connection refused' in error_msg:
                status = 'CONNECTION_REFUSED'
            elif 'Connection timed out' in error_msg:
                status = 'CONNECTION_TIMEOUT'
            else:
                status = 'SSH_FAILED'
            
            return {
                'success': False,
                'host': host,
                'username': username,
                'status': status,
                'error': error_msg[:100]  # First 100 chars
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'host': host,
            'username': username,
            'status': 'SSH_TIMEOUT'
        }
    except Exception as e:
        return {
            'success': False,
            'host': host,
            'username': username,
            'status': f'SSH_ERROR: {str(e)}'
        }

def test_device_comprehensive(host):
    """Comprehensive test of a single device."""
    print_info(f"Testing {host}...")
    
    results = {
        'host': host,
        'ping': None,
        'ssh_port': None,
        'ssh_auth': None,
        'overall_status': 'UNKNOWN'
    }
    
    # Step 1: Ping test
    ping_result = test_ping(host)
    results['ping'] = ping_result
    
    if not ping_result['success']:
        results['overall_status'] = 'UNREACHABLE'
        return results
    
    # Step 2: SSH port test
    ssh_port_result = test_ssh_port(host)
    results['ssh_port'] = ssh_port_result
    
    if not ssh_port_result['success']:
        results['overall_status'] = 'SSH_PORT_CLOSED'
        return results
    
    # Step 3: SSH authentication test
    ssh_auth_result = test_ssh_auth(host)
    results['ssh_auth'] = ssh_auth_result
    
    if ssh_auth_result['success']:
        results['overall_status'] = 'FULLY_ACCESSIBLE'
    elif ssh_auth_result['status'] == 'KEY_EXCHANGE_FAILED':
        results['overall_status'] = 'SSH_ALGORITHM_ISSUE'
    elif ssh_auth_result['status'] == 'AUTH_FAILED':
        results['overall_status'] = 'AUTH_FAILED'
    else:
        results['overall_status'] = 'SSH_FAILED'
    
    return results

def generate_ip_range(start_ip, end_ip):
    """Generate IP addresses in range."""
    # Extract the last octet from start and end IPs
    start_parts = start_ip.split('.')
    end_parts = end_ip.split('.')
    
    if start_parts[:3] != end_parts[:3]:
        raise ValueError("IP addresses must be in the same subnet")
    
    base_ip = '.'.join(start_parts[:3])
    start_octet = int(start_parts[3])
    end_octet = int(end_parts[3])
    
    return [f"{base_ip}.{i}" for i in range(start_octet, end_octet + 1)]

def main():
    """Main function to test IP range."""
    print_header("V4codercli IP Range Connectivity Test")
    print_info("Testing IP range: 172.16.39.100 to 172.16.39.120")
    
    # Generate IP range
    try:
        ip_list = generate_ip_range("172.16.39.100", "172.16.39.120")
        print_info(f"Generated {len(ip_list)} IP addresses to test")
    except Exception as e:
        print_error(f"Error generating IP range: {e}")
        return False
    
    # Test devices in parallel for faster execution
    print_info("Starting parallel connectivity tests...")
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(test_device_comprehensive, ip): ip for ip in ip_list}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                
                # Real-time status update
                host = result['host']
                status = result['overall_status']
                
                if status == 'FULLY_ACCESSIBLE':
                    print_success(f"{host}: READY FOR V4CODERCLI")
                elif status == 'UNREACHABLE':
                    print_error(f"{host}: NOT REACHABLE")
                elif status == 'SSH_PORT_CLOSED':
                    print_warning(f"{host}: PING OK, SSH PORT CLOSED")
                elif status == 'SSH_ALGORITHM_ISSUE':
                    print_warning(f"{host}: SSH ALGORITHM MISMATCH")
                elif status == 'AUTH_FAILED':
                    print_warning(f"{host}: SSH OPEN, AUTH FAILED")
                else:
                    print_error(f"{host}: {status}")
                    
            except Exception as e:
                ip = futures[future]
                print_error(f"Error testing {ip}: {e}")
                results.append({
                    'host': ip,
                    'overall_status': 'TEST_ERROR',
                    'ping': None,
                    'ssh_port': None,
                    'ssh_auth': None
                })
    
    # Generate summary report
    print_header("CONNECTIVITY TEST SUMMARY")
    
    # Count results by status
    status_counts = {}
    accessible_devices = []
    
    for result in results:
        status = result['overall_status']
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if status == 'FULLY_ACCESSIBLE':
            accessible_devices.append(result['host'])
    
    # Display summary
    total_tested = len(results)
    print_info(f"Total devices tested: {total_tested}")
    
    for status, count in status_counts.items():
        if status == 'FULLY_ACCESSIBLE':
            print_success(f"{status}: {count} devices")
        elif status in ['UNREACHABLE', 'TEST_ERROR']:
            print_error(f"{status}: {count} devices")
        else:
            print_warning(f"{status}: {count} devices")
    
    # Show accessible devices
    if accessible_devices:
        print_header("DEVICES READY FOR V4CODERCLI")
        for device in accessible_devices:
            print_success(f"✅ {device}")
            
        # Generate V4codercli compatible CSV
        csv_filename = "accessible_devices.csv"
        with open(csv_filename, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol\n")
            for i, device in enumerate(accessible_devices):
                f.write(f"Router_{device.split('.')[-1]},{device},cisco,cisco,cisco_ios,ssh\n")
        
        print_info(f"Generated {csv_filename} for V4codercli with {len(accessible_devices)} devices")
    else:
        print_error("No devices are accessible via SSH")
        print_info("Possible issues:")
        print_info("  1. Devices are not configured for SSH access")
        print_info("  2. Network filtering is blocking SSH connections")
        print_info("  3. Wrong credentials (default: cisco/cisco)")
        print_info("  4. SSH service not running on devices")
    
    # Show recommendations
    print_header("RECOMMENDATIONS")
    
    unreachable = status_counts.get('UNREACHABLE', 0)
    ssh_port_closed = status_counts.get('SSH_PORT_CLOSED', 0)
    auth_failed = status_counts.get('AUTH_FAILED', 0)
    
    if unreachable > 0:
        print_warning(f"{unreachable} devices not reachable - check network connectivity")
    
    if ssh_port_closed > 0:
        print_warning(f"{ssh_port_closed} devices have SSH port closed/filtered")
        print_info("Configure SSH on devices or check firewall rules")
    
    if auth_failed > 0:
        print_warning(f"{auth_failed} devices reject authentication")
        print_info("Check credentials or try: admin/admin, root/root")
    
    success_rate = (len(accessible_devices) / total_tested * 100) if total_tested > 0 else 0
    print_info(f"Overall success rate: {success_rate:.1f}%")
    
    return len(accessible_devices) > 0

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
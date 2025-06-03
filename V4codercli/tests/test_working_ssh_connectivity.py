#!/usr/bin/env python3
"""
Working SSH Connectivity Test for V4codercli
Tests router connectivity using the PROVEN working SSH parameters:
- KexAlgorithms=+diffie-hellman-group1-sha1
- HostKeyAlgorithms=+ssh-rsa  
- Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc
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

def test_router_ssh_working(router_ip, username='cisco', password='cisco'):
    """Test router SSH using the exact working parameters."""
    print_info(f"Testing {router_ip} with proven SSH parameters...")
    
    # Working SSH parameters from user's successful connection
    ssh_cmd = [
        'sshpass', '-p', password,
        'ssh',
        '-o', 'KexAlgorithms=+diffie-hellman-group1-sha1',
        '-o', 'HostKeyAlgorithms=+ssh-rsa',
        '-o', 'Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'ConnectTimeout=30',
        '-o', 'BatchMode=yes',
        f'{username}@{router_ip}',
        'show version | include Software'
    ]
    
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=45)
        
        if result.returncode == 0:
            print_success(f"SUCCESS: {router_ip} connected with {username}/{password}")
            return {
                'success': True,
                'router': router_ip,
                'username': username,
                'password': password,
                'output': result.stdout.strip(),
                'method': 'working_ssh'
            }
        else:
            error_msg = result.stderr.strip()
            if 'Permission denied' in error_msg:
                print_warning(f"AUTH FAILED for {router_ip} with {username}/{password}")
                return {
                    'success': False,
                    'router': router_ip,
                    'error': 'authentication_failed',
                    'details': error_msg
                }
            elif 'Connection refused' in error_msg:
                print_error(f"SSH service not available on {router_ip}")
                return {
                    'success': False,
                    'router': router_ip,
                    'error': 'ssh_service_down',
                    'details': error_msg
                }
            else:
                print_warning(f"Connection failed: {error_msg[:100]}")
                return {
                    'success': False,
                    'router': router_ip,
                    'error': 'connection_failed',
                    'details': error_msg
                }
                
    except subprocess.TimeoutExpired:
        print_warning(f"Timeout connecting to {router_ip}")
        return {
            'success': False,
            'router': router_ip,
            'error': 'timeout'
        }
    except FileNotFoundError:
        print_error("sshpass not found - installing...")
        try:
            subprocess.run(['apt-get', 'update', '&&', 'apt-get', 'install', '-y', 'sshpass'], 
                         shell=True, check=True)
            print_success("sshpass installed successfully")
            return test_router_ssh_working(router_ip, username, password)  # Retry
        except:
            print_error("Could not install sshpass")
            return {
                'success': False,
                'router': router_ip,
                'error': 'sshpass_not_available'
            }
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return {
            'success': False,
            'router': router_ip,
            'error': 'unexpected_error',
            'details': str(e)
        }

def test_router_ping(router_ip):
    """Test ping connectivity to router."""
    try:
        cmd = ['ping', '-c', '2', '-W', '3', router_ip]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return True
        else:
            return False
            
    except Exception:
        return False

def comprehensive_router_test(router_ip):
    """Comprehensive test of a router."""
    print_header(f"Testing Router: {router_ip}")
    
    result = {
        'router': router_ip,
        'ping_success': False,
        'ssh_result': None,
        'status': 'UNKNOWN'
    }
    
    # Test 1: Ping
    if test_router_ping(router_ip):
        result['ping_success'] = True
        print_success(f"Ping to {router_ip}: SUCCESS")
    else:
        print_warning(f"Ping to {router_ip}: FAILED (may be filtered)")
    
    # Test 2: SSH with working parameters
    ssh_result = test_router_ssh_working(router_ip)
    result['ssh_result'] = ssh_result
    
    if ssh_result['success']:
        result['status'] = 'READY'
        print_success(f"Router {router_ip}: READY for V4codercli")
    else:
        result['status'] = 'FAILED'
        print_error(f"Router {router_ip}: Not accessible via SSH")
    
    return result

def main():
    """Main function."""
    print_header("V4codercli Working SSH Connectivity Test")
    print_info("Using PROVEN working SSH parameters:")
    print_info("  KexAlgorithms=+diffie-hellman-group1-sha1")
    print_info("  HostKeyAlgorithms=+ssh-rsa")
    print_info("  Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc")
    
    # Test routers based on user's successful connections and network discovery
    test_routers = [
        '172.16.39.106',  # User confirmed working (R6)
        '172.16.39.103',  # User confirmed working (R3)
        '172.16.39.115',  # User ping success
        '172.16.39.120',  # User ping success
        '172.16.39.104',  # Network discovery
        '172.16.39.105',  # Network discovery
        '172.16.39.116',  # Network discovery
        '172.16.39.117',  # Network discovery
        '172.16.39.118',  # Network discovery
        '172.16.39.119',  # Network discovery
    ]
    
    print_info(f"Testing {len(test_routers)} routers with working SSH parameters")
    
    results = []
    working_routers = []
    
    # Test each router
    for router_ip in test_routers:
        try:
            result = comprehensive_router_test(router_ip)
            results.append(result)
            
            if result['status'] == 'READY':
                working_routers.append({
                    'ip': router_ip,
                    'username': result['ssh_result']['username'],
                    'password': result['ssh_result']['password'],
                    'ping_ok': result['ping_success']
                })
                
        except KeyboardInterrupt:
            print_warning("Test interrupted by user")
            break
        except Exception as e:
            print_error(f"Error testing {router_ip}: {e}")
    
    # Summary
    print_header("WORKING SSH CONNECTIVITY SUMMARY")
    
    total = len(results)
    ready = len(working_routers)
    ping_success = len([r for r in results if r['ping_success']])
    
    print_info(f"Total routers tested: {total}")
    print_success(f"Routers ready for V4codercli: {ready}")
    print_info(f"Routers responding to ping: {ping_success}")
    
    if working_routers:
        print_header("READY ROUTERS")
        for router in working_routers:
            ping_status = "Ping OK" if router['ping_ok'] else "Ping Failed"
            print_success(f"✅ {router['ip']} - SSH: {router['username']}/{router['password']} ({ping_status})")
        
        # Generate CSV for V4codercli
        csv_filename = "working_ssh_devices.csv"
        with open(csv_filename, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol\n")
            for router in working_routers:
                name = f"R{router['ip'].split('.')[-1]}"
                f.write(f"{name},{router['ip']},{router['username']},{router['password']},cisco_ios,ssh\n")
        
        print_info(f"Generated {csv_filename} for V4codercli")
        
        # Update main V4codercli SSH configuration
        update_v4codercli_ssh_config()
        
    else:
        print_error("No routers are accessible with working SSH parameters")
        print_info("Check router SSH service status and credentials")
    
    # Show detailed error analysis
    if results:
        print_header("ERROR ANALYSIS")
        error_types = {}
        for result in results:
            if result['status'] == 'FAILED' and result['ssh_result']:
                error_type = result['ssh_result'].get('error', 'unknown')
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        for error_type, count in error_types.items():
            print_warning(f"{error_type}: {count} routers")
    
    return len(working_routers) > 0

def update_v4codercli_ssh_config():
    """Update V4codercli SSH configuration with working parameters."""
    try:
        # Update the main SSH config
        main_ssh_config = Path("cisco_ssh_config")
        working_config = Path("cisco_ssh_config_working")
        
        if working_config.exists():
            # Backup original
            if main_ssh_config.exists():
                main_ssh_config.rename("cisco_ssh_config.backup_original")
            
            # Copy working config as main config
            import shutil
            shutil.copy2(working_config, main_ssh_config)
            
            print_success("Updated V4codercli SSH configuration with working parameters")
        
    except Exception as e:
        print_warning(f"Could not update V4codercli configuration: {e}")

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
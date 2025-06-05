#!/usr/bin/env python3
"""
Complete Solution Test for V4codercli
Tests router connectivity using:
1. Jump host routing (172.16.39.128)
2. PROVEN working SSH algorithms
3. Full V4codercli integration

Based on user's successful connection:
ssh -o KexAlgorithms=+diffie-hellman-group1-sha1 -o HostKeyAlgorithms=+ssh-rsa -o Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc cisco@172.16.39.106
"""

import subprocess
import socket
import time
import sys
from pathlib import Path

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

def test_jump_host():
    """Test jump host connectivity."""
    print_info("Testing jump host 172.16.39.128...")
    
    try:
        # Test ping to jump host
        ping_cmd = ['ping', '-c', '2', '-W', '5', '172.16.39.128']
        result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print_success("Jump host 172.16.39.128 is reachable")
            return True
        else:
            print_error("Jump host 172.16.39.128 is not reachable")
            return False
            
    except Exception as e:
        print_error(f"Jump host test error: {e}")
        return False

def test_router_via_complete_solution(router_ip, username='cisco', password='cisco'):
    """Test router using complete solution (jump host + working algorithms)."""
    print_info(f"Testing {router_ip} via complete solution...")
    
    ssh_config_path = Path(__file__).parent / "cisco_ssh_config_complete_solution"
    
    # SSH command using the complete solution config
    ssh_cmd = [
        'sshpass', '-p', password,
        'ssh',
        '-F', str(ssh_config_path),
        '-o', 'ConnectTimeout=45',
        '-o', 'BatchMode=yes',
        f'{username}@{router_ip}',
        'show version | include Software'
    ]
    
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print_success(f"SUCCESS: {router_ip} connected via complete solution")
            return {
                'success': True,
                'router': router_ip,
                'username': username,
                'password': password,
                'output': result.stdout.strip(),
                'method': 'complete_solution'
            }
        else:
            error_msg = result.stderr.strip()
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
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return {
            'success': False,
            'router': router_ip,
            'error': 'unexpected_error',
            'details': str(e)
        }

def test_direct_ssh_command(router_ip, username='cisco', password='cisco'):
    """Test using the exact SSH command that worked for the user."""
    print_info(f"Testing {router_ip} with exact working SSH command...")
    
    # Exact command that worked for user (but via jump host)
    ssh_cmd = [
        'sshpass', '-p', password,
        'ssh',
        '-o', 'ProxyJump=root@172.16.39.128',
        '-o', 'KexAlgorithms=+diffie-hellman-group1-sha1',
        '-o', 'HostKeyAlgorithms=+ssh-rsa',
        '-o', 'Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'ConnectTimeout=45',
        '-o', 'BatchMode=yes',
        f'{username}@{router_ip}',
        'show version | include Software'
    ]
    
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print_success(f"SUCCESS: {router_ip} connected with direct SSH command")
            return {
                'success': True,
                'router': router_ip,
                'username': username,
                'password': password,
                'output': result.stdout.strip(),
                'method': 'direct_ssh_command'
            }
        else:
            error_msg = result.stderr.strip()
            print_warning(f"Direct SSH failed: {error_msg[:100]}")
            return {
                'success': False,
                'router': router_ip,
                'error': 'direct_ssh_failed',
                'details': error_msg
            }
                
    except subprocess.TimeoutExpired:
        print_warning(f"Timeout with direct SSH to {router_ip}")
        return {
            'success': False,
            'router': router_ip,
            'error': 'timeout'
        }
    except Exception as e:
        print_error(f"Direct SSH error: {e}")
        return {
            'success': False,
            'router': router_ip,
            'error': 'direct_ssh_error',
            'details': str(e)
        }

def comprehensive_router_test(router_ip):
    """Comprehensive test of a router using both methods."""
    print_header(f"Testing Router: {router_ip}")
    
    result = {
        'router': router_ip,
        'complete_solution': None,
        'direct_ssh': None,
        'status': 'UNKNOWN'
    }
    
    # Test 1: Complete solution (config file)
    complete_result = test_router_via_complete_solution(router_ip)
    result['complete_solution'] = complete_result
    
    # Test 2: Direct SSH command
    direct_result = test_direct_ssh_command(router_ip)
    result['direct_ssh'] = direct_result
    
    # Determine status
    if complete_result['success'] or direct_result['success']:
        result['status'] = 'READY'
        print_success(f"Router {router_ip}: READY for V4codercli")
        
        # Prefer complete solution result
        if complete_result['success']:
            result['working_method'] = complete_result
        else:
            result['working_method'] = direct_result
    else:
        result['status'] = 'FAILED'
        print_error(f"Router {router_ip}: Not accessible")
    
    return result

def main():
    """Main function."""
    print_header("V4codercli Complete Solution Test")
    print_info("Testing COMPLETE SOLUTION:")
    print_info("  ✅ Jump host routing through 172.16.39.128")
    print_info("  ✅ PROVEN working SSH algorithms")
    print_info("  ✅ V4codercli integration ready")
    
    # First test jump host
    if not test_jump_host():
        print_error("Jump host not accessible - cannot proceed")
        return False
    
    # Test routers that user confirmed working
    priority_routers = [
        '172.16.39.106',  # User confirmed working (R6)
        '172.16.39.103',  # User confirmed working (R3)
    ]
    
    # Additional routers from user's environment
    additional_routers = [
        '172.16.39.115',  # User ping success
        '172.16.39.120',  # User ping success
        '172.16.39.104',  # Network discovery
        '172.16.39.105',  # Network discovery
    ]
    
    print_info(f"Testing {len(priority_routers)} priority routers first...")
    
    results = []
    working_routers = []
    
    # Test priority routers first
    for router_ip in priority_routers:
        try:
            result = comprehensive_router_test(router_ip)
            results.append(result)
            
            if result['status'] == 'READY':
                working_routers.append({
                    'ip': router_ip,
                    'username': result['working_method']['username'],
                    'password': result['working_method']['password'],
                    'method': result['working_method']['method']
                })
                
        except KeyboardInterrupt:
            print_warning("Test interrupted by user")
            break
        except Exception as e:
            print_error(f"Error testing {router_ip}: {e}")
    
    # If priority routers work, test additional ones
    if working_routers:
        print_info("Priority routers working! Testing additional routers...")
        
        for router_ip in additional_routers:
            try:
                result = comprehensive_router_test(router_ip)
                results.append(result)
                
                if result['status'] == 'READY':
                    working_routers.append({
                        'ip': router_ip,
                        'username': result['working_method']['username'],
                        'password': result['working_method']['password'],
                        'method': result['working_method']['method']
                    })
                    
            except KeyboardInterrupt:
                print_warning("Test interrupted by user")
                break
            except Exception as e:
                print_error(f"Error testing {router_ip}: {e}")
    
    # Summary
    print_header("COMPLETE SOLUTION SUMMARY")
    
    total = len(results)
    ready = len(working_routers)
    
    print_info(f"Total routers tested: {total}")
    print_success(f"Routers ready for V4codercli: {ready}")
    
    if working_routers:
        print_header("READY ROUTERS")
        for router in working_routers:
            print_success(f"✅ {router['ip']} - {router['username']}/{router['password']} ({router['method']})")
        
        # Generate CSV for V4codercli
        csv_filename = "complete_solution_devices.csv"
        with open(csv_filename, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol,jump_host\n")
            for router in working_routers:
                name = f"R{router['ip'].split('.')[-1]}"
                f.write(f"{name},{router['ip']},{router['username']},{router['password']},cisco_ios,ssh,172.16.39.128\n")
        
        print_info(f"Generated {csv_filename} for V4codercli")
        
        # Deploy complete solution
        deploy_complete_solution()
        
        print_header("🎉 SUCCESS: V4codercli Ready!")
        print_success("Complete solution implemented and tested")
        print_success("V4codercli can now connect to routers via jump host")
        print_info("Next step: Run V4codercli with Option 2 (Quick connectivity)")
        
    else:
        print_error("No routers accessible with complete solution")
        print_info("Troubleshooting steps:")
        print_info("  1. Verify jump host SSH access")
        print_info("  2. Check router SSH service status")
        print_info("  3. Verify router credentials")
    
    return len(working_routers) > 0

def deploy_complete_solution():
    """Deploy the complete solution to V4codercli."""
    try:
        # Update main SSH config
        main_ssh_config = Path("cisco_ssh_config")
        complete_config = Path("cisco_ssh_config_complete_solution")
        
        if complete_config.exists():
            # Backup original
            if main_ssh_config.exists():
                main_ssh_config.rename("cisco_ssh_config.backup_working")
            
            # Deploy complete solution
            import shutil
            shutil.copy2(complete_config, main_ssh_config)
            
            print_success("Deployed complete solution SSH configuration")
        
    except Exception as e:
        print_warning(f"Could not deploy complete solution: {e}")

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
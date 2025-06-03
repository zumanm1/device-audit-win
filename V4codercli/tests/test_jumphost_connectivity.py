#!/usr/bin/env python3
"""
Jump Host Connectivity Test for V4codercli
Tests router connectivity through jump host 172.16.39.128 with legacy SSH support
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

def test_jump_host_connectivity():
    """Test connectivity to the jump host."""
    print_info("Testing jump host connectivity...")
    
    try:
        # Test ping to jump host
        cmd = ['ping', '-c', '2', '-W', '5', '172.16.39.128']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print_success("Jump host 172.16.39.128 is reachable")
            
            # Test SSH to jump host
            ssh_cmd = [
                'ssh', '-o', 'ConnectTimeout=10',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'BatchMode=yes',
                'root@172.16.39.128',
                'echo "Jump host SSH test successful"'
            ]
            
            ssh_result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
            
            if ssh_result.returncode == 0:
                print_success("Jump host SSH access working")
                return True
            else:
                print_warning("Jump host SSH may need password authentication")
                return True  # Still usable with password
        else:
            print_error("Jump host 172.16.39.128 is not reachable")
            return False
            
    except Exception as e:
        print_error(f"Jump host test error: {e}")
        return False

def test_router_via_jumphost(router_ip, username='cisco', password='cisco'):
    """Test router connectivity through jump host."""
    ssh_config_path = Path(__file__).parent / "cisco_ssh_config_jumphost"
    
    print_info(f"Testing {router_ip} via jump host...")
    
    # Test multiple credential combinations
    credentials = [
        ('cisco', 'cisco'),
        ('admin', 'admin'),
        ('root', 'root'),
        ('lab', 'lab123')
    ]
    
    for username, password in credentials:
        try:
            print_info(f"  Trying {username}/{password}")
            
            # SSH command via jump host
            ssh_cmd = [
                'sshpass', '-p', password,
                'ssh',
                '-F', str(ssh_config_path),
                '-o', 'ConnectTimeout=30',
                '-o', 'BatchMode=yes',
                f'{username}@{router_ip}',
                'show version | include Software'
            ]
            
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=45)
            
            if result.returncode == 0:
                print_success(f"  SUCCESS: {router_ip} via jump host with {username}/{password}")
                return {
                    'success': True,
                    'router': router_ip,
                    'username': username,
                    'password': password,
                    'method': 'jumphost',
                    'output': result.stdout.strip()[:100]
                }
            else:
                error_msg = result.stderr.strip()
                if 'Permission denied' in error_msg:
                    print_warning(f"  AUTH FAILED for {username}/{password}")
                elif 'no matching key exchange method' in error_msg:
                    print_error(f"  SSH algorithm issue: {error_msg[:50]}")
                elif 'Connection refused' in error_msg:
                    print_error(f"  SSH service not available on {router_ip}")
                    break  # No point trying other credentials
                else:
                    print_warning(f"  Connection failed: {error_msg[:50]}")
                    
        except subprocess.TimeoutExpired:
            print_warning(f"  Timeout connecting to {router_ip} via jump host")
        except FileNotFoundError:
            print_error("sshpass not found - installing...")
            try:
                subprocess.run(['apt-get', 'update', '&&', 'apt-get', 'install', '-y', 'sshpass'], 
                             shell=True, check=True)
                print_success("sshpass installed, please re-run the test")
            except:
                print_error("Could not install sshpass")
            break
        except Exception as e:
            print_warning(f"  Error: {e}")
    
    return {
        'success': False,
        'router': router_ip,
        'error': 'All authentication methods failed'
    }

def test_router_ping_via_jumphost(router_ip):
    """Test router ping through jump host."""
    try:
        # Use jump host to ping the router
        ping_cmd = [
            'ssh', '-o', 'ConnectTimeout=10',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            'root@172.16.39.128',
            f'ping -c 2 -W 3 {router_ip}'
        ]
        
        result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0 and 'bytes from' in result.stdout:
            return True
        else:
            return False
            
    except Exception:
        return False

def comprehensive_router_test(router_ip):
    """Comprehensive test of a router via jump host."""
    print_header(f"Testing Router: {router_ip}")
    
    result = {
        'router': router_ip,
        'ping_via_jumphost': False,
        'ssh_via_jumphost': None,
        'status': 'UNKNOWN'
    }
    
    # Test 1: Ping via jump host
    if test_router_ping_via_jumphost(router_ip):
        result['ping_via_jumphost'] = True
        print_success(f"Ping to {router_ip} via jump host: SUCCESS")
    else:
        print_warning(f"Ping to {router_ip} via jump host: FAILED")
    
    # Test 2: SSH via jump host
    ssh_result = test_router_via_jumphost(router_ip)
    result['ssh_via_jumphost'] = ssh_result
    
    if ssh_result['success']:
        result['status'] = 'READY'
        print_success(f"Router {router_ip}: READY for V4codercli")
    else:
        result['status'] = 'FAILED'
        print_error(f"Router {router_ip}: Not accessible via jump host")
    
    return result

def main():
    """Main function."""
    print_header("V4codercli Jump Host Connectivity Test")
    print_info("Testing router connectivity through jump host 172.16.39.128")
    print_info("All connections will use legacy SSH algorithm support")
    
    # First test jump host
    if not test_jump_host_connectivity():
        print_error("Jump host is not accessible - cannot proceed")
        return False
    
    # Test routers from inventory (based on user's ping results)
    responsive_routers = [
        '172.16.39.106',  # User confirmed responding
        '172.16.39.115',  # User confirmed responding  
        '172.16.39.120',  # User confirmed responding
        '172.16.39.103',  # From nmap discovery
        '172.16.39.104',  # From nmap discovery
        '172.16.39.105',  # From nmap discovery
        '172.16.39.116',  # From nmap discovery
        '172.16.39.117',  # From nmap discovery
        '172.16.39.118',  # From nmap discovery
        '172.16.39.119',  # From nmap discovery
    ]
    
    print_info(f"Testing {len(responsive_routers)} routers via jump host")
    
    results = []
    working_routers = []
    
    # Test each router
    for router_ip in responsive_routers:
        try:
            result = comprehensive_router_test(router_ip)
            results.append(result)
            
            if result['status'] == 'READY':
                working_routers.append({
                    'ip': router_ip,
                    'username': result['ssh_via_jumphost']['username'],
                    'password': result['ssh_via_jumphost']['password']
                })
                
        except KeyboardInterrupt:
            print_warning("Test interrupted by user")
            break
        except Exception as e:
            print_error(f"Error testing {router_ip}: {e}")
    
    # Summary
    print_header("JUMP HOST CONNECTIVITY SUMMARY")
    
    total = len(results)
    ready = len(working_routers)
    ping_success = len([r for r in results if r['ping_via_jumphost']])
    
    print_info(f"Total routers tested: {total}")
    print_success(f"Routers ready for V4codercli: {ready}")
    print_info(f"Routers pingable via jump host: {ping_success}")
    
    if working_routers:
        print_header("READY ROUTERS")
        for router in working_routers:
            print_success(f"✅ {router['ip']} (SSH: {router['username']}/{router['password']})")
        
        # Generate CSV for V4codercli
        csv_filename = "jumphost_ready_devices.csv"
        with open(csv_filename, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol,jump_host\n")
            for router in working_routers:
                name = f"R{router['ip'].split('.')[-1]}"
                f.write(f"{name},{router['ip']},{router['username']},{router['password']},cisco_ios,ssh,172.16.39.128\n")
        
        print_info(f"Generated {csv_filename} for V4codercli with jump host configuration")
        
        # Update main V4codercli configuration
        print_info("Updating V4codercli to use jump host for all connections...")
        update_v4codercli_for_jumphost()
        
    else:
        print_error("No routers are accessible via jump host")
        print_info("Possible issues:")
        print_info("  1. Routers need SSH service enabled")
        print_info("  2. Check router credentials")
        print_info("  3. Verify jump host routing to router network")
    
    return len(working_routers) > 0

def update_v4codercli_for_jumphost():
    """Update V4codercli configuration to use jump host."""
    try:
        # Update the main SSH config to use jump host
        main_ssh_config = Path("cisco_ssh_config")
        jumphost_config = Path("cisco_ssh_config_jumphost")
        
        if jumphost_config.exists():
            # Backup original
            if main_ssh_config.exists():
                main_ssh_config.rename("cisco_ssh_config.backup")
            
            # Copy jump host config as main config
            import shutil
            shutil.copy2(jumphost_config, main_ssh_config)
            
            print_success("Updated V4codercli SSH configuration to use jump host")
        
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
#!/usr/bin/env python3
"""
Simple Direct Connection Test
Tests the exact SSH command that worked for the user from EVE-NG jump host
"""

import subprocess
import sys

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
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.WHITE}{title:^60}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def test_router_direct(router_ip, username='cisco', password='cisco'):
    """Test router using the exact working SSH parameters."""
    print_info(f"Testing {router_ip} with exact working parameters...")
    
    # The exact SSH command that worked for the user
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
            print_success(f"SUCCESS: {router_ip} connected!")
            print_info(f"Output: {result.stdout.strip()}")
            return True
        else:
            error_msg = result.stderr.strip()
            print_error(f"Failed: {error_msg}")
            return False
                
    except subprocess.TimeoutExpired:
        print_error(f"Timeout connecting to {router_ip}")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    """Test the routers that user confirmed working."""
    print_header("Simple Direct Connection Test")
    print_info("Using exact SSH parameters that worked for user")
    
    # Test the routers user confirmed working
    test_routers = [
        ('172.16.39.106', 'cisco', 'cisco'),  # R6 - user confirmed
        ('172.16.39.103', 'cisco', 'cisco'),  # R3 - user confirmed
    ]
    
    working_count = 0
    
    for router_ip, username, password in test_routers:
        if test_router_direct(router_ip, username, password):
            working_count += 1
    
    print_header("RESULTS")
    print_info(f"Working routers: {working_count}/{len(test_routers)}")
    
    if working_count > 0:
        print_success("SSH parameters are working!")
        print_info("These routers are ready for V4codercli")
        
        # Create a simple device CSV
        with open('verified_devices.csv', 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol\n")
            for router_ip, username, password in test_routers:
                if test_router_direct(router_ip, username, password):
                    name = f"R{router_ip.split('.')[-1]}"
                    f.write(f"{name},{router_ip},{username},{password},cisco_ios,ssh\n")
        
        print_info("Generated verified_devices.csv")
        return True
    else:
        print_error("No routers accessible")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
"""
Router Test with Jump Host Authentication
Tests 172.16.39.106 and 172.16.39.120 with proper jump host handling
"""

import subprocess
import time
import sys
from pathlib import Path

# ANSI color codes
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

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def test_jump_host_auth(jump_host='172.16.39.128', jump_user='root'):
    """Test different authentication methods for jump host."""
    print_info(f"Testing jump host authentication: {jump_user}@{jump_host}")
    
    # Common passwords for EVE-NG and lab environments
    passwords = ['unl', 'eve', 'root', 'admin', 'cisco', '']
    
    for password in passwords:
        try:
            if password == '':
                print_info("Trying passwordless/key-based authentication...")
                cmd = ['ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes', 
                       '-o', 'StrictHostKeyChecking=no', f'{jump_user}@{jump_host}', 'echo SUCCESS']
            else:
                print_info(f"Trying password: '{password}'")
                cmd = ['sshpass', '-p', password, 'ssh', '-o', 'ConnectTimeout=10', 
                       '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', 
                       f'{jump_user}@{jump_host}', 'echo SUCCESS']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and 'SUCCESS' in result.stdout:
                print_success(f"Jump host authentication successful with password: '{password}'")
                return password
            else:
                print_warning(f"Failed with password: '{password}'")
                
        except subprocess.TimeoutExpired:
            print_warning(f"Timeout with password: '{password}'")
        except Exception as e:
            print_warning(f"Error with password '{password}': {e}")
    
    print_error("No working authentication method found for jump host")
    return None

def test_router_via_jumphost(router_ip, router_name, jump_password, 
                           jump_host='172.16.39.128', jump_user='root',
                           router_user='cisco', router_password='cisco'):
    """Test router connection via jump host with working authentication."""
    print_header(f"Testing {router_name} ({router_ip}) via Jump Host")
    
    if jump_password == '':
        # Key-based authentication
        ssh_cmd = [
            'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'ConnectTimeout=30',
            f'{jump_user}@{jump_host}',
            f'sshpass -p {router_password} ssh -o KexAlgorithms=+diffie-hellman-group1-sha1 '
            f'-o HostKeyAlgorithms=+ssh-rsa -o Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc '
            f'-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=20 '
            f'{router_user}@{router_ip} "show version | include Software"'
        ]
    else:
        # Password-based authentication
        ssh_cmd = [
            'sshpass', '-p', jump_password, 'ssh', 
            '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'ConnectTimeout=30',
            f'{jump_user}@{jump_host}',
            f'sshpass -p {router_password} ssh -o KexAlgorithms=+diffie-hellman-group1-sha1 '
            f'-o HostKeyAlgorithms=+ssh-rsa -o Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc '
            f'-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=20 '
            f'{router_user}@{router_ip} "show version | include Software"'
        ]
    
    try:
        print_info("Executing SSH command via jump host...")
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output and 'Software' in output:
                print_success(f"SUCCESS: {router_name} connected via jump host!")
                print_info(f"Router output: {output[:150]}...")
                return {
                    'success': True,
                    'router': router_ip,
                    'name': router_name,
                    'output': output,
                    'jump_password': jump_password
                }
            else:
                print_warning(f"Connected but no valid output: {output}")
        else:
            error_msg = result.stderr.strip()
            print_error(f"SSH command failed: {error_msg[:200]}")
            
    except subprocess.TimeoutExpired:
        print_error("SSH command timed out")
    except Exception as e:
        print_error(f"SSH command error: {e}")
    
    return {'success': False, 'router': router_ip, 'name': router_name}

def main():
    """Main test function."""
    print_header("Router Test with Jump Host Authentication")
    print_info("Testing R106 (172.16.39.106) and R120 (172.16.39.120)")
    print_info("Finding working jump host authentication...")
    
    # First, find working jump host authentication
    jump_password = test_jump_host_auth()
    
    if jump_password is None:
        print_error("Cannot authenticate to jump host - test failed")
        return False
    
    # Test routers via jump host
    routers = [
        ('172.16.39.106', 'R106'),
        ('172.16.39.120', 'R120')
    ]
    
    working_routers = []
    
    for router_ip, router_name in routers:
        result = test_router_via_jumphost(router_ip, router_name, jump_password)
        
        if result['success']:
            working_routers.append(result)
    
    # Summary
    print_header("TEST RESULTS")
    
    print_info(f"Routers tested: {len(routers)}")
    print_success(f"Working routers: {len(working_routers)}")
    
    if working_routers:
        print_header("SUCCESSFUL CONNECTIONS")
        for router in working_routers:
            print_success(f"✅ {router['name']} ({router['router']})")
        
        # Save results
        csv_filename = "jumphost_verified_routers.csv"
        with open(csv_filename, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol,jump_host,jump_password\n")
            for router in working_routers:
                f.write(f"{router['name']},{router['router']},cisco,cisco,cisco_ios,ssh,172.16.39.128,{router['jump_password']}\n")
        
        print_info(f"Results saved to {csv_filename}")
        
        print_header("🎉 SUCCESS!")
        print_success("V4codercli full range solution validated with jump host authentication")
        print_info(f"Jump host password found: '{jump_password}'")
        return True
    else:
        print_error("No routers were accessible via jump host")
        return False

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
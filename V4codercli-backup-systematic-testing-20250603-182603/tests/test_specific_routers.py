#!/usr/bin/env python3
"""
Specific Router Test for V4codercli
Tests connectivity to 172.16.39.106 and 172.16.39.120
Using PROVEN working SSH parameters
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

def test_jump_host():
    """Test jump host connectivity."""
    print_info("Testing jump host 172.16.39.128...")
    
    try:
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

def test_router_with_methods(router_ip, router_name, username='cisco', password='cisco'):
    """Test router with multiple methods."""
    print_header(f"Testing {router_name} ({router_ip})")
    
    methods = [
        {
            'name': 'SSH Config File',
            'cmd': [
                'sshpass', '-p', password,
                'ssh', '-F', 'cisco_ssh_config_full_range',
                '-o', 'ConnectTimeout=30',
                '-o', 'BatchMode=yes',
                f'{username}@{router_ip}',
                'show version | include Software'
            ]
        },
        {
            'name': 'Direct SSH with ProxyJump',
            'cmd': [
                'sshpass', '-p', password,
                'ssh',
                '-o', 'ProxyJump=root@172.16.39.128',
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
        }
    ]
    
    for i, method in enumerate(methods, 1):
        print_info(f"Method {i}: {method['name']}")
        
        try:
            result = subprocess.run(method['cmd'], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print_success(f"SUCCESS: {router_name} connected via {method['name']}")
                output = result.stdout.strip()
                if output:
                    print_info(f"Output: {output[:150]}...")
                return {
                    'success': True,
                    'router': router_ip,
                    'name': router_name,
                    'method': method['name'],
                    'output': output
                }
            else:
                error_msg = result.stderr.strip()
                print_warning(f"Failed via {method['name']}: {error_msg[:100]}")
                
        except subprocess.TimeoutExpired:
            print_warning(f"Timeout with {method['name']}")
        except Exception as e:
            print_warning(f"Error with {method['name']}: {e}")
    
    print_error(f"All methods failed for {router_name}")
    return {'success': False, 'router': router_ip, 'name': router_name}

def main():
    """Test specific routers."""
    print_header("V4codercli Specific Router Test")
    print_info("Testing R106 (172.16.39.106) and R120 (172.16.39.120)")
    print_info("Using proven working SSH parameters")
    
    # Test jump host first
    if not test_jump_host():
        print_error("Jump host not accessible - cannot proceed")
        return False
    
    # Test specific routers
    routers = [
        ('172.16.39.106', 'R106'),
        ('172.16.39.120', 'R120')
    ]
    
    results = []
    working_routers = []
    
    for router_ip, router_name in routers:
        result = test_router_with_methods(router_ip, router_name)
        results.append(result)
        
        if result['success']:
            working_routers.append(result)
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    
    print_info(f"Routers tested: {len(routers)}")
    print_success(f"Working routers: {len(working_routers)}")
    
    if working_routers:
        print_header("WORKING ROUTERS")
        for router in working_routers:
            print_success(f"✅ {router['name']} ({router['router']}) - {router['method']}")
        
        # Generate simple CSV for working routers
        csv_filename = "verified_specific_routers.csv"
        with open(csv_filename, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol,method\n")
            for router in working_routers:
                f.write(f"{router['name']},{router['router']},cisco,cisco,cisco_ios,ssh,{router['method']}\n")
        
        print_info(f"Generated {csv_filename}")
        
        print_header("🎉 SUCCESS!")
        print_success("Specific routers tested and verified working")
        print_info("V4codercli full range solution validated")
        return True
    else:
        print_error("No routers were accessible")
        print_info("Check jump host authentication and router status")
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
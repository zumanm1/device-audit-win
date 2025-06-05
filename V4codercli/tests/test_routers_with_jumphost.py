#!/usr/bin/env python3
"""
Router Testing with Jump Host - Security Enhanced
Tests router connectivity using jump host with credentials from .env-t
"""

import subprocess
import time
import csv
import os
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

def load_credentials_from_env():
    """Load credentials from .env-t file."""
    credentials = {}
    env_file = Path('.env-t')
    
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        credentials[key.strip()] = value.strip()
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Could not load .env-t file: {e}")
    
    return {
        'jump_host_ip': credentials.get('JUMP_HOST_IP', '172.16.39.128'),
        'jump_host_username': credentials.get('JUMP_HOST_USERNAME', 'root'),
        'jump_host_password': credentials.get('JUMP_HOST_PASSWORD', 'eve'),
        'router_username': credentials.get('ROUTER_USERNAME', 'cisco'),
        'router_password': credentials.get('ROUTER_PASSWORD', 'cisco')
    }

def get_test_passwords():
    """Get list of test passwords from environment, with fallbacks for testing."""
    creds = load_credentials_from_env()
    # For testing purposes, include common passwords but prioritize env credentials
    test_passwords = [
        creds['jump_host_password'],  # Primary from .env-t
        creds['router_password'],     # Secondary from .env-t
        'eve', 'unl', 'root', 'admin', 'cisco'  # Common test passwords
    ]
    # Remove duplicates while preserving order
    return list(dict.fromkeys(test_passwords))

def test_jump_host_auth(jump_host=None, jump_user=None):
    """Test jump host authentication using credentials from .env-t."""
    creds = load_credentials_from_env()
    
    if jump_host is None:
        jump_host = creds['jump_host_ip']
    if jump_user is None:
        jump_user = creds['jump_host_username']
    
    print(f"Testing jump host authentication: {jump_user}@{jump_host}")
    
    passwords = get_test_passwords()
    
    for password in passwords:
        try:
            print(f"Trying password: {'*' * len(password)}")
            cmd = [
                'sshpass', '-p', password,
                'ssh', '-o', 'ConnectTimeout=10',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'{jump_user}@{jump_host}',
                'echo "Authentication successful"'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print(f"✅ Jump host authentication successful with {jump_user}@{jump_host}")
                return password
            else:
                print(f"❌ Authentication failed: {result.stderr.strip()}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Connection timeout for password")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"❌ All authentication attempts failed for {jump_user}@{jump_host}")
    return None

def test_router_via_jumphost(router_ip, router_name,
                           jump_host=None, jump_user=None,
                           router_user=None, router_password=None):
    """Test router connectivity via jump host using .env-t credentials."""
    creds = load_credentials_from_env()
    
    # Use environment credentials if not provided
    if jump_host is None:
        jump_host = creds['jump_host_ip']
    if jump_user is None:
        jump_user = creds['jump_host_username']
    if router_user is None:
        router_user = creds['router_username']
    if router_password is None:
        router_password = creds['router_password']
    
    print(f"\n{'='*60}")
    print(f"Testing {router_name} ({router_ip}) via jump host")
    print(f"Jump Host: {jump_user}@{jump_host}")
    print(f"Router: {router_user}@{router_ip}")
    print(f"{'='*60}")
    
    # First ensure jump host authentication works
    jump_password = test_jump_host_auth(jump_host, jump_user)
    if not jump_password:
        return {
            'router': router_name,
            'router_ip': router_ip,
            'status': 'FAILED',
            'error': 'Jump host authentication failed',
            'jump_password': None
        }
    
    # Test router connectivity via jump host
    try:
        cmd = [
            'sshpass', '-p', jump_password,
            'ssh', '-o', 'ConnectTimeout=10',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'{jump_user}@{jump_host}',
            f"sshpass -p {router_password} ssh "
            f"-o ConnectTimeout=10 -o StrictHostKeyChecking=no "
            f"-o UserKnownHostsFile=/dev/null "
            f"{router_user}@{router_ip} 'show version | include Software'"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {router_name} is accessible!")
            print(f"Output: {result.stdout.strip()[:100]}...")
            return {
                'router': router_name,
                'router_ip': router_ip,
                'status': 'SUCCESS',
                'output': result.stdout.strip(),
                'jump_password': jump_password
            }
        else:
            print(f"❌ FAILED: {router_name} connection failed")
            print(f"Error: {result.stderr.strip()}")
            return {
                'router': router_name,
                'router_ip': router_ip,
                'status': 'FAILED',
                'error': result.stderr.strip(),
                'jump_password': jump_password
            }
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {router_name} connection timed out")
        return {
            'router': router_name,
            'router_ip': router_ip,
            'status': 'TIMEOUT',
            'error': 'Connection timeout',
            'jump_password': jump_password
        }
    except Exception as e:
        print(f"❌ ERROR: {router_name} - {e}")
        return {
            'router': router_name,
            'router_ip': router_ip,
            'status': 'ERROR',
            'error': str(e),
            'jump_password': jump_password
        }

def generate_working_inventory(working_routers):
    """Generate inventory CSV for working routers using .env-t credentials."""
    creds = load_credentials_from_env()
    
    filename = 'working_routers_inventory.csv'
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hostname', 'ip_address', 'username', 'password', 'device_type', 'protocol', 'jump_host', 'jump_password'])
            
            for router in working_routers:
                if router['status'] == 'SUCCESS':
                    writer.writerow([
                        router['name'],
                        router['router'],
                        creds['router_username'],
                        creds['router_password'],
                        'cisco_ios',
                        'ssh',
                        creds['jump_host_ip'],
                        router['jump_password']
                    ])
        
        print(f"✅ Generated inventory file: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to generate inventory: {e}")
        return None

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
        
        if result['status'] == 'SUCCESS':
            working_routers.append(result)
    
    # Summary
    print_header("TEST RESULTS")
    
    print_info(f"Routers tested: {len(routers)}")
    print_success(f"Working routers: {len(working_routers)}")
    
    if working_routers:
        print_header("SUCCESSFUL CONNECTIONS")
        for router in working_routers:
            print_success(f"✅ {router['router']} ({router['router_ip']})")
        
        # Save results
        csv_filename = generate_working_inventory(working_routers)
        
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
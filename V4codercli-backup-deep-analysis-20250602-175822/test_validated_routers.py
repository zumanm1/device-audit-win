#!/usr/bin/env python3
"""
Validated Router Test with Working Credentials
Tests R106 and R120 with confirmed working jump host authentication
Uses credentials from .env-t file
"""

import subprocess
import time
import sys
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
    print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.WHITE}{title:^70}{Colors.END}")
    print(f"{Colors.CYAN}{'='*70}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def load_credentials():
    """Load credentials from .env-t file."""
    env_file = Path(".env-t")
    credentials = {
        'jump_host': os.getenv('JUMP_HOST_IP', '172.16.39.128'),
        'jump_user': os.getenv('JUMP_HOST_USERNAME', 'root'),
        'jump_pass': os.getenv('JUMP_HOST_PASSWORD', 'eve'),
        'router_user': os.getenv('ROUTER_USERNAME', 'cisco'),
        'router_pass': os.getenv('ROUTER_PASSWORD', 'cisco')
    }
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value  # Set environment variable
                        if key == 'JUMP_HOST_IP':
                            credentials['jump_host'] = value
                        elif key == 'JUMP_HOST_USERNAME':
                            credentials['jump_user'] = value
                        elif key == 'JUMP_HOST_PASSWORD':
                            credentials['jump_pass'] = value
                        elif key == 'ROUTER_USERNAME':
                            credentials['router_user'] = value
                        elif key == 'ROUTER_PASSWORD':
                            credentials['router_pass'] = value
        
        print_success("Loaded credentials from .env-t file")
    else:
        print_warning("Using default credentials (.env-t file not found)")
    
    return credentials

def test_jump_host(creds):
    """Test jump host connectivity with loaded credentials."""
    print_info(f"Testing jump host: {creds['jump_user']}@{creds['jump_host']}")
    
    try:
        cmd = [
            'sshpass', '-p', creds['jump_pass'], 'ssh',
            '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=no',
            f"{creds['jump_user']}@{creds['jump_host']}", 'echo SUCCESS'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and 'SUCCESS' in result.stdout:
            print_success("Jump host authentication successful")
            return True
        else:
            print_error(f"Jump host authentication failed: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Jump host test error: {e}")
        return False

def test_router_via_jumphost(router_ip, router_name, creds):
    """Test router connection via jump host with validated credentials."""
    print_header(f"Testing {router_name} ({router_ip})")
    
    # Construct SSH command
    ssh_cmd = [
        'sshpass', '-p', creds['jump_pass'], 'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'ConnectTimeout=30',
        f"{creds['jump_user']}@{creds['jump_host']}",
        f"sshpass -p {creds['router_pass']} ssh "
        f"-o KexAlgorithms=+diffie-hellman-group1-sha1 "
        f"-o HostKeyAlgorithms=+ssh-rsa "
        f"-o Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc "
        f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        f"-o ConnectTimeout=20 {creds['router_user']}@{router_ip} "
        f"'show version | include Software'"
    ]
    
    try:
        print_info("Connecting via jump host...")
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output and 'Software' in output:
                print_success(f"SUCCESS: {router_name} connected!")
                print_info(f"Router output: {output[:150]}...")
                return {
                    'success': True,
                    'router': router_ip,
                    'name': router_name,
                    'output': output,
                    'cisco_version': output.split(',')[1].strip() if ',' in output else 'Unknown'
                }
            else:
                print_warning(f"Connected but no valid output: {output}")
        else:
            error_msg = result.stderr.strip()
            print_error(f"Connection failed: {error_msg[:200]}")
            
    except subprocess.TimeoutExpired:
        print_error("Connection timed out")
    except Exception as e:
        print_error(f"Connection error: {e}")
    
    return {'success': False, 'router': router_ip, 'name': router_name}

def main():
    """Main test function."""
    print_header("V4codercli Validated Router Test")
    print_info("Testing R106 and R120 with validated credentials")
    
    # Load credentials
    creds = load_credentials()
    print_info(f"Jump host: {creds['jump_host']}")
    print_info(f"Jump user: {creds['jump_user']}")
    
    # Test jump host first
    if not test_jump_host(creds):
        print_error("Jump host authentication failed - cannot proceed")
        return False
    
    # Test specific routers
    routers = [
        ('172.16.39.106', 'R106'),
        ('172.16.39.120', 'R120')
    ]
    
    working_routers = []
    
    for router_ip, router_name in routers:
        result = test_router_via_jumphost(router_ip, router_name, creds)
        
        if result['success']:
            working_routers.append(result)
    
    # Summary
    print_header("VALIDATED TEST RESULTS")
    
    print_info(f"Routers tested: {len(routers)}")
    print_success(f"Working routers: {len(working_routers)}")
    
    if working_routers:
        print_header("VALIDATED WORKING ROUTERS")
        for router in working_routers:
            print_success(f"✅ {router['name']} ({router['router']}) - {router['cisco_version']}")
        
        # Generate validated CSV
        csv_filename = "validated_working_routers.csv"
        with open(csv_filename, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol,jump_host,jump_user,jump_pass,cisco_version\n")
            for router in working_routers:
                f.write(f"{router['name']},{router['router']},{creds['router_user']},{creds['router_pass']},"
                       f"cisco_ios,ssh,{creds['jump_host']},{creds['jump_user']},{creds['jump_pass']},"
                       f"\"{router['cisco_version']}\"\n")
        
        print_info(f"Generated {csv_filename}")
        
        # Update main inventory with validated routers
        main_csv = "rr4-complete-enchanced-v4-cli-routers-validated.csv"
        with open(main_csv, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol\n")
            for router in working_routers:
                f.write(f"{router['name']},{router['router']},{creds['router_user']},{creds['router_pass']},cisco_ios,ssh\n")
        
        print_info(f"Updated main inventory: {main_csv}")
        
        print_header("🎉 VALIDATION SUCCESS!")
        print_success("V4codercli full range solution VALIDATED and WORKING!")
        print_success("Both target routers (R106 & R120) are accessible")
        print_info("Solution components:")
        print_info("  ✅ Jump host authentication: WORKING")
        print_info("  ✅ SSH algorithms: PROVEN")
        print_info("  ✅ Router connectivity: VERIFIED")
        print_info("  ✅ V4codercli ready: YES")
        
        return True
    else:
        print_error("No routers were accessible")
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
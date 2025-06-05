#!/usr/bin/env python3
"""
Full Range Connectivity Test for V4codercli
Tests router connectivity for IP range 172.16.39.100 to 172.16.39.150
Using VALIDATED working SSH parameters and jump host routing with credentials from .env-t
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

def load_credentials():
    """Load credentials from .env-t file."""
    env_file = Path(".env-t")
    credentials = {
        'jump_host': '172.16.39.128',
        'jump_user': 'root',
        'jump_pass': 'eve',
        'router_user': 'cisco',
        'router_pass': 'cisco'
    }
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
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
    """Test jump host connectivity."""
    print_info(f"Testing jump host {creds['jump_host']}...")
    
    try:
        # Test ping to jump host
        ping_cmd = ['ping', '-c', '2', '-W', '5', creds['jump_host']]
        result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print_success(f"Jump host {creds['jump_host']} is reachable")
            
            # Test SSH authentication
            ssh_cmd = [
                'sshpass', '-p', creds['jump_pass'], 'ssh',
                '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=no',
                f"{creds['jump_user']}@{creds['jump_host']}", 'echo SUCCESS'
            ]
            
            ssh_result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
            
            if ssh_result.returncode == 0 and 'SUCCESS' in ssh_result.stdout:
                print_success("Jump host authentication successful")
                return True
            else:
                print_error("Jump host authentication failed")
                return False
        else:
            print_error(f"Jump host {creds['jump_host']} is not reachable")
            return False
            
    except Exception as e:
        print_error(f"Jump host test error: {e}")
        return False

def test_router_connectivity(router_ip, creds):
    """Test router connectivity using validated solution."""
    try:
        # SSH command using validated credentials and algorithms
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
        
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=45)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output and 'Software' in output:
                return {
                    'success': True,
                    'router': router_ip,
                    'method': 'validated_ssh',
                    'output': output[:100],
                    'cisco_version': output.split(',')[1].strip() if ',' in output else 'Unknown'
                }
            
        return {
            'success': False,
            'router': router_ip,
            'error': 'connection_failed',
            'details': result.stderr.strip()[:100]
        }
                
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'router': router_ip,
            'error': 'timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'router': router_ip,
            'error': 'unexpected_error',
            'details': str(e)
        }

def test_router_batch(router_list, creds, max_workers=10):
    """Test multiple routers in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_router = {
            executor.submit(test_router_connectivity, router, creds): router 
            for router in router_list
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_router):
            router = future_to_router[future]
            try:
                result = future.result()
                results.append(result)
                
                if result['success']:
                    print_success(f"{router} - Connected ({result['method']})")
                else:
                    print_warning(f"{router} - Failed: {result['error']}")
                    
            except Exception as e:
                print_error(f"{router} - Exception: {e}")
                results.append({
                    'success': False,
                    'router': router,
                    'error': 'exception',
                    'details': str(e)
                })
    
    return results

def generate_ip_range(start_ip, end_ip):
    """Generate IP addresses in range."""
    start_parts = start_ip.split('.')
    end_parts = end_ip.split('.')
    
    base = '.'.join(start_parts[:3])
    start_host = int(start_parts[3])
    end_host = int(end_parts[3])
    
    return [f"{base}.{i}" for i in range(start_host, end_host + 1)]

def main():
    """Main function."""
    print_header("V4codercli Full Range Connectivity Test")
    print_info("Testing IP range: 172.16.39.100 to 172.16.39.150")
    print_info("Total devices: 51")
    print_info("Using VALIDATED working SSH parameters via jump host")
    
    # Load credentials
    creds = load_credentials()
    print_info(f"Jump host: {creds['jump_user']}@{creds['jump_host']}")
    
    # First test jump host
    if not test_jump_host(creds):
        print_error("Jump host not accessible - cannot proceed")
        return False
    
    # Generate full IP range
    router_ips = generate_ip_range("172.16.39.100", "172.16.39.150")
    
    print_info(f"Testing {len(router_ips)} devices in parallel...")
    
    # Test all routers
    start_time = time.time()
    results = test_router_batch(router_ips, creds, max_workers=15)
    end_time = time.time()
    
    # Analyze results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print_header("FULL RANGE CONNECTIVITY SUMMARY")
    
    total_time = end_time - start_time
    print_info(f"Total test time: {total_time:.2f} seconds")
    print_info(f"Total devices tested: {len(results)}")
    print_success(f"Successful connections: {len(successful)}")
    print_warning(f"Failed connections: {len(failed)}")
    print_info(f"Success rate: {(len(successful)/len(results)*100):.1f}%")
    
    if successful:
        print_header("WORKING DEVICES")
        for result in successful:
            cisco_version = result.get('cisco_version', 'Unknown')
            print_success(f"✅ {result['router']} - {cisco_version}")
        
        # Generate comprehensive CSV
        csv_filename = "full_range_validated_devices.csv"
        with open(csv_filename, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol,jump_host,jump_user,jump_pass,cisco_version\n")
            for result in successful:
                ip = result['router']
                name = f"R{ip.split('.')[-1]}"
                cisco_version = result.get('cisco_version', 'Unknown')
                f.write(f"{name},{ip},{creds['router_user']},{creds['router_pass']},"
                       f"cisco_ios,ssh,{creds['jump_host']},{creds['jump_user']},{creds['jump_pass']},"
                       f"\"{cisco_version}\"\n")
        
        print_info(f"Generated {csv_filename} with {len(successful)} working devices")
        
        # Update main device inventory
        main_csv = "rr4-complete-enchanced-v4-cli-routers-full-range-validated.csv"
        with open(main_csv, 'w') as f:
            f.write("device_name,ip_address,username,password,device_type,protocol\n")
            for result in successful:
                ip = result['router']
                name = f"R{ip.split('.')[-1]}"
                f.write(f"{name},{ip},{creds['router_user']},{creds['router_pass']},cisco_ios,ssh\n")
        
        print_info(f"Updated main inventory: {main_csv}")
        
    if failed:
        print_header("FAILED DEVICES ANALYSIS")
        error_summary = {}
        for result in failed:
            error_type = result.get('error', 'unknown')
            error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        for error_type, count in error_summary.items():
            print_warning(f"{error_type}: {count} devices")
        
        # List first 10 failed devices for reference
        print_info("Sample failed devices:")
        for result in failed[:10]:
            print_error(f"❌ {result['router']} - {result.get('error', 'unknown')}")
    
    # Update SSH configuration with validated credentials
    if successful:
        print_info("Deploying validated SSH configuration...")
        try:
            validated_config_path = Path("cisco_ssh_config_validated")
            
            config_content = f"""# Validated SSH Configuration for V4codercli
# Based on WORKING credentials and proven algorithms

# Jump Host Configuration
Host jumphost eve-ng
    HostName {creds['jump_host']}
    User {creds['jump_user']}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ConnectTimeout 15
    ServerAliveInterval 30
    ServerAliveCountMax 3

# ALL Cisco routers via jump host with VALIDATED algorithms
Host 172.16.39.1* cisco-* router-* R1*
    ProxyJump jumphost
    User {creds['router_user']}
    
    # PROVEN WORKING algorithms
    KexAlgorithms +diffie-hellman-group1-sha1
    HostKeyAlgorithms +ssh-rsa
    Ciphers +aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc
    
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ConnectTimeout 45
    ServerAliveInterval 60
    ServerAliveCountMax 5
    
    PreferredAuthentications password,keyboard-interactive
    PasswordAuthentication yes
    PubkeyAuthentication no
    
    Protocol 2
    RequestTTY yes
    ForwardAgent no
    ForwardX11 no
    LogLevel ERROR
"""
            
            with open(validated_config_path, 'w') as f:
                f.write(config_content)
                
            print_success("Created validated SSH configuration")
        except Exception as e:
            print_warning(f"Could not create validated SSH configuration: {e}")
    
    print_header("🎉 FULL RANGE TEST COMPLETE!")
    
    if len(successful) > 0:
        print_success(f"V4codercli ready with {len(successful)} validated working devices!")
        print_info("You can now use V4codercli with the validated device inventory")
        print_info("Next step: python3 start_rr4_cli_enhanced.py --option 1")
        print_info(f"Credentials stored in .env-t: {creds['jump_user']}@{creds['jump_host']} (password: {creds['jump_pass']})")
        return True
    else:
        print_error("No devices accessible in the full range")
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
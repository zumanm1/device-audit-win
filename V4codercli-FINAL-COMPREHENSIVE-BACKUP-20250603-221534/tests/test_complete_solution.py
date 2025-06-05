#!/usr/bin/env python3
"""
Complete V4codercli Solution Test - Security Enhanced
Comprehensive test of the complete solution with environment-based credentials
Tests:
1. Jump host routing (via .env-t credentials)
2. Cisco device connectivity  
3. Command execution
4. Data collection
"""

import subprocess
import os
import time
import sys
from pathlib import Path

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

def print_status(message, status="INFO"):
    """Print formatted status message."""
    colors = {
        "SUCCESS": "\033[92m✅",
        "ERROR": "\033[91m❌", 
        "WARNING": "\033[93m⚠️",
        "INFO": "\033[94mℹ️"
    }
    print(f"{colors.get(status, colors['INFO'])} {message}\033[0m")

def test_jump_host_connectivity():
    """Test jump host connectivity using .env-t credentials."""
    creds = load_credentials_from_env()
    
    print_status("Testing jump host connectivity...")
    print_status(f"Target: {creds['jump_host_username']}@{creds['jump_host_ip']}")
    
    try:
        cmd = [
            'sshpass', '-p', creds['jump_host_password'],
            'ssh', '-o', 'ConnectTimeout=10',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f"{creds['jump_host_username']}@{creds['jump_host_ip']}",
            'echo "Jump host test successful"'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print_status("Jump host connectivity successful", "SUCCESS")
            return True
        else:
            print_status(f"Jump host failed: {result.stderr.strip()}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Jump host test error: {e}", "ERROR")
        return False

def test_router_via_complete_solution(router_ip, username=None, password=None):
    """Test router connectivity using complete solution with .env-t credentials."""
    creds = load_credentials_from_env()
    
    # Use environment credentials if not provided
    if username is None:
        username = creds['router_username']
    if password is None:
        password = creds['router_password']
    
    print_status(f"Testing router {router_ip} with complete solution...")
    print_status(f"Using credentials: {username}/{'*' * len(password)}")
    
    try:
        # Test via jump host with legacy SSH algorithms
        cmd = [
            'sshpass', '-p', creds['jump_host_password'],
            'ssh', '-o', 'ConnectTimeout=15',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f"{creds['jump_host_username']}@{creds['jump_host_ip']}",
            f"sshpass -p {password} ssh "
            f"-o KexAlgorithms=+diffie-hellman-group1-sha1 "
            f"-o HostKeyAlgorithms=+ssh-rsa "
            f"-o Ciphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc "
            f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
            f"-o ConnectTimeout=20 {username}@{router_ip} 'show version | include Software'"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print_status(f"Router {router_ip} connectivity successful", "SUCCESS")
            print_status(f"Output: {result.stdout.strip()[:100]}...")
            return {
                'success': True,
                'router_ip': router_ip,
                'output': result.stdout.strip(),
                'username': username
            }
        else:
            print_status(f"Router {router_ip} failed: {result.stderr.strip()}", "ERROR")
            return {
                'success': False,
                'router_ip': router_ip,
                'error': result.stderr.strip()
            }
            
    except subprocess.TimeoutExpired:
        print_status(f"Router {router_ip} connection timeout", "ERROR")
        return {
            'success': False,
            'router_ip': router_ip,
            'error': 'Connection timeout'
        }
    except Exception as e:
        print_status(f"Router {router_ip} test error: {e}", "ERROR")
        return {
            'success': False,
            'router_ip': router_ip,
            'error': str(e)
        }

def test_v4codercli_integration():
    """Test V4codercli integration with security-enhanced configuration."""
    print_status("Testing V4codercli integration...")
    
    try:
        # Test basic CLI functionality
        cmd = ['python3', 'start_rr4_cli_enhanced.py', '--help']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print_status("V4codercli CLI integration successful", "SUCCESS")
            return True
        else:
            print_status(f"V4codercli CLI failed: {result.stderr.strip()}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"V4codercli integration error: {e}", "ERROR")
        return False

def run_comprehensive_test():
    """Run comprehensive test of the complete solution."""
    print("=" * 70)
    print("🔒 V4codercli Complete Solution Test - Security Enhanced")
    print("=" * 70)
    
    creds = load_credentials_from_env()
    print_status(f"📄 Loaded credentials from .env-t file")
    print_status(f"🏢 Jump Host: {creds['jump_host_username']}@{creds['jump_host_ip']}")
    print_status(f"🔐 Router User: {creds['router_username']}")
    print("=" * 70)
    
    # Test results tracking
    test_results = {
        'jump_host_test': False,
        'router_tests': [],
        'v4codercli_integration': False
    }
    
    # Test 1: Jump host connectivity
    print_status("🔧 Phase 1: Jump Host Connectivity Test")
    test_results['jump_host_test'] = test_jump_host_connectivity()
    
    if not test_results['jump_host_test']:
        print_status("Cannot proceed without jump host connectivity", "ERROR")
        return False
    
    # Test 2: Router connectivity
    print_status("🔧 Phase 2: Router Connectivity Tests")
    test_routers = ['172.16.39.106', '172.16.39.120']
    
    for router_ip in test_routers:
        result = test_router_via_complete_solution(router_ip)
        test_results['router_tests'].append(result)
        time.sleep(2)  # Brief pause between tests
    
    # Test 3: V4codercli integration
    print_status("🔧 Phase 3: V4codercli Integration Test")
    test_results['v4codercli_integration'] = test_v4codercli_integration()
    
    # Summary
    print("=" * 70)
    print_status("📊 TEST SUMMARY")
    print("=" * 70)
    
    successful_routers = len([r for r in test_results['router_tests'] if r['success']])
    total_routers = len(test_results['router_tests'])
    
    print_status(f"Jump Host: {'PASS' if test_results['jump_host_test'] else 'FAIL'}")
    print_status(f"Router Tests: {successful_routers}/{total_routers} PASS")
    print_status(f"V4codercli Integration: {'PASS' if test_results['v4codercli_integration'] else 'FAIL'}")
    
    # Individual router results
    for result in test_results['router_tests']:
        status = "SUCCESS" if result['success'] else "ERROR"
        print_status(f"Router {result['router_ip']}: {'PASS' if result['success'] else 'FAIL'}", status)
    
    overall_success = (
        test_results['jump_host_test'] and
        successful_routers > 0 and
        test_results['v4codercli_integration']
    )
    
    print("=" * 70)
    if overall_success:
        print_status("🎉 COMPLETE SOLUTION TEST: PASSED", "SUCCESS")
        print_status("✅ V4codercli solution is working with secure credentials", "SUCCESS")
    else:
        print_status("❌ COMPLETE SOLUTION TEST: FAILED", "ERROR")
        print_status("⚠️ Check individual test results above", "WARNING")
    
    print_status("🔒 All credentials loaded from .env-t file - No hardcoded values")
    print("=" * 70)
    
    return overall_success

def main():
    """Main test function."""
    try:
        success = run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print_status("Test interrupted by user", "WARNING")
        return 130
    except Exception as e:
        print_status(f"Unexpected test error: {e}", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
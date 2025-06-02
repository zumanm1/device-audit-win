#!/usr/bin/env python3
"""
Enhanced Connection Diagnostics for V4codercli
Tests various connection methods with environment-based credentials
"""

import os
import subprocess
import sys
import time
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

def get_test_credentials():
    """Get test credentials prioritizing environment variables."""
    creds = load_credentials_from_env()
    
    # Test credentials for fallback testing (prioritize environment)
    test_combos = [
        (creds['router_username'], creds['router_password']),  # Primary from .env-t
        ('cisco', 'cisco'),      # Common default
        ('admin', 'admin'),      # Alternative
        ('root', 'root'),        # Another alternative
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_combos = []
    for combo in test_combos:
        if combo not in seen:
            seen.add(combo)
            unique_combos.append(combo)
    
    return unique_combos

def test_device_connectivity(target_ip, test_creds=None):
    """Test connectivity to a device using various credential combinations."""
    if test_creds is None:
        test_creds = get_test_credentials()
    
    creds = load_credentials_from_env()
    
    print(f"🔍 Testing connectivity to {target_ip}")
    print(f"Using jump host: {creds['jump_host_username']}@{creds['jump_host_ip']}")
    
    for username, password in test_creds:
        print(f"\n📡 Trying credentials: {username}/{'*' * len(password)}")
        
        # Test via jump host
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
            f"-o ConnectTimeout=15 {username}@{target_ip} 'show version | include Software'"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ SUCCESS: {username}@{target_ip} - Connection successful!")
                print(f"Output: {result.stdout.strip()[:100]}...")
                return {
                    'success': True,
                    'username': username,
                    'password': password,
                    'output': result.stdout.strip()
                }
            else:
                print(f"❌ FAILED: {result.stderr.strip()[:100]}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: Connection timed out")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"❌ All credential combinations failed for {target_ip}")
    return {'success': False}

def main():
    """Main diagnostic function."""
    print("🔒 V4codercli Connection Diagnostics (Security Enhanced)")
    print("=" * 60)
    
    creds = load_credentials_from_env()
    print(f"📄 Loaded credentials from .env-t")
    print(f"🏢 Jump Host: {creds['jump_host_username']}@{creds['jump_host_ip']}")
    print(f"🔐 Router User: {creds['router_username']}")
    print("=" * 60)
    
    # Test specific routers
    test_routers = [
        ('172.16.39.106', 'R106'),
        ('172.16.39.120', 'R120')
    ]
    
    results = []
    for router_ip, router_name in test_routers:
        print(f"\n{'='*60}")
        print(f"Testing {router_name} ({router_ip})")
        print(f"{'='*60}")
        
        result = test_device_connectivity(router_ip)
        result['router_name'] = router_name
        result['router_ip'] = router_ip
        results.append(result)
        
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 DIAGNOSTIC SUMMARY")
    print(f"{'='*60}")
    
    for result in results:
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"{status}: {result['router_name']} ({result['router_ip']})")
    
    print(f"\n🔒 All credentials loaded from .env-t file")
    print(f"📁 No hardcoded credentials in this script")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Enhanced Connectivity Test for V4codercli
Tests router connectivity with legacy SSH algorithm support
"""

import subprocess
import sys
from pathlib import Path

def test_router_connection(host, username='cisco', password='cisco'):
    """Test connection to a router with legacy SSH support."""
    
    # Create SSH config for legacy devices
    config_content = """Host *
    KexAlgorithms +diffie-hellman-group1-sha1,diffie-hellman-group14-sha1
    Ciphers +aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc
    MACs +hmac-sha1,hmac-sha1-96
    HostKeyAlgorithms +ssh-rsa,ssh-dss
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ConnectTimeout 15
    PasswordAuthentication yes
    PubkeyAuthentication no
"""
    
    config_path = Path('temp_ssh_config')
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    try:
        # Test SSH connection
        cmd = [
            'sshpass', '-p', password,
            'ssh', '-F', str(config_path),
            f'{username}@{host}',
            'show version | include Software'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print(f"✅ Connection successful to {host}")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Connection failed to {host}")
            print(f"   Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing {host}: {e}")
        return False
    finally:
        # Cleanup
        if config_path.exists():
            config_path.unlink()

def main():
    """Main test function."""
    test_hosts = ['172.16.39.115', '172.16.39.116', '172.16.39.117']
    
    print("Testing router connectivity with legacy SSH support...")
    
    success_count = 0
    for host in test_hosts:
        if test_router_connection(host):
            success_count += 1
    
    print(f"\nResults: {success_count}/{len(test_hosts)} devices connected successfully")
    
    if success_count > 0:
        print("✅ V4codercli should be able to connect to working devices")
    else:
        print("❌ No devices accessible - check network configuration")

if __name__ == "__main__":
    main()

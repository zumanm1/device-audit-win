#!/usr/bin/env python3
"""
Update Connection Manager for V4codercli
Enhances the connection manager to handle legacy SSH algorithms and connectivity issues
"""

import os
import sys
from pathlib import Path
import shutil
import subprocess

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

def backup_original_file(file_path):
    """Create a backup of the original file."""
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    if file_path.exists() and not backup_path.exists():
        shutil.copy2(file_path, backup_path)
        print_success(f"Created backup: {backup_path}")
        return True
    return False

def update_connection_manager():
    """Update the connection manager with enhanced connectivity."""
    print_header("Updating Connection Manager")
    
    core_dir = Path('rr4_complete_enchanced_v4_cli_core')
    connection_manager_path = core_dir / 'connection_manager.py'
    
    if not connection_manager_path.exists():
        print_error(f"Connection manager not found: {connection_manager_path}")
        return False
    
    # Backup original
    backup_original_file(connection_manager_path)
    
    # Read current content
    with open(connection_manager_path, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'LEGACY_SSH_ALGORITHMS' in content:
        print_info("Connection manager already has legacy SSH support")
        return True
    
    # Enhanced SSH configuration for legacy devices
    enhanced_ssh_code = '''
# Enhanced SSH Configuration for Legacy Cisco Devices
LEGACY_SSH_ALGORITHMS = {
    'kex_algorithms': [
        'diffie-hellman-group1-sha1',
        'diffie-hellman-group14-sha1',
        'diffie-hellman-group14-sha256',
        'diffie-hellman-group16-sha512'
    ],
    'ciphers': [
        'aes128-cbc', '3des-cbc', 'aes192-cbc', 'aes256-cbc',
        'aes128-ctr', 'aes192-ctr', 'aes256-ctr'
    ],
    'macs': [
        'hmac-sha1', 'hmac-sha1-96',
        'hmac-sha2-256', 'hmac-sha2-512'
    ],
    'host_key_algorithms': [
        'ssh-rsa', 'ssh-dss',
        'rsa-sha2-256', 'rsa-sha2-512'
    ]
}

def create_legacy_ssh_config():
    """Create SSH config file for legacy device support."""
    config_content = f"""# SSH Configuration for Legacy Cisco Devices
Host cisco-legacy cisco-* 172.16.39.* 10.* 192.168.*
    # Enable legacy key exchange methods
    KexAlgorithms +{','.join(LEGACY_SSH_ALGORITHMS['kex_algorithms'])}
    
    # Enable legacy ciphers
    Ciphers +{','.join(LEGACY_SSH_ALGORITHMS['ciphers'])}
    
    # Enable legacy MAC algorithms
    MACs +{','.join(LEGACY_SSH_ALGORITHMS['macs'])}
    
    # Enable legacy host key algorithms
    HostKeyAlgorithms +{','.join(LEGACY_SSH_ALGORITHMS['host_key_algorithms'])}
    
    # Connection optimization
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ConnectTimeout 15
    ServerAliveInterval 30
    ServerAliveCountMax 3
    
    # Authentication settings
    PreferredAuthentications password,keyboard-interactive
    PasswordAuthentication yes
    PubkeyAuthentication no
    
    # Protocol and feature settings
    Protocol 2
    RequestTTY yes
    ForwardAgent no
    ForwardX11 no
    LogLevel ERROR
"""
    
    config_path = Path(__file__).parent / 'cisco_legacy_ssh_config'
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    return config_path

def get_enhanced_ssh_command(host, username, password, command='show version'):
    """Get SSH command with legacy algorithm support."""
    ssh_config = create_legacy_ssh_config()
    
    # Multiple command variations to try
    commands = [
        # Using sshpass with legacy config
        [
            'sshpass', '-p', password,
            'ssh', '-F', str(ssh_config),
            '-o', 'ConnectTimeout=15',
            '-o', 'BatchMode=yes',
            f'{username}@{host}',
            command
        ],
        # Direct SSH with legacy algorithms
        [
            'sshpass', '-p', password,
            'ssh',
            '-o', f'KexAlgorithms=+{",".join(LEGACY_SSH_ALGORITHMS["kex_algorithms"])}',
            '-o', f'Ciphers=+{",".join(LEGACY_SSH_ALGORITHMS["ciphers"])}',
            '-o', f'MACs=+{",".join(LEGACY_SSH_ALGORITHMS["macs"])}',
            '-o', f'HostKeyAlgorithms=+{",".join(LEGACY_SSH_ALGORITHMS["host_key_algorithms"])}',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'ConnectTimeout=15',
            f'{username}@{host}',
            command
        ]
    ]
    
    return commands

def test_enhanced_ssh_connection(host, username='cisco', password='cisco'):
    """Test SSH connection with enhanced algorithms."""
    print_info(f"Testing enhanced SSH connection to {host}")
    
    commands = get_enhanced_ssh_command(host, username, password, 'show version | include Software')
    
    for i, cmd in enumerate(commands):
        try:
            print_info(f"Trying SSH method {i+1}/{len(commands)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            
            if result.returncode == 0:
                print_success(f"SSH connection successful with method {i+1}")
                return {
                    'success': True,
                    'method': i+1,
                    'output': result.stdout.strip(),
                    'command': cmd
                }
            else:
                error_msg = result.stderr.strip()
                print_warning(f"Method {i+1} failed: {error_msg[:100]}")
                
        except subprocess.TimeoutExpired:
            print_warning(f"Method {i+1} timed out")
        except Exception as e:
            print_warning(f"Method {i+1} error: {e}")
    
    return {'success': False, 'error': 'All SSH methods failed'}
'''
    
    # Find a good place to insert the code (after imports)
    import_section_end = content.find('\n\nclass')
    if import_section_end == -1:
        import_section_end = content.find('\ndef')
    if import_section_end == -1:
        import_section_end = len(content)
    
    # Insert the enhanced SSH code
    updated_content = (
        content[:import_section_end] + 
        enhanced_ssh_code + 
        content[import_section_end:]
    )
    
    # Write updated content
    with open(connection_manager_path, 'w') as f:
        f.write(updated_content)
    
    print_success("Updated connection manager with legacy SSH support")
    return True

def create_connectivity_test_function():
    """Create a standalone connectivity test function."""
    test_code = '''#!/usr/bin/env python3
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
    
    print(f"\\nResults: {success_count}/{len(test_hosts)} devices connected successfully")
    
    if success_count > 0:
        print("✅ V4codercli should be able to connect to working devices")
    else:
        print("❌ No devices accessible - check network configuration")

if __name__ == "__main__":
    main()
'''
    
    test_file = Path('test_enhanced_connectivity.py')
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    test_file.chmod(0o755)
    print_success(f"Created connectivity test script: {test_file}")
    return test_file

def create_eveng_lab_guide():
    """Create a guide for EVE-NG lab connectivity issues."""
    guide_content = '''# EVE-NG Router Connectivity Guide

## Issue: Filtered Management Interfaces

Your EVE-NG lab has all router management interfaces (SSH/Telnet) filtered by default.
This is a security feature but prevents external management access.

## Solutions:

### Option 1: Enable Management Access on Routers
Connect to each router via console and configure:

```
enable
configure terminal
!
! Enable SSH
ip domain-name lab.local
crypto key generate rsa modulus 1024
username cisco password cisco
username cisco privilege 15
!
! Configure VTY lines
line vty 0 15
 transport input ssh telnet
 login local
 privilege level 15
!
! Optional: Configure management ACL
access-list 100 permit tcp any any eq 22
access-list 100 permit tcp any any eq 23
interface vlan1
 ip access-group 100 in
!
end
write memory
```

### Option 2: Use EVE-NG Console Access
1. Access routers via EVE-NG web console
2. Configure devices from console interface
3. Use V4codercli with console connections

### Option 3: Configure Network Access
From EVE-NG topology:
1. Add management network connections
2. Configure proper routing
3. Remove security filters if in lab environment

## Testing Connectivity

Use the provided test script:
```bash
python3 test_enhanced_connectivity.py
```

This will test legacy SSH connectivity to your routers.

## V4codercli Configuration

Once connectivity is established, V4codercli will automatically use the enhanced
SSH configuration for legacy algorithm support.

## Common Issues:

1. **SSH Key Exchange Failure**: Fixed by legacy algorithm support
2. **Connection Timeout**: Check network routing and firewall rules  
3. **Authentication Failure**: Verify username/password credentials
4. **Port Filtered**: Enable SSH/Telnet on router management interface

## For Production Networks:
- Use proper SSH key authentication
- Configure appropriate access controls
- Enable logging and monitoring
- Regular security updates
'''
    
    guide_file = Path('EVE-NG_Connectivity_Guide.md')
    with open(guide_file, 'w') as f:
        f.write(guide_content)
    
    print_success(f"Created EVE-NG connectivity guide: {guide_file}")
    return guide_file

def main():
    """Main update function."""
    print_header("V4codercli Connection Manager Enhancement")
    print_info("Adding legacy SSH algorithm support and connectivity troubleshooting")
    
    # Update connection manager
    if update_connection_manager():
        print_success("Connection manager updated successfully")
    else:
        print_error("Failed to update connection manager")
        return False
    
    # Create connectivity test
    test_file = create_connectivity_test_function()
    
    # Create EVE-NG guide
    guide_file = create_eveng_lab_guide()
    
    print_header("Update Complete")
    print_success("V4codercli now supports legacy SSH algorithms")
    print_info("Next steps:")
    print_info(f"1. Review the guide: {guide_file}")
    print_info(f"2. Test connectivity: python3 {test_file}")
    print_info("3. Configure router management access if needed")
    print_info("4. Run V4codercli with enhanced connectivity")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\nUpdate interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Update error: {e}")
        sys.exit(1) 
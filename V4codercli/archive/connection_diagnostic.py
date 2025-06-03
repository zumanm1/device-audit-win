#!/usr/bin/env python3
"""
Connection Diagnostic Tool for RR4 Complete Enhanced v4 CLI

This tool provides comprehensive diagnostics for connection issues including:
- Jump host connectivity testing
- Direct device connectivity testing
- SSH tunnel testing through jump host
- Network routing and DNS resolution tests
- Environment configuration validation

Author: AI Assistant
Version: 1.0.0
Created: 2025-05-29
"""

import os
import sys
import time
import socket
import logging
import subprocess
import paramiko
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Add the core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rr4-complete-enchanced-v4-cli-core'))

from inventory_loader import InventoryLoader
from connection_manager import ConnectionManager, ConnectionDiagnostics

class NetworkDiagnostics:
    """Comprehensive network diagnostics for troubleshooting connectivity issues."""
    
    def __init__(self, env_file: str = "rr4-complete-enchanced-v4-cli.env-t"):
        self.env_file = env_file
        self.logger = logging.getLogger('connection_diagnostics')
        self.setup_logging()
        self.load_environment()
        
    def setup_logging(self):
        """Setup logging for diagnostics."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('connection_diagnostics.log')
            ]
        )
    
    def load_environment(self):
        """Load environment configuration."""
        if not Path(self.env_file).exists():
            raise FileNotFoundError(f"Environment file not found: {self.env_file}")
        
        load_dotenv(self.env_file)
        
        self.jump_host_config = {
            'hostname': os.getenv('JUMP_HOST_IP'),
            'username': os.getenv('JUMP_HOST_USERNAME'),
            'password': os.getenv('JUMP_HOST_PASSWORD'),
            'port': int(os.getenv('JUMP_HOST_PORT', 22))
        }
        
        self.device_credentials = {
            'username': os.getenv('DEVICE_USERNAME', 'cisco'),
            'password': os.getenv('DEVICE_PASSWORD', 'cisco')
        }
        
        print(f"🔧 Environment Configuration:")
        print(f"   Jump Host: {self.jump_host_config['hostname']}:{self.jump_host_config['port']}")
        print(f"   Jump Host User: {self.jump_host_config['username']}")
        print(f"   Device Credentials: {self.device_credentials['username']}")
        print()
    
    def test_basic_connectivity(self, hostname: str, port: int = 22, timeout: int = 10) -> Dict[str, Any]:
        """Test basic TCP connectivity to a host."""
        result = {
            'hostname': hostname,
            'port': port,
            'reachable': False,
            'response_time': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            connection_result = sock.connect_ex((hostname, port))
            sock.close()
            
            response_time = time.time() - start_time
            result['response_time'] = response_time
            
            if connection_result == 0:
                result['reachable'] = True
                self.logger.info(f"✅ {hostname}:{port} is reachable ({response_time:.2f}s)")
            else:
                result['error'] = f"Connection refused (error code: {connection_result})"
                self.logger.warning(f"❌ {hostname}:{port} is not reachable: {result['error']}")
                
        except socket.timeout:
            result['error'] = "Connection timeout"
            self.logger.warning(f"❌ {hostname}:{port} connection timeout after {timeout}s")
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ {hostname}:{port} connection error: {e}")
        
        return result
    
    def test_dns_resolution(self, hostname: str) -> Dict[str, Any]:
        """Test DNS resolution for hostname."""
        result = {
            'hostname': hostname,
            'resolved': False,
            'ip_address': None,
            'error': None
        }
        
        try:
            ip_address = socket.gethostbyname(hostname)
            result['resolved'] = True
            result['ip_address'] = ip_address
            self.logger.info(f"✅ DNS: {hostname} → {ip_address}")
        except Exception as e:
            result['error'] = str(e)
            self.logger.warning(f"❌ DNS resolution failed for {hostname}: {e}")
        
        return result
    
    def test_jump_host_connectivity(self) -> Dict[str, Any]:
        """Test jump host SSH connectivity."""
        result = {
            'success': False,
            'response_time': None,
            'error': None,
            'ssh_version': None
        }
        
        self.logger.info("🔗 Testing jump host connectivity...")
        
        # First test basic connectivity
        basic_test = self.test_basic_connectivity(
            self.jump_host_config['hostname'], 
            self.jump_host_config['port']
        )
        
        if not basic_test['reachable']:
            result['error'] = f"Jump host not reachable: {basic_test['error']}"
            return result
        
        # Test SSH connection
        try:
            start_time = time.time()
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                hostname=self.jump_host_config['hostname'],
                username=self.jump_host_config['username'],
                password=self.jump_host_config['password'],
                port=self.jump_host_config['port'],
                timeout=30
            )
            
            # Test command execution
            stdin, stdout, stderr = ssh.exec_command('echo "Jump host test successful"')
            output = stdout.read().decode().strip()
            
            # Get SSH version
            try:
                stdin, stdout, stderr = ssh.exec_command('ssh -V')
                ssh_version = stderr.read().decode().strip()
                result['ssh_version'] = ssh_version
            except:
                pass
            
            result['success'] = True
            result['response_time'] = time.time() - start_time
            
            ssh.close()
            
            self.logger.info(f"✅ Jump host SSH connection successful ({result['response_time']:.2f}s)")
            self.logger.info(f"   Output: {output}")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ Jump host SSH connection failed: {e}")
        
        return result
    
    def test_device_connectivity_through_jump_host(self, device_ip: str) -> Dict[str, Any]:
        """Test device connectivity through jump host tunnel."""
        result = {
            'device_ip': device_ip,
            'success': False,
            'tunnel_established': False,
            'device_reachable': False,
            'error': None
        }
        
        self.logger.info(f"🔗 Testing device {device_ip} through jump host...")
        
        try:
            # Create SSH connection to jump host
            jump_ssh = paramiko.SSHClient()
            jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            jump_ssh.connect(
                hostname=self.jump_host_config['hostname'],
                username=self.jump_host_config['username'],
                password=self.jump_host_config['password'],
                port=self.jump_host_config['port'],
                timeout=30
            )
            
            # Create tunnel through jump host
            transport = jump_ssh.get_transport()
            dest_addr = (device_ip, 22)
            local_addr = ('127.0.0.1', 0)
            
            channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
            result['tunnel_established'] = True
            self.logger.info(f"✅ SSH tunnel to {device_ip} established")
            
            # Test device SSH connection through tunnel
            device_ssh = paramiko.SSHClient()
            device_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            device_ssh.connect(
                hostname=device_ip,
                username=self.device_credentials['username'],
                password=self.device_credentials['password'],
                port=22,
                timeout=30,
                sock=channel
            )
            
            # Test command execution
            stdin, stdout, stderr = device_ssh.exec_command('show version | include uptime')
            output = stdout.read().decode().strip()
            
            result['success'] = True
            result['device_reachable'] = True
            
            device_ssh.close()
            channel.close()
            jump_ssh.close()
            
            self.logger.info(f"✅ Device {device_ip} reachable through jump host")
            self.logger.info(f"   Device response: {output[:100]}...")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ Device {device_ip} not reachable through jump host: {e}")
            
            # Clean up connections
            try:
                if 'channel' in locals():
                    channel.close()
                if 'jump_ssh' in locals():
                    jump_ssh.close()
            except:
                pass
        
        return result
    
    def test_network_routes(self) -> Dict[str, Any]:
        """Test network routing information."""
        result = {
            'default_gateway': None,
            'routing_table': [],
            'error': None
        }
        
        try:
            # Get default gateway
            if sys.platform.startswith('linux'):
                gateway_cmd = "ip route | grep default"
            else:
                gateway_cmd = "route -n get default"
            
            gateway_result = subprocess.run(
                gateway_cmd.split(), 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if gateway_result.returncode == 0:
                result['default_gateway'] = gateway_result.stdout.strip()
                self.logger.info(f"🛣️  Default gateway: {result['default_gateway']}")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.warning(f"❌ Could not get routing information: {e}")
        
        return result
    
    def run_comprehensive_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive connectivity diagnostics."""
        self.logger.info("🔍 Starting Comprehensive Connection Diagnostics")
        self.logger.info("=" * 60)
        
        diagnostics = {
            'timestamp': time.time(),
            'environment': {
                'jump_host': self.jump_host_config,
                'device_credentials': self.device_credentials
            },
            'tests': {}
        }
        
        # Test 1: Jump host connectivity
        print("\n1️⃣  Testing Jump Host Connectivity")
        print("-" * 40)
        diagnostics['tests']['jump_host'] = self.test_jump_host_connectivity()
        
        # Test 2: Network routing
        print("\n2️⃣  Testing Network Configuration")
        print("-" * 40)
        diagnostics['tests']['network'] = self.test_network_routes()
        
        # Test 3: Load device inventory and test devices
        print("\n3️⃣  Testing Device Connectivity")
        print("-" * 40)
        
        try:
            # Load device inventory
            inventory_loader = InventoryLoader("rr4-complete-enchanced-v4-cli-routers01.csv")
            devices = inventory_loader.load_csv_inventory()
            
            diagnostics['tests']['devices'] = {}
            
            for device in devices[:3]:  # Test first 3 devices to avoid long waits
                device_ip = device.management_ip
                
                print(f"\n   Testing {device.hostname} ({device_ip}):")
                
                # Test basic connectivity (direct)
                basic_test = self.test_basic_connectivity(device_ip)
                
                # Test connectivity through jump host
                jump_test = self.test_device_connectivity_through_jump_host(device_ip)
                
                diagnostics['tests']['devices'][device.hostname] = {
                    'ip': device_ip,
                    'direct_connectivity': basic_test,
                    'jump_host_connectivity': jump_test
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error testing devices: {e}")
            diagnostics['tests']['devices'] = {'error': str(e)}
        
        # Summary
        print("\n📋 Diagnostic Summary")
        print("=" * 40)
        self.print_diagnostic_summary(diagnostics)
        
        return diagnostics
    
    def print_diagnostic_summary(self, diagnostics: Dict[str, Any]):
        """Print a summary of diagnostic results."""
        
        # Jump host status
        jump_host = diagnostics['tests'].get('jump_host', {})
        if jump_host.get('success'):
            print("✅ Jump Host: Connected successfully")
        else:
            print(f"❌ Jump Host: Connection failed - {jump_host.get('error', 'Unknown error')}")
        
        # Device status
        devices = diagnostics['tests'].get('devices', {})
        if isinstance(devices, dict) and 'error' not in devices:
            successful_devices = []
            failed_devices = []
            
            for hostname, device_test in devices.items():
                if device_test.get('jump_host_connectivity', {}).get('success'):
                    successful_devices.append(hostname)
                else:
                    failed_devices.append(hostname)
            
            print(f"✅ Device Connectivity: {len(successful_devices)} successful, {len(failed_devices)} failed")
            
            if failed_devices:
                print(f"   Failed devices: {', '.join(failed_devices)}")
        else:
            print("❌ Device Testing: Failed to test devices")
        
        # Recommendations
        print("\n💡 Recommendations:")
        
        if not jump_host.get('success'):
            print("   1. Check jump host connectivity and credentials")
            print("   2. Verify jump host IP address and port")
            print("   3. Ensure jump host SSH service is running")
        
        if diagnostics['tests'].get('devices', {}).get('error'):
            print("   4. Check device inventory file")
            print("   5. Verify device IP addresses are correct")
        
        print("   6. Check network routing and firewall rules")
        print("   7. Verify SSH is enabled on target devices")


def main():
    """Main diagnostic function."""
    print("🔍 RR4 Connection Diagnostics Tool")
    print("=" * 50)
    
    try:
        diagnostics = NetworkDiagnostics()
        results = diagnostics.run_comprehensive_diagnostics()
        
        # Save results
        import json
        with open('connection_diagnostics_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Full results saved to: connection_diagnostics_results.json")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        logging.error(f"Diagnostic error: {e}", exc_info=True)


if __name__ == "__main__":
    main() 
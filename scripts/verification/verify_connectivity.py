#!/usr/bin/env python3
"""
Verify Connectivity to Network Devices
- Tests ping and SSH connectivity to devices from jump host
- Uses paramiko for SSH testing
- Reports detailed results for troubleshooting
"""

import argparse
import asyncio
import csv
import io
import os
import paramiko
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
JUMP_HOST = "172.16.39.128"
JUMP_USERNAME = "root"
JUMP_PASSWORD = "eve"
INVENTORY_FILE = "/root/za-con/inventories/network-inventory.csv"
TIMEOUT = 5  # seconds

class NetworkValidator:
    """Network device connectivity validator"""
    
    def __init__(self, jump_host, jump_username, jump_password):
        self.jump_host = jump_host
        self.jump_username = jump_username
        self.jump_password = jump_password
        self.jump_client = None
    
    async def connect_to_jump_host(self) -> bool:
        """Connect to the jump host"""
        print(f"Connecting to jump host {self.jump_host}...")
        try:
            self.jump_client = paramiko.SSHClient()
            self.jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.jump_client.connect(
                self.jump_host, 
                username=self.jump_username, 
                password=self.jump_password,
                timeout=TIMEOUT
            )
            
            # Test the connection
            stdin, stdout, stderr = self.jump_client.exec_command("echo 'Connection test'")
            output = stdout.read().decode('utf-8').strip()
            if output == 'Connection test':
                print(f"✅ Successfully connected to jump host {self.jump_host}")
                return True
            else:
                print(f"❌ Failed to connect to jump host - unexpected output: {output}")
                return False
        except Exception as e:
            print(f"❌ Failed to connect to jump host: {e}")
            return False
    
    def close_jump_host(self):
        """Close connection to jump host"""
        if self.jump_client:
            self.jump_client.close()
            print(f"Closed connection to jump host {self.jump_host}")
    
    async def ping_device(self, ip_address) -> Tuple[bool, str]:
        """Ping a device from the jump host"""
        if not self.jump_client:
            return False, "Jump host not connected"
        
        try:
            command = f"/bin/ping -c 2 -W 2 {ip_address}"
            print(f"Pinging {ip_address} from jump host...")
            
            stdin, stdout, stderr = self.jump_client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            
            if exit_status == 0:
                print(f"✅ Ping to {ip_address} successful")
                return True, output
            else:
                print(f"❌ Ping to {ip_address} failed (exit status: {exit_status})")
                return False, output
        except Exception as e:
            print(f"❌ Error during ping to {ip_address}: {e}")
            return False, str(e)
    
    async def test_ssh_connection(self, ip_address, username, password) -> Tuple[bool, str]:
        """Test SSH connection to a device through the jump host"""
        if not self.jump_client:
            return False, "Jump host not connected"
        
        try:
            print(f"Testing SSH to {ip_address} with user '{username}'...")
            
            # Create a direct-tcpip channel
            src_addr = ('127.0.0.1', 0)
            dst_addr = (ip_address, 22)
            channel = self.jump_client.get_transport().open_channel("direct-tcpip", dst_addr, src_addr)
            
            # Try to establish SSH connection through the channel
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                client.connect(
                    ip_address,
                    username=username,
                    password=password,
                    sock=channel,
                    timeout=TIMEOUT,
                    allow_agent=False,
                    look_for_keys=False
                )
                
                # Test the connection with a simple command
                stdin, stdout, stderr = client.exec_command("show version")
                exit_status = stdout.channel.recv_exit_status()
                output = stdout.read().decode('utf-8')
                
                client.close()
                
                if exit_status == 0:
                    print(f"✅ SSH to {ip_address} successful")
                    return True, "SSH connection successful"
                else:
                    print(f"❌ SSH command execution failed (exit status: {exit_status})")
                    return False, "SSH command execution failed"
                
            except paramiko.AuthenticationException as auth_err:
                print(f"❌ SSH authentication failed: {auth_err}")
                return False, f"Authentication failed: {auth_err}"
            except paramiko.SSHException as ssh_err:
                print(f"❌ SSH connection error: {ssh_err}")
                return False, f"SSH error: {ssh_err}"
            except Exception as e:
                print(f"❌ SSH connection failed: {e}")
                return False, str(e)
                
        except Exception as e:
            print(f"❌ Error creating channel to {ip_address}: {e}")
            return False, str(e)
    
    async def load_inventory(self, inventory_file) -> List[Dict]:
        """Load inventory from CSV file"""
        try:
            with open(inventory_file, 'r') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            print(f"❌ Error loading inventory: {e}")
            return []
    
    async def validate_devices(self, inventory_file) -> Dict:
        """Validate connectivity to all devices in inventory"""
        print(f"\n===== Validating Network Connectivity =====")
        print(f"Jump Host: {self.jump_host}")
        print(f"Inventory File: {inventory_file}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Connect to jump host
        jump_connected = await self.connect_to_jump_host()
        if not jump_connected:
            return {"success": False, "message": "Failed to connect to jump host"}
        
        # Load inventory
        devices = await self.load_inventory(inventory_file)
        if not devices:
            self.close_jump_host()
            return {"success": False, "message": "Failed to load inventory or empty inventory"}
        
        print(f"Loaded {len(devices)} devices from inventory\n")
        
        # Test connectivity to each device
        results = []
        
        for device in devices:
            device_result = {
                "hostname": device.get("hostname", "unknown"),
                "ip": device.get("ip", "unknown"),
                "device_type": device.get("device_type", "unknown"),
                "ping_status": False,
                "ping_output": "",
                "ssh_status": False,
                "ssh_output": ""
            }
            
            # Test ping
            ping_success, ping_output = await self.ping_device(device["ip"])
            device_result["ping_status"] = ping_success
            device_result["ping_output"] = ping_output
            
            # Test SSH if ping successful
            if ping_success:
                ssh_success, ssh_output = await self.test_ssh_connection(
                    device["ip"], 
                    device["username"], 
                    device["password"]
                )
                device_result["ssh_status"] = ssh_success
                device_result["ssh_output"] = ssh_output
            
            results.append(device_result)
        
        # Close jump host connection
        self.close_jump_host()
        
        # Summarize results
        ping_success_count = sum(1 for r in results if r["ping_status"])
        ssh_success_count = sum(1 for r in results if r["ssh_status"])
        
        print("\n===== Connectivity Test Results =====")
        print(f"Total devices tested: {len(results)}")
        print(f"Ping successful: {ping_success_count} of {len(results)}")
        print(f"SSH successful: {ssh_success_count} of {len(results)}")
        
        print("\nDetailed Results:")
        for result in results:
            ping_status = "✅" if result["ping_status"] else "❌"
            ssh_status = "✅" if result["ssh_status"] else "❌"
            print(f"{result['hostname']} ({result['ip']}): Ping: {ping_status}, SSH: {ssh_status}")
        
        return {
            "success": True,
            "message": "Validation completed",
            "results": results,
            "summary": {
                "total": len(results),
                "ping_success": ping_success_count,
                "ssh_success": ssh_success_count
            }
        }

async def main():
    validator = NetworkValidator(JUMP_HOST, JUMP_USERNAME, JUMP_PASSWORD)
    await validator.validate_devices(INVENTORY_FILE)

if __name__ == "__main__":
    asyncio.run(main())

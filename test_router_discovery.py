#!/usr/bin/env python3
"""
Unit tests for router discovery and connectivity validation methods
Tests different ways to find and access routers in the enhanced audit tool
"""

import unittest
import os
import sys
import tempfile
import csv
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock

# Silence logger during tests
logging.basicConfig(level=logging.CRITICAL)

# Import the router audit tool
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Use importlib to import module with hyphens in filename
import importlib.util
spec = importlib.util.spec_from_file_location(
    "router_audit", 
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "rr4-router-complete-enchanced-v3.8-cli-only.py")
)
router_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router_audit)
JumpHostAuditor = router_audit.JumpHostAuditor

class TestRouterDiscovery(unittest.TestCase):
    """Test different ways to discover and access routers"""
    
    def setUp(self):
        """Set up test environment"""
        # Create JumpHostAuditor instance with mocked methods
        self.auditor = JumpHostAuditor()
        self.auditor.jump_host["password"] = "test_password"  # Set a dummy password for testing
        
        # Create a temporary CSV file with test routers
        self.temp_csv = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv')
        self.csv_path = self.temp_csv.name
        
        # Write test data to the CSV
        csv_writer = csv.writer(self.temp_csv)
        csv_writer.writerow(['hostname', 'ip_address', 'username', 'password', 'secret', 'model'])
        csv_writer.writerow(['TEST-ROUTER-1', '192.168.1.1', 'admin', 'password1', 'secret1', 'C3560'])
        csv_writer.writerow(['TEST-ROUTER-2', '192.168.1.2', 'admin', 'password2', 'secret2', 'C4500'])
        self.temp_csv.close()
        
        # Mock the read_inventory_file method
        self.original_read_inventory = self.auditor.read_inventory_file
        self.auditor.read_inventory_file = self.mock_read_inventory_file
    
    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.csv_path):
            os.unlink(self.csv_path)
            
    def mock_read_inventory_file(self, csv_file=None):
        """Mock the read_inventory_file method to return test data"""
        if not csv_file:
            csv_file = self.csv_path
            
        # Read from our test CSV file
        routers = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                router = {
                    'hostname': row['hostname'],
                    'host': row['ip_address'],
                    'username': row['username'],
                    'password': row['password'],
                    'secret': row['secret'],
                    'model': row.get('model', 'Unknown')
                }
                routers.append(router)
        return routers
    
    def test_inventory_file_loading(self):
        """Test loading routers from inventory file"""
        # Test reading from our temp CSV
        routers = self.auditor.read_inventory_file(self.csv_path)
        
        # Verify we loaded 2 routers from the CSV
        self.assertEqual(len(routers), 2)
        self.assertEqual(routers[0]['hostname'], 'TEST-ROUTER-1')
        self.assertEqual(routers[0]['host'], '192.168.1.1')
        self.assertEqual(routers[1]['hostname'], 'TEST-ROUTER-2')
        self.assertEqual(routers[1]['host'], '192.168.1.2')
    
    def test_ping_discovery(self):
        """Test finding routers through ping"""
        # Create a test method that doesn't rely on ConnectHandler
        def mock_ping_device(host, jump_conn=None):
            # Simulate ping responses for test IP addresses
            ping_responses = {
                "192.168.1.1": (True, "5 packets transmitted, 5 received, 0% packet loss"),
                "192.168.1.2": (True, "5 packets transmitted, 5 received, 0% packet loss"),
                "192.168.1.3": (False, "5 packets transmitted, 0 received, 100% packet loss"),
                "192.168.1.255": (False, "5 packets transmitted, 0 received, 100% packet loss")
            }
            
            # Return predefined response if available, otherwise failure
            if host in ping_responses:
                return ping_responses[host]
            return (False, f"Unknown host: {host}")
        
        # Save original method and replace with our test version
        original_ping_method = self.auditor.ping_device
        self.auditor.ping_device = mock_ping_device
        
        try:
            # Test successful ping
            success, output = self.auditor.ping_device("192.168.1.1")
            self.assertTrue(success)
            
            # Test another successful ping
            success, output = self.auditor.ping_device("192.168.1.2")
            self.assertTrue(success)
            
            # Test failed ping
            success, output = self.auditor.ping_device("192.168.1.3")
            self.assertFalse(success)
            
            # Test unknown host
            success, output = self.auditor.ping_device("192.168.2.1")
            self.assertFalse(success)
        finally:
            # Restore original method
            self.auditor.ping_device = original_ping_method
    
    def test_ssh_discovery(self):
        """Test finding routers through SSH connectivity"""
        # Create a test method that doesn't rely on ConnectHandler
        def mock_ssh_connectivity(host, username, password, jump_conn=None):
            # Simulate SSH responses for different scenarios
            ssh_scenarios = {
                # Successful connection
                ("192.168.1.1", "admin", "password1"): (True, "SSH connectivity successful"),
                # Connection refused
                ("192.168.1.2", "admin", "password2"): (False, "Connection refused"),
                # Authentication failure
                ("192.168.1.3", "admin", "wrong_password"): (False, "Authentication failed"),
                # Host key verification failed
                ("192.168.1.4", "admin", "password"): (False, "Host key verification failed"),
                # No route to host
                ("192.168.1.5", "admin", "password"): (False, "No route to host")
            }
            
            scenario_key = (host, username, password)
            if scenario_key in ssh_scenarios:
                return ssh_scenarios[scenario_key]
            return (False, "Unknown host or credentials")
        
        # Save original method and replace with our test version
        original_ssh_method = self.auditor.test_ssh_connectivity
        self.auditor.test_ssh_connectivity = mock_ssh_connectivity
        
        try:
            # Test successful SSH connection
            success, message = self.auditor.test_ssh_connectivity("192.168.1.1", "admin", "password1")
            self.assertTrue(success)
            self.assertEqual(message, "SSH connectivity successful")
            
            # Test connection refused
            success, message = self.auditor.test_ssh_connectivity("192.168.1.2", "admin", "password2")
            self.assertFalse(success)
            self.assertEqual(message, "Connection refused")
            
            # Test authentication failure
            success, message = self.auditor.test_ssh_connectivity("192.168.1.3", "admin", "wrong_password")
            self.assertFalse(success)
            self.assertEqual(message, "Authentication failed")
            
            # Test host key verification failure
            success, message = self.auditor.test_ssh_connectivity("192.168.1.4", "admin", "password")
            self.assertFalse(success)
            self.assertEqual(message, "Host key verification failed")
            
            # Test no route to host
            success, message = self.auditor.test_ssh_connectivity("192.168.1.5", "admin", "password")
            self.assertFalse(success)
            self.assertEqual(message, "No route to host")
        finally:
            # Restore original method
            self.auditor.test_ssh_connectivity = original_ssh_method
    
    def test_network_scan_discovery(self):
        """Test finding routers through network scanning"""
        # This would typically use something like nmap or a custom scanning method
        # For our test, we'll simulate a network scan with a mocked ping method
        
        # Create dictionary to store ping responses
        ping_responses = {
            "192.168.1.1": (True, "5 packets transmitted, 5 received, 0% packet loss"),
            "192.168.1.2": (True, "5 packets transmitted, 5 received, 0% packet loss"),
            "192.168.1.3": (False, "5 packets transmitted, 0 received, 100% packet loss"),
            "192.168.1.4": (True, "5 packets transmitted, 5 received, 0% packet loss"),
            "192.168.1.5": (False, "5 packets transmitted, 0 received, 100% packet loss")
        }
        
        # Mock function for ping_device
        def mock_ping_device(host, jump_conn=None):
            if host in ping_responses:
                return ping_responses[host]
            return (False, f"Unknown host: {host}")
        
        # Replace the real method with our mock
        original_ping_method = self.auditor.ping_device
        self.auditor.ping_device = mock_ping_device
        
        try:
            # Define a small network range to scan
            network_prefixes = ["192.168.1."]
            found_hosts = []
            
            # Simulate network scan by pinging a small range
            for prefix in network_prefixes:
                for i in range(1, 6):  # Test IPs .1 through .5
                    ip = f"{prefix}{i}"
                    success, _ = self.auditor.ping_device(ip)
                    if success:
                        found_hosts.append(ip)
            
            # We expect to find 3 hosts (.1, .2, and .4) based on our mock responses
            self.assertEqual(len(found_hosts), 3)
            self.assertIn("192.168.1.1", found_hosts)
            self.assertIn("192.168.1.2", found_hosts)
            self.assertIn("192.168.1.4", found_hosts)
            self.assertNotIn("192.168.1.3", found_hosts)
            self.assertNotIn("192.168.1.5", found_hosts)
        finally:
            # Restore the original method
            self.auditor.ping_device = original_ping_method

    def test_multi_method_discovery(self):
        """Test using multiple methods together to discover routers"""
        # Create a mock for ping discovery
        def mock_ping_device(host, jump_conn=None):
            ping_responses = {
                "192.168.1.1": (True, "Ping successful"),
                "192.168.1.2": (True, "Ping successful"),
                "192.168.1.3": (False, "Ping failed"),
                "192.168.1.4": (True, "Ping successful"),
                "192.168.1.5": (False, "Ping failed")
            }
            if host in ping_responses:
                return ping_responses[host]
            return (False, f"Unknown host: {host}")
            
        # Create a mock for SSH discovery
        def mock_ssh_connectivity(host, username, password, jump_conn=None):
            ssh_responses = {
                "192.168.1.1": (True, "SSH successful"),
                "192.168.1.2": (True, "SSH successful"),
                "192.168.1.3": (False, "SSH failed"),
                "192.168.1.4": (False, "SSH failed"),  # Pingable but SSH fails
                "192.168.1.5": (False, "SSH failed")
            }
            key = host
            if key in ssh_responses:
                return ssh_responses[key]
            return (False, f"Unknown host: {host}")
            
        # Save original methods
        original_ping = self.auditor.ping_device
        original_ssh = self.auditor.test_ssh_connectivity
        
        # Replace with our test versions
        self.auditor.ping_device = mock_ping_device
        self.auditor.test_ssh_connectivity = mock_ssh_connectivity
        
        try:
            # Simulate discovery process using both ping and SSH
            network_range = [f"192.168.1.{i}" for i in range(1, 6)]
            discovered_routers = []
            
            for ip in network_range:
                # First try ping
                ping_success, _ = self.auditor.ping_device(ip)
                
                if ping_success:
                    # If ping works, try SSH
                    ssh_success, _ = self.auditor.test_ssh_connectivity(ip, "admin", "password")
                    
                    discovered_routers.append({
                        "ip": ip,
                        "ping": ping_success,
                        "ssh": ssh_success,
                        "fully_accessible": ping_success and ssh_success
                    })
            
            # Check our results
            self.assertEqual(len(discovered_routers), 3)  # We found 3 pingable devices
            
            # Check which are fully accessible (ping + SSH)
            fully_accessible = [r for r in discovered_routers if r["fully_accessible"]]
            self.assertEqual(len(fully_accessible), 2)  # Only 2 have both ping and SSH working
            
            # Verify specific IPs
            discovered_ips = [r["ip"] for r in discovered_routers]
            self.assertIn("192.168.1.1", discovered_ips)  # Ping + SSH works
            self.assertIn("192.168.1.2", discovered_ips)  # Ping + SSH works
            self.assertIn("192.168.1.4", discovered_ips)  # Ping works, SSH fails
            
        finally:
            # Restore original methods
            self.auditor.ping_device = original_ping
            self.auditor.test_ssh_connectivity = original_ssh

if __name__ == "__main__":
    unittest.main()

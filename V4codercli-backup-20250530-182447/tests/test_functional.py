#!/usr/bin/env python3
"""Functional tests for RR4 Complete Enhanced v4 CLI."""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from rr4_complete_enchanced_v4_cli_core.connection_manager import ConnectionManager
from rr4_complete_enchanced_v4_cli_core.data_parser import DataParser
from rr4_complete_enchanced_v4_cli_tasks.igp_collector import IGPCollector

class TestEndToEnd(unittest.TestCase):
    """End-to-end functional tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_device = {
            'hostname': '192.168.1.1',
            'device_type': 'cisco_ios',
            'username': 'admin',
            'password': 'password'
        }
        
        cls.sample_outputs = {
            'show version': """
Cisco IOS Software, Version 15.2(4)M7
cisco ISR4321/K9 (revision 1.0) with 2097152K/6147K bytes of memory
""",
            'show ip ospf neighbor': """
Neighbor ID     Pri   State           Dead Time   Address         Interface
10.0.0.2         1   FULL/DR         00:00:33    10.1.1.2       GigabitEthernet0/1
10.0.0.3         1   FULL/BDR        00:00:31    10.1.1.3       GigabitEthernet0/1
""",
            'show ip route': """
Gateway of last resort is 10.0.0.1

      10.0.0.0/24 is subnetted, 2 subnets
C        10.1.1.0 is directly connected, GigabitEthernet0/1
O        10.2.2.0 [110/2] via 10.1.1.2, 00:05:40, GigabitEthernet0/1
"""
        }
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection_manager = ConnectionManager(max_connections=5)
        # Mock the connection creation
        self.connection_manager.connection_pool._create_connection_with_diagnostics = MagicMock()
        self.mock_connection = Mock()
        self.mock_connection.device_type = 'cisco_ios'
        self.mock_connection.host = '192.168.1.1'
        self.connection_manager.connection_pool._create_connection_with_diagnostics.return_value = self.mock_connection
        
        # Set up mock command execution
        def mock_send_command(command, **kwargs):
            return self.sample_outputs.get(command, "Command not found")
        self.mock_connection.send_command = mock_send_command
    
    def test_igp_collection_workflow(self):
        """Test complete IGP collection workflow."""
        with self.connection_manager.get_connection(**self.test_device) as connection:
            collector = IGPCollector(connection)
            results = collector.collect()
            
            self.assertTrue(results['success'])
            self.assertGreater(len(results['data']), 0)
            self.assertEqual(results['failure_count'], 0)
            
            # Verify OSPF neighbor data
            self.assertIn('show ip ospf neighbor', results['data'])
            ospf_data = results['data']['show ip ospf neighbor']
            self.assertIn('raw_output', ospf_data)
            self.assertIn('parsed_data', ospf_data)
            self.assertTrue(ospf_data['success'])
    
    def test_error_handling_workflow(self):
        """Test error handling in the collection workflow."""
        # Mock command execution with failures
        command_count = 0
        def mock_send_command_with_errors(command, **kwargs):
            nonlocal command_count
            command_count += 1
            if command_count % 3 == 0:  # Fail every third command
                raise Exception("Simulated network error")
            return self.sample_outputs.get(command, "Command not found")
        
        self.mock_connection.send_command = mock_send_command_with_errors
        
        with self.connection_manager.get_connection(**self.test_device) as connection:
            collector = IGPCollector(connection)
            results = collector.collect()
            
            self.assertTrue('failure_count' in results)
            self.assertGreater(results['failure_count'], 0)
            self.assertTrue('commands_failed' in results)
            
            # Verify error handling in data
            failed_commands = [cmd for cmd, data in results['data'].items() if not data['success']]
            self.assertEqual(len(failed_commands), results['failure_count'])
    
    def test_connection_recovery_workflow(self):
        """Test connection recovery workflow."""
        # First attempt fails, second succeeds
        self.connection_manager.connection_pool._create_connection_with_diagnostics.side_effect = [
            None,  # First attempt fails
            self.mock_connection  # Second attempt succeeds
        ]
        
        with self.connection_manager.get_connection(**self.test_device) as connection:
            self.assertEqual(connection, self.mock_connection)
            
            # Test command execution after recovery
            collector = IGPCollector(connection)
            results = collector.collect()
            self.assertTrue(results['success'])
            self.assertGreater(len(results['data']), 0)
    
    def test_data_collection_workflow(self):
        """Test complete data collection workflow."""
        with self.connection_manager.get_connection(**self.test_device) as connection:
            # Test IGP collection
            collector = IGPCollector(connection)
            results = collector.collect()
            
            self.assertTrue(results['success'])
            self.assertGreater(len(results['data']), 0)
            self.assertEqual(results['failure_count'], 0)
            
            # Verify data structure
            self.assertIn('show ip ospf neighbor', results['data'])
            self.assertIn('show ip route', results['data'])
            
            # Verify OSPF data
            ospf_data = results['data']['show ip ospf neighbor']
            self.assertTrue(ospf_data['success'])
            self.assertIn('raw_output', ospf_data)
            self.assertIn('parsed_data', ospf_data)

if __name__ == '__main__':
    unittest.main() 
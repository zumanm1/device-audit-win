#!/usr/bin/env python3
"""Unit tests for MPLSCollector module."""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from rr4_complete_enchanced_v4_cli_tasks.mpls_collector import MPLSCollector

class TestMPLSCollector(unittest.TestCase):
    """Test cases for MPLSCollector class."""
    
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
            'show mpls ldp neighbor': """
Peer LDP Ident: 10.0.0.2:0; Local LDP Ident 10.0.0.1:0
    TCP connection: 10.0.0.2.646 - 10.0.0.1.12345
    State: Operational; Msgs sent/rcvd: 123/456; Downstream
    Up time: 02:03:04
    LDP discovery sources:
      GigabitEthernet0/1
    Addresses bound to peer LDP Ident:
      10.0.0.2        10.1.1.2        
Peer LDP Ident: 10.0.0.3:0; Local LDP Ident 10.0.0.1:0
    TCP connection: 10.0.0.3.646 - 10.0.0.1.12346
    State: Operational; Msgs sent/rcvd: 234/567; Downstream
    Up time: 01:02:03
    LDP discovery sources:
      GigabitEthernet0/2
    Addresses bound to peer LDP Ident:
      10.0.0.3        10.1.1.3
""",
            'show mpls forwarding-table': """
Local  Outgoing    Prefix            Bytes tag  Outgoing   Next Hop    
tag    tag         or Tunnel Id      switched   interface              
16     Pop tag     10.1.1.0/24      0          Gi0/1      10.1.1.2     
17     18          10.2.2.0/24      0          Gi0/1      10.1.1.2     
18     Pop tag     10.3.3.0/24      0          Gi0/2      10.1.1.3     
19     20          10.4.4.0/24      0          Gi0/2      10.1.1.3
""",
            'show mpls traffic-eng tunnels': """
Name: R1_t1                             (Tunnel1) Destination: 10.0.0.2
  Status:
    Admin: up         Oper: up     Path: valid       Signalling: connected
    path option 1, type explicit path1 (Basis for Setup, path weight 10)
  Config Parameters:
    Bandwidth: 100      kbps (Global)  Priority: 7  7   Affinity: 0x0/0xFFFF
    Metric Type: TE (default)
    AutoRoute:  enabled  LockDown: disabled  Loadshare: 100      bw-based
    auto-bw: disabled
  
Name: R1_t2                             (Tunnel2) Destination: 10.0.0.3
  Status:
    Admin: up         Oper: up     Path: valid       Signalling: connected
    path option 1, type dynamic (Basis for Setup, path weight 20)
  Config Parameters:
    Bandwidth: 200      kbps (Global)  Priority: 7  7   Affinity: 0x0/0xFFFF
    Metric Type: TE (default)
    AutoRoute:  enabled  LockDown: disabled  Loadshare: 100      bw-based
    auto-bw: disabled
""",
            'show segment-routing mpls': """
Segment Routing Global Block (SRGB):
  Size: 10000, Range: [16000..26000]
  
Connected-Prefix-SID:
  10.0.0.1/32 index 1 range 1
  10.1.1.0/24 index 2 range 1
  10.2.2.0/24 index 3 range 1
  
Segment Routing Mapping Server Entries:
  10.3.3.0/24 index 4 range 1
  10.4.4.0/24 index 5 range 1
"""
        }
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = Mock()
        self.mock_connection.device_type = 'cisco_ios'
        self.mock_connection.host = '192.168.1.1'
        
        # Set up mock command execution
        def mock_send_command(command, **kwargs):
            return self.sample_outputs.get(command, "Command not found")
        self.mock_connection.send_command = mock_send_command
        
        self.collector = MPLSCollector(self.mock_connection)
    
    def test_get_commands_for_platform(self):
        """Test getting commands for different platforms."""
        ios_commands = self.collector.get_commands_for_platform('ios')
        self.assertIsInstance(ios_commands, list)
        self.assertGreater(len(ios_commands), 0)
        self.assertIn('show mpls ldp neighbor', ios_commands)
        
        iosxr_commands = self.collector.get_commands_for_platform('iosxr')
        self.assertIsInstance(iosxr_commands, list)
        self.assertGreater(len(iosxr_commands), 0)
        self.assertIn('show mpls ldp neighbor', iosxr_commands)
        
        # Test unknown platform defaults to IOS
        unknown_commands = self.collector.get_commands_for_platform('unknown')
        self.assertEqual(unknown_commands, ios_commands)
    
    def test_mpls_collection_workflow(self):
        """Test complete MPLS collection workflow."""
        results = self.collector.collect()
        
        self.assertTrue(results['success'])
        self.assertGreater(len(results['data']), 0)
        self.assertEqual(results['failure_count'], 0)
        
        # Verify LDP neighbor data
        self.assertIn('show mpls ldp neighbor', results['data'])
        ldp_data = results['data']['show mpls ldp neighbor']
        self.assertIn('raw_output', ldp_data)
        self.assertIn('parsed_data', ldp_data)
        self.assertTrue(ldp_data['success'])
        
        # Verify protocols detected
        self.assertIn('LDP', results['protocols_detected'])
        self.assertEqual(results['neighbor_count']['ldp'], 2)
    
    def test_error_handling_workflow(self):
        """Test error handling in the collection workflow."""
        # Mock command execution with failures
        command_count = 0
        def mock_send_command_with_errors(command, **kwargs):
            nonlocal command_count
            command_count += 1
            if command_count % 3 == 0:  # Fail every third command
                raise Exception("MPLS not enabled")
            return self.sample_outputs.get(command, "Command not found")
        
        self.mock_connection.send_command = mock_send_command_with_errors
        
        results = self.collector.collect()
        
        self.assertTrue('failure_count' in results)
        self.assertGreater(results['failure_count'], 0)
        self.assertTrue('commands_failed' in results)
        
        # Verify error handling in data
        failed_commands = [cmd for cmd, data in results['data'].items() if not data['success']]
        self.assertEqual(len(failed_commands), results['failure_count'])
    
    def test_protocol_detection(self):
        """Test MPLS protocol detection."""
        results = self.collector.collect()
        
        # Verify LDP detection
        self.assertIn('LDP', results['protocols_detected'])
        self.assertEqual(results['neighbor_count']['ldp'], 2)
        
        # Verify MPLS-TE detection
        self.assertIn('MPLS-TE', results['protocols_detected'])
        self.assertEqual(results['neighbor_count']['te'], 2)
        
        # Verify SR-MPLS detection
        self.assertIn('SR-MPLS', results['protocols_detected'])
        self.assertGreater(results['neighbor_count']['sr'], 0)
    
    def test_command_timeout_handling(self):
        """Test command timeout settings."""
        # Test long-running commands
        long_commands = [
            'show mpls ldp bindings',
            'show mpls forwarding-table',
            'show mpls traffic-eng topology'
        ]
        
        for cmd in long_commands:
            timeout = self.collector._get_command_timeout(cmd)
            self.assertEqual(timeout, 120)
        
        # Test regular commands
        regular_commands = [
            'show mpls interfaces',
            'show mpls ldp neighbor',
            'show mpls label range'
        ]
        
        for cmd in regular_commands:
            timeout = self.collector._get_command_timeout(cmd)
            self.assertEqual(timeout, 60)
    
    def test_layer_info(self):
        """Test layer information retrieval."""
        info = self.collector.get_layer_info()
        
        self.assertEqual(info['name'], 'mpls')
        self.assertIn('description', info)
        self.assertIsInstance(info['categories'], list)
        self.assertGreater(len(info['categories']), 0)
        self.assertIn('platforms_supported', info)
        self.assertIn('estimated_time', info)

if __name__ == '__main__':
    unittest.main() 
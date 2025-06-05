#!/usr/bin/env python3
"""Unit tests for DataParser module."""

import unittest
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from rr4_complete_enchanced_v4_cli_core.data_parser import DataParser, ParseResult

class TestDataParser(unittest.TestCase):
    """Test cases for DataParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = DataParser()
    
    def test_parse_show_version(self):
        """Test parsing show version output."""
        sample_output = """
Router uptime is 7 weeks, 3 days, 2 hours, 30 minutes
Cisco IOS Software, Version 15.2(4)M7
cisco ISR4321/K9 (revision 1.0) with 2097152K/6147K bytes of memory
"""
        result = self.parser._parse_show_version(sample_output)
        self.assertIsInstance(result, dict)
        self.assertIn('version', result)
        self.assertEqual(result['version'], '15.2(4)M7')
    
    def test_parse_interface_brief(self):
        """Test parsing show ip interface brief output."""
        sample_output = """
Interface                  IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0        192.168.1.1     YES NVRAM  up                    up
GigabitEthernet0/1        unassigned      YES NVRAM  administratively down down
"""
        result = self.parser._parse_interface_brief(sample_output)
        self.assertIsInstance(result, dict)
        self.assertIn('interfaces', result)
        self.assertEqual(len(result['interfaces']), 2)
        self.assertEqual(result['interfaces']['GigabitEthernet0/0']['ip_address'], '192.168.1.1')
    
    def test_parse_bgp_summary(self):
        """Test parsing show ip bgp summary output."""
        sample_output = """
BGP router identifier 10.0.0.1, local AS number 65000
BGP table version is 12345
Neighbor        V    AS    MsgRcvd    MsgSent   TblVer  InQ  OutQ Up/Down  State/PfxRcd
192.168.1.2     4 65001      12345      12345    12345    0    0 00:05:00        5
192.168.1.3     4 65002      12345      12345    12345    0    0 00:10:00        3
"""
        result = self.parser._parse_bgp_summary(sample_output)
        self.assertIsInstance(result, dict)
        self.assertIn('neighbors', result)
        self.assertEqual(len(result['neighbors']), 2)
        self.assertEqual(result['neighbors']['192.168.1.2']['as_number'], '65001')
    
    def test_parse_ospf_neighbors(self):
        """Test parsing show ip ospf neighbor output."""
        sample_output = """
Neighbor ID     Pri   State           Dead Time   Address         Interface
10.0.0.2         1   FULL/DR         00:00:33    192.168.1.2     GigabitEthernet0/0
10.0.0.3         1   FULL/BDR        00:00:37    192.168.1.3     GigabitEthernet0/1
"""
        result = self.parser._parse_ospf_neighbors(sample_output)
        self.assertIsInstance(result, dict)
        self.assertIn('neighbors', result)
        self.assertEqual(len(result['neighbors']), 2)
        self.assertEqual(result['neighbors']['10.0.0.2']['state'], 'FULL/DR')
    
    def test_partial_parsing(self):
        """Test partial parsing functionality."""
        sample_output = """
Key1: Value1
Key2: Value2

Field1    Field2    Field3
data1     data2     data3
data4     data5     data6
"""
        result = self.parser._attempt_partial_parse(None, sample_output)
        self.assertIsInstance(result, dict)
        self.assertIn('key1', result)
        self.assertEqual(result['key1'], 'Value1')
        self.assertIn('tabular_data', result)
        # Should only have 2 data rows, not counting header
        self.assertEqual(len(result['tabular_data']), 2)
        self.assertEqual(result['tabular_data'][0], ['data1', 'data2', 'data3'])
        self.assertEqual(result['tabular_data'][1], ['data4', 'data5', 'data6'])
    
    def test_is_ip_address(self):
        """Test IP address validation."""
        self.assertTrue(self.parser._is_ip_address('192.168.1.1'))
        self.assertTrue(self.parser._is_ip_address('10.0.0.1'))
        self.assertFalse(self.parser._is_ip_address('256.256.256.256'))
        self.assertFalse(self.parser._is_ip_address('not.an.ip.address'))
    
    @patch('genie.libs.parser.utils.get_parser')
    def test_genie_parsing(self, mock_get_parser):
        """Test Genie parsing with mocked parser."""
        # Mock Genie parser
        mock_parser = Mock()
        mock_parser.parse.return_value = {'parsed': 'data'}
        mock_get_parser.return_value = mock_parser
        
        # Mock device for Genie
        with patch('genie.libs.parser.utils.Device') as mock_device:
            mock_device.return_value = Mock()
            
            result = self.parser._parse_with_genie('show version', 'sample output', 'ios')
            self.assertTrue(result.success)
            self.assertEqual(result.parsed_data, {'parsed': 'data'})
    
    def test_parse_command_output(self):
        """Test parse_command_output method."""
        sample_output = """
Interface    Status    Protocol
Gi0/1       up        up
Gi0/2       down      down
"""
        result = self.parser.parse_command_output('show interfaces', sample_output, 'ios')
        self.assertTrue(result.success)
        self.assertIn('interfaces', result.parsed_data)
        self.assertEqual(len(result.parsed_data['interfaces']), 2)
        self.assertEqual(result.parsed_data['interfaces'][0]['name'], 'Gi0/1')
        self.assertEqual(result.parsed_data['interfaces'][0]['status'], 'up')

if __name__ == '__main__':
    unittest.main() 
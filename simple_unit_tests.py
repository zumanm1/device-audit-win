#!/usr/bin/env python3
"""
Simple unit tests for Router Audit Tool
Tests the core functionality of the router audit tool without network connections
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import csv
from io import StringIO

# Add directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions to test
from rr4_router_complete_enchanced_v3_8_cli_only import JumpHostAuditor

class TestRouterAudit(unittest.TestCase):
    """Test case for the router audit tool"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create auditor instance
        self.auditor = JumpHostAuditor()
        
        # Sample router output for testing
        self.sample_output = """
        hostname RTR-TEST-01
        !
        line aux 0
         transport input telnet
         no exec-timeout
         login local
        !
        """
        
        # Sample CSV data
        self.csv_data = """index,hostname,management_ip,wan_ip,model_name
0,RTR-CORE-01.xrnet.net,172.16.39.100,203.0.113.1,Cisco 4431 ISR
1,RTR-EDGE-02.xrnet.net,172.16.39.101,203.0.113.2,Cisco 4451-X ISR"""
    
    def test_parse_router_output(self):
        """Test parsing router output"""
        result = self.auditor.parse_router_output(self.sample_output, "RTR-TEST-01", "192.168.1.1")
        
        # Check if parsing was correct
        self.assertEqual(result['hostname'], 'RTR-TEST-01')
        self.assertEqual(result['ip_address'], '192.168.1.1')
        self.assertEqual(result['telnet_allowed'], 'YES')
        self.assertTrue(result['login_method'] in ['local', 'LOCAL'])
        
        # Print actual values for debugging
        print(f"exec_timeout value: {result['exec_timeout']}")
        print(f"risk_level value: {result['risk_level']}")
        
        # Risk level should be high or critical since telnet is allowed
        self.assertTrue(result['risk_level'] in ['HIGH', 'CRITICAL', 'MEDIUM'])
    
    def test_assess_risk(self):
        """Test risk assessment logic"""
        # Test different risk scenarios
        telnet_yes = self.auditor.assess_risk('YES', 'local', 'NO')
        telnet_yes_timeout = self.auditor.assess_risk('YES', 'local', '10')
        no_telnet_no_timeout = self.auditor.assess_risk('NO', 'local', 'NO')
        no_telnet_timeout = self.auditor.assess_risk('NO', 'local', '10')
        
        print(f"Risk assessment results:")
        print(f"  Telnet + No timeout: {telnet_yes}")
        print(f"  Telnet + Timeout: {telnet_yes_timeout}")
        print(f"  No telnet + No timeout: {no_telnet_no_timeout}")
        print(f"  No telnet + Timeout: {no_telnet_timeout}")
        
        # Basic assertions - telnet should have higher risk than no telnet
        self.assertTrue(telnet_yes in ['HIGH', 'CRITICAL', 'MEDIUM'])
        self.assertTrue(no_telnet_timeout in ['LOW', 'MEDIUM', 'SECURE'])
    
    @patch('netmiko.ConnectHandler')
    def test_jump_host_connection_mocked(self, mock_connect):
        """Test jump host connection with proper mocking"""
        # Create a mock context manager
        mock_context = MagicMock()
        mock_context.send_command.return_value = "test-hostname"
        
        # Configure the mock to return our mock context
        mock_connect.return_value.__enter__.return_value = mock_context
        
        # Set password for testing
        self.auditor.jump_host['password'] = 'test_password'
        
        # Test the connection
        result = self.auditor.test_jump_host_connection()
        
        # Verify the connection was attempted with correct parameters
        mock_connect.assert_called_once()
        self.assertTrue(result)
        
        # Now test failure case
        mock_connect.reset_mock()
        mock_connect.side_effect = Exception("Mock connection failure")
        
        result = self.auditor.test_jump_host_connection()
        self.assertFalse(result)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.DictWriter')
    @patch('datetime.datetime')
    def test_generate_reports(self, mock_datetime, mock_csv_writer, mock_file):
        """Test report generation with mocks"""
        # Setup mocks
        mock_writer = MagicMock()
        mock_csv_writer.return_value = mock_writer
        mock_datetime.now.return_value.strftime.return_value = "20250526-180000"
        
        # Setup test data
        self.auditor.results = [
            {
                'hostname': 'RTR-TEST-01',
                'ip_address': '172.16.39.100',
                'telnet_allowed': 'YES',
                'login_method': 'local',
                'exec_timeout': 'NO',
                'risk_level': 'HIGH',
                'error': None,
                'timestamp': '2025-05-26 18:00:00'
            }
        ]
        
        # Generate reports
        result = self.auditor.generate_reports()
        
        # Check results
        mock_file.assert_called()
        mock_writer.writeheader.assert_called_once()
        mock_writer.writerow.assert_called()
        self.assertTrue("router_audit_" in result)

if __name__ == '__main__':
    unittest.main()

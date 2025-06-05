#!/usr/bin/env python3
"""
Unit tests for the Enhanced Router Audit integration
"""

import unittest
import os
import csv
from unittest.mock import patch, MagicMock, mock_open
from enhanced_router_audit import EnhancedRouterAudit
from netmiko import ConnectHandler

class TestEnhancedRouterAudit(unittest.TestCase):
    """Test cases for the EnhancedRouterAudit class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test audit instance with credential manager mocked
        with patch('enhanced_router_audit.CredentialManager'):
            self.audit = EnhancedRouterAudit()
            # Mock the credential manager to avoid actual encryption/decryption
            self.audit.cred_manager = MagicMock()
            self.audit.cred_manager.encrypt.return_value = "ENCRYPTED"
            self.audit.cred_manager.decrypt.return_value = "DECRYPTED"
    
    def test_initialize_security(self):
        """Test security initialization"""
        with patch('getpass.getpass', return_value="test_master_password"):
            with patch('builtins.print'):  # Suppress output
                self.audit.initialize_security()
                
        # Verify master password was set and initialize was called
        self.assertEqual(self.audit.master_password, "test_master_password")
        self.audit.cred_manager.initialize.assert_called_once_with("test_master_password")
    
    @patch('builtins.open', new_callable=mock_open, read_data='hostname,ip_address,username,password,secret\nRouter1,192.168.1.1,admin,cisco,cisco\nRouter2,192.168.1.2,admin,ENC:encrypted_password,ENC:encrypted_secret')
    def test_load_encrypted_router_credentials(self, mock_file):
        """Test loading router configurations with encrypted credentials"""
        # Mock csv.DictReader
        with patch('csv.DictReader') as mock_reader:
            # Setup mock rows
            mock_reader.return_value = [
                {'hostname': 'Router1', 'ip_address': '192.168.1.1', 'username': 'admin', 
                 'password': 'cisco', 'secret': 'cisco'},
                {'hostname': 'Router2', 'ip_address': '192.168.1.2', 'username': 'admin',
                 'password': 'ENC:encrypted_password', 'secret': 'ENC:encrypted_secret'}
            ]
            
            with patch('builtins.print'):  # Suppress output
                routers = self.audit.load_encrypted_router_credentials('test.csv')
        
        # Verify two routers were loaded
        self.assertEqual(len(routers), 2)
        
        # First router should have plaintext credentials
        self.assertEqual(routers[0]['hostname'], 'Router1')
        self.assertEqual(routers[0]['password'], 'cisco')
        
        # Second router should have decrypted credentials
        self.assertEqual(routers[1]['hostname'], 'Router2')
        self.assertEqual(routers[1]['password'], 'DECRYPTED')  # From our mocked decrypt
        self.assertEqual(routers[1]['secret'], 'DECRYPTED')  # From our mocked decrypt
        
        # Verify decrypt was called twice (once for password, once for secret)
        self.assertEqual(self.audit.cred_manager.decrypt.call_count, 2)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.DictReader')
    @patch('csv.DictWriter')
    def test_encrypt_router_credentials(self, mock_writer, mock_reader, mock_file):
        """Test encrypting router credentials"""
        # Setup mock for csv reader
        mock_reader.return_value.fieldnames = ['hostname', 'ip_address', 'username', 'password', 'secret']
        mock_reader.return_value.__iter__.return_value = [
            {'hostname': 'Router1', 'ip_address': '192.168.1.1', 'username': 'admin', 
             'password': 'cisco', 'secret': 'cisco'},
        ]
        
        with patch('builtins.print'):  # Suppress output
            result = self.audit.encrypt_router_credentials('input.csv', 'output.csv')
            
        # Verify encryption was successful
        self.assertTrue(result)
        
        # Verify encrypt was called twice (once for password, once for secret)
        self.assertEqual(self.audit.cred_manager.encrypt.call_count, 2)
        
        # Verify DictWriter was called with correct arguments
        mock_writer.assert_called_once()
        
    @patch('enhanced_router_audit.ConnectHandler')
    @patch('enhanced_router_audit.SSHCommandHandler')
    def test_audit_router_successful(self, mock_cmd_handler_class, mock_connect):
        """Test successful router audit"""
        # Setup mock connection
        mock_connection = MagicMock()
        mock_connection.is_alive.return_value = True
        mock_connection.find_prompt.return_value = "Router1#"  # Privileged mode
        mock_connect.return_value = mock_connection
        
        # Setup mock command handler
        mock_cmd_handler = MagicMock()
        mock_cmd_handler.execute_multiple_commands.return_value = {
            'summary': {
                'total_commands': 4,
                'successful': 4,
                'failed': 0,
                'all_succeeded': True,
                'status': 'SUCCESS'
            },
            'terminal length 0': {'success': True, 'duration': 0.5},
            'show version | include IOS': {'success': True, 'duration': 0.7},
            'show platform': {'success': True, 'duration': 0.8},
            'show run | include telnet|aux|line': {'success': True, 'duration': 1.2}
        }
        mock_cmd_handler.get_command_failures.return_value = []
        mock_cmd_handler_class.return_value = mock_cmd_handler
        
        # Create a test router config
        router_config = {
            'hostname': 'Router1',
            'host': '192.168.1.1',
            'username': 'admin',
            'password': 'cisco',
            'secret': 'cisco',
            'device_type': 'cisco_ios'
        }
        
        # Run the audit with suppressed output
        with patch('builtins.print'):
            result = self.audit.audit_router(router_config)
        
        # Verify connection was made with correct params
        mock_connect.assert_called_once()
        
        # Verify command handler was used
        mock_cmd_handler_class.assert_called_once()
        
        # Verify result has expected values
        self.assertEqual(result['hostname'], 'Router1')
        self.assertEqual(result['ip_address'], '192.168.1.1')
        self.assertEqual(result['ssh_status'], 'SUCCESS')
        self.assertEqual(result['auth_status'], 'SUCCESS')
        self.assertEqual(result['privilege_level'], 'PRIVILEGED')
        self.assertEqual(result['command_status'], 'SUCCESS')
        self.assertEqual(result['command_failures'], [])
        
    @patch('enhanced_router_audit.ConnectHandler')
    def test_audit_router_ssh_failure(self, mock_connect):
        """Test router audit with SSH connection failure"""
        # Setup mock connection to raise exception
        mock_connect.side_effect = Exception("SSH connection failed")
        
        # Create a test router config
        router_config = {
            'hostname': 'Router1',
            'host': '192.168.1.1',
            'username': 'admin',
            'password': 'wrong_password',
            'device_type': 'cisco_ios'
        }
        
        # Run the audit with suppressed output
        with patch('builtins.print'):
            with patch('enhanced_router_audit.logger'):  # Mock logger to suppress log output
                result = self.audit.audit_router(router_config)
        
        # Verify connection attempt was made
        mock_connect.assert_called_once()
        
        # Verify result indicates failure
        self.assertEqual(result['ssh_status'], 'FAILED')
        self.assertEqual(result['auth_status'], 'UNKNOWN')
        self.assertIn('SSH connection error', result['error'])

    def test_print_summary(self):
        """Test summary generation"""
        # Create some test results
        self.audit.results = [
            {
                'hostname': 'Router1',
                'ip_address': '192.168.1.1',
                'ssh_status': 'SUCCESS',
                'auth_status': 'SUCCESS',
                'privilege_level': 'PRIVILEGED',
                'command_status': 'SUCCESS',
                'command_failures': []
            },
            {
                'hostname': 'Router2',
                'ip_address': '192.168.1.2',
                'ssh_status': 'SUCCESS',
                'auth_status': 'FAILED',
                'privilege_level': 'UNKNOWN',
                'command_status': 'FAILED',
                'command_failures': ['show platform', 'show run | include telnet|aux|line'],
                'auth_error_details': 'Authentication failed'
            }
        ]
        
        # Run summary with suppressed output
        with patch('builtins.print'):
            self.audit.print_summary()
        
        # Not much to assert here since we're just printing output
        # A real test would validate the structure of any returned summary data


if __name__ == "__main__":
    unittest.main()

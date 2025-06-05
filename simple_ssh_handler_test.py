#!/usr/bin/env python3
"""
Simplified test for SSH Command Handler
"""

import unittest
from unittest.mock import MagicMock, patch
from ssh_command_handler import SSHCommandHandler

class TestSSHHandler(unittest.TestCase):
    """Simple tests for SSH Command Handler"""
    
    def test_execute_command_success(self):
        """Test command execution success"""
        # Create a mock connection
        mock_conn = MagicMock()
        
        # Setup the read_channel to return a successful response
        mock_conn.read_channel = MagicMock()
        mock_conn.read_channel.return_value = "Router1# show version\nCisco IOS Software, Version 15.4\nRouter1#"
        
        # Create the handler with our mock
        handler = SSHCommandHandler(mock_conn)
        
        # Override time.sleep and time.time to avoid actual waiting
        with patch('time.sleep'), patch('time.time', side_effect=[0, 1, 2]):
            with patch('builtins.print'):  # Suppress output
                result = handler.execute_command("show version")
        
        # Check result
        self.assertTrue(result['success'])
        self.assertFalse(result['timed_out'])
        self.assertIsNone(result['error'])
    
    def test_command_failures(self):
        """Test tracking of command failures"""
        handler = SSHCommandHandler(MagicMock())
        
        # Manually populate command history with success and failure
        handler.command_history = {
            'show version': {'success': True},
            'show interfaces': {'success': False},
            'show ip route': {'success': False}
        }
        
        # Get failures
        failures = handler.get_command_failures()
        
        # Check failures
        self.assertEqual(len(failures), 2)
        self.assertIn('show interfaces', failures)
        self.assertIn('show ip route', failures)

if __name__ == '__main__':
    unittest.main()

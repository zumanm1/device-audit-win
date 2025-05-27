#!/usr/bin/env python3
"""
Unit tests for the SSH Command Handler module
"""

import unittest
import time
from unittest.mock import patch, MagicMock, call
from ssh_command_handler import SSHCommandHandler

class TestSSHCommandHandler(unittest.TestCase):
    """Test cases for the SSHCommandHandler class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock connection
        self.mock_connection = MagicMock()
        
        # Create an SSH command handler with the mock connection
        self.handler = SSHCommandHandler(self.mock_connection, timeout=2)  # Using shorter timeout for tests
    
    def test_initialization(self):
        """Test initialization of command handler"""
        self.assertEqual(self.handler.connection, self.mock_connection)
        self.assertEqual(self.handler.default_timeout, 2)
        self.assertIsNone(self.handler.last_error)
        self.assertEqual(self.handler.command_history, {})
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    @patch('time.time')
    @patch('builtins.print')  # Mock print to avoid console output during tests
    def test_execute_command_success(self, mock_print, mock_time, mock_sleep):
        """Test successful command execution"""
        # Setup time mocking to simulate command execution time
        mock_time.side_effect = [10, 10.5, 11, 11.5]  # Start, loop checks, end
        
        # Setup connection to return successful command output
        self.mock_connection.read_channel.side_effect = [
            "command echo", 
            "more output\n#"  # Second read includes prompt, indicating completion
        ]
        
        # Execute a test command
        result = self.handler.execute_command("show version", timeout=1.5)
        
        # Verify command was sent correctly
        self.mock_connection.write_channel.assert_called_once_with("show version\n")
        
        # Verify result is successful
        self.assertTrue(result['success'])
        self.assertEqual(result['output'], "command echomore output\n#")
        self.assertEqual(result['duration'], 1.5)  # Based on our mocked time
        self.assertFalse(result['timed_out'])
        self.assertIsNone(result['error'])
        
        # Verify command was added to history
        self.assertIn("show version", self.handler.command_history)
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    @patch('time.time')
    @patch('builtins.print')  # Mock print to avoid console output during tests
    def test_execute_command_timeout(self, mock_print, mock_time, mock_sleep):
        """Test command execution timeout"""
        # Setup time mocking to simulate timeout
        mock_time.side_effect = [10, 10.5, 11, 11.5, 12, 12.5, 13]  # Multiple calls exceeding timeout
        
        # Setup connection to return incomplete output
        self.mock_connection.read_channel.side_effect = [
            "command echo", 
            "more output",
            "still running..."  # No prompt to indicate completion
        ]
        
        # Execute a test command with a 2-second timeout
        result = self.handler.execute_command("show running-config", timeout=2)
        
        # Verify result indicates timeout
        self.assertFalse(result['success'])
        self.assertTrue(result['timed_out'])
        self.assertIn("timed out", result['error'])
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    @patch('time.time')
    @patch('builtins.print')  # Mock print to avoid console output during tests
    def test_execute_command_insufficient_output(self, mock_print, mock_time, mock_sleep):
        """Test command execution with insufficient output"""
        # Setup time mocking to simulate a quick failure (not a timeout)
        # First value is start time, last is end time calculation, middle values are for the loop
        mock_time.side_effect = [10, 10.5, 11, 11]  # Less than timeout (2 seconds)
        
        # Setup connection to return minimal but non-empty output (not enough to be successful)
        self.mock_connection.read_channel.side_effect = ["minimal output", ""]
        
        # Execute a test command
        result = self.handler.execute_command("show version")
        
        # Verify result indicates failure but not timeout
        self.assertFalse(result['success'])
        self.assertFalse(result['timed_out'])
        self.assertIn("insufficient", result['error'].lower())
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    @patch('builtins.print')  # Mock print to avoid console output during tests
    def test_execute_multiple_commands_all_success(self, mock_print, mock_sleep):
        """Test executing multiple commands with all succeeding"""
        # Instead of mocking time.time, let's override the execute_command method
        # This is more reliable than trying to mock all the time.time calls
        self.handler.execute_command = MagicMock()
        
        # Setup the mock to return successful results for both commands
        self.handler.execute_command.side_effect = [
            {'success': True, 'output': 'terminal length 0\n#', 'duration': 0.5, 'timed_out': False, 'error': None},
            {'success': True, 'output': 'show version\nIOS Version: 15.4\n#', 'duration': 0.7, 'timed_out': False, 'error': None}
        ]
        
        # Execute multiple commands
        commands = ["terminal length 0", "show version"]
        results = self.handler.execute_multiple_commands(commands)
        
        # Verify all commands were sent
        self.assertEqual(self.mock_connection.write_channel.call_count, 2)
        
        # Verify summary shows all succeeded
        self.assertEqual(results['summary']['total_commands'], 2)
        self.assertEqual(results['summary']['successful'], 2)
        self.assertEqual(results['summary']['failed'], 0)
        self.assertTrue(results['summary']['all_succeeded'])
        self.assertEqual(results['summary']['status'], 'SUCCESS')
        
        # Verify individual results
        self.assertTrue(results['terminal length 0']['success'])
        self.assertTrue(results['show version']['success'])
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    @patch('time.time')
    @patch('builtins.print')  # Mock print to avoid console output during tests
    def test_execute_multiple_commands_partial_success(self, mock_print, mock_time, mock_sleep):
        """Test executing multiple commands with some failing"""
        # Setup mocks for multiple commands
        mock_time.side_effect = [
            10, 10.5, 11,  # First command
            20, 20.5, 21, 21.5, 22, 22.5, 23,  # Second command (timeout)
        ]
        
        # Different responses for each command
        self.mock_connection.read_channel.side_effect = [
            "terminal length 0\n#",  # Command 1, first read
            "",  # Command 1, second read (no more output)
            "show running-config",  # Command 2, first read
            "...",  # Command 2, more output
            "still running..."  # Command 2, no prompt (timeout)
        ]
        
        # Execute multiple commands
        commands = ["terminal length 0", "show running-config"]
        results = self.handler.execute_multiple_commands(commands)
        
        # Verify summary shows partial success
        self.assertEqual(results['summary']['successful'], 1)
        self.assertEqual(results['summary']['failed'], 1)
        self.assertFalse(results['summary']['all_succeeded'])
        self.assertEqual(results['summary']['status'], 'PARTIAL')
        
        # Verify individual results
        self.assertTrue(results['terminal length 0']['success'])
        self.assertFalse(results['show running-config']['success'])
    
    def test_get_command_failures(self):
        """Test getting list of failed commands"""
        # Populate command history with some successes and failures
        self.handler.command_history = {
            'show version': {'success': True},
            'show running-config': {'success': False},
            'show interfaces': {'success': True},
            'show platform': {'success': False}
        }
        
        # Get command failures
        failures = self.handler.get_command_failures()
        
        # Verify failed commands are returned
        self.assertEqual(len(failures), 2)
        self.assertIn('show running-config', failures)
        self.assertIn('show platform', failures)

if __name__ == "__main__":
    unittest.main()

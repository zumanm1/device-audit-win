#!/usr/bin/env python3
"""Unit tests for ConnectionManager module."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from rr4_complete_enchanced_v4_cli_core.connection_manager import ConnectionManager, ConnectionPool, ConnectionConfig

class TestConnectionManager(unittest.TestCase):
    """Test cases for ConnectionManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ConnectionManager(max_connections=5)
        # Mock the _create_connection_with_diagnostics method
        self.manager.connection_pool._create_connection_with_diagnostics = MagicMock()
        self.mock_connection = Mock()
        self.manager.connection_pool._create_connection_with_diagnostics.return_value = self.mock_connection
    
    def test_get_connection(self):
        """Test getting a connection."""
        with self.manager.get_connection('192.168.1.1', 'cisco_ios', 'admin', 'password') as conn:
            self.assertEqual(conn, self.mock_connection)
            
    def test_connection_retry(self):
        """Test connection retry logic."""
        # First attempt fails, second succeeds
        self.manager.connection_pool._create_connection_with_diagnostics.side_effect = [
            None,  # First attempt fails
            self.mock_connection  # Second attempt succeeds
        ]
        
        with self.manager.get_connection('192.168.1.1', 'cisco_ios', 'admin', 'password') as conn:
            self.assertEqual(conn, self.mock_connection)
    
    def test_execute_command(self):
        """Test command execution."""
        mock_connection = Mock()
        mock_connection.send_command.return_value = "Command output"
        
        result = self.manager.execute_command(mock_connection, "show version")
        self.assertTrue(result['success'])
        self.assertEqual(result['output'], "Command output")
    
    def test_execute_commands_batch(self):
        """Test batch command execution."""
        mock_connection = Mock()
        mock_connection.send_command.return_value = "Command output"
        
        commands = ["show version", "show ip interface brief"]
        results = self.manager.execute_commands_batch(mock_connection, commands)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['success'] for r in results))

class TestConnectionPool(unittest.TestCase):
    """Test cases for ConnectionPool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pool = ConnectionPool(max_connections=3)
        # Mock the _create_connection_with_diagnostics method
        self.pool._create_connection_with_diagnostics = MagicMock()
        self.mock_connection = Mock()
        self.pool._create_connection_with_diagnostics.return_value = self.mock_connection
    
    def test_acquire_connection(self):
        """Test acquiring a connection."""
        config = ConnectionConfig(
            hostname='192.168.1.1',
            device_type='cisco_ios',
            username='admin',
            password='password'
        )
        
        connection = self.pool.acquire_connection(config)
        self.assertEqual(connection, self.mock_connection)
        self.assertEqual(len(self.pool.active_connections), 1)
    
    def test_connection_pool_limit(self):
        """Test connection pool limit enforcement."""
        configs = [
            ConnectionConfig(hostname=f'192.168.1.{i}',
                           device_type='cisco_ios',
                           username='admin',
                           password='password')
            for i in range(1, 5)
        ]
        
        # Create max_connections
        for i in range(self.pool.max_connections):
            connection = self.pool.acquire_connection(configs[i])
            self.assertIsNotNone(connection)
        
        # Try to create one more connection
        with self.assertRaises(Exception) as context:
            self.pool.acquire_connection(configs[3])
        self.assertIn("Connection pool exhausted", str(context.exception))
    
    def test_cleanup_dead_connections(self):
        """Test cleaning up dead connections."""
        # Create mock connections
        mock_connections = {
            'conn1': Mock(spec=['disconnect']),
            'conn2': Mock(spec=['disconnect'])
        }
        
        # Set up the pool with mock connections
        self.pool.active_connections = mock_connections.copy()
        self.pool.connection_metadata = {
            'conn1': {'created_at': time.time(), 'hostname': '192.168.1.1'},
            'conn2': {'created_at': time.time(), 'hostname': '192.168.1.2'}
        }
        
        # Mock connection health check to return one dead connection
        with patch.object(self.pool, '_is_connection_alive') as mock_check:
            mock_check.side_effect = [True, False]
            
            cleaned = self.pool._cleanup_dead_connections()
            
            self.assertEqual(cleaned, 1)
            self.assertEqual(len(self.pool.active_connections), 1)
    
    def test_connection_reuse(self):
        """Test connection reuse logic."""
        config = ConnectionConfig(
            hostname='192.168.1.1',
            device_type='cisco_ios',
            username='admin',
            password='password'
        )
        
        # First connection attempt
        conn1 = self.pool.acquire_connection(config)
        self.assertEqual(conn1, self.mock_connection)
        
        # Second connection attempt should reuse the first connection
        conn2 = self.pool.acquire_connection(config)
        self.assertEqual(conn1, conn2)
        self.assertEqual(self.pool._pool_stats['total_reused'], 1)

if __name__ == '__main__':
    unittest.main() 
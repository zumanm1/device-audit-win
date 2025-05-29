#!/usr/bin/env python3
"""
Connection Manager Module for RR4 Complete Enhanced v4 CLI

This module handles SSH connections to network devices through jump hosts
with connection pooling, retry logic, and session management.

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from contextlib import contextmanager
import paramiko
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

@dataclass
class ConnectionConfig:
    """Connection configuration container."""
    hostname: str
    device_type: str
    username: str
    password: str
    port: int = 22
    timeout: int = 60
    session_timeout: int = 300
    global_delay_factor: int = 2
    jump_host: Optional[Dict[str, Any]] = None

class ConnectionPool:
    """Manage a pool of SSH connections."""
    
    def __init__(self, max_connections: int = 15):
        self.max_connections = max_connections
        self.active_connections: Dict[str, Any] = {}
        self.connection_lock = threading.Lock()
        self.logger = logging.getLogger('rr4_collector.connection_pool')
    
    def get_connection_key(self, config: ConnectionConfig) -> str:
        """Generate unique key for connection."""
        return f"{config.hostname}:{config.port}:{config.username}"
    
    def acquire_connection(self, config: ConnectionConfig) -> Any:
        """Acquire a connection from the pool."""
        key = self.get_connection_key(config)
        
        with self.connection_lock:
            if key in self.active_connections:
                connection = self.active_connections[key]
                if self._is_connection_alive(connection):
                    self.logger.debug(f"Reusing connection to {config.hostname}")
                    return connection
                else:
                    # Remove dead connection
                    del self.active_connections[key]
            
            # Create new connection if under limit
            if len(self.active_connections) < self.max_connections:
                connection = self._create_connection(config)
                if connection:
                    self.active_connections[key] = connection
                    return connection
            
            return None
    
    def release_connection(self, config: ConnectionConfig, connection: Any) -> None:
        """Release a connection back to the pool."""
        # For now, keep connections alive in the pool
        # In production, you might want to implement connection aging
        pass
    
    def close_all_connections(self) -> None:
        """Close all connections in the pool."""
        with self.connection_lock:
            for key, connection in self.active_connections.items():
                try:
                    connection.disconnect()
                    self.logger.debug(f"Closed connection: {key}")
                except Exception as e:
                    self.logger.warning(f"Error closing connection {key}: {e}")
            
            self.active_connections.clear()
    
    def _create_connection(self, config: ConnectionConfig) -> Optional[Any]:
        """Create a new SSH connection."""
        try:
            connection_params = {
                'device_type': config.device_type,
                'host': config.hostname,
                'username': config.username,
                'password': config.password,
                'port': config.port,
                'timeout': config.timeout,
                'session_timeout': config.session_timeout,
                'global_delay_factor': config.global_delay_factor,
                'verbose': False
            }
            
            # Add jump host configuration if provided
            if config.jump_host:
                connection_params.update({
                    'ssh_config_file': None,
                    'sock': self._create_jump_host_socket(config)
                })
            
            connection = ConnectHandler(**connection_params)
            self.logger.debug(f"Created new connection to {config.hostname}")
            return connection
            
        except Exception as e:
            self.logger.error(f"Failed to create connection to {config.hostname}: {e}")
            return None
    
    def _create_jump_host_socket(self, config: ConnectionConfig) -> paramiko.Channel:
        """Create SSH socket through jump host."""
        if not config.jump_host:
            raise ValueError("Jump host configuration required")
        
        # Create SSH client for jump host
        jump_ssh = paramiko.SSHClient()
        jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            jump_ssh.connect(
                hostname=config.jump_host['hostname'],
                username=config.jump_host['username'],
                password=config.jump_host['password'],
                port=config.jump_host.get('port', 22),
                timeout=config.timeout
            )
            
            # Create tunnel through jump host
            transport = jump_ssh.get_transport()
            dest_addr = (config.hostname, config.port)
            local_addr = ('127.0.0.1', 0)
            
            channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
            return channel
            
        except Exception as e:
            self.logger.error(f"Failed to create jump host tunnel: {e}")
            jump_ssh.close()
            raise
    
    def _is_connection_alive(self, connection: Any) -> bool:
        """Check if connection is still alive."""
        try:
            # Send a simple command to test connectivity
            connection.send_command("", expect_string=r"[>#]", read_timeout=5)
            return True
        except Exception:
            return False

class ConnectionManager:
    """Manage SSH connections with retry logic and error handling."""
    
    def __init__(self, jump_host_config: Optional[Dict[str, Any]] = None, 
                 max_connections: int = 15, retry_attempts: int = 3, retry_delay: int = 5):
        self.jump_host_config = jump_host_config
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.connection_pool = ConnectionPool(max_connections)
        self.logger = logging.getLogger('rr4_collector.connection_manager')
    
    @contextmanager
    def get_connection(self, hostname: str, device_type: str, username: str, password: str, **kwargs):
        """Context manager for getting connections with automatic cleanup."""
        config = ConnectionConfig(
            hostname=hostname,
            device_type=device_type,
            username=username,
            password=password,
            jump_host=self.jump_host_config,
            **kwargs
        )
        
        connection = None
        attempt = 0
        
        while attempt < self.retry_attempts:
            try:
                connection = self.connection_pool.acquire_connection(config)
                if connection:
                    # Prepare session for command execution
                    self._prepare_session(connection)
                    yield connection
                    break
                else:
                    raise Exception("Failed to acquire connection from pool")
                    
            except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
                attempt += 1
                self.logger.warning(f"Connection attempt {attempt} failed for {hostname}: {e}")
                
                if attempt < self.retry_attempts:
                    self.logger.info(f"Retrying connection to {hostname} in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"All connection attempts failed for {hostname}")
                    raise
                    
            except Exception as e:
                self.logger.error(f"Unexpected error connecting to {hostname}: {e}")
                raise
                
            finally:
                if connection:
                    self.connection_pool.release_connection(config, connection)
    
    def _prepare_session(self, connection: Any) -> None:
        """Prepare SSH session for command execution."""
        try:
            # Set terminal length to 0 to avoid pagination
            connection.send_command("terminal length 0", expect_string=r"[>#]")
            
            # Set terminal width for better formatting
            connection.send_command("terminal width 0", expect_string=r"[>#]")
            
            # Disable more prompts
            connection.send_command("terminal no more", expect_string=r"[>#]")
            
            self.logger.debug("Session prepared successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to prepare session: {e}")
    
    def test_connectivity(self, hostname: str, device_type: str, username: str, password: str, **kwargs) -> Dict[str, Any]:
        """Test connectivity to a device."""
        result = {
            'hostname': hostname,
            'success': False,
            'error': None,
            'response_time': None
        }
        
        start_time = time.time()
        
        try:
            with self.get_connection(hostname, device_type, username, password, **kwargs) as connection:
                # Test with a simple command
                output = connection.send_command("show version | include uptime", read_timeout=10)
                result['success'] = True
                result['test_output'] = output.strip()
                
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Connectivity test failed for {hostname}: {e}")
        
        result['response_time'] = time.time() - start_time
        return result
    
    def execute_command(self, connection: Any, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute a command on the device."""
        result = {
            'command': command,
            'success': False,
            'output': '',
            'error': None,
            'execution_time': None
        }
        
        start_time = time.time()
        
        try:
            # Handle commands that might take longer (like BGP tables)
            if any(keyword in command.lower() for keyword in ['bgp', 'route', 'forwarding']):
                timeout = max(timeout, 120)  # Minimum 2 minutes for large tables
            
            output = connection.send_command(command, read_timeout=timeout, expect_string=r"[>#]")
            result['output'] = output
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Command execution failed: {command} - {e}")
        
        result['execution_time'] = time.time() - start_time
        return result
    
    def execute_commands_batch(self, connection: Any, commands: List[str], timeout: int = 60) -> List[Dict[str, Any]]:
        """Execute multiple commands in batch."""
        results = []
        
        for command in commands:
            result = self.execute_command(connection, command, timeout)
            results.append(result)
            
            # Add small delay between commands to avoid overwhelming the device
            time.sleep(0.5)
        
        return results
    
    def close_all_connections(self) -> None:
        """Close all active connections."""
        self.connection_pool.close_all_connections()
        self.logger.info("All connections closed")
    
    def cleanup(self) -> None:
        """Cleanup method alias for close_all_connections."""
        self.close_all_connections()

class JumpHostManager:
    """Manage jump host connections and tunneling."""
    
    def __init__(self, jump_host_config: Dict[str, Any]):
        self.config = jump_host_config
        self.logger = logging.getLogger('rr4_collector.jump_host')
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate jump host configuration."""
        required_fields = ['hostname', 'username', 'password']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Jump host configuration missing required field: {field}")
    
    def test_jump_host_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to jump host."""
        result = {
            'success': False,
            'error': None,
            'response_time': None
        }
        
        start_time = time.time()
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                hostname=self.config['hostname'],
                username=self.config['username'],
                password=self.config['password'],
                port=self.config.get('port', 22),
                timeout=30
            )
            
            # Test with a simple command
            stdin, stdout, stderr = ssh.exec_command('echo "Jump host test successful"')
            output = stdout.read().decode().strip()
            
            result['success'] = True
            result['test_output'] = output
            
            ssh.close()
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Jump host connectivity test failed: {e}")
        
        result['response_time'] = time.time() - start_time
        return result 
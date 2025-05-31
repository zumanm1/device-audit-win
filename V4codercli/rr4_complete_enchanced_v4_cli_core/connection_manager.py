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

@dataclass
class ConnectionDiagnostics:
    """Detailed connection diagnostics."""
    hostname: str
    connection_attempts: int = 0
    last_error: Optional[str] = None
    error_type: Optional[str] = None
    response_times: List[float] = None
    jump_host_status: Optional[str] = None
    device_reachable: Optional[bool] = None
    authentication_status: Optional[str] = None
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []

class ConnectionPool:
    """Manage a pool of SSH connections with enhanced monitoring."""
    
    def __init__(self, max_connections: int = 15):
        self.max_connections = max_connections
        self.active_connections: Dict[str, Any] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.connection_lock = threading.Lock()
        self.logger = logging.getLogger('rr4_collector.connection_pool')
        self._pool_stats = {
            'total_created': 0,
            'total_reused': 0,
            'total_failed': 0,
            'current_active': 0
        }
    
    def get_connection_key(self, config: ConnectionConfig) -> str:
        """Generate unique key for connection."""
        return f"{config.hostname}:{config.port}:{config.username}"
    
    def acquire_connection(self, config: ConnectionConfig) -> Any:
        """Acquire a connection from the pool with enhanced failure handling."""
        key = self.get_connection_key(config)
        
        with self.connection_lock:
            # Check for existing connection
            if key in self.active_connections:
                connection = self.active_connections[key]
                if self._is_connection_alive(connection):
                    self.logger.debug(f"Reusing connection to {config.hostname}")
                    self._pool_stats['total_reused'] += 1
                    return connection
                else:
                    # Handle dead connection
                    self.logger.warning(f"Found dead connection for {config.hostname}, attempting recovery")
                    new_connection = self._handle_connection_failure(connection, config)
                    if new_connection:
                        return new_connection
            
            # Check pool capacity
            if len(self.active_connections) >= self.max_connections:
                # Try to clean up dead connections first
                cleaned = self._cleanup_dead_connections()
                self.logger.info(f"Cleaned up {cleaned} dead connections")
                
                # If still at capacity, try to free some connections
                if len(self.active_connections) >= self.max_connections:
                    freed = self._free_oldest_connections(min(3, len(self.active_connections) // 4))
                    self.logger.info(f"Freed {freed} oldest connections to make room")
            
            # Create new connection if under limit
            if len(self.active_connections) < self.max_connections:
                connection = self._create_connection_with_diagnostics(config)
                if connection:
                    self.active_connections[key] = connection
                    self.connection_metadata[key] = {
                        'created_at': time.time(),
                        'last_used': time.time(),
                        'hostname': config.hostname,
                        'usage_count': 0
                    }
                    self._pool_stats['current_active'] += 1
                    self._pool_stats['total_created'] += 1
                    self.logger.info(f"Created new connection to {config.hostname}")
                    return connection
                else:
                    self._pool_stats['total_failed'] += 1
            
            # Pool is full and couldn't create connection
            error_msg = f"Connection pool exhausted ({len(self.active_connections)}/{self.max_connections}). Unable to connect to {config.hostname}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _create_connection_with_diagnostics(self, config: ConnectionConfig) -> Optional[Any]:
        """Create a new SSH connection with detailed diagnostics."""
        diagnostics = ConnectionDiagnostics(hostname=config.hostname)
        
        try:
            diagnostics.connection_attempts += 1
            start_time = time.time()
            
            # Skip direct connectivity test if jump host is configured
            if not config.jump_host:
                # Check if hostname is reachable (basic connectivity test)
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    result = sock.connect_ex((config.hostname, config.port))
                    sock.close()
                    diagnostics.device_reachable = (result == 0)
                    if result != 0:
                        diagnostics.last_error = f"Device unreachable on port {config.port}"
                        self.logger.warning(f"Device {config.hostname} unreachable on port {config.port}")
                except Exception as e:
                    diagnostics.device_reachable = False
                    diagnostics.last_error = f"Connectivity test failed: {str(e)}"
                
                if not diagnostics.device_reachable:
                    return None
            else:
                # When using jump host, assume device is reachable through jump host
                diagnostics.device_reachable = True
                self.logger.info(f"Using jump host for {config.hostname}, skipping direct connectivity test")
            
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
                try:
                    self.logger.info(f"Establishing jump host tunnel for {config.hostname}")
                    sock = self._create_jump_host_socket(config)
                    connection_params.update({
                        'ssh_config_file': None,
                        'sock': sock
                    })
                    diagnostics.jump_host_status = "connected"
                    self.logger.info(f"Jump host tunnel established for {config.hostname}")
                except Exception as e:
                    diagnostics.jump_host_status = f"failed: {str(e)}"
                    diagnostics.last_error = f"Jump host connection failed: {str(e)}"
                    self.logger.error(f"Jump host connection failed for {config.hostname}: {e}")
                    return None
            
            self.logger.info(f"Connecting to {config.hostname} via {'jump host' if config.jump_host else 'direct connection'}")
            connection = ConnectHandler(**connection_params)
            response_time = time.time() - start_time
            diagnostics.response_times.append(response_time)
            diagnostics.authentication_status = "success"
            
            self.logger.info(f"Successfully created connection to {config.hostname} in {response_time:.2f}s")
            return connection
            
        except NetmikoAuthenticationException as e:
            diagnostics.error_type = "authentication"
            diagnostics.authentication_status = "failed"
            diagnostics.last_error = f"Authentication failed: {str(e)}"
            self.logger.error(f"Authentication failed for {config.hostname}: {e}")
            return None
        except NetmikoTimeoutException as e:
            diagnostics.error_type = "timeout"
            diagnostics.last_error = f"Connection timeout: {str(e)}"
            self.logger.error(f"Connection timeout for {config.hostname}: {e}")
            return None
        except Exception as e:
            diagnostics.error_type = "general"
            diagnostics.last_error = f"Connection failed: {str(e)}"
            self.logger.error(f"Failed to create connection to {config.hostname}: {e}")
            return None
        finally:
            # Log diagnostics for troubleshooting
            self._log_connection_diagnostics(diagnostics)
    
    def _log_connection_diagnostics(self, diagnostics: ConnectionDiagnostics) -> None:
        """Log detailed connection diagnostics."""
        self.logger.debug(f"Connection diagnostics for {diagnostics.hostname}:")
        self.logger.debug(f"  Attempts: {diagnostics.connection_attempts}")
        self.logger.debug(f"  Device reachable: {diagnostics.device_reachable}")
        self.logger.debug(f"  Authentication: {diagnostics.authentication_status}")
        self.logger.debug(f"  Jump host: {diagnostics.jump_host_status}")
        self.logger.debug(f"  Error type: {diagnostics.error_type}")
        self.logger.debug(f"  Last error: {diagnostics.last_error}")
        if diagnostics.response_times:
            avg_time = sum(diagnostics.response_times) / len(diagnostics.response_times)
            self.logger.debug(f"  Average response time: {avg_time:.2f}s")

    def _cleanup_dead_connections(self) -> int:
        """Clean up dead connections from the pool."""
        dead_keys = []
        
        # Create a copy of the dictionary to avoid iteration issues
        connections_copy = dict(self.active_connections)
        
        for key, connection in connections_copy.items():
            if not self._is_connection_alive(connection):
                dead_keys.append(key)
        
        for key in dead_keys:
            try:
                if key in self.active_connections:
                    self.active_connections[key].disconnect()
            except:
                pass
            if key in self.active_connections:
                del self.active_connections[key]
            if key in self.connection_metadata:
                del self.connection_metadata[key]
            self._pool_stats['current_active'] -= 1
        
        return len(dead_keys)
    
    def _free_oldest_connections(self, count: int) -> int:
        """Free the oldest connections to make room for new ones."""
        if not self.connection_metadata:
            return 0
        
        # Create a copy of the metadata to avoid iteration issues  
        metadata_copy = dict(self.connection_metadata)
        
        # Sort by creation time
        sorted_connections = sorted(
            metadata_copy.items(),
            key=lambda x: x[1]['created_at']
        )
        
        freed = 0
        for key, metadata in sorted_connections[:count]:
            if key in self.active_connections:
                try:
                    self.active_connections[key].disconnect()
                    self.logger.debug(f"Freed connection to {metadata['hostname']}")
                except:
                    pass
                if key in self.active_connections:
                    del self.active_connections[key]
                if key in self.connection_metadata:
                    del self.connection_metadata[key]
                self._pool_stats['current_active'] -= 1
                freed += 1
        
        return freed

    def release_connection(self, config: ConnectionConfig, connection: Any) -> None:
        """Release a connection back to the pool."""
        key = self.get_connection_key(config)
        if key in self.connection_metadata:
            self.connection_metadata[key]['last_used'] = time.time()
            self.connection_metadata[key]['usage_count'] += 1

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
            self.connection_metadata.clear()
            self._pool_stats['current_active'] = 0
            
        self.logger.info("All connections closed")
    
    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        with self.connection_lock:
            return {
                'active_connections': len(self.active_connections),
                'max_connections': self.max_connections,
                'total_created': self._pool_stats['total_created'],
                'total_reused': self._pool_stats['total_reused'],
                'total_failed': self._pool_stats['total_failed'],
                'utilization_pct': (len(self.active_connections) / self.max_connections) * 100,
                'connection_details': {
                    key: {
                        'hostname': meta['hostname'],
                        'age_seconds': time.time() - meta['created_at'],
                        'usage_count': meta['usage_count'],
                        'last_used_seconds_ago': time.time() - meta['last_used']
                    }
                    for key, meta in self.connection_metadata.items()
                }
            }

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
        """Check if connection is still alive and responsive."""
        try:
            if not connection:
                return False
            
            # Try to send a newline to check connection
            if hasattr(connection, 'find_prompt'):
                try:
                    connection.find_prompt()
                    return True
                except:
                    return False
            
            # For raw SSH connections
            if hasattr(connection, 'transport'):
                return connection.transport.is_active()
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Connection check failed: {e}")
            return False

    def _handle_connection_failure(self, connection: Any, config: ConnectionConfig) -> Optional[Any]:
        """Handle connection failure with retry logic."""
        try:
            # Try to close the failed connection
            try:
                if hasattr(connection, 'disconnect'):
                    connection.disconnect()
            except:
                pass
            
            # Remove from pool
            key = self.get_connection_key(config)
            with self.connection_lock:
                if key in self.active_connections:
                    del self.active_connections[key]
                if key in self.connection_metadata:
                    del self.connection_metadata[key]
                self._pool_stats['current_active'] -= 1
            
            # Try to establish new connection
            new_connection = self._create_connection_with_diagnostics(config)
            if new_connection:
                with self.connection_lock:
                    self.active_connections[key] = new_connection
                    self.connection_metadata[key] = {
                        'created_at': time.time(),
                        'last_used': time.time(),
                        'hostname': config.hostname,
                        'usage_count': 0
                    }
                    self._pool_stats['current_active'] += 1
                return new_connection
            
        except Exception as e:
            self.logger.error(f"Failed to handle connection failure: {e}")
        
        return None

class ConnectionManager:
    """Manage SSH connections with retry logic and enhanced error reporting."""
    
    def __init__(self, jump_host_config: Optional[Dict[str, Any]] = None, 
                 max_connections: int = 25, retry_attempts: int = 3, retry_delay: int = 5):
        self.jump_host_config = jump_host_config
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.connection_pool = ConnectionPool(max_connections)
        self.logger = logging.getLogger('rr4_collector.connection_manager')
        self.connection_diagnostics: Dict[str, ConnectionDiagnostics] = {}
    
    @contextmanager
    def get_connection(self, hostname: str, device_type: str, username: str, password: str, **kwargs):
        """Context manager for getting connections with automatic cleanup and detailed error reporting."""
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
        last_error = None
        
        # Initialize diagnostics for this device
        if hostname not in self.connection_diagnostics:
            self.connection_diagnostics[hostname] = ConnectionDiagnostics(hostname=hostname)
        
        diagnostics = self.connection_diagnostics[hostname]
        
        while attempt < self.retry_attempts:
            try:
                attempt += 1
                diagnostics.connection_attempts += 1
                
                self.logger.info(f"Attempting connection to {hostname} (attempt {attempt}/{self.retry_attempts})")
                
                connection = self.connection_pool.acquire_connection(config)
                if connection:
                    # Prepare session for command execution
                    self._prepare_session(connection)
                    diagnostics.authentication_status = "success"
                    self.logger.info(f"Successfully connected to {hostname}")
                    yield connection
                    break
                else:
                    raise Exception("Failed to acquire connection from pool")
                    
            except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
                last_error = str(e)
                diagnostics.last_error = last_error
                diagnostics.error_type = "netmiko_specific"
                
                self.logger.warning(f"Connection attempt {attempt} failed for {hostname}: {e}")
                
                if attempt < self.retry_attempts:
                    self.logger.info(f"Retrying connection to {hostname} in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"All connection attempts failed for {hostname}: {last_error}")
                    raise
                    
            except Exception as e:
                last_error = str(e)
                diagnostics.last_error = last_error
                diagnostics.error_type = "general"
                
                # Check if it's a pool exhaustion issue
                if "pool exhausted" in last_error.lower() or "acquire connection from pool" in last_error.lower():
                    # Log pool statistics for debugging
                    pool_stats = self.connection_pool.get_pool_statistics()
                    self.logger.error(f"Connection pool issue for {hostname}: {last_error}")
                    self.logger.error(f"Pool statistics: {pool_stats}")
                    
                    # Try to clean up and retry once
                    if attempt == 1:
                        self.logger.info("Attempting to clean up connection pool...")
                        cleaned = self.connection_pool._cleanup_dead_connections()
                        self.logger.info(f"Cleaned up {cleaned} dead connections")
                        time.sleep(2)  # Short delay before retry
                        continue
                
                self.logger.error(f"Unexpected error connecting to {hostname}: {e}")
                
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay)
                else:
                    raise
                
        # Always try to release connection back to pool
        if connection:
            try:
                self.connection_pool.release_connection(config, connection)
            except Exception as e:
                self.logger.warning(f"Error releasing connection for {hostname}: {e}")

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
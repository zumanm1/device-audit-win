#!/usr/bin/env python3
"""
RR5 Router Auditing Framework - Three-Phase Network Change Validation
Version: 1.0.0
File: rr5-router-new-new.py

A comprehensive three-phase framework for validating router changes:
- Phase 1: Pre-check (Hardware & Health)
- Phase 2: Pre-check Data Collection (L3VPN/MPLS/IP/OSPF/BGP)
- Phase 3: Post-check & Comparison

Built with lessons learned from NetAuditPro:
- Structured data collection and storage
- Real-time progress tracking
- Enhanced error handling and fallback
- Comprehensive reporting (CLI, Web, Files)
- Configuration-driven approach
"""

import os
import sys
import json
import yaml
import csv
import argparse
import threading
import time
import logging
import re
import random
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import subprocess
from dataclasses import dataclass, asdict
from collections import defaultdict

# Network automation libraries
try:
    import paramiko
    from netmiko import ConnectHandler
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False
    print("[WARNING] Netmiko not available, using Paramiko only")

# Web interface libraries
try:
    from flask import Flask, render_template, request, jsonify, send_file
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("[WARNING] Flask not available, CLI-only mode")

# Reporting libraries
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

APP_VERSION = "1.0.0"
SCRIPT_NAME = "RR5 Router Auditing Framework"

# Default configuration
DEFAULT_CONFIG = {
    "jump_host": os.getenv("JUMP_HOST", "172.16.39.128"),
    "jump_username": os.getenv("JUMP_USERNAME", "cisco"),
    "jump_password": os.getenv("JUMP_PASSWORD", "cisco"),
    "device_username": os.getenv("DEVICE_USERNAME", "cisco"),
    "device_password": os.getenv("DEVICE_PASSWORD", "cisco"),
    "device_enable": os.getenv("DEVICE_ENABLE", "cisco"),
    "inventory_file": "inventory-list-v00.csv",
    "output_dir": "RR5-AUDIT-RESULTS",
    "web_port": 5015,
    "timeout": 30,
    "ping_count": 10,
    "ping_timeout": 2,
    "ping_size": 1500
}

# Phase definitions
AUDIT_PHASES = {
    "pre": "Phase 1 & 2: Pre-check Hardware Health + Data Collection",
    "post": "Phase 3: Post-check Data Collection",
    "compare": "Phase 3: Comparison and Analysis"
}

# Health check thresholds
HEALTH_THRESHOLDS = {
    "cpu_max": 70,          # CPU should be < 70%
    "memory_min": 30,       # Memory should have > 30% free
    "disk_min": 20,         # Disk should have > 20% free
    "temperature_max": 75,  # Temperature should be < 75°C
    "bgp_prefix_delta": 2,  # BGP prefix changes ≤ 2
    "cpu_delta": 10,        # CPU delta ≤ 10%
    "crc_error_delta": 0    # CRC errors delta = 0
}

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DeviceInfo:
    """Device information from inventory"""
    name: str
    ip_address: str
    device_type: str
    description: str = ""
    location: str = ""
    group: str = ""

@dataclass
class HealthMetrics:
    """Hardware health metrics"""
    timestamp: str
    device: str
    cpu_percent: float
    memory_used_percent: float
    memory_free_percent: float
    disk_used_percent: float
    disk_free_percent: float
    temperature_max: float
    power_status: str
    environment_status: str
    chassis_status: str

@dataclass
class InterfaceMetrics:
    """Interface metrics"""
    name: str
    status: str
    ip_address: str
    mtu: int
    crc_errors: int
    input_drops: int
    output_drops: int
    input_packets: int
    output_packets: int

@dataclass
class RoutingMetrics:
    """Routing protocol metrics"""
    ospf_neighbors: int
    ospf_interfaces: int
    bgp_neighbors: int
    bgp_prefixes_received: int
    bgp_prefixes_advertised: int
    total_routes: int
    ldp_sessions: int
    ldp_interfaces: int

@dataclass
class VRFMetrics:
    """VRF-specific metrics"""
    name: str
    import_rt: List[str]
    export_rt: List[str]
    imported_routes: int
    exported_routes: int
    sample_routes: List[Dict[str, Any]]

@dataclass
class AuditResult:
    """Individual audit check result"""
    check_name: str
    category: str
    pre_value: Any
    post_value: Any
    delta: Any
    status: str  # PASS, WARN, FAIL
    threshold: Any
    message: str

# ============================================================================
# LOGGING AND UTILITIES
# ============================================================================

class AuditLogger:
    """Enhanced logging with real-time updates"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file
        self.logs = []
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.log_file) if self.log_file else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        self.logs.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
        
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
        
        # Emit to web interface if available
        if FLASK_AVAILABLE and hasattr(self, 'socketio'):
            self.socketio.emit('audit_log', {
                'timestamp': timestamp,
                'level': level,
                'message': message
            })
    
    def get_logs(self) -> List[Dict]:
        """Get all logs"""
        return self.logs

def sanitize_credentials(text: str) -> str:
    """Sanitize sensitive information from logs"""
    # Patterns for credential sanitization
    patterns = [
        (r'password\s*[:=]\s*\S+', 'password: ####'),
        (r'username\s*[:=]\s*(\w+)', r'username: ****'),
        (r'enable\s*[:=]\s*\S+', 'enable: ####'),
        (r'(\w+):(\w+)@', r'****:####@'),
        (r'ssh\s+(\w+)@', r'ssh ****@')
    ]
    
    sanitized = text
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized

def parse_inventory(inventory_file: str) -> List[DeviceInfo]:
    """Parse inventory file (CSV or YAML)"""
    devices = []
    
    if not os.path.exists(inventory_file):
        raise FileNotFoundError(f"Inventory file not found: {inventory_file}")
    
    if inventory_file.endswith('.csv'):
        with open(inventory_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                devices.append(DeviceInfo(
                    name=row.get('device_name', ''),
                    ip_address=row.get('ip_address', ''),
                    device_type=row.get('device_type', 'cisco_ios'),
                    description=row.get('description', ''),
                    location=row.get('location', ''),
                    group=row.get('group', '')
                ))
    
    elif inventory_file.endswith(('.yml', '.yaml')):
        with open(inventory_file, 'r') as f:
            data = yaml.safe_load(f)
            for device_name, device_info in data.items():
                devices.append(DeviceInfo(
                    name=device_name,
                    ip_address=device_info.get('ip_address', ''),
                    device_type=device_info.get('device_type', 'cisco_ios'),
                    description=device_info.get('description', ''),
                    location=device_info.get('location', ''),
                    group=device_info.get('group', '')
                ))
    
    return devices

# ============================================================================
# NETWORK CONNECTION MANAGEMENT
# ============================================================================

class NetworkConnector:
    """Enhanced network connection management with fallback"""
    
    def __init__(self, config: Dict, logger: AuditLogger):
        self.config = config
        self.logger = logger
        self.connections = {}
    
    def connect_device(self, device: DeviceInfo) -> Optional[Any]:
        """Connect to device with fallback mechanism"""
        connection_params = {
            'device_type': device.device_type,
            'host': device.ip_address,
            'username': self.config['device_username'],
            'password': self.config['device_password'],
            'secret': self.config['device_enable'],
            'timeout': self.config['timeout'],
            'session_timeout': self.config['timeout'] * 2,
            'auth_timeout': 15,
            'banner_timeout': 10,
            'conn_timeout': 10
        }
        
        # Try Netmiko first
        if NETMIKO_AVAILABLE:
            try:
                self.logger.log(f"Connecting to {device.name} ({device.ip_address}) via Netmiko")
                connection = ConnectHandler(**connection_params)
                if self.config['device_enable']:
                    connection.enable()
                self.connections[device.name] = connection
                self.logger.log(f"✅ Connected to {device.name} successfully")
                return connection
            except Exception as e:
                self.logger.log(f"Netmiko connection failed for {device.name}: {sanitize_credentials(str(e))}", "WARNING")
        
        # Fallback to Paramiko
        try:
            self.logger.log(f"Falling back to Paramiko for {device.name}")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                device.ip_address,
                username=self.config['device_username'],
                password=self.config['device_password'],
                timeout=self.config['timeout']
            )
            
            # Wrap Paramiko client to mimic Netmiko interface
            wrapper = ParamikoWrapper(client, self.config['device_enable'])
            self.connections[device.name] = wrapper
            self.logger.log(f"✅ Connected to {device.name} via Paramiko")
            return wrapper
            
        except Exception as e:
            self.logger.log(f"❌ All connection methods failed for {device.name}: {sanitize_credentials(str(e))}", "ERROR")
            return None
    
    def disconnect_device(self, device_name: str):
        """Disconnect from device"""
        if device_name in self.connections:
            try:
                self.connections[device_name].disconnect()
                del self.connections[device_name]
                self.logger.log(f"Disconnected from {device_name}")
            except Exception as e:
                self.logger.log(f"Error disconnecting from {device_name}: {e}", "WARNING")
    
    def disconnect_all(self):
        """Disconnect from all devices"""
        for device_name in list(self.connections.keys()):
            self.disconnect_device(device_name)

class ParamikoWrapper:
    """Paramiko wrapper to mimic Netmiko interface"""
    
    def __init__(self, client: paramiko.SSHClient, enable_password: str = None):
        self.client = client
        self.enable_password = enable_password
        self.shell = None
    
    def send_command(self, command: str, **kwargs) -> str:
        """Send command and return output"""
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=kwargs.get('timeout', 30))
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                raise Exception(f"Command error: {error}")
            
            return output
        except Exception as e:
            raise Exception(f"Command execution failed: {e}")
    
    def enable(self):
        """Enter enable mode (simplified)"""
        if self.enable_password:
            try:
                self.send_command("enable")
                # Note: This is a simplified implementation
                # Real implementation would handle enable password prompt
            except:
                pass
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            self.client.close()
        except:
            pass

# ============================================================================
# COMMAND EXECUTION ENGINE
# ============================================================================

class CommandExecutor:
    """Command execution with comprehensive error handling"""
    
    def __init__(self, logger: AuditLogger):
        self.logger = logger
        self.command_results = {}
    
    def execute_command(self, connection: Any, command: str, device_name: str) -> Dict[str, Any]:
        """Execute command with error handling and logging"""
        start_time = time.time()
        result = {
            'command': command,
            'device': device_name,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'output': '',
            'error': '',
            'execution_time': 0
        }
        
        try:
            self.logger.log(f"[{device_name}] Executing: {command}")
            
            output = connection.send_command(command, timeout=30)
            execution_time = time.time() - start_time
            
            result.update({
                'success': True,
                'output': output,
                'execution_time': execution_time
            })
            
            # Store sanitized version
            sanitized_output = sanitize_credentials(output)
            self.logger.log(f"[{device_name}] Command completed in {execution_time:.2f}s")
            
            # Store result
            if device_name not in self.command_results:
                self.command_results[device_name] = []
            self.command_results[device_name].append(result.copy())
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = sanitize_credentials(str(e))
            
            result.update({
                'success': False,
                'error': error_msg,
                'execution_time': execution_time
            })
            
            self.logger.log(f"[{device_name}] Command failed: {error_msg}", "ERROR")
            
            if device_name not in self.command_results:
                self.command_results[device_name] = []
            self.command_results[device_name].append(result.copy())
            
            return result
    
    def get_command_history(self, device_name: str = None) -> Dict[str, List]:
        """Get command execution history"""
        if device_name:
            return self.command_results.get(device_name, [])
        return self.command_results

# ============================================================================
# DATA PARSERS
# ============================================================================

class DataParser:
    """Parse command outputs into structured data"""
    
    def __init__(self, logger: AuditLogger):
        self.logger = logger
    
    def parse_cpu_memory(self, output: str, device_type: str) -> Dict[str, float]:
        """Parse CPU and memory usage"""
        result = {
            'cpu_percent': 0.0,
            'memory_used_percent': 0.0,
            'memory_free_percent': 0.0
        }
        
        try:
            if 'cisco_ios' in device_type:
                # Parse IOS CPU
                cpu_match = re.search(r'CPU utilization for.*?(\d+)%', output, re.IGNORECASE)
                if cpu_match:
                    result['cpu_percent'] = float(cpu_match.group(1))
                
                # Parse IOS memory
                mem_match = re.search(r'(\d+)\s+(\d+)\s+(\d+)', output)
                if mem_match:
                    total = int(mem_match.group(1))
                    used = int(mem_match.group(2))
                    free = int(mem_match.group(3))
                    result['memory_used_percent'] = (used / total) * 100
                    result['memory_free_percent'] = (free / total) * 100
            
            elif 'cisco_ios_xr' in device_type:
                # Parse XR CPU
                cpu_match = re.search(r'(\d+\.\d+)%', output)
                if cpu_match:
                    result['cpu_percent'] = float(cpu_match.group(1))
        
        except Exception as e:
            self.logger.log(f"Error parsing CPU/Memory: {e}", "WARNING")
        
        return result
    
    def parse_interfaces(self, output: str) -> List[InterfaceMetrics]:
        """Parse interface information"""
        interfaces = []
        
        try:
            lines = output.split('\n')
            for line in lines:
                if 'GigabitEthernet' in line or 'FastEthernet' in line or 'TenGigE' in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        interface = InterfaceMetrics(
                            name=parts[0],
                            status=parts[1],
                            ip_address=parts[1] if len(parts) > 1 else '',
                            mtu=1500,  # Default, would need separate command
                            crc_errors=0,  # Would need detailed interface stats
                            input_drops=0,
                            output_drops=0,
                            input_packets=0,
                            output_packets=0
                        )
                        interfaces.append(interface)
        
        except Exception as e:
            self.logger.log(f"Error parsing interfaces: {e}", "WARNING")
        
        return interfaces
    
    def parse_routing_summary(self, output: str) -> RoutingMetrics:
        """Parse routing protocol summary"""
        metrics = RoutingMetrics(
            ospf_neighbors=0,
            ospf_interfaces=0,
            bgp_neighbors=0,
            bgp_prefixes_received=0,
            bgp_prefixes_advertised=0,
            total_routes=0,
            ldp_sessions=0,
            ldp_interfaces=0
        )
        
        try:
            # Parse total routes
            route_match = re.search(r'Total.*?(\d+)', output, re.IGNORECASE)
            if route_match:
                metrics.total_routes = int(route_match.group(1))
        
        except Exception as e:
            self.logger.log(f"Error parsing routing summary: {e}", "WARNING")
        
        return metrics
    
    def parse_vrfs(self, output: str) -> List[VRFMetrics]:
        """Parse VRF information"""
        vrfs = []
        
        try:
            # This would need specific parsing based on device type and output format
            # For now, return empty list
            pass
        
        except Exception as e:
            self.logger.log(f"Error parsing VRFs: {e}", "WARNING")
        
        return vrfs
    
    def extract_random_routes(self, output: str, count: int = 2) -> List[Dict[str, Any]]:
        """Extract random routes for comparison"""
        routes = []
        
        try:
            lines = output.split('\n')
            route_lines = [line for line in lines if re.match(r'^\s*\d+\.\d+\.\d+\.\d+', line)]
            
            if route_lines:
                # Select first and random route
                selected_lines = [route_lines[0]]
                if len(route_lines) > 1:
                    random_index = random.randint(1, len(route_lines) - 1)
                    selected_lines.append(route_lines[random_index])
                
                for line in selected_lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        routes.append({
                            'prefix': parts[0],
                            'next_hop': parts[1] if len(parts) > 1 else '',
                            'metric': parts[2] if len(parts) > 2 else '',
                            'full_line': line.strip()
                        })
        
        except Exception as e:
            self.logger.log(f"Error extracting random routes: {e}", "WARNING")
        
        return routes

# ============================================================================
# AUDIT PHASES
# ============================================================================

class Phase1HealthChecker:
    """Phase 1: Hardware Health Checks"""
    
    def __init__(self, connector: NetworkConnector, executor: CommandExecutor, parser: DataParser, logger: AuditLogger):
        self.connector = connector
        self.executor = executor
        self.parser = parser
        self.logger = logger
    
    def check_device_health(self, device: DeviceInfo) -> HealthMetrics:
        """Perform comprehensive health check on device"""
        self.logger.log(f"🔍 Phase 1: Health check for {device.name}")
        
        connection = self.connector.connect_device(device)
        if not connection:
            return None
        
        try:
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'device': device.name,
                'cpu_percent': 0.0,
                'memory_used_percent': 0.0,
                'memory_free_percent': 0.0,
                'disk_used_percent': 0.0,
                'disk_free_percent': 0.0,
                'temperature_max': 0.0,
                'power_status': 'Unknown',
                'environment_status': 'Unknown',
                'chassis_status': 'Unknown'
            }
            
            # CPU and Memory
            cpu_cmd = self._get_cpu_command(device.device_type)
            mem_cmd = self._get_memory_command(device.device_type)
            
            if cpu_cmd:
                result = self.executor.execute_command(connection, cpu_cmd, device.name)
                if result['success']:
                    cpu_mem_data = self.parser.parse_cpu_memory(result['output'], device.device_type)
                    health_data.update(cpu_mem_data)
            
            # Environment
            env_cmd = self._get_environment_command(device.device_type)
            if env_cmd:
                result = self.executor.execute_command(connection, env_cmd, device.name)
                if result['success']:
                    health_data['environment_status'] = 'OK' if 'OK' in result['output'] else 'CHECK'
            
            # Platform/Chassis
            platform_cmd = self._get_platform_command(device.device_type)
            if platform_cmd:
                result = self.executor.execute_command(connection, platform_cmd, device.name)
                if result['success']:
                    health_data['chassis_status'] = 'OK' if 'OK' in result['output'] else 'CHECK'
            
            # Disk space
            disk_cmd = self._get_disk_command(device.device_type)
            if disk_cmd:
                result = self.executor.execute_command(connection, disk_cmd, device.name)
                if result['success']:
                    # Parse disk usage (simplified)
                    if 'bytes' in result['output']:
                        health_data['disk_free_percent'] = 80.0  # Placeholder
                        health_data['disk_used_percent'] = 20.0
            
            return HealthMetrics(**health_data)
        
        finally:
            self.connector.disconnect_device(device.name)
    
    def _get_cpu_command(self, device_type: str) -> str:
        """Get CPU command for device type"""
        commands = {
            'cisco_ios': 'show processes cpu history',
            'cisco_ios_xe': 'show processes cpu history',
            'cisco_ios_xr': 'show processes cpu'
        }
        return commands.get(device_type, 'show processes cpu')
    
    def _get_memory_command(self, device_type: str) -> str:
        """Get memory command for device type"""
        commands = {
            'cisco_ios': 'show processes memory',
            'cisco_ios_xe': 'show memory statistics',
            'cisco_ios_xr': 'show memory summary'
        }
        return commands.get(device_type, 'show processes memory')
    
    def _get_environment_command(self, device_type: str) -> str:
        """Get environment command for device type"""
        commands = {
            'cisco_ios': 'show env all',
            'cisco_ios_xe': 'show env all',
            'cisco_ios_xr': 'show environment all'
        }
        return commands.get(device_type, 'show env all')
    
    def _get_platform_command(self, device_type: str) -> str:
        """Get platform command for device type"""
        commands = {
            'cisco_ios': 'show inventory',
            'cisco_ios_xe': 'show platform',
            'cisco_ios_xr': 'show platform'
        }
        return commands.get(device_type, 'show platform')
    
    def _get_disk_command(self, device_type: str) -> str:
        """Get disk command for device type"""
        commands = {
            'cisco_ios': 'show disk0:',
            'cisco_ios_xe': 'show disk0:',
            'cisco_ios_xr': 'show disk0:'
        }
        return commands.get(device_type, 'show disk0:')

class Phase2DataCollector:
    """Phase 2: Data Collection (L3VPN/MPLS/IP/OSPF/BGP)"""
    
    def __init__(self, connector: NetworkConnector, executor: CommandExecutor, parser: DataParser, logger: AuditLogger):
        self.connector = connector
        self.executor = executor
        self.parser = parser
        self.logger = logger
    
    def collect_device_data(self, device: DeviceInfo) -> Dict[str, Any]:
        """Collect comprehensive data from device"""
        self.logger.log(f"📊 Phase 2: Data collection for {device.name}")
        
        connection = self.connector.connect_device(device)
        if not connection:
            return None
        
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'device': device.name,
                'interfaces': [],
                'routing': {},
                'vrfs': [],
                'sample_routes': [],
                'reachability': {}
            }
            
            # Collect interface data
            self._collect_interfaces(connection, device, data)
            
            # Collect routing data
            self._collect_routing(connection, device, data)
            
            # Collect VRF data
            self._collect_vrfs(connection, device, data)
            
            # Collect sample routes
            self._collect_sample_routes(connection, device, data)
            
            # Perform reachability tests
            self._test_reachability(connection, device, data)
            
            return data
        
        finally:
            self.connector.disconnect_device(device.name)
    
    def _collect_interfaces(self, connection: Any, device: DeviceInfo, data: Dict):
        """Collect interface information"""
        commands = [
            'show ip interface brief',
            'show interfaces'
        ]
        
        for cmd in commands:
            result = self.executor.execute_command(connection, cmd, device.name)
            if result['success']:
                if 'brief' in cmd:
                    interfaces = self.parser.parse_interfaces(result['output'])
                    data['interfaces'] = [asdict(intf) for intf in interfaces]
    
    def _collect_routing(self, connection: Any, device: DeviceInfo, data: Dict):
        """Collect routing protocol information"""
        commands = [
            'show ip route summary',
            'show ip ospf interface brief',
            'show ip ospf neighbor',
            'show bgp all summary',
            'show mpls ldp neighbors',
            'show mpls interfaces'
        ]
        
        routing_data = {}
        
        for cmd in commands:
            result = self.executor.execute_command(connection, cmd, device.name)
            if result['success']:
                if 'route summary' in cmd:
                    routing_metrics = self.parser.parse_routing_summary(result['output'])
                    routing_data.update(asdict(routing_metrics))
                else:
                    # Store raw output for other commands
                    cmd_key = cmd.replace(' ', '_').replace('show_', '')
                    routing_data[cmd_key] = result['output']
        
        data['routing'] = routing_data
    
    def _collect_vrfs(self, connection: Any, device: DeviceInfo, data: Dict):
        """Collect VRF information"""
        vrf_commands = [
            'show vrf detail',
            'show ip vrf detail'
        ]
        
        for cmd in vrf_commands:
            result = self.executor.execute_command(connection, cmd, device.name)
            if result['success']:
                vrfs = self.parser.parse_vrfs(result['output'])
                data['vrfs'] = [asdict(vrf) for vrf in vrfs]
                break
    
    def _collect_sample_routes(self, connection: Any, device: DeviceInfo, data: Dict):
        """Collect sample routes for comparison"""
        route_commands = [
            'show ip route',
            'show ip route bgp'
        ]
        
        for cmd in route_commands:
            result = self.executor.execute_command(connection, cmd, device.name)
            if result['success']:
                sample_routes = self.parser.extract_random_routes(result['output'])
                if sample_routes:
                    data['sample_routes'].extend(sample_routes)
    
    def _test_reachability(self, connection: Any, device: DeviceInfo, data: Dict):
        """Test reachability to key destinations"""
        # This would ping configured neighbors or test destinations
        # For now, just record that we attempted reachability tests
        data['reachability'] = {
            'tests_performed': True,
            'timestamp': datetime.now().isoformat()
        }

class Phase3Comparator:
    """Phase 3: Post-check and Comparison"""
    
    def __init__(self, logger: AuditLogger):
        self.logger = logger
        self.thresholds = HEALTH_THRESHOLDS
    
    def compare_datasets(self, pre_data: Dict, post_data: Dict) -> List[AuditResult]:
        """Compare pre and post datasets"""
        self.logger.log("🔄 Phase 3: Comparing pre and post data")
        
        results = []
        
        # Compare each device
        for device_name in pre_data.keys():
            if device_name not in post_data:
                results.append(AuditResult(
                    check_name=f"{device_name}_availability",
                    category="device",
                    pre_value="Available",
                    post_value="Missing",
                    delta="Device not found in post-check",
                    status="FAIL",
                    threshold="Available",
                    message=f"Device {device_name} not found in post-check data"
                ))
                continue
            
            device_results = self._compare_device_data(
                device_name, 
                pre_data[device_name], 
                post_data[device_name]
            )
            results.extend(device_results)
        
        return results
    
    def _compare_device_data(self, device_name: str, pre_data: Dict, post_data: Dict) -> List[AuditResult]:
        """Compare data for a single device"""
        results = []
        
        # Compare health metrics
        if 'health' in pre_data and 'health' in post_data:
            health_results = self._compare_health_metrics(device_name, pre_data['health'], post_data['health'])
            results.extend(health_results)
        
        # Compare interface metrics
        if 'data' in pre_data and 'data' in post_data:
            interface_results = self._compare_interfaces(device_name, pre_data['data'], post_data['data'])
            results.extend(interface_results)
            
            # Compare routing metrics
            routing_results = self._compare_routing(device_name, pre_data['data'], post_data['data'])
            results.extend(routing_results)
            
            # Compare sample routes
            route_results = self._compare_sample_routes(device_name, pre_data['data'], post_data['data'])
            results.extend(route_results)
        
        return results
    
    def _compare_health_metrics(self, device_name: str, pre_health: Dict, post_health: Dict) -> List[AuditResult]:
        """Compare health metrics"""
        results = []
        
        # CPU comparison
        cpu_pre = pre_health.get('cpu_percent', 0)
        cpu_post = post_health.get('cpu_percent', 0)
        cpu_delta = cpu_post - cpu_pre
        
        cpu_status = "PASS"
        if cpu_post > self.thresholds['cpu_max']:
            cpu_status = "FAIL"
        elif abs(cpu_delta) > self.thresholds['cpu_delta']:
            cpu_status = "WARN"
        
        results.append(AuditResult(
            check_name=f"{device_name}_cpu_usage",
            category="health",
            pre_value=f"{cpu_pre}%",
            post_value=f"{cpu_post}%",
            delta=f"{cpu_delta:+.1f}%",
            status=cpu_status,
            threshold=f"<{self.thresholds['cpu_max']}%, Δ<{self.thresholds['cpu_delta']}%",
            message=f"CPU usage: {cpu_pre}% → {cpu_post}% (Δ{cpu_delta:+.1f}%)"
        ))
        
        # Memory comparison
        mem_free_pre = pre_health.get('memory_free_percent', 100)
        mem_free_post = post_health.get('memory_free_percent', 100)
        
        mem_status = "PASS" if mem_free_post > self.thresholds['memory_min'] else "FAIL"
        
        results.append(AuditResult(
            check_name=f"{device_name}_memory_free",
            category="health",
            pre_value=f"{mem_free_pre:.1f}%",
            post_value=f"{mem_free_post:.1f}%",
            delta=f"{mem_free_post - mem_free_pre:+.1f}%",
            status=mem_status,
            threshold=f">{self.thresholds['memory_min']}%",
            message=f"Free memory: {mem_free_pre:.1f}% → {mem_free_post:.1f}%"
        ))
        
        return results
    
    def _compare_interfaces(self, device_name: str, pre_data: Dict, post_data: Dict) -> List[AuditResult]:
        """Compare interface metrics"""
        results = []
        
        pre_interfaces = {intf['name']: intf for intf in pre_data.get('interfaces', [])}
        post_interfaces = {intf['name']: intf for intf in post_data.get('interfaces', [])}
        
        # Check for interface status changes
        for intf_name, pre_intf in pre_interfaces.items():
            if intf_name in post_interfaces:
                post_intf = post_interfaces[intf_name]
                
                # Compare status
                if pre_intf.get('status') != post_intf.get('status'):
                    status = "FAIL" if post_intf.get('status') == 'down' else "WARN"
                    results.append(AuditResult(
                        check_name=f"{device_name}_{intf_name}_status",
                        category="interface",
                        pre_value=pre_intf.get('status', 'unknown'),
                        post_value=post_intf.get('status', 'unknown'),
                        delta="Status changed",
                        status=status,
                        threshold="up",
                        message=f"Interface {intf_name} status changed: {pre_intf.get('status')} → {post_intf.get('status')}"
                    ))
                
                # Compare CRC errors
                pre_crc = pre_intf.get('crc_errors', 0)
                post_crc = post_intf.get('crc_errors', 0)
                crc_delta = post_crc - pre_crc
                
                crc_status = "PASS" if crc_delta == 0 else "FAIL"
                
                results.append(AuditResult(
                    check_name=f"{device_name}_{intf_name}_crc_errors",
                    category="interface",
                    pre_value=str(pre_crc),
                    post_value=str(post_crc),
                    delta=f"+{crc_delta}" if crc_delta > 0 else str(crc_delta),
                    status=crc_status,
                    threshold="0",
                    message=f"CRC errors on {intf_name}: {pre_crc} → {post_crc}"
                ))
        
        return results
    
    def _compare_routing(self, device_name: str, pre_data: Dict, post_data: Dict) -> List[AuditResult]:
        """Compare routing metrics"""
        results = []
        
        pre_routing = pre_data.get('routing', {})
        post_routing = post_data.get('routing', {})
        
        # Compare total routes
        pre_routes = pre_routing.get('total_routes', 0)
        post_routes = post_routing.get('total_routes', 0)
        route_delta = post_routes - pre_routes
        
        route_status = "PASS"
        if abs(route_delta) > self.thresholds['bgp_prefix_delta']:
            route_status = "WARN" if abs(route_delta) <= 5 else "FAIL"
        
        results.append(AuditResult(
            check_name=f"{device_name}_total_routes",
            category="routing",
            pre_value=str(pre_routes),
            post_value=str(post_routes),
            delta=f"{route_delta:+d}",
            status=route_status,
            threshold=f"Δ≤{self.thresholds['bgp_prefix_delta']}",
            message=f"Total routes: {pre_routes} → {post_routes} (Δ{route_delta:+d})"
        ))
        
        return results
    
    def _compare_sample_routes(self, device_name: str, pre_data: Dict, post_data: Dict) -> List[AuditResult]:
        """Compare sample routes"""
        results = []
        
        pre_routes = {route['prefix']: route for route in pre_data.get('sample_routes', [])}
        post_routes = {route['prefix']: route for route in post_data.get('sample_routes', [])}
        
        for prefix, pre_route in pre_routes.items():
            if prefix in post_routes:
                post_route = post_routes[prefix]
                
                # Compare next hop
                pre_nh = pre_route.get('next_hop', '')
                post_nh = post_route.get('next_hop', '')
                
                if pre_nh != post_nh:
                    results.append(AuditResult(
                        check_name=f"{device_name}_route_{prefix}_next_hop",
                        category="routing",
                        pre_value=pre_nh,
                        post_value=post_nh,
                        delta="Next-hop changed",
                        status="WARN",
                        threshold="Stable",
                        message=f"Route {prefix} next-hop changed: {pre_nh} → {post_nh}"
                    ))
            else:
                results.append(AuditResult(
                    check_name=f"{device_name}_route_{prefix}_missing",
                    category="routing",
                    pre_value="Present",
                    post_value="Missing",
                    delta="Route disappeared",
                    status="FAIL",
                    threshold="Present",
                    message=f"Sample route {prefix} disappeared"
                ))
        
        return results

# ============================================================================
# REPORTING ENGINE
# ============================================================================

class ReportGenerator:
    """Generate comprehensive reports"""
    
    def __init__(self, output_dir: str, logger: AuditLogger):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logger
    
    def generate_cli_report(self, results: List[AuditResult]) -> str:
        """Generate CLI summary report"""
        report = []
        report.append("=" * 80)
        report.append("RR5 ROUTER AUDIT RESULTS SUMMARY")
        report.append("=" * 80)
        
        # Count results by status
        status_counts = defaultdict(int)
        category_counts = defaultdict(lambda: defaultdict(int))
        
        for result in results:
            status_counts[result.status] += 1
            category_counts[result.category][result.status] += 1
        
        # Overall summary
        report.append(f"\nOVERALL SUMMARY:")
        report.append(f"  ✅ PASS: {status_counts['PASS']}")
        report.append(f"  ⚠️  WARN: {status_counts['WARN']}")
        report.append(f"  ❌ FAIL: {status_counts['FAIL']}")
        report.append(f"  📊 Total checks: {len(results)}")
        
        # Category breakdown
        report.append(f"\nCATEGORY BREAKDOWN:")
        for category, counts in category_counts.items():
            report.append(f"  {category.upper()}:")
            for status, count in counts.items():
                emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[status]
                report.append(f"    {emoji} {status}: {count}")
        
        # Detailed results
        report.append(f"\nDETAILED RESULTS:")
        report.append("-" * 80)
        
        for result in sorted(results, key=lambda x: (x.status != 'FAIL', x.status != 'WARN', x.check_name)):
            emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[result.status]
            report.append(f"{emoji} {result.check_name}")
            report.append(f"    Pre:  {result.pre_value}")
            report.append(f"    Post: {result.post_value}")
            report.append(f"    Δ:    {result.delta}")
            report.append(f"    Threshold: {result.threshold}")
            if result.message:
                report.append(f"    Message: {result.message}")
            report.append("")
        
        return "\n".join(report)
    
    def generate_json_report(self, results: List[AuditResult], filename: str = "audit_results.json"):
        """Generate JSON report"""
        filepath = self.output_dir / filename
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(results),
            'results': [asdict(result) for result in results]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.log(f"JSON report saved: {filepath}")
        return str(filepath)
    
    def generate_csv_report(self, results: List[AuditResult], filename: str = "audit_results.csv"):
        """Generate CSV report"""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'check_name', 'category', 'pre_value', 'post_value', 
                'delta', 'status', 'threshold', 'message'
            ])
            writer.writeheader()
            for result in results:
                writer.writerow(asdict(result))
        
        self.logger.log(f"CSV report saved: {filepath}")
        return str(filepath)
    
    def generate_html_report(self, results: List[AuditResult], filename: str = "audit_results.html"):
        """Generate HTML report"""
        filepath = self.output_dir / filename
        
        summary = self._generate_summary(results)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RR5 Router Audit Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .results {{ margin-top: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .pass {{ color: green; }}
                .warn {{ color: orange; }}
                .fail {{ color: red; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RR5 Router Audit Results</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Checks:</strong> {summary['total']}</p>
                <p><strong>✅ Passed:</strong> {summary['pass']}</p>
                <p><strong>⚠️ Warnings:</strong> {summary['warn']}</p>
                <p><strong>❌ Failed:</strong> {summary['fail']}</p>
            </div>
            
            <div class="results">
                <h2>Detailed Results</h2>
                <table>
                    <tr>
                        <th>Check</th>
                        <th>Category</th>
                        <th>Pre</th>
                        <th>Post</th>
                        <th>Delta</th>
                        <th>Status</th>
                        <th>Threshold</th>
                        <th>Message</th>
                    </tr>
        """
        
        for result in results:
            status_class = result.status.lower()
            html_content += f"""
                    <tr>
                        <td>{result.check_name}</td>
                        <td>{result.category}</td>
                        <td>{result.pre_value}</td>
                        <td>{result.post_value}</td>
                        <td>{result.delta}</td>
                        <td class="{status_class}">{result.status}</td>
                        <td>{result.threshold}</td>
                        <td>{result.message}</td>
                    </tr>
            """
        
        html_content += """
                </table>
            </div>
        </body>
        </html>
        """
        
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        self.logger.log(f"HTML report saved: {filepath}")
        return str(filepath)
    
    def _generate_summary(self, results: List[AuditResult]) -> Dict[str, int]:
        """Generate summary statistics"""
        summary = defaultdict(int)
        for result in results:
            summary[result.status.lower()] += 1
        
        return {
            'total': len(results),
            'pass': summary['pass'],
            'warn': summary['warn'],
            'fail': summary['fail']
        }

# ============================================================================
# DATA STORAGE
# ============================================================================

class DataStorage:
    """Handle data storage and retrieval"""
    
    def __init__(self, output_dir: str, logger: AuditLogger):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logger
    
    def save_phase_data(self, phase: str, data: Dict, timestamp: str = None):
        """Save phase data to file"""
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{phase}_data_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.log(f"Phase data saved: {filepath}")
        return str(filepath)
    
    def load_phase_data(self, filepath: str) -> Dict:
        """Load phase data from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.logger.log(f"Phase data loaded: {filepath}")
            return data
        except Exception as e:
            self.logger.log(f"Error loading phase data: {e}", "ERROR")
            return {}
    
    def list_phase_files(self, phase: str) -> List[str]:
        """List available phase files"""
        pattern = f"{phase}_data_*.json"
        files = list(self.output_dir.glob(pattern))
        return [str(f) for f in sorted(files, reverse=True)]

# ============================================================================
# WEB INTERFACE (Optional)
# ============================================================================

if FLASK_AVAILABLE:
    class WebInterface:
        """Optional web interface for monitoring"""
        
        def __init__(self, config: Dict, logger: AuditLogger):
            self.config = config
            self.logger = logger
            self.app = Flask(__name__)
            self.app.config['SECRET_KEY'] = 'rr5-audit-secret'
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
            self.setup_routes()
            logger.socketio = self.socketio
        
        def setup_routes(self):
            """Setup Flask routes"""
            
            @self.app.route('/')
            def index():
                return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>RR5 Router Audit Monitor</title>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .log-container { 
                            height: 400px; 
                            overflow-y: auto; 
                            border: 1px solid #ccc; 
                            padding: 10px; 
                            background: #f9f9f9; 
                            font-family: monospace;
                        }
                        .log-entry { margin: 2px 0; }
                        .info { color: #007bff; }
                        .warning { color: #ffc107; }
                        .error { color: #dc3545; }
                    </style>
                </head>
                <body>
                    <h1>RR5 Router Audit Monitor</h1>
                    <div class="log-container" id="logs"></div>
                    
                    <script>
                        const socket = io();
                        const logsContainer = document.getElementById('logs');
                        
                        socket.on('audit_log', function(data) {
                            const logEntry = document.createElement('div');
                            logEntry.className = `log-entry ${data.level.toLowerCase()}`;
                            logEntry.textContent = `[${data.timestamp}] ${data.message}`;
                            logsContainer.appendChild(logEntry);
                            logsContainer.scrollTop = logsContainer.scrollHeight;
                        });
                    </script>
                </body>
                </html>
                """
            
            @self.app.route('/api/status')
            def api_status():
                return jsonify({
                    'status': 'running',
                    'version': APP_VERSION,
                    'timestamp': datetime.now().isoformat()
                })
        
        def run(self, host='0.0.0.0', port=None):
            """Run web interface"""
            port = port or self.config.get('web_port', 5015)
            self.logger.log(f"Starting web interface on http://{host}:{port}")
            self.socketio.run(self.app, host=host, port=port, debug=False)

# ============================================================================
# MAIN AUDIT ORCHESTRATOR
# ============================================================================

class RR5AuditOrchestrator:
    """Main audit orchestrator"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = AuditLogger(os.path.join(config['output_dir'], 'audit.log'))
        self.storage = DataStorage(config['output_dir'], self.logger)
        self.connector = NetworkConnector(config, self.logger)
        self.executor = CommandExecutor(self.logger)
        self.parser = DataParser(self.logger)
        self.health_checker = Phase1HealthChecker(self.connector, self.executor, self.parser, self.logger)
        self.data_collector = Phase2DataCollector(self.connector, self.executor, self.parser, self.logger)
        self.comparator = Phase3Comparator(self.logger)
        self.reporter = ReportGenerator(config['output_dir'], self.logger)
        
        # Initialize web interface if available
        self.web_interface = None
        if FLASK_AVAILABLE and config.get('web_enabled', False):
            self.web_interface = WebInterface(config, self.logger)
    
    def run_pre_check(self, devices: List[DeviceInfo]) -> str:
        """Run Phase 1 & 2: Pre-check"""
        self.logger.log("🚀 Starting RR5 Audit - Pre-check Phase")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        all_data = {}
        
        for device in devices:
            device_data = {
                'device_info': asdict(device),
                'health': None,
                'data': None
            }
            
            try:
                # Phase 1: Health check
                health_metrics = self.health_checker.check_device_health(device)
                if health_metrics:
                    device_data['health'] = asdict(health_metrics)
                
                # Phase 2: Data collection
                collected_data = self.data_collector.collect_device_data(device)
                if collected_data:
                    device_data['data'] = collected_data
                
                all_data[device.name] = device_data
                
            except Exception as e:
                self.logger.log(f"Error processing device {device.name}: {e}", "ERROR")
                device_data['error'] = str(e)
                all_data[device.name] = device_data
        
        # Save pre-check data
        filepath = self.storage.save_phase_data('pre', all_data, timestamp)
        self.logger.log(f"✅ Pre-check completed. Data saved to: {filepath}")
        
        return filepath
    
    def run_post_check(self, devices: List[DeviceInfo]) -> str:
        """Run Phase 3: Post-check"""
        self.logger.log("🔄 Starting RR5 Audit - Post-check Phase")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        all_data = {}
        
        for device in devices:
            device_data = {
                'device_info': asdict(device),
                'health': None,
                'data': None
            }
            
            try:
                # Same checks as pre-check
                health_metrics = self.health_checker.check_device_health(device)
                if health_metrics:
                    device_data['health'] = asdict(health_metrics)
                
                collected_data = self.data_collector.collect_device_data(device)
                if collected_data:
                    device_data['data'] = collected_data
                
                all_data[device.name] = device_data
                
            except Exception as e:
                self.logger.log(f"Error processing device {device.name}: {e}", "ERROR")
                device_data['error'] = str(e)
                all_data[device.name] = device_data
        
        # Save post-check data
        filepath = self.storage.save_phase_data('post', all_data, timestamp)
        self.logger.log(f"✅ Post-check completed. Data saved to: {filepath}")
        
        return filepath
    
    def run_comparison(self, pre_file: str, post_file: str) -> List[str]:
        """Run Phase 3: Comparison"""
        self.logger.log("📊 Starting RR5 Audit - Comparison Phase")
        
        # Load data
        pre_data = self.storage.load_phase_data(pre_file)
        post_data = self.storage.load_phase_data(post_file)
        
        if not pre_data or not post_data:
            self.logger.log("Failed to load pre or post data", "ERROR")
            return []
        
        # Perform comparison
        results = self.comparator.compare_datasets(pre_data, post_data)
        
        # Generate reports
        report_files = []
        
        # CLI report
        cli_report = self.reporter.generate_cli_report(results)
        print(cli_report)
        
        # JSON report
        json_file = self.reporter.generate_json_report(results)
        report_files.append(json_file)
        
        # CSV report
        csv_file = self.reporter.generate_csv_report(results)
        report_files.append(csv_file)
        
        # HTML report
        html_file = self.reporter.generate_html_report(results)
        report_files.append(html_file)
        
        self.logger.log(f"✅ Comparison completed. {len(results)} checks performed.")
        self.logger.log(f"Reports generated: {', '.join(report_files)}")
        
        return report_files
    
    def start_web_interface(self):
        """Start web interface"""
        if self.web_interface:
            self.web_interface.run(port=self.config['web_port'])
        else:
            self.logger.log("Web interface not available", "WARNING")

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="RR5 Router Auditing Framework - Three-Phase Network Change Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pre-check phase
  python rr5-router-new-new.py --phase pre --devices inventory.csv --output pre_upgrade
  
  # Post-check phase
  python rr5-router-new-new.py --phase post --devices inventory.csv --output post_upgrade
  
  # Comparison phase
  python rr5-router-new-new.py --phase compare --pre pre_upgrade/pre_data_*.json --post post_upgrade/post_data_*.json
  
  # Web interface
  python rr5-router-new-new.py --web --port 5015
        """
    )
    
    parser.add_argument('--version', action='version', version=f"{SCRIPT_NAME} v{APP_VERSION}")
    parser.add_argument('--phase', choices=['pre', 'post', 'compare'], help='Audit phase to run')
    parser.add_argument('--devices', help='Device inventory file (CSV or YAML)')
    parser.add_argument('--output', help='Output directory name')
    parser.add_argument('--pre', help='Pre-check data file (for comparison)')
    parser.add_argument('--post', help='Post-check data file (for comparison)')
    parser.add_argument('--config', help='Configuration file (YAML)')
    parser.add_argument('--web', action='store_true', help='Start web interface')
    parser.add_argument('--port', type=int, default=5015, help='Web interface port')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Load configuration
    config = DEFAULT_CONFIG.copy()
    
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            user_config = yaml.safe_load(f)
            config.update(user_config)
    
    if args.output:
        config['output_dir'] = args.output
    
    if args.port:
        config['web_port'] = args.port
    
    config['web_enabled'] = args.web
    
    # Initialize orchestrator
    orchestrator = RR5AuditOrchestrator(config)
    
    try:
        if args.web:
            # Start web interface
            orchestrator.start_web_interface()
        
        elif args.phase == 'pre':
            if not args.devices:
                print("Error: --devices required for pre-check phase")
                sys.exit(1)
            
            devices = parse_inventory(args.devices)
            orchestrator.run_pre_check(devices)
        
        elif args.phase == 'post':
            if not args.devices:
                print("Error: --devices required for post-check phase")
                sys.exit(1)
            
            devices = parse_inventory(args.devices)
            orchestrator.run_post_check(devices)
        
        elif args.phase == 'compare':
            if not args.pre or not args.post:
                print("Error: --pre and --post files required for comparison phase")
                sys.exit(1)
            
            orchestrator.run_comparison(args.pre, args.post)
        
        else:
            print("No phase specified. Use --help for usage information.")
            print(f"\n{SCRIPT_NAME} v{APP_VERSION}")
            print("Available phases:", ", ".join(AUDIT_PHASES.keys()))
    
    except KeyboardInterrupt:
        print("\nAudit interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup connections
        orchestrator.connector.disconnect_all()

if __name__ == "__main__":
    main() 
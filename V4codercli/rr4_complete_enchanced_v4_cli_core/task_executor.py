#!/usr/bin/env python3
"""
Task Executor Module for RR4 Complete Enhanced v4 CLI

This module handles Nornir task execution, orchestration, and progress tracking
for network device data collection.

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import os
import sys
import time
import logging
import importlib
import importlib.util
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir.core.filter import F

from .connection_manager import ConnectionManager
from .output_handler import OutputHandler

@dataclass
class TaskResult:
    """Container for task execution results."""
    hostname: str
    task_name: str
    success: bool
    start_time: float
    end_time: float
    duration: float
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CollectionProgress:
    """Track collection progress across devices and tasks."""
    total_devices: int = 0
    completed_devices: int = 0
    failed_devices: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def device_completion_rate(self) -> float:
        """Calculate device completion percentage."""
        if self.total_devices == 0:
            return 0.0
        return (self.completed_devices / self.total_devices) * 100
    
    @property
    def task_completion_rate(self) -> float:
        """Calculate task completion percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time."""
        if not self.start_time:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

class ProgressReporter:
    """Report task execution progress."""
    
    def __init__(self):
        """Initialize progress reporter."""
        self.logger = logging.getLogger('rr4_collector.progress')
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.total_devices = 0
        self.completed_devices = 0
        self.failed_devices = 0
        self.start_time = None
        self.end_time = None
        self._lock = threading.Lock()
        
    def set_total(self, total: int) -> None:
        """Set total number of tasks.
        
        Args:
            total: Total number of tasks
        """
        with self._lock:
            self.total_tasks = total
            
    def increment_completed(self) -> None:
        """Increment completed tasks counter."""
        with self._lock:
            self.completed_tasks += 1
            self._report_progress()
            
    def increment_failed(self) -> None:
        """Increment failed tasks counter."""
        with self._lock:
            self.failed_tasks += 1
            self._report_progress()
            
    def _report_progress(self) -> None:
        """Report current progress."""
        total = self.total_tasks
        completed = self.completed_tasks
        failed = self.failed_tasks
        
        if total > 0:
            percent = (completed + failed) * 100 / total
            self.logger.info(
                f"Progress: {completed + failed}/{total} tasks ({percent:.1f}%) - "
                f"Success: {completed}, Failed: {failed}"
            )
    
    @property
    def device_completion_rate(self) -> float:
        """Calculate device completion percentage."""
        if self.total_devices == 0:
            return 0.0
        return (self.completed_devices / self.total_devices) * 100
    
    @property
    def task_completion_rate(self) -> float:
        """Calculate task completion percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time."""
        if not self.start_time:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

class TaskExecutor:
    """Execute collection tasks on devices."""
    
    def __init__(self, inventory: List[Dict[str, Any]], output_handler: OutputHandler,
                 max_workers: int = 4, timeout: int = 120):
        """Initialize task executor.
        
        Args:
            inventory: List of device dictionaries
            output_handler: Output handler instance
            max_workers: Maximum number of concurrent workers
            timeout: Command timeout in seconds
        """
        self.logger = logging.getLogger('rr4_collector.executor')
        self.inventory = inventory
        self.output_handler = output_handler
        self.max_workers = max_workers
        self.timeout = timeout
        self.progress = ProgressReporter()
        self.progress_callbacks = []  # Add progress callbacks list
        self.progress_lock = threading.Lock()  # Add progress lock
        self.task_results = []  # Add task results list
        
        # Initialize Nornir instance
        self._initialize_nornir()
        
        # Initialize connection manager with jump host config
        self._initialize_connection_manager()
        
    def _initialize_nornir(self):
        """Initialize Nornir from the inventory data."""
        try:
            # Create a temporary Nornir config file
            config_dir = Path("rr4-complete-enchanced-v4-cli-config")
            config_dir.mkdir(exist_ok=True)
            
            nornir_config = {
                "inventory": {
                    "plugin": "SimpleInventory",
                    "options": {
                        "host_file": str(config_dir / "inventory" / "hosts.yaml"),
                        "group_file": str(config_dir / "inventory" / "groups.yaml"),
                        "defaults_file": str(config_dir / "inventory" / "defaults.yaml")
                    }
                },
                "runner": {
                    "plugin": "threaded",
                    "options": {
                        "num_workers": self.max_workers
                    }
                },
                "logging": {
                    "enabled": True,
                    "level": "INFO",
                    "loggers": ["nornir"]
                }
            }
            
            # Initialize Nornir with the config
            self.nr = InitNornir(
                inventory={
                    "plugin": "SimpleInventory",
                    "options": {
                        "host_file": str(config_dir / "inventory" / "hosts.yaml"),
                        "group_file": str(config_dir / "inventory" / "groups.yaml"),
                        "defaults_file": str(config_dir / "inventory" / "defaults.yaml")
                    }
                },
                runner={
                    "plugin": "threaded",
                    "options": {
                        "num_workers": self.max_workers
                    }
                },
                logging={
                    "enabled": True,
                    "level": "INFO",
                    "loggers": ["nornir"]
                }
            )
            
            self.logger.debug(f"Nornir initialized with {len(self.nr.inventory.hosts)} hosts")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Nornir: {e}")
            # Fall back to None - some methods don't require Nornir
            self.nr = None
            
    def _initialize_connection_manager(self):
        """Initialize connection manager with jump host configuration."""
        try:
            # Get jump host configuration from environment
            import os
            jump_host_config = None
            if os.getenv('JUMP_HOST_IP'):
                jump_host_config = {
                    'hostname': os.getenv('JUMP_HOST_IP'),
                    'username': os.getenv('JUMP_HOST_USERNAME'),
                    'password': os.getenv('JUMP_HOST_PASSWORD'),
                    'port': int(os.getenv('JUMP_HOST_PORT', '22'))
                }
                self.logger.debug(f"Connection manager using jump host: {jump_host_config['hostname']}")
            
            self.connection_manager = ConnectionManager(jump_host_config=jump_host_config)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize connection manager: {e}")
            self.connection_manager = None
        
    def add_progress_callback(self, callback):
        """Add a progress callback function.
        
        Args:
            callback: Function to call with progress updates
        """
        self.progress_callbacks.append(callback)
    
    def execute_tasks(self, task_function: Callable, layers: List[str]) -> Dict[str, Any]:
        """Execute tasks on devices.
        
        Args:
            task_function: Function to execute on each device
            layers: List of layers to collect
            
        Returns:
            Dictionary containing execution results
        """
        results = {
            'successful_devices': [],
            'failed_devices': [],
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'errors': []
        }
        
        # Set total tasks
        total_tasks = len(self.inventory) * len(layers)
        self.progress.set_total(total_tasks)
        
        try:
            # Create thread pool
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks for each device and layer
                futures = []
                for device in self.inventory:
                    for layer in layers:
                        future = executor.submit(
                            self._execute_device_task,
                            device,
                            layer,
                            task_function
                        )
                        futures.append(future)
                
                # Process completed tasks
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result['success']:
                            results['successful_devices'].append(result['device'])
                            results['successful_commands'] += result['commands']
                            self.progress.increment_completed()
                        else:
                            results['failed_devices'].append(result['device'])
                            results['failed_commands'] += result['commands']
                            results['errors'].append(result['error'])
                            self.progress.increment_failed()
                            
                        results['total_commands'] += result['commands']
                        
                    except Exception as e:
                        self.logger.error(f"Task execution failed: {e}")
                        results['errors'].append(str(e))
                        self.progress.increment_failed()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            raise
            
    def _execute_device_task(self, device: Dict[str, Any], layer: str,
                           task_function: Callable) -> Dict[str, Any]:
        """Execute task on single device.
        
        Args:
            device: Device dictionary
            layer: Collection layer
            task_function: Task function to execute
            
        Returns:
            Dictionary containing task results
        """
        result = {
            'device': device['hostname'],
            'layer': layer,
            'success': False,
            'commands': 0,
            'error': None
        }
        
        try:
            # Create connection manager
            connection = ConnectionManager(device)
            
            # Connect to device
            if not connection.connect():
                result['error'] = f"Failed to connect to {device['hostname']}"
                return result
            
            try:
                # Execute task
                task_result = task_function(
                    connection=connection,
                    hostname=device['hostname'],
                    layer=layer,
                    output_handler=self.output_handler
                )
                
                # Process result
                result['success'] = task_result.get('success', False)
                result['commands'] = task_result.get('total_commands', 0)
                if not result['success']:
                    result['error'] = task_result.get('error', 'Unknown error')
                    
            finally:
                # Always disconnect
                connection.disconnect()
                
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed for {device['hostname']}: {e}")
            result['error'] = str(e)
            return result
    
    def filter_devices(self, device_filter: Optional[str] = None, 
                      device_list: Optional[List[str]] = None,
                      group_filter: Optional[str] = None) -> None:
        """Filter Nornir inventory based on criteria."""
        if device_list:
            # Filter by specific device list
            self.nr = self.nr.filter(lambda host: host.name in device_list)
        elif device_filter:
            # Filter by device pattern
            self.nr = self.nr.filter(F(name__contains=device_filter))
        elif group_filter:
            # Filter by group
            self.nr = self.nr.filter(F(groups__contains=group_filter))
        
        self.logger.info(f"Filtered to {len(self.nr.inventory.hosts)} devices")
    
    def execute_collection_task(self, task_name: str, task_function: Callable,
                               layer_filter: Optional[List[str]] = None,
                               exclude_layers: Optional[List[str]] = None,
                               **task_kwargs) -> Dict[str, List[TaskResult]]:
        """Execute a collection task across all filtered devices."""
        self.logger.info(f"Starting task execution: {task_name}")
        
        # Initialize progress
        with self.progress_lock:
            self.progress.total_devices = len(self.nr.inventory.hosts)
            self.progress.completed_devices = 0
            self.progress.failed_devices = 0
            self.progress.start_time = time.time()
            self.progress.end_time = None
        
        # Execute task using Nornir
        try:
            nornir_result = self.nr.run(
                task=task_function,
                task_name=task_name,
                layer_filter=layer_filter,
                exclude_layers=exclude_layers,
                **task_kwargs
            )
            
            # Process results
            results = self._process_nornir_results(nornir_result, task_name)
            
            # Update final progress
            with self.progress_lock:
                self.progress.end_time = time.time()
            
            self.logger.info(f"Task execution completed: {task_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {task_name} - {e}")
            with self.progress_lock:
                self.progress.end_time = time.time()
            raise
    
    def _process_nornir_results(self, nornir_result: Any, task_name: str) -> Dict[str, List[TaskResult]]:
        """Process Nornir results and update progress."""
        results = {
            'successful': [],
            'failed': []
        }
        
        for hostname, host_result in nornir_result.items():
            try:
                if host_result.failed:
                    # Handle failed result
                    task_result = TaskResult(
                        hostname=hostname,
                        task_name=task_name,
                        success=False,
                        start_time=time.time(),  # Approximate
                        end_time=time.time(),
                        duration=0.0,
                        error=str(host_result.exception) if host_result.exception else "Unknown error"
                    )
                    results['failed'].append(task_result)
                    
                    with self.progress_lock:
                        self.progress.failed_devices += 1
                else:
                    # Handle successful result
                    task_result = TaskResult(
                        hostname=hostname,
                        task_name=task_name,
                        success=True,
                        start_time=time.time(),  # Approximate
                        end_time=time.time(),
                        duration=0.0,
                        output=host_result.result,
                        metadata=getattr(host_result, 'metadata', {})
                    )
                    results['successful'].append(task_result)
                    
                    with self.progress_lock:
                        self.progress.completed_devices += 1
                
                self.task_results.append(task_result)
                
            except Exception as e:
                self.logger.error(f"Error processing result for {hostname}: {e}")
        
        return results
    
    def execute_connectivity_test(self) -> Dict[str, Any]:
        """Test connectivity to all devices in inventory."""
        self.logger.info("Starting connectivity test")
        
        results = {
            'successful': [],
            'failed': [],
            'total_devices': len(self.inventory),
            'successful_connections': 0,
            'failed_connections': 0,
            'success_rate': 0.0
        }
        
        # Test connectivity to each device
        for device in self.inventory:
            try:
                hostname = device.hostname
                self.logger.debug(f"Testing connectivity to {hostname}")
                
                # Get jump host configuration from environment
                import os
                jump_host_config = None
                if os.getenv('JUMP_HOST_IP'):
                    jump_host_config = {
                        'hostname': os.getenv('JUMP_HOST_IP'),
                        'username': os.getenv('JUMP_HOST_USERNAME'),
                        'password': os.getenv('JUMP_HOST_PASSWORD'),
                        'port': int(os.getenv('JUMP_HOST_PORT', '22'))
                    }
                    self.logger.debug(f"Using jump host: {jump_host_config['hostname']}")
                
                # Create connection manager for this device with jump host config
                connection_manager = ConnectionManager(jump_host_config=jump_host_config)
                
                # Test connection using the test_connectivity method
                result = connection_manager.test_connectivity(
                    hostname=device.management_ip,
                    device_type=device.device_type or 'cisco_ios',
                    username=device.username or 'cisco',
                    password=device.password or 'cisco'
                )
                
                if result.get('success', False):
                    self.logger.debug(f"Successfully connected to {hostname}")
                    results['successful'].append({
                        'hostname': hostname,
                        'ip': device.management_ip,
                        'platform': device.platform or device.device_type
                    })
                    results['successful_connections'] += 1
                else:
                    self.logger.debug(f"Failed to connect to {hostname}: {result.get('error', 'Unknown error')}")
                    results['failed'].append({
                        'hostname': hostname,
                        'ip': device.management_ip,
                        'platform': device.platform or device.device_type,
                        'error': result.get('error', 'Connection failed')
                    })
                    results['failed_connections'] += 1
                    
            except Exception as e:
                hostname = getattr(device, 'hostname', 'unknown')
                self.logger.error(f"Error testing connectivity to {hostname}: {e}")
                results['failed'].append({
                    'hostname': hostname,
                    'ip': getattr(device, 'management_ip', 'unknown'),
                    'platform': getattr(device, 'platform', 'unknown'),
                    'error': str(e)
                })
                results['failed_connections'] += 1
        
        # Calculate success rate
        if results['total_devices'] > 0:
            results['success_rate'] = (results['successful_connections'] / results['total_devices']) * 100
        
        self.logger.info(f"Connectivity test completed: {results['successful_connections']}/{results['total_devices']} successful ({results['success_rate']:.1f}%)")
        
        return results
    
    def execute_layer_collection(self, layers: List[str], exclude_layers: Optional[List[str]] = None,
                                timeout: int = 60) -> Dict[str, Any]:
        """Execute data collection for specified layers."""
        self.logger.info(f"Starting layer collection: {layers}")
        
        def collection_task(task: Task, layer_filter: List[str], exclude_layers: Optional[List[str]],
                           timeout: int, **kwargs) -> Result:
            """Nornir task for layer data collection."""
            hostname = task.host.hostname
            
            # Get connection parameters from Nornir host
            netmiko_options = getattr(task.host.connection_options, 'netmiko', None)
            if netmiko_options:
                device_type = getattr(netmiko_options, 'platform', 'cisco_ios')
                username = getattr(netmiko_options, 'username', 'cisco')
                password = getattr(netmiko_options, 'password', 'cisco')
            else:
                device_type = 'cisco_ios'
                username = 'cisco'
                password = 'cisco'
            
            collection_results = {}
            
            try:
                with self.connection_manager.get_connection(
                    hostname=hostname,
                    device_type=device_type,
                    username=username,
                    password=password,
                    timeout=timeout
                ) as connection:
                    
                    # Execute collection task for each layer
                    for layer in layer_filter:
                        if exclude_layers and layer in exclude_layers:
                            continue
                        
                        try:
                            # Import the layer collector function using the proper path
                            import importlib.util
                            import os
                            
                            # Get the tasks directory path
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            parent_dir = os.path.dirname(current_dir)
                            tasks_dir = os.path.join(parent_dir, 'rr4_complete_enchanced_v4_cli_tasks')
                            
                            # Add tasks directory to Python path if not already there
                            if tasks_dir not in sys.path:
                                sys.path.insert(0, tasks_dir)
                            
                            # Map layer names to actual collector module files and class names
                            collector_mapping = {
                                'health': ('health_collector', 'HealthCollector'),
                                'interfaces': ('interface_collector', 'InterfaceCollector'),
                                'igp': ('igp_collector', 'IGPCollector'),
                                'mpls': ('mpls_collector', 'MPLSCollector'),
                                'bgp': ('bgp_collector', 'BGPCollector'),
                                'vpn': ('vpn_collector', 'VPNCollector'),
                                'static': ('static_route_collector', 'StaticRouteCollector'),
                                'console': ('console_line_collector', 'ConsoleLineCollector')
                            }
                            
                            if layer not in collector_mapping:
                                raise ImportError(f"Unknown layer: {layer}")
                            
                            module_name, class_name = collector_mapping[layer]
                            
                            # Import the specific collector module using absolute import
                            try:
                                            collector_module = importlib.import_module(module_name)
                            except ImportError as e:
                                self.logger.error(f"Failed to import {module_name}: {e}")
                                # Try alternative import path
                                full_module_name = f"rr4_complete_enchanced_v4_cli_tasks.{module_name}"
                                collector_module = importlib.import_module(full_module_name)
                            
                            # Get the collector class
                            collector_class = getattr(collector_module, class_name)
                            
                            # Create collector instance and collect data
                            collector = collector_class()
                            
                            # Get platform with fallback logic
                            platform = task.host.platform
                            if platform is None:
                                # Try to get platform from data or connection options
                                platform = getattr(task.host.data, 'platform', None)
                                if platform is None:
                                    # Extract platform from device_type
                                    if 'cisco_ios' in device_type:
                                        platform = 'ios'
                                    elif 'cisco_iosxe' in device_type:
                                        platform = 'iosxe'
                                    elif 'cisco_iosxr' in device_type:
                                        platform = 'iosxr'
                                    else:
                                        platform = 'ios'  # Default fallback
                            
                            # Debug logging
                            self.logger.debug(f"Collector parameters: hostname={hostname}, platform={platform}, device_type={device_type}")
                            self.logger.debug(f"task.host.platform={task.host.platform}, task.host.data={getattr(task.host, 'data', 'None')}")
                            
                            layer_result = collector.collect_layer_data(
                                connection=connection,
                                hostname=hostname,
                                platform=platform,
                                output_handler=self.output_handler
                            )
                            collection_results[layer] = layer_result
                            
                        except Exception as e:
                            import traceback
                            self.logger.error(f"Layer collection failed for {hostname}/{layer}: {e}")
                            self.logger.error(f"Full traceback: {traceback.format_exc()}")
                            collection_results[layer] = {'error': str(e)}
                
                return Result(host=task.host, result=collection_results)
                
            except Exception as e:
                self.logger.error(f"Connection failed for {hostname}: {e}")
                return Result(host=task.host, result={'error': str(e)}, failed=True)
        
        # Execute layer collection
        results = self.execute_collection_task(
            "layer_collection",
            collection_task,
            layer_filter=layers,
            exclude_layers=exclude_layers,
            timeout=timeout
        )
        
        # Summarize results
        summary = {
            'total_devices': len(self.nr.inventory.hosts),
            'successful_devices': len(results['successful']),
            'failed_devices': len(results['failed']),
            'layers_collected': layers,
            'excluded_layers': exclude_layers or [],
            'success_rate': len(results['successful']) / len(self.nr.inventory.hosts) * 100 if self.nr.inventory.hosts else 0,
            'results': results
        }
        
        return summary
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        with self.progress_lock:
            return {
                'total_devices': self.progress.total_devices,
                'completed_devices': self.progress.completed_devices,
                'failed_devices': self.progress.failed_devices,
                'device_completion_rate': self.progress.device_completion_rate,
                'task_completion_rate': self.progress.task_completion_rate,
                'elapsed_time': self.progress.elapsed_time,
                'is_running': self.progress.end_time is None
            }
    
    def get_detailed_results(self) -> List[TaskResult]:
        """Get detailed task results."""
        return self.task_results.copy()
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self.connection_manager:
                        self.connection_manager.close_all_connections()
            self.logger.info("Task executor cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
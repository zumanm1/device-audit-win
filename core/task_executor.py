#!/usr/bin/env python3
"""
Task Executor Module for RR4 Complete Enhanced v4 CLI

This module handles Nornir task execution, orchestration, and progress tracking
for network device data collection.

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir.core.filter import F

from core.connection_manager import ConnectionManager
from core.output_handler import OutputHandler

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

class TaskExecutor:
    """Execute tasks using Nornir with progress tracking and error handling."""
    
    def __init__(self, nornir_config: Dict[str, Any], connection_manager: ConnectionManager,
                 output_handler: OutputHandler):
        self.connection_manager = connection_manager
        self.output_handler = output_handler
        self.logger = logging.getLogger('rr4_collector.task_executor')
        
        # Initialize Nornir
        self.nr = InitNornir(
            runner=nornir_config.get('runner', {'plugin': 'threaded', 'options': {'num_workers': 15}}),
            inventory=nornir_config.get('inventory', {}),
            logging=nornir_config.get('logging', {'enabled': False})
        )
        
        # Progress tracking
        self.progress = CollectionProgress()
        self.progress_lock = threading.Lock()
        self.task_results: List[TaskResult] = []
        
        # Callbacks for progress updates
        self.progress_callbacks: List[Callable[[CollectionProgress], None]] = []
    
    def add_progress_callback(self, callback: Callable[[CollectionProgress], None]) -> None:
        """Add a callback function for progress updates."""
        self.progress_callbacks.append(callback)
    
    def _update_progress(self, **kwargs) -> None:
        """Update progress and notify callbacks."""
        with self.progress_lock:
            for key, value in kwargs.items():
                if hasattr(self.progress, key):
                    setattr(self.progress, key, value)
            
            # Notify callbacks
            for callback in self.progress_callbacks:
                try:
                    callback(self.progress)
                except Exception as e:
                    self.logger.warning(f"Progress callback error: {e}")
    
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
        """Test connectivity to all filtered devices."""
        self.logger.info("Starting connectivity test")
        
        def connectivity_task(task: Task, **kwargs) -> Result:
            """Nornir task for testing connectivity."""
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
            
            result = self.connection_manager.test_connectivity(
                hostname=hostname,
                device_type=device_type,
                username=username,
                password=password
            )
            
            return Result(host=task.host, result=result)
        
        # Execute connectivity test
        results = self.execute_collection_task("connectivity_test", connectivity_task)
        
        # Summarize results
        summary = {
            'total_devices': len(self.nr.inventory.hosts),
            'successful_connections': len(results['successful']),
            'failed_connections': len(results['failed']),
            'success_rate': len(results['successful']) / len(self.nr.inventory.hosts) * 100 if self.nr.inventory.hosts else 0,
            'results': results
        }
        
        return summary
    
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
                            from tasks import get_layer_collector
                            collector = get_layer_collector(layer)
                            layer_result = collector.collect_layer_data(
                                connection=connection,
                                hostname=hostname,
                                platform=task.host.platform,
                                output_handler=self.output_handler
                            )
                            collection_results[layer] = layer_result
                            
                        except Exception as e:
                            self.logger.error(f"Layer collection failed for {hostname}/{layer}: {e}")
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
            self.connection_manager.close_all_connections()
            self.logger.info("Task executor cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

class ProgressReporter:
    """Report collection progress to console and logs."""
    
    def __init__(self, update_interval: int = 5):
        self.update_interval = update_interval
        self.logger = logging.getLogger('rr4_collector.progress')
        self.last_update = 0
    
    def __call__(self, progress: CollectionProgress) -> None:
        """Progress callback function."""
        current_time = time.time()
        
        # Throttle updates
        if current_time - self.last_update < self.update_interval:
            return
        
        self.last_update = current_time
        
        # Log progress
        self.logger.info(
            f"Progress: {progress.completed_devices}/{progress.total_devices} devices "
            f"({progress.device_completion_rate:.1f}%) - "
            f"Elapsed: {progress.elapsed_time:.1f}s"
        )
        
        # Print to console
        print(f"\rProgress: {progress.completed_devices}/{progress.total_devices} devices "
              f"({progress.device_completion_rate:.1f}%) - "
              f"Elapsed: {progress.elapsed_time:.1f}s", end='', flush=True) 
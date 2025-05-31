#!/usr/bin/env python3
"""
Output Handler Module for RR4 Complete Enhanced v4 CLI

This module handles file output, directory organization, compression,
and metadata generation for collected network data.

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import os
import json
import gzip
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import threading

@dataclass
class FileMetadata:
    """Metadata for output files."""
    filename: str
    original_size: int
    compressed_size: Optional[int] = None
    compression_ratio: Optional[float] = None
    created_timestamp: str = ""
    command: str = ""
    hostname: str = ""
    layer: str = ""
    platform: str = ""
    
    def __post_init__(self):
        if not self.created_timestamp:
            self.created_timestamp = datetime.now().isoformat()

@dataclass
class CollectionMetadata:
    """Metadata for entire collection run."""
    collection_id: str
    start_time: str
    end_time: Optional[str] = None
    total_devices: int = 0
    successful_devices: int = 0
    failed_devices: int = 0
    total_commands: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    total_output_size_bytes: int = 0
    compressed_output_size_bytes: int = 0
    compression_ratio: float = 0.0
    layers_collected: List[str] = None
    
    def __post_init__(self):
        if self.layers_collected is None:
            self.layers_collected = []

class OutputHandler:
    """Handle command outputs and results."""
    
    def __init__(self, base_output_dir: str = "output"):
        """Initialize output handler.
        
        Args:
            base_output_dir: Base directory for outputs
        """
        self.logger = logging.getLogger('rr4_collector.output_handler')
        self.base_output_dir = Path(base_output_dir)
        self.base_dir = self.base_output_dir  # For backward compatibility
        self.current_run_dir = None
        self.collection_metadata = None  # Add collection metadata attribute
        self.collection_id = None  # Add collection ID attribute for collectors
        self._setup_output_directory()
        
    def _setup_output_directory(self) -> None:
        """Set up output directory structure."""
        try:
            # Create run-specific directory
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            self.current_run_dir = self.base_dir / f"collector-run-{timestamp}"
            self.current_run_dir.mkdir(parents=True, exist_ok=True)
            
            # Create logs directory
            (self.current_run_dir / "logs").mkdir(exist_ok=True)
            
            self.logger.info(f"Created output directory: {self.current_run_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup output directory: {e}")
            raise
    
    def create_run_directory(self) -> str:
        """Create and return run directory ID.
        
        Returns:
            Run directory ID string
        """
        if self.current_run_dir:
            # Set collection_id to the run directory name
            self.collection_id = self.current_run_dir.name
            # Initialize collection_metadata if not already done
            if not self.collection_metadata:
                self.collection_metadata = CollectionMetadata(
                    collection_id=self.collection_id,
                    start_time=datetime.now().isoformat()
                )
            return self.current_run_dir.name
        else:
            # If not already created, create it now
            self._setup_output_directory()
            self.collection_id = self.current_run_dir.name
            # Initialize collection_metadata
            if not self.collection_metadata:
                self.collection_metadata = CollectionMetadata(
                    collection_id=self.collection_id,
                    start_time=datetime.now().isoformat()
                )
            return self.current_run_dir.name
    
    def create_device_directory_structure(self, hostname: str, layer: str) -> Path:
        """Create device directory structure for a collection layer.
        
        Args:
            hostname: Device hostname
            layer: Collection layer name
            
        Returns:
            Path to the device layer directory
        """
        return self.get_device_directory(hostname, layer)
    
    def get_device_directory(self, hostname: str, layer: str) -> Path:
        """Get device-specific output directory.
        
        Args:
            hostname: Device hostname
            layer: Collection layer name
            
        Returns:
            Path to device directory
        """
        try:
            device_dir = self.current_run_dir / hostname / layer
            device_dir.mkdir(parents=True, exist_ok=True)
            return device_dir
                
        except Exception as e:
            self.logger.error(f"Failed to create device directory for {hostname}: {e}")
            raise
            
    def save_command_output(self, hostname: str, layer: str, command: str, 
                          output: str) -> None:
        """Save command output to file.
        
        Args:
            hostname: Device hostname
            layer: Collection layer name
            command: Command that was executed
            output: Command output
        """
        try:
            device_dir = self.get_device_directory(hostname, layer)
            
            # Convert command to filename
            filename = command.replace(' ', '_').replace('|', '__pipe__') + '.txt'
            output_file = device_dir / filename
            
            # Save output
            with open(output_file, 'w') as f:
                f.write(output)
                
            self.logger.debug(f"Saved output for command '{command}' to {output_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to save command output: {e}")
            raise
            
    def save_parsed_output(self, hostname: str, layer: str, command: str, 
                          parsed_data: Dict[str, Any]) -> None:
        """Save parsed command output to JSON file.
        
        Args:
            hostname: Device hostname
            layer: Collection layer name
            command: Command that was executed
            parsed_data: Parsed command output data
        """
        try:
            device_dir = self.get_device_directory(hostname, layer)
            
            # Convert command to filename
            filename = command.replace(' ', '_').replace('|', '__pipe__') + '.json'
            output_file = device_dir / filename
            
            # Save parsed data
            with open(output_file, 'w') as f:
                json.dump(parsed_data, f, indent=2)
                
            self.logger.debug(f"Saved parsed output for command '{command}' to {output_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to save parsed output: {e}")
            raise
            
    def save_collection_results(self, hostname: str, layer: str, 
                              results: Dict[str, Any]) -> None:
        """Save collection results to JSON file.
        
        Args:
            hostname: Device hostname
            layer: Collection layer name
            results: Collection results dictionary
        """
        try:
            device_dir = self.get_device_directory(hostname, layer)
            results_file = device_dir / "collection_results.json"
            
            # Add metadata
            results['metadata'] = {
                'hostname': hostname,
                'layer': layer,
                'timestamp': datetime.now().isoformat(),
                'output_dir': str(device_dir)
            }
            
            # Save results
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
                
            self.logger.info(f"Saved collection results for {hostname} to {results_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save collection results: {e}")
            raise
            
    def save_error_log(self, hostname: str, error: str) -> None:
        """Save error message to log file.
        
        Args:
            hostname: Device hostname
            error: Error message
        """
        try:
            log_dir = self.current_run_dir / "logs"
            error_file = log_dir / f"{hostname}_errors.log"
            
            # Append error with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(error_file, 'a') as f:
                f.write(f"[{timestamp}] {error}\n")
                
            self.logger.debug(f"Saved error log for {hostname} to {error_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save error log: {e}")
            raise
            
    def get_run_summary(self) -> Dict[str, Any]:
        """Get summary of current collection run.
        
        Returns:
            Dictionary containing run summary
        """
        try:
            summary = {
                'run_directory': str(self.current_run_dir),
                'start_time': self.current_run_dir.name.split('-')[1],
                'devices': [],
                'layers': set(),
                'total_commands': 0,
                'errors': 0
            }
            
            # Process device directories
            for device_dir in self.current_run_dir.glob('*'):
                if device_dir.is_dir() and device_dir.name != 'logs':
                    device_summary = {
                        'hostname': device_dir.name,
                        'layers': [],
                        'commands': 0,
                        'errors': 0
                    }
                    
                    # Process layer directories
                    for layer_dir in device_dir.glob('*'):
                        if layer_dir.is_dir():
                            layer = layer_dir.name
                            device_summary['layers'].append(layer)
                            summary['layers'].add(layer)
                            
                            # Count command outputs
                            cmd_files = list(layer_dir.glob('*.txt'))
                            device_summary['commands'] += len(cmd_files)
                            summary['total_commands'] += len(cmd_files)
                            
                    # Check for errors
                    error_file = self.current_run_dir / 'logs' / f"{device_dir.name}_errors.log"
                    if error_file.exists():
                        with open(error_file) as f:
                            errors = f.readlines()
                            device_summary['errors'] = len(errors)
                            summary['errors'] += len(errors)
                            
                    summary['devices'].append(device_summary)
                    
            return summary
                        
        except Exception as e:
            self.logger.error(f"Failed to generate run summary: {e}")
            raise

class FileManager:
    """Utility class for file operations."""
    
    @staticmethod
    def get_file_size_human(size_bytes: int) -> str:
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio."""
        if original_size == 0:
            return 0.0
        return (original_size - compressed_size) / original_size
    
    @staticmethod
    def validate_output_directory(directory: Path) -> bool:
        """Validate output directory exists and is writable."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = directory / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            
            return True
            
        except Exception:
            return False 
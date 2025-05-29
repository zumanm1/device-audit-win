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
    """Handle file output, compression, and metadata management."""
    
    def __init__(self, base_output_dir: str = "output", compression_threshold_mb: float = 1.0):
        self.base_output_dir = Path(base_output_dir)
        self.compression_threshold_bytes = int(compression_threshold_mb * 1024 * 1024)
        self.logger = logging.getLogger('rr4_collector.output_handler')
        
        # Thread safety
        self.file_lock = threading.Lock()
        
        # Metadata tracking
        self.file_metadata: List[FileMetadata] = []
        self.collection_metadata: Optional[CollectionMetadata] = None
        
        # Create base directory
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_collection_run_directory(self) -> Path:
        """Create a new collection run directory with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_id = f"collector-run-{timestamp}"
        run_dir = self.base_output_dir / run_id
        
        try:
            run_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize collection metadata
            self.collection_metadata = CollectionMetadata(
                collection_id=run_id,
                start_time=datetime.now().isoformat()
            )
            
            self.logger.info(f"Created collection run directory: {run_dir}")
            return run_dir
            
        except Exception as e:
            self.logger.error(f"Failed to create run directory: {e}")
            raise
    
    def create_run_directory(self) -> str:
        """Create a new collection run directory and return the run ID."""
        run_dir = self.create_collection_run_directory()
        return run_dir.name
    
    def create_device_directory_structure(self, run_dir: Path, hostname: str) -> Dict[str, Path]:
        """Create directory structure for a device."""
        device_dir = run_dir / hostname
        
        # Layer directories
        layer_dirs = {
            'health': device_dir / 'health',
            'interfaces': device_dir / 'interfaces',
            'igp': device_dir / 'igp',
            'mpls': device_dir / 'mpls',
            'bgp': device_dir / 'bgp',
            'vpn': device_dir / 'vpn',
            'static': device_dir / 'static'
        }
        
        # Create all directories
        for layer_dir in layer_dirs.values():
            layer_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.debug(f"Created device directory structure for {hostname}")
        return layer_dirs
    
    def save_command_output(self, output_dir: Path, command: str, output: str,
                           hostname: str, layer: str, platform: str) -> Dict[str, Any]:
        """Save command output to file with optional compression."""
        # Generate safe filename from command
        safe_command = self._sanitize_filename(command)
        base_filename = f"{safe_command}.txt"
        file_path = output_dir / base_filename
        
        result = {
            'filename': base_filename,
            'file_path': str(file_path),
            'original_size': 0,
            'compressed': False,
            'compression_ratio': 0.0
        }
        
        try:
            with self.file_lock:
                # Write raw output
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                
                original_size = file_path.stat().st_size
                result['original_size'] = original_size
                
                # Compress if file is large enough
                compressed_path = None
                if original_size > self.compression_threshold_bytes:
                    compressed_path = self._compress_file(file_path)
                    if compressed_path:
                        compressed_size = compressed_path.stat().st_size
                        result['compressed'] = True
                        result['compressed_size'] = compressed_size
                        result['compression_ratio'] = (original_size - compressed_size) / original_size
                        result['compressed_file'] = str(compressed_path)
                
                # Create metadata
                metadata = FileMetadata(
                    filename=base_filename,
                    original_size=original_size,
                    compressed_size=result.get('compressed_size'),
                    compression_ratio=result.get('compression_ratio'),
                    command=command,
                    hostname=hostname,
                    layer=layer,
                    platform=platform
                )
                
                self.file_metadata.append(metadata)
                
                self.logger.debug(f"Saved command output: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to save command output: {e}")
            result['error'] = str(e)
        
        return result
    
    def save_parsed_output(self, output_dir: Path, command: str, parsed_data: Dict[str, Any],
                          hostname: str, layer: str, platform: str) -> Dict[str, Any]:
        """Save parsed/structured output to JSON file."""
        safe_command = self._sanitize_filename(command)
        json_filename = f"{safe_command}.json"
        json_path = output_dir / json_filename
        
        result = {
            'filename': json_filename,
            'file_path': str(json_path),
            'size': 0
        }
        
        try:
            with self.file_lock:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=2, default=str)
                
                result['size'] = json_path.stat().st_size
                self.logger.debug(f"Saved parsed output: {json_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to save parsed output: {e}")
            result['error'] = str(e)
        
        return result
    
    def _compress_file(self, file_path: Path) -> Optional[Path]:
        """Compress a file using gzip."""
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            self.logger.debug(f"Compressed file: {file_path} -> {compressed_path}")
            return compressed_path
            
        except Exception as e:
            self.logger.error(f"Failed to compress file {file_path}: {e}")
            return None
    
    def _sanitize_filename(self, command: str) -> str:
        """Convert command to safe filename."""
        # Replace problematic characters
        safe_name = command.replace(' ', '_')
        safe_name = safe_name.replace('|', '_pipe_')
        safe_name = safe_name.replace('>', '_gt_')
        safe_name = safe_name.replace('<', '_lt_')
        safe_name = safe_name.replace('/', '_slash_')
        safe_name = safe_name.replace('\\', '_backslash_')
        safe_name = safe_name.replace(':', '_colon_')
        safe_name = safe_name.replace('*', '_star_')
        safe_name = safe_name.replace('?', '_question_')
        safe_name = safe_name.replace('"', '_quote_')
        
        # Limit length
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        
        return safe_name
    
    def save_collection_metadata(self, run_dir: Path) -> None:
        """Save collection metadata to JSON file."""
        if not self.collection_metadata:
            self.logger.warning("No collection metadata to save")
            return
        
        # Update end time
        self.collection_metadata.end_time = datetime.now().isoformat()
        
        # Calculate totals
        total_original_size = sum(fm.original_size for fm in self.file_metadata)
        total_compressed_size = sum(fm.compressed_size or fm.original_size for fm in self.file_metadata)
        
        self.collection_metadata.total_output_size_bytes = total_original_size
        self.collection_metadata.compressed_output_size_bytes = total_compressed_size
        
        if total_original_size > 0:
            self.collection_metadata.compression_ratio = (
                total_original_size - total_compressed_size
            ) / total_original_size
        
        # Save metadata
        metadata_file = run_dir / 'collection_metadata.json'
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.collection_metadata), f, indent=2)
            
            self.logger.info(f"Saved collection metadata: {metadata_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save collection metadata: {e}")
    
    def save_file_metadata(self, run_dir: Path) -> None:
        """Save file metadata to JSON file."""
        metadata_file = run_dir / 'file_metadata.json'
        
        try:
            metadata_list = [asdict(fm) for fm in self.file_metadata]
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_list, f, indent=2)
            
            self.logger.info(f"Saved file metadata: {metadata_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save file metadata: {e}")
    
    def save_collection_summary(self, run_dir: Path, summary_data: Dict[str, Any]) -> None:
        """Save collection summary to JSON file."""
        summary_file = run_dir / 'collection_summary.json'
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved collection summary: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save collection summary: {e}")
    
    def save_collection_report(self, report: Dict[str, Any]) -> None:
        """Save collection report to JSON file."""
        if not self.collection_metadata:
            self.logger.warning("No collection metadata available for report")
            return
        
        # Determine run directory from collection metadata
        run_id = self.collection_metadata.collection_id
        run_dir = self.base_output_dir / run_id
        
        if not run_dir.exists():
            self.logger.warning(f"Run directory not found: {run_dir}")
            return
        
        report_file = run_dir / 'collection_report.json'
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Saved collection report: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save collection report: {e}")
    
    def update_collection_stats(self, **kwargs) -> None:
        """Update collection metadata statistics."""
        if not self.collection_metadata:
            return
        
        for key, value in kwargs.items():
            if hasattr(self.collection_metadata, key):
                setattr(self.collection_metadata, key, value)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get current collection statistics."""
        if not self.collection_metadata:
            return {}
        
        return {
            'collection_id': self.collection_metadata.collection_id,
            'total_devices': self.collection_metadata.total_devices,
            'successful_devices': self.collection_metadata.successful_devices,
            'failed_devices': self.collection_metadata.failed_devices,
            'total_commands': self.collection_metadata.total_commands,
            'successful_commands': self.collection_metadata.successful_commands,
            'failed_commands': self.collection_metadata.failed_commands,
            'total_files': len(self.file_metadata),
            'total_output_size_mb': self.collection_metadata.total_output_size_bytes / (1024 * 1024),
            'compressed_output_size_mb': self.collection_metadata.compressed_output_size_bytes / (1024 * 1024),
            'compression_ratio': self.collection_metadata.compression_ratio
        }
    
    def cleanup_old_collections(self, keep_days: int = 30) -> None:
        """Clean up old collection directories."""
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
        
        try:
            for item in self.base_output_dir.iterdir():
                if item.is_dir() and item.name.startswith('collector-run-'):
                    if item.stat().st_mtime < cutoff_time:
                        shutil.rmtree(item)
                        self.logger.info(f"Cleaned up old collection: {item}")
                        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

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
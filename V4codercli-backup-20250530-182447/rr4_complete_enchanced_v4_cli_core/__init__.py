"""
Core package for RR4 Complete Enhanced v4 CLI.

This package contains core functionality for:
- Connection management
- Data parsing
- Output handling
- Task execution
"""

__version__ = '1.0.0'

from .inventory_loader import InventoryLoader
from .connection_manager import ConnectionManager
from .task_executor import TaskExecutor, ProgressReporter
from .output_handler import OutputHandler
from .data_parser import DataParser

__all__ = [
    'InventoryLoader',
    'ConnectionManager',
    'TaskExecutor',
    'ProgressReporter',
    'OutputHandler',
    'DataParser'
]

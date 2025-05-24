#!/usr/bin/env python3
"""
Test configuration and fixtures for NetAuditPro Router Auditing Application
"""

import pytest
import os
import sys
import tempfile
import shutil
import importlib.util
from unittest.mock import Mock, patch, MagicMock
import json
import yaml
from datetime import datetime

# Add the parent directory to the path so we can import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main application module using importlib to handle hyphenated filename
def load_app_module():
    """Load the main application module"""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    module_path = os.path.join(parent_dir, "rr4-router-complete-enhanced-v2.py")
    
    if os.path.exists(module_path):
        spec = importlib.util.spec_from_file_location("app_module", module_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        return app_module
    else:
        raise ImportError(f"Could not find main application file at {module_path}")

# Load the module once
try:
    app_module = load_app_module()
except ImportError as e:
    print(f"Warning: Could not load main application module: {e}")
    app_module = None

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    if app_module is None:
        pytest.skip("Main application module not available")
    
    # Create a temporary directory for test files
    test_dir = tempfile.mkdtemp()
    
    # Configure the app for testing
    app_module.app.config['TESTING'] = True
    app_module.app.config['UPLOAD_FOLDER'] = os.path.join(test_dir, 'inventories')
    app_module.app.config['WTF_CSRF_ENABLED'] = False
    
    # Create necessary directories
    os.makedirs(app_module.app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app_module.app.app_context():
        yield app_module.app
    
    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def mock_ssh_client():
    """Mock SSH client for testing network operations."""
    mock_client = Mock()
    mock_client.connect.return_value = None
    mock_client.exec_command.return_value = (Mock(), Mock(), Mock())
    mock_client.close.return_value = None
    return mock_client

@pytest.fixture
def mock_paramiko_client():
    """Mock Paramiko SSH client."""
    with patch('paramiko.SSHClient') as mock_client:
        instance = mock_client.return_value
        instance.connect.return_value = None
        instance.exec_command.return_value = (Mock(), Mock(), Mock())
        instance.close.return_value = None
        yield instance

@pytest.fixture
def sample_inventory_data():
    """Sample inventory data for testing."""
    return {
        "routers": {
            "R1": {
                "ip": "192.168.1.1",
                "device_type": "cisco_ios",
                "description": "Test Router 1"
            },
            "R2": {
                "ip": "192.168.1.2", 
                "device_type": "cisco_ios",
                "description": "Test Router 2"
            }
        }
    }

@pytest.fixture
def sample_csv_inventory_data():
    """Sample CSV inventory data for testing."""
    return {
        "headers": ["hostname", "ip", "device_type", "description"],
        "data": [
            {
                "hostname": "R1",
                "ip": "192.168.1.1",
                "device_type": "cisco_ios", 
                "description": "Test Router 1"
            },
            {
                "hostname": "R2",
                "ip": "192.168.1.2",
                "device_type": "cisco_ios",
                "description": "Test Router 2"
            }
        ]
    }

@pytest.fixture
def sample_app_config():
    """Sample application configuration for testing."""
    return {
        "JUMP_HOST": "192.168.1.100",
        "JUMP_USERNAME": "testuser",
        "JUMP_PASSWORD": "testpass",
        "DEVICE_USERNAME": "admin",
        "DEVICE_PASSWORD": "admin123",
        "DEVICE_ENABLE": "enable123",
        "PORT": "5007"
    }

@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_ping_success():
    """Mock successful ping operations."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        yield mock_run

@pytest.fixture
def mock_ping_failure():
    """Mock failed ping operations."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        yield mock_run

@pytest.fixture
def mock_socketio():
    """Mock SocketIO for testing real-time features."""
    with patch.object(app_module, 'socketio') as mock_sio:
        yield mock_sio

@pytest.fixture
def reset_global_state():
    """Reset global state variables before each test."""
    # Store original values
    original_values = {
        'ui_logs': app_module.ui_logs.copy(),
        'APP_CONFIG': app_module.APP_CONFIG.copy(),
        'DEVICE_STATUS_TRACKING': getattr(app_module, 'DEVICE_STATUS_TRACKING', {}).copy(),
        'DOWN_DEVICES': getattr(app_module, 'DOWN_DEVICES', {}).copy(),
        'DEVICE_COMMAND_LOGS': getattr(app_module, 'DEVICE_COMMAND_LOGS', {}).copy(),
    }
    
    # Clear global state
    app_module.ui_logs.clear()
    app_module.APP_CONFIG.clear()
    if hasattr(app_module, 'DEVICE_STATUS_TRACKING'):
        app_module.DEVICE_STATUS_TRACKING.clear()
    if hasattr(app_module, 'DOWN_DEVICES'):
        app_module.DOWN_DEVICES.clear()
    if hasattr(app_module, 'DEVICE_COMMAND_LOGS'):
        app_module.DEVICE_COMMAND_LOGS.clear()
    
    yield
    
    # Restore original values
    app_module.ui_logs.clear()
    app_module.ui_logs.extend(original_values['ui_logs'])
    app_module.APP_CONFIG.clear()
    app_module.APP_CONFIG.update(original_values['APP_CONFIG'])
    if hasattr(app_module, 'DEVICE_STATUS_TRACKING'):
        app_module.DEVICE_STATUS_TRACKING.clear()
        app_module.DEVICE_STATUS_TRACKING.update(original_values['DEVICE_STATUS_TRACKING'])
    if hasattr(app_module, 'DOWN_DEVICES'):
        app_module.DOWN_DEVICES.clear()
        app_module.DOWN_DEVICES.update(original_values['DOWN_DEVICES'])
    if hasattr(app_module, 'DEVICE_COMMAND_LOGS'):
        app_module.DEVICE_COMMAND_LOGS.clear()
        app_module.DEVICE_COMMAND_LOGS.update(original_values['DEVICE_COMMAND_LOGS'])

@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    with patch('builtins.open', create=True) as mock_open, \
         patch('os.path.exists') as mock_exists, \
         patch('os.makedirs') as mock_makedirs:
        mock_exists.return_value = True
        yield {
            'open': mock_open,
            'exists': mock_exists,
            'makedirs': mock_makedirs
        }

@pytest.fixture
def sample_command_output():
    """Sample command output for testing."""
    return {
        "show_version": "Cisco IOS Software, Version 15.1(4)M12a",
        "show_ip_interface_brief": "Interface                  IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0         192.168.1.1     YES NVRAM  up                    up",
        "show_running_config": "Building configuration...\n\nCurrent configuration : 1234 bytes\n!\nversion 15.1\n!"
    } 
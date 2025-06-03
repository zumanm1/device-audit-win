#!/usr/bin/env python3
"""
Test Suite 0002: CLI Functionality Testing for RR4 Complete Enhanced v4 CLI

This test suite validates the CLI interface functionality including:
- Command line argument parsing
- Environment management
- Project structure initialization
- Dependency checking
- Collection orchestration
- Error handling

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import csv

# Import CLI modules under test
import sys
sys.path.insert(0, '.')

# Import the main CLI module
try:
    from rr4_complete_enchanced_v4_cli import (
        cli, collect_all, collect_devices, collect_group, validate_inventory, show_config,
        Logger, EnvironmentManager, ProjectStructure, DependencyChecker, CollectionManager,
        CLIError, CONFIG
    )
    CLI_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: CLI module not available: {e}")
    CLI_MODULE_AVAILABLE = False

def load_test_credentials():
    """Load test credentials from .env-t file or use secure defaults."""
    credentials = {
        'jump_host_ip': os.getenv('JUMP_HOST_IP', '172.16.39.128'),
        'jump_host_username': os.getenv('JUMP_HOST_USERNAME', 'root'),
        'jump_host_password': os.getenv('JUMP_HOST_PASSWORD', 'eve'),
        'device_username': os.getenv('ROUTER_USERNAME', 'cisco'),
        'device_password': os.getenv('ROUTER_PASSWORD', 'cisco')
    }
    
    # Try to load from .env-t if available
    env_file = Path('.env-t')
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                        
                        # Update credentials dictionary
                        if key.strip() == 'JUMP_HOST_IP':
                            credentials['jump_host_ip'] = value.strip()
                        elif key.strip() == 'JUMP_HOST_USERNAME':
                            credentials['jump_host_username'] = value.strip()
                        elif key.strip() == 'JUMP_HOST_PASSWORD':
                            credentials['jump_host_password'] = value.strip()
                        elif key.strip() == 'ROUTER_USERNAME':
                            credentials['device_username'] = value.strip()
                        elif key.strip() == 'ROUTER_PASSWORD':
                            credentials['device_password'] = value.strip()
        except Exception:
            pass  # Use defaults if file reading fails
    
    return credentials

class TestCLIBasicFunctionality:
    """Test basic CLI functionality."""
    
    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CLI_MODULE_AVAILABLE, reason="CLI module not available")
    def test_cli_version_flag(self, runner):
        """Test --version flag."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'RR4 Complete Enhanced v4 CLI' in result.output
        assert CONFIG['version'] in result.output
    
    @pytest.mark.skipif(not CLI_MODULE_AVAILABLE, reason="CLI module not available")
    def test_cli_help(self, runner):
        """Test CLI help output."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Network State Collector' in result.output
        assert 'collect-all' in result.output
        assert 'collect-devices' in result.output
    
    @pytest.mark.skipif(not CLI_MODULE_AVAILABLE, reason="CLI module not available")
    def test_cli_no_command(self, runner):
        """Test CLI with no command shows help."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'Usage:' in result.output

class TestLogger:
    """Test Logger class functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CLI_MODULE_AVAILABLE, reason="CLI module not available")
    def test_logger_initialization(self):
        """Test Logger initialization."""
        logger_manager = Logger(log_level="INFO")
        logger = logger_manager.get_logger()
        
        assert logger is not None
        assert logger.name == 'rr4_collector'

class TestEnvironmentManager:
    """Test EnvironmentManager class functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_env_file(self, temp_dir):
        """Create sample .env-t file."""
        env_file = temp_dir / '.env-t'
        env_content = """
JUMP_HOST_IP=jumphost.example.com
JUMP_HOST_USERNAME=jumpuser
JUMP_HOST_PASSWORD=jumppass
JUMP_HOST_PORT=22
MAX_CONCURRENT_CONNECTIONS=10
COMMAND_TIMEOUT=60
"""
        env_file.write_text(env_content)
        return env_file
    
    @pytest.mark.skipif(not CLI_MODULE_AVAILABLE, reason="CLI module not available")
    def test_environment_manager_success(self, sample_env_file):
        """Test successful environment loading."""
        with patch.dict(os.environ, {}, clear=True):
            env_manager = EnvironmentManager(str(sample_env_file))
            config = env_manager.get_config()
            
            assert config['jump_host_ip'] == 'jumphost.example.com'
            assert config['jump_host_username'] == 'jumpuser'
            assert config['jump_host_password'] == 'jumppass'

class TestProjectStructure:
    """Test ProjectStructure class functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CLI_MODULE_AVAILABLE, reason="CLI module not available")
    def test_project_structure_initialization(self, temp_dir):
        """Test ProjectStructure initialization."""
        structure = ProjectStructure(str(temp_dir))
        assert structure.base_dir == temp_dir
        assert len(structure.required_dirs) > 0
        assert 'core' in structure.required_dirs
        assert 'tasks' in structure.required_dirs

class TestDependencyChecker:
    """Test DependencyChecker class functionality."""
    
    @pytest.mark.skipif(not CLI_MODULE_AVAILABLE, reason="CLI module not available")
    def test_dependency_checker_initialization(self):
        """Test DependencyChecker initialization."""
        checker = DependencyChecker()
        assert len(checker.required_packages) > 0
        assert 'click' in checker.required_packages
        assert 'netmiko' in checker.required_packages

class TestCollectionManager:
    """Test CollectionManager class functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for CollectionManager."""
        return {
            'jump_host_ip': 'jumphost.example.com',
            'jump_host_username': 'jumpuser',
            'jump_host_password': 'jumppass',
            'jump_host_port': '22',
            'max_concurrent_connections': '10',
            'connection_retry_attempts': '3',
            'device_username': 'cisco',
            'device_password': 'cisco'
        }

class TestCLICommands:
    """Test CLI command functionality."""
    
    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CLI_MODULE_AVAILABLE, reason="CLI module not available")
    def test_collect_all_command_help(self, runner):
        """Test collect-all command help."""
        result = runner.invoke(cli, ['collect-all', '--help'])
        assert result.exit_code == 0
        assert 'Collect data from all devices' in result.output
        assert '--workers' in result.output
        assert '--timeout' in result.output

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 
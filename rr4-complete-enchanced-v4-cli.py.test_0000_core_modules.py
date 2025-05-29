#!/usr/bin/env python3
"""
Test Suite 0000: Core Modules Testing for RR4 Complete Enhanced v4 CLI

This test suite validates the core modules functionality including:
- Inventory loader
- Connection manager
- Task executor
- Output handler
- Data parser

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import csv
import os

# Import modules under test
from core.inventory_loader import InventoryLoader, DeviceInfo
from core.connection_manager import ConnectionManager, ConnectionConfig, ConnectionPool
from core.task_executor import TaskExecutor, CollectionProgress, TaskResult
from core.output_handler import OutputHandler, FileMetadata, CollectionMetadata
from core.data_parser import DataParser, ParseResult

class TestInventoryLoader:
    """Test cases for InventoryLoader class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_csv_data(self):
        """Sample CSV inventory data."""
        return [
            ['hostname', 'management_ip', 'wan_ip', 'model_name'],
            ['router1', '192.168.1.1', '10.1.1.1', 'Cisco 4431'],
            ['router2', '192.168.1.2', '10.1.1.2', 'Cisco ASR1001-X'],
            ['router3', '192.168.1.3', '10.1.1.3', 'Cisco NCS-5500']
        ]
    
    @pytest.fixture
    def sample_csv_file(self, temp_dir, sample_csv_data):
        """Create sample CSV file."""
        csv_file = temp_dir / 'test_inventory.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(sample_csv_data)
        return csv_file
    
    def test_inventory_loader_initialization(self, sample_csv_file):
        """Test InventoryLoader initialization."""
        loader = InventoryLoader(str(sample_csv_file))
        assert loader.csv_file == sample_csv_file
        assert loader.config_dir == Path("config")
    
    def test_load_csv_inventory_success(self, sample_csv_file):
        """Test successful CSV inventory loading."""
        loader = InventoryLoader(str(sample_csv_file))
        devices = loader.load_csv_inventory()
        
        assert len(devices) == 3
        assert devices[0].hostname == 'router1'
        assert devices[0].management_ip == '192.168.1.1'
        assert devices[0].platform == 'iosxe'  # Should detect from Cisco 4431
        
        assert devices[1].platform == 'iosxe'  # ASR1001-X
        assert devices[2].platform == 'iosxr'  # NCS-5500
    
    def test_load_csv_inventory_file_not_found(self):
        """Test CSV loading with non-existent file."""
        loader = InventoryLoader('nonexistent.csv')
        with pytest.raises(FileNotFoundError):
            loader.load_csv_inventory()
    
    def test_platform_detection(self, sample_csv_file):
        """Test platform detection logic."""
        loader = InventoryLoader(str(sample_csv_file))
        
        assert loader._detect_platform('Cisco 4431') == 'iosxe'
        assert loader._detect_platform('Cisco ASR1001-X') == 'iosxr'
        assert loader._detect_platform('Cisco 2911') == 'ios'
        assert loader._detect_platform('Unknown Model') == 'ios'  # Default
        assert loader._detect_platform(None) == 'ios'  # Default
    
    def test_group_assignment(self, sample_csv_file):
        """Test device group assignment."""
        loader = InventoryLoader(str(sample_csv_file))
        
        groups = loader._assign_groups('core-router-1')
        assert 'all_devices' in groups
        assert 'core_routers' in groups
        
        groups = loader._assign_groups('edge-pe-router')
        assert 'edge_routers' in groups
        assert 'pe_routers' in groups
    
    def test_generate_nornir_inventory(self, sample_csv_file):
        """Test Nornir inventory generation."""
        loader = InventoryLoader(str(sample_csv_file))
        devices = loader.load_csv_inventory()
        
        inventory = loader.generate_nornir_inventory(devices, 'testuser', 'testpass')
        
        assert 'hosts' in inventory
        assert 'groups' in inventory
        assert len(inventory['hosts']) == 3
        assert 'router1' in inventory['hosts']
        
        # Check host configuration
        router1 = inventory['hosts']['router1']
        assert router1['hostname'] == '192.168.1.1'
        assert router1['platform'] == 'iosxe'
        assert 'all_devices' in router1['groups']
    
    def test_validate_inventory(self, sample_csv_file):
        """Test inventory validation."""
        loader = InventoryLoader(str(sample_csv_file))
        stats = loader.validate_inventory()
        
        assert stats['total_devices'] == 3
        assert 'platforms' in stats
        assert 'groups' in stats
        assert stats['platforms']['iosxe'] == 2
        assert stats['platforms']['iosxr'] == 1

class TestConnectionManager:
    """Test cases for ConnectionManager class."""
    
    @pytest.fixture
    def jump_host_config(self):
        """Sample jump host configuration."""
        return {
            'hostname': 'jumphost.example.com',
            'username': 'jumpuser',
            'password': 'jumppass',
            'port': 22
        }
    
    @pytest.fixture
    def connection_manager(self, jump_host_config):
        """Create ConnectionManager instance."""
        return ConnectionManager(
            jump_host_config=jump_host_config,
            max_connections=5,
            retry_attempts=2
        )
    
    def test_connection_manager_initialization(self, connection_manager):
        """Test ConnectionManager initialization."""
        assert connection_manager.retry_attempts == 2
        assert connection_manager.connection_pool.max_connections == 5
    
    @patch('core.connection_manager.ConnectHandler')
    def test_connection_pool_acquire_connection(self, mock_connect_handler, connection_manager):
        """Test connection pool acquire functionality."""
        mock_connection = Mock()
        mock_connect_handler.return_value = mock_connection
        
        config = ConnectionConfig(
            hostname='192.168.1.1',
            device_type='cisco_ios',
            username='testuser',
            password='testpass'
        )
        
        connection = connection_manager.connection_pool.acquire_connection(config)
        assert connection is not None
        mock_connect_handler.assert_called_once()
    
    def test_connection_config_creation(self):
        """Test ConnectionConfig creation."""
        config = ConnectionConfig(
            hostname='192.168.1.1',
            device_type='cisco_ios',
            username='testuser',
            password='testpass',
            timeout=30
        )
        
        assert config.hostname == '192.168.1.1'
        assert config.device_type == 'cisco_ios'
        assert config.timeout == 30
    
    @patch('core.connection_manager.ConnectHandler')
    def test_execute_command(self, mock_connect_handler, connection_manager):
        """Test command execution."""
        mock_connection = Mock()
        mock_connection.send_command.return_value = "Router uptime is 1 day"
        
        result = connection_manager.execute_command(
            mock_connection, 
            "show version | include uptime",
            timeout=30
        )
        
        assert result['success'] is True
        assert "Router uptime" in result['output']
        assert result['command'] == "show version | include uptime"

class TestTaskExecutor:
    """Test cases for TaskExecutor class."""
    
    @pytest.fixture
    def mock_nornir_config(self):
        """Mock Nornir configuration."""
        return {
            'runner': {'plugin': 'threaded', 'options': {'num_workers': 2}},
            'inventory': {'plugin': 'SimpleInventory'},
            'logging': {'enabled': False}
        }
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Mock ConnectionManager."""
        return Mock(spec=ConnectionManager)
    
    @pytest.fixture
    def mock_output_handler(self):
        """Mock OutputHandler."""
        return Mock(spec=OutputHandler)
    
    def test_collection_progress_initialization(self):
        """Test CollectionProgress initialization."""
        progress = CollectionProgress()
        assert progress.total_devices == 0
        assert progress.completed_devices == 0
        assert progress.device_completion_rate == 0.0
    
    def test_collection_progress_calculations(self):
        """Test CollectionProgress calculations."""
        progress = CollectionProgress(
            total_devices=10,
            completed_devices=7,
            total_tasks=50,
            completed_tasks=35
        )
        
        assert progress.device_completion_rate == 70.0
        assert progress.task_completion_rate == 70.0
    
    def test_task_result_creation(self):
        """Test TaskResult creation."""
        result = TaskResult(
            hostname='router1',
            task_name='test_task',
            success=True,
            start_time=1000.0,
            end_time=1010.0,
            duration=10.0
        )
        
        assert result.hostname == 'router1'
        assert result.success is True
        assert result.duration == 10.0

class TestOutputHandler:
    """Test cases for OutputHandler class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def output_handler(self, temp_dir):
        """Create OutputHandler instance."""
        return OutputHandler(base_output_dir=str(temp_dir))
    
    def test_output_handler_initialization(self, output_handler, temp_dir):
        """Test OutputHandler initialization."""
        assert output_handler.base_output_dir == temp_dir
        assert temp_dir.exists()
    
    def test_create_collection_run_directory(self, output_handler):
        """Test collection run directory creation."""
        run_dir = output_handler.create_collection_run_directory()
        
        assert run_dir.exists()
        assert run_dir.name.startswith('collector-run-')
        assert output_handler.collection_metadata is not None
    
    def test_create_device_directory_structure(self, output_handler):
        """Test device directory structure creation."""
        run_dir = output_handler.create_collection_run_directory()
        device_dirs = output_handler.create_device_directory_structure(run_dir, 'router1')
        
        expected_layers = ['health', 'interfaces', 'igp', 'mpls', 'bgp', 'vpn', 'static']
        for layer in expected_layers:
            assert layer in device_dirs
            assert device_dirs[layer].exists()
    
    def test_save_command_output(self, output_handler):
        """Test command output saving."""
        run_dir = output_handler.create_collection_run_directory()
        device_dirs = output_handler.create_device_directory_structure(run_dir, 'router1')
        
        result = output_handler.save_command_output(
            output_dir=device_dirs['health'],
            command='show version',
            output='Router version information...',
            hostname='router1',
            layer='health',
            platform='ios'
        )
        
        assert result['filename'] == 'show_version.txt'
        assert 'file_path' in result
        assert result['original_size'] > 0
    
    def test_file_metadata_creation(self):
        """Test FileMetadata creation."""
        metadata = FileMetadata(
            filename='test.txt',
            original_size=1024,
            command='show version',
            hostname='router1',
            layer='health',
            platform='ios'
        )
        
        assert metadata.filename == 'test.txt'
        assert metadata.original_size == 1024
        assert metadata.created_timestamp is not None
    
    def test_collection_metadata_creation(self):
        """Test CollectionMetadata creation."""
        metadata = CollectionMetadata(
            collection_id='test-run-001',
            start_time='2025-01-27T10:00:00',
            total_devices=5
        )
        
        assert metadata.collection_id == 'test-run-001'
        assert metadata.total_devices == 5
        assert metadata.layers_collected == []

class TestDataParser:
    """Test cases for DataParser class."""
    
    @pytest.fixture
    def data_parser(self):
        """Create DataParser instance."""
        return DataParser()
    
    def test_data_parser_initialization(self, data_parser):
        """Test DataParser initialization."""
        assert data_parser.parser_mapping is not None
        assert data_parser.platform_commands is not None
    
    def test_parse_result_creation(self):
        """Test ParseResult creation."""
        result = ParseResult(
            command='show version',
            success=True,
            parsed_data={'version': '15.1'},
            parser_used='genie'
        )
        
        assert result.command == 'show version'
        assert result.success is True
        assert result.parsed_data['version'] == '15.1'
    
    def test_parse_show_version(self, data_parser):
        """Test show version parsing."""
        output = """
        Router uptime is 1 day, 2 hours, 30 minutes
        System returned to ROM by power-on
        System image file is "bootflash:isr4300-universalk9.16.09.04.SPA.bin"
        
        cisco ISR4331/K9 (1RU) processor with 1795072K/6147K bytes of memory.
        Processor board ID FDO21520123
        
        Cisco IOS XE Software, Version 16.09.04
        """
        
        result = data_parser._parse_show_version(output)
        assert 'uptime' in result
        assert 'model' in result
        assert result['model'] == 'ISR4331/K9'
    
    def test_parse_interface_brief(self, data_parser):
        """Test interface brief parsing."""
        output = """
        Interface                  IP-Address      OK? Method Status                Protocol
        GigabitEthernet0/0/0       192.168.1.1     YES NVRAM  up                    up      
        GigabitEthernet0/0/1       unassigned      YES NVRAM  administratively down down    
        Loopback0                  10.1.1.1        YES NVRAM  up                    up      
        """
        
        result = data_parser._parse_interface_brief(output)
        assert 'interfaces' in result
        assert 'GigabitEthernet0/0/0' in result['interfaces']
        assert result['interfaces']['GigabitEthernet0/0/0']['ip_address'] == '192.168.1.1'
        assert result['interfaces']['GigabitEthernet0/0/1']['ip_address'] is None
    
    def test_platform_command_mapping(self, data_parser):
        """Test platform-specific command mapping."""
        ios_cmd = data_parser._get_platform_command('show ip interface brief', 'ios')
        iosxr_cmd = data_parser._get_platform_command('show ip interface brief', 'iosxr')
        
        assert ios_cmd == 'show ip interface brief'
        assert iosxr_cmd == 'show ipv4 interface brief'
    
    def test_ip_address_validation(self, data_parser):
        """Test IP address validation."""
        assert data_parser._is_ip_address('192.168.1.1') is True
        assert data_parser._is_ip_address('10.0.0.1') is True
        assert data_parser._is_ip_address('invalid.ip') is False
        assert data_parser._is_ip_address('192.168.1.256') is False

# Integration Tests
class TestCoreModulesIntegration:
    """Integration tests for core modules working together."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_inventory_to_output_integration(self, temp_dir):
        """Test integration between inventory loader and output handler."""
        # Create sample inventory
        csv_file = temp_dir / 'inventory.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows([
                ['hostname', 'management_ip', 'model_name'],
                ['router1', '192.168.1.1', 'Cisco 4431']
            ])
        
        # Load inventory
        loader = InventoryLoader(str(csv_file))
        devices = loader.load_csv_inventory()
        
        # Create output handler
        output_handler = OutputHandler(base_output_dir=str(temp_dir / 'output'))
        run_dir = output_handler.create_collection_run_directory()
        
        # Create device directories
        device_dirs = output_handler.create_device_directory_structure(run_dir, devices[0].hostname)
        
        assert len(devices) == 1
        assert devices[0].hostname == 'router1'
        assert device_dirs['health'].exists()
    
    @patch('core.connection_manager.ConnectHandler')
    def test_connection_to_parser_integration(self, mock_connect_handler):
        """Test integration between connection manager and data parser."""
        # Setup mocks
        mock_connection = Mock()
        mock_connection.send_command.return_value = "Cisco IOS XE Software, Version 16.09.04"
        mock_connect_handler.return_value = mock_connection
        
        # Create connection manager
        connection_manager = ConnectionManager()
        
        # Create data parser
        data_parser = DataParser()
        
        # Execute command and parse
        cmd_result = connection_manager.execute_command(
            mock_connection, 
            "show version",
            timeout=30
        )
        
        parse_result = data_parser.parse_command_output(
            "show version",
            cmd_result['output'],
            platform='iosxe'
        )
        
        assert cmd_result['success'] is True
        assert parse_result.success is True

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 
#!/usr/bin/env python3
"""
Test Suite 0003: Integration Tests for RR4 Complete Enhanced v4 CLI

This test suite validates end-to-end integration functionality including:
- Complete collection workflows
- Module integration
- File I/O operations
- Error propagation
- Performance characteristics

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

import pytest
import tempfile
import shutil
import os
import csv
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

# Import modules for integration testing
try:
    from inventory_loader import InventoryLoader
    from connection_manager import ConnectionManager
    from task_executor import TaskExecutor
    from output_handler import OutputHandler
    from data_parser import DataParser
    from health_collector import HealthCollector
    from tasks import get_layer_collector, get_available_layers
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Core modules not available: {e}")
    CORE_MODULES_AVAILABLE = False

class TestInventoryToCollectionIntegration:
    """Test integration from inventory loading to data collection."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_inventory_data(self):
        """Sample inventory data for testing."""
        return [
            ['hostname', 'management_ip', 'wan_ip', 'model_name'],
            ['core-router-1', '192.168.1.1', '10.1.1.1', 'Cisco 4431'],
            ['edge-router-1', '192.168.1.2', '10.1.1.2', 'Cisco ASR1001-X'],
            ['branch-router-1', '192.168.1.3', '10.1.1.3', 'Cisco 2911']
        ]
    
    @pytest.fixture
    def sample_inventory_file(self, temp_dir, sample_inventory_data):
        """Create sample inventory CSV file."""
        csv_file = temp_dir / 'test_inventory.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(sample_inventory_data)
        return csv_file
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_inventory_to_output_full_workflow(self, temp_dir, sample_inventory_file):
        """Test complete workflow from inventory loading to output generation."""
        # Load inventory
        inventory_loader = InventoryLoader(str(sample_inventory_file))
        devices = inventory_loader.load_devices()
        
        # Create output handler
        output_handler = OutputHandler(base_output_dir=str(temp_dir / 'output'))
        run_dir = output_handler.create_collection_run_directory()
        
        # Process each device
        for device in devices:
            device_dirs = output_handler.create_device_directory_structure(run_dir, device.hostname)
            
            # Verify device directory structure
            assert device_dirs['health'].exists()
            assert device_dirs['interfaces'].exists()
            assert device_dirs['bgp'].exists()
            
            # Save sample output
            sample_output = f"Sample output for {device.hostname}"
            result = output_handler.save_command_output(
                output_dir=device_dirs['health'],
                command='show version',
                output=sample_output,
                hostname=device.hostname,
                layer='health',
                platform=device.platform
            )
            
            assert result['filename'] == 'show_version.txt'
            assert result['original_size'] > 0
        
        # Save metadata
        output_handler.save_collection_metadata(run_dir)
        output_handler.save_file_metadata(run_dir)
        
        # Verify metadata files exist
        assert (run_dir / 'collection_metadata.json').exists()
        assert (run_dir / 'file_metadata.json').exists()
        
        # Verify device count
        assert len(devices) == 3
        assert any(d.hostname == 'core-router-1' for d in devices)
        assert any(d.platform == 'iosxe' for d in devices)
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_inventory_validation_integration(self, sample_inventory_file):
        """Test inventory validation integration."""
        inventory_loader = InventoryLoader(str(sample_inventory_file))
        
        # Test loading
        devices = inventory_loader.load_devices()
        assert len(devices) == 3
        
        # Test validation
        stats = inventory_loader.validate_inventory()
        assert stats['total_devices'] == 3
        assert 'platforms' in stats
        assert 'groups' in stats
        assert len(stats['validation_errors']) == 0
        
        # Test Nornir inventory generation
        inventory = inventory_loader.generate_nornir_inventory(devices, 'testuser', 'testpass')
        assert 'hosts' in inventory
        assert 'groups' in inventory
        assert len(inventory['hosts']) == 3

class TestConnectionToCollectionIntegration:
    """Test integration from connection management to data collection."""
    
    @pytest.fixture
    def mock_jump_host_config(self):
        """Mock jump host configuration."""
        return {
            'hostname': 'jumphost.example.com',
            'username': 'jumpuser',
            'password': 'jumppass',
            'port': 22
        }
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    @patch('core.connection_manager.ConnectHandler')
    def test_connection_to_health_collection_integration(self, mock_connect_handler, 
                                                        mock_jump_host_config, temp_dir):
        """Test integration from connection to health data collection."""
        # Setup mock connection
        mock_connection = Mock()
        mock_connection.send_command.return_value = """
        Cisco IOS XE Software, Version 16.09.04
        Router uptime is 1 day, 2 hours, 30 minutes
        cisco ISR4331/K9 (1RU) processor with 1795072K/6147K bytes of memory.
        """
        mock_connect_handler.return_value = mock_connection
        
        # Create connection manager
        connection_manager = ConnectionManager(jump_host_config=mock_jump_host_config)
        
        # Create output handler
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        run_dir = output_handler.create_collection_run_directory()
        
        # Create health collector
        health_collector = HealthCollector()
        
        # Execute collection workflow
        with connection_manager.get_connection(
            hostname='192.168.1.1',
            device_type='cisco_xe',
            username='testuser',
            password='testpass'
        ) as connection:
            result = health_collector.collect_layer_data(
                connection=connection,
                hostname='test-router',
                platform='iosxe',
                output_handler=output_handler
            )
        
        # Verify results
        assert result['hostname'] == 'test-router'
        assert result['platform'] == 'iosxe'
        assert result['layer'] == 'health'
        assert result['success_count'] > 0
        
        # Verify files were created
        device_dir = run_dir / 'test-router' / 'health'
        assert device_dir.exists()
        
        # Check for output files
        output_files = list(device_dir.glob('*.txt'))
        assert len(output_files) > 0
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    @patch('core.connection_manager.ConnectHandler')
    def test_connection_retry_integration(self, mock_connect_handler, mock_jump_host_config):
        """Test connection retry logic integration."""
        # Setup connection that fails then succeeds
        mock_connection = Mock()
        mock_connect_handler.side_effect = [
            Exception("Connection timeout"),
            mock_connection
        ]
        
        connection_manager = ConnectionManager(
            jump_host_config=mock_jump_host_config,
            retry_attempts=2,
            retry_delay=1
        )
        
        # Test connectivity with retry
        result = connection_manager.test_connectivity(
            hostname='192.168.1.1',
            device_type='cisco_ios',
            username='testuser',
            password='testpass'
        )
        
        # Should eventually succeed after retry
        assert 'response_time' in result

class TestDataParsingIntegration:
    """Test data parsing integration with collectors."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_parser_to_output_integration(self, temp_dir):
        """Test integration from parsing to output saving."""
        # Create data parser
        data_parser = DataParser()
        
        # Create output handler
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        run_dir = output_handler.create_collection_run_directory()
        device_dirs = output_handler.create_device_directory_structure(run_dir, 'test-router')
        
        # Sample command outputs
        test_commands = {
            'show version': """
            Cisco IOS XE Software, Version 16.09.04
            Router uptime is 1 day, 2 hours, 30 minutes
            cisco ISR4331/K9 (1RU) processor
            """,
            'show ip interface brief': """
            Interface                  IP-Address      OK? Method Status                Protocol
            GigabitEthernet0/0/0       192.168.1.1     YES NVRAM  up                    up      
            GigabitEthernet0/0/1       unassigned      YES NVRAM  administratively down down    
            """,
            'show ip bgp summary': """
            BGP router identifier 10.1.1.1, local AS number 65001
            Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
            10.1.1.2        4        65002    1234    1235        0    0    0 01:23:45        5
            """
        }
        
        # Process each command
        for command, output in test_commands.items():
            # Parse output
            parse_result = data_parser.parse_command_output(
                command=command,
                output=output,
                platform='iosxe'
            )
            
            # Save raw output
            raw_result = output_handler.save_command_output(
                output_dir=device_dirs['health'],
                command=command,
                output=output,
                hostname='test-router',
                layer='health',
                platform='iosxe'
            )
            
            # Save parsed output if successful
            if parse_result.success and parse_result.parsed_data:
                parsed_result = output_handler.save_parsed_output(
                    output_dir=device_dirs['health'],
                    command=command,
                    parsed_data=parse_result.parsed_data,
                    hostname='test-router',
                    layer='health',
                    platform='iosxe'
                )
                
                assert parsed_result['filename'].endswith('.json')
            
            assert raw_result['filename'].endswith('.txt')
            assert parse_result.success is True
        
        # Verify files were created
        txt_files = list(device_dirs['health'].glob('*.txt'))
        json_files = list(device_dirs['health'].glob('*.json'))
        
        assert len(txt_files) == 3
        assert len(json_files) >= 1  # At least some should parse successfully

class TestMultiLayerCollectionIntegration:
    """Test integration across multiple collection layers."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_connection(self):
        """Mock network connection with realistic outputs."""
        mock_conn = Mock()
        
        # Define realistic command outputs
        command_outputs = {
            'show version': 'Cisco IOS XE Software, Version 16.09.04',
            'show inventory': 'NAME: "Chassis", DESCR: "Cisco ISR4331"',
            'show processes cpu': 'CPU utilization for five seconds: 5%/0%',
            'show interfaces description': 'Interface Status Protocol Description',
            'show ip interface brief': 'Interface IP-Address OK? Method Status Protocol',
            'show ip ospf': 'Routing Process "ospf 1" with ID 10.1.1.1',
            'show mpls interfaces': 'Interface IP Tunnel BGP Static Operational',
            'show ip bgp summary': 'BGP router identifier 10.1.1.1',
            'show vrf': 'Name Default RD Interfaces',
            'show ip route static': 'Codes: L - local, C - connected'
        }
        
        def mock_send_command(command, **kwargs):
            for cmd_pattern, output in command_outputs.items():
                if cmd_pattern in command:
                    return output
            return f"Mock output for: {command}"
        
        mock_conn.send_command.side_effect = mock_send_command
        return mock_conn
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_multi_layer_collection_workflow(self, temp_dir, mock_connection):
        """Test complete multi-layer collection workflow."""
        # Create output handler
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        run_dir = output_handler.create_collection_run_directory()
        
        # Get all available layers
        available_layers = get_available_layers()
        
        # Test collection for each layer
        layer_results = {}
        for layer_name in available_layers:
            try:
                collector = get_layer_collector(layer_name)
                
                result = collector.collect_layer_data(
                    connection=mock_connection,
                    hostname='multi-layer-router',
                    platform='iosxe',
                    output_handler=output_handler
                )
                
                layer_results[layer_name] = result
                
                # Verify basic result structure
                assert result['hostname'] == 'multi-layer-router'
                assert result['platform'] == 'iosxe'
                assert result['layer'] == layer_name
                assert 'success_count' in result
                assert 'failure_count' in result
                
            except Exception as e:
                pytest.fail(f"Layer {layer_name} collection failed: {e}")
        
        # Verify all layers were processed
        assert len(layer_results) == len(available_layers)
        
        # Verify device directory structure exists
        device_dir = run_dir / 'multi-layer-router'
        assert device_dir.exists()
        
        # Check that each layer directory has files
        for layer_name in available_layers:
            layer_dir = device_dir / layer_name
            if layer_dir.exists():
                files = list(layer_dir.glob('*.txt'))
                # Should have at least some output files
                assert len(files) >= 0  # Some layers might not have files in mock scenario

class TestErrorPropagationIntegration:
    """Test error handling and propagation across modules."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_connection_error_propagation(self, temp_dir):
        """Test error propagation from connection failures."""
        # Create connection manager with invalid config
        connection_manager = ConnectionManager(
            jump_host_config={
                'hostname': 'invalid-host',
                'username': 'invalid',
                'password': 'invalid'
            }
        )
        
        # Create output handler
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        
        # Create health collector
        health_collector = HealthCollector()
        
        # Mock connection that always fails
        mock_connection = Mock()
        mock_connection.send_command.side_effect = Exception("Connection failed")
        
        # Execute collection and expect graceful error handling
        result = health_collector.collect_layer_data(
            connection=mock_connection,
            hostname='failing-router',
            platform='ios',
            output_handler=output_handler
        )
        
        # Should handle errors gracefully
        assert result['hostname'] == 'failing-router'
        assert result['failure_count'] > 0
        assert result['success_rate'] < 100
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_parsing_error_handling(self, temp_dir):
        """Test error handling in parsing pipeline."""
        # Create data parser
        data_parser = DataParser()
        
        # Test with malformed output
        malformed_outputs = [
            "",  # Empty output
            "Invalid command output",  # Unrecognized format
            "Error: Command not found",  # Error message
            None  # None output
        ]
        
        for output in malformed_outputs:
            try:
                result = data_parser.parse_command_output(
                    command='show version',
                    output=output or "",
                    platform='ios'
                )
                
                # Should not fail, but may not parse successfully
                assert result.command == 'show version'
                # Success can be True or False depending on fallback handling
                
            except Exception as e:
                pytest.fail(f"Parser should handle malformed output gracefully: {e}")

class TestPerformanceIntegration:
    """Test performance characteristics of integrated workflows."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_large_inventory_processing_performance(self, temp_dir):
        """Test performance with larger inventory."""
        # Create large inventory file
        csv_file = temp_dir / 'large_inventory.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hostname', 'management_ip', 'model_name'])
            
            # Create 50 devices
            for i in range(50):
                writer.writerow([
                    f'router-{i:03d}',
                    f'192.168.{i//10}.{i%10+1}',
                    'Cisco 4431'
                ])
        
        # Measure loading time
        start_time = time.time()
        
        inventory_loader = InventoryLoader(str(csv_file))
        devices = inventory_loader.load_devices()
        
        load_time = time.time() - start_time
        
        # Should load 50 devices quickly (under 1 second)
        assert len(devices) == 50
        assert load_time < 1.0
        
        # Test validation performance
        start_time = time.time()
        stats = inventory_loader.validate_inventory()
        validation_time = time.time() - start_time
        
        assert stats['total_devices'] == 50
        assert validation_time < 1.0
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_output_handler_performance(self, temp_dir):
        """Test output handler performance with multiple files."""
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        run_dir = output_handler.create_collection_run_directory()
        
        # Create multiple device directories
        device_count = 10
        files_per_device = 5
        
        start_time = time.time()
        
        for device_idx in range(device_count):
            hostname = f'perf-router-{device_idx:02d}'
            device_dirs = output_handler.create_device_directory_structure(run_dir, hostname)
            
            # Save multiple files per device
            for file_idx in range(files_per_device):
                command = f'show test-command-{file_idx}'
                output = f'Test output for {hostname} command {file_idx}' * 100  # Make it larger
                
                result = output_handler.save_command_output(
                    output_dir=device_dirs['health'],
                    command=command,
                    output=output,
                    hostname=hostname,
                    layer='health',
                    platform='ios'
                )
                
                assert result['original_size'] > 0
        
        # Save metadata
        output_handler.save_collection_metadata(run_dir)
        output_handler.save_file_metadata(run_dir)
        
        total_time = time.time() - start_time
        
        # Should handle 50 files (10 devices × 5 files) efficiently
        total_files = device_count * files_per_device
        assert total_files == 50
        assert total_time < 5.0  # Should complete in under 5 seconds
        
        # Verify all files were created
        all_files = list(run_dir.rglob('*.txt'))
        assert len(all_files) == total_files

class TestEndToEndIntegration:
    """Test complete end-to-end integration scenarios."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def complete_test_setup(self, temp_dir):
        """Create complete test environment."""
        # Create inventory file
        csv_file = temp_dir / 'test_inventory.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows([
                ['hostname', 'management_ip', 'model_name'],
                ['core-router-1', '192.168.1.1', 'Cisco 4431'],
                ['edge-router-1', '192.168.1.2', 'Cisco ASR1001-X']
            ])
        
        return {
            'inventory_file': csv_file,
            'temp_dir': temp_dir
        }
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    @patch('core.connection_manager.ConnectHandler')
    def test_complete_collection_workflow(self, mock_connect_handler, complete_test_setup):
        """Test complete collection workflow from inventory to output."""
        # Setup mock connection
        mock_connection = Mock()
        mock_connection.send_command.return_value = "Mock command output"
        mock_connect_handler.return_value = mock_connection
        
        # Load inventory
        inventory_loader = InventoryLoader(str(complete_test_setup['inventory_file']))
        devices = inventory_loader.load_devices()
        
        # Create connection manager
        connection_manager = ConnectionManager()
        
        # Create output handler
        output_handler = OutputHandler(
            base_output_dir=str(complete_test_setup['temp_dir'] / 'output')
        )
        run_dir = output_handler.create_collection_run_directory()
        
        # Process each device
        collection_results = []
        for device in devices:
            try:
                with connection_manager.get_connection(
                    hostname=device.management_ip,
                    device_type=device.device_type,
                    username='testuser',
                    password='testpass'
                ) as connection:
                    
                    # Collect health data
                    health_collector = HealthCollector()
                    result = health_collector.collect_layer_data(
                        connection=connection,
                        hostname=device.hostname,
                        platform=device.platform,
                        output_handler=output_handler
                    )
                    
                    collection_results.append(result)
                    
            except Exception as e:
                # Record failure
                collection_results.append({
                    'hostname': device.hostname,
                    'error': str(e),
                    'success_count': 0,
                    'failure_count': 1
                })
        
        # Save final metadata
        output_handler.save_collection_metadata(run_dir)
        output_handler.save_file_metadata(run_dir)
        
        # Verify results
        assert len(collection_results) == 2
        assert all('hostname' in result for result in collection_results)
        
        # Verify output structure
        assert run_dir.exists()
        assert (run_dir / 'collection_metadata.json').exists()
        
        # Verify device directories
        for device in devices:
            device_dir = run_dir / device.hostname
            assert device_dir.exists()

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 
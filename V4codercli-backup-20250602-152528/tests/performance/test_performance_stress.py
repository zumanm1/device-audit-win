#!/usr/bin/env python3
"""
Test Suite 0004: Performance and Stress Testing for RR4 Complete Enhanced v4 CLI

This test suite validates performance characteristics and stress testing including:
- Large-scale device processing
- Memory usage optimization
- Concurrent connection handling
- File I/O performance
- Error recovery under load

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
import time
import threading
import concurrent.futures
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import psutil
import gc

# Import modules for performance testing
try:
    from inventory_loader import InventoryLoader
    from connection_manager import ConnectionManager, ConnectionPool
    from task_executor import TaskExecutor
    from output_handler import OutputHandler
    from data_parser import DataParser
    from health_collector import HealthCollector
    from tasks import get_layer_collector, get_available_layers
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Core modules not available: {e}")
    CORE_MODULES_AVAILABLE = False

class TestLargeScaleInventoryPerformance:
    """Test performance with large device inventories."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def create_large_inventory(self, temp_dir: Path, device_count: int) -> Path:
        """Create large inventory file for testing."""
        csv_file = temp_dir / f'large_inventory_{device_count}.csv'
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hostname', 'management_ip', 'model_name'])
            
            models = ['Cisco 4431', 'Cisco ASR1001-X', 'Cisco 2911', 'Cisco NCS-5500']
            
            for i in range(device_count):
                writer.writerow([
                    f'router-{i:04d}',
                    f'192.168.{(i//254)+1}.{(i%254)+1}',
                    models[i % len(models)]
                ])
        
        return csv_file
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    @pytest.mark.parametrize("device_count", [100, 500, 1000])
    def test_large_inventory_loading_performance(self, temp_dir, device_count):
        """Test inventory loading performance with different scales."""
        csv_file = self.create_large_inventory(temp_dir, device_count)
        
        # Measure loading time
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        inventory_loader = InventoryLoader(str(csv_file))
        devices = inventory_loader.load_csv_inventory()
        
        load_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_used = end_memory - start_memory
        
        # Performance assertions
        assert len(devices) == device_count
        assert load_time < (device_count / 100)  # Should load ~100 devices per second
        assert memory_used < (device_count / 10)  # Should use less than 0.1MB per device
        
        print(f"Loaded {device_count} devices in {load_time:.2f}s, "
              f"Memory used: {memory_used:.2f}MB")
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_inventory_validation_performance(self, temp_dir):
        """Test inventory validation performance."""
        device_count = 1000
        csv_file = self.create_large_inventory(temp_dir, device_count)
        
        inventory_loader = InventoryLoader(str(csv_file))
        
        # Measure validation time
        start_time = time.time()
        stats = inventory_loader.validate_inventory()
        validation_time = time.time() - start_time
        
        assert stats['total_devices'] == device_count
        assert validation_time < 5.0  # Should validate 1000 devices in under 5 seconds
        assert len(stats['validation_errors']) == 0
        
        print(f"Validated {device_count} devices in {validation_time:.2f}s")
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_nornir_inventory_generation_performance(self, temp_dir):
        """Test Nornir inventory generation performance."""
        device_count = 500
        csv_file = self.create_large_inventory(temp_dir, device_count)
        
        inventory_loader = InventoryLoader(str(csv_file))
        devices = inventory_loader.load_csv_inventory()
        
        # Measure generation time
        start_time = time.time()
        inventory = inventory_loader.generate_nornir_inventory(devices, 'testuser', 'testpass')
        generation_time = time.time() - start_time
        
        assert len(inventory['hosts']) == device_count
        assert generation_time < 10.0  # Should generate 500 device inventory in under 10 seconds
        
        print(f"Generated Nornir inventory for {device_count} devices in {generation_time:.2f}s")

class TestConnectionPoolPerformance:
    """Test connection pool performance and concurrency."""
    
    @pytest.fixture
    def mock_jump_host_config(self):
        """Mock jump host configuration."""
        return {
            'hostname': 'jumphost.example.com',
            'username': 'jumpuser',
            'password': 'jumppass',
            'port': 22
        }
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    @patch('core.connection_manager.ConnectHandler')
    def test_connection_pool_concurrent_access(self, mock_connect_handler, mock_jump_host_config):
        """Test connection pool under concurrent access."""
        # Setup mock connections
        mock_connections = []
        for i in range(20):
            mock_conn = Mock()
            mock_conn.send_command.return_value = f"Output from connection {i}"
            mock_connections.append(mock_conn)
        
        mock_connect_handler.side_effect = mock_connections
        
        connection_manager = ConnectionManager(
            jump_host_config=mock_jump_host_config,
            max_connections=10
        )
        
        # Test concurrent connection requests
        def test_connection(device_id):
            try:
                with connection_manager.get_connection(
                    hostname=f'192.168.1.{device_id}',
                    device_type='cisco_ios',
                    username='testuser',
                    password='testpass'
                ) as connection:
                    result = connection_manager.execute_command(
                        connection, 
                        'show version',
                        timeout=30
                    )
                    return result['success']
            except Exception as e:
                return False
        
        # Execute concurrent connections
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(test_connection, i) for i in range(1, 21)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        execution_time = time.time() - start_time
        
        # Verify results
        success_count = sum(results)
        assert success_count >= 10  # At least pool size should succeed
        assert execution_time < 30.0  # Should complete within reasonable time
        
        print(f"Concurrent connections: {success_count}/20 successful in {execution_time:.2f}s")
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_connection_pool_memory_usage(self, mock_jump_host_config):
        """Test connection pool memory usage."""
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple connection pools
        pools = []
        for i in range(10):
            connection_manager = ConnectionManager(
                jump_host_config=mock_jump_host_config,
                max_connections=15
            )
            pools.append(connection_manager)
        
        mid_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Clean up
        for pool in pools:
            pool.close_all_connections()
        
        del pools
        gc.collect()
        
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        memory_growth = mid_memory - start_memory
        memory_cleanup = mid_memory - end_memory
        
        # Memory should not grow excessively
        assert memory_growth < 100  # Less than 100MB for 10 pools
        assert memory_cleanup > (memory_growth * 0.5)  # At least 50% cleanup
        
        print(f"Memory growth: {memory_growth:.2f}MB, Cleanup: {memory_cleanup:.2f}MB")

class TestOutputHandlerPerformance:
    """Test output handler performance with large volumes."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    @pytest.mark.parametrize("device_count,files_per_device", [
        (50, 10),
        (100, 15),
        (200, 20)
    ])
    def test_large_scale_file_output_performance(self, temp_dir, device_count, files_per_device):
        """Test file output performance with large numbers of files."""
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        run_dir = output_handler.create_collection_run_directory()
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        total_files = 0
        total_size = 0
        
        for device_idx in range(device_count):
            hostname = f'perf-router-{device_idx:03d}'
            device_dirs = output_handler.create_device_directory_structure(run_dir, hostname)
            
            for file_idx in range(files_per_device):
                command = f'show test-command-{file_idx}'
                # Create variable-sized output (1KB to 10KB)
                output_size = 1000 + (file_idx * 1000)
                output = 'X' * output_size
                
                result = output_handler.save_command_output(
                    output_dir=device_dirs['health'],
                    command=command,
                    output=output,
                    hostname=hostname,
                    layer='health',
                    platform='ios'
                )
                
                total_files += 1
                total_size += result['original_size']
        
        # Save metadata
        output_handler.save_collection_metadata(run_dir)
        output_handler.save_file_metadata(run_dir)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        # Performance assertions
        expected_files = device_count * files_per_device
        assert total_files == expected_files
        assert execution_time < (expected_files / 50)  # Should handle ~50 files per second
        assert memory_used < 200  # Should use less than 200MB
        
        # Verify all files exist
        all_files = list(run_dir.rglob('*.txt'))
        assert len(all_files) == expected_files
        
        print(f"Created {total_files} files ({total_size/1024/1024:.2f}MB) "
              f"in {execution_time:.2f}s, Memory: {memory_used:.2f}MB")
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_compression_performance(self, temp_dir):
        """Test file compression performance."""
        output_handler = OutputHandler(
            base_output_dir=str(temp_dir),
            compression_threshold_mb=0.001  # Compress files > 1KB
        )
        run_dir = output_handler.create_collection_run_directory()
        device_dirs = output_handler.create_device_directory_structure(run_dir, 'compression-test')
        
        # Create files of different sizes
        file_sizes = [500, 2000, 5000, 10000, 50000]  # bytes
        compression_results = []
        
        start_time = time.time()
        
        for i, size in enumerate(file_sizes):
            command = f'show large-output-{i}'
            output = 'A' * size  # Highly compressible content
            
            result = output_handler.save_command_output(
                output_dir=device_dirs['health'],
                command=command,
                output=output,
                hostname='compression-test',
                layer='health',
                platform='ios'
            )
            
            compression_results.append(result)
        
        compression_time = time.time() - start_time
        
        # Verify compression worked for larger files
        compressed_count = sum(1 for r in compression_results if r.get('compressed', False))
        assert compressed_count >= 3  # Files > 1KB should be compressed
        assert compression_time < 5.0  # Should complete quickly
        
        print(f"Compressed {compressed_count}/5 files in {compression_time:.2f}s")

class TestDataParserPerformance:
    """Test data parser performance with large outputs."""
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_large_output_parsing_performance(self):
        """Test parsing performance with large command outputs."""
        data_parser = DataParser()
        
        # Create large BGP table output
        bgp_output_lines = [
            "BGP table version is 12345, local router ID is 10.1.1.1",
            "Status codes: s suppressed, d damped, h history, * valid, > best, i - internal",
            "Origin codes: i - IGP, e - EGP, ? - incomplete"
        ]
        
        # Add many BGP routes
        for i in range(1000):
            network = f"10.{i//256}.{i%256}.0/24"
            next_hop = f"192.168.{i%10}.{(i//10)%10}"
            bgp_output_lines.append(f"*> {network:<18} {next_hop:<15} 0 100 0 i")
        
        large_bgp_output = '\n'.join(bgp_output_lines)
        
        # Measure parsing time
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        result = data_parser.parse_command_output(
            command='show ip bgp',
            output=large_bgp_output,
            platform='ios'
        )
        
        parse_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_used = end_memory - start_memory
        
        assert result.success is True
        assert parse_time < 5.0  # Should parse large output in under 5 seconds
        assert memory_used < 50  # Should use less than 50MB
        
        print(f"Parsed large BGP output ({len(large_bgp_output)} chars) "
              f"in {parse_time:.2f}s, Memory: {memory_used:.2f}MB")
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_concurrent_parsing_performance(self):
        """Test concurrent parsing performance."""
        data_parser = DataParser()
        
        # Create different command outputs
        test_outputs = {
            'show version': 'Cisco IOS XE Software, Version 16.09.04\nRouter uptime is 1 day',
            'show ip interface brief': 'Interface IP-Address OK? Method Status Protocol\nGi0/0/0 192.168.1.1 YES NVRAM up up',
            'show ip route': 'Codes: L - local, C - connected\nC 192.168.1.0/24 is directly connected',
            'show ip bgp summary': 'BGP router identifier 10.1.1.1\nNeighbor V AS MsgRcvd MsgSent',
            'show interfaces': 'GigabitEthernet0/0/0 is up, line protocol is up'
        }
        
        def parse_output(command_output_pair):
            command, output = command_output_pair
            return data_parser.parse_command_output(command, output, 'ios')
        
        # Test concurrent parsing
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Parse each output 10 times concurrently
            tasks = []
            for _ in range(10):
                for command, output in test_outputs.items():
                    tasks.append((command, output))
            
            futures = [executor.submit(parse_output, task) for task in tasks]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        parse_time = time.time() - start_time
        
        # Verify results
        successful_parses = sum(1 for r in results if r.success)
        total_parses = len(results)
        
        assert successful_parses == total_parses  # All should succeed
        assert parse_time < 10.0  # Should complete within reasonable time
        
        print(f"Concurrent parsing: {successful_parses}/{total_parses} successful "
              f"in {parse_time:.2f}s")

class TestStressAndErrorRecovery:
    """Test system behavior under stress and error conditions."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_memory_pressure_handling(self, temp_dir):
        """Test behavior under memory pressure."""
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        run_dir = output_handler.create_collection_run_directory()
        
        # Create progressively larger outputs
        device_dirs = output_handler.create_device_directory_structure(run_dir, 'memory-test')
        
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        max_memory = start_memory
        
        try:
            for i in range(20):
                # Create increasingly large outputs (up to 10MB)
                output_size = min(1024 * 1024 * (i + 1), 10 * 1024 * 1024)
                large_output = 'X' * output_size
                
                result = output_handler.save_command_output(
                    output_dir=device_dirs['health'],
                    command=f'show large-command-{i}',
                    output=large_output,
                    hostname='memory-test',
                    layer='health',
                    platform='ios'
                )
                
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                max_memory = max(max_memory, current_memory)
                
                # Force garbage collection
                del large_output
                gc.collect()
                
                assert result['original_size'] > 0
        
        except MemoryError:
            pytest.skip("System ran out of memory - this is expected behavior")
        
        memory_growth = max_memory - start_memory
        
        # Memory growth should be reasonable
        assert memory_growth < 500  # Less than 500MB growth
        
        print(f"Maximum memory growth under pressure: {memory_growth:.2f}MB")
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    @patch('core.connection_manager.ConnectHandler')
    def test_connection_failure_recovery(self, mock_connect_handler, temp_dir):
        """Test recovery from connection failures."""
        # Setup connections that fail intermittently
        failure_count = 0
        
        def failing_connection(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if failure_count % 3 == 0:  # Every 3rd connection fails
                raise Exception("Simulated connection failure")
            
            mock_conn = Mock()
            mock_conn.send_command.return_value = "Success output"
            return mock_conn
        
        mock_connect_handler.side_effect = failing_connection
        
        connection_manager = ConnectionManager(retry_attempts=2, retry_delay=0.1)
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        health_collector = HealthCollector()
        
        # Test multiple collection attempts
        results = []
        for i in range(10):
            try:
                with connection_manager.get_connection(
                    hostname=f'192.168.1.{i+1}',
                    device_type='cisco_ios',
                    username='testuser',
                    password='testpass'
                ) as connection:
                    result = health_collector.collect_layer_data(
                        connection=connection,
                        hostname=f'test-router-{i}',
                        platform='ios',
                        output_handler=output_handler
                    )
                    results.append(result)
            except Exception as e:
                results.append({'error': str(e), 'hostname': f'test-router-{i}'})
        
        # Should have some successes despite failures
        successful_results = [r for r in results if 'error' not in r]
        failed_results = [r for r in results if 'error' in r]
        
        assert len(successful_results) > 0  # Some should succeed
        assert len(failed_results) > 0  # Some should fail (as expected)
        
        print(f"Connection recovery test: {len(successful_results)} successes, "
              f"{len(failed_results)} failures")
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    def test_disk_space_handling(self, temp_dir):
        """Test behavior when disk space is limited."""
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        run_dir = output_handler.create_collection_run_directory()
        device_dirs = output_handler.create_device_directory_structure(run_dir, 'disk-test')
        
        # Get initial disk space
        disk_usage = shutil.disk_usage(temp_dir)
        available_space = disk_usage.free
        
        # Try to create files until we approach disk limits
        file_count = 0
        total_size = 0
        
        try:
            while total_size < (available_space * 0.1):  # Use up to 10% of available space
                output_size = 1024 * 1024  # 1MB files
                large_output = 'D' * output_size
                
                result = output_handler.save_command_output(
                    output_dir=device_dirs['health'],
                    command=f'show disk-test-{file_count}',
                    output=large_output,
                    hostname='disk-test',
                    layer='health',
                    platform='ios'
                )
                
                file_count += 1
                total_size += result['original_size']
                
                if file_count > 100:  # Safety limit
                    break
        
        except OSError as e:
            # Expected when disk space runs out
            print(f"Disk space exhausted after {file_count} files: {e}")
        
        # Should have created some files before running out of space
        assert file_count > 0
        assert total_size > 0
        
        print(f"Created {file_count} files ({total_size/1024/1024:.2f}MB) before disk limits")

class TestConcurrentCollectionPerformance:
    """Test performance of concurrent data collection."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.skipif(not CORE_MODULES_AVAILABLE, reason="Core modules not available")
    @patch('core.connection_manager.ConnectHandler')
    def test_concurrent_multi_device_collection(self, mock_connect_handler, temp_dir):
        """Test concurrent collection from multiple devices."""
        # Setup mock connections
        def create_mock_connection(*args, **kwargs):
            mock_conn = Mock()
            mock_conn.send_command.return_value = "Mock device output"
            return mock_conn
        
        mock_connect_handler.side_effect = create_mock_connection
        
        # Create test setup
        connection_manager = ConnectionManager(max_connections=10)
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        
        def collect_from_device(device_id):
            """Collect data from a single device."""
            try:
                with connection_manager.get_connection(
                    hostname=f'192.168.1.{device_id}',
                    device_type='cisco_ios',
                    username='testuser',
                    password='testpass'
                ) as connection:
                    
                    health_collector = HealthCollector()
                    result = health_collector.collect_layer_data(
                        connection=connection,
                        hostname=f'concurrent-router-{device_id}',
                        platform='ios',
                        output_handler=output_handler
                    )
                    return result
            except Exception as e:
                return {'error': str(e), 'device_id': device_id}
        
        # Test concurrent collection
        device_count = 20
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(collect_from_device, i) for i in range(1, device_count + 1)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        execution_time = time.time() - start_time
        
        # Analyze results
        successful_collections = [r for r in results if 'error' not in r]
        failed_collections = [r for r in results if 'error' in r]
        
        assert len(successful_collections) >= device_count * 0.8  # At least 80% success
        assert execution_time < 60.0  # Should complete within reasonable time
        
        # Calculate throughput
        throughput = len(successful_collections) / execution_time
        
        print(f"Concurrent collection: {len(successful_collections)}/{device_count} devices "
              f"in {execution_time:.2f}s (Throughput: {throughput:.2f} devices/sec)")

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s']) 
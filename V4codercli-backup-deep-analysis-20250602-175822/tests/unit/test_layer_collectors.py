#!/usr/bin/env python3
"""
Test Suite 0001: Layer Collectors Testing for RR4 Complete Enhanced v4 CLI

This test suite validates the layer-specific collectors functionality including:
- Health collector
- Interface collector
- IGP collector
- MPLS collector
- BGP collector
- VPN collector
- Static route collector

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

# Import modules under test
from health_collector import HealthCollector, HealthCommands
from interface_collector import InterfaceCollector
from igp_collector import IGPCollector
from mpls_collector import MPLSCollector
from bgp_collector import BGPCollector
from vpn_collector import VPNCollector
from static_route_collector import StaticRouteCollector
from tasks import get_layer_collector, get_available_layers, validate_layers

from output_handler import OutputHandler
from data_parser import DataParser

class TestHealthCollector:
    """Test cases for HealthCollector class."""
    
    @pytest.fixture
    def health_collector(self):
        """Create HealthCollector instance."""
        return HealthCollector()
    
    @pytest.fixture
    def mock_connection(self):
        """Mock network connection."""
        mock_conn = Mock()
        mock_conn.send_command.return_value = "Sample command output"
        return mock_conn
    
    @pytest.fixture
    def mock_output_handler(self):
        """Mock OutputHandler."""
        mock_handler = Mock(spec=OutputHandler)
        mock_handler.collection_metadata = Mock()
        mock_handler.collection_metadata.collection_id = "test-run-001"
        mock_handler.base_output_dir = Path("/tmp/test")
        mock_handler.create_device_directory_structure.return_value = {
            'health': Path("/tmp/test/router1/health")
        }
        mock_handler.save_command_output.return_value = {
            'filename': 'show_version.txt',
            'original_size': 1024
        }
        mock_handler.save_parsed_output.return_value = {
            'filename': 'show_version.json',
            'size': 512
        }
        return mock_handler
    
    def test_health_collector_initialization(self, health_collector):
        """Test HealthCollector initialization."""
        assert health_collector.logger is not None
        assert health_collector.data_parser is not None
        assert health_collector.commands is not None
    
    def test_health_commands_initialization(self):
        """Test HealthCommands initialization."""
        commands = HealthCommands()
        assert len(commands.ios_commands) > 0
        assert len(commands.iosxe_commands) > 0
        assert len(commands.iosxr_commands) > 0
        assert "show version" in commands.ios_commands
    
    def test_get_commands_for_platform(self, health_collector):
        """Test platform-specific command selection."""
        ios_commands = health_collector.get_commands_for_platform('ios')
        iosxe_commands = health_collector.get_commands_for_platform('iosxe')
        iosxr_commands = health_collector.get_commands_for_platform('iosxr')
        
        assert "show version" in ios_commands
        assert "show version" in iosxe_commands
        assert "show version" in iosxr_commands
        
        # IOS XR should have different commands
        assert "show platform" in iosxr_commands
        assert "admin show processes memory" in iosxr_commands
    
    def test_get_command_timeout(self, health_collector):
        """Test command timeout calculation."""
        short_timeout = health_collector._get_command_timeout("show version")
        long_timeout = health_collector._get_command_timeout("show processes memory sorted")
        
        assert short_timeout == 60  # Default
        assert long_timeout == 120  # Extended for memory commands
    
    @patch('tasks.health_collector.DataParser')
    def test_collect_layer_data_success(self, mock_parser_class, health_collector, 
                                       mock_connection, mock_output_handler):
        """Test successful health data collection."""
        # Setup mock parser
        mock_parser = Mock()
        mock_parser.parse_command_output.return_value = Mock(
            success=True,
            parsed_data={'version': '15.1'},
            parser_used='genie'
        )
        mock_parser_class.return_value = mock_parser
        health_collector.data_parser = mock_parser
        
        # Execute collection
        result = health_collector.collect_layer_data(
            connection=mock_connection,
            hostname='router1',
            platform='ios',
            output_handler=mock_output_handler
        )
        
        # Verify results
        assert result['hostname'] == 'router1'
        assert result['platform'] == 'ios'
        assert result['layer'] == 'health'
        assert result['success_count'] > 0
        assert result['total_commands'] > 0
    
    def test_validate_health_status(self, health_collector):
        """Test health status validation."""
        health_data = {
            'success_rate': 95.0,
            'commands_executed': [
                {'command': 'show version', 'parsed': True},
                {'command': 'show processes cpu', 'parsed': True}
            ]
        }
        
        validation = health_collector.validate_health_status(health_data)
        
        assert validation['overall_health'] == 'healthy'
        assert len(validation['issues']) == 0
    
    def test_validate_health_status_low_success_rate(self, health_collector):
        """Test health validation with low success rate."""
        health_data = {
            'success_rate': 75.0,
            'commands_executed': []
        }
        
        validation = health_collector.validate_health_status(health_data)
        
        assert validation['overall_health'] == 'critical'
        assert len(validation['issues']) > 0
        assert 'Low command success rate' in validation['issues'][0]
    
    def test_get_health_summary(self, health_collector):
        """Test health summary generation."""
        health_data = {
            'hostname': 'router1',
            'platform': 'ios',
            'total_commands': 10,
            'success_count': 9,
            'failure_count': 1,
            'success_rate': 90.0
        }
        
        summary = health_collector.get_health_summary(health_data)
        
        assert summary['hostname'] == 'router1'
        assert summary['platform'] == 'ios'
        assert summary['command_statistics']['total_commands'] == 10
        assert summary['command_statistics']['success_rate'] == 90.0

class TestInterfaceCollector:
    """Test cases for InterfaceCollector class."""
    
    @pytest.fixture
    def interface_collector(self):
        """Create InterfaceCollector instance."""
        return InterfaceCollector()
    
    @pytest.fixture
    def mock_connection(self):
        """Mock network connection."""
        mock_conn = Mock()
        mock_conn.send_command.return_value = "Interface output"
        return mock_conn
    
    @pytest.fixture
    def mock_output_handler(self):
        """Mock OutputHandler."""
        return Mock(spec=OutputHandler)
    
    def test_interface_collector_initialization(self, interface_collector):
        """Test InterfaceCollector initialization."""
        assert interface_collector.logger is not None
        assert interface_collector.data_parser is not None
    
    def test_collect_layer_data(self, interface_collector, mock_connection, mock_output_handler):
        """Test interface data collection."""
        result = interface_collector.collect_layer_data(
            connection=mock_connection,
            hostname='router1',
            platform='ios',
            output_handler=mock_output_handler
        )
        
        assert result['hostname'] == 'router1'
        assert result['platform'] == 'ios'
        assert result['layer'] == 'interfaces'
        assert 'success_count' in result
        assert 'failure_count' in result

class TestIGPCollector:
    """Test cases for IGPCollector class."""
    
    @pytest.fixture
    def igp_collector(self):
        """Create IGPCollector instance."""
        return IGPCollector()
    
    def test_igp_collector_initialization(self, igp_collector):
        """Test IGPCollector initialization."""
        assert igp_collector.logger is not None
        assert igp_collector.data_parser is not None
    
    def test_collect_layer_data(self, igp_collector):
        """Test IGP data collection."""
        mock_connection = Mock()
        mock_connection.send_command.return_value = "OSPF output"
        mock_output_handler = Mock(spec=OutputHandler)
        
        result = igp_collector.collect_layer_data(
            connection=mock_connection,
            hostname='router1',
            platform='ios',
            output_handler=mock_output_handler
        )
        
        assert result['layer'] == 'igp'

class TestMPLSCollector:
    """Test cases for MPLSCollector class."""
    
    @pytest.fixture
    def mpls_collector(self):
        """Create MPLSCollector instance."""
        return MPLSCollector()
    
    def test_mpls_collector_initialization(self, mpls_collector):
        """Test MPLSCollector initialization."""
        assert mpls_collector.logger is not None
        assert mpls_collector.data_parser is not None
    
    def test_collect_layer_data(self, mpls_collector):
        """Test MPLS data collection."""
        mock_connection = Mock()
        mock_connection.send_command.return_value = "MPLS output"
        mock_output_handler = Mock(spec=OutputHandler)
        
        result = mpls_collector.collect_layer_data(
            connection=mock_connection,
            hostname='router1',
            platform='ios',
            output_handler=mock_output_handler
        )
        
        assert result['layer'] == 'mpls'

class TestBGPCollector:
    """Test cases for BGPCollector class."""
    
    @pytest.fixture
    def bgp_collector(self):
        """Create BGPCollector instance."""
        return BGPCollector()
    
    def test_bgp_collector_initialization(self, bgp_collector):
        """Test BGPCollector initialization."""
        assert bgp_collector.logger is not None
        assert bgp_collector.data_parser is not None
    
    def test_collect_layer_data_with_timeout(self, bgp_collector):
        """Test BGP data collection with appropriate timeouts."""
        mock_connection = Mock()
        mock_connection.send_command.return_value = "BGP output"
        mock_output_handler = Mock(spec=OutputHandler)
        
        result = bgp_collector.collect_layer_data(
            connection=mock_connection,
            hostname='router1',
            platform='ios',
            output_handler=mock_output_handler
        )
        
        assert result['layer'] == 'bgp'
        # Verify that send_command was called with appropriate timeouts
        calls = mock_connection.send_command.call_args_list
        
        # Check if any call used extended timeout for large BGP tables
        extended_timeout_used = any(
            call.kwargs.get('read_timeout', 60) > 60 
            for call in calls if call.kwargs
        )
        assert extended_timeout_used

class TestVPNCollector:
    """Test cases for VPNCollector class."""
    
    @pytest.fixture
    def vpn_collector(self):
        """Create VPNCollector instance."""
        return VPNCollector()
    
    def test_vpn_collector_initialization(self, vpn_collector):
        """Test VPNCollector initialization."""
        assert vpn_collector.logger is not None
        assert vpn_collector.data_parser is not None
    
    def test_collect_layer_data(self, vpn_collector):
        """Test VPN data collection."""
        mock_connection = Mock()
        mock_connection.send_command.return_value = "VPN output"
        mock_output_handler = Mock(spec=OutputHandler)
        
        result = vpn_collector.collect_layer_data(
            connection=mock_connection,
            hostname='router1',
            platform='ios',
            output_handler=mock_output_handler
        )
        
        assert result['layer'] == 'vpn'

class TestStaticRouteCollector:
    """Test cases for StaticRouteCollector class."""
    
    @pytest.fixture
    def static_collector(self):
        """Create StaticRouteCollector instance."""
        return StaticRouteCollector()
    
    def test_static_collector_initialization(self, static_collector):
        """Test StaticRouteCollector initialization."""
        assert static_collector.logger is not None
        assert static_collector.data_parser is not None
    
    def test_collect_layer_data(self, static_collector):
        """Test static route data collection."""
        mock_connection = Mock()
        mock_connection.send_command.return_value = "Static route output"
        mock_output_handler = Mock(spec=OutputHandler)
        
        result = static_collector.collect_layer_data(
            connection=mock_connection,
            hostname='router1',
            platform='ios',
            output_handler=mock_output_handler
        )
        
        assert result['layer'] == 'static'

class TestLayerCollectorRegistry:
    """Test cases for layer collector registry functions."""
    
    def test_get_available_layers(self):
        """Test getting available layers."""
        layers = get_available_layers()
        
        expected_layers = ['health', 'interfaces', 'igp', 'mpls', 'bgp', 'vpn', 'static']
        for layer in expected_layers:
            assert layer in layers
    
    def test_get_layer_collector_valid(self):
        """Test getting valid layer collectors."""
        health_collector = get_layer_collector('health')
        assert isinstance(health_collector, HealthCollector)
        
        interface_collector = get_layer_collector('interfaces')
        assert isinstance(interface_collector, InterfaceCollector)
        
        bgp_collector = get_layer_collector('bgp')
        assert isinstance(bgp_collector, BGPCollector)
    
    def test_get_layer_collector_invalid(self):
        """Test getting invalid layer collector."""
        with pytest.raises(ValueError) as exc_info:
            get_layer_collector('invalid_layer')
        
        assert "Unknown layer: invalid_layer" in str(exc_info.value)
    
    def test_validate_layers_valid(self):
        """Test validating valid layers."""
        valid_layers = ['health', 'interfaces', 'bgp']
        result = validate_layers(valid_layers)
        assert result is True
    
    def test_validate_layers_invalid(self):
        """Test validating invalid layers."""
        invalid_layers = ['health', 'invalid_layer', 'bgp']
        
        with pytest.raises(ValueError) as exc_info:
            validate_layers(invalid_layers)
        
        assert "Invalid layers: ['invalid_layer']" in str(exc_info.value)

class TestLayerCollectorErrorHandling:
    """Test error handling in layer collectors."""
    
    @pytest.fixture
    def health_collector(self):
        """Create HealthCollector instance."""
        return HealthCollector()
    
    def test_connection_failure_handling(self, health_collector):
        """Test handling of connection failures."""
        mock_connection = Mock()
        mock_connection.send_command.side_effect = Exception("Connection timeout")
        
        mock_output_handler = Mock(spec=OutputHandler)
        mock_output_handler.collection_metadata = Mock()
        mock_output_handler.collection_metadata.collection_id = "test-run-001"
        mock_output_handler.base_output_dir = Path("/tmp/test")
        mock_output_handler.create_device_directory_structure.return_value = {
            'health': Path("/tmp/test/router1/health")
        }
        
        result = health_collector.collect_layer_data(
            connection=mock_connection,
            hostname='router1',
            platform='ios',
            output_handler=mock_output_handler
        )
        
        # Should handle errors gracefully
        assert result['hostname'] == 'router1'
        assert result['failure_count'] > 0
        assert result['success_rate'] < 100
    
    def test_command_retry_logic(self, health_collector):
        """Test command retry logic."""
        mock_connection = Mock()
        # First call fails, second succeeds
        mock_connection.send_command.side_effect = [
            Exception("Temporary failure"),
            "Success output"
        ]
        
        result = health_collector._execute_command_with_retry(
            mock_connection, 
            "show version", 
            timeout=60,
            max_retries=2
        )
        
        assert result['success'] is True
        assert result['output'] == "Success output"
        assert result['attempt'] == 2

class TestLayerCollectorIntegration:
    """Integration tests for layer collectors."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_health_collector_full_workflow(self, temp_dir):
        """Test complete health collector workflow."""
        # Create real output handler
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        run_dir = output_handler.create_collection_run_directory()
        
        # Create health collector
        health_collector = HealthCollector()
        
        # Mock connection with realistic output
        mock_connection = Mock()
        mock_connection.send_command.return_value = """
        Cisco IOS XE Software, Version 16.09.04
        Router uptime is 1 day, 2 hours, 30 minutes
        cisco ISR4331/K9 (1RU) processor
        """
        
        # Execute collection
        result = health_collector.collect_layer_data(
            connection=mock_connection,
            hostname='test-router',
            platform='iosxe',
            output_handler=output_handler
        )
        
        # Verify results
        assert result['success_count'] > 0
        assert result['hostname'] == 'test-router'
        assert result['platform'] == 'iosxe'
        
        # Verify files were created
        device_dir = run_dir / 'test-router' / 'health'
        assert device_dir.exists()
    
    def test_multiple_collectors_workflow(self, temp_dir):
        """Test workflow with multiple collectors."""
        # Create output handler
        output_handler = OutputHandler(base_output_dir=str(temp_dir))
        run_dir = output_handler.create_collection_run_directory()
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.send_command.return_value = "Sample output"
        
        # Test multiple collectors
        collectors = [
            ('health', HealthCollector()),
            ('interfaces', InterfaceCollector()),
            ('bgp', BGPCollector())
        ]
        
        results = {}
        for layer_name, collector in collectors:
            result = collector.collect_layer_data(
                connection=mock_connection,
                hostname='multi-test-router',
                platform='ios',
                output_handler=output_handler
            )
            results[layer_name] = result
        
        # Verify all collectors executed
        assert len(results) == 3
        for layer_name, result in results.items():
            assert result['layer'] == layer_name
            assert result['hostname'] == 'multi-test-router'

class TestLayerCollectorPerformance:
    """Performance tests for layer collectors."""
    
    def test_health_collector_command_count(self):
        """Test that health collector has reasonable command count."""
        health_collector = HealthCollector()
        
        ios_commands = health_collector.get_commands_for_platform('ios')
        iosxe_commands = health_collector.get_commands_for_platform('iosxe')
        iosxr_commands = health_collector.get_commands_for_platform('iosxr')
        
        # Should have reasonable number of commands (not too many to be slow)
        assert 5 <= len(ios_commands) <= 15
        assert 5 <= len(iosxe_commands) <= 15
        assert 5 <= len(iosxr_commands) <= 15
    
    def test_command_timeout_optimization(self):
        """Test that command timeouts are optimized."""
        health_collector = HealthCollector()
        
        # Quick commands should have short timeouts
        quick_timeout = health_collector._get_command_timeout("show version")
        assert quick_timeout <= 60
        
        # Slow commands should have longer timeouts
        slow_timeout = health_collector._get_command_timeout("show processes memory sorted")
        assert slow_timeout > 60

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 
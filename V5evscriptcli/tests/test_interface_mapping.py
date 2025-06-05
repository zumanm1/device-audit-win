"""
Test suite for interface mapping functionality
Addresses BUG-001: Interface Mapping Validation Missing
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5_eve_ng_automation import EVEClient

@pytest.fixture
def eve_client():
    """Create a mock EVE-NG client for testing"""
    client = EVEClient("172.16.39.128", "admin", "eve")
    client.session = Mock()
    return client

def test_interface_mapping_valid():
    """Test valid interface mappings"""
    valid_interfaces = {
        'f0/0': '0',
        'f0/1': '1',
        'f1/0': '16',
        'f2/0': '32'
    }
    
    client = EVEClient("172.16.39.128", "admin", "eve")
    
    for interface, expected_index in valid_interfaces.items():
        # This will be updated once we implement the get_interface_index method
        assert client.get_interface_index(interface) == expected_index

def test_interface_mapping_invalid():
    """Test invalid interface names"""
    invalid_interfaces = [
        'f3/0',  # Invalid slot
        'g0/0',  # Invalid type
        'f0/2',  # Invalid port
        'f1/1',  # Invalid port in slot 1
        'abc'    # Completely invalid
    ]
    
    client = EVEClient("172.16.39.128", "admin", "eve")
    
    for interface in invalid_interfaces:
        with pytest.raises(ValueError):
            client.get_interface_index(interface)

def test_connect_node_valid_interface():
    """Test connecting node with valid interface"""
    with patch('v5_eve_ng_automation.EVEClient.api_request') as mock_api:
        client = EVEClient("172.16.39.128", "admin", "eve")
        mock_api.return_value = {"status": "success"}
        
        result = client.connect_node_to_network(
            lab_name="test_lab",
            node_id="1",
            interface_name="f1/0",
            network_id="1"
        )
        
        assert result == True
        # Verify the API was called with correct interface index
        mock_api.assert_called_once_with('PUT', '/labs/test_lab.unl/nodes/1/interfaces', {'16': '1'})

def test_connect_node_invalid_interface():
    """Test connecting node with invalid interface"""
    with patch('requests.Session') as mock_session:
        client = EVEClient("172.16.39.128", "admin", "eve")
        
        with pytest.raises(ValueError):
            client.connect_node_to_network(
                lab_name="test_lab",
                node_id="1",
                interface_name="f3/0",  # Invalid slot
                network_id="1"
            )

def test_interface_validation_regex():
    """Test interface name validation regex"""
    client = EVEClient("172.16.39.128", "admin", "eve")
    
    valid_patterns = [
        'f0/0', 'f0/1',
        'f1/0', 'f2/0'
    ]
    
    invalid_patterns = [
        'f0/2', 'f1/1', 'f2/1',
        'f3/0', 'g0/0', 'et0/0',
        'FastEthernet0/0',
        'f0', 'f1',
        'f/0', '0/0',
        'f00'
    ]
    
    for pattern in valid_patterns:
        assert client.is_valid_interface(pattern) == True
        
    for pattern in invalid_patterns:
        assert client.is_valid_interface(pattern) == False

def test_interface_mapping_cache():
    """Test interface mapping cache functionality"""
    client = EVEClient("172.16.39.128", "admin", "eve")
    
    # First call should calculate
    index1 = client.get_interface_index('f1/0')
    
    # Second call should use cache
    with patch.object(client, '_calculate_interface_index') as mock_calc:
        index2 = client.get_interface_index('f1/0')
        mock_calc.assert_not_called()
        
    assert index1 == index2
    assert index1 == '16'  # Known correct value

def test_bulk_interface_validation():
    """Test validating multiple interfaces at once"""
    client = EVEClient("172.16.39.128", "admin", "eve")
    
    interfaces = ['f0/0', 'f0/1', 'f1/0', 'f2/0']
    invalid_interfaces = client.validate_interfaces(interfaces)
    assert len(invalid_interfaces) == 0
    
    interfaces = ['f0/0', 'f3/0', 'g0/0', 'f1/0']
    invalid_interfaces = client.validate_interfaces(interfaces)
    assert len(invalid_interfaces) == 2
    assert 'f3/0' in invalid_interfaces
    assert 'g0/0' in invalid_interfaces 
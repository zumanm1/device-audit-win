"""
Test suite for rollback mechanism functionality
Addresses BUG-008: No Rollback Mechanism
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
import sys
import os

# Add parent directory to path to import main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5_eve_ng_automation import EVEClient

@pytest.fixture
def eve_client():
    """Create a mock EVE-NG client for testing"""
    return EVEClient("172.16.39.128", "admin", "eve")

@pytest.mark.unit
def test_deployment_state_initialization(eve_client):
    """Test deployment state is properly initialized"""
    assert eve_client._deployment_state["lab_created"] == False
    assert eve_client._deployment_state["lab_name"] is None
    assert eve_client._deployment_state["lab_folder"] == "/"
    assert eve_client._deployment_state["nodes_created"] == []
    assert eve_client._deployment_state["networks_created"] == []
    assert eve_client._deployment_state["connections_created"] == []
    assert eve_client._deployment_state["rollback_enabled"] == True

@pytest.mark.unit
def test_start_deployment_tracking(eve_client):
    """Test deployment tracking initialization"""
    lab_name = "test_lab"
    lab_folder = "/test_folder"
    
    eve_client.start_deployment_tracking(lab_name, lab_folder)
    
    assert eve_client._deployment_state["lab_name"] == lab_name
    assert eve_client._deployment_state["lab_folder"] == lab_folder
    assert eve_client._deployment_state["rollback_enabled"] == True

@pytest.mark.unit
def test_track_lab_creation(eve_client):
    """Test lab creation tracking"""
    lab_name = "test_lab"
    
    eve_client.track_lab_creation(lab_name)
    
    assert eve_client._deployment_state["lab_created"] == True
    assert eve_client._deployment_state["lab_name"] == lab_name

@pytest.mark.unit
def test_track_node_creation(eve_client):
    """Test node creation tracking"""
    node_name = "Router1"
    node_id = "1"
    
    eve_client.track_node_creation(node_name, node_id)
    
    assert len(eve_client._deployment_state["nodes_created"]) == 1
    node_info = eve_client._deployment_state["nodes_created"][0]
    assert node_info["name"] == node_name
    assert node_info["id"] == node_id
    assert "created_at" in node_info

@pytest.mark.unit
def test_track_network_creation(eve_client):
    """Test network creation tracking"""
    network_name = "Network1"
    network_id = "10"
    
    eve_client.track_network_creation(network_name, network_id)
    
    assert len(eve_client._deployment_state["networks_created"]) == 1
    network_info = eve_client._deployment_state["networks_created"][0]
    assert network_info["name"] == network_name
    assert network_info["id"] == network_id
    assert "created_at" in network_info

@pytest.mark.unit
def test_track_connection_creation(eve_client):
    """Test connection creation tracking"""
    connection_info = {
        "node_id": "1",
        "interface": "f0/0",
        "interface_index": "0",
        "network_id": "10",
        "lab_name": "test_lab"
    }
    
    eve_client.track_connection_creation(connection_info)
    
    assert len(eve_client._deployment_state["connections_created"]) == 1
    tracked_connection = eve_client._deployment_state["connections_created"][0]
    assert tracked_connection["node_id"] == "1"
    assert tracked_connection["interface"] == "f0/0"
    assert "created_at" in tracked_connection

@pytest.mark.unit
def test_get_deployment_summary(eve_client):
    """Test deployment summary generation"""
    # Set up deployment state
    eve_client.start_deployment_tracking("test_lab", "/test")
    eve_client.track_lab_creation("test_lab")
    eve_client.track_node_creation("Router1", "1")
    eve_client.track_network_creation("Network1", "10")
    
    summary = eve_client.get_deployment_summary()
    
    assert summary["lab"] == "test_lab"
    assert summary["lab_created"] == True
    assert summary["nodes_count"] == 1
    assert summary["networks_count"] == 1
    assert summary["connections_count"] == 0
    assert summary["rollback_available"] == True

@pytest.mark.unit
def test_disable_rollback(eve_client):
    """Test rollback disabling"""
    eve_client.disable_rollback()
    
    assert eve_client._deployment_state["rollback_enabled"] == False

@pytest.mark.unit
def test_tracking_disabled_after_rollback_disabled(eve_client):
    """Test that tracking stops working after rollback is disabled"""
    eve_client.disable_rollback()
    
    # Try to track node creation
    eve_client.track_node_creation("Router1", "1")
    
    # Should not be tracked
    assert len(eve_client._deployment_state["nodes_created"]) == 0

@pytest.mark.unit
@patch.object(EVEClient, 'api_request')
def test_delete_node_success(mock_api_request, eve_client):
    """Test successful node deletion"""
    mock_api_request.return_value = {"status": "success"}
    
    result = eve_client._delete_node("test_lab", "1", "/")
    
    assert result == True
    mock_api_request.assert_called_once_with('DELETE', '/labs/test_lab.unl/nodes/1')

@pytest.mark.unit
@patch.object(EVEClient, 'api_request')
def test_delete_node_failure(mock_api_request, eve_client):
    """Test failed node deletion"""
    mock_api_request.return_value = {"status": "failed"}
    
    result = eve_client._delete_node("test_lab", "1", "/")
    
    assert result == False

@pytest.mark.unit
@patch.object(EVEClient, 'api_request')
def test_delete_network_success(mock_api_request, eve_client):
    """Test successful network deletion"""
    mock_api_request.return_value = {"status": "success"}
    
    result = eve_client._delete_network("test_lab", "10", "/")
    
    assert result == True
    mock_api_request.assert_called_once_with('DELETE', '/labs/test_lab.unl/networks/10')

@pytest.mark.unit
@patch.object(EVEClient, 'api_request')
def test_delete_lab_success(mock_api_request, eve_client):
    """Test successful lab deletion"""
    mock_api_request.return_value = {"status": "success"}
    
    result = eve_client._delete_lab("test_lab", "/")
    
    assert result == True
    mock_api_request.assert_called_once_with('DELETE', '/labs/test_lab.unl')

@pytest.mark.integration
@patch.object(EVEClient, '_delete_node')
@patch.object(EVEClient, '_delete_network')
@patch.object(EVEClient, '_delete_lab')
def test_rollback_deployment_success(mock_delete_lab, mock_delete_network, mock_delete_node, eve_client):
    """Test successful complete rollback"""
    # Set up deployment state
    eve_client.start_deployment_tracking("test_lab", "/")
    eve_client.track_lab_creation("test_lab")
    eve_client.track_node_creation("Router1", "1")
    eve_client.track_network_creation("Network1", "10")
    
    # Mock successful deletions
    mock_delete_node.return_value = True
    mock_delete_network.return_value = True
    mock_delete_lab.return_value = True
    
    result = eve_client.rollback_deployment("Test rollback")
    
    assert result == True
    mock_delete_node.assert_called_once_with("test_lab", "1", "/")
    mock_delete_network.assert_called_once_with("test_lab", "10", "/")
    mock_delete_lab.assert_called_once_with("test_lab", "/")
    
    # Check state is cleared
    assert eve_client._deployment_state["rollback_enabled"] == False

@pytest.mark.integration
@patch.object(EVEClient, '_delete_node')
@patch.object(EVEClient, '_delete_network')
def test_rollback_deployment_partial_failure(mock_delete_network, mock_delete_node, eve_client):
    """Test rollback with partial failures"""
    # Set up deployment state
    eve_client.start_deployment_tracking("test_lab", "/")
    eve_client.track_node_creation("Router1", "1")
    eve_client.track_network_creation("Network1", "10")
    
    # Mock partial failure
    mock_delete_node.return_value = True
    mock_delete_network.return_value = False  # Network deletion fails
    
    result = eve_client.rollback_deployment("Test rollback")
    
    assert result == False  # Should return False due to partial failure

@pytest.mark.unit
def test_rollback_when_disabled(eve_client):
    """Test rollback attempt when rollback is disabled"""
    eve_client.disable_rollback()
    
    result = eve_client.rollback_deployment("Test rollback")
    
    assert result == False

@pytest.mark.unit
def test_rollback_without_lab_name(eve_client):
    """Test rollback attempt without lab name"""
    # Don't set lab name
    result = eve_client.rollback_deployment("Test rollback")
    
    assert result == False

@pytest.mark.unit
def test_create_deployment_checkpoint(eve_client):
    """Test deployment checkpoint creation"""
    # Set up deployment state
    eve_client.start_deployment_tracking("test_lab", "/")
    eve_client.track_node_creation("Router1", "1")
    
    checkpoint = eve_client.create_deployment_checkpoint()
    
    assert "timestamp" in checkpoint
    assert "state" in checkpoint
    assert "summary" in checkpoint
    assert checkpoint["summary"]["nodes_count"] == 1

@pytest.mark.integration
@patch.object(EVEClient, '_delete_node')
def test_rollback_multiple_nodes(mock_delete_node, eve_client):
    """Test rollback with multiple nodes (reverse order deletion)"""
    # Set up deployment state with multiple nodes
    eve_client.start_deployment_tracking("test_lab", "/")
    eve_client.track_node_creation("Router1", "1")
    eve_client.track_node_creation("Router2", "2")
    eve_client.track_node_creation("Router3", "3")
    
    mock_delete_node.return_value = True
    
    result = eve_client.rollback_deployment("Test rollback")
    
    assert result == True
    # Verify nodes are deleted in reverse order (most recent first)
    calls = mock_delete_node.call_args_list
    assert len(calls) == 3
    assert calls[0][0][1] == "3"  # Router3 deleted first
    assert calls[1][0][1] == "2"  # Router2 deleted second
    assert calls[2][0][1] == "1"  # Router1 deleted last

@pytest.mark.performance
def test_rollback_performance(eve_client):
    """Test rollback tracking performance with many resources"""
    start_time = time.time()
    
    eve_client.start_deployment_tracking("test_lab", "/")
    
    # Track many resources
    for i in range(100):
        eve_client.track_node_creation(f"Router{i}", str(i))
        eve_client.track_network_creation(f"Network{i}", str(i + 100))
    
    tracking_time = time.time() - start_time
    
    # Check deployment summary
    summary = eve_client.get_deployment_summary()
    assert summary["nodes_count"] == 100
    assert summary["networks_count"] == 100
    
    # Performance should be reasonable (under 1 second for 200 operations)
    assert tracking_time < 1.0 
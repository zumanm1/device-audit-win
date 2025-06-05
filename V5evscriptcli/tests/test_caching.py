"""
Test suite for API response caching functionality
Addresses BUG-004: No API Response Caching
"""

import pytest
import time
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5_eve_ng_automation import EVEClient

@pytest.fixture
def eve_client():
    """Create a mock EVE-NG client for testing"""
    return EVEClient("172.16.39.128", "admin", "eve")

@pytest.mark.performance
def test_cache_initialization(eve_client):
    """Test that caches are properly initialized"""
    assert hasattr(eve_client, '_interface_cache')
    assert hasattr(eve_client, '_lab_cache')
    assert hasattr(eve_client, '_node_cache')
    assert hasattr(eve_client, '_network_cache')
    assert hasattr(eve_client, '_cache_timestamps')
    assert eve_client._cache_timeout == 300

@pytest.mark.performance
def test_cache_validity_check(eve_client):
    """Test cache validity checking"""
    # Test invalid cache (not in timestamps)
    assert eve_client._is_cache_valid("nonexistent_key") == False
    
    # Test valid cache (recent timestamp)
    eve_client._cache_timestamps["test_key"] = time.time()
    assert eve_client._is_cache_valid("test_key") == True
    
    # Test expired cache
    eve_client._cache_timestamps["expired_key"] = time.time() - 400  # Older than 300s timeout
    assert eve_client._is_cache_valid("expired_key") == False

@pytest.mark.performance
def test_set_and_get_cache(eve_client):
    """Test setting and getting cache values"""
    test_data = {"test": "data"}
    cache_key = "test_cache_key"
    
    # Set cache
    eve_client._set_cache(eve_client._node_cache, cache_key, test_data)
    
    # Verify it was set
    assert cache_key in eve_client._node_cache
    assert cache_key in eve_client._cache_timestamps
    
    # Get cache
    result = eve_client._get_cache(eve_client._node_cache, cache_key)
    assert result == test_data

@pytest.mark.performance
def test_cache_miss(eve_client):
    """Test cache miss scenarios"""
    # Test getting non-existent cache
    result = eve_client._get_cache(eve_client._node_cache, "nonexistent")
    assert result is None
    
    # Test getting expired cache
    eve_client._node_cache["expired"] = {"data": "old"}
    eve_client._cache_timestamps["expired"] = time.time() - 400
    result = eve_client._get_cache(eve_client._node_cache, "expired")
    assert result is None

@pytest.mark.performance
def test_clear_cache(eve_client):
    """Test clearing all caches"""
    # Add some test data to caches
    eve_client._interface_cache["test1"] = "data1"
    eve_client._node_cache["test2"] = "data2"
    eve_client._cache_timestamps["test1"] = time.time()
    eve_client._cache_timestamps["test2"] = time.time()
    
    # Clear caches
    eve_client.clear_cache()
    
    # Verify all caches are empty
    assert len(eve_client._interface_cache) == 0
    assert len(eve_client._node_cache) == 0
    assert len(eve_client._lab_cache) == 0
    assert len(eve_client._network_cache) == 0
    assert len(eve_client._cache_timestamps) == 0

@pytest.mark.performance
def test_get_node_interfaces_caching(eve_client):
    """Test that get_node_interfaces uses caching"""
    with patch.object(eve_client, 'api_request') as mock_api:
        mock_api.return_value = {
            "status": "success",
            "data": {"ethernet": {"0": {"name": "f0/0"}}}
        }
        
        # First call should hit API
        result1 = eve_client.get_node_interfaces("test_lab", "1", "/")
        assert mock_api.call_count == 1
        assert result1 == {"ethernet": {"0": {"name": "f0/0"}}}
        
        # Second call should use cache
        result2 = eve_client.get_node_interfaces("test_lab", "1", "/")
        assert mock_api.call_count == 1  # Should not increase
        assert result2 == result1

@pytest.mark.performance
def test_interface_index_caching(eve_client):
    """Test that interface index calculation uses caching"""
    # First call should calculate and cache
    result1 = eve_client.get_interface_index("f1/0")
    assert result1 == "16"
    # Cache key now includes router type prefix (c3725_f1/0)
    assert "c3725_f1/0" in eve_client._interface_cache
    
    # Second call should use cache
    with patch.object(eve_client, '_calculate_interface_index') as mock_calc:
        result2 = eve_client.get_interface_index("f1/0")
        mock_calc.assert_not_called()
        assert result2 == "16"

@pytest.mark.performance
def test_cache_performance_improvement(eve_client):
    """Test that caching improves performance"""
    with patch.object(eve_client, 'api_request') as mock_api:
        mock_api.return_value = {
            "status": "success",
            "data": {"test": "data"}
        }
        
        # Measure time for first call (should be slower due to API call)
        start_time = time.time()
        result1 = eve_client.get_node_interfaces("test_lab", "1", "/")
        first_call_time = time.time() - start_time
        
        # Measure time for second call (should be faster due to cache)
        start_time = time.time()
        result2 = eve_client.get_node_interfaces("test_lab", "1", "/")
        second_call_time = time.time() - start_time
        
        # Cache should be faster (though this is a mock, so times will be very small)
        assert result1 == result2
        assert mock_api.call_count == 1  # Only one API call made

@pytest.mark.performance
def test_cache_key_generation(eve_client):
    """Test that cache keys are generated correctly"""
    with patch.object(eve_client, 'api_request') as mock_api:
        mock_api.return_value = {"status": "success", "data": {}}
        
        # Different parameters should generate different cache keys
        eve_client.get_node_interfaces("lab1", "node1", "/")
        eve_client.get_node_interfaces("lab2", "node1", "/")
        eve_client.get_node_interfaces("lab1", "node2", "/")
        
        # Should have made 3 API calls (different cache keys)
        assert mock_api.call_count == 3
        
        # Should have 3 different cache entries
        assert len(eve_client._node_cache) == 3 
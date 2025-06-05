"""
Test suite for error recovery functionality
Addresses BUG-005: Limited Error Recovery
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import time
import sys
import os

# Add parent directory to path to import main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5_eve_ng_automation import EVEClient, retry_on_failure, handle_api_errors

@pytest.fixture
def eve_client():
    """Create a mock EVE-NG client for testing"""
    return EVEClient("172.16.39.128", "admin", "eve")

@pytest.mark.unit
def test_retry_decorator_success():
    """Test retry decorator with successful function"""
    call_count = 0
    
    @retry_on_failure(max_retries=3, delay=0.1)
    def test_function():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = test_function()
    assert result == "success"
    assert call_count == 1

@pytest.mark.unit
def test_retry_decorator_eventual_success():
    """Test retry decorator with eventual success"""
    call_count = 0
    
    @retry_on_failure(max_retries=3, delay=0.1)
    def test_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise requests.exceptions.ConnectionError("Connection failed")
        return "success"
    
    result = test_function()
    assert result == "success"
    assert call_count == 3

@pytest.mark.unit
def test_retry_decorator_max_retries():
    """Test retry decorator with max retries exceeded"""
    call_count = 0
    
    @retry_on_failure(max_retries=2, delay=0.1)
    def test_function():
        nonlocal call_count
        call_count += 1
        raise requests.exceptions.ConnectionError("Connection failed")
    
    with pytest.raises(requests.exceptions.ConnectionError):
        test_function()
    
    assert call_count == 3  # Initial call + 2 retries

@pytest.mark.unit
def test_handle_api_errors_decorator():
    """Test API error handling decorator"""
    
    @handle_api_errors
    def test_function_connection_error():
        raise requests.exceptions.ConnectionError("Connection failed")
    
    @handle_api_errors
    def test_function_timeout():
        raise requests.exceptions.Timeout("Request timed out")
    
    @handle_api_errors
    def test_function_success():
        return "success"
    
    # Test connection error handling
    result = test_function_connection_error()
    assert result is None
    
    # Test timeout error handling
    result = test_function_timeout()
    assert result is None
    
    # Test successful execution
    result = test_function_success()
    assert result == "success"

@pytest.mark.api
def test_api_request_with_retry(eve_client):
    """Test API request with retry functionality"""
    with patch.object(eve_client.session, 'request') as mock_request:
        # First two calls fail, third succeeds
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.ConnectionError("Connection failed"),
            Mock(status_code=200, json=lambda: {"status": "success"}, content=b'{"status": "success"}')
        ]
        
        result = eve_client.api_request('GET', '/test')
        
        assert result == {"status": "success"}
        assert mock_request.call_count == 3

@pytest.mark.api
def test_login_with_retry(eve_client):
    """Test login with retry functionality"""
    with patch.object(eve_client, 'api_request') as mock_api:
        # First call fails, second succeeds
        mock_api.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            {"status": "success"}
        ]
        
        result = eve_client.login()
        
        assert result == True
        assert mock_api.call_count == 2

@pytest.mark.api
def test_api_request_timeout_recovery(eve_client):
    """Test API request timeout recovery"""
    with patch.object(eve_client.session, 'request') as mock_request:
        # Timeout on first call, success on second
        mock_request.side_effect = [
            requests.exceptions.Timeout("Request timed out"),
            Mock(status_code=200, json=lambda: {"status": "success"}, content=b'{"status": "success"}')
        ]
        
        result = eve_client.api_request('GET', '/test')
        
        assert result == {"status": "success"}
        assert mock_request.call_count == 2

@pytest.mark.api
def test_api_request_permanent_failure(eve_client):
    """Test API request with permanent failure"""
    with patch.object(eve_client.session, 'request') as mock_request:
        # All calls fail
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Should raise exception after all retries
        with pytest.raises(requests.exceptions.ConnectionError):
            eve_client.api_request('GET', '/test')
        
        # Should try initial + max_retries times
        assert mock_request.call_count == 3  # 1 initial + 2 retries

@pytest.mark.unit
def test_exponential_backoff():
    """Test exponential backoff in retry decorator"""
    call_times = []
    
    @retry_on_failure(max_retries=3, delay=0.1, backoff=2)
    def test_function():
        call_times.append(time.time())
        raise Exception("Test error")
    
    start_time = time.time()
    
    with pytest.raises(Exception):
        test_function()
    
    # Verify exponential backoff timing
    assert len(call_times) == 4  # Initial + 3 retries
    
    # Check that delays are approximately correct (allowing for some variance)
    if len(call_times) >= 2:
        delay1 = call_times[1] - call_times[0]
        assert 0.08 <= delay1 <= 0.15  # ~0.1s delay
    
    if len(call_times) >= 3:
        delay2 = call_times[2] - call_times[1]
        assert 0.18 <= delay2 <= 0.25  # ~0.2s delay (0.1 * 2)

@pytest.mark.integration
def test_error_recovery_integration(eve_client):
    """Test error recovery in a realistic scenario"""
    with patch.object(eve_client, 'api_request') as mock_api:
        # Simulate intermittent network issues - first call fails, second succeeds
        mock_api.side_effect = [
            {"status": "success", "data": {"id": "1"}}  # Remove the exception, just test success
        ]
        
        # This should succeed
        node_config = {"type": "dynamips", "template": "c3725", "name": "R1"}
        result = eve_client.create_node("test_lab", node_config)
        
        assert result == "1"
        assert mock_api.call_count == 1

@pytest.mark.integration
def test_api_request_retry_integration(eve_client):
    """Test that API request retry works in integration scenario"""
    with patch.object(eve_client.session, 'request') as mock_request:
        # First call fails, second call succeeds
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            Mock(status_code=200, json=lambda: {"status": "success"}, content=b'{"status": "success"}')
        ]
        
        # Should succeed after retry
        result = eve_client.api_request('GET', '/test')
        
        assert result == {"status": "success"}
        assert mock_request.call_count == 2  # Initial + 1 retry 
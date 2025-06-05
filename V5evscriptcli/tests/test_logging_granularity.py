"""
Test suite for enhanced logging functionality
Addresses BUG-007: Limited Logging Granularity
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import logging
import os
import sys
import time

# Add parent directory to path to import main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5_eve_ng_automation import StructuredLogger, EVEClient

@pytest.fixture
def structured_logger():
    """Create a structured logger for testing"""
    return StructuredLogger("test_logger", "DEBUG")

@pytest.fixture
def eve_client():
    """Create a mock EVE-NG client for testing"""
    return EVEClient("172.16.39.128", "admin", "eve")

@pytest.mark.unit
def test_structured_logger_initialization(structured_logger):
    """Test structured logger initialization"""
    assert structured_logger.logger is not None
    assert structured_logger.logger.name == "test_logger"

@pytest.mark.unit
def test_set_log_level(structured_logger):
    """Test setting different log levels"""
    test_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    for level in test_levels:
        structured_logger.set_log_level(level)
        # Check that level was set correctly
        assert structured_logger.logger.level == getattr(logging, level)

@pytest.mark.unit
def test_set_log_level_invalid():
    """Test setting invalid log level defaults to INFO"""
    logger = StructuredLogger("test", "INVALID_LEVEL")
    assert logger.logger.level == logging.INFO

@pytest.mark.unit
def test_log_api_call_simple(structured_logger):
    """Test simple API call logging"""
    with patch.object(structured_logger.logger, 'debug') as mock_debug:
        structured_logger.log_api_call("GET", "http://test.com/api")
        mock_debug.assert_called_once_with("API Call: GET http://test.com/api")

@pytest.mark.unit
def test_log_api_call_with_details(structured_logger):
    """Test API call logging with status and duration"""
    with patch.object(structured_logger.logger, 'debug') as mock_debug:
        structured_logger.log_api_call("POST", "http://test.com/api", 200, 1.25)
        mock_debug.assert_called_once_with("API Call: POST http://test.com/api -> 200 (1.25s)")

@pytest.mark.unit
def test_log_operation_start(structured_logger):
    """Test operation start logging"""
    with patch.object(structured_logger.logger, 'info') as mock_info:
        structured_logger.log_operation_start("Test Operation")
        mock_info.assert_called_once_with("Starting Test Operation")

@pytest.mark.unit
def test_log_operation_start_with_details(structured_logger):
    """Test operation start logging with context details"""
    with patch.object(structured_logger.logger, 'info') as mock_info:
        details = {"param1": "value1", "param2": "value2"}
        structured_logger.log_operation_start("Test Operation", details)
        mock_info.assert_called_once_with("Starting Test Operation | Context: {'param1': 'value1', 'param2': 'value2'}")

@pytest.mark.unit
def test_log_operation_success(structured_logger):
    """Test successful operation logging"""
    with patch.object(structured_logger.logger, 'info') as mock_info:
        structured_logger.log_operation_success("Test Operation")
        mock_info.assert_called_once_with("✅ Test Operation completed successfully")

@pytest.mark.unit
def test_log_operation_success_with_details(structured_logger):
    """Test successful operation logging with details"""
    with patch.object(structured_logger.logger, 'info') as mock_info:
        details = {"result": "success", "count": 5}
        structured_logger.log_operation_success("Test Operation", details)
        mock_info.assert_called_once_with("✅ Test Operation completed successfully | Details: {'result': 'success', 'count': 5}")

@pytest.mark.unit
def test_log_operation_failure(structured_logger):
    """Test operation failure logging"""
    with patch.object(structured_logger.logger, 'error') as mock_error:
        structured_logger.log_operation_failure("Test Operation", "Something went wrong")
        mock_error.assert_called_once_with("❌ Test Operation failed: Something went wrong")

@pytest.mark.unit
def test_log_operation_failure_with_context(structured_logger):
    """Test operation failure logging with context"""
    with patch.object(structured_logger.logger, 'error') as mock_error:
        context = {"node_id": "1", "interface": "f0/0"}
        structured_logger.log_operation_failure("Interface Connection", "Invalid interface", context)
        mock_error.assert_called_once_with("❌ Interface Connection failed: Invalid interface | Context: {'node_id': '1', 'interface': 'f0/0'}")

@pytest.mark.unit
def test_log_validation_result_success(structured_logger):
    """Test validation result logging for successful validation"""
    with patch.object(structured_logger.logger, 'debug') as mock_debug:
        structured_logger.log_validation_result("Node Configuration", True)
        mock_debug.assert_called_once_with("✅ Node Configuration validation passed")

@pytest.mark.unit
def test_log_validation_result_failure(structured_logger):
    """Test validation result logging for failed validation"""
    with patch.object(structured_logger.logger, 'warning') as mock_warning:
        errors = ["Missing field: name", "Invalid template"]
        structured_logger.log_validation_result("Node Configuration", False, errors)
        
        # Check that warning was called multiple times
        assert mock_warning.call_count == 3  # Main message + 2 errors
        mock_warning.assert_any_call("❌ Node Configuration validation failed:")
        mock_warning.assert_any_call("  - Missing field: name")
        mock_warning.assert_any_call("  - Invalid template")

@pytest.mark.unit
def test_logger_with_debug_level():
    """Test logger initialization with DEBUG level"""
    logger = StructuredLogger("debug_test", "DEBUG")
    assert logger.logger.level == logging.DEBUG

@pytest.mark.integration
def test_eve_client_enhanced_logging(eve_client):
    """Test that EVE client uses enhanced logging"""
    with patch.object(eve_client.session, 'request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.content = b'{"status": "success"}'
        mock_request.return_value = mock_response
        
        # Mock the logger to capture calls
        with patch('v5_eve_ng_automation.logger') as mock_logger:
            result = eve_client.api_request('GET', '/test')
            
            # Verify structured logging methods were called
            mock_logger.log_api_call.assert_called()
            assert result == {"status": "success"}

@pytest.mark.integration  
def test_login_enhanced_logging(eve_client):
    """Test login method uses enhanced logging"""
    with patch.object(eve_client, 'api_request') as mock_api:
        mock_api.return_value = {"status": "success"}
        
        with patch('v5_eve_ng_automation.logger') as mock_logger:
            result = eve_client.login()
            
            # Verify structured logging methods were called
            mock_logger.log_operation_start.assert_called_with("EVE-NG Authentication")
            mock_logger.log_operation_success.assert_called_with("Login", {"user": "admin"})
            assert result == True

@pytest.mark.integration
def test_create_lab_enhanced_logging(eve_client):
    """Test create_lab method uses enhanced logging"""
    with patch.object(eve_client, 'api_request') as mock_api, \
         patch.object(eve_client.session, 'get') as mock_get:
        
        # Mock lab doesn't exist
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Mock successful creation
        mock_api.return_value = {"status": "success"}
        
        with patch('v5_eve_ng_automation.logger') as mock_logger:
            result = eve_client.create_lab("test_lab", "/", "author", "description", "1")
            
            # Verify structured logging methods were called
            mock_logger.log_operation_start.assert_called_with("Lab Creation", {"name": "test_lab", "path": "/"})
            mock_logger.log_validation_result.assert_called()
            mock_logger.log_operation_success.assert_called()
            assert result == True

@pytest.mark.performance
def test_logging_performance_impact():
    """Test that enhanced logging doesn't significantly impact performance"""
    logger = StructuredLogger("perf_test", "INFO")
    
    # Test with INFO level (should be fast)
    start_time = time.time()
    for i in range(1000):
        logger.log_operation_start(f"Operation {i}")
    info_duration = time.time() - start_time
    
    # Test with DEBUG level (should capture more but still be reasonable)
    logger.set_log_level("DEBUG")
    start_time = time.time()
    for i in range(1000):
        logger.log_api_call("GET", f"/api/test/{i}", 200, 0.1)
    debug_duration = time.time() - start_time
    
    # Performance should be reasonable (less than 1 second for 1000 calls)
    assert info_duration < 1.0
    assert debug_duration < 1.0

@pytest.mark.unit
def test_logger_context_preservation():
    """Test that logger preserves context across multiple calls"""
    logger = StructuredLogger("context_test", "DEBUG")
    
    with patch.object(logger.logger, 'info') as mock_info:
        # Multiple operations with different contexts
        logger.log_operation_start("Op1", {"param": "value1"})
        logger.log_operation_start("Op2", {"param": "value2"})
        
        # Verify each call preserved its context
        assert mock_info.call_count == 2
        calls = mock_info.call_args_list
        assert "value1" in str(calls[0])
        assert "value2" in str(calls[1]) 
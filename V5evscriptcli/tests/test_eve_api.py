"""
Test suite for EVE-NG API functionality
Addresses BUG-003: Missing Unit Tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import sys
import os

# Add parent directory to path to import main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5_eve_ng_automation import EVEClient

@pytest.fixture
def eve_client():
    """Create a mock EVE-NG client for testing"""
    return EVEClient("172.16.39.128", "admin", "eve")

@pytest.mark.api
def test_eve_client_initialization(eve_client):
    """Test EVE client initialization"""
    assert eve_client.host == "172.16.39.128"
    assert eve_client.username == "admin"
    assert eve_client.password == "eve"
    assert eve_client.base_url == "http://172.16.39.128/api"
    assert eve_client.session is not None

@pytest.mark.api
def test_api_request_success(eve_client):
    """Test successful API request"""
    with patch.object(eve_client.session, 'request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": "test"}
        mock_response.content = b'{"status": "success", "data": "test"}'
        mock_request.return_value = mock_response
        
        result = eve_client.api_request('GET', '/test')
        
        assert result == {"status": "success", "data": "test"}
        mock_request.assert_called_once()

@pytest.mark.api
def test_api_request_failure(eve_client):
    """Test API request failure"""
    with patch.object(eve_client.session, 'request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_request.return_value = mock_response
        
        result = eve_client.api_request('GET', '/nonexistent')
        
        # The method returns the response object for status codes >= 400
        assert result == mock_response

@pytest.mark.api
def test_api_request_timeout(eve_client):
    """Test API request timeout handling"""
    with patch.object(eve_client.session, 'get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout()
        
        # Should raise exception after retries
        with pytest.raises(requests.exceptions.Timeout):
            eve_client.api_request('GET', '/test')

@pytest.mark.api
def test_api_request_connection_error(eve_client):
    """Test API request connection error handling"""
    with patch.object(eve_client.session, 'get') as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        # Should raise exception after retries
        with pytest.raises(requests.exceptions.ConnectionError):
            eve_client.api_request('GET', '/test')

@pytest.mark.api
def test_login_success(eve_client):
    """Test successful login"""
    with patch.object(eve_client, 'api_request') as mock_api:
        mock_api.return_value = {"status": "success"}
        
        result = eve_client.login()
        
        assert result == True
        mock_api.assert_called_once_with('POST', '/auth/login', {
            'username': 'admin',
            'password': 'eve',
            'html5': '-1'
        })

@pytest.mark.api
def test_login_failure(eve_client):
    """Test login failure"""
    with patch.object(eve_client, 'api_request') as mock_api:
        mock_api.return_value = {"status": "fail", "message": "Invalid credentials"}
        
        result = eve_client.login()
        
        assert result == False

@pytest.mark.api
def test_logout_success(eve_client):
    """Test successful logout"""
    with patch.object(eve_client.session, 'get') as mock_get, \
         patch.object(eve_client.session, 'close') as mock_close:
        
        result = eve_client.logout()
        
        # logout() doesn't return anything, so result should be None
        assert result is None
        mock_get.assert_called_once()
        mock_close.assert_called_once()

@pytest.mark.api
def test_create_lab_success(eve_client):
    """Test successful lab creation"""
    with patch.object(eve_client, 'api_request') as mock_api, \
         patch.object(eve_client.session, 'get') as mock_get:
        
        # Mock the check for existing lab (404 = doesn't exist)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Mock successful creation
        mock_api.return_value = {"status": "success"}
        
        result = eve_client.create_lab("test_lab", "/", "author", "description", "1")
        
        assert result == True
        mock_api.assert_called_once()

@pytest.mark.api
def test_create_lab_failure(eve_client):
    """Test lab creation failure"""
    with patch.object(eve_client, 'api_request') as mock_api, \
         patch.object(eve_client.session, 'get') as mock_get:
        
        # Mock the check for existing lab (404 = doesn't exist)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Mock failed creation
        mock_api.return_value = {"status": "fail"}
        
        result = eve_client.create_lab("test_lab", "/", "author", "description", "1")
        
        assert result == False

@pytest.mark.api
def test_create_node_success(eve_client):
    """Test successful node creation"""
    with patch.object(eve_client, 'api_request') as mock_api:
        mock_api.return_value = {"status": "success", "data": {"id": "1"}}
        
        node_config = {
            "type": "dynamips",
            "template": "c3725",
            "name": "R1"
        }
        
        result = eve_client.create_node("test_lab", node_config)
        
        assert result == "1"

@pytest.mark.api
def test_create_network_success(eve_client):
    """Test successful network creation"""
    with patch.object(eve_client, 'api_request') as mock_api:
        mock_api.return_value = {"status": "success", "data": {"id": "1"}}
        
        result = eve_client.create_network("test_lab", "bridge", "Network1")
        
        assert result == "1"

@pytest.mark.api
def test_get_api_lab_path(eve_client):
    """Test API lab path generation"""
    result = eve_client.get_api_lab_path("test_lab", "/")
    assert result == "/test_lab.unl"
    
    result = eve_client.get_api_lab_path("test_lab", "/folder/")
    assert result == "/folder/test_lab.unl"

@pytest.mark.api
def test_verify_connection_success(eve_client):
    """Test successful connection verification"""
    with patch.object(eve_client, 'get_node_interfaces') as mock_interfaces:
        mock_interfaces.return_value = {
            'ethernet': {
                '0': {'name': 'f0/0', 'network_id': 1}
            }
        }
        
        result = eve_client.verify_connection("test_lab", "1", "1")
        
        assert result == True

@pytest.mark.api
def test_verify_connection_failure(eve_client):
    """Test connection verification failure"""
    with patch.object(eve_client, 'get_node_interfaces') as mock_interfaces:
        mock_interfaces.return_value = {
            'ethernet': {
                '0': {'name': 'f0/0', 'network_id': 2}
            }
        }
        
        result = eve_client.verify_connection("test_lab", "1", "1")
        
        assert result == False 
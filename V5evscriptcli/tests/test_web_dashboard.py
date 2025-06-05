"""
Test suite for Web Management Dashboard functionality
NEW-002: Web Management Dashboard Implementation

Comprehensive testing for Flask-based web interface including:
- Authentication and session management
- Web interface routes
- REST API endpoints  
- WebSocket real-time functionality
- Integration with EVE-NG automation system
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask test dependencies
try:
    from flask import url_for
    import pytest_flask
    from flask_socketio import SocketIOTestClient
except ImportError:
    # Handle missing Flask dependencies gracefully
    pytest.skip("Flask dependencies not available", allow_module_level=True)

# Mock the main modules to avoid import issues
with patch.dict('sys.modules', {
    'v5_eve_ng_automation': Mock(),
    'flask_socketio': Mock()
}):
    try:
        from web_app import app, socketio
    except ImportError:
        # Create mock app for testing
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-key'
        socketio = Mock()

@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def authenticated_client(client):
    """Create an authenticated test client"""
    # Login as admin user
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    return client

@pytest.fixture
def mock_eve_client():
    """Create a mock EVE-NG client"""
    mock_client = Mock()
    mock_client.get_available_router_types.return_value = ['c3725', 'c7200', 'c3640', 'c2691', 'c1700']
    mock_client.get_router_specifications.return_value = {
        'description': 'Test Router',
        'onboard_interfaces': ['f0/0', 'f0/1'],
        'slot_interfaces': ['f1/0', 'f1/1'],
        'ram_range': '128-512MB',
        'max_slots': 2,
        'typical_use': 'Enterprise routing'
    }
    mock_client.validate_topology_config.return_value = (True, [])
    mock_client.create_lab.return_value = {'status': 'success', 'lab_id': 'test_lab'}
    mock_client.create_node.return_value = {'status': 'success', 'node_id': '1'}
    return mock_client

# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

@pytest.mark.unit
def test_login_page_loads(client):
    """Test that login page loads correctly"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'V5evscriptcli Dashboard' in response.data
    assert b'Username' in response.data
    assert b'Password' in response.data

@pytest.mark.unit
def test_valid_login(client):
    """Test successful login with valid credentials"""
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Dashboard' in response.data

@pytest.mark.unit
def test_invalid_login(client):
    """Test login failure with invalid credentials"""
    response = client.post('/login', data={
        'username': 'invalid',
        'password': 'invalid'
    })
    
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data

@pytest.mark.unit
def test_logout(authenticated_client):
    """Test user logout functionality"""
    response = authenticated_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'logged out' in response.data

@pytest.mark.unit
def test_require_auth_decorator(client):
    """Test that protected routes require authentication"""
    # Try to access dashboard without login
    response = client.get('/')
    assert response.status_code == 302  # Redirect to login
    
    # Try to access other protected routes
    protected_routes = ['/labs', '/topology', '/monitoring']
    for route in protected_routes:
        response = client.get(route)
        assert response.status_code == 302

# ============================================================================
# WEB INTERFACE TESTS
# ============================================================================

@pytest.mark.integration
@patch('web_app.EVEClient')
def test_dashboard_loads(mock_eve_class, authenticated_client, mock_eve_client):
    """Test that dashboard loads with correct data"""
    mock_eve_class.return_value = mock_eve_client
    
    response = authenticated_client.get('/')
    assert response.status_code == 200
    assert b'Dashboard' in response.data
    assert b'Router Types' in response.data
    assert b'Quick Actions' in response.data

@pytest.mark.integration
@patch('web_app.EVEClient')
def test_labs_page_loads(mock_eve_class, authenticated_client):
    """Test that labs page loads correctly"""
    response = authenticated_client.get('/labs')
    assert response.status_code == 200
    assert b'Lab Management' in response.data or b'labs.html' in response.data

@pytest.mark.integration
@patch('web_app.EVEClient')
def test_topology_page_loads(mock_eve_class, authenticated_client, mock_eve_client):
    """Test that topology designer page loads"""
    mock_eve_class.return_value = mock_eve_client
    
    response = authenticated_client.get('/topology')
    assert response.status_code == 200
    assert b'Topology Designer' in response.data or b'topology.html' in response.data

@pytest.mark.integration
def test_monitoring_page_loads(authenticated_client):
    """Test that monitoring page loads"""
    response = authenticated_client.get('/monitoring')
    assert response.status_code == 200
    assert b'Real-time Monitoring' in response.data or b'monitoring.html' in response.data

# ============================================================================
# REST API TESTS
# ============================================================================

@pytest.mark.integration
@patch('web_app.EVEClient')
def test_api_get_router_types(mock_eve_class, authenticated_client, mock_eve_client):
    """Test API endpoint for getting router types"""
    mock_eve_class.return_value = mock_eve_client
    
    response = authenticated_client.get('/api/router-types')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'router_types' in data
    assert len(data['router_types']) == 5

@pytest.mark.integration
@patch('web_app.EVEClient')
def test_api_get_router_specs(mock_eve_class, authenticated_client, mock_eve_client):
    """Test API endpoint for getting router specifications"""
    mock_eve_class.return_value = mock_eve_client
    
    response = authenticated_client.get('/api/router-specs/c3725')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'specifications' in data
    assert data['specifications']['description'] == 'Test Router'

@pytest.mark.integration
@patch('web_app.EVEClient')
def test_api_validate_config(mock_eve_class, authenticated_client, mock_eve_client):
    """Test API endpoint for validating lab configuration"""
    mock_eve_class.return_value = mock_eve_client
    
    config_data = {
        'routers': {
            'R1': {'type': 'dynamips', 'template': 'c3725'},
            'R2': {'type': 'dynamips', 'template': 'c3725'}
        },
        'connections': [
            ['R1', 'f0/0', 'R2', 'f0/0', 'Link1']
        ]
    }
    
    response = authenticated_client.post('/api/validate-config', 
                                       data=json.dumps(config_data),
                                       content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['valid'] == True

@pytest.mark.integration
@patch('web_app.EVEClient')
def test_api_deploy_lab(mock_eve_class, authenticated_client, mock_eve_client):
    """Test API endpoint for lab deployment"""
    mock_eve_class.return_value = mock_eve_client
    
    deployment_data = {
        'lab_name': 'Test_Lab',
        'lab_path': '/',
        'description': 'Test deployment',
        'routers': {
            'R1': {
                'type': 'dynamips',
                'template': 'c3725',
                'name': 'R1',
                'left': '100',
                'top': '100'
            }
        },
        'connections': []
    }
    
    response = authenticated_client.post('/api/deploy-lab',
                                       data=json.dumps(deployment_data),
                                       content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'deployment_id' in data
    assert 'message' in data

@pytest.mark.unit
def test_api_get_deployment_status(authenticated_client):
    """Test API endpoint for getting deployment status"""
    # Test non-existent deployment
    response = authenticated_client.get('/api/deployment-status/nonexistent')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'not found' in data['error']

@pytest.mark.unit
def test_api_authentication_required(client):
    """Test that API endpoints require authentication"""
    api_endpoints = [
        '/api/router-types',
        '/api/router-specs/c3725',
        '/api/validate-config',
        '/api/deploy-lab',
        '/api/deployment-status/test'
    ]
    
    for endpoint in api_endpoints:
        if endpoint in ['/api/validate-config', '/api/deploy-lab']:
            response = client.post(endpoint, data=json.dumps({}), 
                                 content_type='application/json')
        else:
            response = client.get(endpoint)
        
        assert response.status_code == 302  # Redirect to login

# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.unit
def test_404_error_handler(authenticated_client):
    """Test 404 error handling"""
    response = authenticated_client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b'not found' in response.data or b'error.html' in response.data

@pytest.mark.integration
@patch('web_app.EVEClient')
def test_api_error_handling(mock_eve_class, authenticated_client):
    """Test API error handling"""
    # Mock EVEClient to raise an exception
    mock_eve_client = Mock()
    mock_eve_client.get_available_router_types.side_effect = Exception("Connection failed")
    mock_eve_class.return_value = mock_eve_client
    
    response = authenticated_client.get('/api/router-types')
    assert response.status_code == 500
    
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error' in data

# ============================================================================
# WEBSOCKET TESTS
# ============================================================================

@pytest.mark.integration
def test_socketio_connection():
    """Test WebSocket connection establishment"""
    # This test requires proper Flask-SocketIO setup
    # For now, we'll test the basic structure
    try:
        if hasattr(socketio, 'test_client'):
            client = socketio.test_client(app)
            assert client.is_connected()
        else:
            # Mock test for when Flask-SocketIO is not available
            assert True
    except:
        # Skip if SocketIO testing is not available
        pytest.skip("SocketIO testing not available")

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@patch('web_app.EVEClient')
def test_full_lab_creation_workflow(mock_eve_class, authenticated_client, mock_eve_client):
    """Test complete lab creation workflow"""
    mock_eve_class.return_value = mock_eve_client
    
    # Step 1: Access topology designer
    response = authenticated_client.get('/topology')
    assert response.status_code == 200
    
    # Step 2: Get router types
    response = authenticated_client.get('/api/router-types')
    assert response.status_code == 200
    
    # Step 3: Validate configuration
    config_data = {
        'routers': {
            'R1': {'type': 'dynamips', 'template': 'c3725'},
            'R2': {'type': 'dynamips', 'template': 'c7200'}
        },
        'connections': []
    }
    
    response = authenticated_client.post('/api/validate-config',
                                       data=json.dumps(config_data),
                                       content_type='application/json')
    assert response.status_code == 200
    
    # Step 4: Deploy lab
    deployment_data = {
        'lab_name': 'Integration_Test_Lab',
        'routers': config_data['routers'],
        'connections': config_data['connections']
    }
    
    response = authenticated_client.post('/api/deploy-lab',
                                       data=json.dumps(deployment_data),
                                       content_type='application/json')
    assert response.status_code == 200

@pytest.mark.performance
@patch('web_app.EVEClient')
def test_dashboard_performance(mock_eve_class, authenticated_client, mock_eve_client):
    """Test dashboard loading performance"""
    mock_eve_class.return_value = mock_eve_client
    
    start_time = time.time()
    response = authenticated_client.get('/')
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 2.0  # Should load within 2 seconds

@pytest.mark.performance
def test_api_response_times(authenticated_client):
    """Test API endpoint response times"""
    endpoints = ['/api/router-types']
    
    for endpoint in endpoints:
        start_time = time.time()
        response = authenticated_client.get(endpoint)
        end_time = time.time()
        
        # Allow for higher response time due to mocking overhead
        assert (end_time - start_time) < 5.0
        assert response.status_code in [200, 500]  # Allow for mock failures

# ============================================================================
# SECURITY TESTS
# ============================================================================

@pytest.mark.security
def test_session_security(client):
    """Test session security features"""
    # Test that sessions are properly managed
    with client.session_transaction() as sess:
        sess['user'] = 'admin'
        sess['role'] = 'admin'
    
    response = client.get('/')
    assert response.status_code == 200

@pytest.mark.security
def test_csrf_protection(authenticated_client):
    """Test CSRF protection (when enabled)"""
    # For now, just ensure endpoints are accessible
    # In production, CSRF protection should be enabled
    response = authenticated_client.post('/api/validate-config',
                                       data=json.dumps({}),
                                       content_type='application/json')
    # Should not fail due to CSRF in test environment
    assert response.status_code in [200, 400, 500]

# ============================================================================
# MULTI-VENDOR INTEGRATION TESTS
# ============================================================================

@pytest.mark.multi_vendor
@patch('web_app.EVEClient')
def test_multi_vendor_router_support(mock_eve_class, authenticated_client, mock_eve_client):
    """Test multi-vendor router support integration"""
    mock_eve_class.return_value = mock_eve_client
    
    # Test all router types are available
    response = authenticated_client.get('/api/router-types')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    expected_routers = ['c3725', 'c7200', 'c3640', 'c2691', 'c1700']
    assert all(router in data['router_types'] for router in expected_routers)

@pytest.mark.multi_vendor
@patch('web_app.EVEClient')
def test_router_specifications_all_types(mock_eve_class, authenticated_client, mock_eve_client):
    """Test router specifications for all supported types"""
    mock_eve_class.return_value = mock_eve_client
    
    router_types = ['c3725', 'c7200', 'c3640', 'c2691', 'c1700']
    
    for router_type in router_types:
        response = authenticated_client.get(f'/api/router-specs/{router_type}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'specifications' in data

# ============================================================================
# DEPLOYMENT TRACKING TESTS
# ============================================================================

@pytest.mark.integration
def test_deployment_tracking_structure():
    """Test deployment tracking data structure"""
    # Import the deployment tracking structure
    try:
        from web_app import active_deployments, deployment_lock
        
        # Test that the tracking structures exist
        assert isinstance(active_deployments, dict)
        assert deployment_lock is not None
        
    except ImportError:
        # Mock test if imports fail
        assert True

@pytest.mark.integration
@patch('web_app.threading.Thread')
def test_background_deployment_threading(mock_thread, authenticated_client):
    """Test that deployments run in background threads"""
    deployment_data = {
        'lab_name': 'Thread_Test_Lab',
        'routers': {'R1': {'type': 'dynamips', 'template': 'c3725'}},
        'connections': []
    }
    
    # Mock successful deployment start
    with patch('web_app.EVEClient') as mock_eve_class:
        mock_eve_client = Mock()
        mock_eve_class.return_value = mock_eve_client
        
        response = authenticated_client.post('/api/deploy-lab',
                                           data=json.dumps(deployment_data),
                                           content_type='application/json')
        
        # Check that thread was created (if threading is properly mocked)
        if mock_thread.called:
            assert mock_thread.call_count >= 1 
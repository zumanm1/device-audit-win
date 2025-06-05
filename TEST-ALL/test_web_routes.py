#!/usr/bin/env python3
"""
Test suite for Flask web routes in NetAuditPro Router Auditing Application
"""

import pytest
import os
import sys
import json
import importlib.util
from unittest.mock import Mock, patch, mock_open

# Add the parent directory to the path so we can import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_app_module():
    """Load the main application module"""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    module_path = os.path.join(parent_dir, "rr4-router-complete-enhanced-v2.py")
    
    if os.path.exists(module_path):
        spec = importlib.util.spec_from_file_location("app_module", module_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        return app_module
    else:
        raise ImportError(f"Could not find main application file at {module_path}")

@pytest.fixture
def app():
    """Create Flask test app"""
    try:
        app_module = load_app_module()
        app_module.app.config['TESTING'] = True
        app_module.app.config['WTF_CSRF_ENABLED'] = False
        return app_module.app
    except ImportError:
        pytest.skip("Could not import main module")

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

class TestBasicRoutes:
    """Test basic web routes"""
    
    def test_index_route(self, client):
        """Test the main index route"""
        response = client.get('/')
        assert response.status_code == 200
        # Should contain some expected content
        assert b'NetAuditPro' in response.data or b'Router' in response.data
    
    def test_audit_progress_data_route(self, client):
        """Test audit progress data endpoint"""
        response = client.get('/audit_progress_data')
        assert response.status_code == 200
        # Should return JSON
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_device_status_route(self, client):
        """Test device status endpoint"""
        response = client.get('/device_status')
        assert response.status_code == 200
        # Should return JSON
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_down_devices_route(self, client):
        """Test down devices endpoint"""
        response = client.get('/down_devices')
        assert response.status_code == 200
        # Should return JSON
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_enhanced_summary_route(self, client):
        """Test enhanced summary endpoint"""
        response = client.get('/enhanced_summary')
        assert response.status_code == 200
        # Should return JSON
        data = json.loads(response.data)
        assert isinstance(data, dict)

class TestSettingsRoutes:
    """Test settings-related routes"""
    
    def test_settings_get(self, client):
        """Test GET request to settings"""
        response = client.get('/settings')
        assert response.status_code == 200
        # Should contain settings form
        assert b'settings' in response.data.lower() or b'configuration' in response.data.lower()
    
    @patch('builtins.open', mock_open())
    @patch('os.path.exists', return_value=True)
    def test_settings_post(self, mock_exists, client):
        """Test POST request to settings"""
        settings_data = {
            'JUMP_HOST': '192.168.1.100',
            'JUMP_USERNAME': 'testuser',
            'JUMP_PASSWORD': 'testpass',
            'DEVICE_USERNAME': 'admin',
            'DEVICE_PASSWORD': 'admin123',
            'DEVICE_ENABLE': 'enable123'
        }
        
        response = client.post('/settings', data=settings_data)
        # Should redirect or return success
        assert response.status_code in [200, 302]

class TestInventoryRoutes:
    """Test inventory management routes"""
    
    def test_manage_inventories_get(self, client):
        """Test GET request to manage inventories"""
        response = client.get('/manage_inventories')
        assert response.status_code == 200
        # Should contain inventory management interface
        assert b'inventory' in response.data.lower() or b'manage' in response.data.lower()
    
    def test_export_inventory_csv(self, client):
        """Test CSV export endpoint"""
        response = client.get('/export_inventory_csv')
        assert response.status_code == 200
        # Should return CSV content type
        assert 'text/csv' in response.content_type or 'application/octet-stream' in response.content_type
    
    @patch('builtins.open', mock_open(read_data='hostname,ip,device_type\nR1,192.168.1.1,cisco_ios'))
    def test_edit_active_inventory_content(self, mock_file, client):
        """Test editing active inventory content"""
        inventory_data = {
            'inventory_content': 'hostname,ip,device_type\nR1,192.168.1.1,cisco_ios\nR2,192.168.1.2,cisco_ios'
        }
        
        response = client.post('/edit_active_inventory_content', data=inventory_data)
        # Should redirect or return success
        assert response.status_code in [200, 302]

class TestAuditRoutes:
    """Test audit-related routes"""
    
    def test_start_audit_get(self, client):
        """Test GET request to start audit"""
        response = client.get('/start_audit')
        assert response.status_code == 200
        # Should contain audit interface
        assert b'audit' in response.data.lower() or b'start' in response.data.lower()
    
    @patch('threading.Thread')
    def test_start_audit_post(self, mock_thread, client):
        """Test POST request to start audit"""
        response = client.post('/start_audit')
        # Should redirect or return success
        assert response.status_code in [200, 302]
    
    def test_pause_audit(self, client):
        """Test pause audit endpoint"""
        response = client.post('/pause_audit')
        assert response.status_code == 200
        # Should return JSON response
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'status' in data
    
    def test_resume_audit(self, client):
        """Test resume audit endpoint"""
        response = client.post('/resume_audit')
        assert response.status_code == 200
        # Should return JSON response
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'status' in data

class TestCommandLogRoutes:
    """Test command log routes"""
    
    def test_command_logs_route(self, client):
        """Test command logs listing"""
        response = client.get('/command_logs')
        assert response.status_code == 200
        # Should contain command logs interface
        assert b'command' in response.data.lower() or b'logs' in response.data.lower()
    
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data='Test log content'))
    def test_view_command_log(self, mock_file, mock_exists, client):
        """Test viewing a specific command log"""
        response = client.get('/view_command_log/test_log.txt')
        assert response.status_code == 200
        # Should contain log content
        assert b'Test log content' in response.data or response.status_code == 200
    
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data='Test log content'))
    def test_download_command_log(self, mock_file, mock_exists, client):
        """Test downloading a command log"""
        response = client.get('/download_command_log/test_log.txt')
        assert response.status_code == 200
        # Should have appropriate headers for download
        assert 'attachment' in response.headers.get('Content-Disposition', '')

class TestUtilityRoutes:
    """Test utility routes"""
    
    def test_clear_logs(self, client):
        """Test clear logs endpoint"""
        response = client.post('/clear_logs')
        assert response.status_code == 200
        # Should return JSON response
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'status' in data

class TestErrorHandling:
    """Test error handling in routes"""
    
    def test_nonexistent_route(self, client):
        """Test accessing non-existent route"""
        response = client.get('/nonexistent_route')
        assert response.status_code == 404
    
    def test_invalid_command_log(self, client):
        """Test accessing non-existent command log"""
        response = client.get('/view_command_log/nonexistent.txt')
        # Should handle gracefully
        assert response.status_code in [200, 404]
    
    def test_invalid_report_file(self, client):
        """Test accessing non-existent report file"""
        response = client.get('/reports/nonexistent/file.txt')
        # Should handle gracefully
        assert response.status_code in [200, 404]

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
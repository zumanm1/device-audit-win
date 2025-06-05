#!/usr/bin/env python3
"""
Test suite for inventory management functions in NetAuditPro Router Auditing Application
"""

import pytest
import os
import sys
import tempfile
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

class TestInventoryValidation:
    """Test inventory validation functions"""
    
    def test_validate_csv_data_list_valid(self):
        """Test CSV data validation with valid data"""
        try:
            app_module = load_app_module()
            
            headers = ["hostname", "ip", "device_type"]
            data = [
                {"hostname": "R1", "ip": "192.168.1.1", "device_type": "cisco_ios"},
                {"hostname": "R2", "ip": "192.168.1.2", "device_type": "cisco_ios"}
            ]
            
            is_valid, error_msg = app_module.validate_csv_data_list(data, headers)
            assert is_valid == True
            assert error_msg == ""
            
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_validate_csv_data_list_missing_headers(self):
        """Test CSV data validation with missing headers"""
        try:
            app_module = load_app_module()
            
            headers = ["hostname", "device_type"]  # Missing 'ip'
            data = [
                {"hostname": "R1", "device_type": "cisco_ios"}
            ]
            
            is_valid, error_msg = app_module.validate_csv_data_list(data, headers)
            assert is_valid == False
            assert "ip" in error_msg.lower()
            
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_validate_csv_data_list_missing_data(self):
        """Test CSV data validation with missing required data"""
        try:
            app_module = load_app_module()
            
            headers = ["hostname", "ip", "device_type"]
            data = [
                {"hostname": "R1", "device_type": "cisco_ios"}  # Missing IP
            ]
            
            is_valid, error_msg = app_module.validate_csv_data_list(data, headers)
            assert is_valid == False
            assert "ip" in error_msg.lower()
            
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_validate_csv_data_list_empty(self):
        """Test CSV data validation with empty data"""
        try:
            app_module = load_app_module()
            
            headers = ["hostname", "ip", "device_type"]
            data = []
            
            is_valid, error_msg = app_module.validate_csv_data_list(data, headers)
            assert is_valid == False
            assert "empty" in error_msg.lower()
            
        except ImportError:
            pytest.skip("Could not import main module")

class TestInventoryConversion:
    """Test inventory format conversion functions"""
    
    def test_convert_router_dict_to_csv_list(self):
        """Test router dictionary to CSV conversion"""
        try:
            app_module = load_app_module()
            
            router_dict = {
                "routers": {
                    "R1": {
                        "ip": "192.168.1.1",
                        "device_type": "cisco_ios",
                        "description": "Test Router 1"
                    },
                    "R2": {
                        "ip": "192.168.1.2",
                        "device_type": "cisco_ios",
                        "description": "Test Router 2"
                    }
                }
            }
            
            result = app_module.convert_router_dict_to_csv_list(router_dict)
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["hostname"] == "R1"
            assert result[1]["hostname"] == "R2"
            assert result[0]["ip"] == "192.168.1.1"
            assert result[1]["ip"] == "192.168.1.2"
            
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_convert_router_dict_to_csv_list_empty(self):
        """Test router dictionary to CSV conversion with empty dict"""
        try:
            app_module = load_app_module()
            
            router_dict = {}
            result = app_module.convert_router_dict_to_csv_list(router_dict)
            assert isinstance(result, list)
            assert len(result) == 0
            
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_get_csv_headers_from_data(self):
        """Test CSV header extraction"""
        try:
            app_module = load_app_module()
            
            data = [
                {"hostname": "R1", "ip": "192.168.1.1", "device_type": "cisco_ios"},
                {"hostname": "R2", "ip": "192.168.1.2", "device_type": "cisco_ios"}
            ]
            
            headers = app_module.get_csv_headers_from_data(data)
            assert isinstance(headers, list)
            assert "hostname" in headers
            assert "ip" in headers
            assert "device_type" in headers
            
        except ImportError:
            pytest.skip("Could not import main module")

class TestCSVParsing:
    """Test CSV parsing functions"""
    
    def test_read_csv_data_from_str_valid(self):
        """Test CSV string parsing with valid data"""
        try:
            app_module = load_app_module()
            
            csv_string = "hostname,ip,device_type\nR1,192.168.1.1,cisco_ios\nR2,192.168.1.2,cisco_ios"
            
            data, headers = app_module.read_csv_data_from_str(csv_string)
            assert isinstance(data, list)
            assert isinstance(headers, list)
            assert len(data) == 2
            assert len(headers) == 3
            assert "hostname" in headers
            assert data[0]["hostname"] == "R1"
            assert data[1]["hostname"] == "R2"
            
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_read_csv_data_from_str_empty(self):
        """Test CSV string parsing with empty string"""
        try:
            app_module = load_app_module()
            
            csv_string = ""
            
            data, headers = app_module.read_csv_data_from_str(csv_string)
            assert data == []
            assert headers == []
            
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_write_csv_data_to_str(self):
        """Test CSV string generation"""
        try:
            app_module = load_app_module()
            
            headers = ["hostname", "ip", "device_type"]
            data = [
                {"hostname": "R1", "ip": "192.168.1.1", "device_type": "cisco_ios"},
                {"hostname": "R2", "ip": "192.168.1.2", "device_type": "cisco_ios"}
            ]
            
            csv_string = app_module.write_csv_data_to_str(data, headers)
            assert isinstance(csv_string, str)
            assert "hostname,ip,device_type" in csv_string
            assert "R1,192.168.1.1,cisco_ios" in csv_string
            assert "R2,192.168.1.2,cisco_ios" in csv_string
            
        except ImportError:
            pytest.skip("Could not import main module")

class TestInventoryRowValidation:
    """Test individual inventory row validation"""
    
    def test_validate_csv_inventory_row_valid(self):
        """Test valid CSV inventory row"""
        try:
            app_module = load_app_module()
            
            row = {
                "hostname": "R1",
                "ip": "192.168.1.1",
                "device_type": "cisco_ios",
                "description": "Test Router"
            }
            
            is_valid, error_msg, extracted_data = app_module.validate_csv_inventory_row(row, 1)
            assert is_valid == True
            assert error_msg == ""
            assert "R1" in extracted_data
            assert extracted_data["R1"]["ip"] == "192.168.1.1"
            
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_validate_csv_inventory_row_missing_required(self):
        """Test CSV inventory row with missing required fields"""
        try:
            app_module = load_app_module()
            
            row = {
                "hostname": "R1",
                "device_type": "cisco_ios"
                # Missing IP
            }
            
            is_valid, error_msg, extracted_data = app_module.validate_csv_inventory_row(row, 1)
            assert is_valid == False
            assert "ip" in error_msg.lower()
            assert extracted_data == {}
            
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_validate_csv_inventory_row_invalid_hostname(self):
        """Test CSV inventory row with invalid hostname"""
        try:
            app_module = load_app_module()
            
            row = {
                "hostname": "invalid hostname with spaces",
                "ip": "192.168.1.1",
                "device_type": "cisco_ios"
            }
            
            is_valid, error_msg, extracted_data = app_module.validate_csv_inventory_row(row, 1)
            assert is_valid == False
            assert "hostname" in error_msg.lower()
            assert extracted_data == {}
            
        except ImportError:
            pytest.skip("Could not import main module")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
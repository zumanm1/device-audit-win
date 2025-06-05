#!/usr/bin/env python3
"""
Test suite for utility functions in NetAuditPro Router Auditing Application
"""

import pytest
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime

# Add the parent directory to the path so we can import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_app_module():
    """Load the main application module"""
    import importlib.util
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    module_path = os.path.join(parent_dir, "rr4-router-complete-enhanced-v2.py")
    
    if os.path.exists(module_path):
        spec = importlib.util.spec_from_file_location("app_module", module_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        return app_module
    else:
        raise ImportError(f"Could not find main application file at {module_path}")

# Load the module
app_module = load_app_module()

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_strip_ansi(self):
        """Test ANSI escape sequence removal"""
        # Test with ANSI codes
        text_with_ansi = "\033[31mRed text\033[0m"
        result = app_module.strip_ansi(text_with_ansi)
        assert result == "Red text"
        
        # Test with no ANSI codes
        plain_text = "Plain text"
        result = app_module.strip_ansi(plain_text)
        assert result == "Plain text"
        
        # Test with empty string
        result = app_module.strip_ansi("")
        assert result == ""
    
    def test_sanitize_log_message(self):
        """Test log message sanitization"""
        # Test basic sanitization
        message = "Test message"
        result = app_module.sanitize_log_message(message)
        assert isinstance(result, str)
        
        # Test with special characters
        message_with_special = "Test\nmessage\twith\rspecial"
        result = app_module.sanitize_log_message(message_with_special)
        assert "\n" not in result or "\t" not in result or "\r" not in result
    
    def test_is_valid_hostname(self):
        """Test hostname validation"""
        # Valid hostnames
        assert app_module.is_valid_hostname("router1") == True
        assert app_module.is_valid_hostname("test-router") == True
        assert app_module.is_valid_hostname("R1") == True
        
        # Invalid hostnames
        assert app_module.is_valid_hostname("") == False
        assert app_module.is_valid_hostname("router with spaces") == False
        assert app_module.is_valid_hostname("router@invalid") == False
    
    def test_is_valid_ip(self):
        """Test IP address validation"""
        # Valid IPs
        assert app_module.is_valid_ip("192.168.1.1") == True
        assert app_module.is_valid_ip("10.0.0.1") == True
        assert app_module.is_valid_ip("172.16.1.1") == True
        
        # Invalid IPs
        assert app_module.is_valid_ip("") == False
        assert app_module.is_valid_ip("256.256.256.256") == False
        assert app_module.is_valid_ip("not.an.ip.address") == False
        assert app_module.is_valid_ip("192.168.1") == False
    
    def test_bar_audit(self):
        """Test progress bar generation"""
        # Test 0%
        result = app_module.bar_audit(0.0, width=10)
        assert len(result) == 10
        assert result == "          "
        
        # Test 50%
        result = app_module.bar_audit(0.5, width=10)
        assert len(result) == 10
        assert "█" in result
        
        # Test 100%
        result = app_module.bar_audit(1.0, width=10)
        assert len(result) == 10
        assert result == "██████████"
    
    def test_mark_audit(self):
        """Test audit mark generation"""
        # Test success mark
        success_mark = app_module.mark_audit(True)
        assert "✓" in success_mark or "OK" in success_mark
        
        # Test failure mark
        failure_mark = app_module.mark_audit(False)
        assert "✗" in failure_mark or "FAIL" in failure_mark

class TestInventoryFunctions:
    """Test inventory management functions"""
    
    def test_validate_csv_data_list(self):
        """Test CSV data validation"""
        # Valid data
        headers = ["hostname", "ip", "device_type"]
        data = [
            {"hostname": "R1", "ip": "192.168.1.1", "device_type": "cisco_ios"},
            {"hostname": "R2", "ip": "192.168.1.2", "device_type": "cisco_ios"}
        ]
        is_valid, error_msg = app_module.validate_csv_data_list(data, headers)
        assert is_valid == True
        assert error_msg == ""
        
        # Invalid data - missing required field
        invalid_data = [
            {"hostname": "R1", "device_type": "cisco_ios"}  # Missing IP
        ]
        is_valid, error_msg = app_module.validate_csv_data_list(invalid_data, headers)
        assert is_valid == False
        assert "ip" in error_msg.lower()
    
    def test_convert_router_dict_to_csv_list(self):
        """Test router dictionary to CSV conversion"""
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
    
    def test_get_csv_headers_from_data(self):
        """Test CSV header extraction"""
        data = [
            {"hostname": "R1", "ip": "192.168.1.1", "device_type": "cisco_ios"},
            {"hostname": "R2", "ip": "192.168.1.2", "device_type": "cisco_ios"}
        ]
        
        headers = app_module.get_csv_headers_from_data(data)
        assert isinstance(headers, list)
        assert "hostname" in headers
        assert "ip" in headers
        assert "device_type" in headers
    
    @patch('builtins.open', new_callable=mock_open, read_data='hostname,ip,device_type\nR1,192.168.1.1,cisco_ios\n')
    def test_read_csv_data_from_str(self, mock_file):
        """Test CSV string parsing"""
        csv_string = "hostname,ip,device_type\nR1,192.168.1.1,cisco_ios\nR2,192.168.1.2,cisco_ios"
        
        result = app_module.read_csv_data_from_str(csv_string)
        assert isinstance(result, dict)
        assert "headers" in result
        assert "data" in result
        assert len(result["data"]) == 2

class TestCommandLogging:
    """Test command logging functionality"""
    
    def test_ensure_command_logs_directory(self, temp_directory):
        """Test command logs directory creation"""
        with patch.object(app_module, 'COMMAND_LOGS_DIR', temp_directory):
            app_module.ensure_command_logs_directory()
            assert os.path.exists(temp_directory)
    
    def test_log_device_command(self, reset_global_state):
        """Test device command logging"""
        device_name = "R1"
        command = "show version"
        response = "Cisco IOS Software"
        
        app_module.log_device_command(device_name, command, response, "SUCCESS")
        
        assert device_name in app_module.DEVICE_COMMAND_LOGS
        assert len(app_module.DEVICE_COMMAND_LOGS[device_name]["commands"]) == 1
        assert app_module.DEVICE_COMMAND_LOGS[device_name]["commands"][0]["command"] == command
        assert app_module.DEVICE_COMMAND_LOGS[device_name]["commands"][0]["response"] == response
        assert app_module.DEVICE_COMMAND_LOGS[device_name]["commands"][0]["status"] == "SUCCESS"
    
    def test_update_device_connection_status(self, reset_global_state):
        """Test device connection status updates"""
        device_name = "R1"
        
        app_module.update_device_connection_status(device_name, ping_status="SUCCESS", ssh_status="SUCCESS")
        
        assert device_name in app_module.DEVICE_COMMAND_LOGS
        assert app_module.DEVICE_COMMAND_LOGS[device_name]["ping_status"] == "SUCCESS"
        assert app_module.DEVICE_COMMAND_LOGS[device_name]["ssh_status"] == "SUCCESS"

class TestDeviceStatusTracking:
    """Test enhanced device status tracking"""
    
    def test_track_device_status(self, reset_global_state):
        """Test device status tracking"""
        device_name = "R1"
        status = "DOWN"
        failure_reason = "ICMP timeout"
        
        app_module.track_device_status(device_name, status, failure_reason)
        
        assert device_name in app_module.DEVICE_STATUS_TRACKING
        assert app_module.DEVICE_STATUS_TRACKING[device_name] == status
        
        if status == "DOWN":
            assert device_name in app_module.DOWN_DEVICES
            assert app_module.DOWN_DEVICES[device_name]["status"] == status
            assert app_module.DOWN_DEVICES[device_name]["failure_reason"] == failure_reason
    
    def test_get_device_status_summary(self, reset_global_state):
        """Test device status summary generation"""
        # Add some test data
        app_module.track_device_status("R1", "UP")
        app_module.track_device_status("R2", "DOWN", "SSH timeout")
        app_module.track_device_status("R3", "ICMP_FAIL", "Network unreachable")
        
        summary = app_module.get_device_status_summary()
        
        assert isinstance(summary, dict)
        assert "total_devices" in summary
        assert "up_devices" in summary
        assert "down_devices" in summary
        assert summary["total_devices"] == 3
        assert summary["up_devices"] == 1
        assert summary["down_devices"] == 2

class TestProgressTracking:
    """Test audit progress tracking"""
    
    def test_start_audit_progress(self, reset_global_state):
        """Test audit progress initialization"""
        device_count = 5
        app_module.start_audit_progress(device_count)
        
        assert app_module.AUDIT_PROGRESS["total_devices"] == device_count
        assert app_module.AUDIT_PROGRESS["completed_devices"] == 0
        assert app_module.AUDIT_PROGRESS["percentage"] == 0.0
    
    def test_update_audit_progress(self, reset_global_state):
        """Test audit progress updates"""
        app_module.start_audit_progress(5)
        
        app_module.update_audit_progress(device="R1", status="COMPLETED", completed=True)
        
        assert app_module.AUDIT_PROGRESS["completed_devices"] == 1
        assert app_module.AUDIT_PROGRESS["percentage"] == 20.0
        assert app_module.AUDIT_PROGRESS["current_device"] == "R1"

class TestConfigurationManagement:
    """Test configuration management functions"""
    
    @patch.dict(os.environ, {"JUMP_HOST": "192.168.1.100", "JUMP_USERNAME": "testuser"})
    def test_load_app_config(self):
        """Test application configuration loading"""
        with patch('os.path.exists', return_value=False):
            config = app_module.load_app_config()
            assert isinstance(config, dict)
            # Should have default values or environment values
    
    def test_get_inventory_path(self, temp_directory):
        """Test inventory path generation"""
        with patch('os.path.dirname', return_value=temp_directory):
            path = app_module.get_inventory_path("test.yaml", "yaml")
            assert path.endswith("test.yaml")
            assert temp_directory in path

class TestNetworkOperations:
    """Test network operation functions"""
    
    @patch('subprocess.run')
    def test_ping_local_success(self, mock_run):
        """Test successful local ping"""
        mock_run.return_value.returncode = 0
        
        result = app_module.ping_local("192.168.1.1")
        assert result == True
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_ping_local_failure(self, mock_run):
        """Test failed local ping"""
        mock_run.return_value.returncode = 1
        
        result = app_module.ping_local("192.168.1.1")
        assert result == False
        mock_run.assert_called_once()
    
    def test_ping_remote(self, mock_ssh_client):
        """Test remote ping through SSH"""
        # Mock successful ping
        mock_stdout = Mock()
        mock_stdout.read.return_value = b"64 bytes from 192.168.1.1"
        mock_ssh_client.exec_command.return_value = (Mock(), mock_stdout, Mock())
        
        result = app_module.ping_remote(mock_ssh_client, "192.168.1.1")
        assert result == True
        
        # Mock failed ping
        mock_stdout.read.return_value = b"100% packet loss"
        result = app_module.ping_remote(mock_ssh_client, "192.168.1.1")
        assert result == False

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
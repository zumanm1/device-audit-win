#!/usr/bin/env python3
"""
Test suite for enhanced features in NetAuditPro Router Auditing Application
"""

import pytest
import os
import sys
import tempfile
import importlib.util
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

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

class TestCommandLogging:
    """Test command logging functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        try:
            self.app_module = load_app_module()
            # Clear global state
            if hasattr(self.app_module, 'DEVICE_COMMAND_LOGS'):
                self.app_module.DEVICE_COMMAND_LOGS.clear()
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_log_device_command(self):
        """Test device command logging"""
        device_name = "R1"
        command = "show version"
        response = "Cisco IOS Software"
        
        self.app_module.log_device_command(device_name, command, response, "SUCCESS")
        
        assert device_name in self.app_module.DEVICE_COMMAND_LOGS
        assert len(self.app_module.DEVICE_COMMAND_LOGS[device_name]["commands"]) == 1
        assert self.app_module.DEVICE_COMMAND_LOGS[device_name]["commands"][0]["command"] == command
        assert self.app_module.DEVICE_COMMAND_LOGS[device_name]["commands"][0]["response"] == response
        assert self.app_module.DEVICE_COMMAND_LOGS[device_name]["commands"][0]["status"] == "SUCCESS"
    
    def test_log_multiple_commands(self):
        """Test logging multiple commands for same device"""
        device_name = "R1"
        
        self.app_module.log_device_command(device_name, "show version", "Version output", "SUCCESS")
        self.app_module.log_device_command(device_name, "show ip route", "Route output", "SUCCESS")
        self.app_module.log_device_command(device_name, "show interfaces", "Interface output", "FAILED")
        
        assert len(self.app_module.DEVICE_COMMAND_LOGS[device_name]["commands"]) == 3
        assert self.app_module.DEVICE_COMMAND_LOGS[device_name]["summary"]["total_commands"] == 3
        assert self.app_module.DEVICE_COMMAND_LOGS[device_name]["summary"]["successful_commands"] == 2
        assert self.app_module.DEVICE_COMMAND_LOGS[device_name]["summary"]["failed_commands"] == 1
    
    def test_update_device_connection_status(self):
        """Test device connection status updates"""
        device_name = "R1"
        
        self.app_module.update_device_connection_status(device_name, ping_status="SUCCESS", ssh_status="SUCCESS")
        
        assert device_name in self.app_module.DEVICE_COMMAND_LOGS
        assert self.app_module.DEVICE_COMMAND_LOGS[device_name]["ping_status"] == "SUCCESS"
        assert self.app_module.DEVICE_COMMAND_LOGS[device_name]["ssh_status"] == "SUCCESS"
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_ensure_command_logs_directory(self, mock_makedirs, mock_exists):
        """Test command logs directory creation"""
        mock_exists.return_value = False
        
        self.app_module.ensure_command_logs_directory()
        
        mock_makedirs.assert_called_once()

class TestDeviceStatusTracking:
    """Test enhanced device status tracking"""
    
    def setup_method(self):
        """Setup for each test method"""
        try:
            self.app_module = load_app_module()
            # Clear global state
            if hasattr(self.app_module, 'DEVICE_STATUS_TRACKING'):
                self.app_module.DEVICE_STATUS_TRACKING.clear()
            if hasattr(self.app_module, 'DOWN_DEVICES'):
                self.app_module.DOWN_DEVICES.clear()
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_track_device_status_up(self):
        """Test tracking device status as UP"""
        device_name = "R1"
        status = "UP"
        
        self.app_module.track_device_status(device_name, status)
        
        assert device_name in self.app_module.DEVICE_STATUS_TRACKING
        assert self.app_module.DEVICE_STATUS_TRACKING[device_name] == status
        # UP devices should not be in DOWN_DEVICES
        assert device_name not in self.app_module.DOWN_DEVICES
    
    def test_track_device_status_down(self):
        """Test tracking device status as DOWN"""
        device_name = "R1"
        status = "DOWN"
        failure_reason = "ICMP timeout"
        
        self.app_module.track_device_status(device_name, status, failure_reason)
        
        assert device_name in self.app_module.DEVICE_STATUS_TRACKING
        assert self.app_module.DEVICE_STATUS_TRACKING[device_name] == status
        assert device_name in self.app_module.DOWN_DEVICES
        assert self.app_module.DOWN_DEVICES[device_name]["status"] == status
        assert self.app_module.DOWN_DEVICES[device_name]["failure_reason"] == failure_reason
    
    def test_track_device_status_icmp_fail(self):
        """Test tracking device status as ICMP_FAIL"""
        device_name = "R1"
        status = "ICMP_FAIL"
        failure_reason = "Network unreachable"
        
        self.app_module.track_device_status(device_name, status, failure_reason)
        
        assert device_name in self.app_module.DEVICE_STATUS_TRACKING
        assert self.app_module.DEVICE_STATUS_TRACKING[device_name] == status
        assert device_name in self.app_module.DOWN_DEVICES
        assert self.app_module.DOWN_DEVICES[device_name]["status"] == status
        assert self.app_module.DOWN_DEVICES[device_name]["failure_reason"] == failure_reason
    
    def test_get_device_status_summary(self):
        """Test device status summary generation"""
        # Add some test data
        self.app_module.track_device_status("R1", "UP")
        self.app_module.track_device_status("R2", "DOWN", "SSH timeout")
        self.app_module.track_device_status("R3", "ICMP_FAIL", "Network unreachable")
        self.app_module.track_device_status("R4", "UP")
        
        summary = self.app_module.get_device_status_summary()
        
        assert isinstance(summary, dict)
        assert "total_devices" in summary
        assert "up_devices" in summary
        assert "down_devices" in summary
        assert summary["total_devices"] == 4
        assert summary["up_devices"] == 2
        assert summary["down_devices"] == 2

class TestProgressTracking:
    """Test audit progress tracking"""
    
    def setup_method(self):
        """Setup for each test method"""
        try:
            self.app_module = load_app_module()
            # Initialize progress tracking
            if hasattr(self.app_module, 'AUDIT_PROGRESS'):
                self.app_module.AUDIT_PROGRESS.clear()
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_start_audit_progress(self):
        """Test audit progress initialization"""
        device_count = 5
        self.app_module.start_audit_progress(device_count)
        
        assert self.app_module.AUDIT_PROGRESS["total_devices"] == device_count
        assert self.app_module.AUDIT_PROGRESS["completed_devices"] == 0
        assert self.app_module.AUDIT_PROGRESS["percentage"] == 0.0
    
    def test_update_audit_progress(self):
        """Test audit progress updates"""
        self.app_module.start_audit_progress(5)
        
        self.app_module.update_audit_progress(device="R1", status="COMPLETED", completed=True)
        
        assert self.app_module.AUDIT_PROGRESS["completed_devices"] == 1
        assert self.app_module.AUDIT_PROGRESS["percentage"] == 20.0
        assert self.app_module.AUDIT_PROGRESS["current_device"] == "R1"
    
    def test_update_audit_progress_multiple(self):
        """Test multiple audit progress updates"""
        self.app_module.start_audit_progress(4)
        
        self.app_module.update_audit_progress(device="R1", status="COMPLETED", completed=True)
        self.app_module.update_audit_progress(device="R2", status="COMPLETED", completed=True)
        self.app_module.update_audit_progress(device="R3", status="FAILED", completed=True)
        
        assert self.app_module.AUDIT_PROGRESS["completed_devices"] == 3
        assert self.app_module.AUDIT_PROGRESS["percentage"] == 75.0

class TestUtilityFunctions:
    """Test utility functions for enhanced features"""
    
    def setup_method(self):
        """Setup for each test method"""
        try:
            self.app_module = load_app_module()
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_bar_audit(self):
        """Test progress bar generation"""
        # Test 0%
        result = self.app_module.bar_audit(0.0, width=10)
        assert len(result) == 10
        assert result == "          "
        
        # Test 50%
        result = self.app_module.bar_audit(0.5, width=10)
        assert len(result) == 10
        assert "█" in result
        
        # Test 100%
        result = self.app_module.bar_audit(1.0, width=10)
        assert len(result) == 10
        assert result == "██████████"
    
    def test_mark_audit(self):
        """Test audit mark generation"""
        # Test success mark
        success_mark = self.app_module.mark_audit(True)
        assert "✓" in success_mark or "OK" in success_mark
        
        # Test failure mark
        failure_mark = self.app_module.mark_audit(False)
        assert "✗" in failure_mark or "FAIL" in failure_mark
    
    def test_sanitize_log_message(self):
        """Test log message sanitization"""
        # Test basic sanitization
        message = "Test message"
        result = self.app_module.sanitize_log_message(message)
        assert isinstance(result, str)
        
        # Test with special characters
        message_with_special = "Test\nmessage\twith\rspecial"
        result = self.app_module.sanitize_log_message(message_with_special)
        # Should handle special characters appropriately
        assert isinstance(result, str)

class TestPlaceholderGeneration:
    """Test placeholder configuration generation for down devices"""
    
    def setup_method(self):
        """Setup for each test method"""
        try:
            self.app_module = load_app_module()
        except ImportError:
            pytest.skip("Could not import main module")
    
    def test_generate_placeholder_config_for_down_device(self):
        """Test placeholder configuration generation"""
        device_name = "R1"
        device_ip = "192.168.1.1"
        failure_reason = "ICMP timeout"
        base_report_dir = "/tmp/reports"
        
        result = self.app_module.generate_placeholder_config_for_down_device(
            device_name, device_ip, failure_reason, base_report_dir
        )
        
        assert isinstance(result, str)
        assert device_name in result
        assert device_ip in result
        assert failure_reason in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
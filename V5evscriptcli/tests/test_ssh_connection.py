"""
Test suite for SSH connection functionality
Addresses BUG-002: SSH Connection Error Handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
import os

# Add parent directory to path to import main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5_eve_ng_automation import ssh_execute_command, verify_ssh_access

@pytest.mark.ssh
def test_ssh_execute_command_success():
    """Test successful SSH command execution"""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "SSH command output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = ssh_execute_command("echo 'test'")
        
        assert result == "SSH command output"
        mock_run.assert_called_once()

@pytest.mark.ssh
def test_ssh_execute_command_failure():
    """Test SSH command execution failure"""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Connection failed"
        mock_run.return_value = mock_result
        
        result = ssh_execute_command("invalid_command")
        
        assert result is None
        mock_run.assert_called_once()

@pytest.mark.ssh
def test_ssh_execute_command_timeout():
    """Test SSH command timeout handling"""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("ssh", 30)
        
        result = ssh_execute_command("sleep 60")
        
        assert result is None

@pytest.mark.ssh
def test_ssh_execute_command_exception():
    """Test SSH command exception handling"""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Network error")
        
        result = ssh_execute_command("echo 'test'")
        
        assert result is None

@pytest.mark.ssh
def test_verify_ssh_access_success():
    """Test successful SSH access verification"""
    with patch('v5_eve_ng_automation.ssh_execute_command') as mock_ssh:
        mock_ssh.return_value = "SSH connection test"
        
        result = verify_ssh_access()
        
        assert result == True
        mock_ssh.assert_called_once_with("echo 'SSH connection test'")

@pytest.mark.ssh
def test_verify_ssh_access_failure():
    """Test failed SSH access verification"""
    with patch('v5_eve_ng_automation.ssh_execute_command') as mock_ssh:
        mock_ssh.return_value = None
        
        result = verify_ssh_access()
        
        assert result == False

@pytest.mark.ssh
def test_ssh_command_construction():
    """Test SSH command string construction"""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_run.return_value = mock_result
        
        ssh_execute_command("ls -la")
        
        # Verify the SSH command was constructed correctly
        call_args = mock_run.call_args[0][0]
        assert "sshpass" in call_args
        assert "ssh" in call_args
        assert "StrictHostKeyChecking=no" in call_args
        assert "ls -la" in call_args

@pytest.mark.ssh
def test_ssh_error_logging():
    """Test that SSH errors are properly logged"""
    with patch('subprocess.run') as mock_run, \
         patch('v5_eve_ng_automation.logger') as mock_logger:
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_run.return_value = mock_result
        
        result = ssh_execute_command("restricted_command")
        
        assert result is None
        mock_logger.warning.assert_called()
        
        # Check that the error message contains useful information
        warning_call = mock_logger.warning.call_args[0][0]
        assert "SSH command failed" in warning_call
        assert "Permission denied" in warning_call 
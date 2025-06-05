import sys
import os
import pytest
from datetime import datetime, timedelta
import time
from unittest.mock import patch, MagicMock

# Import the router audit class for testing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# The actual file has hyphens and periods, but Python modules need underscores
# So we'll import it directly using importlib
import importlib.util
spec = importlib.util.spec_from_file_location("router_module", 
                                             os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                                        "rr4-router-complete-enchanced-v3.8-cli-only.py"))
router_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router_module)

# Get the JumpHostAuditor class from the module
JumpHostAuditor = router_module.JumpHostAuditor

class TestTimingFeatures:
    """Test class for the timing features in the router audit tool"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.auditor = JumpHostAuditor()
    
    def test_start_timer(self):
        """Test that the timer starts correctly"""
        start_time = self.auditor.start_timer()
        assert self.auditor.start_time is not None
        assert self.auditor.end_time is None
        assert self.auditor.total_pause_duration == timedelta(0)
        assert self.auditor.is_paused is False
        
    def test_pause_resume_timer(self):
        """Test pausing and resuming the timer"""
        self.auditor.start_timer()
        time.sleep(0.1)  # Small delay
        
        # Test pause
        pause_time = self.auditor.pause_timer()
        assert pause_time is not None
        assert self.auditor.is_paused is True
        assert self.auditor.pause_start_time is not None
        
        time.sleep(0.1)  # Small delay during pause
        
        # Test resume
        pause_duration = self.auditor.resume_timer()
        assert pause_duration is not None
        assert self.auditor.is_paused is False
        assert self.auditor.total_pause_duration > timedelta(0)
        
    def test_stop_timer(self):
        """Test stopping the timer and calculating elapsed time"""
        self.auditor.start_timer()
        time.sleep(0.2)  # Small delay
        elapsed_time = self.auditor.stop_timer()
        
        assert elapsed_time is not None
        assert elapsed_time > timedelta(0)
        assert self.auditor.end_time is not None
        
    def test_format_elapsed_time(self):
        """Test formatting of elapsed time"""
        # Test seconds
        time_obj = timedelta(seconds=45)
        formatted = self.auditor.format_elapsed_time(time_obj)
        assert formatted == "45s"
        
        # Test minutes and seconds
        time_obj = timedelta(minutes=5, seconds=15)
        formatted = self.auditor.format_elapsed_time(time_obj)
        assert formatted == "5m 15s"
        
        # Test hours, minutes, and seconds
        time_obj = timedelta(hours=2, minutes=30, seconds=10)
        formatted = self.auditor.format_elapsed_time(time_obj)
        assert formatted == "2h 30m 10s"
        
        # Test None
        formatted = self.auditor.format_elapsed_time(None)
        assert formatted == "N/A"
        
    def test_get_timing_summary(self):
        """Test generating timing summary"""
        # Test when audit hasn't started
        summary = self.auditor.get_timing_summary()
        assert summary == "Audit has not started"
        
        # Test running status
        self.auditor.start_timer()
        summary = self.auditor.get_timing_summary()
        assert isinstance(summary, dict)
        assert summary["status"] == "RUNNING"
        assert "start_time" in summary
        assert "elapsed_time" in summary
        
        # Test paused status
        self.auditor.pause_timer()
        summary = self.auditor.get_timing_summary()
        assert summary["status"] == "PAUSED"
        
        # Test completed status
        self.auditor.resume_timer()
        self.auditor.stop_timer()
        summary = self.auditor.get_timing_summary()
        assert summary["status"] == "COMPLETED"
        assert "end_time" in summary
        
    def test_record_phase_time(self):
        """Test recording phase times"""
        # Record times for each phase
        phase_duration = timedelta(seconds=10)
        
        for phase in ["connectivity", "authentication", "config_audit", "risk_assessment", "reporting"]:
            self.auditor.record_phase_time(phase, phase_duration)
            assert self.auditor.phase_times[phase] == phase_duration
            
        # Test invalid phase
        self.auditor.record_phase_time("invalid_phase", phase_duration)
        assert "invalid_phase" not in self.auditor.phase_times
        
    def test_timing_in_workflow(self):
        """Test timing integration in the audit workflow"""
        # Skip patching and use real time - just test the integration
        
        # Setup for test
        self.auditor.phase_times = {
            "connectivity": timedelta(seconds=5),
            "authentication": timedelta(seconds=3),
            "config_audit": timedelta(seconds=10),
            "risk_assessment": timedelta(seconds=2),
            "reporting": timedelta(seconds=1)
        }
        
        # Set timing values manually
        self.auditor.start_time = datetime.now() - timedelta(seconds=30)
        self.auditor.end_time = datetime.now()
        self.auditor.total_pause_duration = timedelta(seconds=5)
        
        # Get timing summary and check it
        timing_summary = self.auditor.get_timing_summary()
            
        # Verify the summary contains expected data
        assert isinstance(timing_summary, dict)
        assert "elapsed_time" in timing_summary
        assert "start_time" in timing_summary
        assert "end_time" in timing_summary
        assert "phase_times" in timing_summary
        
        # Check that all phases are in the summary
        phase_times_dict = timing_summary["phase_times"]
        assert "connectivity" in phase_times_dict
        assert "authentication" in phase_times_dict
        assert "config_audit" in phase_times_dict
        assert "risk_assessment" in phase_times_dict
        assert "reporting" in phase_times_dict
        
        # Verify formatted times are strings
        for phase, time_str in phase_times_dict.items():
            assert isinstance(time_str, str)
            
        # Verify formatted times use the correct format based on duration
        assert self.auditor.format_elapsed_time(timedelta(seconds=5)) == "5s"
        assert self.auditor.format_elapsed_time(timedelta(minutes=1, seconds=5)) == "1m 5s"
            


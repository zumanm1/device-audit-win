#!/usr/bin/env python3
"""
NetAuditPro Progress Tracker Module
Provides comprehensive progress tracking for router and stage-level audit operations
"""

import json
import threading
import time
from datetime import datetime
from typing import Dict, Optional, List


class ProgressTracker:
    """
    Comprehensive progress tracking for NetAuditPro audit operations.
    
    Tracks both router-level progress (which router is being processed)
    and stage-level progress (which stage within the current router).
    
    Features:
    - Router-level progress tracking (1 of 6 routers)
    - Stage-level progress tracking (A1 of A8 stages)
    - Percentage calculations for both levels
    - Thread-safe operations
    - JSON serialization for API responses
    - Progress history tracking
    """
    
    def __init__(self, total_routers: int):
        """
        Initialize the progress tracker.
        
        Args:
            total_routers (int): Total number of routers to be audited
        """
        self.total_routers = total_routers
        self.current_router_index = 0  # 0-based index
        self.current_stage = 0  # 0-based index (0=A1, 1=A2, etc.)
        self.total_stages = 8  # A1 through A8
        self.router_name = ""
        self.stage_name = ""
        self.stage_description = ""
        
        # Stage mapping for display purposes
        self.stage_names = [
            "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"
        ]
        
        self.stage_descriptions = [
            "ICMP Connectivity Test",
            "SSH Connection & Authentication", 
            "Authorization Test",
            "Wait and Confirm Data Collection",
            "Data Collection and Save",
            "Data Processing for Dashboard Updates",
            "Core Telnet Security Analysis",
            "Comprehensive Reporting"
        ]
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Progress history
        self.start_time = datetime.now()
        self.progress_history: List[Dict] = []
        
        # Status tracking
        self.is_completed = False
        self.is_failed = False
        self.error_message = ""
        
    def get_router_progress(self) -> Dict:
        """
        Get current router-level progress information.
        
        Returns:
            dict: Router progress data including current, total, percentage, and name
        """
        with self._lock:
            # Calculate 1-based display numbers
            current_display = self.current_router_index + 1 if self.current_router_index < self.total_routers else self.total_routers
            
            # Calculate percentage
            if self.total_routers > 0:
                percentage = (current_display / self.total_routers) * 100
            else:
                percentage = 0.0
                
            return {
                "current": current_display,
                "total": self.total_routers,
                "percentage": round(percentage, 2),
                "router_name": self.router_name,
                "router_index": self.current_router_index
            }
    
    def get_stage_progress(self) -> Dict:
        """
        Get current stage-level progress information.
        
        Returns:
            dict: Stage progress data including current, total, percentage, and description
        """
        with self._lock:
            # Calculate 1-based display numbers
            current_display = self.current_stage + 1 if self.current_stage < self.total_stages else self.total_stages
            
            # Calculate percentage
            if self.total_stages > 0:
                percentage = (current_display / self.total_stages) * 100
            else:
                percentage = 0.0
                
            # Get stage name and description
            stage_name = self.stage_names[self.current_stage] if self.current_stage < len(self.stage_names) else f"A{current_display}"
            stage_desc = self.stage_descriptions[self.current_stage] if self.current_stage < len(self.stage_descriptions) else self.stage_description
                
            return {
                "current": current_display,
                "total": self.total_stages,
                "percentage": round(percentage, 2),
                "stage_name": stage_name,
                "stage_description": stage_desc,
                "stage_index": self.current_stage
            }
    
    def get_combined_progress(self) -> Dict:
        """
        Get combined router and stage progress information.
        
        Returns:
            dict: Combined progress data with both router and stage information
        """
        router_progress = self.get_router_progress()
        stage_progress = self.get_stage_progress()
        
        # Calculate overall progress (router progress + stage progress within current router)
        if self.total_routers > 0 and self.total_stages > 0:
            router_weight = (self.current_router_index / self.total_routers) * 100
            stage_weight = (stage_progress["percentage"] / self.total_stages) * (100 / self.total_routers)
            overall_percentage = router_weight + stage_weight
        else:
            overall_percentage = 0.0
        
        return {
            "router": router_progress,
            "stage": stage_progress,
            "overall_percentage": round(overall_percentage, 2),
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "error_message": self.error_message,
            "elapsed_time": self._get_elapsed_time()
        }
    
    def update_router(self, router_index: int, router_name: str = "") -> None:
        """
        Update the current router being processed.
        
        Args:
            router_index (int): 0-based index of the current router
            router_name (str): Name of the current router
        """
        with self._lock:
            self.current_router_index = router_index
            self.router_name = router_name
            self.current_stage = 0  # Reset stage when moving to new router
            self.stage_name = ""
            self.stage_description = ""
            
            # Add to history
            self._add_to_history("router_update", {
                "router_index": router_index,
                "router_name": router_name
            })
    
    def update_stage(self, stage_index: int, stage_description: str = "") -> None:
        """
        Update the current stage being processed.
        
        Args:
            stage_index (int): 0-based index of the current stage (0=A1, 1=A2, etc.)
            stage_description (str): Optional custom description for the stage
        """
        with self._lock:
            self.current_stage = stage_index
            self.stage_description = stage_description or (
                self.stage_descriptions[stage_index] if stage_index < len(self.stage_descriptions) else ""
            )
            
            # Add to history
            self._add_to_history("stage_update", {
                "stage_index": stage_index,
                "stage_name": self.stage_names[stage_index] if stage_index < len(self.stage_names) else f"A{stage_index + 1}",
                "stage_description": self.stage_description
            })
    
    def next_stage(self) -> bool:
        """
        Move to the next stage within the current router.
        
        Returns:
            bool: True if successfully moved to next stage, False if already at last stage
        """
        with self._lock:
            if self.current_stage < self.total_stages - 1:
                self.current_stage += 1
                self.stage_description = (
                    self.stage_descriptions[self.current_stage] 
                    if self.current_stage < len(self.stage_descriptions) 
                    else ""
                )
                
                # Add to history
                self._add_to_history("stage_next", {
                    "new_stage_index": self.current_stage,
                    "stage_name": self.stage_names[self.current_stage] if self.current_stage < len(self.stage_names) else f"A{self.current_stage + 1}"
                })
                return True
            return False
    
    def next_router(self) -> bool:
        """
        Move to the next router.
        
        Returns:
            bool: True if successfully moved to next router, False if already at last router
        """
        with self._lock:
            if self.current_router_index < self.total_routers - 1:
                self.current_router_index += 1
                self.current_stage = 0  # Reset to first stage
                self.router_name = ""
                self.stage_description = ""
                
                # Add to history
                self._add_to_history("router_next", {
                    "new_router_index": self.current_router_index
                })
                return True
            return False
    
    def complete_audit(self) -> None:
        """Mark the entire audit as completed."""
        with self._lock:
            self.is_completed = True
            self.current_router_index = self.total_routers
            self.current_stage = self.total_stages
            
            # Add to history
            self._add_to_history("audit_completed", {
                "total_routers": self.total_routers,
                "total_time": self._get_elapsed_time()
            })
    
    def fail_audit(self, error_message: str = "") -> None:
        """
        Mark the audit as failed.
        
        Args:
            error_message (str): Optional error message describing the failure
        """
        with self._lock:
            self.is_failed = True
            self.error_message = error_message
            
            # Add to history
            self._add_to_history("audit_failed", {
                "error_message": error_message,
                "failed_at_router": self.current_router_index,
                "failed_at_stage": self.current_stage
            })
    
    def reset(self) -> None:
        """Reset the progress tracker to initial state."""
        with self._lock:
            self.current_router_index = 0
            self.current_stage = 0
            self.router_name = ""
            self.stage_name = ""
            self.stage_description = ""
            self.is_completed = False
            self.is_failed = False
            self.error_message = ""
            self.start_time = datetime.now()
            self.progress_history.clear()
            
            # Add to history
            self._add_to_history("progress_reset", {})
    
    def get_progress_summary(self) -> str:
        """
        Get a formatted progress summary string.
        
        Returns:
            str: Human-readable progress summary
        """
        router_progress = self.get_router_progress()
        stage_progress = self.get_stage_progress()
        
        return (
            f"Router {router_progress['current']}/{router_progress['total']} "
            f"({router_progress['percentage']:.2f}%) - "
            f"Stage {stage_progress['stage_name']}/{self.total_stages} "
            f"({stage_progress['percentage']:.2f}%)"
        )
    
    def get_detailed_status(self) -> str:
        """
        Get a detailed status string for logging.
        
        Returns:
            str: Detailed status string
        """
        router_progress = self.get_router_progress()
        stage_progress = self.get_stage_progress()
        
        status_parts = [
            f"Router {router_progress['current']}/{router_progress['total']} ({router_progress['percentage']:.2f}%)"
        ]
        
        if router_progress['router_name']:
            status_parts.append(f"[{router_progress['router_name']}]")
            
        status_parts.append(f"Stage {stage_progress['stage_name']}/{self.total_stages} ({stage_progress['percentage']:.2f}%)")
        
        if stage_progress['stage_description']:
            status_parts.append(f"[{stage_progress['stage_description']}]")
        
        return " - ".join(status_parts)
    
    def to_dict(self) -> Dict:
        """
        Convert progress tracker to dictionary for JSON serialization.
        
        Returns:
            dict: Complete progress tracker state
        """
        return {
            "total_routers": self.total_routers,
            "current_router_index": self.current_router_index,
            "current_stage": self.current_stage,
            "total_stages": self.total_stages,
            "router_name": self.router_name,
            "stage_description": self.stage_description,
            "router_progress": self.get_router_progress(),
            "stage_progress": self.get_stage_progress(),
            "combined_progress": self.get_combined_progress(),
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "error_message": self.error_message,
            "start_time": self.start_time.isoformat(),
            "elapsed_time": self._get_elapsed_time(),
            "progress_history": self.progress_history[-10:]  # Last 10 history entries
        }
    
    def to_json(self) -> str:
        """
        Convert progress tracker to JSON string.
        
        Returns:
            str: JSON representation of progress tracker
        """
        return json.dumps(self.to_dict(), indent=2)
    
    def _get_elapsed_time(self) -> float:
        """Get elapsed time since start in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    def _add_to_history(self, event_type: str, data: Dict) -> None:
        """
        Add an event to the progress history.
        
        Args:
            event_type (str): Type of event
            data (dict): Event data
        """
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "router_progress": self.get_router_progress(),
            "stage_progress": self.get_stage_progress()
        }
        
        self.progress_history.append(history_entry)
        
        # Keep only last 50 entries to prevent memory bloat
        if len(self.progress_history) > 50:
            self.progress_history = self.progress_history[-50:]


# Global progress tracker instance (will be initialized when audit starts)
global_progress_tracker: Optional[ProgressTracker] = None


def initialize_progress_tracker(total_routers: int) -> ProgressTracker:
    """
    Initialize the global progress tracker.
    
    Args:
        total_routers (int): Total number of routers to be audited
        
    Returns:
        ProgressTracker: Initialized progress tracker instance
    """
    global global_progress_tracker
    global_progress_tracker = ProgressTracker(total_routers)
    return global_progress_tracker


def get_progress_tracker() -> Optional[ProgressTracker]:
    """
    Get the global progress tracker instance.
    
    Returns:
        ProgressTracker or None: Current progress tracker instance
    """
    return global_progress_tracker


def reset_progress_tracker() -> None:
    """Reset the global progress tracker."""
    global global_progress_tracker
    if global_progress_tracker:
        global_progress_tracker.reset()
    else:
        global_progress_tracker = None


# Progress logging functions
def log_router_progress(progress_tracker: ProgressTracker, log_raw_trace_func=None) -> None:
    """
    Log router-level progress to console and raw trace logs.
    
    Args:
        progress_tracker (ProgressTracker): Progress tracker instance
        log_raw_trace_func (callable): Function to log to raw trace logs
    """
    progress = progress_tracker.get_router_progress()
    
    # Console log with emoji and formatting
    message = f"📍 Processing router {progress['current']} of {progress['total']} ({progress['percentage']:.2f}%): {progress['router_name']}"
    print(message)
    
    # Raw trace log
    if log_raw_trace_func:
        raw_message = f"[PROGRESS] [ROUTER] {progress['current']}/{progress['total']} ({progress['percentage']:.2f}%): {progress['router_name']}"
        log_raw_trace_func(raw_message)


def log_stage_progress(progress_tracker: ProgressTracker, log_raw_trace_func=None) -> None:
    """
    Log stage-level progress to console and raw trace logs.
    
    Args:
        progress_tracker (ProgressTracker): Progress tracker instance
        log_raw_trace_func (callable): Function to log to raw trace logs
    """
    stage_progress = progress_tracker.get_stage_progress()
    
    # Console log with emoji and formatting
    message = f"📍 Stage {stage_progress['stage_name']} of A{progress_tracker.total_stages} ({stage_progress['percentage']:.2f}%): {stage_progress['stage_description']}"
    print(message)
    
    # Raw trace log
    if log_raw_trace_func:
        raw_message = f"[PROGRESS] [STAGE] {stage_progress['stage_name']}/A{progress_tracker.total_stages} ({stage_progress['percentage']:.2f}%): {stage_progress['stage_description']}"
        log_raw_trace_func(raw_message)


def log_combined_progress(progress_tracker: ProgressTracker, log_raw_trace_func=None) -> None:
    """
    Log combined router and stage progress.
    
    Args:
        progress_tracker (ProgressTracker): Progress tracker instance
        log_raw_trace_func (callable): Function to log to raw trace logs
    """
    combined = progress_tracker.get_combined_progress()
    router = combined['router']
    stage = combined['stage']
    
    # Console log with emoji and formatting
    message = (
        f"📊 Progress: Router {router['current']}/{router['total']} ({router['percentage']:.2f}%) - "
        f"Stage {stage['stage_name']}/A{progress_tracker.total_stages} ({stage['percentage']:.2f}%) - "
        f"Overall: {combined['overall_percentage']:.2f}%"
    )
    print(message)
    
    # Raw trace log
    if log_raw_trace_func:
        raw_message = (
            f"[PROGRESS] [COMBINED] Router {router['current']}/{router['total']} ({router['percentage']:.2f}%) | "
            f"Stage {stage['stage_name']}/A{progress_tracker.total_stages} ({stage['percentage']:.2f}%) | "
            f"Overall {combined['overall_percentage']:.2f}%"
        )
        log_raw_trace_func(raw_message)


if __name__ == "__main__":
    # Test the progress tracker
    print("Testing NetAuditPro Progress Tracker...")
    
    # Initialize with 6 routers
    tracker = ProgressTracker(6)
    
    # Test router progress
    tracker.update_router(0, "Cisco 2911")
    print(f"Router Progress: {tracker.get_router_progress()}")
    
    # Test stage progress
    tracker.update_stage(0, "ICMP Connectivity Test")
    print(f"Stage Progress: {tracker.get_stage_progress()}")
    
    # Test combined progress
    print(f"Combined Progress: {tracker.get_combined_progress()}")
    
    # Test progress summary
    print(f"Summary: {tracker.get_progress_summary()}")
    
    # Test JSON serialization
    print(f"JSON: {tracker.to_json()}")
    
    print("Progress Tracker test completed successfully!") 
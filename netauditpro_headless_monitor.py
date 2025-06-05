#!/usr/bin/env python3
"""
NetAuditPro Headless Monitor
Comprehensive monitoring without browser dependencies
"""

import requests
import time
import json
from datetime import datetime
import sys

class NetAuditProMonitor:
    def __init__(self, base_url="http://127.0.0.1:5011"):
        self.base_url = base_url
        self.start_time = time.time()
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def get_progress(self):
        """Get current audit progress"""
        try:
            response = requests.get(f"{self.base_url}/api/progress", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"❌ Progress API error: {response.status_code}")
                return None
        except Exception as e:
            self.log(f"❌ Progress request failed: {e}")
            return None
            
    def get_raw_logs(self):
        """Get raw logs"""
        try:
            response = requests.get(f"{self.base_url}/api/raw-logs", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            return None
            
    def start_audit(self):
        """Start an audit"""
        try:
            response = requests.post(f"{self.base_url}/api/start-audit", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log("🚀 Audit started successfully")
                    return True
                else:
                    self.log(f"❌ Failed to start audit: {data.get('message')}")
                    return False
            else:
                self.log(f"❌ Start audit API error: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Start audit request failed: {e}")
            return False
            
    def monitor_audit(self, max_duration=600):
        """Monitor audit progress"""
        self.log("🤖 Starting audit monitoring...")
        
        # Try to start audit
        if not self.start_audit():
            self.log("❌ Could not start audit - monitoring existing state")
        
        start_time = time.time()
        last_progress = None
        stable_count = 0
        
        while time.time() - start_time < max_duration:
            progress = self.get_progress()
            
            if progress:
                current_status = progress.get('status', 'Unknown')
                completed = progress.get('completed_devices', 0)
                total = progress.get('total_devices', 0)
                percent = progress.get('percent_complete', 0)
                current_device = progress.get('current_device', 'Unknown')
                
                # Log progress if changed
                current_progress_key = f"{completed}-{total}-{current_status}"
                if current_progress_key != last_progress:
                    self.log(f"📊 Progress: {percent:.1f}% ({completed}/{total}) "
                           f"Status: {current_status} Device: {current_device}")
                    last_progress = current_progress_key
                    stable_count = 0
                else:
                    stable_count += 1
                
                # Check for completion
                if current_status == "Completed":
                    self.log("🎉 Audit completed!")
                    
                    # Verify completion is correct
                    if completed < total:
                        self.log(f"⚠️  WARNING: Status is 'Completed' but only {completed}/{total} devices processed")
                        self.log("🔧 This indicates a progress tracking issue that needs fixing")
                    else:
                        self.log(f"✅ All {total} devices processed successfully")
                    
                    break
                    
                # Check if stuck
                if stable_count > 20:  # 20 * 3 seconds = 1 minute of no progress
                    self.log("⚠️  No progress for 1 minute - audit may be stuck")
                    
            else:
                self.log("❌ Could not get progress data")
                
            time.sleep(3)
            
        # Final summary
        self.log("=" * 50)
        self.log("📊 MONITORING SUMMARY")
        self.log("=" * 50)
        
        final_progress = self.get_progress()
        if final_progress:
            self.log(f"Final Status: {final_progress.get('status', 'Unknown')}")
            self.log(f"Devices Processed: {final_progress.get('completed_devices', 0)}/{final_progress.get('total_devices', 0)}")
            self.log(f"Success Rate: {final_progress.get('percent_complete', 0):.1f}%")
            
            status_counts = final_progress.get('status_counts', {})
            self.log(f"Results: Success={status_counts.get('success', 0)}, "
                   f"Warning={status_counts.get('warning', 0)}, "
                   f"Failure={status_counts.get('failure', 0)}")
        
        # Get final raw logs count
        raw_logs = self.get_raw_logs()
        if raw_logs:
            log_count = len(raw_logs.get('logs', []))
            self.log(f"Raw Log Entries: {log_count}")
            
        duration = time.time() - start_time
        self.log(f"Monitoring Duration: {duration:.1f} seconds")
        
        return final_progress

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--duration":
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    else:
        duration = 600
        
    monitor = NetAuditProMonitor()
    result = monitor.monitor_audit(max_duration=duration)
    
    # Exit with appropriate code
    if result and result.get('status') == 'Completed':
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

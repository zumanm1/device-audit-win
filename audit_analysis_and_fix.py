#!/usr/bin/env python3
"""
NetAuditPro Audit Analysis and Fix Script
Analyzes audit results and provides fixes for identified issues
"""

import requests
import json
import time
from datetime import datetime
import sys

class AuditAnalyzer:
    def __init__(self, base_url="http://127.0.0.1:5011"):
        self.base_url = base_url
        self.issues_found = []
        self.recommendations = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def check_api_endpoint(self, endpoint):
        """Check if an API endpoint is accessible"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
            return response.status_code == 200, response
        except Exception as e:
            return False, str(e)
            
    def analyze_audit_progress(self):
        """Analyze the audit progress for inconsistencies"""
        self.log("🔍 Analyzing audit progress...")
        
        # Check progress API
        accessible, response = self.check_api_endpoint("/api/progress")
        if not accessible:
            self.issues_found.append("Progress API not accessible")
            return
            
        try:
            progress_data = response.json()
            self.log(f"Progress Data: {json.dumps(progress_data, indent=2)}")
            
            # Check for inconsistencies
            total_devices = progress_data.get('total_devices', 0)
            completed_devices = progress_data.get('completed_devices', 0)
            percent_complete = progress_data.get('percent_complete', 0)
            status = progress_data.get('status', 'Unknown')
            
            # Issue 1: Device count mismatch
            if total_devices != 6:
                issue = f"Expected 6 devices in inventory, but found {total_devices}"
                self.issues_found.append(issue)
                self.log(f"❌ ISSUE: {issue}")
                
            # Issue 2: Completion logic error
            if status == "Completed" and completed_devices < total_devices:
                issue = f"Status shows 'Completed' but only {completed_devices}/{total_devices} devices processed"
                self.issues_found.append(issue)
                self.log(f"❌ ISSUE: {issue}")
                
            # Issue 3: Percentage calculation error
            expected_percent = (completed_devices / total_devices * 100) if total_devices > 0 else 0
            if abs(percent_complete - expected_percent) > 0.1:
                issue = f"Percentage calculation error: expected {expected_percent:.1f}%, got {percent_complete:.1f}%"
                self.issues_found.append(issue)
                self.log(f"❌ ISSUE: {issue}")
                
        except Exception as e:
            self.issues_found.append(f"Failed to parse progress data: {e}")
            
    def analyze_raw_logs(self):
        """Analyze raw logs for audit process issues"""
        self.log("🔍 Analyzing raw logs...")
        
        accessible, response = self.check_api_endpoint("/api/raw-logs")
        if not accessible:
            self.issues_found.append("Raw logs API not accessible")
            return
            
        try:
            logs_data = response.json()
            logs = logs_data.get('logs', [])
            
            self.log(f"Found {len(logs)} raw log entries")
            
            # Analyze log patterns
            ping_attempts = [log for log in logs if '[PING]' in log]
            ping_successes = [log for log in logs if '[PING_SUCCESS]' in log]
            ping_failures = [log for log in logs if '[PING_FAIL]' in log]
            ssh_tunnels = [log for log in logs if '[SSH_TUNNEL]' in log]
            
            self.log(f"📊 Log Analysis:")
            self.log(f"   • Ping attempts: {len(ping_attempts)}")
            self.log(f"   • Ping successes: {len(ping_successes)}")
            self.log(f"   • Ping failures: {len(ping_failures)}")
            self.log(f"   • SSH tunnel attempts: {len(ssh_tunnels)}")
            
            # Check for missing devices
            expected_devices = 6
            if len(ping_attempts) != expected_devices:
                issue = f"Expected {expected_devices} ping attempts, found {len(ping_attempts)}"
                self.issues_found.append(issue)
                self.log(f"❌ ISSUE: {issue}")
                
            # Check for audit completion
            completion_logs = [log for log in logs if 'Audit completed' in log or 'TIMING.*completed' in log]
            if not completion_logs:
                issue = "No audit completion log found"
                self.issues_found.append(issue)
                self.log(f"❌ ISSUE: {issue}")
            else:
                self.log(f"✅ Audit completion logged: {completion_logs[-1]}")
                
        except Exception as e:
            self.issues_found.append(f"Failed to parse raw logs: {e}")
            
    def check_device_processing(self):
        """Check if all devices were properly processed"""
        self.log("🔍 Checking device processing...")
        
        # Expected devices from inventory
        expected_devices = [
            "Cisco 2911", "Cisco 2921", "Cisco 1941", 
            "Cisco 3750X", "Cisco 2960", "Cisco ASA 5506"
        ]
        
        accessible, response = self.check_api_endpoint("/api/raw-logs")
        if accessible:
            try:
                logs_data = response.json()
                logs = logs_data.get('logs', [])
                
                processed_devices = set()
                for log in logs:
                    for device in expected_devices:
                        if device in log:
                            processed_devices.add(device)
                            
                self.log(f"📱 Devices found in logs: {len(processed_devices)}")
                for device in processed_devices:
                    self.log(f"   ✅ {device}")
                    
                missing_devices = set(expected_devices) - processed_devices
                if missing_devices:
                    issue = f"Missing devices in logs: {', '.join(missing_devices)}"
                    self.issues_found.append(issue)
                    self.log(f"❌ ISSUE: {issue}")
                else:
                    self.log("✅ All expected devices found in logs")
                    
            except Exception as e:
                self.issues_found.append(f"Failed to check device processing: {e}")
                
    def test_audit_controls(self):
        """Test audit control functionality"""
        self.log("🔍 Testing audit controls...")
        
        # Test start audit (should fail if already running)
        try:
            response = requests.post(f"{self.base_url}/api/start-audit", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if not data.get('success', False):
                    self.log("✅ Start audit correctly rejected (audit already running)")
                else:
                    self.log("⚠️  Start audit accepted (might indicate issue)")
            else:
                self.issues_found.append(f"Start audit API returned {response.status_code}")
        except Exception as e:
            self.issues_found.append(f"Failed to test start audit: {e}")
            
        # Test other controls
        for control in ['pause', 'stop', 'reset']:
            try:
                response = requests.post(f"{self.base_url}/api/{control}-audit", timeout=5)
                if response.status_code == 200:
                    self.log(f"✅ {control.title()} audit API accessible")
                else:
                    self.issues_found.append(f"{control.title()} audit API returned {response.status_code}")
            except Exception as e:
                self.issues_found.append(f"Failed to test {control} audit: {e}")
                
    def generate_fixes(self):
        """Generate fixes for identified issues"""
        self.log("🔧 Generating fixes...")
        
        fixes = []
        
        # Fix 1: Progress calculation issue
        if any("Percentage calculation error" in issue for issue in self.issues_found):
            fixes.append({
                "issue": "Progress percentage calculation",
                "fix": "Update progress calculation in /api/progress endpoint",
                "code_location": "Line ~3400 in rr4-router-complete-enhanced-v3.py",
                "suggested_fix": """
# In the progress API endpoint, ensure proper calculation:
percent_complete = (completed_devices / total_devices * 100) if total_devices > 0 else 0
"""
            })
            
        # Fix 2: Completion status logic
        if any("Status shows 'Completed' but only" in issue for issue in self.issues_found):
            fixes.append({
                "issue": "Audit completion status logic",
                "fix": "Fix completion status determination",
                "code_location": "Audit completion logic",
                "suggested_fix": """
# Ensure status is only 'Completed' when all devices are processed:
if completed_devices >= total_devices and audit_thread_active == False:
    status = "Completed"
elif audit_thread_active:
    status = "Running"
else:
    status = "Stopped"
"""
            })
            
        # Fix 3: Device count verification
        if any("Expected 6 devices" in issue for issue in self.issues_found):
            fixes.append({
                "issue": "Device count mismatch",
                "fix": "Verify inventory loading and device counting",
                "code_location": "Inventory loading section",
                "suggested_fix": """
# Add logging to verify inventory loading:
logger.info(f"Loaded {len(devices)} devices from inventory")
for i, device in enumerate(devices, 1):
    logger.info(f"Device {i}: {device.get('name', 'Unknown')}")
"""
            })
            
        return fixes
        
    def create_monitoring_script(self):
        """Create a simple monitoring script for future use"""
        monitoring_script = '''#!/usr/bin/env python3
"""
Simple NetAuditPro Monitor
Monitors audit progress without browser dependencies
"""

import requests
import time
import json
from datetime import datetime

def monitor_audit(base_url="http://127.0.0.1:5011", duration=300):
    """Monitor audit for specified duration (seconds)"""
    start_time = time.time()
    
    print(f"🤖 Starting audit monitoring for {duration} seconds...")
    
    while time.time() - start_time < duration:
        try:
            # Get progress
            response = requests.get(f"{base_url}/api/progress", timeout=5)
            if response.status_code == 200:
                data = response.json()
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Progress: {data.get('percent_complete', 0):.1f}% "
                      f"({data.get('completed_devices', 0)}/{data.get('total_devices', 0)}) "
                      f"Status: {data.get('status', 'Unknown')}")
                
                if data.get('status') == 'Completed':
                    print("🎉 Audit completed!")
                    break
            else:
                print(f"❌ API error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            
        time.sleep(5)
        
    print("✅ Monitoring completed")

if __name__ == "__main__":
    monitor_audit()
'''
        
        with open('simple_audit_monitor.py', 'w') as f:
            f.write(monitoring_script)
            
        self.log("📄 Created simple_audit_monitor.py for future monitoring")
        
    def run_analysis(self):
        """Run complete analysis"""
        self.log("🚀 Starting NetAuditPro Audit Analysis...")
        self.log("=" * 60)
        
        # Run all analysis functions
        self.analyze_audit_progress()
        self.analyze_raw_logs()
        self.check_device_processing()
        self.test_audit_controls()
        
        # Generate report
        self.log("=" * 60)
        self.log("📊 ANALYSIS SUMMARY")
        self.log("=" * 60)
        
        if not self.issues_found:
            self.log("✅ No issues found - audit appears to be working correctly!")
        else:
            self.log(f"❌ Found {len(self.issues_found)} issues:")
            for i, issue in enumerate(self.issues_found, 1):
                self.log(f"   {i}. {issue}")
                
        # Generate fixes
        fixes = self.generate_fixes()
        if fixes:
            self.log("\n🔧 SUGGESTED FIXES:")
            for i, fix in enumerate(fixes, 1):
                self.log(f"\n   Fix {i}: {fix['issue']}")
                self.log(f"   Location: {fix['code_location']}")
                self.log(f"   Solution: {fix['fix']}")
                self.log(f"   Code: {fix['suggested_fix']}")
                
        # Create monitoring script
        self.create_monitoring_script()
        
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "issues_found": self.issues_found,
            "fixes_suggested": fixes,
            "analysis_complete": True
        }
        
        with open('audit_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"\n📄 Analysis report saved to: audit_analysis_report.json")
        
        return len(self.issues_found) == 0

def main():
    analyzer = AuditAnalyzer()
    success = analyzer.run_analysis()
    
    if success:
        print("\n🎉 Analysis completed successfully - no issues found!")
        sys.exit(0)
    else:
        print(f"\n⚠️  Analysis completed - {len(analyzer.issues_found)} issues found")
        sys.exit(1)

if __name__ == "__main__":
    main() 
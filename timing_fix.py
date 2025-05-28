#!/usr/bin/env python3
"""
Timing Fix Script for NetAuditPro
Identifies and fixes timing display issues
"""

import requests
import json
import time
from datetime import datetime

class TimingFixer:
    def __init__(self, base_url="http://127.0.0.1:5011"):
        self.base_url = base_url
        
    def check_timing_api(self):
        """Check the timing API response"""
        print("🔍 Checking Timing API...")
        
        try:
            response = requests.get(f"{self.base_url}/api/timing")
            if response.status_code == 200:
                data = response.json()
                print("✅ Timing API Response:")
                print(json.dumps(data, indent=2))
                
                # Check for timing issues
                timing = data.get('timing', {})
                if timing.get('raw_start_time'):
                    raw_start = timing['raw_start_time']
                    start_time_str = timing.get('start_time', '')
                    
                    # Convert raw timestamp to readable time
                    start_dt = datetime.fromtimestamp(raw_start)
                    current_dt = datetime.now()
                    
                    print(f"\n📊 Timing Analysis:")
                    print(f"   • Raw Start Time: {raw_start}")
                    print(f"   • Converted Start Time: {start_dt.strftime('%H:%M:%S')}")
                    print(f"   • API Start Time String: {start_time_str}")
                    print(f"   • Current System Time: {current_dt.strftime('%H:%M:%S')}")
                    
                    # Check for discrepancies
                    if start_time_str != start_dt.strftime('%H:%M:%S'):
                        print(f"⚠️ TIMING DISCREPANCY DETECTED!")
                        print(f"   API String: {start_time_str}")
                        print(f"   Calculated: {start_dt.strftime('%H:%M:%S')}")
                        return False
                    else:
                        print(f"✅ Timing consistency verified")
                        return True
                else:
                    print("⚠️ No active audit timing found")
                    return True
                    
            else:
                print(f"❌ API Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    def check_progress_api(self):
        """Check the progress API for Quick Stats data"""
        print("\n🔍 Checking Progress API...")
        
        try:
            response = requests.get(f"{self.base_url}/api/progress")
            if response.status_code == 200:
                data = response.json()
                print("✅ Progress API Response:")
                print(json.dumps(data, indent=2))
                
                # Validate Quick Stats data
                total_devices = data.get('total_devices', 0)
                status_counts = data.get('status_counts', {})
                
                print(f"\n📊 Quick Stats Analysis:")
                print(f"   • Total Devices: {total_devices}")
                print(f"   • Successful: {status_counts.get('success', 0)}")
                print(f"   • Violations: {status_counts.get('violations', 0)}")
                print(f"   • Failures: {status_counts.get('failure', 0)}")
                
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    def generate_timing_report(self):
        """Generate a comprehensive timing report"""
        print("\n📋 COMPREHENSIVE TIMING ANALYSIS REPORT")
        print("=" * 60)
        
        # System information
        current_time = datetime.now()
        print(f"🕒 Report Generated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all checks
        timing_ok = self.check_timing_api()
        progress_ok = self.check_progress_api()
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   • Timing API: {'✅ OK' if timing_ok else '❌ ISSUES'}")
        print(f"   • Progress API: {'✅ OK' if progress_ok else '❌ ISSUES'}")
        
        overall_status = timing_ok and progress_ok
        print(f"\n🎯 Overall Status: {'✅ ALL SYSTEMS OK' if overall_status else '⚠️ ISSUES DETECTED'}")
        
        return overall_status

def main():
    """Main execution"""
    print("🔧 NetAuditPro Timing Diagnostic Tool")
    print("=" * 60)
    
    fixer = TimingFixer()
    success = fixer.generate_timing_report()
    
    if success:
        print("\n🎉 All timing systems are functioning correctly!")
    else:
        print("\n⚠️ Timing issues detected - review the report above")
    
    return success

if __name__ == "__main__":
    main() 
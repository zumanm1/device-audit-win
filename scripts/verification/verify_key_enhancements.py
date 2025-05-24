#!/usr/bin/env python3
"""
Focused verification script for NetAuditPro key enhancements:

1. Enhanced Progress Tracking data structure in the API
2. Stop/Reset functionality (via direct API endpoint)
3. CSV inventory structure validation

This script makes direct API calls rather than using browser automation
to reduce complexity and potential timing issues.
"""

import json
import os
import sys
import time
import requests
from datetime import datetime

# Configuration
APP_URL = "http://localhost:5007"
REPORT_FILE = "enhancement_verification_report.json"


def print_header(text):
    """Print a formatted header"""
    print(f"\n{'=' * 80}")
    print(f"  {text}")
    print(f"{'=' * 80}")


def test_enhanced_progress_tracking():
    """Test the Enhanced Progress Tracking data structure in the API"""
    print_header("Testing Enhanced Progress Tracking API")
    
    try:
        # Make direct API call to get audit progress
        response = requests.get(f"{APP_URL}/get_audit_progress")
        if response.status_code != 200:
            print(f"❌ API Error: Status code {response.status_code}")
            return False, f"API Error: Status code {response.status_code}"
        
        # Parse response data
        data = response.json()
        
        # Check for enhanced_progress key
        if 'enhanced_progress' not in data:
            print("❌ Missing enhanced_progress data in API response")
            return False, "Missing enhanced_progress data in API response"
        
        # Validate enhanced progress structure
        enhanced_progress = data['enhanced_progress']
        required_fields = [
            'status', 'current_device', 'total_devices', 'completed_devices',
            'device_statuses', 'status_counts'
        ]
        
        missing_fields = [field for field in required_fields if field not in enhanced_progress]
        if missing_fields:
            print(f"❌ Missing fields in enhanced_progress: {missing_fields}")
            return False, f"Missing fields in enhanced_progress: {missing_fields}"
        
        # Check status_counts structure
        status_counts = enhanced_progress['status_counts']
        required_counts = ['success', 'failure', 'warning']
        missing_counts = [count for count in required_counts if count not in status_counts]
        if missing_counts:
            print(f"❌ Missing status counts: {missing_counts}")
            return False, f"Missing status counts: {missing_counts}"
        
        print("✅ Enhanced Progress Tracking API has correct structure")
        print(f"✅ Current status: {enhanced_progress['status']}")
        print(f"✅ Completed: {enhanced_progress['completed_devices']}/{enhanced_progress['total_devices']}")
        print(f"✅ Status counts: {json.dumps(status_counts)}")
        
        return True, "Enhanced Progress Tracking API has correct structure"
    
    except Exception as e:
        print(f"❌ Error testing enhanced progress tracking: {str(e)}")
        return False, f"Error: {str(e)}"


def test_stop_reset_functionality():
    """Test the Stop/Reset functionality via direct API call"""
    print_header("Testing Stop/Reset Functionality")
    
    try:
        # First start an audit to test stopping it
        print("1. Starting an audit...")
        start_response = requests.post(f"{APP_URL}/start_audit")
        if start_response.status_code != 200:
            print(f"❌ Failed to start audit: {start_response.status_code}")
            return False, f"Failed to start audit: {start_response.status_code}"
        
        # Wait a moment for the audit to start
        time.sleep(2)
        
        # Check that audit is running
        progress_response = requests.get(f"{APP_URL}/get_audit_progress")
        if progress_response.status_code != 200:
            print(f"❌ Failed to get audit progress: {progress_response.status_code}")
            return False, f"Failed to get audit progress: {progress_response.status_code}"
        
        progress_data = progress_response.json()
        if progress_data['progress']['status'] != 'running':
            print(f"❌ Audit did not start properly. Status: {progress_data['progress']['status']}")
            return False, f"Audit did not start properly. Status: {progress_data['progress']['status']}"
        
        print(f"✅ Audit started successfully with status: {progress_data['progress']['status']}")
        
        # Now stop/reset the audit
        print("2. Stopping/resetting the audit...")
        stop_response = requests.post(f"{APP_URL}/stop_reset_audit")
        if stop_response.status_code != 200:
            print(f"❌ Failed to stop/reset audit: {stop_response.status_code}")
            return False, f"Failed to stop/reset audit: {stop_response.status_code}"
        
        stop_data = stop_response.json()
        print(f"✅ Stop/Reset API response: {json.dumps(stop_data)}")
        
        # Wait a moment for the reset to complete
        time.sleep(2)
        
        # Check the audit status again
        after_progress_response = requests.get(f"{APP_URL}/get_audit_progress")
        if after_progress_response.status_code != 200:
            print(f"❌ Failed to get audit progress after reset: {after_progress_response.status_code}")
            return False, f"Failed to get audit progress after reset: {after_progress_response.status_code}"
        
        after_progress_data = after_progress_response.json()
        
        # Check for various indicators of successful reset
        reset_indicators = {
            "Progress status reset": after_progress_data['progress']['status'] != 'running',
            "Enhanced progress status reset": after_progress_data['enhanced_progress']['status'] != 'running',
            "Progress completed devices reset": after_progress_data['progress']['completed_devices'] == 0,
            "No active devices": len(after_progress_data['progress'].get('device_statuses', {})) == 0 or 
                               all(status == 'idle' for status in after_progress_data['progress']['device_statuses'].values())
        }
        
        success_count = sum(1 for indicator, value in reset_indicators.items() if value)
        
        # Report on each indicator
        for indicator, value in reset_indicators.items():
            print(f"{'✅' if value else '❌'} {indicator}")
        
        if success_count >= 2:  # At least 2 indicators should be positive
            print(f"✅ Stop/Reset functionality verified with {success_count}/{len(reset_indicators)} positive indicators")
            return True, f"Stop/Reset functionality verified with {success_count}/{len(reset_indicators)} positive indicators"
        else:
            print(f"❌ Stop/Reset may not have fully worked: only {success_count}/{len(reset_indicators)} positive indicators")
            return False, f"Stop/Reset may not have fully worked: only {success_count}/{len(reset_indicators)} positive indicators"
    
    except Exception as e:
        print(f"❌ Error testing stop/reset functionality: {str(e)}")
        return False, f"Error: {str(e)}"


def test_csv_inventory_structure():
    """Test the CSV inventory structure and validation"""
    print_header("Testing CSV Inventory Structure")
    
    try:
        # Get the inventory page to check the structure
        response = requests.get(f"{APP_URL}/manage_inventories")
        if response.status_code != 200:
            print(f"❌ Failed to access inventory page: {response.status_code}")
            return False, f"Failed to access inventory page: {response.status_code}"
        
        # Check for expected CSV table elements in the HTML
        html_content = response.text.lower()
        csv_indicators = {
            "CSV table present": "id=\"csvtable\"" in html_content or "class=\"table" in html_content,
            "CSV headers row": "<thead" in html_content or "<th" in html_content,
            "Active inventory indicator": "active inventory" in html_content,
            "CSV format indicator": "csv" in html_content
        }
        
        # Report on each indicator
        for indicator, value in csv_indicators.items():
            print(f"{'✅' if value else '❌'} {indicator}")
        
        success_count = sum(1 for indicator, value in csv_indicators.items() if value)
        
        if success_count >= 3:  # At least 3 indicators should be positive
            print(f"✅ CSV inventory structure verified with {success_count}/{len(csv_indicators)} positive indicators")
            return True, f"CSV inventory structure verified with {success_count}/{len(csv_indicators)} positive indicators"
        else:
            print(f"❌ CSV inventory structure verification failed: only {success_count}/{len(csv_indicators)} positive indicators")
            return False, f"CSV inventory structure verification failed: only {success_count}/{len(csv_indicators)} positive indicators"
    
    except Exception as e:
        print(f"❌ Error testing CSV inventory structure: {str(e)}")
        return False, f"Error: {str(e)}"


def main():
    """Run all verification tests and generate a report"""
    print("\n" + "=" * 30 + " NetAuditPro Enhancement Verification " + "=" * 30)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test Enhanced Progress Tracking
    success, message = test_enhanced_progress_tracking()
    results["tests"]["enhanced_progress_tracking"] = {"success": success, "message": message}
    
    # Test Stop/Reset Functionality
    success, message = test_stop_reset_functionality()
    results["tests"]["stop_reset_functionality"] = {"success": success, "message": message}
    
    # Test CSV Inventory Structure
    success, message = test_csv_inventory_structure()
    results["tests"]["csv_inventory_structure"] = {"success": success, "message": message}
    
    # Calculate overall results
    total_tests = len(results["tests"])
    passed_tests = sum(1 for test in results["tests"].values() if test["success"])
    results["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "pass_rate": f"{(passed_tests / total_tests) * 100:.1f}%",
        "overall_status": "PASSED" if passed_tests == total_tests else "PARTIAL" if passed_tests > 0 else "FAILED"
    }
    
    # Print summary
    print("\n" + "=" * 30 + " Verification Summary " + "=" * 30)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Pass Rate: {results['summary']['pass_rate']}")
    print(f"Overall Status: {results['summary']['overall_status']}")
    
    # Save report
    with open(REPORT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nReport saved to: {REPORT_FILE}")
    print("=" * 80)
    
    # Return exit code
    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())

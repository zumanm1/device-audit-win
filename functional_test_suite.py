#!/usr/bin/env python3
"""
Comprehensive Functional Test Suite for NetAuditPro
Tests all major functionality and identifies issues
"""

import requests
import json
import time
import sys
import subprocess
from typing import Dict, List, Any
from datetime import datetime

class NetAuditProFunctionalTester:
    def __init__(self, base_url: str = "http://127.0.0.1:5011"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.issues_found = []
        
    def log_test(self, test_name: str, status: str, details: str = "", issue: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if status == "FAIL" and issue:
            self.issues_found.append({
                "test": test_name,
                "issue": issue,
                "details": details
            })
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if issue:
            print(f"   Issue: {issue}")
    
    def test_application_startup(self):
        """Test if application starts and responds"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                self.log_test("Application Startup", "PASS", f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Application Startup", "FAIL", 
                            f"Status: {response.status_code}", 
                            "Application not responding correctly")
                return False
        except Exception as e:
            self.log_test("Application Startup", "FAIL", 
                        f"Exception: {str(e)}", 
                        "Cannot connect to application")
            return False
    
    def test_dashboard_page(self):
        """Test dashboard page loads correctly"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if "Quick Stats" in response.text and "NetAuditPro" in response.text:
                self.log_test("Dashboard Page", "PASS", "Dashboard loads with expected content")
                return True
            else:
                self.log_test("Dashboard Page", "FAIL", 
                            "Missing expected content", 
                            "Dashboard missing Quick Stats or title")
                return False
        except Exception as e:
            self.log_test("Dashboard Page", "FAIL", f"Exception: {str(e)}", "Dashboard page error")
            return False
    
    def test_quick_stats_section(self):
        """Test Quick Stats section specifically"""
        try:
            response = self.session.get(f"{self.base_url}/")
            content = response.text
            
            # Check for Quick Stats section
            if "Quick Stats" not in content:
                self.log_test("Quick Stats Section", "FAIL", 
                            "Quick Stats section not found", 
                            "Missing Quick Stats section")
                return False
            
            # Check for three columns
            if content.count('col-4') < 3:
                self.log_test("Quick Stats Layout", "FAIL", 
                            f"Found {content.count('col-4')} col-4 elements, expected at least 3", 
                            "Quick Stats not using 3-column layout")
                return False
            
            # Check for expected labels
            expected_labels = ["Total Devices", "Successful", "Violations"]
            missing_labels = []
            for label in expected_labels:
                if label not in content:
                    missing_labels.append(label)
            
            if missing_labels:
                self.log_test("Quick Stats Labels", "FAIL", 
                            f"Missing labels: {missing_labels}", 
                            "Quick Stats missing expected labels")
                return False
            
            self.log_test("Quick Stats Section", "PASS", "All Quick Stats elements present")
            return True
            
        except Exception as e:
            self.log_test("Quick Stats Section", "FAIL", f"Exception: {str(e)}", "Quick Stats test error")
            return False
    
    def test_api_endpoints(self):
        """Test critical API endpoints"""
        endpoints = [
            "/api/progress",
            "/api/progress-detailed", 
            "/api/progress-summary",
            "/api/live-logs",
            "/api/raw-logs",
            "/api/timing"
        ]
        
        all_passed = True
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log_test(f"API {endpoint}", "PASS", f"Returns valid JSON")
                    except:
                        self.log_test(f"API {endpoint}", "WARN", 
                                    "Returns non-JSON response", 
                                    "API endpoint returns non-JSON")
                        all_passed = False
                else:
                    self.log_test(f"API {endpoint}", "FAIL", 
                                f"Status: {response.status_code}", 
                                f"API endpoint {endpoint} not working")
                    all_passed = False
            except Exception as e:
                self.log_test(f"API {endpoint}", "FAIL", 
                            f"Exception: {str(e)}", 
                            f"API endpoint {endpoint} error")
                all_passed = False
        
        return all_passed
    
    def test_progress_api_structure(self):
        """Test progress API returns expected structure"""
        try:
            response = self.session.get(f"{self.base_url}/api/progress")
            data = response.json()
            
            expected_fields = [
                "completed_devices", "current_device", "elapsed_time", 
                "percent_complete", "status", "status_counts", 
                "success", "total_devices"
            ]
            
            missing_fields = []
            for field in expected_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log_test("Progress API Structure", "FAIL", 
                            f"Missing fields: {missing_fields}", 
                            "Progress API missing expected fields")
                return False
            
            # Check status_counts structure
            if "status_counts" in data and isinstance(data["status_counts"], dict):
                expected_counts = ["success", "failure", "warning", "violations"]
                missing_counts = []
                for count in expected_counts:
                    if count not in data["status_counts"]:
                        missing_counts.append(count)
                
                if missing_counts:
                    self.log_test("Progress API Status Counts", "FAIL", 
                                f"Missing status counts: {missing_counts}", 
                                "Progress API missing violations count")
                    return False
                else:
                    self.log_test("Progress API Structure", "PASS", 
                                "All expected fields present including violations")
                    return True
            else:
                self.log_test("Progress API Structure", "FAIL", 
                            "status_counts not found or not dict", 
                            "Progress API status_counts structure issue")
                return False
                
        except Exception as e:
            self.log_test("Progress API Structure", "FAIL", 
                        f"Exception: {str(e)}", 
                        "Progress API structure test error")
            return False
    
    def test_inventory_loading(self):
        """Test inventory loading functionality"""
        try:
            response = self.session.get(f"{self.base_url}/inventory")
            if response.status_code == 200:
                content = response.text
                if "routers01.csv" in content or "inventory" in content.lower():
                    self.log_test("Inventory Loading", "PASS", "Inventory page accessible")
                    return True
                else:
                    self.log_test("Inventory Loading", "WARN", 
                                "Inventory page loads but content unclear", 
                                "Inventory page content issue")
                    return False
            else:
                self.log_test("Inventory Loading", "FAIL", 
                            f"Status: {response.status_code}", 
                            "Inventory page not accessible")
                return False
        except Exception as e:
            self.log_test("Inventory Loading", "FAIL", 
                        f"Exception: {str(e)}", 
                        "Inventory loading test error")
            return False
    
    def test_settings_page(self):
        """Test settings page functionality"""
        try:
            response = self.session.get(f"{self.base_url}/settings")
            if response.status_code == 200:
                content = response.text
                if "JUMP_HOST" in content or "settings" in content.lower():
                    self.log_test("Settings Page", "PASS", "Settings page accessible")
                    return True
                else:
                    self.log_test("Settings Page", "WARN", 
                                "Settings page loads but content unclear", 
                                "Settings page content issue")
                    return False
            else:
                self.log_test("Settings Page", "FAIL", 
                            f"Status: {response.status_code}", 
                            "Settings page not accessible")
                return False
        except Exception as e:
            self.log_test("Settings Page", "FAIL", 
                        f"Exception: {str(e)}", 
                        "Settings page test error")
            return False
    
    def test_audit_controls(self):
        """Test audit control API endpoints"""
        controls = [
            ("start-audit", "POST"),
            ("pause-audit", "POST"), 
            ("stop-audit", "POST"),
            ("reset-audit", "POST")
        ]
        
        all_passed = True
        for control, method in controls:
            try:
                if method == "POST":
                    response = self.session.post(f"{self.base_url}/api/{control}")
                else:
                    response = self.session.get(f"{self.base_url}/api/{control}")
                
                # We expect these to return JSON responses, even if they fail
                if response.status_code in [200, 400, 500]:
                    try:
                        data = response.json()
                        if "success" in data or "error" in data:
                            self.log_test(f"Audit Control {control}", "PASS", 
                                        f"Returns structured response")
                        else:
                            self.log_test(f"Audit Control {control}", "WARN", 
                                        "Response structure unclear", 
                                        f"Audit control {control} response format issue")
                            all_passed = False
                    except:
                        self.log_test(f"Audit Control {control}", "WARN", 
                                    "Non-JSON response", 
                                    f"Audit control {control} returns non-JSON")
                        all_passed = False
                else:
                    self.log_test(f"Audit Control {control}", "FAIL", 
                                f"Status: {response.status_code}", 
                                f"Audit control {control} unexpected status")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Audit Control {control}", "FAIL", 
                            f"Exception: {str(e)}", 
                            f"Audit control {control} error")
                all_passed = False
        
        return all_passed
    
    def test_static_resources(self):
        """Test that static resources load correctly"""
        try:
            response = self.session.get(f"{self.base_url}/")
            content = response.text
            
            # Check for Bootstrap CSS
            if "bootstrap" not in content.lower():
                self.log_test("Static Resources", "WARN", 
                            "Bootstrap CSS not detected", 
                            "Missing Bootstrap CSS")
                return False
            
            # Check for Font Awesome
            if "font-awesome" not in content.lower() and "fontawesome" not in content.lower():
                self.log_test("Static Resources", "WARN", 
                            "Font Awesome not detected", 
                            "Missing Font Awesome")
                return False
            
            # Check for Chart.js
            if "chart.js" not in content.lower():
                self.log_test("Static Resources", "WARN", 
                            "Chart.js not detected", 
                            "Missing Chart.js")
                return False
            
            self.log_test("Static Resources", "PASS", "All expected resources detected")
            return True
            
        except Exception as e:
            self.log_test("Static Resources", "FAIL", 
                        f"Exception: {str(e)}", 
                        "Static resources test error")
            return False
    
    def run_all_tests(self):
        """Run all functional tests"""
        print("🧪 Starting Comprehensive Functional Testing...")
        print("=" * 60)
        
        # Core functionality tests
        if not self.test_application_startup():
            print("❌ Application startup failed - stopping tests")
            return False
        
        self.test_dashboard_page()
        self.test_quick_stats_section()
        self.test_api_endpoints()
        self.test_progress_api_structure()
        self.test_inventory_loading()
        self.test_settings_page()
        self.test_audit_controls()
        self.test_static_resources()
        
        # Generate summary
        self.generate_summary()
        return len(self.issues_found) == 0
    
    def generate_summary(self):
        """Generate test summary and recommendations"""
        print("\n" + "=" * 60)
        print("🧪 FUNCTIONAL TESTING SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"📊 Test Results:")
        print(f"   • Total Tests: {total_tests}")
        print(f"   • Passed: {passed} ✅")
        print(f"   • Failed: {failed} ❌")
        print(f"   • Warnings: {warnings} ⚠️")
        print(f"   • Success Rate: {(passed/total_tests)*100:.1f}%")
        
        if self.issues_found:
            print(f"\n🔧 Issues Found ({len(self.issues_found)}):")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"   {i}. {issue['test']}: {issue['issue']}")
                if issue['details']:
                    print(f"      Details: {issue['details']}")
        else:
            print("\n🎉 No critical issues found!")
        
        # Save detailed results
        with open("functional_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed,
                    "failed": failed,
                    "warnings": warnings,
                    "success_rate": (passed/total_tests)*100
                },
                "test_results": self.test_results,
                "issues_found": self.issues_found
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: functional_test_results.json")

def main():
    """Main test execution"""
    tester = NetAuditProFunctionalTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️ Found {len(tester.issues_found)} issues that need attention")
        sys.exit(1)

if __name__ == "__main__":
    main() 
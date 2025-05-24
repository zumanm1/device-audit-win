#!/usr/bin/env python3
"""
Test script for Enhanced NetAuditPro Features
Tests command logging, navigation, and down device reporting
"""

import os
import sys
import time
import requests
import subprocess
from threading import Thread

class NetAuditProTester:
    def __init__(self, base_url="http://localhost:5009"):
        self.base_url = base_url
        self.app_process = None
        
    def start_application(self):
        """Start the NetAuditPro application"""
        print("🚀 Starting NetAuditPro Enhanced Application...")
        try:
            self.app_process = subprocess.Popen([
                'python3', 'rr4-router-complete-enhanced-v2.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a bit for the application to start
            time.sleep(5)
            print("✅ Application started successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to start application: {e}")
            return False
    
    def stop_application(self):
        """Stop the NetAuditPro application"""
        if self.app_process:
            self.app_process.terminate()
            self.app_process.wait()
            print("🛑 Application stopped")
    
    def test_web_interface(self):
        """Test the web interface accessibility"""
        print("\n🌐 Testing Web Interface...")
        
        endpoints_to_test = [
            ('/', 'Home Page'),
            ('/settings', 'Settings Page'),
            ('/manage_inventories', 'Inventory Management'),
            ('/command_logs', 'Command Logs'),
            ('/device_status', 'Device Status API'),
            ('/down_devices', 'Down Devices API'),
            ('/enhanced_summary', 'Enhanced Summary API')
        ]
        
        results = []
        for endpoint, description in endpoints_to_test:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ {description}: OK (Status: {response.status_code})")
                    results.append(True)
                else:
                    print(f"⚠️  {description}: Warning (Status: {response.status_code})")
                    results.append(False)
            except Exception as e:
                print(f"❌ {description}: Failed ({e})")
                results.append(False)
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n📊 Web Interface Test Results: {success_rate:.1f}% success rate")
        return success_rate > 80
    
    def test_file_structure(self):
        """Test that all required files exist"""
        print("\n📁 Testing File Structure...")
        
        required_files = [
            'rr4-router-complete-enhanced-v2.py',
            'inventories/network-inventory-current-status.csv',
            'NETWORK_AUDIT_TASK_MANAGEMENT.md',
            'templates/base_layout.html',
            'templates/command_logs.html',
            'templates/view_command_log.html',
            'templates/index_page.html'
        ]
        
        results = []
        for file_path in required_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"✅ {file_path}: Exists ({size} bytes)")
                results.append(True)
            else:
                print(f"❌ {file_path}: Missing")
                results.append(False)
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n📊 File Structure Test Results: {success_rate:.1f}% success rate")
        return success_rate == 100
    
    def test_inventory_data(self):
        """Test inventory data structure"""
        print("\n📋 Testing Inventory Data...")
        
        inventory_file = 'inventories/network-inventory-current-status.csv'
        try:
            with open(inventory_file, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')
                
                if len(lines) >= 2:  # Header + at least one data row
                    header = lines[0]
                    expected_columns = ['router_name', 'router_ip', 'router_type', 'status']
                    
                    has_required_columns = all(col in header for col in expected_columns)
                    if has_required_columns:
                        print(f"✅ Inventory structure: Valid ({len(lines)-1} devices)")
                        
                        # Check for UP and DOWN devices
                        up_devices = [line for line in lines[1:] if ',UP' in line]
                        down_devices = [line for line in lines[1:] if ',DOWN' in line]
                        
                        print(f"📊 Device Status: {len(up_devices)} UP, {len(down_devices)} DOWN")
                        return True
                    else:
                        print(f"❌ Inventory structure: Missing required columns")
                        return False
                else:
                    print(f"❌ Inventory structure: Insufficient data")
                    return False
                    
        except Exception as e:
            print(f"❌ Inventory test failed: {e}")
            return False
    
    def test_command_logging_directories(self):
        """Test that command logging directories can be created"""
        print("\n📝 Testing Command Logging Setup...")
        
        try:
            # Test if we can create the command logs directory
            command_logs_dir = "COMMAND-LOGS"
            if not os.path.exists(command_logs_dir):
                os.makedirs(command_logs_dir)
                print(f"✅ Created command logs directory: {command_logs_dir}")
            else:
                print(f"✅ Command logs directory exists: {command_logs_dir}")
            
            # Test write permissions
            test_file = os.path.join(command_logs_dir, "test_write_permissions.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("✅ Command logs directory: Write permissions OK")
            
            return True
            
        except Exception as e:
            print(f"❌ Command logging setup failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🧪 Starting Comprehensive NetAuditPro Enhancement Tests\n")
        print("=" * 60)
        
        test_results = []
        
        # Test 1: File Structure
        test_results.append(self.test_file_structure())
        
        # Test 2: Inventory Data
        test_results.append(self.test_inventory_data())
        
        # Test 3: Command Logging Setup
        test_results.append(self.test_command_logging_directories())
        
        # Test 4: Start Application and Test Web Interface
        if self.start_application():
            test_results.append(self.test_web_interface())
            self.stop_application()
        else:
            test_results.append(False)
        
        # Calculate overall results
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        success_rate = passed_tests / total_tests * 100
        
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Failed Tests: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 95:
            print("🏆 EXCELLENT: All enhancements working perfectly!")
        elif success_rate >= 80:
            print("✅ GOOD: Most enhancements working well")
        elif success_rate >= 60:
            print("⚠️  FAIR: Some issues need attention")
        else:
            print("❌ POOR: Significant issues detected")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = NetAuditProTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1) 
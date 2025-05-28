#!/usr/bin/env python3
"""
Comprehensive Test Runner for Quick Stats Functionality
Runs unit tests, Playwright tests, and Puppeteer tests
"""

import sys
import os
import subprocess
import time
import asyncio
from pathlib import Path

class TestRunner:
    """Comprehensive test runner for Quick Stats functionality"""
    
    def __init__(self):
        self.test_results = {
            'unit_tests': {'passed': False, 'details': ''},
            'playwright_tests': {'passed': False, 'details': ''},
            'puppeteer_tests': {'passed': False, 'details': ''}
        }
        
    def print_header(self, title):
        """Print a formatted header"""
        print("\n" + "=" * 80)
        print(f"🧪 {title}")
        print("=" * 80)
        
    def print_summary(self):
        """Print overall test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['passed'])
        
        print(f"📋 Test Categories: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📈 Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        
        print("\n📝 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            print(f"   • {test_name.replace('_', ' ').title()}: {status}")
            if result['details']:
                print(f"     Details: {result['details']}")
                
        overall_success = all(result['passed'] for result in self.test_results.values())
        
        if overall_success:
            print("\n🎉 ALL TESTS PASSED! Quick Stats functionality is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Please review the results above.")
            
        return overall_success
        
    def run_unit_tests(self):
        """Run Python unit tests"""
        self.print_header("UNIT TESTS (Python unittest)")
        
        try:
            # Check if test file exists
            if not os.path.exists('test_quick_stats.py'):
                raise FileNotFoundError("test_quick_stats.py not found")
                
            # Run unit tests
            result = subprocess.run(
                [sys.executable, 'test_quick_stats.py'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
                
            success = result.returncode == 0
            self.test_results['unit_tests']['passed'] = success
            
            if not success:
                self.test_results['unit_tests']['details'] = f"Exit code: {result.returncode}"
                
        except subprocess.TimeoutExpired:
            print("❌ Unit tests timed out after 60 seconds")
            self.test_results['unit_tests']['details'] = "Timeout after 60 seconds"
        except FileNotFoundError as e:
            print(f"❌ Unit test file not found: {e}")
            self.test_results['unit_tests']['details'] = str(e)
        except Exception as e:
            print(f"❌ Unit tests failed with error: {e}")
            self.test_results['unit_tests']['details'] = str(e)
            
    def run_playwright_tests(self):
        """Run Playwright tests"""
        self.print_header("PLAYWRIGHT TESTS (Browser Automation)")
        
        try:
            # Check if test file exists
            if not os.path.exists('test_quick_stats_playwright.py'):
                raise FileNotFoundError("test_quick_stats_playwright.py not found")
                
            # Check if playwright is installed
            try:
                import playwright
            except ImportError:
                print("⚠️  Playwright not installed. Installing...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'playwright'], check=True)
                subprocess.run([sys.executable, '-m', 'playwright', 'install'], check=True)
                
            # Run Playwright tests
            result = subprocess.run(
                [sys.executable, 'test_quick_stats_playwright.py'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
                
            success = result.returncode == 0
            self.test_results['playwright_tests']['passed'] = success
            
            if not success:
                self.test_results['playwright_tests']['details'] = f"Exit code: {result.returncode}"
                
        except subprocess.TimeoutExpired:
            print("❌ Playwright tests timed out after 120 seconds")
            self.test_results['playwright_tests']['details'] = "Timeout after 120 seconds"
        except FileNotFoundError as e:
            print(f"❌ Playwright test file not found: {e}")
            self.test_results['playwright_tests']['details'] = str(e)
        except Exception as e:
            print(f"❌ Playwright tests failed with error: {e}")
            self.test_results['playwright_tests']['details'] = str(e)
            
    def run_puppeteer_tests(self):
        """Run Puppeteer tests"""
        self.print_header("PUPPETEER TESTS (Node.js Browser Automation)")
        
        try:
            # Check if test file exists
            if not os.path.exists('test_quick_stats_puppeteer.js'):
                raise FileNotFoundError("test_quick_stats_puppeteer.js not found")
                
            # Check if Node.js is available
            try:
                subprocess.run(['node', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ Node.js not found. Please install Node.js to run Puppeteer tests.")
                self.test_results['puppeteer_tests']['details'] = "Node.js not available"
                return
                
            # Check if puppeteer is installed
            try:
                subprocess.run(['npm', 'list', 'puppeteer'], capture_output=True, check=True)
            except subprocess.CalledProcessError:
                print("⚠️  Puppeteer not installed. Installing...")
                subprocess.run(['npm', 'install', 'puppeteer'], check=True)
                
            # Run Puppeteer tests
            result = subprocess.run(
                ['node', 'test_quick_stats_puppeteer.js'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
                
            success = result.returncode == 0
            self.test_results['puppeteer_tests']['passed'] = success
            
            if not success:
                self.test_results['puppeteer_tests']['details'] = f"Exit code: {result.returncode}"
                
        except subprocess.TimeoutExpired:
            print("❌ Puppeteer tests timed out after 120 seconds")
            self.test_results['puppeteer_tests']['details'] = "Timeout after 120 seconds"
        except FileNotFoundError as e:
            print(f"❌ Puppeteer test file not found: {e}")
            self.test_results['puppeteer_tests']['details'] = str(e)
        except Exception as e:
            print(f"❌ Puppeteer tests failed with error: {e}")
            self.test_results['puppeteer_tests']['details'] = str(e)
            
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        self.print_header("PREREQUISITES CHECK")
        
        checks = []
        
        # Check Python
        try:
            python_version = sys.version.split()[0]
            print(f"✅ Python: {python_version}")
            checks.append(True)
        except Exception as e:
            print(f"❌ Python check failed: {e}")
            checks.append(False)
            
        # Check main application file
        if os.path.exists('rr4-router-complete-enhanced-v3.py'):
            print("✅ Main application file: Found")
            checks.append(True)
        else:
            print("❌ Main application file: Not found")
            checks.append(False)
            
        # Check test files
        test_files = [
            'test_quick_stats.py',
            'test_quick_stats_playwright.py', 
            'test_quick_stats_puppeteer.js'
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                print(f"✅ Test file {test_file}: Found")
                checks.append(True)
            else:
                print(f"❌ Test file {test_file}: Not found")
                checks.append(False)
                
        # Check Node.js (optional)
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js: {result.stdout.strip()}")
            else:
                print("⚠️  Node.js: Not available (Puppeteer tests will be skipped)")
        except FileNotFoundError:
            print("⚠️  Node.js: Not available (Puppeteer tests will be skipped)")
            
        all_critical_checks_passed = all(checks[:4])  # Python + app file + 2 Python test files
        
        if all_critical_checks_passed:
            print("\n✅ All critical prerequisites met")
        else:
            print("\n❌ Some critical prerequisites missing")
            
        return all_critical_checks_passed
        
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Quick Stats Testing Suite")
        print(f"📅 Test execution started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites check failed. Cannot proceed with testing.")
            return False
            
        # Run all test suites
        self.run_unit_tests()
        self.run_playwright_tests()
        self.run_puppeteer_tests()
        
        # Print summary
        overall_success = self.print_summary()
        
        print(f"\n📅 Test execution completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return overall_success

def main():
    """Main function"""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 
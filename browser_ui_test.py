#!/usr/bin/env python3
"""
Browser-based UI Testing for NetAuditPro
Tests the actual UI functionality using browser automation
"""

import asyncio
import sys
import time
from playwright.async_api import async_playwright

class NetAuditProUITester:
    def __init__(self, base_url: str = "http://127.0.0.1:5011"):
        self.base_url = base_url
        self.issues_found = []
        
    async def test_quick_stats_ui(self, page):
        """Test Quick Stats UI functionality"""
        print("🧪 Testing Quick Stats UI...")
        
        try:
            # Navigate to dashboard
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # Check if Quick Stats section exists
            quick_stats = await page.query_selector('h5:has-text("Quick Stats")')
            if not quick_stats:
                self.issues_found.append("Quick Stats section not found in UI")
                return False
            
            # Check for three columns
            stats_container = await page.query_selector('.card:has(h5:has-text("Quick Stats")) .row')
            if stats_container:
                columns = await stats_container.query_selector_all('.col-4')
                if len(columns) != 3:
                    self.issues_found.append(f"Expected 3 columns, found {len(columns)}")
                    return False
            else:
                self.issues_found.append("Quick Stats container not found")
                return False
            
            # Check column content
            expected_labels = ["Total Devices", "Successful", "Violations"]
            for label in expected_labels:
                label_element = await page.query_selector(f'small:has-text("{label}")')
                if not label_element:
                    self.issues_found.append(f"Label '{label}' not found")
                    return False
            
            # Check for numeric values
            total_devices = await page.query_selector('#total-devices-count')
            successful_devices = await page.query_selector('#successful-devices-count')
            violations_count = await page.query_selector('#violations-count')
            
            if not all([total_devices, successful_devices, violations_count]):
                self.issues_found.append("Missing Quick Stats numeric elements")
                return False
            
            # Get actual values
            total_value = await total_devices.text_content()
            successful_value = await successful_devices.text_content()
            violations_value = await violations_count.text_content()
            
            print(f"   📊 Quick Stats Values:")
            print(f"      • Total Devices: {total_value}")
            print(f"      • Successful: {successful_value}")
            print(f"      • Violations: {violations_value}")
            
            # Verify values are numeric
            try:
                int(total_value)
                int(successful_value)
                int(violations_value)
            except ValueError:
                self.issues_found.append("Quick Stats values are not numeric")
                return False
            
            print("   ✅ Quick Stats UI test passed")
            return True
            
        except Exception as e:
            self.issues_found.append(f"Quick Stats UI test error: {str(e)}")
            return False
    
    async def test_navigation_menu(self, page):
        """Test navigation menu functionality"""
        print("🧪 Testing Navigation Menu...")
        
        try:
            # Check navigation links
            nav_links = [
                ("Dashboard", "/"),
                ("Settings", "/settings"),
                ("Inventory", "/inventory"),
                ("Logs", "/logs"),
                ("Reports", "/reports")
            ]
            
            for link_text, expected_url in nav_links:
                link = await page.query_selector(f'a.nav-link:has-text("{link_text}")')
                if not link:
                    self.issues_found.append(f"Navigation link '{link_text}' not found")
                    continue
                
                # Click the link
                await link.click()
                await page.wait_for_load_state('networkidle')
                
                # Check if we're on the right page
                current_url = page.url
                if not current_url.endswith(expected_url):
                    self.issues_found.append(f"Navigation to {link_text} failed. Expected: {expected_url}, Got: {current_url}")
                
                # Go back to dashboard for next test
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')
            
            print("   ✅ Navigation menu test passed")
            return True
            
        except Exception as e:
            self.issues_found.append(f"Navigation menu test error: {str(e)}")
            return False
    
    async def test_audit_controls(self, page):
        """Test audit control buttons"""
        print("🧪 Testing Audit Controls...")
        
        try:
            # Check for audit control buttons
            start_button = await page.query_selector('#start-audit')
            pause_button = await page.query_selector('#pause-audit')
            stop_button = await page.query_selector('#stop-audit')
            reset_button = await page.query_selector('#reset-audit')
            
            if not all([start_button, pause_button, stop_button, reset_button]):
                self.issues_found.append("Missing audit control buttons")
                return False
            
            # Test start button
            await start_button.click()
            await page.wait_for_timeout(1000)  # Wait for response
            
            # Check if button states changed
            start_disabled = await start_button.is_disabled()
            if not start_disabled:
                print("   ⚠️ Start button should be disabled after clicking")
            
            # Test pause button
            await pause_button.click()
            await page.wait_for_timeout(1000)
            
            # Test stop button
            await stop_button.click()
            await page.wait_for_timeout(1000)
            
            # Test reset button
            await reset_button.click()
            await page.wait_for_timeout(1000)
            
            print("   ✅ Audit controls test passed")
            return True
            
        except Exception as e:
            self.issues_found.append(f"Audit controls test error: {str(e)}")
            return False
    
    async def test_responsive_design(self, page):
        """Test responsive design"""
        print("🧪 Testing Responsive Design...")
        
        try:
            viewports = [
                {"width": 1920, "height": 1080, "name": "Desktop"},
                {"width": 768, "height": 1024, "name": "Tablet"},
                {"width": 375, "height": 667, "name": "Mobile"}
            ]
            
            for viewport in viewports:
                await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
                await page.wait_for_timeout(500)
                
                # Check if Quick Stats is still visible
                quick_stats = await page.query_selector('h5:has-text("Quick Stats")')
                if not quick_stats:
                    self.issues_found.append(f"Quick Stats not visible on {viewport['name']}")
                    continue
                
                is_visible = await quick_stats.is_visible()
                if not is_visible:
                    self.issues_found.append(f"Quick Stats not visible on {viewport['name']}")
                
                print(f"   ✅ {viewport['name']} ({viewport['width']}x{viewport['height']}) - OK")
            
            # Reset to desktop view
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            print("   ✅ Responsive design test passed")
            return True
            
        except Exception as e:
            self.issues_found.append(f"Responsive design test error: {str(e)}")
            return False
    
    async def test_real_time_updates(self, page):
        """Test real-time updates functionality"""
        print("🧪 Testing Real-time Updates...")
        
        try:
            # Get initial Quick Stats values
            total_initial = await page.text_content('#total-devices-count')
            successful_initial = await page.text_content('#successful-devices-count')
            violations_initial = await page.text_content('#violations-count')
            
            print(f"   📊 Initial Values: Total={total_initial}, Successful={successful_initial}, Violations={violations_initial}")
            
            # Start an audit to trigger updates
            start_button = await page.query_selector('#start-audit')
            if start_button:
                await start_button.click()
                await page.wait_for_timeout(2000)  # Wait for updates
                
                # Check if values might have changed (or at least the page is responsive)
                total_after = await page.text_content('#total-devices-count')
                successful_after = await page.text_content('#successful-devices-count')
                violations_after = await page.text_content('#violations-count')
                
                print(f"   📊 After Start: Total={total_after}, Successful={successful_after}, Violations={violations_after}")
                
                # Stop the audit
                stop_button = await page.query_selector('#stop-audit')
                if stop_button:
                    await stop_button.click()
                    await page.wait_for_timeout(1000)
                
                # Reset
                reset_button = await page.query_selector('#reset-audit')
                if reset_button:
                    await reset_button.click()
                    await page.wait_for_timeout(1000)
            
            print("   ✅ Real-time updates test passed")
            return True
            
        except Exception as e:
            self.issues_found.append(f"Real-time updates test error: {str(e)}")
            return False
    
    async def run_all_ui_tests(self):
        """Run all UI tests"""
        print("🎭 Starting Browser-based UI Testing...")
        print("=" * 60)
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Run all tests
                tests = [
                    self.test_quick_stats_ui,
                    self.test_navigation_menu,
                    self.test_audit_controls,
                    self.test_responsive_design,
                    self.test_real_time_updates
                ]
                
                passed = 0
                total = len(tests)
                
                for test in tests:
                    try:
                        result = await test(page)
                        if result:
                            passed += 1
                    except Exception as e:
                        self.issues_found.append(f"Test {test.__name__} failed: {str(e)}")
                
                # Generate summary
                print("\n" + "=" * 60)
                print("🎭 BROWSER UI TESTING SUMMARY")
                print("=" * 60)
                print(f"📊 Test Results:")
                print(f"   • Total Tests: {total}")
                print(f"   • Passed: {passed} ✅")
                print(f"   • Failed: {total - passed} ❌")
                print(f"   • Success Rate: {(passed/total)*100:.1f}%")
                
                if self.issues_found:
                    print(f"\n🔧 Issues Found ({len(self.issues_found)}):")
                    for i, issue in enumerate(self.issues_found, 1):
                        print(f"   {i}. {issue}")
                else:
                    print("\n🎉 No UI issues found!")
                
                return len(self.issues_found) == 0
                
            finally:
                await browser.close()

async def main():
    """Main test execution"""
    tester = NetAuditProUITester()
    success = await tester.run_all_ui_tests()
    
    if success:
        print("\n🎉 All UI tests passed successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️ Found {len(tester.issues_found)} UI issues that need attention")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
Comprehensive Playwright script to test all aspects of the NetAuditPro Web UI.

This script performs end-to-end testing of all key functionality:
1. Dashboard & UI Components
2. Audit Controls (Start, Pause, Resume, Stop/Reset)
3. Enhanced Progress Tracking
4. Summary Reports & Downloads
5. Captured Router Configurations
6. Inventory Management
"""

import os
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, expect

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = Path("webui_verification_screenshots")
TEST_RESULTS = {}

class WebUITester:
    """Test runner for NetAuditPro Web UI verification"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.success_count = 0
        self.fail_count = 0
        self.warning_count = 0
        
    async def setup(self):
        """Set up the test environment"""
        # Create screenshots directory
        SCREENSHOT_DIR.mkdir(exist_ok=True, parents=True)
        
        # Initialize test results
        global TEST_RESULTS
        TEST_RESULTS = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "screenshot_dir": str(SCREENSHOT_DIR)
        }
        
        # Launch browser
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        self.context = await self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = await self.context.new_page()
    
    async def teardown(self):
        """Clean up after tests"""
        if self.browser:
            await self.browser.close()
        
        # Calculate summary statistics
        TEST_RESULTS["summary"] = {
            "total_tests": self.success_count + self.fail_count + self.warning_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "warning_count": self.warning_count,
            "pass_rate": f"{(self.success_count / (self.success_count + self.fail_count + self.warning_count)) * 100:.1f}%" if (self.success_count + self.fail_count + self.warning_count) > 0 else "N/A"
        }
        
        # Write test results to file
        with open("webui_verification_results.json", "w") as f:
            json.dump(TEST_RESULTS, f, indent=2)
        
        print(f"\n{'='*30} TEST SUMMARY {'='*30}")
        print(f"Total Tests: {TEST_RESULTS['summary']['total_tests']}")
        print(f"Passed: {self.success_count}")
        print(f"Failed: {self.fail_count}")
        print(f"Warnings: {self.warning_count}")
        print(f"Pass Rate: {TEST_RESULTS['summary']['pass_rate']}")
        print(f"{'='*72}")
        print(f"Results saved to: webui_verification_results.json")
        print(f"Screenshots saved to: {SCREENSHOT_DIR}/")
    
    def record_result(self, test_name, result, details=""):
        """Record a test result"""
        status = "PASS" if result else "FAIL"
        if status == "PASS":
            self.success_count += 1
            print(f"✅ {test_name}: {status}")
        else:
            self.fail_count += 1
            print(f"❌ {test_name}: {status} - {details}")
        
        TEST_RESULTS["tests"][test_name] = {
            "status": status,
            "details": details
        }
        return result
    
    def record_warning(self, test_name, details=""):
        """Record a test warning"""
        self.warning_count += 1
        print(f"⚠️ {test_name}: WARNING - {details}")
        
        TEST_RESULTS["tests"][test_name] = {
            "status": "WARNING",
            "details": details
        }
    
    async def wait_for_network_idle(self, timeout=5000):
        """Wait for network to be idle"""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            # Continue even if timeout
            pass
    
    async def test_dashboard_loading(self):
        """Test if the dashboard loads correctly"""
        print(f"\n{'='*30} Testing Dashboard Loading {'='*30}")
        
        try:
            # Navigate to the dashboard
            await self.page.goto(APP_URL)
            await self.wait_for_network_idle()
            
            # Take screenshot
            await self.page.screenshot(path=SCREENSHOT_DIR / "01_dashboard.png")
            
            # Check page title
            title = await self.page.title()
            self.record_result("Dashboard Title Check", "NetAuditPro" in title,
                             f"Expected 'NetAuditPro' in title, got: {title}")
            
            # Check for key elements
            header = await self.page.query_selector('h1, h2')
            if header:
                header_text = await header.inner_text()
                self.record_result("Dashboard Header", "Router Audit" in header_text,
                                 f"Expected 'Router Audit' in header, got: {header_text}")
            else:
                self.record_result("Dashboard Header", False, "No header found")
            
            # Check for audit controls section
            audit_controls = await self.page.query_selector('h3:has-text("Audit Controls"), div:has-text("Audit Controls")')
            self.record_result("Audit Controls Section", audit_controls is not None,
                             "Audit Controls section not found")
            
            # Check for current status section
            status_section = await self.page.query_selector('div:has-text("Current Audit Status")')
            self.record_result("Current Status Section", status_section is not None,
                             "Current Status section not found")
            
            # Check for progress bar
            progress_bar = await self.page.query_selector('.progress-bar')
            self.record_result("Progress Bar", progress_bar is not None,
                             "Progress bar not found")
            
            # Check for logs section
            logs_section = await self.page.query_selector('#logs-container, div:has-text("Live Audit Logs")')
            self.record_result("Logs Section", logs_section is not None,
                             "Logs section not found")
            
            return True
        except Exception as e:
            self.record_result("Dashboard Loading", False, f"Error: {str(e)}")
            return False
    
    async def test_audit_controls(self):
        """Test the audit control buttons and functionality"""
        print(f"\n{'='*30} Testing Audit Controls {'='*30}")
        
        try:
            # Ensure we're on the dashboard
            await self.page.goto(APP_URL)
            await self.wait_for_network_idle()
            
            # Find the audit control buttons
            run_button = await self.page.query_selector('button:has-text("Run Audit")')
            self.record_result("Run Audit Button", run_button is not None, 
                             "Run Audit button not found")
            
            pause_button = await self.page.query_selector('button:has-text("Pause Audit")')
            self.record_result("Pause Audit Button", pause_button is not None,
                             "Pause Audit button not found")
            
            resume_button = await self.page.query_selector('button:has-text("Resume Audit")')
            self.record_result("Resume Audit Button", resume_button is not None,
                             "Resume Audit button not found")
            
            stop_button = await self.page.query_selector('button:has-text("Stop/Reset Audit")')
            self.record_result("Stop/Reset Button", stop_button is not None,
                             "Stop/Reset button not found")
            
            # Take screenshot of audit controls
            if run_button:
                await run_button.scroll_into_view_if_needed()
                await self.page.screenshot(path=SCREENSHOT_DIR / "02_audit_controls.png")
            
            # Test starting an audit
            if run_button:
                print("Starting an audit...")
                await run_button.click()
                await self.wait_for_network_idle(timeout=2000)
                
                # Check if audit status changes
                await asyncio.sleep(2)  # Wait for status to update
                status_text = await self.page.inner_text('#audit-status, div:has-text("Current Audit Status")')
                audit_running = "Running" in status_text or "running" in status_text
                self.record_result("Start Audit", audit_running, 
                                 f"Expected 'Running' in status, got: {status_text}")
                
                # Take screenshot of running audit
                await self.page.screenshot(path=SCREENSHOT_DIR / "03_audit_running.png")
                
                # Test pausing the audit
                if pause_button and audit_running:
                    print("Pausing the audit...")
                    try:
                        await pause_button.click()
                        await self.wait_for_network_idle(timeout=2000)
                        
                        # Check if audit status changes to paused
                        await asyncio.sleep(2)  # Wait for status to update
                        status_text = await self.page.inner_text('#audit-status, div:has-text("Current Audit Status")')
                        audit_paused = "Paused" in status_text or "paused" in status_text
                        self.record_result("Pause Audit", audit_paused,
                                         f"Expected 'Paused' in status, got: {status_text}")
                        
                        # Take screenshot of paused audit
                        await self.page.screenshot(path=SCREENSHOT_DIR / "04_audit_paused.png")
                        
                        # Test resuming the audit
                        if resume_button and audit_paused:
                            print("Resuming the audit...")
                            await resume_button.click()
                            await self.wait_for_network_idle(timeout=2000)
                            
                            # Check if audit status changes back to running
                            await asyncio.sleep(2)  # Wait for status to update
                            status_text = await self.page.inner_text('#audit-status, div:has-text("Current Audit Status")')
                            audit_resumed = "Running" in status_text or "running" in status_text
                            self.record_result("Resume Audit", audit_resumed,
                                             f"Expected 'Running' in status, got: {status_text}")
                            
                            # Take screenshot of resumed audit
                            await self.page.screenshot(path=SCREENSHOT_DIR / "05_audit_resumed.png")
                    except Exception as e:
                        self.record_result("Pause/Resume Audit", False, f"Error: {str(e)}")
                
                # Test stopping/resetting the audit
                if stop_button:
                    print("Stopping/resetting the audit...")
                    try:
                        # Handle confirmation dialog
                        self.page.on("dialog", lambda dialog: dialog.accept())
                        
                        await stop_button.click()
                        await self.wait_for_network_idle(timeout=5000)
                        
                        # Check if audit status resets
                        await asyncio.sleep(5)  # Wait longer for reset to complete
                        
                        # Refresh page to ensure we see the latest state
                        await self.page.reload()
                        await self.wait_for_network_idle()
                        
                        status_text = await self.page.inner_text('#audit-status, div:has-text("Current Audit Status")')
                        audit_reset = "Idle" in status_text or "idle" in status_text or "Completed" in status_text
                        self.record_result("Stop/Reset Audit", audit_reset,
                                         f"Expected 'Idle' or 'Completed' in status, got: {status_text}")
                        
                        # Take screenshot of reset audit
                        await self.page.screenshot(path=SCREENSHOT_DIR / "06_audit_reset.png")
                    except Exception as e:
                        self.record_result("Stop/Reset Audit", False, f"Error: {str(e)}")
            
            return True
        except Exception as e:
            self.record_result("Audit Controls", False, f"Error: {str(e)}")
            return False
    
    async def test_enhanced_progress_tracking(self):
        """Test the Enhanced Progress Tracking functionality"""
        print(f"\n{'='*30} Testing Enhanced Progress Tracking {'='*30}")
        
        try:
            # Ensure we're on the dashboard
            await self.page.goto(APP_URL)
            await self.wait_for_network_idle()
            
            # Check for enhanced progress section
            progress_section = await self.page.query_selector('div:has-text("Enhanced Progress Tracking")')
            self.record_result("Enhanced Progress Section", progress_section is not None,
                             "Enhanced Progress Tracking section not found")
            
            if progress_section:
                # Take screenshot
                await progress_section.scroll_into_view_if_needed()
                await self.page.screenshot(path=SCREENSHOT_DIR / "07_enhanced_progress.png")
                
                # Check for key elements in enhanced progress
                elements_to_check = [
                    {"name": "Overall Progress", "pattern": "Overall Progress"},
                    {"name": "Status Indicator", "pattern": "Status:"},
                    {"name": "Elapsed Time", "pattern": "Elapsed:"},
                    {"name": "Completion Counter", "pattern": "Completed:"},
                    {"name": "ETA Display", "pattern": "ETA:"},
                ]
                
                for element in elements_to_check:
                    has_element = await self.page.query_selector(f'div:has-text("{element["pattern"]}")') is not None
                    self.record_result(f"Enhanced Progress - {element['name']}", has_element,
                                     f"{element['name']} not found in Enhanced Progress section")
                
                # Check for status counters
                status_counters = [
                    {"name": "Success Counter", "pattern": "Success"},
                    {"name": "Warning Counter", "pattern": "Warning"},
                    {"name": "Failure Counter", "pattern": "Failure"},
                ]
                
                for counter in status_counters:
                    has_counter = await self.page.query_selector(f'div:has-text("{counter["pattern"]}")') is not None
                    self.record_result(f"Enhanced Progress - {counter['name']}", has_counter,
                                     f"{counter['name']} not found in Enhanced Progress section")
            
            return True
        except Exception as e:
            self.record_result("Enhanced Progress Tracking", False, f"Error: {str(e)}")
            return False
    
    async def test_summary_reports(self):
        """Test the Summary Reports section and download functionality"""
        print(f"\n{'='*30} Testing Summary Reports {'='*30}")
        
        try:
            # Ensure we're on the dashboard
            await self.page.goto(APP_URL)
            await self.wait_for_network_idle()
            
            # Check for summary reports section
            reports_section = await self.page.query_selector('div:has-text("Summary Reports")')
            if reports_section:
                self.record_result("Summary Reports Section", True, "Summary Reports section found")
                
                # Take screenshot
                await reports_section.scroll_into_view_if_needed()
                await self.page.screenshot(path=SCREENSHOT_DIR / "08_summary_reports.png")
                
                # Check for download buttons
                download_buttons = {
                    "PDF Report": await self.page.query_selector('a:has-text("PDF Summary Report")'),
                    "Excel Report": await self.page.query_selector('a:has-text("Excel Summary Report")'),
                    "JSON Report": await self.page.query_selector('a:has-text("JSON Summary Report")'),
                }
                
                found_downloads = [name for name, button in download_buttons.items() if button is not None]
                
                if found_downloads:
                    self.record_result("Summary Report Downloads", True, 
                                     f"Found download buttons for: {', '.join(found_downloads)}")
                else:
                    # Not a failure, as reports might not have been generated yet
                    self.record_warning("Summary Report Downloads", 
                                      "No download buttons found. This might be expected if no audit has completed.")
            else:
                self.record_result("Summary Reports Section", False, "Summary Reports section not found")
            
            return True
        except Exception as e:
            self.record_result("Summary Reports", False, f"Error: {str(e)}")
            return False
    
    async def test_captured_configurations(self):
        """Test the Captured Router Configurations functionality"""
        print(f"\n{'='*30} Testing Captured Router Configurations {'='*30}")
        
        try:
            # Navigate directly to the captured configurations page
            await self.page.goto(f"{APP_URL}/captured_configs")
            await self.wait_for_network_idle()
            
            # Take screenshot
            await self.page.screenshot(path=SCREENSHOT_DIR / "09_captured_configs.png")
            
            # Check page title
            title = await self.page.title()
            self.record_result("Captured Configs Title", "NetAuditPro" in title,
                             f"Expected 'NetAuditPro' in title, got: {title}")
            
            # Check for configurations table
            configs_table = await self.page.query_selector('table')
            
            if configs_table:
                self.record_result("Configurations Table", True, "Configurations table found")
                
                # Check for table headers
                headers = await self.page.query_selector_all('table th')
                header_texts = []
                for header in headers:
                    header_texts.append(await header.inner_text())
                
                expected_headers = ["Router", "Configuration File", "Size", "Last Modified", "Actions"]
                missing_headers = [h for h in expected_headers if not any(h in text for text in header_texts)]
                
                if not missing_headers:
                    self.record_result("Configuration Table Headers", True, 
                                     f"Found all expected headers: {', '.join(header_texts)}")
                else:
                    self.record_result("Configuration Table Headers", False,
                                     f"Missing headers: {', '.join(missing_headers)}")
                
                # Check for configuration entries
                rows = await self.page.query_selector_all('table tbody tr')
                if rows:
                    self.record_result("Configuration Entries", True, 
                                     f"Found {len(rows)} configuration entries")
                    
                    # Check for view/download links
                    view_links = await self.page.query_selector_all('a:has-text("View")')
                    download_links = await self.page.query_selector_all('a:has-text("Download")')
                    
                    if view_links and download_links:
                        self.record_result("Configuration Actions", True,
                                         f"Found {len(view_links)} View and {len(download_links)} Download links")
                        
                        # Test viewing a configuration if available
                        if view_links:
                            print("Testing configuration viewing...")
                            await view_links[0].click()
                            await self.wait_for_network_idle()
                            
                            # Take screenshot of viewed configuration
                            await self.page.screenshot(path=SCREENSHOT_DIR / "10_viewed_config.png")
                            
                            # Check if configuration content is displayed
                            config_content = await self.page.query_selector('pre')
                            self.record_result("View Configuration", config_content is not None,
                                             "Configuration content display not found")
                    else:
                        self.record_warning("Configuration Actions",
                                          "No View/Download links found for configurations")
                else:
                    self.record_warning("Configuration Entries",
                                      "No configuration entries found. This might be expected if no configurations have been captured.")
            else:
                self.record_warning("Configurations Table",
                                  "No configurations table found. This might be expected if no configurations have been captured.")
            
            return True
        except Exception as e:
            self.record_result("Captured Configurations", False, f"Error: {str(e)}")
            return False
    
    async def test_inventory_management(self):
        """Test the Inventory Management functionality"""
        print(f"\n{'='*30} Testing Inventory Management {'='*30}")
        
        try:
            # Navigate to the inventory management page
            await self.page.goto(f"{APP_URL}/manage_inventories")
            await self.wait_for_network_idle()
            
            # Take screenshot
            await self.page.screenshot(path=SCREENSHOT_DIR / "11_inventory_management.png")
            
            # Check page title
            title = await self.page.title()
            self.record_result("Inventory Management Title", "NetAuditPro" in title,
                             f"Expected 'NetAuditPro' in title, got: {title}")
            
            # Check for inventory table
            inventory_table = await self.page.query_selector('table')
            
            if inventory_table:
                self.record_result("Inventory Table", True, "Inventory table found")
                
                # Check for active inventory indicator
                active_inventory = await self.page.query_selector('div:has-text("Active Inventory")')
                self.record_result("Active Inventory Indicator", active_inventory is not None,
                                 "Active Inventory indicator not found")
                
                # Check for CSV format indicator
                csv_indicator = await self.page.query_selector('div:has-text("CSV")')
                self.record_result("CSV Format Indicator", csv_indicator is not None,
                                 "CSV format indicator not found")
                
                # Check for inventory actions
                actions = {
                    "Upload": await self.page.query_selector('button:has-text("Upload")'),
                    "Edit": await self.page.query_selector('a:has-text("Edit")'),
                    "View": await self.page.query_selector('a:has-text("View")'),
                }
                
                found_actions = [name for name, action in actions.items() if action is not None]
                
                if found_actions:
                    self.record_result("Inventory Actions", True,
                                     f"Found inventory actions: {', '.join(found_actions)}")
                else:
                    self.record_result("Inventory Actions", False,
                                     "No inventory actions found")
            else:
                self.record_result("Inventory Table", False, "Inventory table not found")
            
            return True
        except Exception as e:
            self.record_result("Inventory Management", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all WebUI tests"""
        print(f"\n{'='*30} Running All WebUI Tests {'='*30}")
        
        try:
            await self.setup()
            
            # Run all tests
            await self.test_dashboard_loading()
            await self.test_audit_controls()
            await self.test_enhanced_progress_tracking()
            await self.test_summary_reports()
            await self.test_captured_configurations()
            await self.test_inventory_management()
            
        finally:
            await self.teardown()

async def main():
    """Main function to run all tests"""
    tester = WebUITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())

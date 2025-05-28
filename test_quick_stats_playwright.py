#!/usr/bin/env python3
"""
Playwright Tests for Quick Stats UI Functionality
Tests the visual rendering and behavior of the Quick Stats section
"""

import asyncio
import sys
import os
import time
import subprocess
import threading
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class QuickStatsPlaywrightTest:
    """Playwright tests for Quick Stats functionality"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.app_process = None
        self.base_url = "http://127.0.0.1:5011"
        
    async def setup(self):
        """Set up Playwright browser and start application"""
        print("🎭 Setting up Playwright tests...")
        
        # Start the application in background
        await self.start_application()
        
        # Launch browser
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Wait for application to be ready
        await self.wait_for_application()
        
    async def start_application(self):
        """Start the NetAuditPro application"""
        print("🚀 Starting NetAuditPro application...")
        
        # Start application in background
        self.app_process = subprocess.Popen(
            [sys.executable, "rr4-router-complete-enhanced-v3.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Give application time to start
        await asyncio.sleep(5)
        
    async def wait_for_application(self):
        """Wait for application to be accessible"""
        print("⏳ Waiting for application to be ready...")
        
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = await self.page.goto(self.base_url, timeout=5000)
                if response and response.status == 200:
                    print("✅ Application is ready")
                    return
            except Exception as e:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)
                else:
                    raise Exception(f"Application failed to start: {e}")
                    
    async def test_quick_stats_section_exists(self):
        """Test that Quick Stats section exists on the page"""
        print("🧪 Testing Quick Stats section existence...")
        
        await self.page.goto(self.base_url)
        
        # Check if Quick Stats card exists
        quick_stats_card = await self.page.query_selector('h5:has-text("Quick Stats")')
        assert quick_stats_card is not None, "Quick Stats section not found"
        
        print("✅ Quick Stats section exists")
        
    async def test_quick_stats_three_columns(self):
        """Test that Quick Stats has three columns"""
        print("🧪 Testing Quick Stats three-column layout...")
        
        await self.page.goto(self.base_url)
        
        # Find the Quick Stats card
        quick_stats_card = await self.page.query_selector('h5:has-text("Quick Stats")')
        parent_card = await quick_stats_card.query_selector('xpath=ancestor::div[contains(@class, "card")]')
        
        # Check for three columns (col-4 classes)
        columns = await parent_card.query_selector_all('.col-4')
        assert len(columns) == 3, f"Expected 3 columns, found {len(columns)}"
        
        print("✅ Quick Stats has three columns")
        
    async def test_quick_stats_column_labels(self):
        """Test that Quick Stats columns have correct labels"""
        print("🧪 Testing Quick Stats column labels...")
        
        await self.page.goto(self.base_url)
        
        # Check for expected labels
        expected_labels = ["Total Devices", "Successful", "Violations"]
        
        for label in expected_labels:
            label_element = await self.page.query_selector(f'small:has-text("{label}")')
            assert label_element is not None, f"Label '{label}' not found"
            
        print("✅ All Quick Stats labels are present")
        
    async def test_quick_stats_values_are_numbers(self):
        """Test that Quick Stats display numeric values"""
        print("🧪 Testing Quick Stats numeric values...")
        
        await self.page.goto(self.base_url)
        
        # Find all h4 elements in Quick Stats (the numeric values)
        quick_stats_card = await self.page.query_selector('h5:has-text("Quick Stats")')
        parent_card = await quick_stats_card.query_selector('xpath=ancestor::div[contains(@class, "card")]')
        value_elements = await parent_card.query_selector_all('h4')
        
        assert len(value_elements) == 3, f"Expected 3 values, found {len(value_elements)}"
        
        for i, element in enumerate(value_elements):
            text = await element.text_content()
            assert text.isdigit(), f"Value {i+1} is not numeric: {text}"
            
        print("✅ All Quick Stats values are numeric")
        
    async def test_quick_stats_color_coding(self):
        """Test that Quick Stats have correct color coding"""
        print("🧪 Testing Quick Stats color coding...")
        
        await self.page.goto(self.base_url)
        
        # Find Quick Stats values and check their classes
        quick_stats_card = await self.page.query_selector('h5:has-text("Quick Stats")')
        parent_card = await quick_stats_card.query_selector('xpath=ancestor::div[contains(@class, "card")]')
        value_elements = await parent_card.query_selector_all('h4')
        
        # Expected color classes
        expected_classes = ["text-primary", "text-success", "text-danger"]
        
        for i, element in enumerate(value_elements):
            class_attr = await element.get_attribute('class')
            assert expected_classes[i] in class_attr, f"Element {i+1} missing expected class {expected_classes[i]}"
            
        print("✅ Quick Stats have correct color coding")
        
    async def test_quick_stats_initial_values(self):
        """Test Quick Stats initial values before audit"""
        print("🧪 Testing Quick Stats initial values...")
        
        await self.page.goto(self.base_url)
        
        # Get the values
        quick_stats_card = await self.page.query_selector('h5:has-text("Quick Stats")')
        parent_card = await quick_stats_card.query_selector('xpath=ancestor::div[contains(@class, "card")]')
        value_elements = await parent_card.query_selector_all('h4')
        
        values = []
        for element in value_elements:
            text = await element.text_content()
            values.append(int(text))
            
        # Total Devices should be > 0 (from inventory)
        assert values[0] > 0, f"Total Devices should be > 0, got {values[0]}"
        
        # Successful should be 0 initially
        assert values[1] == 0, f"Successful should be 0 initially, got {values[1]}"
        
        # Violations should be 0 initially
        assert values[2] == 0, f"Violations should be 0 initially, got {values[2]}"
        
        print(f"✅ Initial values: Total={values[0]}, Successful={values[1]}, Violations={values[2]}")
        
    async def test_quick_stats_responsive_layout(self):
        """Test Quick Stats responsive layout"""
        print("🧪 Testing Quick Stats responsive layout...")
        
        await self.page.goto(self.base_url)
        
        # Test different viewport sizes
        viewports = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 768, "height": 1024},   # Tablet
            {"width": 375, "height": 667}     # Mobile
        ]
        
        for viewport in viewports:
            await self.page.set_viewport_size(viewport)
            await asyncio.sleep(0.5)  # Allow layout to adjust
            
            # Check if Quick Stats is still visible
            quick_stats = await self.page.query_selector('h5:has-text("Quick Stats")')
            assert quick_stats is not None, f"Quick Stats not visible at {viewport['width']}x{viewport['height']}"
            
        print("✅ Quick Stats responsive layout works")
        
    async def test_quick_stats_accessibility(self):
        """Test Quick Stats accessibility features"""
        print("🧪 Testing Quick Stats accessibility...")
        
        await self.page.goto(self.base_url)
        
        # Check for proper heading structure
        quick_stats_heading = await self.page.query_selector('h5:has-text("Quick Stats")')
        assert quick_stats_heading is not None, "Quick Stats heading not found"
        
        # Check for icon accessibility
        icon = await quick_stats_heading.query_selector('i.fas.fa-chart-bar')
        assert icon is not None, "Quick Stats icon not found"
        
        # Check that values have descriptive labels
        labels = await self.page.query_selector_all('small')
        label_texts = [await label.text_content() for label in labels]
        
        required_labels = ["Total Devices", "Successful", "Violations"]
        for required_label in required_labels:
            assert any(required_label in text for text in label_texts), f"Required label '{required_label}' not found"
            
        print("✅ Quick Stats accessibility features present")
        
    async def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up Playwright tests...")
        
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
            
        # Stop application
        if self.app_process:
            self.app_process.terminate()
            self.app_process.wait()
            
    async def run_all_tests(self):
        """Run all Playwright tests"""
        print("🎭 Starting Playwright Tests for Quick Stats...")
        print("=" * 60)
        
        tests = [
            self.test_quick_stats_section_exists,
            self.test_quick_stats_three_columns,
            self.test_quick_stats_column_labels,
            self.test_quick_stats_values_are_numbers,
            self.test_quick_stats_color_coding,
            self.test_quick_stats_initial_values,
            self.test_quick_stats_responsive_layout,
            self.test_quick_stats_accessibility
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                await test()
                passed += 1
            except Exception as e:
                print(f"❌ {test.__name__} failed: {e}")
                failed += 1
                
        print("\n" + "=" * 60)
        print(f"🎭 Playwright Tests Summary:")
        print(f"   • Tests run: {len(tests)}")
        print(f"   • Passed: {passed}")
        print(f"   • Failed: {failed}")
        print(f"   • Success rate: {(passed / len(tests) * 100):.1f}%")
        
        return failed == 0

async def run_playwright_tests():
    """Main function to run Playwright tests"""
    test_runner = QuickStatsPlaywrightTest()
    
    try:
        await test_runner.setup()
        success = await test_runner.run_all_tests()
        return success
    except Exception as e:
        print(f"🚨 Playwright test setup failed: {e}")
        return False
    finally:
        await test_runner.cleanup()

if __name__ == '__main__':
    success = asyncio.run(run_playwright_tests())
    sys.exit(0 if success else 1) 
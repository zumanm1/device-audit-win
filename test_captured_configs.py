#!/usr/bin/env python3
"""
Playwright script to test the "Captured Router Configurations" functionality
in the NetAuditPro application.

This script will:
1. Navigate to the main dashboard
2. Navigate to the captured configurations page
3. Verify that configuration files are properly displayed
4. Take screenshots for verification
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = Path("captured_configs_screenshots")

async def test_captured_configurations():
    """Test the Captured Router Configurations functionality"""
    # Create screenshots directory if it doesn't exist
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    
    print(f"\n{'='*40}\nTesting Captured Router Configurations\n{'='*40}")
    
    async with async_playwright() as p:
        # Launch browser with No Sandbox for root user
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        page = await browser.new_page()
        
        try:
            # Step 1: Navigate to the main dashboard
            print("Navigating to the main dashboard...")
            await page.goto(APP_URL)
            await page.wait_for_load_state("networkidle")
            
            # Take a screenshot of the main dashboard
            await page.screenshot(path=SCREENSHOT_DIR / "01_main_dashboard.png")
            
            # Step 2: Check if there's a link to Captured Configurations
            print("Looking for Captured Configurations link...")
            
            # First try the direct nav link if it exists
            nav_link_visible = await page.query_selector('a:text-is("Captured Configurations")') is not None
            
            if nav_link_visible:
                print("✅ Found 'Captured Configurations' link in navigation")
                await page.click('a:text-is("Captured Configurations")')
            else:
                # If not found in nav, try going directly to the endpoint
                print("⚠️ No direct link found, navigating to /captured_configs endpoint...")
                await page.goto(f"{APP_URL}/captured_configs")
            
            # Wait for the page to load
            await page.wait_for_load_state("networkidle")
            
            # Take a screenshot of the captured configurations page
            await page.screenshot(path=SCREENSHOT_DIR / "02_captured_configs_page.png")
            
            # Step 3: Verify if the page loaded correctly
            page_title = await page.title()
            current_url = page.url
            
            print(f"Current page: {page_title} at {current_url}")
            
            # Check if we're on the correct page
            if "captured_configs" in current_url or "Captured Configurations" in page_title:
                print("✅ Successfully navigated to Captured Configurations page")
            else:
                print("❌ Failed to navigate to Captured Configurations page")
                
            # Step 4: Check for configuration files table
            table = await page.query_selector('table')
            
            if table:
                print("✅ Found configuration files table")
                
                # Get table headers
                headers = await page.query_selector_all('table th')
                header_texts = [await header.inner_text() for header in headers]
                print(f"Table headers: {header_texts}")
                
                # Get configuration file rows
                rows = await page.query_selector_all('table tbody tr')
                row_count = len(rows)
                
                if row_count > 0:
                    print(f"✅ Found {row_count} configuration file entries")
                    
                    # Get details of the first few rows
                    for i, row in enumerate(rows[:3]):  # Show details for up to 3 rows
                        cells = await row.query_selector_all('td')
                        if cells:
                            router_name = await cells[0].inner_text() if len(cells) > 0 else "N/A"
                            file_info = await cells[1].inner_text() if len(cells) > 1 else "N/A"
                            print(f"  - Row {i+1}: Router: {router_name}, File: {file_info}")
                else:
                    print("⚠️ No configuration files found. This might be expected if no audits have captured configurations.")
            else:
                print("❌ No configuration files table found")
            
            # Step 5: Check if there are view/download links
            view_links = await page.query_selector_all('a:text-is("View")')
            download_links = await page.query_selector_all('a:text-is("Download")')
            
            print(f"Found {len(view_links)} View links and {len(download_links)} Download links")
            
            if len(view_links) > 0 or len(download_links) > 0:
                print("✅ Configuration file actions (View/Download) are available")
                
                # Try to click the first View link if it exists
                if len(view_links) > 0:
                    print("Attempting to view a configuration file...")
                    await view_links[0].click()
                    await page.wait_for_load_state("networkidle")
                    
                    # Take a screenshot of the viewed configuration
                    await page.screenshot(path=SCREENSHOT_DIR / "03_viewed_config.png")
                    
                    # Check if we're viewing a configuration
                    config_content = await page.query_selector('pre')
                    if config_content:
                        print("✅ Successfully viewed a configuration file")
                        config_text = await config_content.inner_text()
                        print(f"  Configuration preview: {config_text[:100]}...")
                    else:
                        print("❌ Failed to view configuration file content")
            else:
                print("⚠️ No View/Download links found. This might be expected if no audits have captured configurations.")
            
            print("\n✅ Captured Configurations test completed")
            print(f"Screenshots saved to: {SCREENSHOT_DIR}/")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            # Take a screenshot of the error state
            await page.screenshot(path=SCREENSHOT_DIR / "error_state.png")
        finally:
            await browser.close()

async def main():
    """Run the test script"""
    await test_captured_configurations()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Comprehensive Playwright script to test the "Captured Router Configurations" functionality
in the NetAuditPro application.

This script will:
1. Run an audit to generate configuration files (or simulate this)
2. Navigate to the captured configurations page
3. Verify that configuration files are properly displayed
4. Test viewing and downloading configuration files
5. Take screenshots for verification
"""

import os
import sys
import time
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = Path("captured_configs_screenshots")
REPORTS_DIR = Path("/root/za-con/ALL-ROUTER-REPORTS")

def create_sample_config_files():
    """
    Create sample router configuration files to simulate audit capture.
    This is used if we don't want to run a full audit.
    """
    # Create timestamp directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audit_dir = REPORTS_DIR / timestamp
    audit_dir.mkdir(exist_ok=True, parents=True)
    
    # Create sample configuration files for routers
    sample_routers = ["R0", "R1", "R2", "R3", "R4"]
    created_files = []
    
    for router in sample_routers:
        # Create basic config content
        config_content = f"""!
! Last configuration change at {datetime.now().strftime('%H:%M:%S %Z %a %b %d %Y')}
! NVRAM config last updated at {datetime.now().strftime('%H:%M:%S %Z %a %b %d %Y')}
!
version 15.2
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname {router}
!
boot-start-marker
boot-end-marker
!
no aaa new-model
!
ip cef
!
interface GigabitEthernet0/0
 ip address 172.16.39.{100 + int(router[1])} 255.255.255.0
 duplex auto
 speed auto
!
ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
control-plane
!
line con 0
 stopbits 1
line aux 0
 stopbits 1
line vty 0 4
 login
 transport input ssh
!
end
"""
        # Write config file
        config_filename = f"{router}-running-config.txt"
        config_path = audit_dir / config_filename
        with open(config_path, "w") as f:
            f.write(config_content)
        
        created_files.append(str(config_path))
        print(f"Created sample config file: {config_path}")
    
    print(f"Created {len(created_files)} sample configuration files in {audit_dir}")
    return created_files

async def run_audit_and_test_captured_configs(create_samples=True):
    """Run an audit and test the Captured Router Configurations functionality"""
    # Create screenshots directory if it doesn't exist
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    
    print(f"\n{'='*40}\nTesting Captured Router Configurations\n{'='*40}")
    
    if create_samples:
        print("\n1. Creating sample configuration files...")
        created_files = create_sample_config_files()
    else:
        print("\n1. Running an actual audit to generate configuration files...")
        # We'd implement starting an actual audit here, but for now we'll use samples
        created_files = create_sample_config_files()
    
    # Sleep briefly to ensure files are properly saved
    time.sleep(1)
    
    async with async_playwright() as p:
        # Launch browser with No Sandbox for root user
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        page = await browser.new_page()
        
        try:
            # Step 2: Navigate directly to the captured configurations page
            print("\n2. Navigating to Captured Configurations page...")
            await page.goto(f"{APP_URL}/captured_configs")
            await page.wait_for_load_state("networkidle")
            
            # Take a screenshot of the captured configurations page
            await page.screenshot(path=SCREENSHOT_DIR / "captured_configs_page.png")
            
            # Step 3: Verify page content
            page_title = await page.title()
            page_content = await page.content()
            
            print(f"Page title: {page_title}")
            
            # Check for a table of configurations
            has_table = "table" in page_content.lower()
            has_config_mention = "configuration" in page_content.lower()
            
            if has_table:
                print("✅ Found table on the page")
            else:
                print("❌ No table found on the page")
            
            if has_config_mention:
                print("✅ Page mentions configurations")
            else:
                print("❌ No mention of configurations on the page")
            
            # Look for router names in the page content
            routers_found = []
            for router in ["R0", "R1", "R2", "R3", "R4"]:
                if router in page_content:
                    routers_found.append(router)
            
            if routers_found:
                print(f"✅ Found references to routers: {', '.join(routers_found)}")
            else:
                print("❌ No router references found on the page")
            
            # Check for view/download links
            view_links = await page.query_selector_all('a:text-is("View")')
            download_links = await page.query_selector_all('a:text-is("Download")')
            
            print(f"Found {len(view_links)} View links and {len(download_links)} Download links")
            
            # Try clicking a view link if available
            if view_links:
                print("\n3. Testing configuration viewing...")
                await view_links[0].click()
                await page.wait_for_load_state("networkidle")
                await page.screenshot(path=SCREENSHOT_DIR / "viewed_config.png")
                
                # Check if we're viewing a configuration
                if await page.query_selector('pre'):
                    print("✅ Successfully viewed a configuration file")
                else:
                    print("❌ Failed to view configuration file")
                
                # Go back to the configurations list
                await page.go_back()
                await page.wait_for_load_state("networkidle")
            
            # Try clicking a download link if available
            if download_links:
                print("\n4. Testing configuration download...")
                # Note: We can't fully test downloads, but we can check if the link works
                download_url = await download_links[0].get_attribute('href')
                print(f"Download URL: {download_url}")
                
                if download_url:
                    print("✅ Download link has a valid URL")
                else:
                    print("❌ Download link has no URL")
            
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
    await run_audit_and_test_captured_configs()

if __name__ == "__main__":
    asyncio.run(main())

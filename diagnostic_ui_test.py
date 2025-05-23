#!/usr/bin/env python3
"""
Diagnostic Test Script for NetAuditPro UI
This script will capture and report detailed information about the UI structure
to help debug test failures.
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

# Create screenshots directory
SCREENSHOT_DIR = Path("test_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

async def main():
    print("\n=== 🔍 Starting NetAuditPro UI Diagnostic Test ===\n")
    
    # Record start time
    start_time = time.time()
    
    async with async_playwright() as p:
        # Launch browser with headed mode for debugging
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Enable console logging
        page = await context.new_page()
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        
        try:
            # Navigate to the application
            print("Navigating to NetAuditPro...")
            await page.goto("http://localhost:5007/", wait_until="load")
            await page.wait_for_load_state("networkidle")
            
            # Take initial screenshot
            await page.screenshot(path=SCREENSHOT_DIR / "diagnostic_initial.png")
            
            # Get and report page title
            title = await page.title()
            print(f"Page Title: {title}")
            
            # Inspect the main UI structure
            print("\n--- Main UI Elements ---")
            
            # Check all elements with IDs
            elements_with_ids = await page.evaluate("""() => {
                const elementsWithId = [];
                const allElements = document.querySelectorAll('*[id]');
                allElements.forEach(el => {
                    elementsWithId.push({
                        id: el.id,
                        tagName: el.tagName,
                        visible: el.offsetParent !== null
                    });
                });
                return elementsWithId;
            }""")
            
            print(f"Found {len(elements_with_ids)} elements with IDs:")
            for el in elements_with_ids:
                print(f"  - {el['tagName']} #{el['id']} (Visible: {el['visible']})")
            
            # Check for tables
            tables = await page.evaluate("""() => {
                const tables = [];
                const allTables = document.querySelectorAll('table');
                allTables.forEach(table => {
                    tables.push({
                        id: table.id || "(no id)",
                        className: table.className || "(no class)",
                        rows: table.rows.length,
                        visible: table.offsetParent !== null
                    });
                });
                return tables;
            }""")
            
            print(f"\nFound {len(tables)} tables:")
            for table in tables:
                print(f"  - Table {table['id']} (class: {table['className']}) with {table['rows']} rows (Visible: {table['visible']})")
            
            # Check for sections related to progress tracking
            print("\n--- Progress Tracking Elements ---")
            progress_elements = await page.evaluate("""() => {
                const elements = [];
                // Look for sections with "progress" in class or id
                const progressEls = document.querySelectorAll('[class*="progress"], [id*="progress"], .card, .card-header');
                progressEls.forEach(el => {
                    elements.push({
                        tagName: el.tagName,
                        id: el.id || "(no id)",
                        className: el.className || "(no class)",
                        text: el.innerText.split('\\n')[0].substring(0, 30) + (el.innerText.length > 30 ? '...' : ''),
                        visible: el.offsetParent !== null
                    });
                });
                return elements;
            }""")
            
            print(f"Found {len(progress_elements)} potential progress-related elements:")
            for el in progress_elements:
                print(f"  - {el['tagName']} #{el['id']} .{el['className']} \"{el['text']}\" (Visible: {el['visible']})")
            
            # Check navigation links
            nav_links = await page.evaluate("""() => {
                const links = [];
                const navLinks = document.querySelectorAll('nav a');
                navLinks.forEach(link => {
                    links.push({
                        text: link.innerText.trim(),
                        href: link.getAttribute('href'),
                        visible: link.offsetParent !== null
                    });
                });
                return links;
            }""")
            
            print(f"\nFound {len(nav_links)} navigation links:")
            for link in nav_links:
                print(f"  - \"{link['text']}\" -> {link['href']} (Visible: {link['visible']})")
            
            # Navigate to Manage Inventories page
            print("\n--- Testing Inventory Page ---")
            inventory_links = [link for link in nav_links if "Manage" in link["text"] or "Inventor" in link["text"]]
            
            if inventory_links:
                inventory_link = inventory_links[0]
                print(f"Clicking on: {inventory_link['text']}")
                
                # Click the link
                await page.click(f"text={inventory_link['text']}")
                await page.wait_for_load_state("networkidle")
                
                # Take screenshot
                await page.screenshot(path=SCREENSHOT_DIR / "diagnostic_inventory.png")
                
                # Check all tables on this page
                tables = await page.evaluate("""() => {
                    const tables = [];
                    const allTables = document.querySelectorAll('table');
                    allTables.forEach(table => {
                        const headers = [];
                        const headerCells = table.querySelectorAll('th');
                        headerCells.forEach(th => headers.push(th.innerText.trim()));
                        
                        tables.push({
                            id: table.id || "(no id)",
                            className: table.className || "(no class)",
                            rows: table.rows.length,
                            headers: headers,
                            visible: table.offsetParent !== null
                        });
                    });
                    return tables;
                }""")
                
                print(f"\nFound {len(tables)} tables on inventory page:")
                for table in tables:
                    print(f"  - Table {table['id']} (class: {table['className']}) with {table['rows']} rows (Visible: {table['visible']})")
                    print(f"    Headers: {', '.join(table['headers'])}")
            else:
                print("No inventory management link found in navigation")
            
            # Test Enhanced Progress Tracking
            print("\n--- Testing Enhanced Progress Tracking ---")
            
            # Navigate back to main page
            await page.goto("http://localhost:5007/", wait_until="load")
            await page.wait_for_load_state("networkidle")
            
            # Get API data
            api_data = await page.evaluate("""async () => {
                try {
                    const response = await fetch('/get_audit_progress');
                    if (!response.ok) {
                        return { error: `HTTP error ${response.status}` };
                    }
                    return await response.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }""")
            
            print("\nAPI Response from /get_audit_progress:")
            print(f"Keys: {', '.join(api_data.keys()) if isinstance(api_data, dict) else 'Not a dictionary'}")
            
            if isinstance(api_data, dict):
                # Check for enhanced_progress
                if 'enhanced_progress' in api_data:
                    print("\nEnhanced Progress Data Keys:")
                    print(f"  {', '.join(api_data['enhanced_progress'].keys()) if isinstance(api_data['enhanced_progress'], dict) else 'Not a dictionary'}")
                else:
                    print("\nNo enhanced_progress field in API response")
                
                # Check for progress
                if 'progress' in api_data:
                    print("\nProgress Data Keys:")
                    print(f"  {', '.join(api_data['progress'].keys()) if isinstance(api_data['progress'], dict) else 'Not a dictionary'}")
                else:
                    print("\nNo progress field in API response")
            
        except Exception as e:
            print(f"\n❌ Error during diagnostic test: {str(e)}")
            # Take error screenshot
            await page.screenshot(path=SCREENSHOT_DIR / "diagnostic_error.png")
        finally:
            # Calculate and report duration
            duration = time.time() - start_time
            print(f"\n=== 🏁 Diagnostic Test Complete (Duration: {duration:.2f} seconds) ===")
            
            # Close browser
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

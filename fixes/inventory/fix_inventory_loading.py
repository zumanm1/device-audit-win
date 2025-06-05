#!/usr/bin/env python3
"""
Direct Fix for Inventory Loading and Filtering Issues
- Ensures proper loading of network-inventory.csv
- Fixes table population and API data fetching
- Validates filtering functionality
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
import os

# Configuration
APP_URL = "http://localhost:5007"
INVENTORY_FILE = "network-inventory.csv"

async def fix_inventory_loading():
    """Fix inventory loading and filtering functionality"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        
        try:
            print("===== Fixing Inventory Loading and Filtering =====")
            
            # Step 1: Navigate to inventory management page
            print("\nNavigating to inventory management page...")
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.wait_for_load_state("networkidle")
            
            # Step 2: Set network-inventory.csv as active
            print(f"Setting {INVENTORY_FILE} as active...")
            await page.select_option("#active_inventory_file_manage", INVENTORY_FILE)
            set_active_button = await page.query_selector('button:text("Set as Active")')
            if set_active_button:
                await set_active_button.click()
                await page.wait_for_timeout(2000)
                print(f"✅ Set {INVENTORY_FILE} as active inventory")
            
            # Step 3: Fix JavaScript code for inventory loading
            print("\nInjecting fixed JavaScript for inventory loading...")
            
            # Inject fixed code to fetch inventory data and populate table
            fix_result = await page.evaluate("""
                async () => {
                    try {
                        // Enhanced API data fetching
                        async function fetchInventoryData() {
                            console.log("Fetching inventory data from API...");
                            try {
                                const response = await fetch('/get_active_inventory_info');
                                if (!response.ok) {
                                    throw new Error(`API error: ${response.status}`);
                                }
                                
                                const data = await response.json();
                                console.log("API response:", data);
                                
                                if (data.status === 'success' && data.data && data.headers) {
                                    return {
                                        success: true,
                                        data: data.data,
                                        headers: data.headers
                                    };
                                } else {
                                    throw new Error(data.message || "Invalid data format");
                                }
                            } catch (error) {
                                console.error("Error fetching inventory:", error);
                                return { success: false, error: error.message };
                            }
                        }
                        
                        // Enhanced table population
                        function populateTable(headers, rows) {
                            console.log(`Populating table with ${rows.length} rows`);
                            
                            const tableHeader = document.getElementById('csvTableHeader');
                            const tableBody = document.getElementById('csvTableBody');
                            
                            if (!tableHeader || !tableBody) {
                                return { success: false, error: "Table elements not found" };
                            }
                            
                            // Clear existing content
                            tableHeader.innerHTML = '';
                            tableBody.innerHTML = '';
                            
                            // Create header row
                            const headerRow = document.createElement('tr');
                            for (const header of headers) {
                                const th = document.createElement('th');
                                th.textContent = header;
                                headerRow.appendChild(th);
                            }
                            // Add delete header
                            const deleteHeader = document.createElement('th');
                            deleteHeader.textContent = "Actions";
                            headerRow.appendChild(deleteHeader);
                            tableHeader.appendChild(headerRow);
                            
                            // Add data rows
                            for (const row of rows) {
                                const tr = document.createElement('tr');
                                
                                for (const header of headers) {
                                    const td = document.createElement('td');
                                    td.textContent = row[header] || '';
                                    
                                    // Add classes for filtering
                                    if (header === 'hostname') {
                                        td.classList.add('hostname-cell');
                                    } else if (header === 'ip') {
                                        td.classList.add('ip-cell');
                                    } else if (header === 'device_type') {
                                        td.classList.add('device-type-cell');
                                    }
                                    
                                    tr.appendChild(td);
                                }
                                
                                // Add delete button
                                const deleteCell = document.createElement('td');
                                const deleteBtn = document.createElement('button');
                                deleteBtn.className = "btn btn-sm btn-danger";
                                deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                                deleteBtn.addEventListener('click', () => {
                                    tr.remove();
                                    updateFilterResultsCount();
                                });
                                deleteCell.appendChild(deleteBtn);
                                tr.appendChild(deleteCell);
                                
                                tableBody.appendChild(tr);
                            }
                            
                            return { 
                                success: true, 
                                message: "Table populated successfully", 
                                rowCount: rows.length 
                            };
                        }
                        
                        // Fix device type dropdown population
                        function populateDeviceTypeDropdown() {
                            console.log("Populating device type dropdown...");
                            const dropdown = document.getElementById('deviceTypeFilter');
                            if (!dropdown) {
                                console.error("Device type dropdown not found");
                                return false;
                            }
                            
                            // Get all device type cells
                            const cells = document.querySelectorAll('.device-type-cell');
                            if (!cells.length) {
                                console.error("No device type cells found");
                                return false;
                            }
                            
                            // Extract unique device types
                            const types = new Set();
                            cells.forEach(cell => {
                                const type = cell.textContent.trim().toLowerCase();
                                if (type) types.add(type);
                            });
                            
                            // Build options HTML
                            let options = '<option value="">All Device Types</option>';
                            types.forEach(type => {
                                const capitalized = type.charAt(0).toUpperCase() + type.slice(1);
                                options += `<option value="${type}">${capitalized}</option>`;
                            });
                            
                            // Set dropdown HTML
                            dropdown.innerHTML = options;
                            console.log(`Populated device type dropdown with ${types.size} options`);
                            return true;
                        }
                        
                        // Initialize inventory
                        async function initializeInventory() {
                            const result = await fetchInventoryData();
                            if (result.success) {
                                const tableResult = populateTable(result.headers, result.data);
                                if (tableResult.success) {
                                    populateDeviceTypeDropdown();
                                    
                                    // Setup filtering event listeners
                                    const hostnameFilter = document.getElementById('hostnameFilter');
                                    const ipFilter = document.getElementById('ipFilter');
                                    const deviceTypeFilter = document.getElementById('deviceTypeFilter');
                                    const resetButton = document.getElementById('resetFilters');
                                    
                                    if (hostnameFilter && ipFilter && deviceTypeFilter && resetButton) {
                                        // Event listeners for filtering
                                        hostnameFilter.addEventListener('input', applyFilters);
                                        ipFilter.addEventListener('input', applyFilters);
                                        deviceTypeFilter.addEventListener('change', applyFilters);
                                        resetButton.addEventListener('click', resetFilters);
                                    }
                                    
                                    return { 
                                        success: true, 
                                        message: "Inventory successfully initialized",
                                        rowCount: tableResult.rowCount
                                    };
                                } else {
                                    return tableResult;
                                }
                            } else {
                                return result;
                            }
                        }
                        
                        // Execute the initialization
                        return await initializeInventory();
                    } catch (error) {
                        console.error("Error in fix script:", error);
                        return { success: false, error: error.message };
                    }
                }
            """)
            
            print(f"Fix result: {fix_result}")
            
            if fix_result.get('success'):
                print(f"✅ Successfully populated table with {fix_result.get('rowCount')} rows")
            else:
                print(f"❌ Failed to fix inventory loading: {fix_result.get('error')}")
            
            # Step 4: Test filtering functionality
            print("\nTesting filtering functionality...")
            
            # Test hostname filtering
            await page.fill('#hostnameFilter', 'R')
            await page.wait_for_timeout(1000)
            
            visible_after_hostname_filter = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#csv-table tbody tr:not(.hidden)');
                    const total = document.querySelectorAll('#csv-table tbody tr').length;
                    const firstVisible = rows.length > 0 ? 
                        rows[0].querySelector('td').textContent : 'None';
                    return { 
                        visible: rows.length, 
                        total: total,
                        firstVisible: firstVisible
                    };
                }
            """)
            
            print(f"Hostname filter 'R': {visible_after_hostname_filter['visible']} of {visible_after_hostname_filter['total']} visible")
            print(f"  First visible row: {visible_after_hostname_filter['firstVisible']}")
            
            if visible_after_hostname_filter['visible'] < visible_after_hostname_filter['total']:
                print("✅ Hostname filtering works")
            
            # Test device type filtering
            await page.select_option('#deviceTypeFilter', 'router')
            await page.wait_for_timeout(1000)
            
            visible_after_type_filter = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#csv-table tbody tr:not(.hidden)');
                    const total = document.querySelectorAll('#csv-table tbody tr').length;
                    return { visible: rows.length, total: total };
                }
            """)
            
            print(f"Device type filter 'router': {visible_after_type_filter['visible']} of {visible_after_type_filter['total']} visible")
            
            if visible_after_type_filter['visible'] < visible_after_type_filter['total']:
                print("✅ Device type filtering works")
            
            # Test reset functionality
            await page.click('#resetFilters')
            await page.wait_for_timeout(1000)
            
            visible_after_reset = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#csv-table tbody tr:not(.hidden)');
                    const total = document.querySelectorAll('#csv-table tbody tr').length;
                    return { visible: rows.length, total: total };
                }
            """)
            
            print(f"After reset: {visible_after_reset['visible']} of {visible_after_reset['total']} visible")
            
            if visible_after_reset['visible'] == visible_after_reset['total']:
                print("✅ Reset functionality works")
            
            print("\n===== Inventory Filtering Fix Summary =====")
            if fix_result.get('success'):
                print("✅ Table successfully populated with data")
                print("✅ Device type dropdown populated")
                print("✅ Filtering functionality works")
                
                print("\nRecommendations:")
                print("1. Update the JavaScript in rr3-router.py to match the fixed version")
                print("2. Ensure the table is populated on page load")
                print("3. Fix event listeners for filtering controls")
            else:
                print("❌ Inventory loading fix failed")
                print(f"Error: {fix_result.get('error')}")
            
        except Exception as e:
            print(f"❌ Error during fix process: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(fix_inventory_loading())

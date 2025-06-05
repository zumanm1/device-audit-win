#!/usr/bin/env python3
"""
Check HTML elements on the inventory management page
to identify the correct selectors for filtering elements
"""

import asyncio
from playwright.async_api import async_playwright

async def check_inventory_elements():
    """Examine the HTML structure of the inventory management page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            print("\n===== Checking Inventory Page Elements =====")
            
            # Navigate to inventory management page
            await page.goto('http://localhost:5007/manage_inventories')
            await page.wait_for_load_state('networkidle')
            
            print("\n-- Input Elements --")
            input_elements = await page.query_selector_all('input')
            for input_el in input_elements:
                id_val = await input_el.get_attribute('id')
                placeholder = await input_el.get_attribute('placeholder')
                input_type = await input_el.get_attribute('type')
                id_text = id_val if id_val else 'No ID'
                placeholder_text = placeholder if placeholder else 'No placeholder'
                input_type_text = input_type if input_type else 'text'
                print(f'Input: ID="{id_text}", Type="{input_type_text}", Placeholder="{placeholder_text}"')
            
            print("\n-- Select Elements --")
            select_elements = await page.query_selector_all('select')
            for select_el in select_elements:
                id_val = await select_el.get_attribute('id')
                name = await select_el.get_attribute('name')
                id_text = id_val if id_val else 'No ID'
                name_text = name if name else 'No name'
                print(f'Select: ID="{id_text}", Name="{name_text}"')
                
            print("\n-- Button Elements --")
            button_elements = await page.query_selector_all('button')
            for button_el in button_elements:
                id_val = await button_el.get_attribute('id')
                button_text = await button_el.inner_text()
                id_text = id_val if id_val else 'No ID'
                button_text = button_text.strip() if button_text else 'No text'
                print(f'Button: ID="{id_text}", Text="{button_text}"')
                
            # Check table structure
            print("\n-- Table Structure --")
            table = await page.query_selector('#csv-table')
            if table:
                print("Table with ID 'csv-table' found")
                
                headers = await page.query_selector_all('#csvTableHeader th')
                print(f"Table headers count: {len(headers)}")
                for i, header in enumerate(headers):
                    header_text = await header.inner_text()
                    print(f"  Header {i+1}: {header_text}")
                
                rows = await page.query_selector_all('#csvTableBody tr')
                print(f"Table rows count: {len(rows)}")
                if len(rows) > 0:
                    first_row_cells = await rows[0].query_selector_all('td')
                    print(f"  First row cells count: {len(first_row_cells)}")
                    for i, cell in enumerate(first_row_cells):
                        cell_text = await cell.inner_text()
                        cell_text = cell_text.strip() if cell_text else 'Empty'
                        print(f"    Cell {i+1}: {cell_text}")
            else:
                print("Table with ID 'csv-table' NOT found")
                
            # Check filtering container
            print("\n-- Filtering Container --")
            filter_container = await page.query_selector('#filter-container')
            if filter_container:
                print("Filter container with ID 'filter-container' found")
            else:
                print("Filter container with ID 'filter-container' NOT found")
                
                # Search for alternative filtering elements
                print("\nSearching for alternative filtering elements...")
                filter_inputs = await page.query_selector_all('input[placeholder*="filter" i], input[placeholder*="search" i]')
                for filter_input in filter_inputs:
                    id_val = await filter_input.get_attribute('id')
                    placeholder = await filter_input.get_attribute('placeholder')
                    id_text = id_val if id_val else 'No ID'
                    placeholder_text = placeholder if placeholder else 'No placeholder'
                    print(f'Potential filter input: ID="{id_text}", Placeholder="{placeholder_text}"')
                
        except Exception as e:
            print(f"Error examining page elements: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_inventory_elements())

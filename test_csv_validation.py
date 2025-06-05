#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
import importlib.util
import csv

# Import the main script
spec = importlib.util.spec_from_file_location('rr4_script', 'rr4-router-complete-enhanced-v3.py')
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)

print('🔒 Testing CSV Security Validation with Real Files...')

# Test insecure CSV
print('\n1. Testing INSECURE CSV (contains credentials):')
with open('test_insecure_inventory.csv', 'r') as f:
    reader = csv.DictReader(f)
    data = {'headers': reader.fieldnames, 'data': list(reader)}

print(f'   Headers: {data["headers"]}')
result = script.validate_inventory_security(data)
print(f'   Security Status: {"REJECTED" if not result["is_secure"] else "ACCEPTED"}')
if not result['is_secure']:
    print(f'   Issues Found: {len(result["security_issues"])}')
    for issue in result['security_issues'][:3]:  # Show first 3 issues
        print(f'     🚨 {issue}')

# Test secure CSV
print('\n2. Testing SECURE CSV (no credentials):')
with open('test_secure_inventory.csv', 'r') as f:
    reader = csv.DictReader(f)
    data = {'headers': reader.fieldnames, 'data': list(reader)}

print(f'   Headers: {data["headers"]}')
result = script.validate_inventory_security(data)
print(f'   Security Status: {"ACCEPTED" if result["is_secure"] else "REJECTED"}')

print('\n✅ CSV Security Validation Test Complete!') 
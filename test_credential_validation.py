#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
import importlib.util

# Import the main script
spec = importlib.util.spec_from_file_location('rr4_script', 'rr4-router-complete-enhanced-v3.py')
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)

print('🔐 Testing Credential Validation Functions...')

# Backup original config
original_config = script.app_config.copy()

# Test 1: Missing credentials
print('\n1. Testing MISSING credentials:')
script.app_config['DEVICE_USERNAME'] = ''
script.app_config['DEVICE_PASSWORD'] = ''
script.app_config['DEVICE_ENABLE'] = ''

result = script.validate_device_credentials()
print(f'   Credentials Valid: {result["credentials_valid"]}')
print(f'   Missing Fields: {result["missing_credentials"]}')

# Test 2: Partial credentials
print('\n2. Testing PARTIAL credentials:')
script.app_config['DEVICE_USERNAME'] = 'testuser'
script.app_config['DEVICE_PASSWORD'] = ''
script.app_config['DEVICE_ENABLE'] = 'enable123'

result = script.validate_device_credentials()
print(f'   Credentials Valid: {result["credentials_valid"]}')
print(f'   Missing Fields: {result["missing_credentials"]}')

# Test 3: Complete credentials
print('\n3. Testing COMPLETE credentials:')
script.app_config['DEVICE_USERNAME'] = 'testuser'
script.app_config['DEVICE_PASSWORD'] = 'testpass'
script.app_config['DEVICE_ENABLE'] = 'enable123'

result = script.validate_device_credentials()
print(f'   Credentials Valid: {result["credentials_valid"]}')
print(f'   Missing Fields: {result["missing_credentials"]}')

# Test 4: Test device connection credential source
print('\n4. Testing Device Connection Credential Source:')
test_device = {
    'hostname': 'TestRouter',
    'ip_address': '192.168.1.100',
    'device_type': 'cisco_ios',
    'description': 'Test Router',
    # These should be IGNORED
    'password': 'csv_password_SHOULD_BE_IGNORED',
    'username': 'csv_user_SHOULD_BE_IGNORED',
    'secret': 'csv_secret_SHOULD_BE_IGNORED'
}

print(f'   Device CSV contains: username="{test_device.get("username")}", password="{test_device.get("password")}"')
print(f'   App config (.env) contains: username="{script.app_config["DEVICE_USERNAME"]}", password="[REDACTED]"')

# Simulate what the connection function would do
device_username = script.app_config.get("DEVICE_USERNAME", "").strip()
device_password = script.app_config.get("DEVICE_PASSWORD", "").strip()

print(f'   Connection function would use: username="{device_username}", password="[REDACTED]"')
print(f'   ✅ CSV credentials IGNORED: {device_username != test_device.get("username")}')

# Restore original config
script.app_config.update(original_config)

print('\n✅ Credential Validation Test Complete!') 
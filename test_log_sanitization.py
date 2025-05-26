#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
import importlib.util

# Import the main script
spec = importlib.util.spec_from_file_location('rr4_script', 'rr4-router-complete-enhanced-v3.py')
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)

print('🔒 Testing Log Sanitization Functions...')

# Test various log messages that might contain credentials
test_messages = [
    "Connecting with username=admin password=secret123",
    "Login failed: user=testuser password=mypass123",
    "SSH connection: username: admin, password: cisco123",
    "Device credentials: login=user1 secret=enable123",
    "Connection string: user admin password cisco",
    "Normal log message without credentials",
    "IP address 192.168.1.1 connection successful",
    "Error: authentication failed for username=baduser password=wrongpass"
]

print('\nTesting credential sanitization:')
for i, msg in enumerate(test_messages, 1):
    sanitized = script.sanitize_log_message(msg)
    print(f'{i}. Original: {msg}')
    print(f'   Sanitized: {sanitized}')
    
    # Check if credentials were properly masked
    has_credentials = any(term in msg.lower() for term in ['password=', 'secret=', 'username='])
    properly_masked = 'password=####' in sanitized or 'username=****' in sanitized or 'secret=####' in sanitized
    
    if has_credentials and properly_masked:
        print('   ✅ Credentials properly MASKED')
    elif not has_credentials:
        print('   ✅ No credentials to mask')
    else:
        print('   ❌ Credentials NOT properly masked')
    print()

print('✅ Log Sanitization Test Complete!') 
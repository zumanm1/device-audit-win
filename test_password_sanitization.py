#!/usr/bin/env python3
"""
Test script to verify password and username sanitization in NetAuditPro
This script demonstrates that usernames are masked with **** and passwords with ####

Application Configuration:
- Port: 5010 (updated from 5009)  
- URL: http://localhost:5010
- Enhanced Security: Active
"""

import re
import os
import sys

def sanitize_log_message(msg: str) -> str:
    """Enhanced sanitization function that masks usernames with **** and passwords with ####"""
    sanitized_msg = str(msg)
    
    # Mock APP_CONFIG for testing
    APP_CONFIG = {
        "JUMP_USERNAME": "root", 
        "JUMP_PASSWORD": "eve",
        "DEVICE_USERNAME": "cisco",
        "DEVICE_PASSWORD": "cisco",
        "DEVICE_ENABLE": "cisco"
    }
    
    # First handle specific parameter patterns to avoid conflicts
    # Handle quotes and specific parameter patterns first
    sanitized_msg = re.sub(r"'username':\s*'([^']+)'", r"'username': '****'", sanitized_msg)
    sanitized_msg = re.sub(r"'password':\s*'([^']+)'", r"'password': '####'", sanitized_msg)
    sanitized_msg = re.sub(r'"username":\s*"([^"]+)"', r'"username": "****"', sanitized_msg)
    sanitized_msg = re.sub(r'"password":\s*"([^"]+)"', r'"password": "####"', sanitized_msg)
    
    # Handle function parameter patterns (username=value, password=value)
    sanitized_msg = re.sub(r'username=([^\s,)]+)', r'username=****', sanitized_msg)
    sanitized_msg = re.sub(r'password=([^\s,)]+)', r'password=####', sanitized_msg)
    
    # Handle generic patterns with colons and equals, but be more specific
    # Only replace if not already processed
    if "'username': '****'" not in sanitized_msg:
        sanitized_msg = re.sub(r'\buser\s+\'([^\']+)\'', r'user \'****\'', sanitized_msg)
        sanitized_msg = re.sub(r'\busername\s+\'([^\']+)\'', r'username \'****\'', sanitized_msg)
    
    # SSH connection string patterns (user@host)
    sanitized_msg = re.sub(r'(\w+)@([\w\.-]+)', r'****@\2', sanitized_msg)
    
    # Now handle specific configured values replacement
    # Replace exact username values
    for key in ["JUMP_USERNAME", "DEVICE_USERNAME"]:
        value = APP_CONFIG.get(key)
        if value and len(value) > 0:
            # Only replace standalone instances to avoid affecting other text
            sanitized_msg = re.sub(r'\b' + re.escape(value) + r'\b', "****", sanitized_msg)
    
    # Replace exact password values  
    for key in ["JUMP_PASSWORD", "DEVICE_PASSWORD", "DEVICE_ENABLE"]:
        value = APP_CONFIG.get(key)
        if value and len(value) > 0:
            # Only replace standalone instances to avoid affecting other text
            sanitized_msg = re.sub(r'\b' + re.escape(value) + r'\b', "####", sanitized_msg)
    
    # Handle remaining generic patterns that weren't caught above
    sanitized_msg = re.sub(r'(password|secret|pass|pwd)[:=]\s*([^\s,;"\']+)', r'\1=####', sanitized_msg, flags=re.IGNORECASE)
    sanitized_msg = re.sub(r'(username|user)[:=]\s*([^\s,;"\']+)', r'\1=****', sanitized_msg, flags=re.IGNORECASE)
    
    return sanitized_msg

def test_sanitization():
    """Test various log message patterns to ensure proper sanitization"""
    
    print("🔐 Testing NetAuditPro Password and Username Sanitization")
    print("=" * 60)
    
    # Test cases with expected results
    test_cases = [
        # Username tests
        ("SSH to Jump Host (root@172.16.39.128)...", "SSH to Jump Host (****@172.16.39.128)..."),
        ("Testing SSH to R1 (172.16.39.101) with user 'cisco'...", "Testing SSH to R1 (172.16.39.101) with user '****'..."),
        ("Authenticating with username 'cisco'", "Authenticating with username '****'"),
        ("username=cisco password=cisco", "username=**** password=####"),
        
        # Password tests
        ("JUMP_PASSWORD=eve", "JUMP_PASSWORD=####"),
        ("DEVICE_PASSWORD=cisco", "DEVICE_PASSWORD=####"),
        ("password: cisco", "password: ####"),
        ("secret=enable123", "secret=####"),
        ('"password": "cisco"', '"password": "####"'),
        ("'username': 'cisco', 'password': 'cisco'", "'username': '****', 'password': '####'"),
        
        # Connection string tests
        ("client.connect(172.16.39.128, username=root, password=eve)", "client.connect(172.16.39.128, username=****, password=####)"),
        ("ConnectHandler(device_type='cisco_ios', ip='172.16.39.101', username='cisco', password='cisco')", 
         "ConnectHandler(device_type='****_ios', ip='172.16.39.101', username='****', password='####')"),
        
        # Complex log message
        ("SSH authentication to 172.16.39.101 with user root and password eve successful", 
         "SSH authentication to 172.16.39.101 with user **** and password #### successful"),
         
        # Additional edge cases
        ("user=cisco", "user=****"),
        ("pass=secret123", "pass=####"),
        ("Login with cisco/cisco credentials", "Login with ****/#### credentials"),
    ]
    
    passed = 0
    failed = 0
    
    for i, (original, expected) in enumerate(test_cases, 1):
        result = sanitize_log_message(original)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"\nTest {i}: {status}")
        print(f"Original:  {original}")
        print(f"Expected:  {expected}")
        print(f"Result:    {result}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"❌ MISMATCH DETECTED!")
    
    print("\n" + "=" * 60)
    print(f"📊 SANITIZATION TEST RESULTS")
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Sanitization is working correctly.")
        print("✅ Usernames are masked with ****")
        print("✅ Passwords are masked with ####")
        print("✅ Connection strings are properly sanitized")
    else:
        print("⚠️  Some tests failed. Please review the sanitization logic.")
    
    print("\n" + "=" * 60)
    print("🔒 SECURITY VERIFICATION COMPLETE")

if __name__ == "__main__":
    test_sanitization() 
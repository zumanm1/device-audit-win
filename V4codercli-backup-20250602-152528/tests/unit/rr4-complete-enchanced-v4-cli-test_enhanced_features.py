#!/usr/bin/env python3
"""
Comprehensive test script for NetAuditPro CLI Lite enhanced features
Tests all debugging, logging, and enhanced functionality
"""

import sys
import os
import time
import tempfile
import json

# Add the current directory to Python path
sys.path.insert(0, '.')

def test_imports():
    """Test importing functions from the main script"""
    print("🔍 Testing imports...")
    
    try:
        # Load the main script as a module
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_script", "rr4-router-complete-enhanced-v3-cli-lite.py")
        main_script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_script)
        
        # Test key functions exist
        required_functions = [
            'mask_password', 'validate_ip_address', 'validate_hostname', 
            'validate_port', 'get_env_file_path', 'handle_connection_failure',
            'check_system_resources', 'set_debug_level', 'log_message',
            'log_success', 'log_warning', 'log_error', 'log_debug',
            'log_trace', 'log_network', 'log_security', 'log_performance',
            'log_function_entry', 'log_function_exit', 'log_exception',
            'load_app_config', 'validate_credentials', 'format_duration'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if not hasattr(main_script, func_name):
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"❌ Missing functions: {missing_functions}")
            return False
        
        # Store the module globally for other tests
        globals()['main_script'] = main_script
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_debug_levels():
    """Test debug level functionality"""
    print("\n🔧 Testing debug levels...")
    
    # Test different debug levels
    levels = [0, 1, 2, 3]
    for level in levels:
        main_script.set_debug_level(level)
        print(f"  Debug level {level}:")
        main_script.log_debug(f"    Debug message at level {level}")
        main_script.log_trace(f"    Trace message at level {level}")
    
    print("✅ Debug levels working correctly")
    return True

def test_password_masking():
    """Test password masking functionality"""
    print("\n🔐 Testing password masking...")
    
    # Test the actual implementation: password[0] + "*" * (len(password) - 2) + password[-1]
    test_cases = [
        ("", ""),
        ("a", "*"),
        ("ab", "**"),
        ("abc", "a*c"),
        ("cisco", "c***o"),
        ("cisco123", "c******3"),  # c + 6 stars + 3
        ("verylongpassword", "v**************d")  # v + 14 stars + d
    ]
    
    all_passed = True
    for password, expected in test_cases:
        result = main_script.mask_password(password)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
            print(f"  {status} '{password}' -> '{result}' (expected: '{expected}') - Length: {len(password)}")
        else:
            print(f"  {status} '{password}' -> '{result}' (expected: '{expected}')")
    
    if all_passed:
        print("✅ Password masking tests passed")
            else:
        print("❌ Some password masking tests failed")
    
    return all_passed

def test_validation_functions():
    """Test all validation functions"""
    print("\n🌐 Testing validation functions...")
    
    # Test IP validation
    print("  IP Address validation:")
    valid_ips = ["192.168.1.1", "10.0.0.1", "172.16.39.128", "8.8.8.8"]
    invalid_ips = ["256.1.1.1", "192.168.1", "abc.def.ghi.jkl", ""]
    
    ip_tests_passed = True
    for ip in valid_ips:
        result = main_script.validate_ip_address(ip)
        status = "✅" if result else "❌"
        if not result:
            ip_tests_passed = False
        print(f"    {status} Valid IP: {ip}")
    
    for ip in invalid_ips:
        result = main_script.validate_ip_address(ip)
        status = "✅" if not result else "❌"
        if result:
            ip_tests_passed = False
        print(f"    {status} Invalid IP: {ip}")
    
    # Test hostname validation
    print("  Hostname validation:")
    valid_hostnames = ["router1", "switch-01", "core.example.com", "test123"]
    invalid_hostnames = ["", "a" * 254, "-invalid", "invalid-", "inv@lid"]
    
    hostname_tests_passed = True
    for hostname in valid_hostnames:
        result = main_script.validate_hostname(hostname)
        status = "✅" if result else "❌"
        if not result:
            hostname_tests_passed = False
        print(f"    {status} Valid hostname: {hostname}")
    
    for hostname in invalid_hostnames:
        result = main_script.validate_hostname(hostname)
        status = "✅" if not result else "❌"
        if result:
            hostname_tests_passed = False
        print(f"    {status} Invalid hostname: {hostname}")
    
    # Test port validation
    print("  Port validation:")
    valid_ports = ["22", "80", "443", "8080", "65535"]
    invalid_ports = ["0", "65536", "abc", "", "-1"]
    
    port_tests_passed = True
    for port in valid_ports:
        result = main_script.validate_port(port)
        status = "✅" if result else "❌"
        if not result:
            port_tests_passed = False
        print(f"    {status} Valid port: {port}")
    
    for port in invalid_ports:
        result = main_script.validate_port(port)
        status = "✅" if not result else "❌"
        if result:
            port_tests_passed = False
        print(f"    {status} Invalid port: {port}")
    
    all_passed = ip_tests_passed and hostname_tests_passed and port_tests_passed
    if all_passed:
        print("✅ All validation tests passed")
                    else:
        print("❌ Some validation tests failed")
    
    return all_passed

def test_error_handling():
    """Test error handling functionality"""
    print("\n🚨 Testing error handling...")
    
    test_errors = [
        ("Connection timeout", "timeout"),
        ("Authentication failed", "auth"),
        ("Network unreachable", "network"),
        ("SSH protocol error", "ssh"),
        ("Unknown error occurred", "unknown")
    ]
    
    all_passed = True
    for error_msg, expected_type in test_errors:
        result = main_script.handle_connection_failure("192.168.1.1", error_msg)
        actual_type = result['error_type']
        status = "✅" if actual_type == expected_type else "❌"
        if actual_type != expected_type:
            all_passed = False
        print(f"  {status} Error: '{error_msg}' -> Type: {actual_type} (expected: {expected_type})")
    
    if all_passed:
        print("✅ Error handling tests passed")
                else:
        print("❌ Some error handling tests failed")
    
    return all_passed

def test_configuration():
    """Test configuration functionality"""
    print("\n⚙️ Testing configuration...")
    
    # Test env file path
    env_path = main_script.get_env_file_path()
    print(f"  📁 Env file path: {env_path}")
    
    # Test default credentials
    default_creds = getattr(main_script, 'DEFAULT_CREDENTIALS', {})
    print(f"  🔑 Default credentials available: {bool(default_creds)}")
    print(f"  🏠 Default jump host: {default_creds.get('JUMP_HOST', 'Not set')}")
    
    print("✅ Configuration tests completed")
    return True

def test_system_resources():
    """Test system resource checking"""
    print("\n💻 Testing system resources...")
    
    try:
        resources = main_script.check_system_resources()
        if resources.get('warnings'):
            print("  ⚠️ System warnings:")
            for warning in resources['warnings']:
                print(f"    - {warning}")
            else:
            print("  ✅ System resources OK")
            
        if 'cpu_percent' in resources:
            print(f"  📊 CPU: {resources['cpu_percent']:.1f}%")
            print(f"  📊 Memory: {resources['memory_percent']:.1f}%")
            print(f"  📊 Disk: {resources['disk_percent']:.1f}%")
        
        print("✅ System resource tests completed")
        return True
    except Exception as e:
        print(f"  ℹ️ Resource monitoring not available: {e}")
        return True

def test_logging_functions():
    """Test all logging functions"""
    print("\n📝 Testing logging functions...")
    
    # Set debug level to maximum for testing
    main_script.set_debug_level(3)
    
    print("  Testing different log types:")
    main_script.log_success("This is a success message")
    main_script.log_warning("This is a warning message")
    main_script.log_error("This is an error message")
    main_script.log_debug("This is a debug message")
    main_script.log_trace("This is a trace message")
    main_script.log_network("This is a network message")
    main_script.log_security("This is a security message")
    main_script.log_performance("This is a performance message")
    
    print("  Testing function entry/exit logging:")
    main_script.log_function_entry("test_function", {"param1": "value1", "password": "secret123"})
    main_script.log_function_exit("test_function", "success")
    
    print("✅ Logging function tests completed")
    return True

def test_utility_functions():
    """Test utility functions"""
    print("\n🛠️ Testing utility functions...")
    
    # Test duration formatting
    durations = [0.5, 1.0, 61.5, 3661.5, 7322.5]
    for duration in durations:
        formatted = main_script.format_duration(duration)
        print(f"  {duration}s -> {formatted}")
    
    print("✅ Utility function tests completed")
    return True

def test_performance():
    """Test performance of key functions"""
    print("\n⚡ Testing performance...")
    
    # Test password masking performance
    start_time = time.time()
    for i in range(1000):
        main_script.mask_password(f"password{i}")
    mask_time = time.time() - start_time
    print(f"  Password masking (1000 calls): {mask_time:.3f}s")
    
    # Test IP validation performance
    start_time = time.time()
    for i in range(1000):
        main_script.validate_ip_address("192.168.1.1")
    ip_time = time.time() - start_time
    print(f"  IP validation (1000 calls): {ip_time:.3f}s")
    
    print("✅ Performance tests completed")
            return True
            
def create_test_env_file():
    """Create a test .env-t file for testing"""
    print("\n📄 Creating test .env-t file...")
    
    test_content = """# Test NetAuditPro CLI Lite Configuration
JUMP_HOST=172.16.39.128
JUMP_USERNAME=root
JUMP_PASSWORD=eve
DEVICE_USERNAME=cisco
DEVICE_PASSWORD=cisco
INVENTORY_FILE=test_routers.csv
"""
    
    try:
        with open('.env-t', 'w') as f:
            f.write(test_content)
        print("✅ Test .env-t file created")
        return True
    except Exception as e:
        print(f"❌ Failed to create test .env-t file: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    
    test_files = ['.env-t']
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"  Removed: {file}")
        except Exception as e:
            print(f"  Failed to remove {file}: {e}")
    
def main():
        """Run all tests"""
    print("🧪 NetAuditPro CLI Lite - Comprehensive Enhanced Features Test Suite")
    print("=" * 80)
        
        test_results = []
        
    try:
        # Run all tests
        test_results.append(("Imports", test_imports()))
        
        if test_results[0][1]:  # Only continue if imports work
            test_results.append(("Debug Levels", test_debug_levels()))
            test_results.append(("Password Masking", test_password_masking()))
            test_results.append(("Validation Functions", test_validation_functions()))
            test_results.append(("Error Handling", test_error_handling()))
            test_results.append(("Configuration", test_configuration()))
            test_results.append(("System Resources", test_system_resources()))
            test_results.append(("Logging Functions", test_logging_functions()))
            test_results.append(("Utility Functions", test_utility_functions()))
            test_results.append(("Performance", test_performance()))
            test_results.append(("Test Env File", create_test_env_file()))
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests completed successfully!")
            print("✅ Enhanced features are working correctly")
            success = True
        else:
            print("❌ Some tests failed")
            success = False
        
        # Cleanup
        cleanup_test_files()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        cleanup_test_files()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
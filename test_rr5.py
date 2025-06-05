#!/usr/bin/env python3
"""
Test script for RR5 Router Auditing Framework
Verifies basic functionality without actual network connections
"""

import sys
import os
import tempfile
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        # Import the main script (this will test all imports)
        import importlib.util
        spec = importlib.util.spec_from_file_location("rr5", "rr5-router-new-new.py")
        rr5 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rr5)
        
        print("✅ All imports successful")
        return True, rr5
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False, None

def test_configuration(rr5):
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        config = rr5.DEFAULT_CONFIG.copy()
        
        # Test config validation
        assert config['jump_host'] == "172.16.39.128"
        assert config['web_port'] == 5015
        assert config['timeout'] == 30
        
        print("✅ Configuration test passed")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_inventory_parsing(rr5):
    """Test inventory file parsing"""
    print("\nTesting inventory parsing...")
    try:
        # Create temporary CSV inventory
        csv_content = """device_name,ip_address,device_type,description,location,group
PE01,10.0.1.1,cisco_ios_xe,PE Router 1,DC1,pe_routers
PE02,10.0.1.2,cisco_ios_xe,PE Router 2,DC1,pe_routers
P01,10.0.2.1,cisco_ios_xr,P Router 1,DC1,p_routers"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            devices = rr5.parse_inventory(temp_file)
            assert len(devices) == 3
            assert devices[0].name == "PE01"
            assert devices[0].device_type == "cisco_ios_xe"
            assert devices[2].device_type == "cisco_ios_xr"
            
            print("✅ Inventory parsing test passed")
            return True
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ Inventory parsing test failed: {e}")
        return False

def test_data_structures(rr5):
    """Test data structure creation"""
    print("\nTesting data structures...")
    try:
        # Test DeviceInfo
        device = rr5.DeviceInfo(
            name="TEST01",
            ip_address="10.0.1.100",
            device_type="cisco_ios",
            description="Test device"
        )
        
        # Test HealthMetrics
        health = rr5.HealthMetrics(
            timestamp=datetime.now().isoformat(),
            device="TEST01",
            cpu_percent=25.5,
            memory_used_percent=60.0,
            memory_free_percent=40.0,
            disk_used_percent=30.0,
            disk_free_percent=70.0,
            temperature_max=45.0,
            power_status="OK",
            environment_status="OK",
            chassis_status="OK"
        )
        
        # Test AuditResult
        result = rr5.AuditResult(
            check_name="test_check",
            category="test",
            pre_value="100",
            post_value="105",
            delta="+5",
            status="PASS",
            threshold="<200",
            message="Test check passed"
        )
        
        print("✅ Data structures test passed")
        return True
        
    except Exception as e:
        print(f"❌ Data structures test failed: {e}")
        return False

def test_logger(rr5):
    """Test logging functionality"""
    print("\nTesting logger...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            logger = rr5.AuditLogger(log_file)
            
            logger.log("Test message", "INFO")
            logger.log("Test warning", "WARNING")
            logger.log("Test error", "ERROR")
            
            logs = logger.get_logs()
            assert len(logs) == 3
            assert logs[0]['message'] == "Test message"
            assert logs[1]['level'] == "WARNING"
            
            print("✅ Logger test passed")
            return True
            
    except Exception as e:
        print(f"❌ Logger test failed: {e}")
        return False

def test_data_parser(rr5):
    """Test data parsing functionality"""
    print("\nTesting data parser...")
    try:
        logger = rr5.AuditLogger()
        parser = rr5.DataParser(logger)
        
        # Test CPU/Memory parsing
        sample_output = """
        CPU utilization for five seconds: 25%/15%; one minute: 22%; five minutes: 18%
        
        Total: 2048000 Used: 1024000 Free: 1024000
        """
        
        result = parser.parse_cpu_memory(sample_output, "cisco_ios")
        assert result['cpu_percent'] == 25.0
        assert result['memory_free_percent'] == 50.0
        
        # Test random route extraction
        route_output = """
        10.1.1.0/24     10.0.1.1        100    200
        10.2.2.0/24     10.0.2.1        110    300
        10.3.3.0/24     10.0.3.1        120    400
        """
        
        routes = parser.extract_random_routes(route_output)
        assert len(routes) >= 1
        assert '10.1.1.0' in routes[0]['prefix']
        
        print("✅ Data parser test passed")
        return True
        
    except Exception as e:
        print(f"❌ Data parser test failed: {e}")
        return False

def test_report_generator(rr5):
    """Test report generation"""
    print("\nTesting report generator...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = rr5.AuditLogger()
            reporter = rr5.ReportGenerator(temp_dir, logger)
            
            # Create sample results
            results = [
                rr5.AuditResult(
                    check_name="test_cpu",
                    category="health",
                    pre_value="20%",
                    post_value="25%",
                    delta="+5%",
                    status="PASS",
                    threshold="<70%",
                    message="CPU usage within limits"
                ),
                rr5.AuditResult(
                    check_name="test_interface",
                    category="interface",
                    pre_value="up",
                    post_value="down",
                    delta="Status changed",
                    status="FAIL",
                    threshold="up",
                    message="Interface went down"
                )
            ]
            
            # Test CLI report
            cli_report = reporter.generate_cli_report(results)
            assert "RR5 ROUTER AUDIT RESULTS SUMMARY" in cli_report
            assert "PASS: 1" in cli_report
            assert "FAIL: 1" in cli_report
            
            # Test JSON report
            json_file = reporter.generate_json_report(results, "test_results.json")
            assert os.path.exists(json_file)
            
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            assert json_data['summary']['total'] == 2
            assert json_data['summary']['pass'] == 1
            assert json_data['summary']['fail'] == 1
            
            print("✅ Report generator test passed")
            return True
            
    except Exception as e:
        print(f"❌ Report generator test failed: {e}")
        return False

def test_credential_sanitization(rr5):
    """Test credential sanitization"""
    print("\nTesting credential sanitization...")
    try:
        # Test various credential patterns
        test_cases = [
            ("password: mypassword123", "password: ####"),
            ("username: admin", "username: ****"),
            ("ssh admin@192.168.1.1", "ssh ****@192.168.1.1"),
            ("admin:secret@router", "****:####@router"),
            ("enable: enable_pass", "enable: ####")
        ]
        
        for input_text, expected in test_cases:
            result = rr5.sanitize_credentials(input_text)
            assert expected in result, f"Failed for: {input_text} -> {result}"
        
        print("✅ Credential sanitization test passed")
        return True
        
    except Exception as e:
        print(f"❌ Credential sanitization test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting RR5 Router Auditing Framework Tests")
    print("=" * 60)
    
    # First test imports
    import_success, rr5 = test_imports()
    if not import_success:
        print("❌ Cannot continue testing without successful imports")
        return 1
    
    tests = [
        (test_configuration, rr5),
        (test_inventory_parsing, rr5),
        (test_data_structures, rr5),
        (test_logger, rr5),
        (test_data_parser, rr5),
        (test_report_generator, rr5),
        (test_credential_sanitization, rr5)
    ]
    
    passed = 1  # Import test already passed
    failed = 0
    
    for test_func, module in tests:
        try:
            if test_func(module):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! RR5 Router Auditing Framework is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
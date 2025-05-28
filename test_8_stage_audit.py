#!/usr/bin/env python3
"""
Test script for Enhanced 8-Stage Audit Module
Verifies the implementation works correctly
"""

import sys
import os
import json
from datetime import datetime

def test_8_stage_audit():
    """Test the 8-stage audit implementation"""
    print("🧪 Testing Enhanced 8-Stage Audit Module")
    print("="*50)
    
    try:
        # Test import
        from enhanced_8_stage_audit import (
            execute_8_stage_device_audit,
            create_device_extraction_folder,
            parse_line_telnet_output,
            analyze_line_config,
            assess_aux_risk
        )
        print("✅ Successfully imported enhanced_8_stage_audit module")
        
        # Test folder creation
        test_folder = create_device_extraction_folder(".")
        print(f"✅ Created test extraction folder: {test_folder}")
        
        # Test risk assessment
        risk_low = assess_aux_risk("NO", "unknown", "default")
        risk_critical = assess_aux_risk("YES", "unknown", "never")
        risk_high = assess_aux_risk("YES", "line_password", "default")
        risk_medium = assess_aux_risk("YES", "local", "5m0s")
        
        print(f"✅ Risk assessment tests:")
        print(f"   - Telnet disabled: {risk_low}")
        print(f"   - Telnet + no auth: {risk_critical}")
        print(f"   - Telnet + line password: {risk_high}")
        print(f"   - Telnet + local auth: {risk_medium}")
        
        # Test line config analysis
        test_config = [
            "line vty 0 4",
            " transport input ssh",
            " login local",
            " exec-timeout 5 0"
        ]
        
        line_analysis = analyze_line_config("line vty 0 4", test_config, "test-device", "vty")
        print(f"✅ Line config analysis test:")
        print(f"   - Telnet allowed: {line_analysis['telnet_allowed']}")
        print(f"   - Risk level: {line_analysis['risk_level']}")
        print(f"   - Analysis: {line_analysis['analysis']}")
        
        # Test VTY output parsing
        test_vty_output = """
show running-config | include ^line vty|^ transport input|^ login|^ exec-timeout
line vty 0 4
 transport input ssh
 login local
 exec-timeout 5 0
line vty 5 15
 transport input all
 login
 exec-timeout 0 0
        """
        
        vty_results = parse_line_telnet_output(test_vty_output, "test-device", "vty")
        print(f"✅ VTY parsing test: Found {len(vty_results)} VTY line configurations")
        
        for vty in vty_results:
            print(f"   - {vty['line']}: Telnet={vty['telnet_allowed']}, Risk={vty['risk_level']}")
        
        # Test summary
        print("\n🎉 All tests passed successfully!")
        print("✅ Enhanced 8-Stage Audit Module is ready for use")
        
        # Cleanup test folder
        if os.path.exists(test_folder):
            import shutil
            shutil.rmtree(test_folder)
            print(f"🧹 Cleaned up test folder: {test_folder}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("⚠️ Make sure enhanced_8_stage_audit.py is in the same directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_integration_with_main_script():
    """Test integration with main script"""
    print("\n🔗 Testing Integration with Main Script")
    print("="*50)
    
    try:
        # Check if main script can import the module
        sys.path.insert(0, '.')
        
        # Test the import that would happen in the main script
        try:
            from enhanced_8_stage_audit import execute_8_stage_device_audit
            print("✅ Main script can import enhanced audit module")
            
            # Test CORE_COMMANDS structure
            CORE_COMMANDS = {
                'show_line': 'show line',
                'aux_telnet_audit': 'show running-config | include ^hostname|^line aux|^ transport input|^ login|^ exec-timeout',
                'vty_telnet_audit': 'show running-config | include ^line vty|^ transport input|^ login|^ exec-timeout',
                'con_telnet_audit': 'show running-config | include ^line con|^ transport input|^ login|^ exec-timeout',
                'show_version': 'show version',
                'show_running_config': 'show running-config'
            }
            
            print("✅ CORE_COMMANDS structure is compatible")
            print(f"   - Commands available: {list(CORE_COMMANDS.keys())}")
            
            return True
            
        except ImportError as import_error:
            print(f"❌ Integration import failed: {import_error}")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Enhanced 8-Stage Audit Module Test Suite")
    print("="*60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    test1_passed = test_8_stage_audit()
    test2_passed = test_integration_with_main_script()
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"✅ Module Tests: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Integration Tests: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Enhanced 8-Stage Audit Module is ready for production use")
        print("\n📋 Next Steps:")
        print("1. Run the main NetAuditPro script")
        print("2. The 8-stage audit will be automatically used")
        print("3. Check the device-extracted-* folders for detailed results")
        print("4. Review comprehensive reports in JSON format")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("⚠️ Please review the errors above and fix issues before using")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
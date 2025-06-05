#!/usr/bin/env python3
"""
Safe Testing Wrapper for V4CODERCLI Options
Provides automated testing with proper timeouts and input handling
"""

import subprocess
import sys
import time
from pathlib import Path

def test_option_with_timeout(option_num, timeout=30, input_data="0\n"):
    """
    Test an option with timeout and automated input
    
    Args:
        option_num: Option number to test
        timeout: Maximum time to wait
        input_data: Input to provide to the script
    
    Returns:
        (success, output, error)
    """
    cmd = [sys.executable, "start_rr4_cli_enhanced.py", "--option", str(option_num)]
    
    try:
        print(f"🧪 Testing Option {option_num} (timeout: {timeout}s)...")
        
        result = subprocess.run(
            cmd,
            input=input_data,
            text=True,
            capture_output=True,
            timeout=timeout
        )
        
        success = result.returncode == 0
        if success:
            print(f"✅ Option {option_num}: SUCCESS")
        else:
            print(f"❌ Option {option_num}: FAILED (exit code: {result.returncode})")
            
        return success, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Option {option_num}: TIMEOUT after {timeout}s")
        return False, "", "Timeout"
        
    except Exception as e:
        print(f"💥 Option {option_num}: ERROR - {str(e)}")
        return False, "", str(e)

def test_all_options():
    """Test all options systematically with appropriate inputs"""
    
    # Define test configurations for each option
    test_configs = {
        0: {"timeout": 5, "input": "\n", "description": "EXIT"},
        1: {"timeout": 30, "input": "n\n", "description": "FIRST-TIME SETUP"},
        2: {"timeout": 60, "input": "y\n", "description": "AUDIT ONLY"},
        3: {"timeout": 90, "input": "n\n", "description": "FULL COLLECTION"},
        4: {"timeout": 30, "input": "q\n", "description": "CUSTOM COLLECTION"},
        5: {"timeout": 30, "input": "\n", "description": "PREREQUISITES CHECK"},
        6: {"timeout": 60, "input": "\n", "description": "ENHANCED CONNECTIVITY"},
        7: {"timeout": 10, "input": "\n", "description": "HELP & OPTIONS"},
        8: {"timeout": 60, "input": "y\n", "description": "CONSOLE AUDIT"},
        9: {"timeout": 90, "input": "n\n", "description": "COMPLETE COLLECTION"},
        10: {"timeout": 60, "input": "y\n", "description": "CONSOLE SECURITY AUDIT"},
        11: {"timeout": 60, "input": "n\nn\n", "description": "FIRST-TIME WIZARD"},
        12: {"timeout": 30, "input": "0\n", "description": "STATUS REPORT"},
        13: {"timeout": 30, "input": "\n", "description": "INSTALLATION VERIFICATION"},
        14: {"timeout": 10, "input": "\n", "description": "PLATFORM STARTUP GUIDE"},
        15: {"timeout": 10, "input": "q\n", "description": "QUICK REFERENCE GUIDE"}
    }
    
    print("🚀 V4CODERCLI COMPREHENSIVE OPTION TESTING")
    print("=" * 50)
    
    results = {}
    total_tests = len(test_configs)
    passed = 0
    failed = 0
    timeouts = 0
    
    for option_num, config in test_configs.items():
        print(f"\n📋 Option {option_num}: {config['description']}")
        print("-" * 40)
        
        success, stdout, stderr = test_option_with_timeout(
            option_num,
            timeout=config['timeout'],
            input_data=config['input']
        )
        
        results[option_num] = {
            'success': success,
            'description': config['description'],
            'stdout': stdout,
            'stderr': stderr
        }
        
        if success:
            passed += 1
        elif stderr == "Timeout":
            timeouts += 1
        else:
            failed += 1
        
        # Brief pause between tests
        time.sleep(1)
    
    # Generate summary report
    print("\n" + "=" * 50)
    print("🏆 COMPREHENSIVE TESTING SUMMARY")
    print("=" * 50)
    
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏰ Timeouts: {timeouts}")
    print(f"📈 Success Rate: {(passed/total_tests)*100:.1f}%")
    
    print("\n📋 DETAILED RESULTS:")
    print("-" * 30)
    
    for option_num in sorted(results.keys()):
        result = results[option_num]
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"Option {option_num:2d}: {status} - {result['description']}")
    
    # Identify problematic options
    failed_options = [num for num, result in results.items() if not result['success']]
    if failed_options:
        print(f"\n🔧 FAILED OPTIONS REQUIRING FIXES: {failed_options}")
        
        print("\n🐛 FAILURE ANALYSIS:")
        for option_num in failed_options:
            result = results[option_num]
            print(f"\nOption {option_num} - {result['description']}:")
            if result['stderr']:
                print(f"  Error: {result['stderr'][:200]}...")
    
    return results

def test_specific_problematic_options():
    """Test the specific options that were causing issues"""
    
    print("🎯 TESTING PROBLEMATIC OPTIONS")
    print("=" * 35)
    
    problematic = [3, 4, 12]  # Options that had infinite loops/hanging
    
    for option_num in problematic:
        print(f"\n🔍 Deep testing Option {option_num}...")
        
        # Test with different input patterns
        test_inputs = [
            ("Cancel immediately", "0\n"),
            ("EOF simulation", ""),
            ("Invalid then cancel", "invalid\n0\n"),
            ("Multiple invalid", "x\ny\nz\n0\n")
        ]
        
        for test_name, input_data in test_inputs:
            print(f"  • {test_name}...")
            success, stdout, stderr = test_option_with_timeout(
                option_num, timeout=10, input_data=input_data
            )
            status = "✅" if success else "❌"
            print(f"    {status} Result: {'PASS' if success else 'FAIL'}")

if __name__ == "__main__":
    # Change to V4codercli directory
    script_dir = Path(__file__).parent
    if script_dir.name != "V4codercli":
        print("❌ Please run this script from the V4codercli directory")
        sys.exit(1)
    
    print("🧪 V4CODERCLI SAFE TESTING FRAMEWORK")
    print("=" * 40)
    
    # Check if main script exists
    if not Path("start_rr4_cli_enhanced.py").exists():
        print("❌ start_rr4_cli_enhanced.py not found!")
        sys.exit(1)
    
    choice = input("\n📋 Choose testing mode:\n"
                  "  1. Test all options (comprehensive)\n"
                  "  2. Test problematic options only\n"
                  "  3. Test specific option\n"
                  "Choice (1-3): ").strip()
    
    if choice == "1":
        results = test_all_options()
    elif choice == "2":
        test_specific_problematic_options()
    elif choice == "3":
        option_num = input("Enter option number (0-15): ").strip()
        try:
            opt = int(option_num)
            if 0 <= opt <= 15:
                success, stdout, stderr = test_option_with_timeout(opt)
                print(f"\nResult: {'✅ SUCCESS' if success else '❌ FAILURE'}")
                if stderr:
                    print(f"Error: {stderr}")
            else:
                print("❌ Invalid option number")
        except ValueError:
            print("❌ Please enter a valid number")
    else:
        print("❌ Invalid choice")
    
    print("\n🎉 Testing completed!") 
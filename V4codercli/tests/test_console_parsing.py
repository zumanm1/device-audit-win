#!/usr/bin/env python3
"""
Test script for console line parsing enhancements

This script tests the console line collector's ability to parse
IOS and IOS XR show line output correctly.
"""

import sys
import os
sys.path.append('rr4_complete_enchanced_v4_cli_tasks')

from console_line_collector import ConsoleLineCollector
import json

def test_ios_parsing():
    """Test IOS console line parsing."""
    print("🧪 Testing IOS Console Line Parsing")
    print("=" * 50)
    
    # Load test data
    with open('test_data_ios_console_lines.txt', 'r') as f:
        ios_output = f.read()
    
    collector = ConsoleLineCollector()
    
    # Parse the output
    parsed_lines = collector.parse_show_line_output(ios_output, 'ios')
    console_lines = collector.extract_console_lines(parsed_lines)
    
    print(f"📊 Parsed {len(parsed_lines)} total lines")
    print(f"📊 Found {len(console_lines)} console lines")
    
    # Show first few console lines
    print(f"\n🔍 First 10 console lines found:")
    for i, line in enumerate(console_lines[:10]):
        print(f"  {i+1}. {line}")
    
    # Show expected range
    expected_lines = []
    for x in [0]:  # Only slot 0 in our test data
        for y in [0, 1]:  # Both subslots
            for z in range(23):  # 0-22
                expected_lines.append(f"{x}/{y}/{z}")
    
    print(f"\n📈 Expected {len(expected_lines)} lines (0/0/0 through 0/1/22)")
    print(f"📈 Found {len(console_lines)} lines")
    
    # Check if we found all expected lines
    missing_lines = set(expected_lines) - set(console_lines)
    extra_lines = set(console_lines) - set(expected_lines)
    
    if missing_lines:
        print(f"❌ Missing lines: {sorted(list(missing_lines))[:5]}... ({len(missing_lines)} total)")
    else:
        print("✅ All expected lines found!")
        
    if extra_lines:
        print(f"⚠️  Extra lines: {sorted(list(extra_lines))}")
    
    # Generate configuration commands
    config_commands = collector.get_line_configuration_commands(console_lines[:5], 'ios')
    print(f"\n🔧 Sample configuration commands:")
    for cmd in config_commands[:3]:
        print(f"  {cmd}")
    
    return len(console_lines), expected_lines

def test_iosxr_parsing():
    """Test IOS XR console line parsing."""
    print("\n🧪 Testing IOS XR Console Line Parsing")
    print("=" * 50)
    
    # Load test data
    with open('test_data_iosxr_console_lines.txt', 'r') as f:
        iosxr_output = f.read()
    
    collector = ConsoleLineCollector()
    
    # Parse the output
    parsed_lines = collector.parse_show_line_output(iosxr_output, 'iosxr')
    console_lines = collector.extract_console_lines(parsed_lines)
    
    print(f"📊 Parsed {len(parsed_lines)} total lines")
    print(f"📊 Found {len(console_lines)} console lines")
    
    # Show first few console lines
    print(f"\n🔍 First 10 console lines found:")
    for i, line in enumerate(console_lines[:10]):
        print(f"  {i+1}. {line}")
    
    # Show expected range
    expected_lines = []
    for x in [0]:  # Only slot 0 in our test data
        for y in [0, 1]:  # Both subslots
            for z in range(23):  # 0-22
                expected_lines.append(f"{x}/{y}/{z}")
    
    print(f"\n📈 Expected {len(expected_lines)} lines (0/0/0 through 0/1/22)")
    print(f"📈 Found {len(console_lines)} lines")
    
    # Check if we found all expected lines
    missing_lines = set(expected_lines) - set(console_lines)
    extra_lines = set(console_lines) - set(expected_lines)
    
    if missing_lines:
        print(f"❌ Missing lines: {sorted(list(missing_lines))[:5]}... ({len(missing_lines)} total)")
    else:
        print("✅ All expected lines found!")
        
    if extra_lines:
        print(f"⚠️  Extra lines: {sorted(list(extra_lines))}")
    
    # Generate configuration commands
    config_commands = collector.get_line_configuration_commands(console_lines[:5], 'iosxr')
    print(f"\n🔧 Sample configuration commands:")
    for cmd in config_commands[:3]:
        print(f"  {cmd}")
    
    return len(console_lines), expected_lines

def generate_sample_outputs():
    """Generate sample JSON and text outputs."""
    print("\n📄 Generating Sample Output Files")
    print("=" * 50)
    
    # Sample console line data for IOS
    ios_sample_data = {
        "device": "192.168.1.100",
        "timestamp": "2025-01-27T01:00:00Z",
        "platform": "ios",
        "show_line_output": "Router#show line\n   Tty Line Typ     Tx/Rx    A Roty AccO AccI   Uses   Noise  Overruns   Int\n   33   33 AUX   9600/9600  -    -    -    -      0       0     0/0    0/0/0\n   34   34 AUX   9600/9600  -    -    -    -      1       0     0/0    0/0/1",
        "console_lines": {
            "0/0/0": {
                "line_type": "aux",
                "status": "available",
                "configuration": "line 0/0/0\n session-timeout 0\n exec-timeout 0 0\n transport input all\n transport output all\n stopbits 1",
                "command_used": "show running-config | section \"line 0/0/0\"",
                "success": True
            },
            "0/0/1": {
                "line_type": "aux", 
                "status": "available",
                "configuration": "line 0/0/1\n session-timeout 0\n exec-timeout 0 0\n transport input all\n transport output all\n stopbits 1",
                "command_used": "show running-config | section \"line 0/0/1\"",
                "success": True
            }
        },
        "discovered_lines": ["0/0/0", "0/0/1", "0/0/2", "0/0/3", "0/0/4"],
        "configured_lines": ["0/0/0", "0/0/1"],
        "summary": {
            "total_lines_discovered": 46,
            "total_lines_configured": 2,
            "configuration_success_rate": 100.0,
            "overall_success_rate": 100.0
        }
    }
    
    # Sample console line data for IOS XR
    iosxr_sample_data = {
        "device": "192.168.1.200",
        "timestamp": "2025-01-27T01:00:00Z",
        "platform": "iosxr",
        "show_line_output": "RP/0/RP0/CPU0:Router#show line\n   Tty    Line   Typ       Tx/Rx    A Modem  Roty AccO AccI   Uses   Noise  A-bit  Overruns   Int\n   0/0/0    33   AUX      9600/9600 -    -    -    -    -    -      0       0      -     0/0    0/0/0\n   0/0/1    34   AUX      9600/9600 -    -    -    -    -    -      1       0      -     0/0    0/0/1",
        "console_lines": {
            "0/0/0": {
                "line_type": "aux",
                "status": "available",
                "configuration": "line aux 0/0/0\n exec-timeout 0 0\n absolute-timeout 0\n session-timeout 0\n transport input all\n transport output all\n width 0\n length 0",
                "command_used": "show running-config line aux 0/0/0",
                "success": True
            },
            "0/0/1": {
                "line_type": "aux",
                "status": "available", 
                "configuration": "line aux 0/0/1\n exec-timeout 0 0\n absolute-timeout 0\n session-timeout 0\n transport input all\n transport output all\n width 0\n length 0",
                "command_used": "show running-config line aux 0/0/1",
                "success": True
            }
        },
        "discovered_lines": ["0/0/0", "0/0/1", "0/0/2", "0/0/3", "0/0/4"],
        "configured_lines": ["0/0/0", "0/0/1"],
        "summary": {
            "total_lines_discovered": 46,
            "total_lines_configured": 2,
            "configuration_success_rate": 100.0,
            "overall_success_rate": 100.0
        }
    }
    
    # Save sample JSON files
    with open('sample_ios_console_output.json', 'w') as f:
        json.dump(ios_sample_data, f, indent=2)
    print("✅ Created: sample_ios_console_output.json")
    
    with open('sample_iosxr_console_output.json', 'w') as f:
        json.dump(iosxr_sample_data, f, indent=2)
    print("✅ Created: sample_iosxr_console_output.json")
    
    # Generate sample text outputs
    ios_text = f"""Console Line Collection Report - IOS Device
Device: {ios_sample_data['device']}
Platform: {ios_sample_data['platform']}
Timestamp: {ios_sample_data['timestamp']}

Console Lines Discovered: {len(ios_sample_data['discovered_lines'])}
Console Lines Configured: {len(ios_sample_data['configured_lines'])}
Success Rate: {ios_sample_data['summary']['configuration_success_rate']}%

Console Line Configurations:
----------------------------
Line 0/0/0 (AUX):
{ios_sample_data['console_lines']['0/0/0']['configuration']}

Line 0/0/1 (AUX):
{ios_sample_data['console_lines']['0/0/1']['configuration']}

All discovered lines: {', '.join(ios_sample_data['discovered_lines'])}
"""
    
    iosxr_text = f"""Console Line Collection Report - IOS XR Device
Device: {iosxr_sample_data['device']}
Platform: {iosxr_sample_data['platform']}
Timestamp: {iosxr_sample_data['timestamp']}

Console Lines Discovered: {len(iosxr_sample_data['discovered_lines'])}
Console Lines Configured: {len(iosxr_sample_data['configured_lines'])}
Success Rate: {iosxr_sample_data['summary']['configuration_success_rate']}%

Console Line Configurations:
----------------------------
Line 0/0/0 (AUX):
{iosxr_sample_data['console_lines']['0/0/0']['configuration']}

Line 0/0/1 (AUX):
{iosxr_sample_data['console_lines']['0/0/1']['configuration']}

All discovered lines: {', '.join(iosxr_sample_data['discovered_lines'])}
"""
    
    with open('sample_ios_console_output.txt', 'w') as f:
        f.write(ios_text)
    print("✅ Created: sample_ios_console_output.txt")
    
    with open('sample_iosxr_console_output.txt', 'w') as f:
        f.write(iosxr_text)
    print("✅ Created: sample_iosxr_console_output.txt")

def main():
    """Run all tests."""
    print("🚀 Console Line Collector - Enhanced Parsing Test")
    print("=" * 60)
    
    try:
        # Test IOS parsing
        ios_found, ios_expected = test_ios_parsing()
        
        # Test IOS XR parsing
        iosxr_found, iosxr_expected = test_iosxr_parsing()
        
        # Generate sample outputs
        generate_sample_outputs()
        
        # Summary
        print(f"\n🎯 Test Summary")
        print("=" * 50)
        print(f"IOS Parsing: Found {ios_found}/{len(ios_expected)} lines")
        print(f"IOS XR Parsing: Found {iosxr_found}/{len(iosxr_expected)} lines")
        
        if ios_found == len(ios_expected) and iosxr_found == len(iosxr_expected):
            print("✅ All tests passed! Console parsing is working correctly.")
            return True
        else:
            print("❌ Some tests failed. Check parsing logic.")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
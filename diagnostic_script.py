#!/usr/bin/env python3
"""
NetAuditPro v3 Diagnostic Script
Analyzes timing issues, API responses, and system state
"""

import requests
import json
import time
from datetime import datetime
import sys

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n📊 {title}")
    print("-" * 40)

def test_api_endpoint(url, endpoint_name):
    """Test an API endpoint and analyze response"""
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ {endpoint_name}: Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   📄 Response Keys: {list(data.keys())}")
            
            # Analyze timing data specifically
            if 'timing' in data:
                timing = data['timing']
                print(f"   ⏰ Timing Keys: {list(timing.keys())}")
                print(f"   📅 Start Time: {timing.get('raw_start_time', 'None')}")
                print(f"   📅 Completion Time: {timing.get('raw_completion_time', 'None')}")
                print(f"   ⏱️ Is Running: {timing.get('is_running', 'None')}")
                print(f"   ⏸️ Is Paused: {timing.get('is_paused', 'None')}")
            
            # Analyze progress data
            if 'status' in data:
                print(f"   📊 Status: {data.get('status', 'None')}")
                print(f"   🎯 Progress: {data.get('percent_complete', 'None')}%")
                
            return data
        else:
            print(f"   ❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ {endpoint_name}: Error - {e}")
        return None

def analyze_timing_data(timing_data, progress_data):
    """Analyze timing data for inconsistencies"""
    print_section("TIMING DATA ANALYSIS")
    
    if not timing_data or not progress_data:
        print("❌ Missing data for analysis")
        return
    
    # Check for date formatting issues
    timing = timing_data.get('timing', {})
    raw_start = timing.get('raw_start_time')
    raw_completion = timing.get('raw_completion_time')
    
    print(f"🔍 Raw Start Time: {raw_start} (Type: {type(raw_start)})")
    print(f"🔍 Raw Completion Time: {raw_completion} (Type: {type(raw_completion)})")
    
    # Check status consistency
    timing_running = timing.get('is_running', False)
    timing_paused = timing.get('is_paused', False)
    progress_status = progress_data.get('status', 'Unknown')
    
    print(f"🔍 Timing Running: {timing_running}")
    print(f"🔍 Timing Paused: {timing_paused}")
    print(f"🔍 Progress Status: {progress_status}")
    
    # Identify inconsistencies
    issues = []
    
    if raw_start is None and progress_status in ['Running', 'Completed']:
        issues.append("❌ Missing start time for active/completed audit")
    
    if progress_status == 'Completed' and raw_completion is None:
        issues.append("❌ Missing completion time for completed audit")
    
    if progress_status == 'Completed' and timing_running:
        issues.append("❌ Timing shows running but audit is completed")
    
    if progress_status == 'Running' and not timing_running and not timing_paused:
        issues.append("❌ Audit running but timing not active")
    
    if issues:
        print("\n🚨 IDENTIFIED ISSUES:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ No timing inconsistencies detected")

def test_javascript_functions():
    """Test if JavaScript functions are available via browser"""
    print_section("JAVASCRIPT FUNCTION AVAILABILITY")
    
    js_test_script = """
    // Test JavaScript function availability
    const functions = [
        'updateTimingDisplay',
        'updateProgressStats', 
        'fetchProgressData',
        'fetchTimingData',
        'startAutoRefresh',
        'stopAutoRefresh'
    ];
    
    const results = {};
    functions.forEach(func => {
        results[func] = typeof window[func] !== 'undefined';
    });
    
    return results;
    """
    
    print("📝 JavaScript functions to test:")
    functions = ['updateTimingDisplay', 'updateProgressStats', 'fetchProgressData', 
                'fetchTimingData', 'startAutoRefresh', 'stopAutoRefresh']
    for func in functions:
        print(f"   • {func}")

def generate_recommendations(timing_data, progress_data):
    """Generate fix recommendations based on analysis"""
    print_section("FIX RECOMMENDATIONS")
    
    recommendations = []
    
    if timing_data and timing_data.get('timing', {}).get('raw_start_time') is None:
        recommendations.append({
            'priority': 'P1',
            'issue': 'Missing start time data',
            'fix': 'Ensure start_audit_timing() properly sets raw_start_time',
            'code_location': 'start_audit_timing() function'
        })
    
    if progress_data and progress_data.get('status') == 'Completed':
        timing = timing_data.get('timing', {}) if timing_data else {}
        if timing.get('is_running', False):
            recommendations.append({
                'priority': 'P1', 
                'issue': 'Status inconsistency - completed but timing running',
                'fix': 'Call complete_audit_timing() when audit completes',
                'code_location': 'run_complete_audit() function'
            })
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['priority']}] {rec['issue']}")
            print(f"   💡 Fix: {rec['fix']}")
            print(f"   📍 Location: {rec['code_location']}")
            print()
    else:
        print("✅ No specific recommendations at this time")

def main():
    """Main diagnostic function"""
    print_header("NetAuditPro v3 Diagnostic Analysis")
    print(f"🕐 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:5011"
    
    # Test API endpoints
    print_section("API ENDPOINT TESTING")
    timing_data = test_api_endpoint(f"{base_url}/api/timing", "Timing API")
    progress_data = test_api_endpoint(f"{base_url}/api/progress", "Progress API")
    
    # Test basic connectivity
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Main Application: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Main Application: Error - {e}")
        return
    
    # Analyze timing data
    analyze_timing_data(timing_data, progress_data)
    
    # Test JavaScript functions (placeholder)
    test_javascript_functions()
    
    # Generate recommendations
    generate_recommendations(timing_data, progress_data)
    
    # Summary
    print_section("DIAGNOSTIC SUMMARY")
    print("📋 Analysis completed successfully")
    print("📄 Check recommendations above for specific fixes")
    print("🔧 Proceed with systematic fixes based on priority")
    
    # Save results to file
    results = {
        'timestamp': datetime.now().isoformat(),
        'timing_data': timing_data,
        'progress_data': progress_data,
        'analysis_complete': True
    }
    
    with open('diagnostic_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("💾 Results saved to diagnostic_results.json")

if __name__ == "__main__":
    main() 
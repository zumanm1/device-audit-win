#!/usr/bin/env python3
"""
Simple NetAuditPro Monitor
Monitors audit progress without browser dependencies
"""

import requests
import time
import json
from datetime import datetime

def monitor_audit(base_url="http://127.0.0.1:5011", duration=300):
    """Monitor audit for specified duration (seconds)"""
    start_time = time.time()
    
    print(f"🤖 Starting audit monitoring for {duration} seconds...")
    
    while time.time() - start_time < duration:
        try:
            # Get progress
            response = requests.get(f"{base_url}/api/progress", timeout=5)
            if response.status_code == 200:
                data = response.json()
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Progress: {data.get('percent_complete', 0):.1f}% "
                      f"({data.get('completed_devices', 0)}/{data.get('total_devices', 0)}) "
                      f"Status: {data.get('status', 'Unknown')}")
                
                if data.get('status') == 'Completed':
                    print("🎉 Audit completed!")
                    break
            else:
                print(f"❌ API error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            
        time.sleep(5)
        
    print("✅ Monitoring completed")

if __name__ == "__main__":
    monitor_audit()

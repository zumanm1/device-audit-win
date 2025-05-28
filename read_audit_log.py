#!/usr/bin/env python3
"""
Simple script to read and display the last 30 lines of audit.log
"""
import os

LOG_FILE = '/root/za-con/audit.log'
LINES_TO_SHOW = 30

def read_log_file():
    """Read and display the last LINES_TO_SHOW lines of the log file"""
    if not os.path.exists(LOG_FILE):
        print(f"ERROR: {LOG_FILE} does not exist!")
        return False
    
    try:
        # Get file size to decide if we need to read the whole file
        file_size = os.path.getsize(LOG_FILE)
        
        if file_size == 0:
            print(f"WARNING: {LOG_FILE} exists but is empty (0 bytes)")
            return True
            
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            print(f"WARNING: {LOG_FILE} exists but contains no lines")
            return True
        
        print(f"\n=== Last {min(LINES_TO_SHOW, len(lines))} lines of {LOG_FILE} ===")
        print(f"Total lines in log: {len(lines)}")
        
        for line in lines[-LINES_TO_SHOW:]:
            print(line.rstrip())
        
        print("=== End of log file ===\n")
        return True
        
    except Exception as e:
        print(f"ERROR reading {LOG_FILE}: {str(e)}")
        return False

if __name__ == "__main__":
    read_log_file()

#!/usr/bin/env python3

# This script removes duplicate and unmatched tags in the HTML_CAPTURED_CONFIGS_TEMPLATE

file_path = '/root/za-con/rr3-router.py'

# Lines to remove (1-based indexing)
start_line = 5162
end_line = 5164

with open(file_path, 'r') as f:
    lines = f.readlines()

# Convert to 0-based indexing
start_idx = start_line - 1
end_idx = end_line - 1

# Ensure indices are valid
if start_idx < len(lines) and end_idx < len(lines):
    # Save the removed lines for logging
    removed_lines = [lines[i].strip() for i in range(start_idx, end_idx + 1)]
    
    # Remove the specified lines by creating a new list excluding them
    new_lines = lines[:start_idx] + lines[end_idx + 1:]
    
    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Successfully removed lines {start_line}-{end_line}:")
    for i, line in enumerate(removed_lines):
        print(f"  Line {start_line + i}: {line}")
    
else:
    print(f"Error: File has {len(lines)} lines, but we need to access lines {start_line}-{end_line}")

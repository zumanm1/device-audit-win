#!/usr/bin/env python3

# This script fixes a missing parenthesis in the view_config function
# in rr3-router.py

file_path = '/root/za-con/rr3-router.py'
line_number_to_fix = 6135  # 1-based index

with open(file_path, 'r') as f:
    lines = f.readlines()

# Adjust to 0-based index
index_to_fix = line_number_to_fix - 1

if 0 <= index_to_fix < len(lines):
    original_line = lines[index_to_fix]
    if original_line.strip().endswith("APP_CONFIG.get('PORT', 5007)"):
        lines[index_to_fix] = original_line.rstrip() + ')\n'
        with open(file_path, 'w') as f:
            f.writelines(lines)
        print(f"Successfully fixed missing parenthesis on line {line_number_to_fix} in {file_path}")
    else:
        print(f"Error: Line {line_number_to_fix} does not contain the expected content to fix. Content: {original_line.strip()}")
else:
    print(f"Error: Line number {line_number_to_fix} is out of range for file {file_path} with {len(lines)} lines.")

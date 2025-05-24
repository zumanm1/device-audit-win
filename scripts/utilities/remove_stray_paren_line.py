#!/usr/bin/env python3

# This script removes a specific line containing a stray parenthesis
# in rr3-router.py

file_path = '/root/za-con/rr3-router.py'
line_to_remove = 6136  # 1-based index

with open(file_path, 'r') as f:
    lines = f.readlines()

# Adjust to 0-based index
index_to_remove = line_to_remove - 1

if 0 <= index_to_remove < len(lines):
    # Check if the line is indeed just a ')' for safety, though we'll remove it regardless
    if lines[index_to_remove].strip() == ')':
        print(f"Removing line {line_to_remove} which contains: {lines[index_to_remove].strip()}")
    else:
        print(f"Warning: Line {line_to_remove} content ('{lines[index_to_remove].strip()}') is not just ')', but removing it anyway as instructed.")
    
    del lines[index_to_remove]
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Successfully removed line {line_to_remove} from {file_path}")
else:
    print(f"Error: Line number {line_to_remove} is out of range for file {file_path} with {len(lines)} lines.")

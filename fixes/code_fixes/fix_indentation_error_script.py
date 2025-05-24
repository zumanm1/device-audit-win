#!/usr/bin/env python3

# This script removes a block of extraneous HTML that causes an IndentationError
# in rr3-router.py

file_path = '/root/za-con/rr3-router.py'
lines_to_remove_start = 5162  # 1-based index
lines_to_remove_end = 5169    # 1-based index

with open(file_path, 'r') as f:
    lines = f.readlines()

# Adjust to 0-based index for list slicing
start_index = lines_to_remove_start - 1
end_index = lines_to_remove_end - 1

# Ensure indices are valid
if 0 <= start_index < len(lines) and 0 <= end_index < len(lines) and start_index <= end_index:
    # Remove the lines by concatenating the parts of the list before and after the block
    corrected_lines = lines[:start_index] + lines[end_index+1:]
    
    with open(file_path, 'w') as f:
        f.writelines(corrected_lines)
    print(f"Successfully removed lines {lines_to_remove_start}-{lines_to_remove_end} from {file_path}")
else:
    print(f"Error: Line range {lines_to_remove_start}-{lines_to_remove_end} is invalid for file {file_path} with {len(lines)} lines.")

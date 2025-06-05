#!/usr/bin/env python3

# This script applies a minimal fix to the JSON serialization error in the captured_configs route
# It only modifies the sorting key and does not touch any HTML templates

import re

# Read the original file
with open('/root/za-con/rr3-router.py', 'r') as f:
    content = f.readlines()

# Identify the line where the sorting is happening
target_line = None
for i, line in enumerate(content):
    if "key=lambda x: x['last_modified']" in line:
        target_line = i
        break

# If we found the line, replace 'last_modified' with 'last_modified_str'
if target_line is not None:
    content[target_line] = content[target_line].replace("x['last_modified']", "x['last_modified_str']")
    print(f"Found and fixed sorting key on line {target_line + 1}")
else:
    # If the line has already been fixed, let's check if we need to add the 'last_modified_str' field
    for i, line in enumerate(content):
        if "'last_modified': " in line and "last_modified_str" not in line:
            # Find the closing bracket of the dictionary
            if "}" in line:
                # Insert the 'last_modified_str' field before the closing bracket
                closing_index = line.rfind("}")
                content[i] = line[:closing_index] + ", 'last_modified_str': last_modified.strftime('%Y-%m-%d %H:%M:%S')" + line[closing_index:]
                print(f"Added 'last_modified_str' field on line {i + 1}")
                break

# Write the modified content back to the file
with open('/root/za-con/rr3-router.py', 'w') as f:
    f.writelines(content)

print("Fix applied successfully.")

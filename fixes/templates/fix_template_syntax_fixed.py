#!/usr/bin/env python3

# This script fixes template syntax errors in HTML_CAPTURED_CONFIGS_TEMPLATE
# 1. Removes the extra {% endif %} at line 5161
# 2. Adds the missing {% endblock %} tag

file_path = '/root/za-con/rr3-router.py'

# Approximate line numbers for the issues
extra_endif_line = 5161
missing_endblock_position = 5162  # After the last </div>

with open(file_path, 'r') as f:
    lines = f.readlines()

# Verify the extra endif exists
if extra_endif_line - 1 < len(lines) and '{% endif %}' in lines[extra_endif_line - 1]:
    # Remove the extra endif line
    del lines[extra_endif_line - 1]
    print(f"Removed extra endif tag from line {extra_endif_line}")
else:
    print(f"Warning: Expected extra endif tag at line {extra_endif_line} not found. File may have changed.")

# Add the missing endblock
# Calculate the position after deletion (need to account for the removed line)
adjusted_position = missing_endblock_position - 2  # -1 for 0-based index, -1 for removed line
if adjusted_position < len(lines):
    # Add {% endblock %} after the last </div>
    lines.insert(adjusted_position + 1, "{% endblock %}\n")
    print(f"Added missing endblock tag after line {missing_endblock_position - 1}")
else:
    print(f"Warning: Position {missing_endblock_position} is out of range. File may have changed.")

with open(file_path, 'w') as f:
    f.writelines(lines)

print("Template syntax errors fixed in HTML_CAPTURED_CONFIGS_TEMPLATE.")

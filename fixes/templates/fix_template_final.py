#!/usr/bin/env python3

# This script removes the extra {% endif %} and </div> from HTML_CAPTURED_CONFIGS_TEMPLATE

file_path = '/root/za-con/rr3-router.py'

# Lines to remove (1-based)
line_extra_endif = 5162
line_extra_div = 5163

with open(file_path, 'r') as f:
    lines = f.readlines()

# Check if we have enough lines
if len(lines) >= max(line_extra_endif, line_extra_div):
    # Convert to 0-based indices
    idx_extra_endif = line_extra_endif - 1
    idx_extra_div = line_extra_div - 1
    
    # Verify line content for safety
    endif_found = '{% endif %}' in lines[idx_extra_endif]
    div_found = '</div>' in lines[idx_extra_div]
    
    changes_made = False
    
    # Remove the extra endif if found
    if endif_found:
        del lines[idx_extra_endif]
        print(f"Removed extra {% endif %} at line {line_extra_endif}")
        changes_made = True
        # Adjust index for the div since we removed a line
        idx_extra_div -= 1
    else:
        print(f"Warning: Expected {% endif %} not found at line {line_extra_endif}")
    
    # Remove the extra </div> if found (use the adjusted index if we removed the endif)
    if idx_extra_div < len(lines) and '</div>' in lines[idx_extra_div]:
        del lines[idx_extra_div]
        print(f"Removed extra </div> at line {line_extra_div}")
        changes_made = True
    else:
        print(f"Warning: Expected </div> not found at line {line_extra_div}")
    
    if changes_made:
        with open(file_path, 'w') as f:
            f.writelines(lines)
        print("Successfully fixed template syntax errors.")
    else:
        print("No changes were made to the template.")
else:
    print(f"Error: File only has {len(lines)} lines, but we need to access line {max(line_extra_endif, line_extra_div)}")

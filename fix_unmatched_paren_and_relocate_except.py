#!/usr/bin/env python3

# This script fixes an unmatched parenthesis and relocates an orphaned except block
# in rr3-router.py

file_path = '/root/za-con/rr3-router.py'

# Line numbers are 1-based and refer to the state of the file
# that produced the "unmatched ')'" error at line 6273.
line_view_config_return_end = 6135
line_stray_paren = 6272
line_orphaned_except_start = 6273
line_orphaned_except_end = 6274

# Convert to 0-based indices for list operations
idx_view_config_return_end = line_view_config_return_end - 1
idx_stray_paren = line_stray_paren - 1
idx_orphaned_except_start = line_orphaned_except_start - 1
idx_orphaned_except_end = line_orphaned_except_end - 1

try:
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Validate line numbers against file length
    if not (0 <= idx_view_config_return_end < len(lines) and \
            0 <= idx_stray_paren < len(lines) and \
            0 <= idx_orphaned_except_start < len(lines) and \
            0 <= idx_orphaned_except_end < len(lines)):
        print(f"Error: One or more line indices are out of bounds for file {file_path} with {len(lines)} lines.")
        print(f"Indices: view_config_return_end={idx_view_config_return_end}, stray_paren={idx_stray_paren}, except_start={idx_orphaned_except_start}, except_end={idx_orphaned_except_end}")
        exit(1)

    # Part 1: Up to and including the return statement of view_config
    part1_up_to_view_config_return = lines[0 : idx_view_config_return_end + 1]

    # Part 2: The orphaned except block to be moved
    # Ensure the slice indices are correct and do not overlap incorrectly
    except_block_to_move = lines[idx_orphaned_except_start : idx_orphaned_except_end + 1]

    # Part 3: The download routes (content between view_config's return and the stray parenthesis)
    download_routes_part = lines[idx_view_config_return_end + 1 : idx_stray_paren]

    # Part 4: The rest of the file after the original location of the orphaned except block
    part_after_old_except_location = lines[idx_orphaned_except_end + 1 :]

    # Assemble the new content
    new_lines = (part1_up_to_view_config_return +
                 except_block_to_move +
                 download_routes_part +
                 part_after_old_except_location)

    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Successfully restructured {file_path}:")
    print(f"  - Relocated except block (original lines {line_orphaned_except_start}-{line_orphaned_except_end}) after line {line_view_config_return_end}.")
    print(f"  - Removed stray parenthesis (original line {line_stray_paren}).")

except FileNotFoundError:
    print(f"Error: File {file_path} not found.")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

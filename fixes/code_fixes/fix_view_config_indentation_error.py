#!/usr/bin/env python3

# This script fixes an IndentationError in view_config by adding
# a proper except block content in rr3-router.py

file_path = '/root/za-con/rr3-router.py'
# Line number where 'except Exception as e:' is located (1-based)
except_line_number = 6136

# Content to insert, properly indented (8 spaces for content of an except block at 4-space indent)
content_to_insert = [
    '        app.logger.error(f"Error in view_config for {audit_date}/{filename}: {str(e)}")\n',
    '        return f"Error viewing configuration file: {filename}. Details: {str(e)}", 500\n'
]

try:
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Convert to 0-based index for list operations
    insert_after_index = except_line_number - 1

    if not (0 <= insert_after_index < len(lines)):
        print(f"Error: Line number {except_line_number} (index {insert_after_index}) is out of range for file {file_path} with {len(lines)} lines.")
        exit(1)

    # Verify the line is indeed the except statement we expect
    if lines[insert_after_index].strip() != "except Exception as e:":
        print(f"Error: Line {except_line_number} is not 'except Exception as e:'. Found: '{lines[insert_after_index].strip()}'")
        exit(1)

    # Verify the next line is the one causing the IndentationError
    if insert_after_index + 1 < len(lines) and not lines[insert_after_index + 1].strip().startswith("@app.route('/download_config/"):
        print(f"Warning: The line after 'except Exception as e:' is not the expected '@app.route(\'/download_config/\')'. Found: '{lines[insert_after_index + 1].strip()}'")
        # Proceeding anyway as the IndentationError is the primary concern

    # Insert the new content
    # The new lines go *after* the 'except Exception as e:' line,
    # so they will be at insert_after_index + 1, insert_after_index + 2, etc.
    for i, line_content in enumerate(content_to_insert):
        lines.insert(insert_after_index + 1 + i, line_content)

    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print(f"Successfully added error handling to 'except' block at line {except_line_number} in {file_path}.")

except FileNotFoundError:
    print(f"Error: File {file_path} not found.")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

#!/usr/bin/env python3

import os
import re

def fix_indentation(file_path):
    """
    Fix the indentation error in the HTML template.
    """
    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find and fix the problematic line
    fixed_lines = []
    for line in lines:
        # Check if this is the problematic line with improper indentation
        if '</tr>' in line and line.strip() == '</tr>':
            # Replace with properly indented version
            fixed_lines.append('                                            </tr>\n')
        else:
            fixed_lines.append(line)
    
    # Write the fixed content back to the file
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print("Fixed indentation error in HTML template.")

if __name__ == "__main__":
    fix_indentation('/root/za-con/rr3-router.py')

#!/usr/bin/env python3
"""
Fix duplicate command log routes in the enhanced application
"""

def fix_duplicate_routes():
    with open('rr4-router-complete-enhanced-v2.py', 'r') as f:
        lines = f.readlines()
    
    output_lines = []
    i = 0
    first_command_logs_found = False
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a command logs route
        if "@app.route('/command_logs')" in line:
            if not first_command_logs_found:
                # Keep the first occurrence
                first_command_logs_found = True
                output_lines.append(line)
            else:
                # Skip this duplicate section until we find "if __name__"
                while i < len(lines) and "if __name__ ==" not in lines[i]:
                    i += 1
                # Back up one line so the loop increment works
                i -= 1
        else:
            output_lines.append(line)
        
        i += 1
    
    # Write the fixed file
    with open('rr4-router-complete-enhanced-v2.py', 'w') as f:
        f.writelines(output_lines)
    
    print("✅ Fixed duplicate command log routes")

if __name__ == "__main__":
    fix_duplicate_routes() 
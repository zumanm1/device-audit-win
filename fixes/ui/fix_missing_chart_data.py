#!/usr/bin/env python3

# This script adds a default chart_data parameter to the render_template_string call
# in the captured_configs function to prevent the JSON serialization error

file_path = '/root/za-con/rr3-router.py'
line_to_modify = 6090  # Start of the render_template_string call

with open(file_path, 'r') as f:
    lines = f.readlines()

# Look for the render_template_string call in the captured_configs function
render_call_found = False
chart_data_found = False
render_call_end_line = 0

for i in range(line_to_modify - 5, line_to_modify + 10):
    if i < len(lines):
        if 'render_template_string' in lines[i]:
            render_call_found = True
        if 'chart_data' in lines[i]:
            chart_data_found = True
        if render_call_found and ')' in lines[i]:
            render_call_end_line = i
            break

if render_call_found and not chart_data_found and render_call_end_line > 0:
    # Find the last parameter line before the closing parenthesis
    last_param_line = render_call_end_line - 1
    
    # Add the chart_data parameter
    indentation = lines[last_param_line].split('=')[0]
    new_line = f"{indentation}chart_data={{}},\n"
    
    # Insert the new parameter before the closing parenthesis
    lines.insert(render_call_end_line, new_line)
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print(f"Added chart_data={{}} parameter to render_template_string call in captured_configs function.")
else:
    if not render_call_found:
        print("Error: render_template_string call not found at expected line.")
    elif chart_data_found:
        print("chart_data parameter is already present in the render_template_string call.")
    else:
        print("Error: Could not locate end of render_template_string call.")

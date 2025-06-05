#!/usr/bin/env python3

# This script properly handles the chart_data parameter in the captured_configs function
# to ensure it has the correct structure for JSON serialization

file_path = '/root/za-con/rr3-router.py'
captured_configs_func_start = 6034  # Approximate line where captured_configs function starts
captured_configs_render_line = 6090  # Approximate line where render_template_string is called

with open(file_path, 'r') as f:
    lines = f.readlines()

# Find the exact location of the render_template_string call
render_line_idx = None
for i in range(captured_configs_render_line - 5, captured_configs_render_line + 5):
    if i < len(lines) and 'render_template_string' in lines[i]:
        render_line_idx = i
        break

if render_line_idx is not None:
    # Check if we've already added chart_data
    chart_data_exists = False
    chart_data_line = None
    
    # Look at the parameters in the render_template_string call
    for i in range(render_line_idx, render_line_idx + 10):
        if i < len(lines) and 'chart_data' in lines[i]:
            chart_data_exists = True
            chart_data_line = i
            break
    
    # First, add chart_data initialization before render_template_string
    # Looking for the line before render_template_string to add our initialization
    insert_before_idx = render_line_idx
    
    # Create proper chart_data structure as in the index function
    chart_data_init = [
        "    # Initialize chart_data with default values to avoid JSON serialization issues\n",
        "    chart_data = {\"labels\": [\"No Router Configs\"], \"values\": [1], \"colors\": [\"#D3D3D3\"]}\n",
        "    \n"
    ]
    
    # Insert the chart_data initialization
    for i, line in enumerate(chart_data_init):
        lines.insert(insert_before_idx + i, line)
    
    # Adjust indices due to inserted lines
    if chart_data_line is not None:
        chart_data_line += len(chart_data_init)
    render_line_idx += len(chart_data_init)
    
    # Now update or add the chart_data parameter to render_template_string
    if chart_data_exists and chart_data_line is not None:
        # Update existing chart_data parameter
        indentation = lines[chart_data_line].split('chart_data')[0]
        lines[chart_data_line] = f"{indentation}chart_data=chart_data,\n"
    else:
        # Find the last parameter line before the closing parenthesis
        last_param_line = render_line_idx
        
        for i in range(render_line_idx, render_line_idx + 10):
            if i < len(lines) and (')' in lines[i] or i == len(lines) - 1):
                last_param_line = i - 1
                break
        
        # Add the chart_data parameter
        indentation = " " * 27  # Matching other parameters' indentation
        new_line = f"{indentation}chart_data=chart_data,\n"
        
        # Insert the new parameter before the closing parenthesis
        lines.insert(last_param_line + 1, new_line)
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print("Successfully added proper chart_data structure to captured_configs function.")
else:
    print("Error: render_template_string call not found at expected location in captured_configs function.")

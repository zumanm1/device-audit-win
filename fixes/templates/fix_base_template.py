#!/usr/bin/env python3

# This script modifies the base template to safely handle undefined variables
# and adds default parameters to the captured_configs function

file_path = '/root/za-con/rr3-router.py'

with open(file_path, 'r') as f:
    lines = f.readlines()

# Find the HTML_BASE_LAYOUT definition
base_layout_start = None
for i, line in enumerate(lines):
    if "HTML_BASE_LAYOUT = r" in line:
        base_layout_start = i
        break

if base_layout_start is None:
    print("Error: Could not find HTML_BASE_LAYOUT definition.")
    exit(1)

# Find the problematic chart_data handling in the base layout
chart_data_line = None
for i in range(base_layout_start, len(lines)):
    if "chart_data|tojson|safe" in lines[i]:
        chart_data_line = i
        break

if chart_data_line is None:
    print("Error: Could not find chart_data|tojson|safe in HTML_BASE_LAYOUT.")
    exit(1)

# Modify the chart_data handling to use a default empty object if undefined
original_line = lines[chart_data_line]
modified_line = original_line.replace(
    "const chartDataStr = '{{ chart_data|tojson|safe }}';",
    "const chartDataStr = '{{ chart_data|default({})|tojson|safe }}';")
lines[chart_data_line] = modified_line

print(f"Modified chart_data handling in HTML_BASE_LAYOUT at line {chart_data_line + 1}.")

# Find the captured_configs function
captured_configs_start = None
render_line = None
for i, line in enumerate(lines):
    if "def captured_configs():" in line:
        captured_configs_start = i
    elif captured_configs_start and "render_template_string" in line:
        render_line = i
        break

if captured_configs_start is None or render_line is None:
    print("Error: Could not find captured_configs function or render_template_string call.")
    exit(1)

# Ensure chart_data is properly initialized and passed to the template
# Check if chart_data is already initialized
chart_data_init = False
for i in range(captured_configs_start, render_line):
    if "chart_data =" in lines[i]:
        chart_data_init = True
        break

# If chart_data is not initialized, add it before the render_template_string call
if not chart_data_init:
    # Add chart_data initialization before render_template_string
    chart_data_code = [
        "    # Initialize chart_data with default values for JSON serialization\n",
        "    chart_data = {\"labels\": [\"No Router Configs\"], \"values\": [1], \"colors\": [\"#D3D3D3\"]}\n",
        "\n"
    ]
    
    for i, line in enumerate(chart_data_code):
        lines.insert(render_line - 1 + i, line)
    
    # Adjust render_line for subsequent operations
    render_line += len(chart_data_code)
    
    print(f"Added chart_data initialization before render_template_string.")

# Now check if chart_data is passed to the template
chart_data_param = False
for i in range(render_line, render_line + 10):
    if i < len(lines) and "chart_data=" in lines[i]:
        chart_data_param = True
        break

# If chart_data is not passed to the template, add it
if not chart_data_param:
    # Find the last parameter before the closing parenthesis
    param_end = None
    for i in range(render_line, len(lines)):
        if "))" in lines[i]:
            param_end = i
            break
    
    if param_end is not None:
        # Add chart_data parameter before the closing parenthesis
        indent = lines[param_end].split("))")[0]
        chart_data_param_line = f"{indent}chart_data=chart_data,\n"
        lines.insert(param_end, chart_data_param_line)
        print(f"Added chart_data parameter to render_template_string call.")
    else:
        print("Warning: Could not find end of render_template_string parameters.")

# Save the modified file
with open(file_path, 'w') as f:
    f.writelines(lines)

print("Successfully updated the file to safely handle chart_data in templates.")

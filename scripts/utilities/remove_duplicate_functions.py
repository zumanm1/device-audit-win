#!/usr/bin/env python3

# This script removes duplicate function definitions in rr3-router.py

file_path = '/root/za-con/rr3-router.py'

# Approximate line ranges for the duplicate functions (1-based indexing)
# These will be adjusted by the script based on actual function detection
duplicate_download_config_start = 6206
duplicate_download_config_end = 6232

duplicate_download_all_configs_start = 6234
duplicate_download_all_configs_end = 6273

with open(file_path, 'r') as f:
    lines = f.readlines()

# Find actual start of "def download_config" (second instance)
actual_download_config_start = None
for i in range(duplicate_download_config_start - 20, duplicate_download_config_start + 20):
    if i < len(lines) and lines[i].strip().startswith("def download_config"):
        actual_download_config_start = i
        break

# Find actual start of "def download_all_configs" (second instance)
actual_download_all_configs_start = None
for i in range(duplicate_download_all_configs_start - 20, duplicate_download_all_configs_start + 20):
    if i < len(lines) and lines[i].strip().startswith("def download_all_configs"):
        actual_download_all_configs_start = i
        break

if actual_download_config_start is None or actual_download_all_configs_start is None:
    print("Error: Couldn't find one or both duplicate function definitions.")
    exit(1)

# Find the end of the first duplicate function (download_config)
actual_download_config_end = actual_download_config_start
for i in range(actual_download_config_start + 1, len(lines)):
    if lines[i].strip().startswith("@app.route") or lines[i].strip().startswith("def "):
        actual_download_config_end = i - 1
        break

# Find the end of the second duplicate function (download_all_configs)
actual_download_all_configs_end = actual_download_all_configs_start
for i in range(actual_download_all_configs_start + 1, len(lines)):
    if lines[i].strip().startswith("@app.route") or lines[i].strip().startswith("def "):
        actual_download_all_configs_end = i - 1
        break
    elif i == len(lines) - 1:  # Handle case where function is at end of file
        actual_download_all_configs_end = i
        break

# Remove the duplicate functions by reconstructing the file
new_lines = (
    lines[:actual_download_config_start] +  # Content before first duplicate
    lines[actual_download_all_configs_end + 1:]  # Content after second duplicate
)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print(f"Successfully removed duplicate functions:")
print(f"  - download_config (lines {actual_download_config_start+1}-{actual_download_config_end+1})")
print(f"  - download_all_configs (lines {actual_download_all_configs_start+1}-{actual_download_all_configs_end+1})")

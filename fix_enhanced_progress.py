#!/usr/bin/env python3

# This script fixes the get_audit_progress endpoint to include enhanced progress data
# that the UI needs to properly display the Enhanced Progress Tracking section

file_path = '/root/za-con/rr3-router.py'

with open(file_path, 'r') as f:
    lines = f.readlines()

# Search for the get_audit_progress endpoint implementation
get_progress_start = None
get_progress_end = None

for i, line in enumerate(lines):
    if "def get_audit_progress():" in line:
        get_progress_start = i
    elif get_progress_start is not None and "@app.route" in line:
        get_progress_end = i
        break

if get_progress_start is None:
    print("Error: Could not find get_audit_progress function.")
    exit(1)

if get_progress_end is None:
    # If we couldn't find the next route, look for the next function definition
    for i in range(get_progress_start + 1, len(lines)):
        if "def " in lines[i] and "@" in lines[i-1]:
            get_progress_end = i - 1
            break

if get_progress_end is None:
    print("Error: Could not determine where get_audit_progress function ends.")
    exit(1)

# Define the improved get_audit_progress function
improved_get_progress = [
    "def get_audit_progress():\n",
    "    \"\"\"API endpoint to retrieve the current audit progress data\"\"\"\n",
    "    global AUDIT_PROGRESS, last_run_summary_data, chart_data, audit_paused\n",
    "    \n",
    "    try:\n",
    "        # Calculate enhanced progress data (similar to audit_progress_data function)\n",
    "        progress_percent = 0\n",
    "        if AUDIT_PROGRESS.get('total_devices', 0) > 0:\n",
    "            progress_percent = (AUDIT_PROGRESS.get('completed_devices', 0) / AUDIT_PROGRESS.get('total_devices', 0)) * 100\n",
    "        \n",
    "        enhanced_progress = {\n",
    "            'percentage': progress_percent,\n",
    "            'status': AUDIT_PROGRESS.get('status', 'idle'),\n",
    "            'current_device': AUDIT_PROGRESS.get('current_device'),\n",
    "            'total_devices': AUDIT_PROGRESS.get('total_devices', 0),\n",
    "            'completed_devices': AUDIT_PROGRESS.get('completed_devices', 0),\n",
    "            'start_time': AUDIT_PROGRESS.get('start_time'),\n",
    "            'end_time': AUDIT_PROGRESS.get('end_time'),\n",
    "            'current_device_start_time': AUDIT_PROGRESS.get('current_device_start_time'),\n",
    "            'estimated_completion_time': AUDIT_PROGRESS.get('estimated_completion_time'),\n",
    "            'status_counts': {\n",
    "                'success': AUDIT_PROGRESS.get('overall_success_count', 0),\n",
    "                'warning': AUDIT_PROGRESS.get('overall_warning_count', 0),\n",
    "                'failure': AUDIT_PROGRESS.get('overall_failure_count', 0),\n",
    "                'in_progress': 1 if AUDIT_PROGRESS.get('status') == 'running' else 0\n",
    "            },\n",
    "            'device_statuses': AUDIT_PROGRESS.get('device_statuses', {})\n",
    "        }\n",
    "        \n",
    "        # Create response data with both raw progress and enhanced progress\n",
    "        serializable_failures = {k: str(v) if v is not None else None \n",
    "                              for k, v in current_run_failures.items()} if 'current_run_failures' in globals() else {}\n",
    "        \n",
    "        data_to_send = {\n",
    "            'progress': prepare_progress_for_json(AUDIT_PROGRESS),  # Legacy progress format\n",
    "            'enhanced_progress': enhanced_progress,  # New enhanced progress format\n",
    "            'overall_audit_status': audit_status, \n",
    "            'last_run_summary': last_run_summary_data, \n",
    "            'current_run_failures': serializable_failures, \n",
    "            'chart_data': chart_data if 'chart_data' in globals() else {}, \n",
    "            'audit_paused': audit_paused\n",
    "        }\n",
    "        \n",
    "        return jsonify(data_to_send)\n",
    "    except Exception as e:\n",
    "        import traceback\n",
    "        tb = traceback.format_exc()\n",
    "        print(f\"[ERROR] Exception in /get_audit_progress: {e}\\n{tb}\")\n",
    "        return jsonify({'error': str(e)}), 500\n"
]

# Replace the old function with the new one
lines[get_progress_start+1:get_progress_end] = improved_get_progress

with open(file_path, 'w') as f:
    f.writelines(lines)

print(f"Successfully updated get_audit_progress function to include enhanced progress data.")

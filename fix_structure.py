#!/usr/bin/env python3
"""
Fix structural issues in NetAuditPro v3
Separate HTML template from ensure_directories function
"""

import re

def fix_structure():
    """Fix the ensure_directories function structure"""
    
    print("🔧 Fixing code structure...")
    
    with open('rr4-router-complete-enhanced-v3.py', 'r') as f:
        content = f.read()
    
    # Find the ensure_directories function
    lines = content.split('\n')
    
    # Locate the problematic section
    ensure_dir_start = None
    html_start = None
    
    for i, line in enumerate(lines):
        if 'def ensure_directories():' in line:
            ensure_dir_start = i
        elif 'HTML_BASE_LAYOUT = r"""' in line and ensure_dir_start:
            html_start = i
            break
    
    if ensure_dir_start and html_start:
        print(f"📍 Found ensure_directories at line {ensure_dir_start + 1}")
        print(f"📍 Found HTML_BASE_LAYOUT at line {html_start + 1}")
        
        # Extract the actual ensure_directories function (should be short)
        function_end = html_start - 1
        
        # Find where the function actually ends (before HTML template)
        for i in range(ensure_dir_start + 1, html_start):
            line = lines[i].strip()
            if not line or (not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#')):
                if not line.startswith('@') and not line.startswith('def'):
                    function_end = i - 1
                    break
        
        print(f"📐 Actual function ends at line {function_end + 1}")
        
        # Fix the structure by adding proper separation
        fixed_lines = []
        
        # Add lines up to the end of ensure_directories
        for i in range(function_end + 1):
            fixed_lines.append(lines[i])
        
        # Add proper separation comment
        fixed_lines.append("")
        fixed_lines.append("# ====================================================================")
        fixed_lines.append("# PHASE 5: ENHANCED HTML TEMPLATES WITH ACCESSIBILITY")
        fixed_lines.append("# ====================================================================")
        fixed_lines.append("")
        
        # Add the rest of the file starting from HTML template
        for i in range(html_start, len(lines)):
            fixed_lines.append(lines[i])
        
        # Write the fixed content
        with open('rr4-router-complete-enhanced-v3.py', 'w') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"✅ Fixed structure - ensure_directories now {function_end - ensure_dir_start + 1} lines")
        return True
    
    else:
        print("❌ Could not locate the problematic section")
        return False

if __name__ == "__main__":
    if fix_structure():
        print("\n🧪 Testing syntax after fix...")
        import subprocess
        result = subprocess.run(['python3', '-m', 'py_compile', 'rr4-router-complete-enhanced-v3.py'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Syntax check passed")
        else:
            print(f"❌ Syntax error: {result.stderr}")
    else:
        print("❌ Fix failed") 
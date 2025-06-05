#!/usr/bin/env python3
"""
Fix bare except blocks in NetAuditPro v3
Replace bare except: with specific exception handling
"""

import re

def fix_bare_except():
    """Fix bare except blocks by replacing with appropriate exceptions"""
    
    print("🔧 Fixing bare except blocks...")
    
    with open('rr4-router-complete-enhanced-v3.py', 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    changes_made = 0
    
    for i, line in enumerate(lines):
        # Check for bare except blocks
        if re.match(r'^(\s*)except\s*:\s*$', line):
            indent = re.match(r'^(\s*)', line).group(1)
            
            # Look at the context to determine appropriate exception
            context_lines = lines[max(0, i-5):i+5]
            context = ' '.join(context_lines).lower()
            
            # Determine appropriate exception based on context
            if any(keyword in context for keyword in ['close', 'resource', 'file', 'connection']):
                replacement = f"{indent}except Exception:"
                print(f"  Line {i+1}: Replaced bare except with Exception (resource cleanup)")
            elif any(keyword in context for keyword in ['import', 'module', 'attribute']):
                replacement = f"{indent}except (ImportError, AttributeError):"
                print(f"  Line {i+1}: Replaced bare except with ImportError/AttributeError")
            elif any(keyword in context for keyword in ['key', 'index', 'dict', 'list']):
                replacement = f"{indent}except (KeyError, IndexError, TypeError):"
                print(f"  Line {i+1}: Replaced bare except with KeyError/IndexError/TypeError")
            elif any(keyword in context for keyword in ['network', 'connection', 'socket', 'timeout']):
                replacement = f"{indent}except (ConnectionError, TimeoutError, OSError):"
                print(f"  Line {i+1}: Replaced bare except with network exceptions")
            else:
                replacement = f"{indent}except Exception:"
                print(f"  Line {i+1}: Replaced bare except with generic Exception")
            
            fixed_lines.append(replacement)
            changes_made += 1
        else:
            fixed_lines.append(line)
    
    if changes_made > 0:
        # Write the fixed content
        with open('rr4-router-complete-enhanced-v3.py', 'w') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"\n✅ Fixed {changes_made} bare except blocks")
        return True
    else:
        print("✅ No bare except blocks found")
        return False

if __name__ == "__main__":
    if fix_bare_except():
        print("\n🧪 Testing syntax after fix...")
        import subprocess
        result = subprocess.run(['python3', '-m', 'py_compile', 'rr4-router-complete-enhanced-v3.py'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Syntax check passed")
        else:
            print(f"❌ Syntax error: {result.stderr}")
    else:
        print("✅ No changes needed") 
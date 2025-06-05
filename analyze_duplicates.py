#!/usr/bin/env python3
"""
Code Analysis Script for NetAuditPro
Identifies duplicate functions, routes, and other potential issues
"""

import re
from collections import Counter

def analyze_codebase(filename):
    """Analyze the codebase for potential issues"""
    
    with open(filename, 'r') as f:
        content = f.read()
    
    print("="*70)
    print("🔍 NETAUDITPRO CODEBASE ANALYSIS")
    print("="*70)
    
    # 1. Find duplicate function definitions
    functions = re.findall(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content, re.MULTILINE)
    duplicates = {func: count for func, count in Counter(functions).items() if count > 1}
    
    print("\n📋 DUPLICATE FUNCTIONS:")
    if duplicates:
        for func, count in duplicates.items():
            print(f"  ❌ {func}: {count} definitions")
            # Find line numbers for each duplicate
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if re.match(f'^def\\s+{func}\\s*\\(', line):
                    print(f"     Line {i}: {line.strip()}")
    else:
        print("  ✅ No duplicate functions found")
    
    # 2. Find duplicate route definitions
    routes = re.findall(r'@app\.route\([\'"]([^\'"]+)[\'"]', content)
    route_duplicates = {route: count for route, count in Counter(routes).items() if count > 1}
    
    print("\n🌐 DUPLICATE ROUTES:")
    if route_duplicates:
        for route, count in route_duplicates.items():
            print(f"  ❌ {route}: {count} definitions")
    else:
        print("  ✅ No duplicate routes found")
    
    # 3. Find potential import issues
    imports = re.findall(r'^from\s+([^\s]+)\s+import\s+(.+)$', content, re.MULTILINE)
    import_counter = Counter()
    for module, items in imports:
        for item in items.split(','):
            item = item.strip()
            import_counter[item] += 1
    
    duplicate_imports = {item: count for item, count in import_counter.items() if count > 1}
    
    print("\n📦 DUPLICATE IMPORTS:")
    if duplicate_imports:
        for item, count in duplicate_imports.items():
            print(f"  ⚠️ {item}: imported {count} times")
    else:
        print("  ✅ No duplicate imports found")
    
    # 4. Find unused variables and potential issues
    print("\n🔧 CODE STRUCTURE ANALYSIS:")
    total_lines = len(content.split('\n'))
    print(f"  📏 Total lines: {total_lines}")
    
    function_count = len(functions)
    print(f"  🔧 Total functions: {function_count}")
    
    route_count = len(routes)
    print(f"  🌐 Total routes: {route_count}")
    
    # 5. Check for common issues
    print("\n⚠️ POTENTIAL ISSUES:")
    
    # Check for very long functions (>100 lines)
    lines = content.split('\n')
    in_function = False
    current_function = ""
    function_start = 0
    long_functions = []
    
    for i, line in enumerate(lines):
        if re.match(r'^def\s+', line):
            if in_function and (i - function_start) > 100:
                long_functions.append((current_function, function_start + 1, i - function_start))
            in_function = True
            current_function = line.strip()
            function_start = i
    
    if long_functions:
        print("  📏 Long functions (>100 lines):")
        for func, start_line, length in long_functions:
            print(f"     Line {start_line}: {func} ({length} lines)")
    else:
        print("  ✅ No excessively long functions found")
    
    return {
        'duplicate_functions': duplicates,
        'duplicate_routes': route_duplicates,
        'duplicate_imports': duplicate_imports,
        'total_lines': total_lines,
        'total_functions': function_count,
        'total_routes': route_count,
        'long_functions': long_functions
    }

if __name__ == "__main__":
    result = analyze_codebase('rr4-router-complete-enhanced-v3.py')
    
    print("\n" + "="*70)
    print("🎯 ANALYSIS COMPLETE")
    print("="*70) 
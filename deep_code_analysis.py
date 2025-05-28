#!/usr/bin/env python3
"""
Deep Code Analysis for NetAuditPro v3
Analyzes code in batches to identify issues and potential improvements
"""

import re
import ast
import os
from collections import defaultdict, Counter

class CodeAnalyzer:
    def __init__(self, filename):
        self.filename = filename
        self.issues = []
        self.suggestions = []
        
    def read_file(self):
        """Read the file and split into manageable chunks"""
        with open(self.filename, 'r', encoding='utf-8') as f:
            self.content = f.read()
        self.lines = self.content.split('\n')
        
    def analyze_imports(self):
        """Analyze import statements for issues"""
        print("🔍 Analyzing imports...")
        
        imports = []
        from_imports = defaultdict(list)
        
        for i, line in enumerate(self.lines, 1):
            line = line.strip()
            if line.startswith('import '):
                imports.append((i, line))
            elif line.startswith('from '):
                match = re.match(r'from\s+([^\s]+)\s+import\s+(.+)', line)
                if match:
                    module, items = match.groups()
                    from_imports[module].extend([item.strip() for item in items.split(',')])
        
        # Check for potential issues
        print(f"  📦 Found {len(imports)} direct imports")
        print(f"  📦 Found {len(from_imports)} from-imports")
        
        # Check for large from imports
        for module, items in from_imports.items():
            if len(items) > 10:
                self.issues.append(f"Large import from {module}: {len(items)} items")
        
        return {'imports': imports, 'from_imports': from_imports}
    
    def analyze_functions(self):
        """Analyze function definitions and complexity"""
        print("🔍 Analyzing functions...")
        
        functions = []
        current_function = None
        function_lines = 0
        
        for i, line in enumerate(self.lines, 1):
            if re.match(r'^\s*def\s+', line):
                if current_function:
                    functions.append({
                        'name': current_function['name'],
                        'start_line': current_function['start_line'],
                        'end_line': i - 1,
                        'length': function_lines,
                        'complexity': self._estimate_complexity(current_function['start_line'], i - 1)
                    })
                
                func_match = re.match(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                if func_match:
                    current_function = {
                        'name': func_match.group(1),
                        'start_line': i
                    }
                    function_lines = 0
            
            if current_function:
                function_lines += 1
        
        # Add last function
        if current_function:
            functions.append({
                'name': current_function['name'],
                'start_line': current_function['start_line'],
                'end_line': len(self.lines),
                'length': function_lines,
                'complexity': self._estimate_complexity(current_function['start_line'], len(self.lines))
            })
        
        # Analyze function metrics
        long_functions = [f for f in functions if f['length'] > 100]
        complex_functions = [f for f in functions if f['complexity'] > 20]
        
        print(f"  🔧 Total functions: {len(functions)}")
        print(f"  ⚠️ Long functions (>100 lines): {len(long_functions)}")
        print(f"  ⚠️ Complex functions (>20 branches/loops): {len(complex_functions)}")
        
        for func in long_functions[:5]:  # Show top 5 longest
            print(f"    📏 {func['name']}: {func['length']} lines (line {func['start_line']})")
        
        return {'functions': functions, 'long_functions': long_functions, 'complex_functions': complex_functions}
    
    def _estimate_complexity(self, start_line, end_line):
        """Estimate cyclomatic complexity by counting control structures"""
        complexity = 1  # Base complexity
        
        for i in range(start_line - 1, min(end_line, len(self.lines))):
            line = self.lines[i].strip()
            
            # Count control structures
            if re.match(r'^\s*(if|elif|for|while|except|with|and|or)\s', line):
                complexity += 1
            
            # Count nested structures (rough estimate)
            if re.match(r'^\s{8,}(if|elif|for|while)', line):
                complexity += 1
        
        return complexity
    
    def analyze_routes(self):
        """Analyze Flask route definitions"""
        print("🔍 Analyzing Flask routes...")
        
        routes = []
        route_methods = defaultdict(list)
        
        for i, line in enumerate(self.lines, 1):
            if '@app.route(' in line:
                # Extract route info
                route_match = re.search(r"@app\.route\(['\"]([^'\"]+)['\"]", line)
                methods_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", line)
                
                if route_match:
                    route_path = route_match.group(1)
                    methods = ['GET']  # Default
                    
                    if methods_match:
                        methods = [m.strip().strip('\'"') for m in methods_match.group(1).split(',')]
                    
                    routes.append({
                        'path': route_path,
                        'methods': methods,
                        'line': i
                    })
                    
                    for method in methods:
                        route_methods[method].append(route_path)
        
        print(f"  🌐 Total routes: {len(routes)}")
        
        for method, paths in route_methods.items():
            print(f"    {method}: {len(paths)} routes")
        
        return {'routes': routes, 'route_methods': route_methods}
    
    def analyze_security(self):
        """Check for potential security issues"""
        print("🔍 Analyzing security patterns...")
        
        security_issues = []
        
        # Check for hardcoded credentials (excluding comments)
        credential_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']'
        ]
        
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith('#'):
                continue
                
            for pattern in credential_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if it's reading from environment
                    if 'os.getenv' not in line and 'app_config.get' not in line:
                        security_issues.append(f"Line {i}: Potential hardcoded credential")
        
        # Check for SQL injection patterns (if any SQL)
        sql_patterns = [
            r'["\'][^"\']*\s*%\s*',  # String formatting in SQL-like context
            r'["\'][^"\']*\s*\+\s*'   # String concatenation in SQL-like context
        ]
        
        for i, line in enumerate(self.lines, 1):
            if any(keyword in line.lower() for keyword in ['select', 'insert', 'update', 'delete']):
                for pattern in sql_patterns:
                    if re.search(pattern, line):
                        security_issues.append(f"Line {i}: Potential SQL injection risk")
        
        print(f"  🔒 Security issues found: {len(security_issues)}")
        for issue in security_issues[:10]:  # Show first 10
            print(f"    ⚠️ {issue}")
        
        return security_issues
    
    def analyze_performance(self):
        """Check for potential performance issues"""
        print("🔍 Analyzing performance patterns...")
        
        performance_issues = []
        
        # Check for inefficient patterns
        inefficient_patterns = [
            (r'for\s+.*\s+in\s+range\(len\(', 'Use enumerate() instead of range(len())'),
            (r'\.append\([^)]*\)\s*$', 'Consider list comprehension for better performance'),
            (r'time\.sleep\(\d+\)', 'Long sleep statements may impact responsiveness')
        ]
        
        for i, line in enumerate(self.lines, 1):
            for pattern, suggestion in inefficient_patterns:
                if re.search(pattern, line):
                    performance_issues.append(f"Line {i}: {suggestion}")
        
        print(f"  ⚡ Performance suggestions: {len(performance_issues)}")
        for issue in performance_issues[:5]:  # Show first 5
            print(f"    💡 {issue}")
        
        return performance_issues
    
    def analyze_error_handling(self):
        """Check error handling patterns"""
        print("🔍 Analyzing error handling...")
        
        try_blocks = 0
        bare_except = 0
        
        for i, line in enumerate(self.lines, 1):
            if re.match(r'^\s*try\s*:', line):
                try_blocks += 1
            elif re.match(r'^\s*except\s*:', line):
                bare_except += 1
        
        except_blocks = len(re.findall(r'except\s+\w+', self.content))
        
        print(f"  🛡️ Try blocks: {try_blocks}")
        print(f"  🛡️ Specific except blocks: {except_blocks}")
        print(f"  ⚠️ Bare except blocks: {bare_except}")
        
        if bare_except > 0:
            self.issues.append(f"Found {bare_except} bare except blocks - consider specific exceptions")
        
        return {'try_blocks': try_blocks, 'except_blocks': except_blocks, 'bare_except': bare_except}
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "="*70)
        print("📊 DEEP CODE ANALYSIS REPORT")
        print("="*70)
        
        # Run all analyses
        self.read_file()
        imports_data = self.analyze_imports()
        functions_data = self.analyze_functions()
        routes_data = self.analyze_routes()
        security_issues = self.analyze_security()
        performance_issues = self.analyze_performance()
        error_data = self.analyze_error_handling()
        
        # Summary
        print(f"\n📈 SUMMARY:")
        print(f"  📏 Total lines: {len(self.lines)}")
        print(f"  🔧 Total functions: {len(functions_data['functions'])}")
        print(f"  🌐 Total routes: {len(routes_data['routes'])}")
        print(f"  ⚠️ Issues found: {len(self.issues)}")
        print(f"  💡 Suggestions: {len(self.suggestions)}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        
        if functions_data['long_functions']:
            print(f"  📏 Consider breaking down {len(functions_data['long_functions'])} long functions")
        
        if functions_data['complex_functions']:
            print(f"  🔄 Consider refactoring {len(functions_data['complex_functions'])} complex functions")
        
        if security_issues:
            print(f"  🔒 Review {len(security_issues)} potential security issues")
        
        if error_data['bare_except'] > 0:
            print(f"  🛡️ Replace {error_data['bare_except']} bare except blocks with specific exceptions")
        
        return {
            'imports': imports_data,
            'functions': functions_data,
            'routes': routes_data,
            'security': security_issues,
            'performance': performance_issues,
            'error_handling': error_data,
            'issues': self.issues,
            'suggestions': self.suggestions
        }

if __name__ == "__main__":
    analyzer = CodeAnalyzer('rr4-router-complete-enhanced-v3.py')
    report = analyzer.generate_report()
    
    print("\n" + "="*70)
    print("✅ ANALYSIS COMPLETE")
    print("="*70) 
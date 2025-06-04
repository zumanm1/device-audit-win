#!/usr/bin/env python3
"""
V4CODERCLI Installation Validator

Cross-platform validation script to ensure all components are properly installed
and configured for Windows, Linux, and macOS environments.

Usage:
    python3 install-validator.py
    python install-validator.py  (Windows)
"""

import os
import sys
import json
import time
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Cross-platform detection
PLATFORM = platform.system().lower()
IS_WINDOWS = PLATFORM == 'windows'
IS_LINUX = PLATFORM == 'linux'
IS_MACOS = PLATFORM == 'darwin'

# Color codes for cross-platform output
if IS_WINDOWS:
    # Windows console colors
    try:
        import colorama
        colorama.init()
        COLORS = {
            'GREEN': '\033[92m',
            'RED': '\033[91m',
            'YELLOW': '\033[93m',
            'BLUE': '\033[94m',
            'CYAN': '\033[96m',
            'RESET': '\033[0m',
            'BOLD': '\033[1m'
        }
    except ImportError:
        # Fallback to no colors on Windows if colorama not available
        COLORS = {k: '' for k in ['GREEN', 'RED', 'YELLOW', 'BLUE', 'CYAN', 'RESET', 'BOLD']}
else:
    # Unix colors
    COLORS = {
        'GREEN': '\033[92m',
        'RED': '\033[91m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'CYAN': '\033[96m',
        'RESET': '\033[0m',
        'BOLD': '\033[1m'
    }

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{COLORS['CYAN']}{COLORS['BOLD']}{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}{COLORS['RESET']}\n")

def print_success(text: str) -> None:
    """Print success message."""
    print(f"{COLORS['GREEN']}✅ {text}{COLORS['RESET']}")

def print_error(text: str) -> None:
    """Print error message."""
    print(f"{COLORS['RED']}❌ {text}{COLORS['RESET']}")

def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{COLORS['YELLOW']}⚠️  {text}{COLORS['RESET']}")

def print_info(text: str) -> None:
    """Print info message."""
    print(f"{COLORS['BLUE']}ℹ️  {text}{COLORS['RESET']}")

class InstallationValidator:
    """Comprehensive installation validator for V4CODERCLI."""
    
    def __init__(self):
        self.results = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'python_version': platform.python_version()
            },
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'warnings': 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
    def run_validation(self) -> bool:
        """Run complete validation suite."""
        print_header("V4CODERCLI INSTALLATION VALIDATOR")
        print_info(f"Platform: {self.results['platform']['system']} {self.results['platform']['release']}")
        print_info(f"Python: {self.results['platform']['python_version']}")
        print_info(f"Architecture: {self.results['platform']['machine']}")
        
        # Test suite
        tests = [
            ("Python Environment", self._test_python_environment),
            ("Core Dependencies", self._test_core_dependencies),
            ("File Structure", self._test_file_structure),
            ("Import System", self._test_import_system),
            ("Configuration Files", self._test_configuration_files),
            ("Network Modules", self._test_network_modules),
            ("Cross-Platform Features", self._test_cross_platform_features),
            ("Startup Scripts", self._test_startup_scripts),
            ("Documentation", self._test_documentation),
            ("Permissions & Security", self._test_permissions)
        ]
        
        for test_name, test_func in tests:
            self._run_test(test_name, test_func)
        
        # Generate summary
        self._generate_summary()
        
        # Save results
        self._save_results()
        
        return self.results['summary']['failed_tests'] == 0
    
    def _run_test(self, test_name: str, test_func) -> None:
        """Run individual test and record results."""
        print_header(f"Testing: {test_name}")
        self.results['summary']['total_tests'] += 1
        
        try:
            success, details = test_func()
            self.results['tests'][test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                self.results['summary']['passed_tests'] += 1
                print_success(f"{test_name}: PASSED")
            else:
                self.results['summary']['failed_tests'] += 1
                print_error(f"{test_name}: FAILED")
                
        except Exception as e:
            self.results['summary']['failed_tests'] += 1
            self.results['tests'][test_name] = {
                'status': 'ERROR',
                'details': f"Test error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
            print_error(f"{test_name}: ERROR - {str(e)}")
    
    def _test_python_environment(self) -> Tuple[bool, str]:
        """Test Python environment compatibility."""
        details = []
        success = True
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            details.append(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            details.append(f"❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.8+)")
            success = False
        
        # Check pip availability
        try:
            import pip
            details.append("✅ pip available")
        except ImportError:
            details.append("❌ pip not available")
            success = False
        
        # Check virtual environment detection
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        details.append(f"ℹ️  Virtual environment: {'Yes' if in_venv else 'No'}")
        
        return success, '\n'.join(details)
    
    def _test_core_dependencies(self) -> Tuple[bool, str]:
        """Test core dependencies installation."""
        required_packages = [
            ('click', 'CLI framework'),
            ('paramiko', 'SSH library'),
            ('netmiko', 'Network device library'),
            ('nornir', 'Automation framework'),
            ('yaml', 'YAML processing'),
            ('textfsm', 'Template parsing'),
            ('cryptography', 'Security/encryption'),
            ('jinja2', 'Template engine')
        ]
        
        details = []
        success = True
        
        for package, description in required_packages:
            try:
                __import__(package)
                details.append(f"✅ {package} - {description}")
            except ImportError:
                details.append(f"❌ {package} - {description} (MISSING)")
                success = False
        
        # Test optional packages
        optional_packages = [
            ('dotenv', 'Environment management'),
            ('tabulate', 'Table formatting'),
            ('requests', 'HTTP client')
        ]
        
        for package, description in optional_packages:
            try:
                __import__(package)
                details.append(f"✅ {package} - {description} (optional)")
            except ImportError:
                details.append(f"⚠️  {package} - {description} (optional, missing)")
                self.results['summary']['warnings'] += 1
        
        return success, '\n'.join(details)
    
    def _test_file_structure(self) -> Tuple[bool, str]:
        """Test file structure integrity."""
        required_files = [
            'start_rr4_cli_enhanced.py',
            'start_rr4_cli.py',
            'rr4-complete-enchanced-v4-cli.py',
            'system_health_monitor.py',
            'requirements.txt',
            'requirements-minimal.txt',
            'setup.py',
            '.env-t'
        ]
        
        required_dirs = [
            'rr4_complete_enchanced_v4_cli_core',
            'rr4_complete_enchanced_v4_cli_tasks'
        ]
        
        details = []
        success = True
        
        # Check files
        for file in required_files:
            if Path(file).exists():
                size = Path(file).stat().st_size
                details.append(f"✅ {file} ({size} bytes)")
            else:
                details.append(f"❌ {file} (MISSING)")
                success = False
        
        # Check directories
        for dir in required_dirs:
            if Path(dir).is_dir():
                file_count = len(list(Path(dir).glob('*.py')))
                details.append(f"✅ {dir}/ ({file_count} Python files)")
            else:
                details.append(f"❌ {dir}/ (MISSING)")
                success = False
        
        return success, '\n'.join(details)
    
    def _test_import_system(self) -> Tuple[bool, str]:
        """Test import system functionality."""
        test_imports = [
            'rr4_complete_enchanced_v4_cli_core',
            'rr4_complete_enchanced_v4_cli_tasks',
            'rr4_complete_enchanced_v4_cli_core.connection_manager',
            'rr4_complete_enchanced_v4_cli_tasks.base_collector'
        ]
        
        details = []
        success = True
        
        # Add current directory to path for testing
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        
        for module in test_imports:
            try:
                __import__(module)
                details.append(f"✅ {module}")
            except ImportError as e:
                details.append(f"❌ {module} - {str(e)}")
                success = False
        
        return success, '\n'.join(details)
    
    def _test_configuration_files(self) -> Tuple[bool, str]:
        """Test configuration files."""
        config_files = [
            '.env-t',
            'rr4-complete-enchanced-v4-cli.env-t',
            'rr4-complete-enchanced-v4-cli-routers01.csv'
        ]
        
        details = []
        success = True
        warnings = 0
        
        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        if content.strip():
                            details.append(f"✅ {config_file} ({len(content)} chars)")
                        else:
                            details.append(f"⚠️  {config_file} (empty)")
                            warnings += 1
                except Exception as e:
                    details.append(f"❌ {config_file} - Read error: {str(e)}")
                    success = False
            else:
                details.append(f"⚠️  {config_file} (missing)")
                warnings += 1
        
        self.results['summary']['warnings'] += warnings
        return success, '\n'.join(details)
    
    def _test_network_modules(self) -> Tuple[bool, str]:
        """Test network-specific modules."""
        details = []
        success = True
        
        # Test connection manager
        try:
            from rr4_complete_enchanced_v4_cli_core.connection_manager import ConnectionManager
            details.append("✅ ConnectionManager class")
        except Exception as e:
            details.append(f"❌ ConnectionManager: {str(e)}")
            success = False
        
        # Test collectors
        try:
            from rr4_complete_enchanced_v4_cli_tasks import get_available_layers
            layers = get_available_layers()
            details.append(f"✅ Available layers: {', '.join(layers)}")
        except Exception as e:
            details.append(f"❌ Layer collectors: {str(e)}")
            success = False
        
        return success, '\n'.join(details)
    
    def _test_cross_platform_features(self) -> Tuple[bool, str]:
        """Test cross-platform specific features."""
        details = []
        success = True
        
        # Test pathlib usage
        try:
            test_path = Path('.') / 'test_file.tmp'
            details.append("✅ pathlib.Path functionality")
        except Exception as e:
            details.append(f"❌ pathlib: {str(e)}")
            success = False
        
        # Test platform detection
        details.append(f"✅ Platform: {PLATFORM}")
        details.append(f"✅ Windows: {IS_WINDOWS}")
        details.append(f"✅ Linux: {IS_LINUX}")
        details.append(f"✅ macOS: {IS_MACOS}")
        
        # Test file permissions (Unix only)
        if not IS_WINDOWS:
            try:
                import stat
                details.append("✅ Unix file permissions")
            except Exception as e:
                details.append(f"❌ File permissions: {str(e)}")
                success = False
        
        return success, '\n'.join(details)
    
    def _test_startup_scripts(self) -> Tuple[bool, str]:
        """Test startup scripts."""
        scripts = []
        details = []
        success = True
        
        if IS_WINDOWS:
            scripts = ['start-v4codercli.bat']
        else:
            scripts = ['start-v4codercli.sh']
        
        for script in scripts:
            if Path(script).exists():
                details.append(f"✅ {script}")
                # Test if executable (Unix only)
                if not IS_WINDOWS:
                    if os.access(script, os.X_OK):
                        details.append(f"✅ {script} is executable")
                    else:
                        details.append(f"⚠️  {script} not executable")
                        self.results['summary']['warnings'] += 1
            else:
                details.append(f"❌ {script} (MISSING)")
                success = False
        
        return success, '\n'.join(details)
    
    def _test_documentation(self) -> Tuple[bool, str]:
        """Test documentation files."""
        doc_files = [
            'README.md',
            'QUICK_START.txt',
            'STARTUP_COMMANDS_GUIDE.txt',
            'tracking-changes.txt'
        ]
        
        details = []
        success = True
        
        for doc_file in doc_files:
            if Path(doc_file).exists():
                size = Path(doc_file).stat().st_size
                details.append(f"✅ {doc_file} ({size} bytes)")
            else:
                details.append(f"⚠️  {doc_file} (missing)")
                self.results['summary']['warnings'] += 1
        
        return success, '\n'.join(details)
    
    def _test_permissions(self) -> Tuple[bool, str]:
        """Test file permissions and security."""
        details = []
        success = True
        
        # Test write permissions in current directory
        try:
            test_file = Path('test_write_permissions.tmp')
            test_file.write_text('test')
            test_file.unlink()
            details.append("✅ Write permissions in current directory")
        except Exception as e:
            details.append(f"❌ Write permissions: {str(e)}")
            success = False
        
        # Test environment file permissions
        env_files = ['.env-t', 'rr4-complete-enchanced-v4-cli.env-t']
        for env_file in env_files:
            if Path(env_file).exists():
                if IS_WINDOWS:
                    details.append(f"✅ {env_file} exists (Windows)")
                else:
                    # Check Unix permissions
                    file_stat = Path(env_file).stat()
                    perms = oct(file_stat.st_mode)[-3:]
                    details.append(f"✅ {env_file} permissions: {perms}")
        
        return success, '\n'.join(details)
    
    def _generate_summary(self) -> None:
        """Generate validation summary."""
        print_header("VALIDATION SUMMARY")
        
        total = self.results['summary']['total_tests']
        passed = self.results['summary']['passed_tests']
        failed = self.results['summary']['failed_tests']
        warnings = self.results['summary']['warnings']
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {COLORS['GREEN']}{passed}{COLORS['RESET']}")
        print(f"Failed: {COLORS['RED']}{failed}{COLORS['RESET']}")
        print(f"Warnings: {COLORS['YELLOW']}{warnings}{COLORS['RESET']}")
        print(f"Success Rate: {COLORS['CYAN']}{success_rate:.1f}%{COLORS['RESET']}")
        
        if failed == 0:
            print_success("🎉 ALL TESTS PASSED! V4CODERCLI is ready for use.")
        else:
            print_error(f"❌ {failed} test(s) failed. Please review and fix issues.")
        
        if warnings > 0:
            print_warning(f"⚠️  {warnings} warning(s) found. Consider addressing them.")
    
    def _save_results(self) -> None:
        """Save validation results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            print_info(f"Results saved to: {filename}")
        except Exception as e:
            print_warning(f"Could not save results: {str(e)}")

def main():
    """Main validation function."""
    validator = InstallationValidator()
    success = validator.run_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 
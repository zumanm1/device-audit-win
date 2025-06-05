#!/usr/bin/env python3
"""
V4codercli System Health Monitor
Comprehensive testing and monitoring script for V4codercli system
Designed for hourly execution and deep system understanding

Author: AI Assistant  
Version: 1.0.0
Created: 2025-06-02
"""

import sys
import os
import time
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add current directory to path for imports
sys.path.append('.')

class SystemHealthMonitor:
    """Comprehensive system health monitoring and testing."""
    
    def __init__(self):
        """Initialize the health monitor."""
        self.start_time = datetime.now()
        self.results = {
            'timestamp': self.start_time.isoformat(),
            'tests': {},
            'summary': {},
            'recommendations': []
        }
        
    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log test results."""
        self.results['tests'][test_name] = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        print(f"{'✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'} {test_name}: {status}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")

    def test_environment_files(self) -> bool:
        """Test environment file loading and configuration."""
        try:
            test_name = "Environment Files"
            env_files = ['.env-t', 'rr4-complete-enchanced-v4-cli.env-t']
            
            found_files = []
            loaded_config = {}
            
            for env_file in env_files:
                if Path(env_file).exists():
                    found_files.append(env_file)
                    # Try to load it
                    try:
                        with open(env_file, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and '=' in line:
                                    key, value = line.split('=', 1)
                                    loaded_config[key.strip()] = value.strip()
                    except Exception as e:
                        self.log_test(test_name, "FAIL", {"error": f"Failed to load {env_file}: {e}"})
                        return False
            
            if found_files:
                self.log_test(test_name, "PASS", {
                    "found_files": found_files,
                    "config_keys": list(loaded_config.keys()),
                    "jump_host": loaded_config.get('JUMP_HOST_IP', 'NOT_SET')
                })
                return True
            else:
                self.log_test(test_name, "FAIL", {"error": "No environment files found"})
                return False
                
        except Exception as e:
            self.log_test(test_name, "FAIL", {"error": str(e)})
            return False

    def test_core_modules(self) -> bool:
        """Test core module imports and basic functionality."""
        try:
            test_name = "Core Modules"
            
            # Test connection manager
            from rr4_complete_enchanced_v4_cli_core.connection_manager import get_jump_host_config
            config = get_jump_host_config()
            
            # Test other core modules
            from rr4_complete_enchanced_v4_cli_core.data_parser import DataParser
            from rr4_complete_enchanced_v4_cli_core.output_handler import OutputHandler
            from rr4_complete_enchanced_v4_cli_core.inventory_loader import InventoryLoader
            from rr4_complete_enchanced_v4_cli_core.task_executor import TaskExecutor
            
            self.log_test(test_name, "PASS", {
                "connection_manager": "OK",
                "data_parser": "OK", 
                "output_handler": "OK",
                "inventory_loader": "OK",
                "task_executor": "OK",
                "jump_host": config.get('hostname', 'Unknown')
            })
            return True
            
        except Exception as e:
            self.log_test(test_name, "FAIL", {"error": str(e), "traceback": traceback.format_exc()})
            return False

    def test_task_collectors(self) -> bool:
        """Test all task collectors individually."""
        try:
            test_name = "Task Collectors"
            
            from rr4_complete_enchanced_v4_cli_tasks import get_layer_collector, get_available_layers
            
            layers = get_available_layers()
            collector_results = {}
            failed_collectors = []
            
            for layer in layers:
                try:
                    collector_class = get_layer_collector(layer)
                    if collector_class:
                        # Try to instantiate
                        collector = collector_class('cisco_ios')
                        commands = collector.get_commands()
                        collector_results[layer] = {
                            "class_name": collector_class.__name__,
                            "command_count": len(commands),
                            "status": "OK"
                        }
                    else:
                        failed_collectors.append(layer)
                        collector_results[layer] = {"status": "FAILED", "error": "No collector class"}
                except Exception as e:
                    failed_collectors.append(layer)
                    collector_results[layer] = {"status": "FAILED", "error": str(e)}
            
            if not failed_collectors:
                self.log_test(test_name, "PASS", {
                    "total_layers": len(layers),
                    "working_collectors": len(layers) - len(failed_collectors),
                    "collectors": collector_results
                })
                return True
            else:
                self.log_test(test_name, "FAIL", {
                    "failed_collectors": failed_collectors,
                    "details": collector_results
                })
                return False
                
        except Exception as e:
            self.log_test(test_name, "FAIL", {"error": str(e)})
            return False

    def test_main_scripts(self) -> bool:
        """Test main script files and their basic functionality."""
        try:
            test_name = "Main Scripts"
            
            scripts = [
                'start_rr4_cli_enhanced.py',
                'rr4-complete-enchanced-v4-cli.py',
                'start_rr4_cli.py'
            ]
            
            script_status = {}
            
            for script in scripts:
                if Path(script).exists():
                    script_status[script] = {
                        "exists": True,
                        "size": Path(script).stat().st_size,
                        "executable": os.access(script, os.X_OK)
                    }
                    
                    # Check for main function
                    try:
                        with open(script, 'r') as f:
                            content = f.read()
                            script_status[script]["has_main"] = 'def main' in content or 'if __name__' in content
                    except Exception as e:
                        script_status[script]["read_error"] = str(e)
                else:
                    script_status[script] = {"exists": False}
            
            all_exist = all(status.get("exists", False) for status in script_status.values())
            
            self.log_test(test_name, "PASS" if all_exist else "WARN", {
                "scripts": script_status,
                "all_exist": all_exist
            })
            return all_exist
            
        except Exception as e:
            self.log_test(test_name, "FAIL", {"error": str(e)})
            return False

    def test_file_structure(self) -> bool:
        """Test directory and file structure."""
        try:
            test_name = "File Structure"
            
            required_dirs = [
                'rr4_complete_enchanced_v4_cli_core',
                'rr4_complete_enchanced_v4_cli_tasks',
                'outputs',
                'docs',
                'tests'
            ]
            
            dir_status = {}
            for dir_name in required_dirs:
                dir_path = Path(dir_name)
                if dir_path.exists():
                    file_count = len(list(dir_path.glob('*')))
                    py_file_count = len(list(dir_path.glob('*.py')))
                    dir_status[dir_name] = {
                        "exists": True,
                        "total_files": file_count,
                        "python_files": py_file_count
                    }
                else:
                    dir_status[dir_name] = {"exists": False}
            
            all_dirs_exist = all(status.get("exists", False) for status in dir_status.values())
            
            self.log_test(test_name, "PASS" if all_dirs_exist else "WARN", {
                "directories": dir_status,
                "all_required_dirs_exist": all_dirs_exist
            })
            return True
            
        except Exception as e:
            self.log_test(test_name, "FAIL", {"error": str(e)})
            return False

    def perform_comprehensive_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive system analysis."""
        print("🎯 V4CODERCLI SYSTEM HEALTH MONITOR")
        print("=" * 60)
        print(f"📅 Timestamp: {self.start_time}")
        print(f"📂 Working Directory: {os.getcwd()}")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_environment_files,
            self.test_file_structure,
            self.test_core_modules,
            self.test_task_collectors,
            self.test_main_scripts
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                failed += 1
        
        # Generate summary
        total_tests = passed + failed
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'success_rate': success_rate,
            'status': 'HEALTHY' if success_rate >= 90 else 'DEGRADED' if success_rate >= 70 else 'CRITICAL'
        }
        
        # Generate recommendations
        if failed > 0:
            self.results['recommendations'].append("Some tests failed - review failed test details")
        if success_rate < 100:
            self.results['recommendations'].append("System not at 100% health - investigate warnings")
        if success_rate >= 90:
            self.results['recommendations'].append("System is performing well - continue monitoring")
        
        print("\n" + "=" * 60)
        print("📊 SYSTEM HEALTH SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {passed}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ Tests Failed: {failed}/{total_tests}")
        print(f"🎯 Overall Status: {self.results['summary']['status']}")
        
        if self.results['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in self.results['recommendations']:
                print(f"  • {rec}")
        
        # Save detailed results
        try:
            results_file = f"system_health_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📄 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Failed to save results: {e}")
        
        return self.results

def main():
    """Main entry point for health monitoring."""
    try:
        monitor = SystemHealthMonitor()
        results = monitor.perform_comprehensive_analysis()
        
        # Exit with appropriate code
        status = results['summary']['status']
        if status == 'HEALTHY':
            sys.exit(0)
        elif status == 'DEGRADED':
            sys.exit(1)
        else:  # CRITICAL
            sys.exit(2)
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR in health monitor: {e}")
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main() 
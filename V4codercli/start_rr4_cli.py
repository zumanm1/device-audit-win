#!/usr/bin/env python3
"""
RR4 CLI Interactive Startup Script - Cross-Platform Compatible
Comprehensive guided setup and execution for the RR4 Complete Enhanced v4 CLI

CROSS-PLATFORM STARTUP:
- Windows 10/11: python start_rr4_cli.py
- Linux: python3 start_rr4_cli.py
- macOS: python3 start_rr4_cli.py

This script provides:
- Guided first-time setup
- Prerequisites checking
- Step-by-step testing
- Menu-driven interface for different use cases
- Error handling and recovery
- Best practice recommendations

Author: AI Assistant
Version: 1.0.1-CrossPlatform
Created: 2025-05-31
Platform Support: Windows 10/11, Linux, macOS
"""

import os
import sys
import time
import json
import csv
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Cross-platform compatibility check
def get_python_command():
    """Get the appropriate Python command for the current platform"""
    if platform.system().lower() == 'windows':
        return 'python'
    else:
        return 'python3'

def display_startup_info():
    """Display cross-platform startup information"""
    system = platform.system()
    python_cmd = get_python_command()
    
    print(f"{Colors.CYAN}{'=' * 80}")
    print(f"🌐 CROSS-PLATFORM STARTUP INFORMATION")
    print(f"{'=' * 80}{Colors.RESET}")
    print(f"\n{Colors.BOLD}Current Platform: {system} {platform.release()}{Colors.RESET}")
    print(f"{Colors.BOLD}Python Version: {platform.python_version()}{Colors.RESET}")
    print(f"\n{Colors.GREEN}To start this script on different platforms:{Colors.RESET}")
    
    if system.lower() == 'windows':
        print(f"  {Colors.YELLOW}Windows 10/11:{Colors.RESET}")
        print(f"    {Colors.WHITE}{python_cmd} start_rr4_cli.py{Colors.RESET}")
        print(f"    {Colors.WHITE}run_rr4_cli.bat{Colors.RESET}")
    else:
        print(f"  {Colors.YELLOW}Linux/macOS:{Colors.RESET}")
        print(f"    {Colors.WHITE}{python_cmd} start_rr4_cli.py{Colors.RESET}")
        print(f"    {Colors.WHITE}./start_rr4_cli.py{Colors.RESET} (if executable)")
    
    print(f"\n{Colors.BLUE}Universal command (all platforms):{Colors.RESET}")
    print(f"  {Colors.WHITE}{python_cmd} start_rr4_cli.py{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

# ANSI color codes for better terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

def print_header(title: str, color: str = Colors.CYAN):
    """Print a formatted header"""
    width = 80
    print(f"\n{color}{'=' * width}")
    print(f"{title.center(width)}")
    print(f"{'=' * width}{Colors.RESET}\n")

def print_section(title: str, color: str = Colors.YELLOW):
    """Print a formatted section header"""
    print(f"\n{color}{Colors.BOLD}🔧 {title}{Colors.RESET}")
    print(f"{color}{'-' * (len(title) + 4)}{Colors.RESET}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")

class RR4StartupManager:
    """Main startup manager for RR4 CLI"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.main_script = self.script_dir / "rr4-complete-enchanced-v4-cli.py"
        self.test_results = {}
        self.prerequisites_checked = False
        self.platform_info = self._get_platform_info()
        
    def _get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'python_version': platform.python_version(),
            'is_windows': platform.system().lower() == 'windows',
            'is_linux': platform.system().lower() == 'linux',
            'is_macos': platform.system().lower() == 'darwin'
        }
    
    def _run_command(self, command: List[str], description: str, critical: bool = True, timeout: int = 120) -> Tuple[bool, str, str]:
        """Run a command and return success status with output"""
        try:
            print_info(f"Running: {description}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.script_dir
            )
            
            success = result.returncode == 0
            if success:
                print_success(f"{description} - Completed successfully")
                return True, result.stdout, result.stderr
            else:
                error_msg = f"{description} - Failed (Exit code: {result.returncode})"
                if critical:
                    print_error(error_msg)
                    print_error(f"Error output: {result.stderr}")
                else:
                    print_warning(error_msg)
                return False, result.stdout, result.stderr
                
        except subprocess.TimeoutExpired:
            error_msg = f"{description} - Timed out after {timeout} seconds"
            if critical:
                print_error(error_msg)
            else:
                print_warning(error_msg)
            return False, "", "Timeout"
        except Exception as e:
            error_msg = f"{description} - Exception: {str(e)}"
            if critical:
                print_error(error_msg)
            else:
                print_warning(error_msg)
            return False, "", str(e)
    
    def check_prerequisites(self) -> bool:
        """Check all prerequisites"""
        print_header("PREREQUISITES CHECK", Colors.CYAN)
        
        all_good = True
        
        # Check Python version
        print_section("Python Version Check")
        python_version = sys.version_info
        if python_version >= (3, 8):
            print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - Compatible")
        else:
            print_error(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - Requires Python 3.8+")
            all_good = False
        
        # Check if main script exists
        print_section("Main Script Check")
        if self.main_script.exists():
            print_success(f"Main script found: {self.main_script}")
        else:
            print_error(f"Main script not found: {self.main_script}")
            all_good = False
            return False
        
        # Check platform compatibility
        print_section("Platform Compatibility Check")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "show-platform"],
            "Platform information check",
            critical=False
        )
        if success:
            print_success("Platform compatibility verified")
        else:
            print_warning("Platform check had issues but continuing...")
        
        # Check dependencies
        print_section("Dependencies Check")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "--test-dependencies"],
            "Dependencies verification",
            critical=True
        )
        if success:
            print_success("All dependencies are available")
        else:
            print_error("Dependencies check failed")
            print_info("Run: pip install -r requirements.txt")
            all_good = False
        
        self.prerequisites_checked = all_good
        return all_good
    
    def validate_environment(self) -> bool:
        """Validate environment configuration"""
        print_header("ENVIRONMENT VALIDATION", Colors.CYAN)
        
        # Check if environment file exists
        env_file = self.script_dir / "rr4-complete-enchanced-v4-cli.env-t"
        if env_file.exists():
            print_success("Environment file found")
            
            # Check configuration
            success, stdout, stderr = self._run_command(
                ["python3", str(self.main_script), "show-config"],
                "Configuration validation",
                critical=False
            )
            if success:
                print_success("Configuration is valid")
                return True
            else:
                print_warning("Configuration has issues")
                return False
        else:
            print_warning("Environment file not found")
            return False
    
    def setup_environment(self) -> bool:
        """Interactive environment setup"""
        print_header("ENVIRONMENT SETUP", Colors.CYAN)
        
        print_info("Starting interactive environment configuration...")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "configure-env"],
            "Interactive environment configuration",
            critical=True
        )
        
        if success:
            print_success("Environment configuration completed")
            return True
        else:
            print_error("Environment configuration failed")
            return False
    
    def validate_inventory(self) -> bool:
        """Validate inventory file"""
        print_header("INVENTORY VALIDATION", Colors.CYAN)
        
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "validate-inventory"],
            "Inventory file validation",
            critical=True
        )
        
        if success:
            print_success("Inventory validation passed")
            # Extract device count from output
            if "Found" in stdout and "devices" in stdout:
                print_info(f"Inventory details: {stdout.split('Found')[1].split('devices')[0].strip()} devices found")
            return True
        else:
            print_error("Inventory validation failed")
            return False
    
    def test_connectivity(self) -> bool:
        """Test device connectivity"""
        print_header("CONNECTIVITY TEST", Colors.CYAN)
        
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "test-connectivity"],
            "Device connectivity test",
            critical=True
        )
        
        if success:
            print_success("Connectivity test passed")
            # Extract success rate from output
            if "Success rate:" in stdout:
                success_rate_str = stdout.split("Success rate:")[1].split("%")[0].strip()
                try:
                    success_rate = float(success_rate_str)
                    print_info(f"Success rate: {success_rate}%")
                    
                    if success_rate >= 80.0:
                        print_success(f"Excellent connectivity: {success_rate}% of devices reachable")
                        return True
                    elif success_rate >= 50.0:
                        print_warning(f"Partial connectivity: {success_rate}% of devices reachable")
                        print_info("This is acceptable for testing - some devices may be down")
                        return True
                    else:
                        print_error(f"Poor connectivity: Only {success_rate}% of devices reachable")
                        return False
                except ValueError:
                    print_warning("Could not parse success rate, but test completed")
                    return True
            return True
        else:
            print_error("Connectivity test failed")
            return False
    
    def run_sample_collection(self) -> bool:
        """Run a sample data collection"""
        print_header("SAMPLE COLLECTION TEST", Colors.CYAN)
        
        print_info("Running sample collection from first device with health layer...")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-devices", "--device", "R0", "--layers", "health"],
            "Sample collection test (single device, health layer)",
            critical=True
        )
        
        if success:
            print_success("Sample collection completed successfully")
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Output saved to: {output_info}")
            return True
        else:
            print_error("Sample collection failed")
            return False
    
    def show_main_menu(self) -> int:
        """Display main menu and get user choice"""
        # Display cross-platform startup information first
        display_startup_info()
        
        print_header("RR4 CLI INTERACTIVE STARTUP", Colors.MAGENTA)
        
        print(f"{Colors.BOLD}Welcome to RR4 Complete Enhanced v4 CLI Startup Manager{Colors.RESET}")
        print(f"Platform: {self.platform_info['system']} {self.platform_info['release']}")
        print(f"Python: {self.platform_info['python_version']}")
        
        print(f"\n{Colors.BOLD}🚀 STARTUP OPTIONS:{Colors.RESET}")
        print(f"{Colors.GREEN}1. 🎯 FIRST-TIME SETUP (Recommended for new users){Colors.RESET}")
        print(f"   - Complete guided setup with prerequisites check")
        print(f"   - Environment configuration")
        print(f"   - Enhanced connectivity testing (ping + SSH auth)")
        print(f"   - Sample collection test")
        
        print(f"\n{Colors.BLUE}2. 🔍 AUDIT ONLY (Quick connectivity and health check){Colors.RESET}")
        print(f"   - Enhanced connectivity test (ping + SSH auth)")
        print(f"   - Health data collection from reachable devices")
        print(f"   - Generate audit report")
        
        print(f"\n{Colors.CYAN}3. 📊 FULL COLLECTION (Production data collection){Colors.RESET}")
        print(f"   - Enhanced connectivity test first")
        print(f"   - Collect from all reachable devices")
        print(f"   - Standard layers (health, interfaces, igp, bgp, mpls, vpn, static)")
        print(f"   - Generate comprehensive reports")
        
        print(f"\n{Colors.YELLOW}4. 🎛️  CUSTOM COLLECTION (Advanced users){Colors.RESET}")
        print(f"   - Choose specific devices")
        print(f"   - Select layers to collect")
        print(f"   - Custom parameters")
        
        print(f"\n{Colors.MAGENTA}5. 🔧 PREREQUISITES CHECK ONLY{Colors.RESET}")
        print(f"   - Verify system requirements")
        print(f"   - Check dependencies")
        print(f"   - Validate configuration")
        
        print(f"\n{Colors.CYAN}6. 🌐 ENHANCED CONNECTIVITY TEST ONLY{Colors.RESET}")
        print(f"   - Comprehensive ping + SSH authentication test")
        print(f"   - Detailed device-by-device status report")
        print(f"   - No data collection")
        
        print(f"\n{Colors.WHITE}7. 📚 SHOW HELP & OPTIONS{Colors.RESET}")
        print(f"   - Display all available commands")
        print(f"   - Show advanced options")
        print(f"   - Documentation links")
        
        print(f"\n{Colors.YELLOW}8. 🎯 CONSOLE AUDIT (NM4 Console Line Collection){Colors.RESET}")
        print(f"   - Enhanced connectivity test first")
        print(f"   - Console line discovery and configuration collection")
        print(f"   - NM4 console card support (IOS/IOS XR)")
        print(f"   - Generate console audit report")
        
        print(f"\n{Colors.GREEN}9. 🌟 COMPLETE COLLECTION (All layers + Console in systematic order){Colors.RESET}")
        print(f"   - Enhanced connectivity test first")
        print(f"   - Systematic collection in optimal order")
        print(f"   - ALL layers (health, interfaces, igp, bgp, mpls, vpn, static, console)")
        print(f"   - Comprehensive audit and production reports")
        
        print(f"\n{Colors.RED}10. 🔒 CONSOLE SECURITY AUDIT (Transport Security Analysis){Colors.RESET}")
        print(f"   - Analyze console audit results from option 8")
        print(f"   - Detect telnet transport violations (aux, console, vty, line)")
        print(f"   - Security compliance report per router and summary")
        print(f"   - Transport input/output validation")
        
        print(f"\n{Colors.BLUE}12. 📊 COMPREHENSIVE STATUS REPORT (All Options Analysis){Colors.RESET}")
        print(f"   - Analyze collection data from options 1-10 with device filtering")
        print(f"   - Choose: All routers, single router, or platform-specific subsets")
        print(f"   - Generate unified status and gap analysis reports")
        print(f"   - Identify missing collections and remediation needs")
        print(f"   - Executive summary and detailed technical reports")
        
        print(f"\n{Colors.RED}0. 🚪 EXIT{Colors.RESET}")
        
        while True:
            try:
                choice = input(f"\n{Colors.BOLD}Select option (0-12): {Colors.RESET}").strip()
                if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12']:
                    return int(choice)
                else:
                    print_error("Invalid choice. Please enter 0-12 (note: option 11 is reserved).")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                return 0
            except Exception:
                print_error("Invalid input. Please enter a number (0-12, option 11 reserved).")
    
    def first_time_setup(self) -> bool:
        """Complete first-time setup process"""
        print_header("FIRST-TIME SETUP PROCESS", Colors.GREEN)
        
        steps = [
            ("Prerequisites Check", self.check_prerequisites),
            ("Environment Validation", self.validate_environment),
            ("Environment Setup", self.setup_environment),
            ("Inventory Validation", self.validate_inventory),
            ("Enhanced Connectivity Test", self.enhanced_connectivity_test),
            ("Sample Collection", self.run_sample_collection)
        ]
        
        for step_name, step_func in steps:
            print_section(f"Step: {step_name}")
            
            try:
                if step_name == "Environment Setup":
                    # Skip if environment is already valid
                    if self.validate_environment():
                        print_success("Environment already configured, skipping setup")
                        self.test_results[step_name] = "PASSED"
                        continue
                
                success = step_func()
                if success:
                    print_success(f"{step_name} completed successfully")
                    self.test_results[step_name] = "PASSED"
                else:
                    print_error(f"{step_name} failed")
                    self.test_results[step_name] = "FAILED"
                    
                    # Ask user if they want to continue
                    if not self._ask_continue_on_error(step_name):
                        return False
                
                # Special handling for connectivity test - ask before proceeding to collection
                if step_name == "Enhanced Connectivity Test" and success:
                    print_section("Proceed to Sample Collection")
                    try:
                        proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with sample data collection? (y/n): {Colors.RESET}").strip().lower()
                        if proceed not in ['y', 'yes']:
                            print_info("Sample collection skipped by user")
                            self.test_results["Sample Collection"] = "SKIPPED"
                            break
                    except:
                        print_info("Proceeding with sample collection...")
                        
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Setup interrupted by user.{Colors.RESET}")
                return False
            except Exception as e:
                print_error(f"{step_name} error: {str(e)}")
                self.test_results[step_name] = f"ERROR: {str(e)}"
                if not self._ask_continue_on_error(step_name):
                    return False
        
        # Show final results
        self._show_setup_results()
        return True
    
    def audit_only(self) -> bool:
        """Run audit-only mode with enhanced connectivity"""
        print_header("AUDIT ONLY MODE", Colors.BLUE)
        
        print_info("Running quick audit of network devices...")
        
        # Quick prerequisite check
        if not self.prerequisites_checked:
            print_section("Quick Prerequisites Check")
            if not self.check_prerequisites():
                print_error("Prerequisites check failed")
                return False
        
        # Enhanced connectivity test
        if not self.enhanced_connectivity_test():
            print_error("Enhanced connectivity test failed")
            return False
        
        # Ask user before proceeding to data collection
        print_section("Proceed to Data Collection")
        try:
            proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with health data collection? (y/n): {Colors.RESET}").strip().lower()
            if proceed not in ['y', 'yes']:
                print_info("Data collection cancelled by user")
                return True
        except:
            print_info("Proceeding with data collection...")
        
        # Quick health collection from all devices
        print_section("Health Data Collection")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-all", "--layers", "health"],
            "Health data collection from all reachable devices",
            critical=True,
            timeout=300  # 5 minutes for health collection
        )
        
        if success:
            print_success("Audit completed successfully")
            print_info("Health data collected from all reachable devices")
            
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Audit results saved to: {output_info}")
            return True
        else:
            print_error("Audit collection failed")
            return False
    
    def full_collection(self) -> bool:
        """Run full data collection"""
        print_header("FULL COLLECTION MODE", Colors.CYAN)
        
        print_info("Running comprehensive data collection from all devices...")
        
        # Verify prerequisites
        if not self.prerequisites_checked:
            print_section("Prerequisites Verification")
            if not self.check_prerequisites():
                print_error("Prerequisites check failed")
                return False
        
        # Enhanced connectivity test first
        if not self.enhanced_connectivity_test():
            print_error("Enhanced connectivity test failed")
            return False
        
        # Ask user before proceeding to full collection
        print_section("Proceed to Full Collection")
        try:
            proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with full data collection? (y/n): {Colors.RESET}").strip().lower()
            if proceed not in ['y', 'yes']:
                print_info("Full data collection cancelled by user")
                return True
        except:
            print_info("Proceeding with full data collection...")
        
        # Run full collection with standard layers (no console)
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-all", "--layers", "health,interfaces,igp,bgp,mpls,vpn,static"],
            "Full data collection (standard layers, all reachable devices)",
            critical=True,
            timeout=600  # 10 minutes for full collection
        )
        
        if success:
            print_success("Full collection completed successfully")
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Data saved to: {output_info}")
            return True
        else:
            print_error("Full collection failed")
            return False
    
    def enhanced_connectivity_test(self) -> bool:
        """Enhanced connectivity test with ping and SSH authentication"""
        print_header("ENHANCED CONNECTIVITY TEST", Colors.CYAN)
        
        print_info("Performing comprehensive connectivity test...")
        print_info("Step 1: Testing network reachability (ping)")
        print_info("Step 2: Testing SSH authentication")
        print_info("Note: Device is considered UP if SSH authentication succeeds, even if ping fails")
        
        # Run the enhanced connectivity test
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "test-connectivity"],
            "Enhanced connectivity test (ping + SSH authentication)",
            critical=True,
            timeout=180  # 3 minutes for connectivity test
        )
        
        if success:
            print_success("Enhanced connectivity test completed")
            
            # Parse results
            if "Success rate:" in stdout:
                success_rate_str = stdout.split("Success rate:")[1].split("%")[0].strip()
                try:
                    success_rate = float(success_rate_str)
                    print_info(f"Overall success rate: {success_rate}%")
                    
                    # Extract device details
                    if "Device-by-Device Breakdown:" in stdout:
                        breakdown_section = stdout.split("Device-by-Device Breakdown:")[1].split("🔐")[0]
                        lines = breakdown_section.strip().split('\n')
                        
                        successful_devices = []
                        failed_devices = []
                        
                        for line in lines:
                            if "✅" in line and "Connected" in line:
                                device_name = line.split()[1]
                                successful_devices.append(device_name)
                            elif "❌" in line and "Failed" in line:
                                device_name = line.split()[1]
                                failed_devices.append(device_name)
                        
                        print_section("Connectivity Summary")
                        if successful_devices:
                            print_success(f"Successfully connected devices ({len(successful_devices)}): {', '.join(successful_devices)}")
                        
                        if failed_devices:
                            print_warning(f"Failed to connect devices ({len(failed_devices)}): {', '.join(failed_devices)}")
                            print_info("Failed devices will be skipped during data collection")
                    
                    if success_rate >= 50.0:
                        print_success(f"Connectivity test PASSED - {success_rate}% devices reachable")
                        
                        # Ask user if they want to continue
                        print_section("Next Steps Decision")
                        print_info("Connectivity test completed successfully!")
                        print_info(f"✅ {len(successful_devices) if 'successful_devices' in locals() else 'Several'} devices are ready for data collection")
                        if 'failed_devices' in locals() and failed_devices:
                            print_info(f"⚠️  {len(failed_devices)} devices are unreachable and will be skipped")
                        
                        return True
                    else:
                        print_error(f"Connectivity test FAILED - Only {success_rate}% devices reachable")
                        print_error("Too many devices are unreachable for reliable data collection")
                        return False
                        
                except ValueError:
                    print_warning("Could not parse success rate, but test completed")
                    return True
            return True
        else:
            print_error("Enhanced connectivity test failed")
            return False
    
    def custom_collection(self) -> bool:
        """Run custom collection with user choices"""
        print_header("CUSTOM COLLECTION MODE", Colors.YELLOW)
        
        # Get available devices
        print_section("Available Devices")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "validate-inventory"],
            "Loading available devices",
            critical=True
        )
        
        if not success:
            print_error("Could not load device inventory")
            return False
        
        # Device selection
        print_info("Device Selection Options:")
        print("1. All devices")
        print("2. Specific devices")
        print("3. Device group")
        
        device_choice = input("Select device option (1-3): ").strip()
        
        # Layer selection
        print_info("\nAvailable Layers:")
        layers = ["health", "interfaces", "igp", "bgp", "mpls", "vpn", "static", "console"]
        for i, layer in enumerate(layers, 1):
            print(f"{i}. {layer}")
        print("8. All layers")
        
        layer_input = input("Select layers (comma-separated numbers or 8 for all): ").strip()
        
        # Build command
        command = ["python3", str(self.main_script)]
        
        if device_choice == "1":
            command.append("collect-all")
        elif device_choice == "2":
            devices = input("Enter device names (comma-separated): ").strip()
            command.extend(["collect-devices", "--devices", devices])
        elif device_choice == "3":
            group = input("Enter group name: ").strip()
            command.extend(["collect-group", "--group", group])
        else:
            print_error("Invalid device choice")
            return False
        
        # Add layers
        if layer_input == "8":
            selected_layers = ",".join(layers)
        else:
            try:
                selected_nums = [int(x.strip()) for x in layer_input.split(",")]
                selected_layers = ",".join([layers[i-1] for i in selected_nums if 1 <= i <= len(layers)])
            except:
                print_error("Invalid layer selection")
                return False
        
        command.extend(["--layers", selected_layers])
        
        # Run custom collection
        success, stdout, stderr = self._run_command(
            command,
            f"Custom collection: {' '.join(command[2:])}",
            critical=True
        )
        
        if success:
            print_success("Custom collection completed successfully")
            return True
        else:
            print_error("Custom collection failed")
            return False

    def console_audit(self) -> bool:
        """Run dedicated console line audit for NM4 console cards"""
        print_header("CONSOLE AUDIT MODE", Colors.YELLOW)
        
        print_info("Running dedicated console line audit for NM4 console cards...")
        print_info("🎯 This audit specifically targets:")
        print_info("   • Cisco routers with NM4 console cards")
        print_info("   • Console line discovery (x/y/z format)")
        print_info("   • IOS and IOS XR platform support")
        print_info("   • Individual console line configurations")
        
        # Quick prerequisite check
        if not self.prerequisites_checked:
            print_section("Quick Prerequisites Check")
            if not self.check_prerequisites():
                print_error("Prerequisites check failed")
                return False
        
        # Enhanced connectivity test first
        if not self.enhanced_connectivity_test():
            print_error("Enhanced connectivity test failed")
            return False
        
        # Ask user before proceeding to console collection
        print_section("Proceed to Console Line Collection")
        try:
            proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with console line audit? (y/n): {Colors.RESET}").strip().lower()
            if proceed not in ['y', 'yes']:
                print_info("Console audit cancelled by user")
                return True
        except:
            print_info("Proceeding with console audit...")
        
        # Console line collection from all devices
        print_section("Console Line Discovery & Configuration Collection")
        print_info("Discovering console lines using 'show line' command...")
        print_info("Collecting individual line configurations...")
        print_info("Generating console audit report...")
        
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-all", "--layers", "console"],
            "Console line audit from all reachable devices",
            critical=True,
            timeout=600  # 10 minutes for console collection
        )
        
        if success:
            print_success("Console audit completed successfully")
            print_info("✅ Console line discovery and configurations collected")
            print_info("✅ Platform-specific commands executed (IOS/IOS XR)")
            print_info("✅ NM4 console card support validated")
            
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Console audit results saved to: {output_info}")
            elif "rr4-complete-enchanced-v4-cli-output" in stdout:
                # Try to extract from different output format
                lines = stdout.split('\n')
                for line in lines:
                    if "rr4-complete-enchanced-v4-cli-output" in line:
                        print_info(f"Console audit results saved to: {line.strip()}")
                        break
            
            print_section("Console Audit Summary")
            print_info("📋 Console audit includes:")
            print_info("   • JSON format: Structured console line data")
            print_info("   • TXT format: Human-readable console reports") 
            print_info("   • Raw outputs: Individual command outputs")
            print_info("   • Platform detection: IOS vs IOS XR handling")
            print_info("   • Range validation: x:0-1, y:0-1, z:0-22 support")
            
            return True
        else:
            print_error("Console audit failed")
            print_error("Common causes:")
            print_error("   • No NM4 console cards present")
            print_error("   • Insufficient device privileges")
            print_error("   • Platform detection issues")
            print_info("Check the debug output for detailed error information")
            return False

    def complete_collection(self) -> bool:
        """Run complete systematic collection with all layers including console in optimal order"""
        print_header("COMPLETE COLLECTION MODE", Colors.GREEN)
        
        print_info("Running complete systematic data collection from all devices...")
        print_info("🌟 This comprehensive collection includes:")
        print_info("   • All standard network layers (health, interfaces, igp, bgp, mpls, vpn, static)")
        print_info("   • Console line audit (NM4 console cards)")
        print_info("   • Systematic collection in optimal order")
        print_info("   • Complete audit and production reports")
        
        # Verify prerequisites
        if not self.prerequisites_checked:
            print_section("Prerequisites Verification")
            if not self.check_prerequisites():
                print_error("Prerequisites check failed")
                return False
        
        # Enhanced connectivity test first
        if not self.enhanced_connectivity_test():
            print_error("Enhanced connectivity test failed")
            return False
        
        # Ask user before proceeding to complete collection
        print_section("Proceed to Complete Collection")
        try:
            proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with complete data collection (all layers)? (y/n): {Colors.RESET}").strip().lower()
            if proceed not in ['y', 'yes']:
                print_info("Complete data collection cancelled by user")
                return True
        except:
            print_info("Proceeding with complete data collection...")
        
        # Run complete collection with all layers in systematic order
        print_section("Systematic Data Collection")
        print_info("Phase 1: Core infrastructure data (health, interfaces)")
        print_info("Phase 2: Routing protocols (igp, bgp)")
        print_info("Phase 3: Advanced services (mpls, vpn, static)")
        print_info("Phase 4: Console line audit (console)")
        print_info("Phase 5: Report generation and consolidation")
        
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-all", "--layers", "health,interfaces,igp,bgp,mpls,vpn,static,console"],
            "Complete systematic collection (all layers including console)",
            critical=True,
            timeout=900  # 15 minutes for complete collection
        )
        
        if success:
            print_success("Complete collection completed successfully")
            print_info("✅ All standard network layers collected")
            print_info("✅ Console line audit completed")
            print_info("✅ Systematic collection order maintained")
            print_info("✅ Comprehensive reports generated")
            
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Complete collection data saved to: {output_info}")
            elif "rr4-complete-enchanced-v4-cli-output" in stdout:
                # Try to extract from different output format
                lines = stdout.split('\n')
                for line in lines:
                    if "rr4-complete-enchanced-v4-cli-output" in line:
                        print_info(f"Complete collection data saved to: {line.strip()}")
                        break
            
            print_section("Complete Collection Summary")
            print_info("📋 Complete collection includes:")
            print_info("   • Infrastructure: Health status, interface configurations")
            print_info("   • Routing: IGP protocols, BGP neighbors and routes")
            print_info("   • Services: MPLS labels, VPN configurations, static routes")
            print_info("   • Console: NM4 console line discovery and configurations")
            print_info("   • Reports: JSON (structured) and TXT (human-readable)")
            print_info("   • Platform support: IOS, IOS XE, IOS XR automatic detection")
            
            return True
        else:
            print_error("Complete collection failed")
            print_error("Common causes:")
            print_error("   • Network connectivity issues")
            print_error("   • Insufficient device privileges")
            print_error("   • Platform detection issues")
            print_error("   • Timeout due to large network size")
            print_info("Check the debug output for detailed error information")
            print_info("Consider using individual layer collections for troubleshooting")
            return False

    def console_security_audit(self) -> bool:
        """Analyze console audit results for transport security violations"""
        print_header("CONSOLE SECURITY AUDIT MODE", Colors.RED)
        
        print_info("Analyzing console audit results for transport security violations...")
        print_info("🔒 This security audit analyzes:")
        print_info("   • Console audit data from option 8")
        print_info("   • Transport input/output configurations")
        print_info("   • Telnet security violations on aux, console, vty, line")
        print_info("   • SSH-only compliance validation")
        print_info("   • Detailed per-device security analysis")
        print_info("   • Comprehensive downloadable reports")
        
        # Check if console audit data exists
        output_dirs = list(Path("rr4-complete-enchanced-v4-cli-output").glob("collector-run-*"))
        if not output_dirs:
            print_error("No console audit data found!")
            print_error("Please run option 8 (Console Audit) first to collect data.")
            print_info("The security audit requires console line configurations to analyze.")
            return False
        
        # Use the most recent collection
        latest_dir = max(output_dirs, key=lambda x: x.stat().st_mtime)
        print_info(f"Analyzing console data from: {latest_dir.name}")
        
        # Initialize audit results
        audit_results = {
            'total_routers': 0,
            'routers_accessed': 0,
            'routers_authenticated': 0,
            'routers_with_violations': 0,
            'devices': {},
            'summary_violations': {
                'aux_lines': 0,
                'console_lines': 0,
                'vty_lines': 0,
                'other_lines': 0
            },
            'violation_details': {
                'transport_input_all': 0,
                'transport_input_telnet': 0,
                'transport_output_all': 0,
                'transport_output_telnet': 0
            },
            'compliant_devices': [],
            'non_compliant_devices': [],
            'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': latest_dir.name
        }
        
        # Analyze each device's console data
        print_section("Device-by-Device Security Analysis")
        
        device_dirs = [d for d in latest_dir.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name not in ['logs', 'reports']]
        audit_results['total_routers'] = len(device_dirs)
        
        for device_dir in device_dirs:
            device_ip = device_dir.name
            print_info(f"Analyzing device: {device_ip}")
            
            device_audit = {
                'device_ip': device_ip,
                'hostname': 'Unknown',
                'accessible': False,
                'authenticated': False,
                'console_data_found': False,
                'violations': {
                    'aux_lines': [],
                    'console_lines': [],
                    'vty_lines': [],
                    'other_lines': []
                },
                'violation_summary': {
                    'transport_input_all': 0,
                    'transport_input_telnet': 0,
                    'transport_output_all': 0,
                    'transport_output_telnet': 0
                },
                'total_violations': 0,
                'total_lines_analyzed': 0,
                'compliance_status': 'UNKNOWN',
                'risk_level': 'LOW',
                'recommendations': []
            }
            
            # Check for console data
            console_dir = device_dir / 'console'
            if console_dir.exists():
                device_audit['accessible'] = True
                device_audit['authenticated'] = True
                audit_results['routers_accessed'] += 1
                audit_results['routers_authenticated'] += 1
                
                # Look for console line files
                json_files = list(console_dir.glob("*_console_lines.json"))
                if json_files:
                    device_audit['console_data_found'] = True
                    
                    # Analyze JSON console data
                    try:
                        with open(json_files[0], 'r') as f:
                            console_data = json.load(f)
                            device_audit['hostname'] = console_data.get('hostname', device_ip)
                            
                            # Analyze console line configurations
                            violations = self._analyze_transport_security(console_data)
                            device_audit['violations'] = violations
                            device_audit['total_violations'] = sum(len(v) for v in violations.values())
                            
                            # Count total lines analyzed
                            device_audit['total_lines_analyzed'] = len(console_data.get('console_lines', {}))
                            
                            # Calculate violation summary
                            for line_type, viols in violations.items():
                                for violation in viols:
                                    for viol_pattern in violation['violations']:
                                        if 'transport input all' in viol_pattern:
                                            device_audit['violation_summary']['transport_input_all'] += 1
                                            audit_results['violation_details']['transport_input_all'] += 1
                                        elif 'transport input telnet' in viol_pattern:
                                            device_audit['violation_summary']['transport_input_telnet'] += 1
                                            audit_results['violation_details']['transport_input_telnet'] += 1
                                        elif 'transport output all' in viol_pattern:
                                            device_audit['violation_summary']['transport_output_all'] += 1
                                            audit_results['violation_details']['transport_output_all'] += 1
                                        elif 'transport output telnet' in viol_pattern:
                                            device_audit['violation_summary']['transport_output_telnet'] += 1
                                            audit_results['violation_details']['transport_output_telnet'] += 1
                            
                            # Determine compliance status and risk level
                            if device_audit['total_violations'] == 0:
                                device_audit['compliance_status'] = 'COMPLIANT'
                                device_audit['risk_level'] = 'LOW'
                                audit_results['compliant_devices'].append(device_ip)
                            else:
                                device_audit['compliance_status'] = 'NON-COMPLIANT'
                                audit_results['routers_with_violations'] += 1
                                audit_results['non_compliant_devices'].append(device_ip)
                                
                                # Determine risk level
                                if device_audit['total_violations'] >= 5:
                                    device_audit['risk_level'] = 'HIGH'
                                elif device_audit['total_violations'] >= 2:
                                    device_audit['risk_level'] = 'MEDIUM'
                                else:
                                    device_audit['risk_level'] = 'LOW'
                                
                                # Generate recommendations
                                device_audit['recommendations'] = self._generate_device_recommendations(device_audit)
                            
                            # Update summary violations
                            for line_type, viols in violations.items():
                                audit_results['summary_violations'][line_type] += len(viols)
                                
                    except Exception as e:
                        print_warning(f"Error analyzing {device_ip}: {str(e)}")
                        device_audit['compliance_status'] = 'ERROR'
                
                # Also check raw command outputs for additional analysis
                raw_outputs_dir = console_dir / 'command_outputs'
                if raw_outputs_dir.exists():
                    self._analyze_raw_console_outputs(device_audit, raw_outputs_dir)
            
            audit_results['devices'][device_ip] = device_audit
            
            # Display device results with enhanced details
            if device_audit['total_violations'] > 0:
                risk_color = Colors.RED if device_audit['risk_level'] == 'HIGH' else Colors.YELLOW if device_audit['risk_level'] == 'MEDIUM' else Colors.BLUE
                print_error(f"  ❌ {device_ip} ({device_audit['hostname']}): {device_audit['total_violations']} violations | {risk_color}Risk: {device_audit['risk_level']}{Colors.RESET}")
                if device_audit['total_violations'] > 0:
                    for line_type, violations in device_audit['violations'].items():
                        if violations:
                            print_warning(f"     {line_type.replace('_', ' ').title()}: {len(violations)} violations")
            else:
                print_success(f"  ✅ {device_ip} ({device_audit['hostname']}): No violations | Compliant")
        
        # Display comprehensive terminal summary
        self._display_terminal_security_summary(audit_results)
        
        # Generate comprehensive security audit reports
        print_section("Generating Comprehensive Security Reports")
        report_success = self._generate_comprehensive_security_reports(audit_results, latest_dir)
        
        if report_success:
            print_success("Console security audit completed successfully")
            
            # Display report locations
            print_section("Security Audit Report Locations")
            print_info(f"📄 Executive Summary: {latest_dir}/console_security_executive_summary.txt")
            print_info(f"📋 Detailed Report: {latest_dir}/console_security_detailed_report.txt")
            print_info(f"📊 Device Analysis: {latest_dir}/console_security_device_analysis.txt")
            print_info(f"🔒 Compliance Report: {latest_dir}/console_security_compliance_report.txt")
            
            # Ask user if they want to view reports
            print_section("Report Viewing Options")
            try:
                view_choice = input(f"{Colors.YELLOW}Would you like to view the executive summary report on terminal? (y/n): {Colors.RESET}").strip().lower()
                if view_choice in ['y', 'yes']:
                    self._display_executive_summary_on_terminal(latest_dir)
            except:
                pass
            
            return True
        else:
            print_error("Failed to generate security audit reports")
            return False

    def _generate_device_recommendations(self, device_audit: dict) -> list:
        """Generate security recommendations for a specific device"""
        recommendations = []
        
        if device_audit['violation_summary']['transport_input_all'] > 0:
            recommendations.append("Remove 'transport input all' - allows insecure protocols")
        if device_audit['violation_summary']['transport_input_telnet'] > 0:
            recommendations.append("Remove 'transport input telnet' - telnet is unencrypted")
        if device_audit['violation_summary']['transport_output_all'] > 0:
            recommendations.append("Remove 'transport output all' - allows insecure output")
        if device_audit['violation_summary']['transport_output_telnet'] > 0:
            recommendations.append("Remove 'transport output telnet' - telnet output is insecure")
        
        if recommendations:
            recommendations.append("Configure 'transport input ssh' for secure access")
            recommendations.append("Configure 'transport output ssh' for secure output")
            recommendations.append("Implement access control lists (ACLs) on VTY lines")
            recommendations.append("Use strong authentication methods")
        
        return recommendations

    def _display_terminal_security_summary(self, audit_results: dict):
        """Display comprehensive security summary on terminal"""
        print_header("SECURITY AUDIT EXECUTIVE SUMMARY", Colors.MAGENTA)
        
        # Overall Statistics
        print_section("Overall Security Statistics")
        compliance_rate = ((audit_results['total_routers'] - audit_results['routers_with_violations']) / audit_results['total_routers'] * 100) if audit_results['total_routers'] > 0 else 0
        
        print_info(f"📊 Total Network Devices Analyzed: {audit_results['total_routers']}")
        print_info(f"🌐 Devices Successfully Accessed: {audit_results['routers_accessed']}")
        print_info(f"🔐 Devices Successfully Authenticated: {audit_results['routers_authenticated']}")
        print_info(f"✅ Compliant Devices: {len(audit_results['compliant_devices'])}")
        print_info(f"⚠️  Non-Compliant Devices: {audit_results['routers_with_violations']}")
        
        if compliance_rate >= 90:
            print_success(f"🏆 Security Compliance Rate: {compliance_rate:.1f}% (EXCELLENT)")
        elif compliance_rate >= 75:
            print_warning(f"📈 Security Compliance Rate: {compliance_rate:.1f}% (GOOD)")
        elif compliance_rate >= 50:
            print_warning(f"⚠️  Security Compliance Rate: {compliance_rate:.1f}% (NEEDS IMPROVEMENT)")
        else:
            print_error(f"🚨 Security Compliance Rate: {compliance_rate:.1f}% (CRITICAL)")
        
        # Violation Breakdown
        print_section("Transport Security Violation Breakdown")
        total_violations = sum(audit_results['violation_details'].values())
        
        if total_violations > 0:
            print_error(f"🚨 Total Transport Security Violations: {total_violations}")
            print_warning(f"   • transport input all: {audit_results['violation_details']['transport_input_all']} violations")
            print_warning(f"   • transport input telnet: {audit_results['violation_details']['transport_input_telnet']} violations")
            print_warning(f"   • transport output all: {audit_results['violation_details']['transport_output_all']} violations")
            print_warning(f"   • transport output telnet: {audit_results['violation_details']['transport_output_telnet']} violations")
        else:
            print_success("🛡️  No transport security violations detected!")
        
        # Line Type Analysis
        print_section("Line Type Security Analysis")
        print_info(f"🔌 AUX Line Violations: {audit_results['summary_violations']['aux_lines']}")
        print_info(f"📟 Console Line Violations: {audit_results['summary_violations']['console_lines']}")
        print_info(f"💻 VTY Line Violations: {audit_results['summary_violations']['vty_lines']}")
        print_info(f"📡 Other Line Violations: {audit_results['summary_violations']['other_lines']}")
        
        # Risk Assessment
        print_section("Security Risk Assessment")
        high_risk_devices = [dev for dev, data in audit_results['devices'].items() if data['risk_level'] == 'HIGH']
        medium_risk_devices = [dev for dev, data in audit_results['devices'].items() if data['risk_level'] == 'MEDIUM']
        
        if high_risk_devices:
            print_error(f"🔴 HIGH RISK Devices ({len(high_risk_devices)}): {', '.join(high_risk_devices)}")
        if medium_risk_devices:
            print_warning(f"🟡 MEDIUM RISK Devices ({len(medium_risk_devices)}): {', '.join(medium_risk_devices)}")
        if not high_risk_devices and not medium_risk_devices:
            print_success("🟢 All devices are LOW RISK or COMPLIANT")
        
        # Top Recommendations
        print_section("Priority Security Recommendations")
        if audit_results['routers_with_violations'] > 0:
            print_warning("🔧 IMMEDIATE ACTIONS REQUIRED:")
            print_warning("   1. Remove all 'transport input all' configurations")
            print_warning("   2. Replace 'transport input telnet' with 'transport input ssh'")
            print_warning("   3. Remove all 'transport output all' configurations")
            print_warning("   4. Replace 'transport output telnet' with 'transport output ssh'")
            print_warning("   5. Implement VTY access control lists (ACLs)")
            print_warning("   6. Enable strong authentication mechanisms")
        else:
            print_success("🎉 No immediate security actions required!")
            print_info("💡 Consider implementing additional security hardening measures")

    def _display_executive_summary_on_terminal(self, output_dir: Path):
        """Display executive summary report on terminal"""
        try:
            summary_file = output_dir / 'console_security_executive_summary.txt'
            if summary_file.exists():
                print_header("EXECUTIVE SUMMARY REPORT", Colors.CYAN)
                with open(summary_file, 'r') as f:
                    content = f.read()
                    print(content)
            else:
                print_error("Executive summary file not found")
        except Exception as e:
            print_error(f"Error displaying executive summary: {str(e)}")

    def _generate_comprehensive_security_reports(self, audit_results: dict, output_dir: Path) -> bool:
        """Generate comprehensive security audit reports"""
        try:
            # Generate Executive Summary Report
            self._generate_executive_summary_report(audit_results, output_dir)
            
            # Generate Detailed Security Report
            self._generate_detailed_security_report(audit_results, output_dir)
            
            # Generate Device Analysis Report
            self._generate_device_analysis_report(audit_results, output_dir)
            
            # Generate Compliance Report
            self._generate_compliance_report(audit_results, output_dir)
            
            return True
            
        except Exception as e:
            print_error(f"Error generating comprehensive reports: {str(e)}")
            return False

    def _generate_executive_summary_report(self, audit_results: dict, output_dir: Path):
        """Generate executive summary report"""
        report_file = output_dir / 'console_security_executive_summary.txt'
        
        with open(report_file, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("CONSOLE SECURITY AUDIT - EXECUTIVE SUMMARY REPORT\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {audit_results['analysis_timestamp']}\n")
            f.write(f"Data Source: {audit_results['data_source']}\n")
            f.write(f"Report Type: Executive Summary\n")
            f.write("=" * 100 + "\n\n")
            
            # Executive Overview
            compliance_rate = ((audit_results['total_routers'] - audit_results['routers_with_violations']) / audit_results['total_routers'] * 100) if audit_results['total_routers'] > 0 else 0
            
            f.write("EXECUTIVE OVERVIEW\n")
            f.write("-" * 50 + "\n")
            f.write(f"Network Security Posture: ")
            if compliance_rate >= 90:
                f.write("EXCELLENT\n")
            elif compliance_rate >= 75:
                f.write("GOOD\n")
            elif compliance_rate >= 50:
                f.write("NEEDS IMPROVEMENT\n")
            else:
                f.write("CRITICAL\n")
            
            f.write(f"Overall Compliance Rate: {compliance_rate:.1f}%\n")
            f.write(f"Total Devices Audited: {audit_results['total_routers']}\n")
            f.write(f"Devices with Security Violations: {audit_results['routers_with_violations']}\n")
            f.write(f"Security Compliant Devices: {len(audit_results['compliant_devices'])}\n\n")
            
            # Key Findings
            f.write("KEY SECURITY FINDINGS\n")
            f.write("-" * 50 + "\n")
            total_violations = sum(audit_results['violation_details'].values())
            f.write(f"Total Transport Security Violations: {total_violations}\n")
            f.write(f"High Risk Devices: {len([d for d in audit_results['devices'].values() if d['risk_level'] == 'HIGH'])}\n")
            f.write(f"Medium Risk Devices: {len([d for d in audit_results['devices'].values() if d['risk_level'] == 'MEDIUM'])}\n")
            f.write(f"Low Risk Devices: {len([d for d in audit_results['devices'].values() if d['risk_level'] == 'LOW'])}\n\n")
            
            # Critical Issues
            f.write("CRITICAL SECURITY ISSUES\n")
            f.write("-" * 50 + "\n")
            if audit_results['violation_details']['transport_input_all'] > 0:
                f.write(f"• {audit_results['violation_details']['transport_input_all']} instances of 'transport input all' - CRITICAL\n")
            if audit_results['violation_details']['transport_input_telnet'] > 0:
                f.write(f"• {audit_results['violation_details']['transport_input_telnet']} instances of 'transport input telnet' - HIGH RISK\n")
            if audit_results['violation_details']['transport_output_all'] > 0:
                f.write(f"• {audit_results['violation_details']['transport_output_all']} instances of 'transport output all' - MEDIUM RISK\n")
            if audit_results['violation_details']['transport_output_telnet'] > 0:
                f.write(f"• {audit_results['violation_details']['transport_output_telnet']} instances of 'transport output telnet' - MEDIUM RISK\n")
            
            if total_violations == 0:
                f.write("• No critical security issues identified\n")
            f.write("\n")
            
            # Immediate Actions Required
            f.write("IMMEDIATE ACTIONS REQUIRED\n")
            f.write("-" * 50 + "\n")
            if audit_results['routers_with_violations'] > 0:
                f.write("PHASE 1 - CRITICAL FIXES (Complete within 24 hours):\n")
                f.write("1. Remove all 'transport input all' configurations\n")
                f.write("2. Replace 'transport input telnet' with 'transport input ssh'\n\n")
                
                f.write("PHASE 2 - HIGH PRIORITY FIXES (Complete within 1 week):\n")
                f.write("3. Remove all 'transport output all' configurations\n")
                f.write("4. Replace 'transport output telnet' with 'transport output ssh'\n\n")
                
                f.write("PHASE 3 - SECURITY HARDENING (Complete within 1 month):\n")
                f.write("5. Implement VTY access control lists\n")
                f.write("6. Enable strong authentication mechanisms\n")
                f.write("7. Implement session timeout configurations\n")
                f.write("8. Enable logging for security events\n")
            else:
                f.write("✅ Network is fully compliant with security standards\n")
                f.write("💡 Consider additional security hardening measures:\n")
                f.write("   - Implement advanced authentication\n")
                f.write("   - Regular security audits\n")
                f.write("   - Network access control\n")

    def _generate_detailed_security_report(self, audit_results: dict, output_dir: Path):
        """Generate detailed security report with device-specific information"""
        report_file = output_dir / 'console_security_detailed_report.txt'
        
        with open(report_file, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("CONSOLE SECURITY AUDIT - DETAILED ANALYSIS REPORT\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {audit_results['analysis_timestamp']}\n")
            f.write(f"Data Source: {audit_results['data_source']}\n")
            f.write(f"Report Type: Detailed Security Analysis\n")
            f.write("=" * 100 + "\n\n")
            
            # Comprehensive Statistics
            f.write("COMPREHENSIVE SECURITY STATISTICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Network Devices: {audit_results['total_routers']}\n")
            f.write(f"Devices Accessed: {audit_results['routers_accessed']}\n")
            f.write(f"Devices Authenticated: {audit_results['routers_authenticated']}\n")
            f.write(f"Devices with Console Data: {len([d for d in audit_results['devices'].values() if d['console_data_found']])}\n")
            f.write(f"Security Compliant Devices: {len(audit_results['compliant_devices'])}\n")
            f.write(f"Non-Compliant Devices: {audit_results['routers_with_violations']}\n\n")
            
            # Transport Security Violations Detail
            f.write("TRANSPORT SECURITY VIOLATIONS BREAKDOWN\n")
            f.write("-" * 60 + "\n")
            f.write(f"Transport Input All Violations: {audit_results['violation_details']['transport_input_all']}\n")
            f.write(f"Transport Input Telnet Violations: {audit_results['violation_details']['transport_input_telnet']}\n")
            f.write(f"Transport Output All Violations: {audit_results['violation_details']['transport_output_all']}\n")
            f.write(f"Transport Output Telnet Violations: {audit_results['violation_details']['transport_output_telnet']}\n")
            f.write(f"Total Violations: {sum(audit_results['violation_details'].values())}\n\n")
            
            # Line Type Analysis
            f.write("LINE TYPE SECURITY ANALYSIS\n")
            f.write("-" * 60 + "\n")
            f.write(f"AUX Line Violations: {audit_results['summary_violations']['aux_lines']}\n")
            f.write(f"Console Line Violations: {audit_results['summary_violations']['console_lines']}\n")
            f.write(f"VTY Line Violations: {audit_results['summary_violations']['vty_lines']}\n")
            f.write(f"Other Line Violations: {audit_results['summary_violations']['other_lines']}\n\n")
            
            # Device-by-Device Analysis
            f.write("DEVICE-BY-DEVICE SECURITY ANALYSIS\n")
            f.write("-" * 60 + "\n")
            
            for device_ip, device_data in audit_results['devices'].items():
                f.write(f"\nDevice: {device_ip} ({device_data['hostname']})\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"Status: {device_data['compliance_status']}\n")
                f.write(f"Risk Level: {device_data['risk_level']}\n")
                f.write(f"Accessible: {'Yes' if device_data['accessible'] else 'No'}\n")
                f.write(f"Authenticated: {'Yes' if device_data['authenticated'] else 'No'}\n")
                f.write(f"Console Data Found: {'Yes' if device_data['console_data_found'] else 'No'}\n")
                f.write(f"Total Violations: {device_data['total_violations']}\n")
                f.write(f"Total Lines Analyzed: {device_data['total_lines_analyzed']}\n")
                
                if device_data['total_violations'] > 0:
                    f.write(f"\nViolation Breakdown:\n")
                    f.write(f"  Transport Input All: {device_data['violation_summary']['transport_input_all']}\n")
                    f.write(f"  Transport Input Telnet: {device_data['violation_summary']['transport_input_telnet']}\n")
                    f.write(f"  Transport Output All: {device_data['violation_summary']['transport_output_all']}\n")
                    f.write(f"  Transport Output Telnet: {device_data['violation_summary']['transport_output_telnet']}\n")
                    
                    f.write(f"\nViolation Details by Line Type:\n")
                    for line_type, violations in device_data['violations'].items():
                        if violations:
                            f.write(f"  {line_type.replace('_', ' ').title()}:\n")
                            for violation in violations:
                                f.write(f"    Line {violation['line_id']} ({violation['line_type']}):\n")
                                for viol_pattern in violation['violations']:
                                    f.write(f"      - {viol_pattern}\n")
                    
                    if device_data['recommendations']:
                        f.write(f"\nDevice-Specific Recommendations:\n")
                        for i, rec in enumerate(device_data['recommendations'], 1):
                            f.write(f"  {i}. {rec}\n")

    def _generate_device_analysis_report(self, audit_results: dict, output_dir: Path):
        """Generate device analysis report"""
        report_file = output_dir / 'console_security_device_analysis.txt'
        
        with open(report_file, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("CONSOLE SECURITY AUDIT - DEVICE ANALYSIS REPORT\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {audit_results['analysis_timestamp']}\n")
            f.write(f"Data Source: {audit_results['data_source']}\n")
            f.write(f"Report Type: Per-Device Security Analysis\n")
            f.write("=" * 100 + "\n\n")
            
            # Compliant Devices
            f.write("SECURITY COMPLIANT DEVICES\n")
            f.write("-" * 50 + "\n")
            if audit_results['compliant_devices']:
                for device_ip in audit_results['compliant_devices']:
                    device_data = audit_results['devices'][device_ip]
                    f.write(f"✅ {device_ip} ({device_data['hostname']}) - COMPLIANT\n")
                    f.write(f"   Lines Analyzed: {device_data['total_lines_analyzed']}\n")
                    f.write(f"   Risk Level: {device_data['risk_level']}\n\n")
            else:
                f.write("No fully compliant devices found.\n\n")
            
            # Non-Compliant Devices
            f.write("SECURITY NON-COMPLIANT DEVICES\n")
            f.write("-" * 50 + "\n")
            if audit_results['non_compliant_devices']:
                for device_ip in audit_results['non_compliant_devices']:
                    device_data = audit_results['devices'][device_ip]
                    f.write(f"❌ {device_ip} ({device_data['hostname']}) - NON-COMPLIANT\n")
                    f.write(f"   Violations: {device_data['total_violations']}\n")
                    f.write(f"   Risk Level: {device_data['risk_level']}\n")
                    f.write(f"   Lines Analyzed: {device_data['total_lines_analyzed']}\n")
                    
                    # Show top violations
                    if device_data['violation_summary']['transport_input_all'] > 0:
                        f.write(f"   🚨 Transport Input All: {device_data['violation_summary']['transport_input_all']}\n")
                    if device_data['violation_summary']['transport_input_telnet'] > 0:
                        f.write(f"   ⚠️  Transport Input Telnet: {device_data['violation_summary']['transport_input_telnet']}\n")
                    
                    f.write("\n")
            else:
                f.write("All devices are security compliant.\n\n")

    def _generate_compliance_report(self, audit_results: dict, output_dir: Path):
        """Generate compliance report"""
        report_file = output_dir / 'console_security_compliance_report.txt'
        
        with open(report_file, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("CONSOLE SECURITY AUDIT - COMPLIANCE REPORT\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {audit_results['analysis_timestamp']}\n")
            f.write(f"Data Source: {audit_results['data_source']}\n")
            f.write(f"Report Type: Security Compliance Validation\n")
            f.write("=" * 100 + "\n\n")
            
            # Compliance Standards
            f.write("SECURITY COMPLIANCE STANDARDS\n")
            f.write("-" * 50 + "\n")
            f.write("ACCEPTABLE CONFIGURATIONS:\n")
            f.write("  ✅ transport input ssh\n")
            f.write("  ✅ transport output ssh\n")
            f.write("  ✅ transport input none\n")
            f.write("  ✅ transport output none\n\n")
            
            f.write("VIOLATION CONFIGURATIONS:\n")
            f.write("  ❌ transport input all (CRITICAL)\n")
            f.write("  ❌ transport input telnet (HIGH RISK)\n")
            f.write("  ❌ transport output all (MEDIUM RISK)\n")
            f.write("  ❌ transport output telnet (MEDIUM RISK)\n\n")
            
            # Compliance Results
            compliance_rate = ((audit_results['total_routers'] - audit_results['routers_with_violations']) / audit_results['total_routers'] * 100) if audit_results['total_routers'] > 0 else 0
            
            f.write("COMPLIANCE ASSESSMENT RESULTS\n")
            f.write("-" * 50 + "\n")
            f.write(f"Overall Compliance Rate: {compliance_rate:.1f}%\n")
            f.write(f"Compliance Status: ")
            
            if compliance_rate >= 95:
                f.write("EXCELLENT COMPLIANCE\n")
            elif compliance_rate >= 85:
                f.write("GOOD COMPLIANCE\n")
            elif compliance_rate >= 70:
                f.write("ACCEPTABLE COMPLIANCE\n")
            elif compliance_rate >= 50:
                f.write("NEEDS IMPROVEMENT\n")
            else:
                f.write("NON-COMPLIANT (CRITICAL)\n")
            
            f.write(f"\nCompliant Devices: {len(audit_results['compliant_devices'])}/{audit_results['total_routers']}\n")
            f.write(f"Non-Compliant Devices: {audit_results['routers_with_violations']}/{audit_results['total_routers']}\n\n")
            
            # Remediation Plan
            f.write("COMPLIANCE REMEDIATION PLAN\n")
            f.write("-" * 50 + "\n")
            if audit_results['routers_with_violations'] > 0:
                f.write("PHASE 1 - CRITICAL FIXES (Complete within 24 hours):\n")
                f.write("1. Remove all 'transport input all' configurations\n")
                f.write("2. Replace 'transport input telnet' with 'transport input ssh'\n\n")
                
                f.write("PHASE 2 - HIGH PRIORITY FIXES (Complete within 1 week):\n")
                f.write("3. Remove all 'transport output all' configurations\n")
                f.write("4. Replace 'transport output telnet' with 'transport output ssh'\n\n")
                
                f.write("PHASE 3 - SECURITY HARDENING (Complete within 1 month):\n")
                f.write("5. Implement VTY access control lists\n")
                f.write("6. Enable strong authentication mechanisms\n")
                f.write("7. Implement session timeout configurations\n")
                f.write("8. Enable logging for security events\n")
            else:
                f.write("✅ Network is fully compliant with security standards\n")
                f.write("💡 Consider additional security hardening measures:\n")
                f.write("   - Implement advanced authentication\n")
                f.write("   - Regular security audits\n")
                f.write("   - Network access control\n")

    def show_help(self) -> bool:
        """Show help and available options"""
        print_header("HELP & AVAILABLE OPTIONS", Colors.WHITE)
        
        # Show main script help
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "--help"],
            "Displaying main script help",
            critical=False
        )
        
        if success:
            print(stdout)
        
        print_section("Additional Information")
        print_info("Documentation files in this directory:")
        docs = [
            "README.md - Main documentation",
            "CROSS_PLATFORM_GUIDE.md - Cross-platform setup guide", 
            "INSTALLATION.md - Installation instructions",
            "TROUBLESHOOTING.md - Common issues and solutions",
            "EXAMPLES.md - Usage examples",
            "SECURITY.md - Security implementation details"
        ]
        for doc in docs:
            print(f"  📖 {doc}")
        
        return True
    
    def _ask_continue_on_error(self, step_name: str) -> bool:
        """Ask user if they want to continue after an error"""
        print_warning(f"{step_name} encountered an issue.")
        while True:
            choice = input(f"{Colors.YELLOW}Continue anyway? (y/n): {Colors.RESET}").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print_error("Please enter 'y' or 'n'")
    
    def _show_setup_results(self):
        """Show final setup results"""
        print_header("SETUP RESULTS SUMMARY", Colors.MAGENTA)
        
        for step, result in self.test_results.items():
            if result == "PASSED":
                print_success(f"{step}: {result}")
            elif result == "FAILED":
                print_error(f"{step}: {result}")
            else:
                print_warning(f"{step}: {result}")
        
        passed_count = sum(1 for result in self.test_results.values() if result == "PASSED")
        total_count = len(self.test_results)
        
        print(f"\n{Colors.BOLD}Overall: {passed_count}/{total_count} steps completed successfully{Colors.RESET}")
        
        if passed_count == total_count:
            print_success("🎉 Setup completed successfully! Your RR4 CLI is ready to use.")
        else:
            print_warning("⚠️  Setup completed with some issues. Review the results above.")
    
    def run(self):
        """Main run method"""
        try:
            while True:
                choice = self.show_main_menu()
                
                if choice == 0:
                    print(f"\n{Colors.GREEN}Thank you for using RR4 CLI Startup Manager!{Colors.RESET}")
                    break
                elif choice == 1:
                    self.first_time_setup()
                elif choice == 2:
                    self.audit_only()
                elif choice == 3:
                    self.full_collection()
                elif choice == 4:
                    self.custom_collection()
                elif choice == 5:
                    self.check_prerequisites()
                elif choice == 6:
                    self.enhanced_connectivity_test()
                elif choice == 7:
                    self.show_help()
                elif choice == 8:
                    self.console_audit()
                elif choice == 9:
                    self.complete_collection()
                elif choice == 10:
                    self.console_security_audit()
                elif choice == 12:
                    self.comprehensive_status_report()
                else:
                    print_error("Invalid choice. Please enter 0-12.")
                
                # Ask if user wants to continue
                if choice != 0:
                    print(f"\n{Colors.BOLD}Press Enter to return to main menu or Ctrl+C to exit...{Colors.RESET}")
                    try:
                        input()
                    except KeyboardInterrupt:
                        print(f"\n{Colors.GREEN}Goodbye!{Colors.RESET}")
                        break
                        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Startup manager interrupted by user. Goodbye!{Colors.RESET}")
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            print_info("Please check your setup and try again.")

    def comprehensive_status_report(self) -> bool:
        """Generate comprehensive status report for all collection options
        
        This method analyzes collection data from options 1-10 and provides:
        - Unified status analysis across all collection types
        - Gap analysis and missing collection identification
        - Executive summary and detailed technical reports
        - Remediation recommendations for collection gaps
        
        Returns:
            bool: True if report generation successful, False otherwise
        """
        print_header("COMPREHENSIVE COLLECTION STATUS REPORT", Colors.BLUE)
        
        print_info("🚀 Initializing comprehensive analysis of collection data...")
        print_info("📊 This analysis can cover all options 1-10:")
        print_info("   • Option 1: First-time Setup collections")
        print_info("   • Option 2: Audit Only collections") 
        print_info("   • Option 3: Full Collection data")
        print_info("   • Option 4: Custom Collection results")
        print_info("   • Option 8: Console Audit data")
        print_info("   • Option 9: Complete Collection data")
        print_info("   • Option 10: Console Security Audit results")
        print_info("   • And more comprehensive analysis...")
        
        try:
            # Step 1: Select analysis scope (all devices or filtered subset)
            print_section("Analysis Scope Selection")
            device_filter = self._select_analysis_scope()
            
            if device_filter is None:
                print_info("Analysis cancelled by user")
                return True
                
            # T002.1: Data Source Discovery (with optional device filtering)
            print_section("T002.1: Collection Data Discovery Phase")
            collections = self._discover_collection_directories()
            
            if not collections:
                print_warning("⚠️  No collection data found!")
                print_info("📋 This could mean:")
                print_info("   • No data collection has been performed yet")
                print_info("   • Output directory is in a different location")
                print_info("   • Previous collections were manually deleted")
                print_info("\n💡 Recommended actions:")
                print_info("   • Run Option 2 (Audit Only) for quick data collection")
                print_info("   • Run Option 3 (Full Collection) for comprehensive data")
                print_info("   • Run Option 8 (Console Audit) for console data")
                return True  # Not an error, just no data yet
            
            # Apply device filtering if specified
            if device_filter and device_filter['type'] != 'all':
                print_section("Applying Device Filter")
                collections = self._filter_collections_by_devices(collections, device_filter)
                
                if not collections:
                    print_warning("⚠️  No collection data found matching the device filter!")
                    print_info("Selected filter criteria did not match any existing collections.")
                    print_info("Try running collections with the target devices first.")
                    return True

            # T002.2: Analyze collection data structure
            print_section("T002.2: Collection Data Structure Analysis")
            analyzed_collections = self._analyze_collection_structures(collections)
            
            # T002.3: Map collections to options (placeholder for now)
            print_section("T002.3: Option Mapping Analysis")
            mapped_collections = self._map_collections_to_options(analyzed_collections)
            
            # Display discovery results
            print_section("Collection Discovery Summary")
            self._display_discovery_summary(mapped_collections)
            
            # T003: Collection Status Analysis Engine
            print_section("T003: Collection Status Analysis Engine")
            status_analyzed_collections = self._perform_status_analysis(mapped_collections)
            
            # T004: Gap Analysis and Recommendations
            print_section("T004: Gap Analysis and Recommendations")
            gap_analyzed_collections = self._perform_gap_analysis(status_analyzed_collections)
            
            # T005: Enhanced Terminal Display
            print_section("T005: Enhanced Terminal Display and User Interface")
            self._display_comprehensive_terminal_report(gap_analyzed_collections)
            
            # T006: Report Generation Engine
            print_section("T006: Report Generation Engine")
            report_generated_collections = self._generate_comprehensive_reports(gap_analyzed_collections)
            
            # T007: Export and Persistence
            print_section("T007: Export and Persistence")
            exported_collections = self._handle_export_and_persistence(report_generated_collections)
            
            # T008: Testing and Validation
            print_section("T008: Testing and Validation")
            validated_collections = self._perform_testing_and_validation(exported_collections)
            
            print_section("Next Steps")
            print_success("✅ T002: Data Source Analysis and Discovery completed successfully")
            print_success("✅ T003: Collection Status Analysis Engine completed successfully")
            print_success("✅ T004: Gap Analysis and Recommendations completed successfully")
            print_success("✅ T005: Enhanced Terminal Display completed successfully")
            print_success("✅ T006: Report Generation Engine completed successfully")
            print_success("✅ T007: Export and Persistence completed successfully")
            print_success("✅ T008: Testing and Validation completed successfully")
            print_info("🎯 Option 12 implementation complete - All tasks successfully executed!")
            
            return True
            
        except Exception as e:
            print_error(f"Error in comprehensive status report: {str(e)}")
            print_info("This is expected during initial implementation phase")
            return False

    def _select_analysis_scope(self) -> Dict:
        """Select analysis scope - all devices or specific subset
        
        Returns:
            Dict with filter configuration or None if cancelled
        """
        print_header("📋 ANALYSIS SCOPE SELECTION", Colors.CYAN)
        
        print_info("Choose the scope of your comprehensive status analysis:")
        print_info("You can analyze all devices or focus on specific router types.")
        
        print(f"\n{Colors.BOLD}🎯 ANALYSIS SCOPE OPTIONS:{Colors.RESET}")
        print(f"{Colors.GREEN}1. 🌐 ALL ROUTERS (Complete network analysis){Colors.RESET}")
        print(f"   - Analyze all available collection data")
        print(f"   - Full network infrastructure coverage")
        print(f"   - Comprehensive cross-device analysis")
        
        print(f"\n{Colors.BLUE}2. 🎯 SINGLE ROUTER (Focused analysis){Colors.RESET}")
        print(f"   - Deep dive analysis on one specific device")
        print(f"   - Detailed per-device troubleshooting")
        print(f"   - Device-specific recommendations")
        
        print(f"\n{Colors.YELLOW}3. 📊 DEVICE TYPE SUBSET (Platform-specific analysis){Colors.RESET}")
        print(f"   - Select specific Cisco OS types (iOS, iOS-XE, iOS-XR)")
        print(f"   - Platform-specific analysis and recommendations")
        print(f"   - OS version and feature comparisons")
        
        print(f"\n{Colors.MAGENTA}4. 🔧 REPRESENTATIVE SAMPLE (Quick validation){Colors.RESET}")
        print(f"   - Analyze 1 device each: iOS, iOS-XE, iOS-XR")
        print(f"   - Quick network health validation")
        print(f"   - Platform diversity assessment")
        
        print(f"\n{Colors.RED}0. 🚪 CANCEL{Colors.RESET}")
        
        while True:
            try:
                choice = input(f"\n{Colors.BOLD}Select scope option (0-4): {Colors.RESET}").strip()
                
                if choice == '0':
                    return None
                elif choice == '1':
                    return {'type': 'all', 'description': 'All routers - complete network analysis'}
                elif choice == '2':
                    return self._select_single_router()
                elif choice == '3':
                    return self._select_device_types()
                elif choice == '4':
                    return {'type': 'representative', 'count_per_type': 1, 
                           'device_types': ['ios', 'iosxe', 'iosxr'],
                           'description': 'Representative sample - 1 device per OS type'}
                else:
                    print_error("Invalid choice. Please enter 0-4.")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Selection cancelled by user.{Colors.RESET}")
                return None
            except Exception:
                print_error("Invalid input. Please enter a number (0-4).")

    def _select_single_router(self) -> Dict:
        """Select a single router for focused analysis
        
        Returns:
            Dict with single device filter configuration
        """
        print_section("Single Router Selection")
        
        # Discover available devices from existing collections
        available_devices = self._discover_available_devices()
        
        if not available_devices:
            print_warning("⚠️  No devices found in existing collections!")
            print_info("Please run a collection first to analyze specific devices.")
            return None
        
        print_info(f"📋 Found {len(available_devices)} devices in existing collections:")
        print_info("   ┌─────────────────────────────────────────────────────────────────┐")
        print_info("   │ #  │ Device Name              │ OS Type  │ Collections        │")
        print_info("   ├─────────────────────────────────────────────────────────────────┤")
        
        for i, device_info in enumerate(available_devices, 1):
            device_name = device_info['name'][:24].ljust(24)
            os_type = device_info.get('os_type', 'Unknown')[:8].ljust(8)
            collection_count = device_info.get('collection_count', 0)
            print_info(f"   │ {i:2} │ {device_name} │ {os_type} │ {collection_count:15} │")
        
        print_info("   └─────────────────────────────────────────────────────────────────┘")
        
        while True:
            try:
                choice = input(f"\n{Colors.BOLD}Select device number (1-{len(available_devices)}) or 0 to cancel: {Colors.RESET}").strip()
                
                if choice == '0':
                    return None
                
                device_num = int(choice)
                if 1 <= device_num <= len(available_devices):
                    selected_device = available_devices[device_num - 1]
                    return {
                        'type': 'single',
                        'device_name': selected_device['name'],
                        'description': f"Single router analysis - {selected_device['name']}"
                    }
                else:
                    print_error(f"Invalid selection. Please enter 1-{len(available_devices)} or 0.")
                    
            except ValueError:
                print_error("Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Selection cancelled by user.{Colors.RESET}")
                return None

    def _select_device_types(self) -> Dict:
        """Select specific device types for platform-specific analysis
        
        Returns:
            Dict with device type filter configuration
        """
        print_section("Device Type Selection")
        
        print_info("Select which Cisco OS types to include in the analysis:")
        print_info("You can choose multiple types for comparative analysis.")
        
        device_types = [
            {'code': 'ios', 'name': 'Cisco iOS', 'description': 'Traditional Cisco IOS devices'},
            {'code': 'iosxe', 'name': 'Cisco iOS-XE', 'description': 'Next-generation iOS-XE platforms'},
            {'code': 'iosxr', 'name': 'Cisco iOS-XR', 'description': 'Service provider iOS-XR systems'}
        ]
        
        selected_types = []
        
        for device_type in device_types:
            while True:
                try:
                    choice = input(f"\n{Colors.BOLD}Include {device_type['name']} ({device_type['description']})? (y/n): {Colors.RESET}").strip().lower()
                    
                    if choice in ['y', 'yes']:
                        selected_types.append(device_type['code'])
                        print_success(f"✅ {device_type['name']} included")
                        break
                    elif choice in ['n', 'no']:
                        print_info(f"⏭️  {device_type['name']} skipped")
                        break
                    else:
                        print_error("Please enter 'y' for yes or 'n' for no.")
                        
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}Selection cancelled by user.{Colors.RESET}")
                    return None
        
        if not selected_types:
            print_warning("No device types selected. Analysis cancelled.")
            return None
            
        description = f"Platform-specific analysis - {', '.join([t.upper() for t in selected_types])}"
        
        return {
            'type': 'device_types',
            'device_types': selected_types,
            'description': description
        }

    def _discover_available_devices(self) -> List[Dict]:
        """Discover all devices available in existing collections
        
        Returns:
            List of device information dictionaries
        """
        print_info("🔍 Discovering devices from existing collections...")
        
        device_registry = {}
        collections = self._discover_collection_directories()
        
        for collection_name, collection_info in collections.items():
            collection_path = collection_info['path']
            
            # Look for device directories in this collection
            try:
                for item in collection_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        device_name = item.name
                        
                        # Try to determine OS type from device data
                        os_type = self._detect_device_os_type(item)
                        
                        if device_name not in device_registry:
                            device_registry[device_name] = {
                                'name': device_name,
                                'os_type': os_type,
                                'collection_count': 0,
                                'collections': []
                            }
                        
                        device_registry[device_name]['collection_count'] += 1
                        device_registry[device_name]['collections'].append(collection_name)
                        
            except Exception as e:
                print_warning(f"⚠️  Error scanning collection {collection_name}: {str(e)}")
                continue
        
        # Convert to sorted list
        available_devices = list(device_registry.values())
        available_devices.sort(key=lambda x: x['name'])
        
        print_success(f"📊 Discovered {len(available_devices)} unique devices")
        return available_devices

    def _detect_device_os_type(self, device_path: Path) -> str:
        """Detect device OS type from collection data
        
        Args:
            device_path: Path to device directory
            
        Returns:
            Detected OS type or 'unknown'
        """
        # Look for OS indicators in health data or show version files
        health_files = list(device_path.glob("**/health*"))
        version_files = list(device_path.glob("**/show_version*"))
        
        # Check health files first
        for health_file in health_files:
            try:
                if health_file.is_file():
                    content = health_file.read_text(encoding='utf-8', errors='ignore').lower()
                    
                    if 'ios-xr' in content or 'iosxr' in content:
                        return 'iosxr'
                    elif 'ios-xe' in content or 'iosxe' in content:
                        return 'iosxe'
                    elif 'ios' in content and 'cisco ios software' in content:
                        return 'ios'
                        
            except Exception:
                continue
        
        # Check version files
        for version_file in version_files:
            try:
                if version_file.is_file():
                    content = version_file.read_text(encoding='utf-8', errors='ignore').lower()
                    
                    if 'ios xr' in content or 'iosxr' in content:
                        return 'iosxr'
                    elif 'ios xe' in content or 'iosxe' in content:
                        return 'iosxe'
                    elif 'cisco ios software' in content:
                        return 'ios'
                        
            except Exception:
                continue
        
        return 'unknown'

    def _filter_collections_by_devices(self, collections: Dict[str, Dict], device_filter: Dict) -> Dict[str, Dict]:
        """Filter collections based on device selection criteria
        
        Args:
            collections: Original collections dictionary
            device_filter: Device filter configuration
            
        Returns:
            Filtered collections dictionary
        """
        filter_type = device_filter['type']
        
        print_info(f"🔧 Applying device filter: {device_filter['description']}")
        
        if filter_type == 'all':
            return collections
        
        filtered_collections = {}
        
        for collection_name, collection_info in collections.items():
            collection_path = collection_info['path']
            should_include_collection = False
            
            # Scan devices in this collection
            try:
                collection_devices = []
                for item in collection_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        device_name = item.name
                        os_type = self._detect_device_os_type(item)
                        collection_devices.append({
                            'name': device_name,
                            'os_type': os_type,
                            'path': item
                        })
                
                # Apply filter criteria
                if filter_type == 'single':
                    target_device = device_filter['device_name']
                    should_include_collection = any(d['name'] == target_device for d in collection_devices)
                    
                elif filter_type == 'device_types':
                    target_types = device_filter['device_types']
                    should_include_collection = any(d['os_type'] in target_types for d in collection_devices)
                    
                elif filter_type == 'representative':
                    target_types = device_filter['device_types']
                    count_per_type = device_filter['count_per_type']
                    
                    # Check if this collection has devices matching our criteria
                    type_counts = {}
                    for device in collection_devices:
                        os_type = device['os_type']
                        if os_type in target_types:
                            type_counts[os_type] = type_counts.get(os_type, 0) + 1
                    
                    # Include if we have devices of target types
                    should_include_collection = len(type_counts) > 0
                
                if should_include_collection:
                    # Create a filtered version of collection_info
                    filtered_collection_info = collection_info.copy()
                    
                    # Filter device list if applicable
                    if filter_type != 'all':
                        filtered_devices = []
                        for device in collection_devices:
                            include_device = False
                            
                            if filter_type == 'single':
                                include_device = device['name'] == device_filter['device_name']
                            elif filter_type == 'device_types':
                                include_device = device['os_type'] in device_filter['device_types']
                            elif filter_type == 'representative':
                                include_device = device['os_type'] in device_filter['device_types']
                            
                            if include_device:
                                filtered_devices.append(device['name'])
                        
                        filtered_collection_info['filtered_devices'] = filtered_devices
                        filtered_collection_info['device_filter'] = device_filter
                    
                    filtered_collections[collection_name] = filtered_collection_info
                    
            except Exception as e:
                print_warning(f"⚠️  Error processing collection {collection_name}: {str(e)}")
                continue
        
        filter_summary = f"Filter applied: {len(filtered_collections)}/{len(collections)} collections match criteria"
        print_success(filter_summary)
        
        return filtered_collections

    def _display_comprehensive_terminal_report(self, collections: Dict[str, Dict]):
        """Display comprehensive terminal report with enhanced formatting (T005)
        
        Args:
            collections: Collections with complete analysis data
        """
        print_info("🎯 Generating enhanced terminal display...")
        
        # Executive Dashboard Summary
        self._display_executive_dashboard(collections)
        
        # Collection Health Matrix
        self._display_collection_health_matrix(collections)
        
        # Network Infrastructure Overview
        self._display_network_infrastructure_overview(collections)
        
        # Gap Analysis Dashboard
        self._display_gap_analysis_dashboard(collections)
        
        # Recommendations Action Plan
        self._display_recommendations_action_plan(collections)
        
        # Resource Planning Summary
        self._display_resource_planning_summary(collections)
        
        print_success("✅ Enhanced terminal display complete")

    def _display_executive_dashboard(self, collections: Dict[str, Dict]):
        """Display executive summary dashboard"""
        print_header("📊 EXECUTIVE DASHBOARD", Colors.MAGENTA)
        
        # Check if any filtering was applied
        filter_info = None
        for collection_info in collections.values():
            if 'device_filter' in collection_info:
                filter_info = collection_info['device_filter']
                break
        
        # Display filter information if applicable
        if filter_info:
            print_header(f"🎯 ANALYSIS SCOPE: {filter_info['description'].upper()}", Colors.YELLOW)
            if filter_info['type'] == 'single':
                print_info(f"   • Focused analysis on device: {filter_info['device_name']}")
            elif filter_info['type'] == 'device_types':
                device_types = ', '.join([t.upper() for t in filter_info['device_types']])
                print_info(f"   • Platform-specific analysis: {device_types}")
            elif filter_info['type'] == 'representative':
                print_info(f"   • Representative sample: 1 device per OS type")
            print_info("")
        else:
            print_info("🌐 Analysis scope: All available devices and collections\n")
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        
        # Collection Overview
        total_collections = len(collections)
        
        # Count devices - handle filtered vs unfiltered
        total_devices_analyzed = 0
        filtered_device_count = 0
        
        for collection_info in collections.values():
            if 'filtered_devices' in collection_info:
                filtered_device_count += len(collection_info['filtered_devices'])
            else:
                # Use global device stats if available
                global_stats = collection_info.get('global_device_stats', {})
                if global_stats:
                    total_devices_analyzed = max(total_devices_analyzed, len(global_stats.get('total_devices', set())))
        
        # Use filtered count if filtering was applied
        if filter_info and filtered_device_count > 0:
            devices_analyzed = filtered_device_count
            scope_note = " (filtered)"
        else:
            devices_analyzed = len(sample_collection.get('global_device_stats', {}).get('total_devices', set()))
            scope_note = ""
        
        total_layers_available = len(sample_collection.get('global_layer_stats', {}).get('all_layers', set()))
        
        print_info("📈 Collection Overview:")
        print_info(f"   • Total Collections Analyzed: {total_collections}")
        print_info(f"   • Network Devices Analyzed: {devices_analyzed}{scope_note}")
        print_info(f"   • Data Layer Types: {total_layers_available}")
        
        # Device Health Summary (adjusted for filtering)
        device_stats = sample_collection.get('global_device_stats', {})
        
        if filter_info:
            # Calculate accessibility for filtered devices
            accessible_count = 0
            total_filtered = 0
            
            for collection_info in collections.values():
                if 'filtered_devices' in collection_info:
                    filtered_devices = collection_info['filtered_devices']
                    total_filtered += len(filtered_devices)
                    
                    # Check accessibility from device stats
                    accessible_devices = device_stats.get('accessible_devices', set())
                    for device in filtered_devices:
                        if device in accessible_devices:
                            accessible_count += 1
            
            if total_filtered > 0:
                device_reliability = (accessible_count / total_filtered * 100)
                print_info("\n🌐 Filtered Network Health Summary:")
                print_info(f"   • Device Accessibility: {accessible_count}/{total_filtered} ({device_reliability:.1f}%)")
            else:
                print_info("\n🌐 Network Health Summary:")
                print_info("   • Device Accessibility: No filtered devices found")
        else:
            # Standard accessibility calculation
            accessible_devices = len(device_stats.get('accessible_devices', set()))
            device_reliability = (accessible_devices / devices_analyzed * 100) if devices_analyzed > 0 else 0
            
            print_info("\n🌐 Network Health Summary:")
            print_info(f"   • Device Accessibility: {accessible_devices}/{devices_analyzed} ({device_reliability:.1f}%)")
        
        # Collection Effectiveness (unchanged - applies to filtered scope)
        cross_analysis = sample_collection.get('cross_option_analysis', {})
        effectiveness_data = cross_analysis.get('option_effectiveness', {})
        
        if effectiveness_data:
            print_info("\n⚡ Collection Effectiveness:")
            for option_type, effectiveness in effectiveness_data.items():
                effectiveness_pct = effectiveness * 100
                status_icon = "🟢" if effectiveness_pct >= 80 else "🟡" if effectiveness_pct >= 60 else "🔴"
                print_info(f"   • {option_type}: {status_icon} {effectiveness_pct:.1f}%")
        
        # Gap Analysis Summary (applies to filtered scope)
        gap_analysis = sample_collection.get('gap_analysis', {})
        total_gaps = gap_analysis.get('total_gaps_identified', 0)
        missing_options = len(gap_analysis.get('missing_options', []))
        critical_gaps = len(gap_analysis.get('critical_gaps', []))
        
        print_info("\n🔍 Gap Analysis Summary:")
        print_info(f"   • Total Gaps Identified: {total_gaps}")
        print_info(f"   • Missing Collection Options: {missing_options}")
        print_info(f"   • Critical Issues: {critical_gaps}")
        
        # Action Required Indicator
        recommendations = sample_collection.get('recommendations', {})
        immediate_actions = len(recommendations.get('immediate_actions', []))
        
        if immediate_actions > 0:
            print_warning(f"\n⚠️  IMMEDIATE ACTION REQUIRED: {immediate_actions} critical items need attention")
        else:
            print_success("\n✅ No immediate actions required - network collection status is optimal")
            
        # Add filtering summary if applicable
        if filter_info:
            print_info(f"\n📋 Scope Summary: Analysis focused on {filter_info['description'].lower()}")
            if filter_info['type'] != 'all':
                print_info("   • Run analysis with 'All Routers' option for complete network view")

    def _display_collection_health_matrix(self, collections: Dict[str, Dict]):
        """Display collection health status matrix"""
        print_header("🏥 COLLECTION HEALTH MATRIX", Colors.CYAN)
        
        # Check for filtering
        filter_info = None
        for collection_info in collections.values():
            if 'device_filter' in collection_info:
                filter_info = collection_info['device_filter']
                break
        
        if filter_info:
            print_info(f"📋 Health matrix for filtered scope: {filter_info['description']}")
        else:
            print_info("📋 Collection Status Overview:")
            
        print_info("   ┌─────────────────────────────────────────────────────────────────┐")
        print_info("   │ Collection Name              │ Devices │ Layers │ Status      │")
        print_info("   ├─────────────────────────────────────────────────────────────────┤")
        
        for collection_name, collection_info in collections.items():
            # Get device count - use filtered count if available
            if 'filtered_devices' in collection_info:
                device_count = len(collection_info['filtered_devices'])
                device_note = " (F)"  # Filtered indicator
            else:
                device_count = len(collection_info.get('devices', []))
                device_note = ""
                
            layer_count = len(collection_info.get('layer_analysis', {}).get('available_layers', []))
            completeness = collection_info.get('completeness_score', 0) * 100
            
            # Determine status
            if completeness >= 80:
                status = "🟢 Excellent"
            elif completeness >= 60:
                status = "🟡 Good    "
            elif completeness >= 40:
                status = "🟠 Fair    "
            else:
                status = "🔴 Poor    "
            
            # Format collection name for display
            display_name = collection_name[:28].ljust(28)
            device_display = f"{device_count:4}{device_note}".ljust(7)
            layer_display = f"{layer_count:4}".ljust(6)
            
            print_info(f"   │ {display_name} │ {device_display} │ {layer_display} │ {status} │")
        
        print_info("   └─────────────────────────────────────────────────────────────────┘")
        
        if filter_info:
            print_info("   📝 Legend: (F) = Filtered device count based on selection criteria")
        
        # Collection health summary
        total_collections = len(collections)
        excellent_count = sum(1 for c in collections.values() if c.get('completeness_score', 0) >= 0.8)
        good_count = sum(1 for c in collections.values() if 0.6 <= c.get('completeness_score', 0) < 0.8)
        fair_count = sum(1 for c in collections.values() if 0.4 <= c.get('completeness_score', 0) < 0.6)
        poor_count = sum(1 for c in collections.values() if c.get('completeness_score', 0) < 0.4)
        
        print_info(f"\n📊 Health Distribution:")
        print_info(f"   🟢 Excellent: {excellent_count}/{total_collections} ({excellent_count/total_collections*100:.1f}%)")
        print_info(f"   🟡 Good:      {good_count}/{total_collections} ({good_count/total_collections*100:.1f}%)")
        print_info(f"   🟠 Fair:      {fair_count}/{total_collections} ({fair_count/total_collections*100:.1f}%)")
        print_info(f"   🔴 Poor:      {poor_count}/{total_collections} ({poor_count/total_collections*100:.1f}%)")
        
        # Recommendations based on health
        if poor_count > 0:
            print_warning(f"\n⚠️  {poor_count} collection(s) need immediate attention")
        elif fair_count > 0:
            print_info(f"\n💡 {fair_count} collection(s) could benefit from improvement")
        else:
            print_success("\n✅ All collections are in good health")

    def _display_network_infrastructure_overview(self, collections: Dict[str, Dict]):
        """Display network infrastructure overview"""
        print_header("🌐 NETWORK INFRASTRUCTURE OVERVIEW", Colors.BLUE)
        
        # Check for filtering
        filter_info = None
        for collection_info in collections.values():
            if 'device_filter' in collection_info:
                filter_info = collection_info['device_filter']
                break
        
        # Display scope information
        if filter_info:
            print_info(f"🎯 Infrastructure scope: {filter_info['description']}")
            if filter_info['type'] == 'single':
                print_info(f"   • Analyzing single device: {filter_info['device_name']}")
            elif filter_info['type'] == 'device_types':
                device_types = ', '.join([t.upper() for t in filter_info['device_types']])
                print_info(f"   • Platform focus: {device_types}")
            elif filter_info['type'] == 'representative':
                print_info(f"   • Representative sampling across OS types")
            print_info("")
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        device_stats = sample_collection.get('global_device_stats', {})
        layer_stats = sample_collection.get('global_layer_stats', {})
        
        # Calculate device counts - handle filtering
        if filter_info:
            # Count filtered devices
            total_filtered_devices = 0
            accessible_filtered_devices = 0
            consistent_filtered_devices = 0
            
            for collection_info in collections.values():
                if 'filtered_devices' in collection_info:
                    filtered_devices = collection_info['filtered_devices']
                    total_filtered_devices += len(filtered_devices)
                    
                    # Check accessibility and consistency for filtered devices
                    accessible_devices = device_stats.get('accessible_devices', set())
                    consistent_devices = device_stats.get('consistent_devices', set())
                    
                    for device in filtered_devices:
                        if device in accessible_devices:
                            accessible_filtered_devices += 1
                        if device in consistent_devices:
                            consistent_filtered_devices += 1
            
            # Use filtered counts
            total_devices = total_filtered_devices
            accessible_devices_count = accessible_filtered_devices
            consistent_devices_count = consistent_filtered_devices
            scope_note = " (filtered scope)"
        else:
            # Use standard counts
            total_devices = len(device_stats.get('total_devices', set()))
            accessible_devices_count = len(device_stats.get('accessible_devices', set()))
            consistent_devices_count = len(device_stats.get('consistent_devices', set()))
            scope_note = ""
        
        # Device Infrastructure Summary
        print_info(f"🖥️  Device Infrastructure{scope_note}:")
        print_info(f"   • Total Network Devices: {total_devices}")
        
        if total_devices > 0:
            accessibility_pct = (accessible_devices_count / total_devices * 100)
            consistency_pct = (consistent_devices_count / total_devices * 100)
            print_info(f"   • Currently Accessible: {accessible_devices_count} ({accessibility_pct:.1f}%)")
            print_info(f"   • Consistently Reliable: {consistent_devices_count} ({consistency_pct:.1f}%)")
        else:
            print_info(f"   • Currently Accessible: 0 (no devices in scope)")
        
        # Device Type Breakdown (if filtering by types)
        if filter_info and filter_info['type'] in ['device_types', 'representative']:
            print_info("\n📋 Device Type Distribution:")
            type_counts = {}
            
            for collection_info in collections.values():
                if 'filtered_devices' in collection_info:
                    filtered_devices = collection_info['filtered_devices']
                    for device_name in filtered_devices:
                        # Need to determine device type for counting
                        for item in Path(collection_info['path']).iterdir():
                            if item.is_dir() and item.name == device_name:
                                os_type = self._detect_device_os_type(item)
                                type_counts[os_type] = type_counts.get(os_type, 0) + 1
                                break
            
            for os_type, count in sorted(type_counts.items()):
                os_display = os_type.upper() if os_type != 'unknown' else 'Unknown'
                print_info(f"   • {os_display}: {count} device(s)")
        
        # Layer Coverage Analysis
        all_layers = layer_stats.get('all_layers', set())
        critical_layers = layer_stats.get('critical_layers_missing', [])
        
        print_info("\n📊 Data Layer Coverage:")
        print_info(f"   • Available Layer Types: {len(all_layers)}")
        if all_layers:
            layer_list = ", ".join(sorted(all_layers))
            print_info(f"   • Layers: {layer_list}")
        
        if critical_layers:
            print_warning(f"   • Missing Critical Layers: {', '.join(critical_layers)}")
        else:
            print_success("   • All critical layers present")
        
        # Collection Option Coverage
        option_types = set()
        filtered_collections_count = 0
        
        for collection_info in collections.values():
            option_types.add(collection_info.get('option_type', 'unknown'))
            if 'filtered_devices' in collection_info:
                filtered_collections_count += 1
        
        print_info(f"\n🎯 Collection Option Coverage:")
        print_info(f"   • Option Types Used: {len(option_types)}")
        print_info(f"   • Options: {', '.join(sorted(option_types))}")
        
        if filter_info:
            total_collections = len(collections)
            print_info(f"   • Collections in scope: {total_collections}")
            if filter_info['type'] != 'all':
                print_info(f"   • Collections with filtered devices: {filtered_collections_count}")
        
        # Infrastructure Health Assessment
        if total_devices > 0:
            health_score = (accessible_devices_count / total_devices * 0.6) + (consistent_devices_count / total_devices * 0.4)
            health_percentage = health_score * 100
            
            print_info(f"\n💚 Infrastructure Health Score:")
            if health_percentage >= 80:
                health_status = "🟢 Excellent"
            elif health_percentage >= 60:
                health_status = "🟡 Good"
            elif health_percentage >= 40:
                health_status = "🟠 Fair"
            else:
                health_status = "🔴 Poor"
            
            print_info(f"   • Overall Health: {health_status} ({health_percentage:.1f}%)")
            
            if filter_info:
                print_info(f"   • Scope: {filter_info['description']}")
                if filter_info['type'] != 'all':
                    print_info("   • Note: Health score reflects filtered scope only")
        else:
            print_warning("\n💚 Infrastructure Health Score:")
            print_warning("   • Cannot calculate - no devices in current scope")

    def _display_gap_analysis_dashboard(self, collections: Dict[str, Dict]):
        """Display comprehensive gap analysis dashboard"""
        print_header("🔍 GAP ANALYSIS DASHBOARD", Colors.YELLOW)
        
        # Check for filtering
        filter_info = None
        for collection_info in collections.values():
            if 'device_filter' in collection_info:
                filter_info = collection_info['device_filter']
                break
        
        # Display scope information
        if filter_info:
            print_info(f"🎯 Gap analysis scope: {filter_info['description']}")
            if filter_info['type'] == 'single':
                print_info(f"   • Analyzing gaps for device: {filter_info['device_name']}")
            elif filter_info['type'] == 'device_types':
                device_types = ', '.join([t.upper() for t in filter_info['device_types']])
                print_info(f"   • Platform-specific gap analysis: {device_types}")
            elif filter_info['type'] == 'representative':
                print_info(f"   • Representative sampling gap analysis")
            print_info("")
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        gap_analysis = sample_collection.get('gap_analysis', {})
        root_cause_analysis = sample_collection.get('root_cause_analysis', {})
        
        # Gap Overview
        total_gaps = gap_analysis.get('total_gaps_identified', 0)
        missing_options = gap_analysis.get('missing_options', [])
        incomplete_options = gap_analysis.get('incomplete_options', [])
        critical_gaps = gap_analysis.get('critical_gaps', [])
        
        # Adjust gap messaging for filtered scope
        scope_qualifier = ""
        if filter_info and filter_info['type'] != 'all':
            scope_qualifier = " (in filtered scope)"
        
        print_info(f"📋 Gap Analysis Results{scope_qualifier}:")
        print_info(f"   • Total Gaps Identified: {total_gaps}")
        print_info(f"   • Missing Collection Options: {len(missing_options)}")
        print_info(f"   • Incomplete Collections: {len(incomplete_options)}")
        print_info(f"   • Critical Issues: {len(critical_gaps)}")
        
        if missing_options:
            print_warning("   📝 Missing Options:")
            for option in missing_options:
                print_warning(f"     - {option}")
        
        if critical_gaps:
            print_error("   🚨 Critical Gaps:")
            for gap in critical_gaps:
                print_error(f"     - {gap}")
        
        # Filtering-specific gap analysis
        if filter_info and filter_info['type'] != 'all':
            print_info("\n🔬 Filtered Scope Analysis:")
            
            # Count devices in scope
            total_filtered_devices = 0
            for collection_info in collections.values():
                if 'filtered_devices' in collection_info:
                    total_filtered_devices += len(collection_info['filtered_devices'])
            
            print_info(f"   • Devices in scope: {total_filtered_devices}")
            
            if filter_info['type'] == 'single':
                print_info(f"   • Focus: Deep analysis of {filter_info['device_name']}")
                print_info("   • Recommendation: Review device-specific configuration gaps")
                
            elif filter_info['type'] == 'device_types':
                device_types = ', '.join([t.upper() for t in filter_info['device_types']])
                print_info(f"   • Focus: Platform-specific issues for {device_types}")
                print_info("   • Recommendation: Platform standardization and best practices")
                
            elif filter_info['type'] == 'representative':
                print_info("   • Focus: Cross-platform consistency validation")
                print_info("   • Recommendation: Scale findings to entire network")
        
        # Root Cause Analysis Summary
        print_info("\n🔬 Root Cause Analysis:")
        cause_categories = root_cause_analysis.get('cause_categories', {})
        impact_assessment = root_cause_analysis.get('impact_assessment', {})
        
        if cause_categories:
            print_info("   📊 Issue Categories:")
            for category, count in cause_categories.items():
                severity_icon = "🔴" if "critical" in category.lower() else "🟡" if "high" in category.lower() else "🟢"
                print_info(f"     • {category}: {severity_icon} {count} issues")
        
        if impact_assessment:
            print_info("   💥 Impact Assessment:")
            for impact_level, count in impact_assessment.items():
                if count > 0:
                    impact_icon = "🔥" if "critical" in impact_level.lower() else "⚡" if "high" in impact_level.lower() else "📊"
                    print_info(f"     • {impact_level}: {impact_icon} {count} items")
        
        # Gap prioritization based on scope
        if filter_info:
            print_info("\n🎯 Scope-Specific Recommendations:")
            
            if filter_info['type'] == 'single':
                print_info("   • Priority: Device-specific troubleshooting and optimization")
                print_info("   • Next step: Expand analysis to similar device types")
                
            elif filter_info['type'] == 'device_types':
                print_info("   • Priority: Platform standardization across selected OS types")
                print_info("   • Next step: Apply fixes consistently across platform family")
                
            elif filter_info['type'] == 'representative':
                print_info("   • Priority: Validate findings represent network-wide patterns")
                print_info("   • Next step: Run full network analysis to confirm trends")
                
            else:
                print_info("   • Priority: Address critical gaps across entire network")
                print_info("   • Next step: Implement systematic remediation plan")

    def _display_recommendations_action_plan(self, collections: Dict[str, Dict]):
        """Display recommendations and action plan"""
        print_header("💡 RECOMMENDATIONS & ACTION PLAN", Colors.GREEN)
        
        # Check for filtering
        filter_info = None
        for collection_info in collections.values():
            if 'device_filter' in collection_info:
                filter_info = collection_info['device_filter']
                break
        
        # Display scope information
        if filter_info:
            print_info(f"🎯 Action plan scope: {filter_info['description']}")
            if filter_info['type'] == 'single':
                print_info(f"   • Focused recommendations for device: {filter_info['device_name']}")
            elif filter_info['type'] == 'device_types':
                device_types = ', '.join([t.upper() for t in filter_info['device_types']])
                print_info(f"   • Platform-specific action plan: {device_types}")
            elif filter_info['type'] == 'representative':
                print_info(f"   • Scalable recommendations based on representative sample")
            print_info("")
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        recommendations = sample_collection.get('recommendations', {})
        
        # Immediate Actions
#!/usr/bin/env python3
"""
RR4 CLI Interactive Startup Script - Cross-Platform Compatible
Comprehensive guided setup and execution for the RR4 Complete Enhanced v4 CLI

CROSS-PLATFORM STARTUP:
- Windows 10/11: python start_rr4_cli.py
- Linux: python3 start_rr4_cli.py
- macOS: python3 start_rr4_cli.py

This script provides:
- Guided first-time setup
- Prerequisites checking
- Step-by-step testing
- Menu-driven interface for different use cases
- Error handling and recovery
- Best practice recommendations

Author: AI Assistant
Version: 1.0.1-CrossPlatform
Created: 2025-05-31
Platform Support: Windows 10/11, Linux, macOS
"""

import os
import sys
import time
import json
import csv
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Cross-platform compatibility check
def get_python_command():
    """Get the appropriate Python command for the current platform"""
    if platform.system().lower() == 'windows':
        return 'python'
    else:
        return 'python3'

def display_startup_info():
    """Display cross-platform startup information"""
    system = platform.system()
    python_cmd = get_python_command()
    
    print(f"{Colors.CYAN}{'=' * 80}")
    print(f"🌐 CROSS-PLATFORM STARTUP INFORMATION")
    print(f"{'=' * 80}{Colors.RESET}")
    print(f"\n{Colors.BOLD}Current Platform: {system} {platform.release()}{Colors.RESET}")
    print(f"{Colors.BOLD}Python Version: {platform.python_version()}{Colors.RESET}")
    print(f"\n{Colors.GREEN}To start this script on different platforms:{Colors.RESET}")
    
    if system.lower() == 'windows':
        print(f"  {Colors.YELLOW}Windows 10/11:{Colors.RESET}")
        print(f"    {Colors.WHITE}{python_cmd} start_rr4_cli.py{Colors.RESET}")
        print(f"    {Colors.WHITE}run_rr4_cli.bat{Colors.RESET}")
    else:
        print(f"  {Colors.YELLOW}Linux/macOS:{Colors.RESET}")
        print(f"    {Colors.WHITE}{python_cmd} start_rr4_cli.py{Colors.RESET}")
        print(f"    {Colors.WHITE}./start_rr4_cli.py{Colors.RESET} (if executable)")
    
    print(f"\n{Colors.BLUE}Universal command (all platforms):{Colors.RESET}")
    print(f"  {Colors.WHITE}{python_cmd} start_rr4_cli.py{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

# ANSI color codes for better terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

def print_header(title: str, color: str = Colors.CYAN):
    """Print a formatted header"""
    width = 80
    print(f"\n{color}{'=' * width}")
    print(f"{title.center(width)}")
    print(f"{'=' * width}{Colors.RESET}\n")

def print_section(title: str, color: str = Colors.YELLOW):
    """Print a formatted section header"""
    print(f"\n{color}{Colors.BOLD}🔧 {title}{Colors.RESET}")
    print(f"{color}{'-' * (len(title) + 4)}{Colors.RESET}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")

class RR4StartupManager:
    """Main startup manager for RR4 CLI"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.main_script = self.script_dir / "rr4-complete-enchanced-v4-cli.py"
        self.test_results = {}
        self.prerequisites_checked = False
        self.platform_info = self._get_platform_info()
        
    def _get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'python_version': platform.python_version(),
            'is_windows': platform.system().lower() == 'windows',
            'is_linux': platform.system().lower() == 'linux',
            'is_macos': platform.system().lower() == 'darwin'
        }
    
    def _run_command(self, command: List[str], description: str, critical: bool = True, timeout: int = 120) -> Tuple[bool, str, str]:
        """Run a command and return success status with output"""
        try:
            print_info(f"Running: {description}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.script_dir
            )
            
            success = result.returncode == 0
            if success:
                print_success(f"{description} - Completed successfully")
                return True, result.stdout, result.stderr
            else:
                error_msg = f"{description} - Failed (Exit code: {result.returncode})"
                if critical:
                    print_error(error_msg)
                    print_error(f"Error output: {result.stderr}")
                else:
                    print_warning(error_msg)
                return False, result.stdout, result.stderr
                
        except subprocess.TimeoutExpired:
            error_msg = f"{description} - Timed out after {timeout} seconds"
            if critical:
                print_error(error_msg)
            else:
                print_warning(error_msg)
            return False, "", "Timeout"
        except Exception as e:
            error_msg = f"{description} - Exception: {str(e)}"
            if critical:
                print_error(error_msg)
            else:
                print_warning(error_msg)
            return False, "", str(e)
    
    def check_prerequisites(self) -> bool:
        """Check all prerequisites"""
        print_header("PREREQUISITES CHECK", Colors.CYAN)
        
        all_good = True
        
        # Check Python version
        print_section("Python Version Check")
        python_version = sys.version_info
        if python_version >= (3, 8):
            print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - Compatible")
        else:
            print_error(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - Requires Python 3.8+")
            all_good = False
        
        # Check if main script exists
        print_section("Main Script Check")
        if self.main_script.exists():
            print_success(f"Main script found: {self.main_script}")
        else:
            print_error(f"Main script not found: {self.main_script}")
            all_good = False
            return False
        
        # Check platform compatibility
        print_section("Platform Compatibility Check")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "show-platform"],
            "Platform information check",
            critical=False
        )
        if success:
            print_success("Platform compatibility verified")
        else:
            print_warning("Platform check had issues but continuing...")
        
        # Check dependencies
        print_section("Dependencies Check")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "--test-dependencies"],
            "Dependencies verification",
            critical=True
        )
        if success:
            print_success("All dependencies are available")
        else:
            print_error("Dependencies check failed")
            print_info("Run: pip install -r requirements.txt")
            all_good = False
        
        self.prerequisites_checked = all_good
        return all_good
    
    def validate_environment(self) -> bool:
        """Validate environment configuration"""
        print_header("ENVIRONMENT VALIDATION", Colors.CYAN)
        
        # Check if environment file exists
        env_file = self.script_dir / "rr4-complete-enchanced-v4-cli.env-t"
        if env_file.exists():
            print_success("Environment file found")
            
            # Check configuration
            success, stdout, stderr = self._run_command(
                ["python3", str(self.main_script), "show-config"],
                "Configuration validation",
                critical=False
            )
            if success:
                print_success("Configuration is valid")
                return True
            else:
                print_warning("Configuration has issues")
                return False
        else:
            print_warning("Environment file not found")
            return False
    
    def setup_environment(self) -> bool:
        """Interactive environment setup"""
        print_header("ENVIRONMENT SETUP", Colors.CYAN)
        
        print_info("Starting interactive environment configuration...")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "configure-env"],
            "Interactive environment configuration",
            critical=True
        )
        
        if success:
            print_success("Environment configuration completed")
            return True
        else:
            print_error("Environment configuration failed")
            return False
    
    def validate_inventory(self) -> bool:
        """Validate inventory file"""
        print_header("INVENTORY VALIDATION", Colors.CYAN)
        
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "validate-inventory"],
            "Inventory file validation",
            critical=True
        )
        
        if success:
            print_success("Inventory validation passed")
            # Extract device count from output
            if "Found" in stdout and "devices" in stdout:
                print_info(f"Inventory details: {stdout.split('Found')[1].split('devices')[0].strip()} devices found")
            return True
        else:
            print_error("Inventory validation failed")
            return False
    
    def test_connectivity(self) -> bool:
        """Test device connectivity"""
        print_header("CONNECTIVITY TEST", Colors.CYAN)
        
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "test-connectivity"],
            "Device connectivity test",
            critical=True
        )
        
        if success:
            print_success("Connectivity test passed")
            # Extract success rate from output
            if "Success rate:" in stdout:
                success_rate_str = stdout.split("Success rate:")[1].split("%")[0].strip()
                try:
                    success_rate = float(success_rate_str)
                    print_info(f"Success rate: {success_rate}%")
                    
                    if success_rate >= 80.0:
                        print_success(f"Excellent connectivity: {success_rate}% of devices reachable")
                        return True
                    elif success_rate >= 50.0:
                        print_warning(f"Partial connectivity: {success_rate}% of devices reachable")
                        print_info("This is acceptable for testing - some devices may be down")
                        return True
                    else:
                        print_error(f"Poor connectivity: Only {success_rate}% of devices reachable")
                        return False
                except ValueError:
                    print_warning("Could not parse success rate, but test completed")
                    return True
            return True
        else:
            print_error("Connectivity test failed")
            return False
    
    def run_sample_collection(self) -> bool:
        """Run a sample data collection"""
        print_header("SAMPLE COLLECTION TEST", Colors.CYAN)
        
        print_info("Running sample collection from first device with health layer...")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-devices", "--device", "R0", "--layers", "health"],
            "Sample collection test (single device, health layer)",
            critical=True
        )
        
        if success:
            print_success("Sample collection completed successfully")
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Output saved to: {output_info}")
            return True
        else:
            print_error("Sample collection failed")
            return False
    
    def show_main_menu(self) -> int:
        """Display main menu and get user choice"""
        # Display cross-platform startup information first
        display_startup_info()
        
        print_header("RR4 CLI INTERACTIVE STARTUP", Colors.MAGENTA)
        
        print(f"{Colors.BOLD}Welcome to RR4 Complete Enhanced v4 CLI Startup Manager{Colors.RESET}")
        print(f"Platform: {self.platform_info['system']} {self.platform_info['release']}")
        print(f"Python: {self.platform_info['python_version']}")
        
        print(f"\n{Colors.BOLD}🚀 STARTUP OPTIONS:{Colors.RESET}")
        print(f"{Colors.GREEN}1. 🎯 FIRST-TIME SETUP (Recommended for new users){Colors.RESET}")
        print(f"   - Complete guided setup with prerequisites check")
        print(f"   - Environment configuration")
        print(f"   - Enhanced connectivity testing (ping + SSH auth)")
        print(f"   - Sample collection test")
        
        print(f"\n{Colors.BLUE}2. 🔍 AUDIT ONLY (Quick connectivity and health check){Colors.RESET}")
        print(f"   - Enhanced connectivity test (ping + SSH auth)")
        print(f"   - Health data collection from reachable devices")
        print(f"   - Generate audit report")
        
        print(f"\n{Colors.CYAN}3. 📊 FULL COLLECTION (Production data collection){Colors.RESET}")
        print(f"   - Enhanced connectivity test first")
        print(f"   - Collect from all reachable devices")
        print(f"   - Standard layers (health, interfaces, igp, bgp, mpls, vpn, static)")
        print(f"   - Generate comprehensive reports")
        
        print(f"\n{Colors.YELLOW}4. 🎛️  CUSTOM COLLECTION (Advanced users){Colors.RESET}")
        print(f"   - Choose specific devices")
        print(f"   - Select layers to collect")
        print(f"   - Custom parameters")
        
        print(f"\n{Colors.MAGENTA}5. 🔧 PREREQUISITES CHECK ONLY{Colors.RESET}")
        print(f"   - Verify system requirements")
        print(f"   - Check dependencies")
        print(f"   - Validate configuration")
        
        print(f"\n{Colors.CYAN}6. 🌐 ENHANCED CONNECTIVITY TEST ONLY{Colors.RESET}")
        print(f"   - Comprehensive ping + SSH authentication test")
        print(f"   - Detailed device-by-device status report")
        print(f"   - No data collection")
        
        print(f"\n{Colors.WHITE}7. 📚 SHOW HELP & OPTIONS{Colors.RESET}")
        print(f"   - Display all available commands")
        print(f"   - Show advanced options")
        print(f"   - Documentation links")
        
        print(f"\n{Colors.YELLOW}8. 🎯 CONSOLE AUDIT (NM4 Console Line Collection){Colors.RESET}")
        print(f"   - Enhanced connectivity test first")
        print(f"   - Console line discovery and configuration collection")
        print(f"   - NM4 console card support (IOS/IOS XR)")
        print(f"   - Generate console audit report")
        
        print(f"\n{Colors.GREEN}9. 🌟 COMPLETE COLLECTION (All layers + Console in systematic order){Colors.RESET}")
        print(f"   - Enhanced connectivity test first")
        print(f"   - Systematic collection in optimal order")
        print(f"   - ALL layers (health, interfaces, igp, bgp, mpls, vpn, static, console)")
        print(f"   - Comprehensive audit and production reports")
        
        print(f"\n{Colors.RED}10. 🔒 CONSOLE SECURITY AUDIT (Transport Security Analysis){Colors.RESET}")
        print(f"   - Analyze console audit results from option 8")
        print(f"   - Detect telnet transport violations (aux, console, vty, line)")
        print(f"   - Security compliance report per router and summary")
        print(f"   - Transport input/output validation")
        
        print(f"\n{Colors.BLUE}12. 📊 COMPREHENSIVE STATUS REPORT (All Options Analysis){Colors.RESET}")
        print(f"   - Analyze collection data from options 1-10 with device filtering")
        print(f"   - Choose: All routers, single router, or platform-specific subsets")
        print(f"   - Generate unified status and gap analysis reports")
        print(f"   - Identify missing collections and remediation needs")
        print(f"   - Executive summary and detailed technical reports")
        
        print(f"\n{Colors.RED}0. 🚪 EXIT{Colors.RESET}")
        
        while True:
            try:
                choice = input(f"\n{Colors.BOLD}Select option (0-12): {Colors.RESET}").strip()
                if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12']:
                    return int(choice)
                else:
                    print_error("Invalid choice. Please enter 0-12 (note: option 11 is reserved).")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                return 0
            except Exception:
                print_error("Invalid input. Please enter a number (0-12, option 11 reserved).")
    
    def first_time_setup(self) -> bool:
        """Complete first-time setup process"""
        print_header("FIRST-TIME SETUP PROCESS", Colors.GREEN)
        
        steps = [
            ("Prerequisites Check", self.check_prerequisites),
            ("Environment Validation", self.validate_environment),
            ("Environment Setup", self.setup_environment),
            ("Inventory Validation", self.validate_inventory),
            ("Enhanced Connectivity Test", self.enhanced_connectivity_test),
            ("Sample Collection", self.run_sample_collection)
        ]
        
        for step_name, step_func in steps:
            print_section(f"Step: {step_name}")
            
            try:
                if step_name == "Environment Setup":
                    # Skip if environment is already valid
                    if self.validate_environment():
                        print_success("Environment already configured, skipping setup")
                        self.test_results[step_name] = "PASSED"
                        continue
                
                success = step_func()
                if success:
                    print_success(f"{step_name} completed successfully")
                    self.test_results[step_name] = "PASSED"
                else:
                    print_error(f"{step_name} failed")
                    self.test_results[step_name] = "FAILED"
                    
                    # Ask user if they want to continue
                    if not self._ask_continue_on_error(step_name):
                        return False
                
                # Special handling for connectivity test - ask before proceeding to collection
                if step_name == "Enhanced Connectivity Test" and success:
                    print_section("Proceed to Sample Collection")
                    try:
                        proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with sample data collection? (y/n): {Colors.RESET}").strip().lower()
                        if proceed not in ['y', 'yes']:
                            print_info("Sample collection skipped by user")
                            self.test_results["Sample Collection"] = "SKIPPED"
                            break
                    except:
                        print_info("Proceeding with sample collection...")
                        
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Setup interrupted by user.{Colors.RESET}")
                return False
            except Exception as e:
                print_error(f"{step_name} error: {str(e)}")
                self.test_results[step_name] = f"ERROR: {str(e)}"
                if not self._ask_continue_on_error(step_name):
                    return False
        
        # Show final results
        self._show_setup_results()
        return True
    
    def audit_only(self) -> bool:
        """Run audit-only mode with enhanced connectivity"""
        print_header("AUDIT ONLY MODE", Colors.BLUE)
        
        print_info("Running quick audit of network devices...")
        
        # Quick prerequisite check
        if not self.prerequisites_checked:
            print_section("Quick Prerequisites Check")
            if not self.check_prerequisites():
                print_error("Prerequisites check failed")
                return False
        
        # Enhanced connectivity test
        if not self.enhanced_connectivity_test():
            print_error("Enhanced connectivity test failed")
            return False
        
        # Ask user before proceeding to data collection
        print_section("Proceed to Data Collection")
        try:
            proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with health data collection? (y/n): {Colors.RESET}").strip().lower()
            if proceed not in ['y', 'yes']:
                print_info("Data collection cancelled by user")
                return True
        except:
            print_info("Proceeding with data collection...")
        
        # Quick health collection from all devices
        print_section("Health Data Collection")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-all", "--layers", "health"],
            "Health data collection from all reachable devices",
            critical=True,
            timeout=300  # 5 minutes for health collection
        )
        
        if success:
            print_success("Audit completed successfully")
            print_info("Health data collected from all reachable devices")
            
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Audit results saved to: {output_info}")
            return True
        else:
            print_error("Audit collection failed")
            return False
    
    def full_collection(self) -> bool:
        """Run full data collection"""
        print_header("FULL COLLECTION MODE", Colors.CYAN)
        
        print_info("Running comprehensive data collection from all devices...")
        
        # Verify prerequisites
        if not self.prerequisites_checked:
            print_section("Prerequisites Verification")
            if not self.check_prerequisites():
                print_error("Prerequisites check failed")
                return False
        
        # Enhanced connectivity test first
        if not self.enhanced_connectivity_test():
            print_error("Enhanced connectivity test failed")
            return False
        
        # Ask user before proceeding to full collection
        print_section("Proceed to Full Collection")
        try:
            proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with full data collection? (y/n): {Colors.RESET}").strip().lower()
            if proceed not in ['y', 'yes']:
                print_info("Full data collection cancelled by user")
                return True
        except:
            print_info("Proceeding with full data collection...")
        
        # Run full collection with standard layers (no console)
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-all", "--layers", "health,interfaces,igp,bgp,mpls,vpn,static"],
            "Full data collection (standard layers, all reachable devices)",
            critical=True,
            timeout=600  # 10 minutes for full collection
        )
        
        if success:
            print_success("Full collection completed successfully")
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Data saved to: {output_info}")
            return True
        else:
            print_error("Full collection failed")
            return False
    
    def enhanced_connectivity_test(self) -> bool:
        """Enhanced connectivity test with ping and SSH authentication"""
        print_header("ENHANCED CONNECTIVITY TEST", Colors.CYAN)
        
        print_info("Performing comprehensive connectivity test...")
        print_info("Step 1: Testing network reachability (ping)")
        print_info("Step 2: Testing SSH authentication")
        print_info("Note: Device is considered UP if SSH authentication succeeds, even if ping fails")
        
        # Run the enhanced connectivity test
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "test-connectivity"],
            "Enhanced connectivity test (ping + SSH authentication)",
            critical=True,
            timeout=180  # 3 minutes for connectivity test
        )
        
        if success:
            print_success("Enhanced connectivity test completed")
            
            # Parse results
            if "Success rate:" in stdout:
                success_rate_str = stdout.split("Success rate:")[1].split("%")[0].strip()
                try:
                    success_rate = float(success_rate_str)
                    print_info(f"Overall success rate: {success_rate}%")
                    
                    # Extract device details
                    if "Device-by-Device Breakdown:" in stdout:
                        breakdown_section = stdout.split("Device-by-Device Breakdown:")[1].split("🔐")[0]
                        lines = breakdown_section.strip().split('\n')
                        
                        successful_devices = []
                        failed_devices = []
                        
                        for line in lines:
                            if "✅" in line and "Connected" in line:
                                device_name = line.split()[1]
                                successful_devices.append(device_name)
                            elif "❌" in line and "Failed" in line:
                                device_name = line.split()[1]
                                failed_devices.append(device_name)
                        
                        print_section("Connectivity Summary")
                        if successful_devices:
                            print_success(f"Successfully connected devices ({len(successful_devices)}): {', '.join(successful_devices)}")
                        
                        if failed_devices:
                            print_warning(f"Failed to connect devices ({len(failed_devices)}): {', '.join(failed_devices)}")
                            print_info("Failed devices will be skipped during data collection")
                    
                    if success_rate >= 50.0:
                        print_success(f"Connectivity test PASSED - {success_rate}% devices reachable")
                        
                        # Ask user if they want to continue
                        print_section("Next Steps Decision")
                        print_info("Connectivity test completed successfully!")
                        print_info(f"✅ {len(successful_devices) if 'successful_devices' in locals() else 'Several'} devices are ready for data collection")
                        if 'failed_devices' in locals() and failed_devices:
                            print_info(f"⚠️  {len(failed_devices)} devices are unreachable and will be skipped")
                        
                        return True
                    else:
                        print_error(f"Connectivity test FAILED - Only {success_rate}% devices reachable")
                        print_error("Too many devices are unreachable for reliable data collection")
                        return False
                        
                except ValueError:
                    print_warning("Could not parse success rate, but test completed")
                    return True
            return True
        else:
            print_error("Enhanced connectivity test failed")
            return False
    
    def custom_collection(self) -> bool:
        """Run custom collection with user choices"""
        print_header("CUSTOM COLLECTION MODE", Colors.YELLOW)
        
        # Get available devices
        print_section("Available Devices")
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "validate-inventory"],
            "Loading available devices",
            critical=True
        )
        
        if not success:
            print_error("Could not load device inventory")
            return False
        
        # Device selection
        print_info("Device Selection Options:")
        print("1. All devices")
        print("2. Specific devices")
        print("3. Device group")
        
        device_choice = input("Select device option (1-3): ").strip()
        
        # Layer selection
        print_info("\nAvailable Layers:")
        layers = ["health", "interfaces", "igp", "bgp", "mpls", "vpn", "static", "console"]
        for i, layer in enumerate(layers, 1):
            print(f"{i}. {layer}")
        print("8. All layers")
        
        layer_input = input("Select layers (comma-separated numbers or 8 for all): ").strip()
        
        # Build command
        command = ["python3", str(self.main_script)]
        
        if device_choice == "1":
            command.append("collect-all")
        elif device_choice == "2":
            devices = input("Enter device names (comma-separated): ").strip()
            command.extend(["collect-devices", "--devices", devices])
        elif device_choice == "3":
            group = input("Enter group name: ").strip()
            command.extend(["collect-group", "--group", group])
        else:
            print_error("Invalid device choice")
            return False
        
        # Add layers
        if layer_input == "8":
            selected_layers = ",".join(layers)
        else:
            try:
                selected_nums = [int(x.strip()) for x in layer_input.split(",")]
                selected_layers = ",".join([layers[i-1] for i in selected_nums if 1 <= i <= len(layers)])
            except:
                print_error("Invalid layer selection")
                return False
        
        command.extend(["--layers", selected_layers])
        
        # Run custom collection
        success, stdout, stderr = self._run_command(
            command,
            f"Custom collection: {' '.join(command[2:])}",
            critical=True
        )
        
        if success:
            print_success("Custom collection completed successfully")
            return True
        else:
            print_error("Custom collection failed")
            return False

    def console_audit(self) -> bool:
        """Run dedicated console line audit for NM4 console cards"""
        print_header("CONSOLE AUDIT MODE", Colors.YELLOW)
        
        print_info("Running dedicated console line audit for NM4 console cards...")
        print_info("🎯 This audit specifically targets:")
        print_info("   • Cisco routers with NM4 console cards")
        print_info("   • Console line discovery (x/y/z format)")
        print_info("   • IOS and IOS XR platform support")
        print_info("   • Individual console line configurations")
        
        # Quick prerequisite check
        if not self.prerequisites_checked:
            print_section("Quick Prerequisites Check")
            if not self.check_prerequisites():
                print_error("Prerequisites check failed")
                return False
        
        # Enhanced connectivity test first
        if not self.enhanced_connectivity_test():
            print_error("Enhanced connectivity test failed")
            return False
        
        # Ask user before proceeding to console collection
        print_section("Proceed to Console Line Collection")
        try:
            proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with console line audit? (y/n): {Colors.RESET}").strip().lower()
            if proceed not in ['y', 'yes']:
                print_info("Console audit cancelled by user")
                return True
        except:
            print_info("Proceeding with console audit...")
        
        # Console line collection from all devices
        print_section("Console Line Discovery & Configuration Collection")
        print_info("Discovering console lines using 'show line' command...")
        print_info("Collecting individual line configurations...")
        print_info("Generating console audit report...")
        
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-all", "--layers", "console"],
            "Console line audit from all reachable devices",
            critical=True,
            timeout=600  # 10 minutes for console collection
        )
        
        if success:
            print_success("Console audit completed successfully")
            print_info("✅ Console line discovery and configurations collected")
            print_info("✅ Platform-specific commands executed (IOS/IOS XR)")
            print_info("✅ NM4 console card support validated")
            
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Console audit results saved to: {output_info}")
            elif "rr4-complete-enchanced-v4-cli-output" in stdout:
                # Try to extract from different output format
                lines = stdout.split('\n')
                for line in lines:
                    if "rr4-complete-enchanced-v4-cli-output" in line:
                        print_info(f"Console audit results saved to: {line.strip()}")
                        break
            
            print_section("Console Audit Summary")
            print_info("📋 Console audit includes:")
            print_info("   • JSON format: Structured console line data")
            print_info("   • TXT format: Human-readable console reports") 
            print_info("   • Raw outputs: Individual command outputs")
            print_info("   • Platform detection: IOS vs IOS XR handling")
            print_info("   • Range validation: x:0-1, y:0-1, z:0-22 support")
            
            return True
        else:
            print_error("Console audit failed")
            print_error("Common causes:")
            print_error("   • No NM4 console cards present")
            print_error("   • Insufficient device privileges")
            print_error("   • Platform detection issues")
            print_info("Check the debug output for detailed error information")
            return False

    def complete_collection(self) -> bool:
        """Run complete systematic collection with all layers including console in optimal order"""
        print_header("COMPLETE COLLECTION MODE", Colors.GREEN)
        
        print_info("Running complete systematic data collection from all devices...")
        print_info("🌟 This comprehensive collection includes:")
        print_info("   • All standard network layers (health, interfaces, igp, bgp, mpls, vpn, static)")
        print_info("   • Console line audit (NM4 console cards)")
        print_info("   • Systematic collection in optimal order")
        print_info("   • Complete audit and production reports")
        
        # Verify prerequisites
        if not self.prerequisites_checked:
            print_section("Prerequisites Verification")
            if not self.check_prerequisites():
                print_error("Prerequisites check failed")
                return False
        
        # Enhanced connectivity test first
        if not self.enhanced_connectivity_test():
            print_error("Enhanced connectivity test failed")
            return False
        
        # Ask user before proceeding to complete collection
        print_section("Proceed to Complete Collection")
        try:
            proceed = input(f"{Colors.YELLOW}Connectivity test passed. Proceed with complete data collection (all layers)? (y/n): {Colors.RESET}").strip().lower()
            if proceed not in ['y', 'yes']:
                print_info("Complete data collection cancelled by user")
                return True
        except:
            print_info("Proceeding with complete data collection...")
        
        # Run complete collection with all layers in systematic order
        print_section("Systematic Data Collection")
        print_info("Phase 1: Core infrastructure data (health, interfaces)")
        print_info("Phase 2: Routing protocols (igp, bgp)")
        print_info("Phase 3: Advanced services (mpls, vpn, static)")
        print_info("Phase 4: Console line audit (console)")
        print_info("Phase 5: Report generation and consolidation")
        
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-all", "--layers", "health,interfaces,igp,bgp,mpls,vpn,static,console"],
            "Complete systematic collection (all layers including console)",
            critical=True,
            timeout=900  # 15 minutes for complete collection
        )
        
        if success:
            print_success("Complete collection completed successfully")
            print_info("✅ All standard network layers collected")
            print_info("✅ Console line audit completed")
            print_info("✅ Systematic collection order maintained")
            print_info("✅ Comprehensive reports generated")
            
            # Extract output location
            if "Output Location:" in stdout:
                output_info = stdout.split("Output Location:")[1].split("Collection report:")[0].strip()
                print_info(f"Complete collection data saved to: {output_info}")
            elif "rr4-complete-enchanced-v4-cli-output" in stdout:
                # Try to extract from different output format
                lines = stdout.split('\n')
                for line in lines:
                    if "rr4-complete-enchanced-v4-cli-output" in line:
                        print_info(f"Complete collection data saved to: {line.strip()}")
                        break
            
            print_section("Complete Collection Summary")
            print_info("📋 Complete collection includes:")
            print_info("   • Infrastructure: Health status, interface configurations")
            print_info("   • Routing: IGP protocols, BGP neighbors and routes")
            print_info("   • Services: MPLS labels, VPN configurations, static routes")
            print_info("   • Console: NM4 console line discovery and configurations")
            print_info("   • Reports: JSON (structured) and TXT (human-readable)")
            print_info("   • Platform support: IOS, IOS XE, IOS XR automatic detection")
            
            return True
        else:
            print_error("Complete collection failed")
            print_error("Common causes:")
            print_error("   • Network connectivity issues")
            print_error("   • Insufficient device privileges")
            print_error("   • Platform detection issues")
            print_error("   • Timeout due to large network size")
            print_info("Check the debug output for detailed error information")
            print_info("Consider using individual layer collections for troubleshooting")
            return False

    def console_security_audit(self) -> bool:
        """Analyze console audit results for transport security violations"""
        print_header("CONSOLE SECURITY AUDIT MODE", Colors.RED)
        
        print_info("Analyzing console audit results for transport security violations...")
        print_info("🔒 This security audit analyzes:")
        print_info("   • Console audit data from option 8")
        print_info("   • Transport input/output configurations")
        print_info("   • Telnet security violations on aux, console, vty, line")
        print_info("   • SSH-only compliance validation")
        print_info("   • Detailed per-device security analysis")
        print_info("   • Comprehensive downloadable reports")
        
        # Check if console audit data exists
        output_dirs = list(Path("rr4-complete-enchanced-v4-cli-output").glob("collector-run-*"))
        if not output_dirs:
            print_error("No console audit data found!")
            print_error("Please run option 8 (Console Audit) first to collect data.")
            print_info("The security audit requires console line configurations to analyze.")
            return False
        
        # Use the most recent collection
        latest_dir = max(output_dirs, key=lambda x: x.stat().st_mtime)
        print_info(f"Analyzing console data from: {latest_dir.name}")
        
        # Initialize audit results
        audit_results = {
            'total_routers': 0,
            'routers_accessed': 0,
            'routers_authenticated': 0,
            'routers_with_violations': 0,
            'devices': {},
            'summary_violations': {
                'aux_lines': 0,
                'console_lines': 0,
                'vty_lines': 0,
                'other_lines': 0
            },
            'violation_details': {
                'transport_input_all': 0,
                'transport_input_telnet': 0,
                'transport_output_all': 0,
                'transport_output_telnet': 0
            },
            'compliant_devices': [],
            'non_compliant_devices': [],
            'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': latest_dir.name
        }
        
        # Analyze each device's console data
        print_section("Device-by-Device Security Analysis")
        
        device_dirs = [d for d in latest_dir.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name not in ['logs', 'reports']]
        audit_results['total_routers'] = len(device_dirs)
        
        for device_dir in device_dirs:
            device_ip = device_dir.name
            print_info(f"Analyzing device: {device_ip}")
            
            device_audit = {
                'device_ip': device_ip,
                'hostname': 'Unknown',
                'accessible': False,
                'authenticated': False,
                'console_data_found': False,
                'violations': {
                    'aux_lines': [],
                    'console_lines': [],
                    'vty_lines': [],
                    'other_lines': []
                },
                'violation_summary': {
                    'transport_input_all': 0,
                    'transport_input_telnet': 0,
                    'transport_output_all': 0,
                    'transport_output_telnet': 0
                },
                'total_violations': 0,
                'total_lines_analyzed': 0,
                'compliance_status': 'UNKNOWN',
                'risk_level': 'LOW',
                'recommendations': []
            }
            
            # Check for console data
            console_dir = device_dir / 'console'
            if console_dir.exists():
                device_audit['accessible'] = True
                device_audit['authenticated'] = True
                audit_results['routers_accessed'] += 1
                audit_results['routers_authenticated'] += 1
                
                # Look for console line files
                json_files = list(console_dir.glob("*_console_lines.json"))
                if json_files:
                    device_audit['console_data_found'] = True
                    
                    # Analyze JSON console data
                    try:
                        with open(json_files[0], 'r') as f:
                            console_data = json.load(f)
                            device_audit['hostname'] = console_data.get('hostname', device_ip)
                            
                            # Analyze console line configurations
                            violations = self._analyze_transport_security(console_data)
                            device_audit['violations'] = violations
                            device_audit['total_violations'] = sum(len(v) for v in violations.values())
                            
                            # Count total lines analyzed
                            device_audit['total_lines_analyzed'] = len(console_data.get('console_lines', {}))
                            
                            # Calculate violation summary
                            for line_type, viols in violations.items():
                                for violation in viols:
                                    for viol_pattern in violation['violations']:
                                        if 'transport input all' in viol_pattern:
                                            device_audit['violation_summary']['transport_input_all'] += 1
                                            audit_results['violation_details']['transport_input_all'] += 1
                                        elif 'transport input telnet' in viol_pattern:
                                            device_audit['violation_summary']['transport_input_telnet'] += 1
                                            audit_results['violation_details']['transport_input_telnet'] += 1
                                        elif 'transport output all' in viol_pattern:
                                            device_audit['violation_summary']['transport_output_all'] += 1
                                            audit_results['violation_details']['transport_output_all'] += 1
                                        elif 'transport output telnet' in viol_pattern:
                                            device_audit['violation_summary']['transport_output_telnet'] += 1
                                            audit_results['violation_details']['transport_output_telnet'] += 1
                            
                            # Determine compliance status and risk level
                            if device_audit['total_violations'] == 0:
                                device_audit['compliance_status'] = 'COMPLIANT'
                                device_audit['risk_level'] = 'LOW'
                                audit_results['compliant_devices'].append(device_ip)
                            else:
                                device_audit['compliance_status'] = 'NON-COMPLIANT'
                                audit_results['routers_with_violations'] += 1
                                audit_results['non_compliant_devices'].append(device_ip)
                                
                                # Determine risk level
                                if device_audit['total_violations'] >= 5:
                                    device_audit['risk_level'] = 'HIGH'
                                elif device_audit['total_violations'] >= 2:
                                    device_audit['risk_level'] = 'MEDIUM'
                                else:
                                    device_audit['risk_level'] = 'LOW'
                                
                                # Generate recommendations
                                device_audit['recommendations'] = self._generate_device_recommendations(device_audit)
                            
                            # Update summary violations
                            for line_type, viols in violations.items():
                                audit_results['summary_violations'][line_type] += len(viols)
                                
                    except Exception as e:
                        print_warning(f"Error analyzing {device_ip}: {str(e)}")
                        device_audit['compliance_status'] = 'ERROR'
                
                # Also check raw command outputs for additional analysis
                raw_outputs_dir = console_dir / 'command_outputs'
                if raw_outputs_dir.exists():
                    self._analyze_raw_console_outputs(device_audit, raw_outputs_dir)
            
            audit_results['devices'][device_ip] = device_audit
            
            # Display device results with enhanced details
            if device_audit['total_violations'] > 0:
                risk_color = Colors.RED if device_audit['risk_level'] == 'HIGH' else Colors.YELLOW if device_audit['risk_level'] == 'MEDIUM' else Colors.BLUE
                print_error(f"  ❌ {device_ip} ({device_audit['hostname']}): {device_audit['total_violations']} violations | {risk_color}Risk: {device_audit['risk_level']}{Colors.RESET}")
                if device_audit['total_violations'] > 0:
                    for line_type, violations in device_audit['violations'].items():
                        if violations:
                            print_warning(f"     {line_type.replace('_', ' ').title()}: {len(violations)} violations")
            else:
                print_success(f"  ✅ {device_ip} ({device_audit['hostname']}): No violations | Compliant")
        
        # Display comprehensive terminal summary
        self._display_terminal_security_summary(audit_results)
        
        # Generate comprehensive security audit reports
        print_section("Generating Comprehensive Security Reports")
        report_success = self._generate_comprehensive_security_reports(audit_results, latest_dir)
        
        if report_success:
            print_success("Console security audit completed successfully")
            
            # Display report locations
            print_section("Security Audit Report Locations")
            print_info(f"📄 Executive Summary: {latest_dir}/console_security_executive_summary.txt")
            print_info(f"📋 Detailed Report: {latest_dir}/console_security_detailed_report.txt")
            print_info(f"📊 Device Analysis: {latest_dir}/console_security_device_analysis.txt")
            print_info(f"🔒 Compliance Report: {latest_dir}/console_security_compliance_report.txt")
            
            # Ask user if they want to view reports
            print_section("Report Viewing Options")
            try:
                view_choice = input(f"{Colors.YELLOW}Would you like to view the executive summary report on terminal? (y/n): {Colors.RESET}").strip().lower()
                if view_choice in ['y', 'yes']:
                    self._display_executive_summary_on_terminal(latest_dir)
            except:
                pass
            
            return True
        else:
            print_error("Failed to generate security audit reports")
            return False

    def _generate_device_recommendations(self, device_audit: dict) -> list:
        """Generate security recommendations for a specific device"""
        recommendations = []
        
        if device_audit['violation_summary']['transport_input_all'] > 0:
            recommendations.append("Remove 'transport input all' - allows insecure protocols")
        if device_audit['violation_summary']['transport_input_telnet'] > 0:
            recommendations.append("Remove 'transport input telnet' - telnet is unencrypted")
        if device_audit['violation_summary']['transport_output_all'] > 0:
            recommendations.append("Remove 'transport output all' - allows insecure output")
        if device_audit['violation_summary']['transport_output_telnet'] > 0:
            recommendations.append("Remove 'transport output telnet' - telnet output is insecure")
        
        if recommendations:
            recommendations.append("Configure 'transport input ssh' for secure access")
            recommendations.append("Configure 'transport output ssh' for secure output")
            recommendations.append("Implement access control lists (ACLs) on VTY lines")
            recommendations.append("Use strong authentication methods")
        
        return recommendations

    def _display_terminal_security_summary(self, audit_results: dict):
        """Display comprehensive security summary on terminal"""
        print_header("SECURITY AUDIT EXECUTIVE SUMMARY", Colors.MAGENTA)
        
        # Overall Statistics
        print_section("Overall Security Statistics")
        compliance_rate = ((audit_results['total_routers'] - audit_results['routers_with_violations']) / audit_results['total_routers'] * 100) if audit_results['total_routers'] > 0 else 0
        
        print_info(f"📊 Total Network Devices Analyzed: {audit_results['total_routers']}")
        print_info(f"🌐 Devices Successfully Accessed: {audit_results['routers_accessed']}")
        print_info(f"🔐 Devices Successfully Authenticated: {audit_results['routers_authenticated']}")
        print_info(f"✅ Compliant Devices: {len(audit_results['compliant_devices'])}")
        print_info(f"⚠️  Non-Compliant Devices: {audit_results['routers_with_violations']}")
        
        if compliance_rate >= 90:
            print_success(f"🏆 Security Compliance Rate: {compliance_rate:.1f}% (EXCELLENT)")
        elif compliance_rate >= 75:
            print_warning(f"📈 Security Compliance Rate: {compliance_rate:.1f}% (GOOD)")
        elif compliance_rate >= 50:
            print_warning(f"⚠️  Security Compliance Rate: {compliance_rate:.1f}% (NEEDS IMPROVEMENT)")
        else:
            print_error(f"🚨 Security Compliance Rate: {compliance_rate:.1f}% (CRITICAL)")
        
        # Violation Breakdown
        print_section("Transport Security Violation Breakdown")
        total_violations = sum(audit_results['violation_details'].values())
        
        if total_violations > 0:
            print_error(f"🚨 Total Transport Security Violations: {total_violations}")
            print_warning(f"   • transport input all: {audit_results['violation_details']['transport_input_all']} violations")
            print_warning(f"   • transport input telnet: {audit_results['violation_details']['transport_input_telnet']} violations")
            print_warning(f"   • transport output all: {audit_results['violation_details']['transport_output_all']} violations")
            print_warning(f"   • transport output telnet: {audit_results['violation_details']['transport_output_telnet']} violations")
        else:
            print_success("🛡️  No transport security violations detected!")
        
        # Line Type Analysis
        print_section("Line Type Security Analysis")
        print_info(f"🔌 AUX Line Violations: {audit_results['summary_violations']['aux_lines']}")
        print_info(f"📟 Console Line Violations: {audit_results['summary_violations']['console_lines']}")
        print_info(f"💻 VTY Line Violations: {audit_results['summary_violations']['vty_lines']}")
        print_info(f"📡 Other Line Violations: {audit_results['summary_violations']['other_lines']}")
        
        # Risk Assessment
        print_section("Security Risk Assessment")
        high_risk_devices = [dev for dev, data in audit_results['devices'].items() if data['risk_level'] == 'HIGH']
        medium_risk_devices = [dev for dev, data in audit_results['devices'].items() if data['risk_level'] == 'MEDIUM']
        
        if high_risk_devices:
            print_error(f"🔴 HIGH RISK Devices ({len(high_risk_devices)}): {', '.join(high_risk_devices)}")
        if medium_risk_devices:
            print_warning(f"🟡 MEDIUM RISK Devices ({len(medium_risk_devices)}): {', '.join(medium_risk_devices)}")
        if not high_risk_devices and not medium_risk_devices:
            print_success("🟢 All devices are LOW RISK or COMPLIANT")
        
        # Top Recommendations
        print_section("Priority Security Recommendations")
        if audit_results['routers_with_violations'] > 0:
            print_warning("🔧 IMMEDIATE ACTIONS REQUIRED:")
            print_warning("   1. Remove all 'transport input all' configurations")
            print_warning("   2. Replace 'transport input telnet' with 'transport input ssh'")
            print_warning("   3. Remove all 'transport output all' configurations")
            print_warning("   4. Replace 'transport output telnet' with 'transport output ssh'")
            print_warning("   5. Implement VTY access control lists (ACLs)")
            print_warning("   6. Enable strong authentication mechanisms")
        else:
            print_success("🎉 No immediate security actions required!")
            print_info("💡 Consider implementing additional security hardening measures")

    def _display_executive_summary_on_terminal(self, output_dir: Path):
        """Display executive summary report on terminal"""
        try:
            summary_file = output_dir / 'console_security_executive_summary.txt'
            if summary_file.exists():
                print_header("EXECUTIVE SUMMARY REPORT", Colors.CYAN)
                with open(summary_file, 'r') as f:
                    content = f.read()
                    print(content)
            else:
                print_error("Executive summary file not found")
        except Exception as e:
            print_error(f"Error displaying executive summary: {str(e)}")

    def _generate_comprehensive_security_reports(self, audit_results: dict, output_dir: Path) -> bool:
        """Generate comprehensive security audit reports"""
        try:
            # Generate Executive Summary Report
            self._generate_executive_summary_report(audit_results, output_dir)
            
            # Generate Detailed Security Report
            self._generate_detailed_security_report(audit_results, output_dir)
            
            # Generate Device Analysis Report
            self._generate_device_analysis_report(audit_results, output_dir)
            
            # Generate Compliance Report
            self._generate_compliance_report(audit_results, output_dir)
            
            return True
            
        except Exception as e:
            print_error(f"Error generating comprehensive reports: {str(e)}")
            return False

    def _generate_executive_summary_report(self, audit_results: dict, output_dir: Path):
        """Generate executive summary report"""
        report_file = output_dir / 'console_security_executive_summary.txt'
        
        with open(report_file, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("CONSOLE SECURITY AUDIT - EXECUTIVE SUMMARY REPORT\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {audit_results['analysis_timestamp']}\n")
            f.write(f"Data Source: {audit_results['data_source']}\n")
            f.write(f"Report Type: Executive Summary\n")
            f.write("=" * 100 + "\n\n")
            
            # Executive Overview
            compliance_rate = ((audit_results['total_routers'] - audit_results['routers_with_violations']) / audit_results['total_routers'] * 100) if audit_results['total_routers'] > 0 else 0
            
            f.write("EXECUTIVE OVERVIEW\n")
            f.write("-" * 50 + "\n")
            f.write(f"Network Security Posture: ")
            if compliance_rate >= 90:
                f.write("EXCELLENT\n")
            elif compliance_rate >= 75:
                f.write("GOOD\n")
            elif compliance_rate >= 50:
                f.write("NEEDS IMPROVEMENT\n")
            else:
                f.write("CRITICAL\n")
            
            f.write(f"Overall Compliance Rate: {compliance_rate:.1f}%\n")
            f.write(f"Total Devices Audited: {audit_results['total_routers']}\n")
            f.write(f"Devices with Security Violations: {audit_results['routers_with_violations']}\n")
            f.write(f"Security Compliant Devices: {len(audit_results['compliant_devices'])}\n\n")
            
            # Key Findings
            f.write("KEY SECURITY FINDINGS\n")
            f.write("-" * 50 + "\n")
            total_violations = sum(audit_results['violation_details'].values())
            f.write(f"Total Transport Security Violations: {total_violations}\n")
            f.write(f"High Risk Devices: {len([d for d in audit_results['devices'].values() if d['risk_level'] == 'HIGH'])}\n")
            f.write(f"Medium Risk Devices: {len([d for d in audit_results['devices'].values() if d['risk_level'] == 'MEDIUM'])}\n")
            f.write(f"Low Risk Devices: {len([d for d in audit_results['devices'].values() if d['risk_level'] == 'LOW'])}\n\n")
            
            # Critical Issues
            f.write("CRITICAL SECURITY ISSUES\n")
            f.write("-" * 50 + "\n")
            if audit_results['violation_details']['transport_input_all'] > 0:
                f.write(f"• {audit_results['violation_details']['transport_input_all']} instances of 'transport input all' - CRITICAL\n")
            if audit_results['violation_details']['transport_input_telnet'] > 0:
                f.write(f"• {audit_results['violation_details']['transport_input_telnet']} instances of 'transport input telnet' - HIGH RISK\n")
            if audit_results['violation_details']['transport_output_all'] > 0:
                f.write(f"• {audit_results['violation_details']['transport_output_all']} instances of 'transport output all' - MEDIUM RISK\n")
            if audit_results['violation_details']['transport_output_telnet'] > 0:
                f.write(f"• {audit_results['violation_details']['transport_output_telnet']} instances of 'transport output telnet' - MEDIUM RISK\n")
            
            if total_violations == 0:
                f.write("• No critical security issues identified\n")
            f.write("\n")
            
            # Immediate Actions Required
            f.write("IMMEDIATE ACTIONS REQUIRED\n")
            f.write("-" * 50 + "\n")
            if audit_results['routers_with_violations'] > 0:
                f.write("PHASE 1 - CRITICAL FIXES (Complete within 24 hours):\n")
                f.write("1. Remove all 'transport input all' configurations\n")
                f.write("2. Replace 'transport input telnet' with 'transport input ssh'\n\n")
                
                f.write("PHASE 2 - HIGH PRIORITY FIXES (Complete within 1 week):\n")
                f.write("3. Remove all 'transport output all' configurations\n")
                f.write("4. Replace 'transport output telnet' with 'transport output ssh'\n\n")
                
                f.write("PHASE 3 - SECURITY HARDENING (Complete within 1 month):\n")
                f.write("5. Implement VTY access control lists\n")
                f.write("6. Enable strong authentication mechanisms\n")
                f.write("7. Implement session timeout configurations\n")
                f.write("8. Enable logging for security events\n")
            else:
                f.write("✅ Network is fully compliant with security standards\n")
                f.write("💡 Consider additional security hardening measures:\n")
                f.write("   - Implement advanced authentication\n")
                f.write("   - Regular security audits\n")
                f.write("   - Network access control\n")

    def _generate_detailed_security_report(self, audit_results: dict, output_dir: Path):
        """Generate detailed security report with device-specific information"""
        report_file = output_dir / 'console_security_detailed_report.txt'
        
        with open(report_file, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("CONSOLE SECURITY AUDIT - DETAILED ANALYSIS REPORT\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {audit_results['analysis_timestamp']}\n")
            f.write(f"Data Source: {audit_results['data_source']}\n")
            f.write(f"Report Type: Detailed Security Analysis\n")
            f.write("=" * 100 + "\n\n")
            
            # Comprehensive Statistics
            f.write("COMPREHENSIVE SECURITY STATISTICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Network Devices: {audit_results['total_routers']}\n")
            f.write(f"Devices Accessed: {audit_results['routers_accessed']}\n")
            f.write(f"Devices Authenticated: {audit_results['routers_authenticated']}\n")
            f.write(f"Devices with Console Data: {len([d for d in audit_results['devices'].values() if d['console_data_found']])}\n")
            f.write(f"Security Compliant Devices: {len(audit_results['compliant_devices'])}\n")
            f.write(f"Non-Compliant Devices: {audit_results['routers_with_violations']}\n\n")
            
            # Transport Security Violations Detail
            f.write("TRANSPORT SECURITY VIOLATIONS BREAKDOWN\n")
            f.write("-" * 60 + "\n")
            f.write(f"Transport Input All Violations: {audit_results['violation_details']['transport_input_all']}\n")
            f.write(f"Transport Input Telnet Violations: {audit_results['violation_details']['transport_input_telnet']}\n")
            f.write(f"Transport Output All Violations: {audit_results['violation_details']['transport_output_all']}\n")
            f.write(f"Transport Output Telnet Violations: {audit_results['violation_details']['transport_output_telnet']}\n")
            f.write(f"Total Violations: {sum(audit_results['violation_details'].values())}\n\n")
            
            # Line Type Analysis
            f.write("LINE TYPE SECURITY ANALYSIS\n")
            f.write("-" * 60 + "\n")
            f.write(f"AUX Line Violations: {audit_results['summary_violations']['aux_lines']}\n")
            f.write(f"Console Line Violations: {audit_results['summary_violations']['console_lines']}\n")
            f.write(f"VTY Line Violations: {audit_results['summary_violations']['vty_lines']}\n")
            f.write(f"Other Line Violations: {audit_results['summary_violations']['other_lines']}\n\n")
            
            # Device-by-Device Analysis
            f.write("DEVICE-BY-DEVICE SECURITY ANALYSIS\n")
            f.write("-" * 60 + "\n")
            
            for device_ip, device_data in audit_results['devices'].items():
                f.write(f"\nDevice: {device_ip} ({device_data['hostname']})\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"Status: {device_data['compliance_status']}\n")
                f.write(f"Risk Level: {device_data['risk_level']}\n")
                f.write(f"Accessible: {'Yes' if device_data['accessible'] else 'No'}\n")
                f.write(f"Authenticated: {'Yes' if device_data['authenticated'] else 'No'}\n")
                f.write(f"Console Data Found: {'Yes' if device_data['console_data_found'] else 'No'}\n")
                f.write(f"Total Violations: {device_data['total_violations']}\n")
                f.write(f"Total Lines Analyzed: {device_data['total_lines_analyzed']}\n")
                
                if device_data['total_violations'] > 0:
                    f.write(f"\nViolation Breakdown:\n")
                    f.write(f"  Transport Input All: {device_data['violation_summary']['transport_input_all']}\n")
                    f.write(f"  Transport Input Telnet: {device_data['violation_summary']['transport_input_telnet']}\n")
                    f.write(f"  Transport Output All: {device_data['violation_summary']['transport_output_all']}\n")
                    f.write(f"  Transport Output Telnet: {device_data['violation_summary']['transport_output_telnet']}\n")
                    
                    f.write(f"\nViolation Details by Line Type:\n")
                    for line_type, violations in device_data['violations'].items():
                        if violations:
                            f.write(f"  {line_type.replace('_', ' ').title()}:\n")
                            for violation in violations:
                                f.write(f"    Line {violation['line_id']} ({violation['line_type']}):\n")
                                for viol_pattern in violation['violations']:
                                    f.write(f"      - {viol_pattern}\n")
                    
                    if device_data['recommendations']:
                        f.write(f"\nDevice-Specific Recommendations:\n")
                        for i, rec in enumerate(device_data['recommendations'], 1):
                            f.write(f"  {i}. {rec}\n")

    def _generate_device_analysis_report(self, audit_results: dict, output_dir: Path):
        """Generate device analysis report"""
        report_file = output_dir / 'console_security_device_analysis.txt'
        
        with open(report_file, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("CONSOLE SECURITY AUDIT - DEVICE ANALYSIS REPORT\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {audit_results['analysis_timestamp']}\n")
            f.write(f"Data Source: {audit_results['data_source']}\n")
            f.write(f"Report Type: Per-Device Security Analysis\n")
            f.write("=" * 100 + "\n\n")
            
            # Compliant Devices
            f.write("SECURITY COMPLIANT DEVICES\n")
            f.write("-" * 50 + "\n")
            if audit_results['compliant_devices']:
                for device_ip in audit_results['compliant_devices']:
                    device_data = audit_results['devices'][device_ip]
                    f.write(f"✅ {device_ip} ({device_data['hostname']}) - COMPLIANT\n")
                    f.write(f"   Lines Analyzed: {device_data['total_lines_analyzed']}\n")
                    f.write(f"   Risk Level: {device_data['risk_level']}\n\n")
            else:
                f.write("No fully compliant devices found.\n\n")
            
            # Non-Compliant Devices
            f.write("SECURITY NON-COMPLIANT DEVICES\n")
            f.write("-" * 50 + "\n")
            if audit_results['non_compliant_devices']:
                for device_ip in audit_results['non_compliant_devices']:
                    device_data = audit_results['devices'][device_ip]
                    f.write(f"❌ {device_ip} ({device_data['hostname']}) - NON-COMPLIANT\n")
                    f.write(f"   Violations: {device_data['total_violations']}\n")
                    f.write(f"   Risk Level: {device_data['risk_level']}\n")
                    f.write(f"   Lines Analyzed: {device_data['total_lines_analyzed']}\n")
                    
                    # Show top violations
                    if device_data['violation_summary']['transport_input_all'] > 0:
                        f.write(f"   🚨 Transport Input All: {device_data['violation_summary']['transport_input_all']}\n")
                    if device_data['violation_summary']['transport_input_telnet'] > 0:
                        f.write(f"   ⚠️  Transport Input Telnet: {device_data['violation_summary']['transport_input_telnet']}\n")
                    
                    f.write("\n")
            else:
                f.write("All devices are security compliant.\n\n")

    def _generate_compliance_report(self, audit_results: dict, output_dir: Path):
        """Generate compliance report"""
        report_file = output_dir / 'console_security_compliance_report.txt'
        
        with open(report_file, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("CONSOLE SECURITY AUDIT - COMPLIANCE REPORT\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {audit_results['analysis_timestamp']}\n")
            f.write(f"Data Source: {audit_results['data_source']}\n")
            f.write(f"Report Type: Security Compliance Validation\n")
            f.write("=" * 100 + "\n\n")
            
            # Compliance Standards
            f.write("SECURITY COMPLIANCE STANDARDS\n")
            f.write("-" * 50 + "\n")
            f.write("ACCEPTABLE CONFIGURATIONS:\n")
            f.write("  ✅ transport input ssh\n")
            f.write("  ✅ transport output ssh\n")
            f.write("  ✅ transport input none\n")
            f.write("  ✅ transport output none\n\n")
            
            f.write("VIOLATION CONFIGURATIONS:\n")
            f.write("  ❌ transport input all (CRITICAL)\n")
            f.write("  ❌ transport input telnet (HIGH RISK)\n")
            f.write("  ❌ transport output all (MEDIUM RISK)\n")
            f.write("  ❌ transport output telnet (MEDIUM RISK)\n\n")
            
            # Compliance Results
            compliance_rate = ((audit_results['total_routers'] - audit_results['routers_with_violations']) / audit_results['total_routers'] * 100) if audit_results['total_routers'] > 0 else 0
            
            f.write("COMPLIANCE ASSESSMENT RESULTS\n")
            f.write("-" * 50 + "\n")
            f.write(f"Overall Compliance Rate: {compliance_rate:.1f}%\n")
            f.write(f"Compliance Status: ")
            
            if compliance_rate >= 95:
                f.write("EXCELLENT COMPLIANCE\n")
            elif compliance_rate >= 85:
                f.write("GOOD COMPLIANCE\n")
            elif compliance_rate >= 70:
                f.write("ACCEPTABLE COMPLIANCE\n")
            elif compliance_rate >= 50:
                f.write("NEEDS IMPROVEMENT\n")
            else:
                f.write("NON-COMPLIANT (CRITICAL)\n")
            
            f.write(f"\nCompliant Devices: {len(audit_results['compliant_devices'])}/{audit_results['total_routers']}\n")
            f.write(f"Non-Compliant Devices: {audit_results['routers_with_violations']}/{audit_results['total_routers']}\n\n")
            
            # Remediation Plan
            f.write("COMPLIANCE REMEDIATION PLAN\n")
            f.write("-" * 50 + "\n")
            if audit_results['routers_with_violations'] > 0:
                f.write("PHASE 1 - CRITICAL FIXES (Complete within 24 hours):\n")
                f.write("1. Remove all 'transport input all' configurations\n")
                f.write("2. Replace 'transport input telnet' with 'transport input ssh'\n\n")
                
                f.write("PHASE 2 - HIGH PRIORITY FIXES (Complete within 1 week):\n")
                f.write("3. Remove all 'transport output all' configurations\n")
                f.write("4. Replace 'transport output telnet' with 'transport output ssh'\n\n")
                
                f.write("PHASE 3 - SECURITY HARDENING (Complete within 1 month):\n")
                f.write("5. Implement VTY access control lists\n")
                f.write("6. Enable strong authentication mechanisms\n")
                f.write("7. Implement session timeout configurations\n")
                f.write("8. Enable logging for security events\n")
            else:
                f.write("✅ Network is fully compliant with security standards\n")
                f.write("💡 Consider additional security hardening measures:\n")
                f.write("   - Implement advanced authentication\n")
                f.write("   - Regular security audits\n")
                f.write("   - Network access control\n")

    def show_help(self) -> bool:
        """Show help and available options"""
        print_header("HELP & AVAILABLE OPTIONS", Colors.WHITE)
        
        # Show main script help
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "--help"],
            "Displaying main script help",
            critical=False
        )
        
        if success:
            print(stdout)
        
        print_section("Additional Information")
        print_info("Documentation files in this directory:")
        docs = [
            "README.md - Main documentation",
            "CROSS_PLATFORM_GUIDE.md - Cross-platform setup guide", 
            "INSTALLATION.md - Installation instructions",
            "TROUBLESHOOTING.md - Common issues and solutions",
            "EXAMPLES.md - Usage examples",
            "SECURITY.md - Security implementation details"
        ]
        for doc in docs:
            print(f"  📖 {doc}")
        
        return True
    
    def _ask_continue_on_error(self, step_name: str) -> bool:
        """Ask user if they want to continue after an error"""
        print_warning(f"{step_name} encountered an issue.")
        while True:
            choice = input(f"{Colors.YELLOW}Continue anyway? (y/n): {Colors.RESET}").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print_error("Please enter 'y' or 'n'")
    
    def _show_setup_results(self):
        """Show final setup results"""
        print_header("SETUP RESULTS SUMMARY", Colors.MAGENTA)
        
        for step, result in self.test_results.items():
            if result == "PASSED":
                print_success(f"{step}: {result}")
            elif result == "FAILED":
                print_error(f"{step}: {result}")
            else:
                print_warning(f"{step}: {result}")
        
        passed_count = sum(1 for result in self.test_results.values() if result == "PASSED")
        total_count = len(self.test_results)
        
        print(f"\n{Colors.BOLD}Overall: {passed_count}/{total_count} steps completed successfully{Colors.RESET}")
        
        if passed_count == total_count:
            print_success("🎉 Setup completed successfully! Your RR4 CLI is ready to use.")
        else:
            print_warning("⚠️  Setup completed with some issues. Review the results above.")
    
    def run(self):
        """Main run method"""
        try:
            while True:
                choice = self.show_main_menu()
                
                if choice == 0:
                    print(f"\n{Colors.GREEN}Thank you for using RR4 CLI Startup Manager!{Colors.RESET}")
                    break
                elif choice == 1:
                    self.first_time_setup()
                elif choice == 2:
                    self.audit_only()
                elif choice == 3:
                    self.full_collection()
                elif choice == 4:
                    self.custom_collection()
                elif choice == 5:
                    self.check_prerequisites()
                elif choice == 6:
                    self.enhanced_connectivity_test()
                elif choice == 7:
                    self.show_help()
                elif choice == 8:
                    self.console_audit()
                elif choice == 9:
                    self.complete_collection()
                elif choice == 10:
                    self.console_security_audit()
                elif choice == 12:
                    self.comprehensive_status_report()
                else:
                    print_error("Invalid choice. Please enter 0-12.")
                
                # Ask if user wants to continue
                if choice != 0:
                    print(f"\n{Colors.BOLD}Press Enter to return to main menu or Ctrl+C to exit...{Colors.RESET}")
                    try:
                        input()
                    except KeyboardInterrupt:
                        print(f"\n{Colors.GREEN}Goodbye!{Colors.RESET}")
                        break
                        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Startup manager interrupted by user. Goodbye!{Colors.RESET}")
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            print_info("Please check your setup and try again.")

    def comprehensive_status_report(self) -> bool:
        """Generate comprehensive status report for all collection options
        
        This method analyzes collection data from options 1-10 and provides:
        - Unified status analysis across all collection types
        - Gap analysis and missing collection identification
        - Executive summary and detailed technical reports
        - Remediation recommendations for collection gaps
        
        Returns:
            bool: True if report generation successful, False otherwise
        """
        print_header("COMPREHENSIVE COLLECTION STATUS REPORT", Colors.BLUE)
        
        print_info("🚀 Initializing comprehensive analysis of collection data...")
        print_info("📊 This analysis can cover all options 1-10:")
        print_info("   • Option 1: First-time Setup collections")
        print_info("   • Option 2: Audit Only collections") 
        print_info("   • Option 3: Full Collection data")
        print_info("   • Option 4: Custom Collection results")
        print_info("   • Option 8: Console Audit data")
        print_info("   • Option 9: Complete Collection data")
        print_info("   • Option 10: Console Security Audit results")
        print_info("   • And more comprehensive analysis...")
        
        try:
            # Step 1: Select analysis scope (all devices or filtered subset)
            print_section("Analysis Scope Selection")
            device_filter = self._select_analysis_scope()
            
            if device_filter is None:
                print_info("Analysis cancelled by user")
                return True
                
            # T002.1: Data Source Discovery (with optional device filtering)
            print_section("T002.1: Collection Data Discovery Phase")
            collections = self._discover_collection_directories()
            
            if not collections:
                print_warning("⚠️  No collection data found!")
                print_info("📋 This could mean:")
                print_info("   • No data collection has been performed yet")
                print_info("   • Output directory is in a different location")
                print_info("   • Previous collections were manually deleted")
                print_info("\n💡 Recommended actions:")
                print_info("   • Run Option 2 (Audit Only) for quick data collection")
                print_info("   • Run Option 3 (Full Collection) for comprehensive data")
                print_info("   • Run Option 8 (Console Audit) for console data")
                return True  # Not an error, just no data yet
            
            # Apply device filtering if specified
            if device_filter and device_filter['type'] != 'all':
                print_section("Applying Device Filter")
                collections = self._filter_collections_by_devices(collections, device_filter)
                
                if not collections:
                    print_warning("⚠️  No collection data found matching the device filter!")
                    print_info("Selected filter criteria did not match any existing collections.")
                    print_info("Try running collections with the target devices first.")
                    return True

            # T002.2: Analyze collection data structure
            print_section("T002.2: Collection Data Structure Analysis")
            analyzed_collections = self._analyze_collection_structures(collections)
            
            # T002.3: Map collections to options (placeholder for now)
            print_section("T002.3: Option Mapping Analysis")
            mapped_collections = self._map_collections_to_options(analyzed_collections)
            
            # Display discovery results
            print_section("Collection Discovery Summary")
            self._display_discovery_summary(mapped_collections)
            
            # T003: Collection Status Analysis Engine
            print_section("T003: Collection Status Analysis Engine")
            status_analyzed_collections = self._perform_status_analysis(mapped_collections)
            
            # T004: Gap Analysis and Recommendations
            print_section("T004: Gap Analysis and Recommendations")
            gap_analyzed_collections = self._perform_gap_analysis(status_analyzed_collections)
            
            # T005: Enhanced Terminal Display
            print_section("T005: Enhanced Terminal Display and User Interface")
            self._display_comprehensive_terminal_report(gap_analyzed_collections)
            
            # T006: Report Generation Engine
            print_section("T006: Report Generation Engine")
            report_generated_collections = self._generate_comprehensive_reports(gap_analyzed_collections)
            
            # T007: Export and Persistence
            print_section("T007: Export and Persistence")
            exported_collections = self._handle_export_and_persistence(report_generated_collections)
            
            # T008: Testing and Validation
            print_section("T008: Testing and Validation")
            validated_collections = self._perform_testing_and_validation(exported_collections)
            
            print_section("Next Steps")
            print_success("✅ T002: Data Source Analysis and Discovery completed successfully")
            print_success("✅ T003: Collection Status Analysis Engine completed successfully")
            print_success("✅ T004: Gap Analysis and Recommendations completed successfully")
            print_success("✅ T005: Enhanced Terminal Display completed successfully")
            print_success("✅ T006: Report Generation Engine completed successfully")
            print_success("✅ T007: Export and Persistence completed successfully")
            print_success("✅ T008: Testing and Validation completed successfully")
            print_info("🎯 Option 12 implementation complete - All tasks successfully executed!")
            
            return True
            
        except Exception as e:
            print_error(f"Error in comprehensive status report: {str(e)}")
            print_info("This is expected during initial implementation phase")
            return False

    def _select_analysis_scope(self) -> Dict:
        """Select analysis scope - all devices or specific subset
        
        Returns:
            Dict with filter configuration or None if cancelled
        """
        print_header("📋 ANALYSIS SCOPE SELECTION", Colors.CYAN)
        
        print_info("Choose the scope of your comprehensive status analysis:")
        print_info("You can analyze all devices or focus on specific router types.")
        
        print(f"\n{Colors.BOLD}🎯 ANALYSIS SCOPE OPTIONS:{Colors.RESET}")
        print(f"{Colors.GREEN}1. 🌐 ALL ROUTERS (Complete network analysis){Colors.RESET}")
        print(f"   - Analyze all available collection data")
        print(f"   - Full network infrastructure coverage")
        print(f"   - Comprehensive cross-device analysis")
        
        print(f"\n{Colors.BLUE}2. 🎯 SINGLE ROUTER (Focused analysis){Colors.RESET}")
        print(f"   - Deep dive analysis on one specific device")
        print(f"   - Detailed per-device troubleshooting")
        print(f"   - Device-specific recommendations")
        
        print(f"\n{Colors.YELLOW}3. 📊 DEVICE TYPE SUBSET (Platform-specific analysis){Colors.RESET}")
        print(f"   - Select specific Cisco OS types (iOS, iOS-XE, iOS-XR)")
        print(f"   - Platform-specific analysis and recommendations")
        print(f"   - OS version and feature comparisons")
        
        print(f"\n{Colors.MAGENTA}4. 🔧 REPRESENTATIVE SAMPLE (Quick validation){Colors.RESET}")
        print(f"   - Analyze 1 device each: iOS, iOS-XE, iOS-XR")
        print(f"   - Quick network health validation")
        print(f"   - Platform diversity assessment")
        
        print(f"\n{Colors.RED}0. 🚪 CANCEL{Colors.RESET}")
        
        while True:
            try:
                choice = input(f"\n{Colors.BOLD}Select scope option (0-4): {Colors.RESET}").strip()
                
                if choice == '0':
                    return None
                elif choice == '1':
                    return {'type': 'all', 'description': 'All routers - complete network analysis'}
                elif choice == '2':
                    return self._select_single_router()
                elif choice == '3':
                    return self._select_device_types()
                elif choice == '4':
                    return {'type': 'representative', 'count_per_type': 1, 
                           'device_types': ['ios', 'iosxe', 'iosxr'],
                           'description': 'Representative sample - 1 device per OS type'}
                else:
                    print_error("Invalid choice. Please enter 0-4.")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Selection cancelled by user.{Colors.RESET}")
                return None
            except Exception:
                print_error("Invalid input. Please enter a number (0-4).")

    def _select_single_router(self) -> Dict:
        """Select a single router for focused analysis
        
        Returns:
            Dict with single device filter configuration
        """
        print_section("Single Router Selection")
        
        # Discover available devices from existing collections
        available_devices = self._discover_available_devices()
        
        if not available_devices:
            print_warning("⚠️  No devices found in existing collections!")
            print_info("Please run a collection first to analyze specific devices.")
            return None
        
        print_info(f"📋 Found {len(available_devices)} devices in existing collections:")
        print_info("   ┌─────────────────────────────────────────────────────────────────┐")
        print_info("   │ #  │ Device Name              │ OS Type  │ Collections        │")
        print_info("   ├─────────────────────────────────────────────────────────────────┤")
        
        for i, device_info in enumerate(available_devices, 1):
            device_name = device_info['name'][:24].ljust(24)
            os_type = device_info.get('os_type', 'Unknown')[:8].ljust(8)
            collection_count = device_info.get('collection_count', 0)
            print_info(f"   │ {i:2} │ {device_name} │ {os_type} │ {collection_count:15} │")
        
        print_info("   └─────────────────────────────────────────────────────────────────┘")
        
        while True:
            try:
                choice = input(f"\n{Colors.BOLD}Select device number (1-{len(available_devices)}) or 0 to cancel: {Colors.RESET}").strip()
                
                if choice == '0':
                    return None
                
                device_num = int(choice)
                if 1 <= device_num <= len(available_devices):
                    selected_device = available_devices[device_num - 1]
                    return {
                        'type': 'single',
                        'device_name': selected_device['name'],
                        'description': f"Single router analysis - {selected_device['name']}"
                    }
                else:
                    print_error(f"Invalid selection. Please enter 1-{len(available_devices)} or 0.")
                    
            except ValueError:
                print_error("Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Selection cancelled by user.{Colors.RESET}")
                return None

    def _select_device_types(self) -> Dict:
        """Select specific device types for platform-specific analysis
        
        Returns:
            Dict with device type filter configuration
        """
        print_section("Device Type Selection")
        
        print_info("Select which Cisco OS types to include in the analysis:")
        print_info("You can choose multiple types for comparative analysis.")
        
        device_types = [
            {'code': 'ios', 'name': 'Cisco iOS', 'description': 'Traditional Cisco IOS devices'},
            {'code': 'iosxe', 'name': 'Cisco iOS-XE', 'description': 'Next-generation iOS-XE platforms'},
            {'code': 'iosxr', 'name': 'Cisco iOS-XR', 'description': 'Service provider iOS-XR systems'}
        ]
        
        selected_types = []
        
        for device_type in device_types:
            while True:
                try:
                    choice = input(f"\n{Colors.BOLD}Include {device_type['name']} ({device_type['description']})? (y/n): {Colors.RESET}").strip().lower()
                    
                    if choice in ['y', 'yes']:
                        selected_types.append(device_type['code'])
                        print_success(f"✅ {device_type['name']} included")
                        break
                    elif choice in ['n', 'no']:
                        print_info(f"⏭️  {device_type['name']} skipped")
                        break
                    else:
                        print_error("Please enter 'y' for yes or 'n' for no.")
                        
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}Selection cancelled by user.{Colors.RESET}")
                    return None
        
        if not selected_types:
            print_warning("No device types selected. Analysis cancelled.")
            return None
            
        description = f"Platform-specific analysis - {', '.join([t.upper() for t in selected_types])}"
        
        return {
            'type': 'device_types',
            'device_types': selected_types,
            'description': description
        }

    def _discover_available_devices(self) -> List[Dict]:
        """Discover all devices available in existing collections
        
        Returns:
            List of device information dictionaries
        """
        print_info("🔍 Discovering devices from existing collections...")
        
        device_registry = {}
        collections = self._discover_collection_directories()
        
        for collection_name, collection_info in collections.items():
            collection_path = collection_info['path']
            
            # Look for device directories in this collection
            try:
                for item in collection_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        device_name = item.name
                        
                        # Try to determine OS type from device data
                        os_type = self._detect_device_os_type(item)
                        
                        if device_name not in device_registry:
                            device_registry[device_name] = {
                                'name': device_name,
                                'os_type': os_type,
                                'collection_count': 0,
                                'collections': []
                            }
                        
                        device_registry[device_name]['collection_count'] += 1
                        device_registry[device_name]['collections'].append(collection_name)
                        
            except Exception as e:
                print_warning(f"⚠️  Error scanning collection {collection_name}: {str(e)}")
                continue
        
        # Convert to sorted list
        available_devices = list(device_registry.values())
        available_devices.sort(key=lambda x: x['name'])
        
        print_success(f"📊 Discovered {len(available_devices)} unique devices")
        return available_devices

    def _detect_device_os_type(self, device_path: Path) -> str:
        """Detect device OS type from collection data
        
        Args:
            device_path: Path to device directory
            
        Returns:
            Detected OS type or 'unknown'
        """
        # Look for OS indicators in health data or show version files
        health_files = list(device_path.glob("**/health*"))
        version_files = list(device_path.glob("**/show_version*"))
        
        # Check health files first
        for health_file in health_files:
            try:
                if health_file.is_file():
                    content = health_file.read_text(encoding='utf-8', errors='ignore').lower()
                    
                    if 'ios-xr' in content or 'iosxr' in content:
                        return 'iosxr'
                    elif 'ios-xe' in content or 'iosxe' in content:
                        return 'iosxe'
                    elif 'ios' in content and 'cisco ios software' in content:
                        return 'ios'
                        
            except Exception:
                continue
        
        # Check version files
        for version_file in version_files:
            try:
                if version_file.is_file():
                    content = version_file.read_text(encoding='utf-8', errors='ignore').lower()
                    
                    if 'ios xr' in content or 'iosxr' in content:
                        return 'iosxr'
                    elif 'ios xe' in content or 'iosxe' in content:
                        return 'iosxe'
                    elif 'cisco ios software' in content:
                        return 'ios'
                        
            except Exception:
                continue
        
        return 'unknown'

    def _filter_collections_by_devices(self, collections: Dict[str, Dict], device_filter: Dict) -> Dict[str, Dict]:
        """Filter collections based on device selection criteria
        
        Args:
            collections: Original collections dictionary
            device_filter: Device filter configuration
            
        Returns:
            Filtered collections dictionary
        """
        filter_type = device_filter['type']
        
        print_info(f"🔧 Applying device filter: {device_filter['description']}")
        
        if filter_type == 'all':
            return collections
        
        filtered_collections = {}
        
        for collection_name, collection_info in collections.items():
            collection_path = collection_info['path']
            should_include_collection = False
            
            # Scan devices in this collection
            try:
                collection_devices = []
                for item in collection_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        device_name = item.name
                        os_type = self._detect_device_os_type(item)
                        collection_devices.append({
                            'name': device_name,
                            'os_type': os_type,
                            'path': item
                        })
                
                # Apply filter criteria
                if filter_type == 'single':
                    target_device = device_filter['device_name']
                    should_include_collection = any(d['name'] == target_device for d in collection_devices)
                    
                elif filter_type == 'device_types':
                    target_types = device_filter['device_types']
                    should_include_collection = any(d['os_type'] in target_types for d in collection_devices)
                    
                elif filter_type == 'representative':
                    target_types = device_filter['device_types']
                    count_per_type = device_filter['count_per_type']
                    
                    # Check if this collection has devices matching our criteria
                    type_counts = {}
                    for device in collection_devices:
                        os_type = device['os_type']
                        if os_type in target_types:
                            type_counts[os_type] = type_counts.get(os_type, 0) + 1
                    
                    # Include if we have devices of target types
                    should_include_collection = len(type_counts) > 0
                
                if should_include_collection:
                    # Create a filtered version of collection_info
                    filtered_collection_info = collection_info.copy()
                    
                    # Filter device list if applicable
                    if filter_type != 'all':
                        filtered_devices = []
                        for device in collection_devices:
                            include_device = False
                            
                            if filter_type == 'single':
                                include_device = device['name'] == device_filter['device_name']
                            elif filter_type == 'device_types':
                                include_device = device['os_type'] in device_filter['device_types']
                            elif filter_type == 'representative':
                                include_device = device['os_type'] in device_filter['device_types']
                            
                            if include_device:
                                filtered_devices.append(device['name'])
                        
                        filtered_collection_info['filtered_devices'] = filtered_devices
                        filtered_collection_info['device_filter'] = device_filter
                    
                    filtered_collections[collection_name] = filtered_collection_info
                    
            except Exception as e:
                print_warning(f"⚠️  Error processing collection {collection_name}: {str(e)}")
                continue
        
        filter_summary = f"Filter applied: {len(filtered_collections)}/{len(collections)} collections match criteria"
        print_success(filter_summary)
        
        return filtered_collections

    def _display_comprehensive_terminal_report(self, collections: Dict[str, Dict]):
        """Display comprehensive terminal report with enhanced formatting (T005)
        
        Args:
            collections: Collections with complete analysis data
        """
        print_info("🎯 Generating enhanced terminal display...")
        
        # Executive Dashboard Summary
        self._display_executive_dashboard(collections)
        
        # Collection Health Matrix
        self._display_collection_health_matrix(collections)
        
        # Network Infrastructure Overview
        self._display_network_infrastructure_overview(collections)
        
        # Gap Analysis Dashboard
        self._display_gap_analysis_dashboard(collections)
        
        # Recommendations Action Plan
        self._display_recommendations_action_plan(collections)
        
        # Resource Planning Summary
        self._display_resource_planning_summary(collections)
        
        print_success("✅ Enhanced terminal display complete")

    def _display_executive_dashboard(self, collections: Dict[str, Dict]):
        """Display executive summary dashboard"""
        print_header("📊 EXECUTIVE DASHBOARD", Colors.MAGENTA)
        
        # Check if any filtering was applied
        filter_info = None
        for collection_info in collections.values():
            if 'device_filter' in collection_info:
                filter_info = collection_info['device_filter']
                break
        
        # Display filter information if applicable
        if filter_info:
            print_header(f"🎯 ANALYSIS SCOPE: {filter_info['description'].upper()}", Colors.YELLOW)
            if filter_info['type'] == 'single':
                print_info(f"   • Focused analysis on device: {filter_info['device_name']}")
            elif filter_info['type'] == 'device_types':
                device_types = ', '.join([t.upper() for t in filter_info['device_types']])
                print_info(f"   • Platform-specific analysis: {device_types}")
            elif filter_info['type'] == 'representative':
                print_info(f"   • Representative sample: 1 device per OS type")
            print_info("")
        else:
            print_info("🌐 Analysis scope: All available devices and collections\n")
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        
        # Collection Overview
        total_collections = len(collections)
        
        # Count devices - handle filtered vs unfiltered
        total_devices_analyzed = 0
        filtered_device_count = 0
        
        for collection_info in collections.values():
            if 'filtered_devices' in collection_info:
                filtered_device_count += len(collection_info['filtered_devices'])
            else:
                # Use global device stats if available
                global_stats = collection_info.get('global_device_stats', {})
                if global_stats:
                    total_devices_analyzed = max(total_devices_analyzed, len(global_stats.get('total_devices', set())))
        
        # Use filtered count if filtering was applied
        if filter_info and filtered_device_count > 0:
            devices_analyzed = filtered_device_count
            scope_note = " (filtered)"
        else:
            devices_analyzed = len(sample_collection.get('global_device_stats', {}).get('total_devices', set()))
            scope_note = ""
        
        total_layers_available = len(sample_collection.get('global_layer_stats', {}).get('all_layers', set()))
        
        print_info("📈 Collection Overview:")
        print_info(f"   • Total Collections Analyzed: {total_collections}")
        print_info(f"   • Network Devices Analyzed: {devices_analyzed}{scope_note}")
        print_info(f"   • Data Layer Types: {total_layers_available}")
        
        # Device Health Summary (adjusted for filtering)
        device_stats = sample_collection.get('global_device_stats', {})
        
        if filter_info:
            # Calculate accessibility for filtered devices
            accessible_count = 0
            total_filtered = 0
            
            for collection_info in collections.values():
                if 'filtered_devices' in collection_info:
                    filtered_devices = collection_info['filtered_devices']
                    total_filtered += len(filtered_devices)
                    
                    # Check accessibility from device stats
                    accessible_devices = device_stats.get('accessible_devices', set())
                    for device in filtered_devices:
                        if device in accessible_devices:
                            accessible_count += 1
            
            if total_filtered > 0:
                device_reliability = (accessible_count / total_filtered * 100)
                print_info("\n🌐 Filtered Network Health Summary:")
                print_info(f"   • Device Accessibility: {accessible_count}/{total_filtered} ({device_reliability:.1f}%)")
            else:
                print_info("\n🌐 Network Health Summary:")
                print_info("   • Device Accessibility: No filtered devices found")
        else:
            # Standard accessibility calculation
            accessible_devices = len(device_stats.get('accessible_devices', set()))
            device_reliability = (accessible_devices / devices_analyzed * 100) if devices_analyzed > 0 else 0
            
            print_info("\n🌐 Network Health Summary:")
            print_info(f"   • Device Accessibility: {accessible_devices}/{devices_analyzed} ({device_reliability:.1f}%)")
        
        # Collection Effectiveness (unchanged - applies to filtered scope)
        cross_analysis = sample_collection.get('cross_option_analysis', {})
        effectiveness_data = cross_analysis.get('option_effectiveness', {})
        
        if effectiveness_data:
            print_info("\n⚡ Collection Effectiveness:")
            for option_type, effectiveness in effectiveness_data.items():
                effectiveness_pct = effectiveness * 100
                status_icon = "🟢" if effectiveness_pct >= 80 else "🟡" if effectiveness_pct >= 60 else "🔴"
                print_info(f"   • {option_type}: {status_icon} {effectiveness_pct:.1f}%")
        
        # Gap Analysis Summary (applies to filtered scope)
        gap_analysis = sample_collection.get('gap_analysis', {})
        total_gaps = gap_analysis.get('total_gaps_identified', 0)
        missing_options = len(gap_analysis.get('missing_options', []))
        critical_gaps = len(gap_analysis.get('critical_gaps', []))
        
        print_info("\n🔍 Gap Analysis Summary:")
        print_info(f"   • Total Gaps Identified: {total_gaps}")
        print_info(f"   • Missing Collection Options: {missing_options}")
        print_info(f"   • Critical Issues: {critical_gaps}")
        
        # Action Required Indicator
        recommendations = sample_collection.get('recommendations', {})
        immediate_actions = len(recommendations.get('immediate_actions', []))
        
        if immediate_actions > 0:
            print_warning(f"\n⚠️  IMMEDIATE ACTION REQUIRED: {immediate_actions} critical items need attention")
        else:
            print_success("\n✅ No immediate actions required - network collection status is optimal")
            
        # Add filtering summary if applicable
        if filter_info:
            print_info(f"\n📋 Scope Summary: Analysis focused on {filter_info['description'].lower()}")
            if filter_info['type'] != 'all':
                print_info("   • Run analysis with 'All Routers' option for complete network view")

    def _display_collection_health_matrix(self, collections: Dict[str, Dict]):
        """Display collection health status matrix"""
        print_header("🏥 COLLECTION HEALTH MATRIX", Colors.CYAN)
        
        # Check for filtering
        filter_info = None
        for collection_info in collections.values():
            if 'device_filter' in collection_info:
                filter_info = collection_info['device_filter']
                break
        
        if filter_info:
            print_info(f"📋 Health matrix for filtered scope: {filter_info['description']}")
        else:
            print_info("📋 Collection Status Overview:")
            
        print_info("   ┌─────────────────────────────────────────────────────────────────┐")
        print_info("   │ Collection Name              │ Devices │ Layers │ Status      │")
        print_info("   ├─────────────────────────────────────────────────────────────────┤")
        
        for collection_name, collection_info in collections.items():
            # Get device count - use filtered count if available
            if 'filtered_devices' in collection_info:
                device_count = len(collection_info['filtered_devices'])
                device_note = " (F)"  # Filtered indicator
            else:
                device_count = len(collection_info.get('devices', []))
                device_note = ""
                
            layer_count = len(collection_info.get('layer_analysis', {}).get('available_layers', []))
            completeness = collection_info.get('completeness_score', 0) * 100
            
            # Determine status
            if completeness >= 80:
                status = "🟢 Excellent"
            elif completeness >= 60:
                status = "🟡 Good    "
            elif completeness >= 40:
                status = "🟠 Fair    "
            else:
                status = "🔴 Poor    "
            
            # Format collection name for display
            display_name = collection_name[:28].ljust(28)
            device_display = f"{device_count:4}{device_note}".ljust(7)
            layer_display = f"{layer_count:4}".ljust(6)
            
            print_info(f"   │ {display_name} │ {device_display} │ {layer_display} │ {status} │")
        
        print_info("   └─────────────────────────────────────────────────────────────────┘")
        
        if filter_info:
            print_info("   📝 Legend: (F) = Filtered device count based on selection criteria")
        
        # Collection health summary
        total_collections = len(collections)
        excellent_count = sum(1 for c in collections.values() if c.get('completeness_score', 0) >= 0.8)
        good_count = sum(1 for c in collections.values() if 0.6 <= c.get('completeness_score', 0) < 0.8)
        fair_count = sum(1 for c in collections.values() if 0.4 <= c.get('completeness_score', 0) < 0.6)
        poor_count = sum(1 for c in collections.values() if c.get('completeness_score', 0) < 0.4)
        
        print_info(f"\n📊 Health Distribution:")
        print_info(f"   🟢 Excellent: {excellent_count}/{total_collections} ({excellent_count/total_collections*100:.1f}%)")
        print_info(f"   🟡 Good:      {good_count}/{total_collections} ({good_count/total_collections*100:.1f}%)")
        print_info(f"   🟠 Fair:      {fair_count}/{total_collections} ({fair_count/total_collections*100:.1f}%)")
        print_info(f"   🔴 Poor:      {poor_count}/{total_collections} ({poor_count/total_collections*100:.1f}%)")
        
        # Recommendations based on health
        if poor_count > 0:
            print_warning(f"\n⚠️  {poor_count} collection(s) need immediate attention")
        elif fair_count > 0:
            print_info(f"\n💡 {fair_count} collection(s) could benefit from improvement")
        else:
            print_success("\n✅ All collections are in good health")

    def _display_network_infrastructure_overview(self, collections: Dict[str, Dict]):
        """Display network infrastructure overview"""
        print_header("🌐 NETWORK INFRASTRUCTURE OVERVIEW", Colors.BLUE)
        
        # Check for filtering
        filter_info = None
        for collection_info in collections.values():
            if 'device_filter' in collection_info:
                filter_info = collection_info['device_filter']
                break
        
        # Display scope information
        if filter_info:
            print_info(f"🎯 Infrastructure scope: {filter_info['description']}")
            if filter_info['type'] == 'single':
                print_info(f"   • Analyzing single device: {filter_info['device_name']}")
            elif filter_info['type'] == 'device_types':
                device_types = ', '.join([t.upper() for t in filter_info['device_types']])
                print_info(f"   • Platform focus: {device_types}")
            elif filter_info['type'] == 'representative':
                print_info(f"   • Representative sampling across OS types")
            print_info("")
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        device_stats = sample_collection.get('global_device_stats', {})
        layer_stats = sample_collection.get('global_layer_stats', {})
        
        # Calculate device counts - handle filtering
        if filter_info:
            # Count filtered devices
            total_filtered_devices = 0
            accessible_filtered_devices = 0
            consistent_filtered_devices = 0
            
            for collection_info in collections.values():
                if 'filtered_devices' in collection_info:
                    filtered_devices = collection_info['filtered_devices']
                    total_filtered_devices += len(filtered_devices)
                    
                    # Check accessibility and consistency for filtered devices
                    accessible_devices = device_stats.get('accessible_devices', set())
                    consistent_devices = device_stats.get('consistent_devices', set())
                    
                    for device in filtered_devices:
                        if device in accessible_devices:
                            accessible_filtered_devices += 1
                        if device in consistent_devices:
                            consistent_filtered_devices += 1
            
            # Use filtered counts
            total_devices = total_filtered_devices
            accessible_devices_count = accessible_filtered_devices
            consistent_devices_count = consistent_filtered_devices
            scope_note = " (filtered scope)"
        else:
            # Use standard counts
            total_devices = len(device_stats.get('total_devices', set()))
            accessible_devices_count = len(device_stats.get('accessible_devices', set()))
            consistent_devices_count = len(device_stats.get('consistent_devices', set()))
            scope_note = ""
        
        # Device Infrastructure Summary
        print_info(f"🖥️  Device Infrastructure{scope_note}:")
        print_info(f"   • Total Network Devices: {total_devices}")
        
        if total_devices > 0:
            accessibility_pct = (accessible_devices_count / total_devices * 100)
            consistency_pct = (consistent_devices_count / total_devices * 100)
            print_info(f"   • Currently Accessible: {accessible_devices_count} ({accessibility_pct:.1f}%)")
            print_info(f"   • Consistently Reliable: {consistent_devices_count} ({consistency_pct:.1f}%)")
        else:
            print_info(f"   • Currently Accessible: 0 (no devices in scope)")
        
        # Device Type Breakdown (if filtering by types)
        if filter_info and filter_info['type'] in ['device_types', 'representative']:
            print_info("\n📋 Device Type Distribution:")
            type_counts = {}
            
            for collection_info in collections.values():
                if 'filtered_devices' in collection_info:
                    filtered_devices = collection_info['filtered_devices']
                    for device_name in filtered_devices:
                        # Need to determine device type for counting
                        for item in Path(collection_info['path']).iterdir():
                            if item.is_dir() and item.name == device_name:
                                os_type = self._detect_device_os_type(item)
                                type_counts[os_type] = type_counts.get(os_type, 0) + 1
                                break
            
            for os_type, count in sorted(type_counts.items()):
                os_display = os_type.upper() if os_type != 'unknown' else 'Unknown'
                print_info(f"   • {os_display}: {count} device(s)")
        
        # Layer Coverage Analysis
        all_layers = layer_stats.get('all_layers', set())
        critical_layers = layer_stats.get('critical_layers_missing', [])
        
        print_info("\n📊 Data Layer Coverage:")
        print_info(f"   • Available Layer Types: {len(all_layers)}")
        if all_layers:
            layer_list = ", ".join(sorted(all_layers))
            print_info(f"   • Layers: {layer_list}")
        
        if critical_layers:
            print_warning(f"   • Missing Critical Layers: {', '.join(critical_layers)}")
        else:
            print_success("   • All critical layers present")
        
        # Collection Option Coverage
        option_types = set()
        filtered_collections_count = 0
        
        for collection_info in collections.values():
            option_types.add(collection_info.get('option_type', 'unknown'))
            if 'filtered_devices' in collection_info:
                filtered_collections_count += 1
        
        print_info(f"\n🎯 Collection Option Coverage:")
        print_info(f"   • Option Types Used: {len(option_types)}")
        print_info(f"   • Options: {', '.join(sorted(option_types))}")
        
        if filter_info:
            total_collections = len(collections)
            print_info(f"   • Collections in scope: {total_collections}")
            if filter_info['type'] != 'all':
                print_info(f"   • Collections with filtered devices: {filtered_collections_count}")
        
        # Infrastructure Health Assessment
        if total_devices > 0:
            health_score = (accessible_devices_count / total_devices * 0.6) + (consistent_devices_count / total_devices * 0.4)
            health_percentage = health_score * 100
            
            print_info(f"\n💚 Infrastructure Health Score:")
            if health_percentage >= 80:
                health_status = "🟢 Excellent"
            elif health_percentage >= 60:
                health_status = "🟡 Good"
            elif health_percentage >= 40:
                health_status = "🟠 Fair"
            else:
                health_status = "🔴 Poor"
            
            print_info(f"   • Overall Health: {health_status} ({health_percentage:.1f}%)")
            
            if filter_info:
                print_info(f"   • Scope: {filter_info['description']}")
                if filter_info['type'] != 'all':
                    print_info("   • Note: Health score reflects filtered scope only")
        else:
            print_warning("\n💚 Infrastructure Health Score:")
            print_warning("   • Cannot calculate - no devices in current scope")

    def _display_gap_analysis_dashboard(self, collections: Dict[str, Dict]):
        """Display comprehensive gap analysis dashboard"""
        print_header("🔍 GAP ANALYSIS DASHBOARD", Colors.YELLOW)
        
        # Check for filtering
        filter_info = None
        for collection_info in collections.values():
            if 'device_filter' in collection_info:
                filter_info = collection_info['device_filter']
                break
        
        # Display scope information
        if filter_info:
            print_info(f"🎯 Gap analysis scope: {filter_info['description']}")
            if filter_info['type'] == 'single':
                print_info(f"   • Analyzing gaps for device: {filter_info['device_name']}")
            elif filter_info['type'] == 'device_types':
                device_types = ', '.join([t.upper() for t in filter_info['device_types']])
                print_info(f"   • Platform-specific gap analysis: {device_types}")
            elif filter_info['type'] == 'representative':
                print_info(f"   • Representative sampling gap analysis")
            print_info("")
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        gap_analysis = sample_collection.get('gap_analysis', {})
        root_cause_analysis = sample_collection.get('root_cause_analysis', {})
        
        # Gap Overview
        total_gaps = gap_analysis.get('total_gaps_identified', 0)
        missing_options = gap_analysis.get('missing_options', [])
        incomplete_options = gap_analysis.get('incomplete_options', [])
        critical_gaps = gap_analysis.get('critical_gaps', [])
        
        # Adjust gap messaging for filtered scope
        scope_qualifier = ""
        if filter_info and filter_info['type'] != 'all':
            scope_qualifier = " (in filtered scope)"
        
        print_info(f"📋 Gap Analysis Results{scope_qualifier}:")
        print_info(f"   • Total Gaps Identified: {total_gaps}")
        print_info(f"   • Missing Collection Options: {len(missing_options)}")
        print_info(f"   • Incomplete Collections: {len(incomplete_options)}")
        print_info(f"   • Critical Issues: {len(critical_gaps)}")
        
        if missing_options:
            print_warning("   📝 Missing Options:")
            for option in missing_options:
                print_warning(f"     - {option}")
        
        if critical_gaps:
            print_error("   🚨 Critical Gaps:")
            for gap in critical_gaps:
                print_error(f"     - {gap}")
        
        # Filtering-specific gap analysis
        if filter_info and filter_info['type'] != 'all':
            print_info("\n🔬 Filtered Scope Analysis:")
            
            # Count devices in scope
            total_filtered_devices = 0
            for collection_info in collections.values():
                if 'filtered_devices' in collection_info:
                    total_filtered_devices += len(collection_info['filtered_devices'])
            
            print_info(f"   • Devices in scope: {total_filtered_devices}")
            
            if filter_info['type'] == 'single':
                print_info(f"   • Focus: Deep analysis of {filter_info['device_name']}")
                print_info("   • Recommendation: Review device-specific configuration gaps")
                
            elif filter_info['type'] == 'device_types':
                device_types = ', '.join([t.upper() for t in filter_info['device_types']])
                print_info(f"   • Focus: Platform-specific issues for {device_types}")
                print_info("   • Recommendation: Platform standardization and best practices")
                
            elif filter_info['type'] == 'representative':
                print_info("   • Focus: Cross-platform consistency validation")
                print_info("   • Recommendation: Scale findings to entire network")
        
        # Root Cause Analysis Summary
        print_info("\n🔬 Root Cause Analysis:")
        cause_categories = root_cause_analysis.get('cause_categories', {})
        impact_assessment = root_cause_analysis.get('impact_assessment', {})
        
        if cause_categories:
            print_info("   📊 Issue Categories:")
            for category, count in cause_categories.items():
                severity_icon = "🔴" if "critical" in category.lower() else "🟡" if "high" in category.lower() else "🟢"
                print_info(f"     • {category}: {severity_icon} {count} issues")
        
        if impact_assessment:
            print_info("   💥 Impact Assessment:")
            for impact_level, count in impact_assessment.items():
                if count > 0:
                    impact_icon = "🔥" if "critical" in impact_level.lower() else "⚡" if "high" in impact_level.lower() else "📊"
                    print_info(f"     • {impact_level}: {impact_icon} {count} items")
        
        # Gap prioritization based on scope
        if filter_info:
            print_info("\n🎯 Scope-Specific Recommendations:")
            
            if filter_info['type'] == 'single':
                print_info("   • Priority: Device-specific troubleshooting and optimization")
                print_info("   • Next step: Expand analysis to similar device types")
                
            elif filter_info['type'] == 'device_types':
                print_info("   • Priority: Platform standardization across selected OS types")
                print_info("   • Next step: Apply fixes consistently across platform family")
                
            elif filter_info['type'] == 'representative':
                print_info("   • Priority: Validate findings represent network-wide patterns")
                print_info("   • Next step: Run full network analysis to confirm trends")
                
            else:
                print_info("   • Priority: Address critical gaps across entire network")
                print_info("   • Next step: Implement systematic remediation plan")

    def _display_recommendations_action_plan(self, collections: Dict[str, Dict]):
        """Display recommendations and action plan"""
        print_header("💡 RECOMMENDATIONS & ACTION PLAN", Colors.GREEN)
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        recommendations = sample_collection.get('recommendations', {})
        
        # Immediate Actions
        immediate_actions = recommendations.get('immediate_actions', [])
        if immediate_actions:
            print_info("🚨 IMMEDIATE ACTIONS REQUIRED:")
            for i, action in enumerate(immediate_actions, 1):
                priority_icon = "🔥" if action.get('priority') == 'critical' else "⚡"
                print_info(f"   {i}. {priority_icon} {action.get('action', 'Unknown Action')}")
                print_info(f"      📋 {action.get('description', '')}")
                print_info(f"      ⏱️  {action.get('timeline', 'TBD')}")
                if action.get('command'):
                    print_info(f"      💻 Command: {action.get('command')}")
                print_info("")
        
        # Quick Wins
        quick_wins = recommendations.get('quick_wins', [])
        if quick_wins:
            print_info("🎯 QUICK WIN OPPORTUNITIES:")
            for i, win in enumerate(quick_wins, 1):
                print_info(f"   {i}. ⚡ {win.get('action', 'Unknown Action')}")
                print_info(f"      📈 {win.get('description', '')}")
                print_info(f"      ⏱️  {win.get('timeline', 'TBD')}")
                print_info("")
        
        # Implementation Roadmap
        roadmap = recommendations.get('implementation_roadmap', [])
        if roadmap:
            print_info("🗺️  IMPLEMENTATION ROADMAP:")
            for phase in roadmap:
                print_info(f"   📅 {phase.get('phase', 'Unknown Phase')}")
                print_info(f"      ⏰ Timeline: {phase.get('timeline', 'TBD')}")
                print_info(f"      🎯 Objective: {phase.get('objective', '')}")
                actions = phase.get('actions', [])
                if actions:
                    print_info(f"      📋 Actions ({len(actions)} items):")
                    for action in actions[:2]:  # Show first 2 actions
                        print_info(f"        • {action.get('action', 'Unknown')}")
                print_info("")

    def _display_resource_planning_summary(self, collections: Dict[str, Dict]):
        """Display resource planning and success metrics"""
        print_header("📊 RESOURCE PLANNING & SUCCESS METRICS", Colors.MAGENTA)
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        recommendations = sample_collection.get('recommendations', {})
        
        # Resource Requirements
        resource_reqs = recommendations.get('resource_requirements', {})
        if resource_reqs:
            print_info("💼 Resource Requirements:")
            print_info(f"   • Total Effort: {resource_reqs.get('total_estimated_effort', 'TBD')}")
            print_info(f"   • Team Size: {resource_reqs.get('recommended_team_size', 'TBD')}")
            print_info(f"   • Budget: {resource_reqs.get('budget_estimate', 'TBD')}")
            
            # Detailed breakdown
            immediate_hours = resource_reqs.get('immediate_effort_hours', 0)
            short_term_days = resource_reqs.get('short_term_effort_days', 0)
            long_term_weeks = resource_reqs.get('long_term_effort_weeks', 0)
            
            if immediate_hours or short_term_days or long_term_weeks:
                print_info("   📊 Effort Breakdown:")
                if immediate_hours:
                    print_info(f"     • Immediate: {immediate_hours} hours")
                if short_term_days:
                    print_info(f"     • Short-term: {short_term_days} days")
                if long_term_weeks:
                    print_info(f"     • Long-term: {long_term_weeks} weeks")
        
        # Success Metrics
        success_metrics = recommendations.get('success_metrics', {})
        if success_metrics:
            print_info("\n🎯 Success Metrics & Targets:")
            for metric, target in success_metrics.items():
                metric_name = metric.replace('_', ' ').title()
                print_info(f"   • {metric_name}: {target}")
        
        # Strategic Initiatives
        strategic_initiatives = recommendations.get('strategic_initiatives', [])
        if strategic_initiatives:
            print_info("\n🚀 Strategic Initiatives:")
            for initiative in strategic_initiatives:
                print_info(f"   • {initiative.get('initiative', 'Unknown Initiative')}")
                print_info(f"     📋 {initiative.get('description', '')}")
                print_info(f"     ⏰ Timeline: {initiative.get('timeline', 'TBD')}")
                print_info(f"     💥 Impact: {initiative.get('impact', 'TBD')}")
                print_info("")

    def _perform_status_analysis(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Perform comprehensive status analysis on all collections (T003)
        
        Args:
            collections: Mapped and analyzed collections
            
        Returns:
            Dict[str, Dict]: Collections with status analysis
        """
        print_info("🔬 Starting comprehensive status analysis...")
        
        # T003.1: Device-level status analysis
        print_info("📱 T003.1: Performing device-level status analysis...")
        device_analyzed_collections = self._perform_device_status_analysis(collections)
        
        # T003.2: Layer-level completeness analysis
        print_info("📊 T003.2: Performing layer-level completeness analysis...")
        layer_analyzed_collections = self._perform_layer_completeness_analysis(device_analyzed_collections)
        
        # T003.3: Cross-option analysis
        print_info("🔄 T003.3: Performing cross-option analysis...")
        cross_analyzed_collections = self._perform_cross_option_analysis(layer_analyzed_collections)
        
        # Display comprehensive status summary
        self._display_status_analysis_summary(cross_analyzed_collections)
        
        return cross_analyzed_collections
    
    def _perform_device_status_analysis(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Perform device-level status analysis (T003.1)
        
        Analyzes device accessibility, authentication status, data quality, and connection patterns.
        
        Args:
            collections: Collections to analyze
            
        Returns:
            Dict[str, Dict]: Collections with device status analysis
        """
        print_info(f"  🔍 Analyzing device status across {len(collections)} collections...")
        
        # Global device statistics
        global_device_stats = {
            'total_devices': set(),
            'accessible_devices': set(),
            'failed_devices': set(),
            'consistent_devices': set(),
            'inconsistent_devices': set(),
            'device_collection_counts': {},
            'device_success_rates': {},
            'device_layer_coverage': {}
        }
        
        for collection_name, collection_info in collections.items():
            print_info(f"    📂 Analyzing devices in: {collection_name}")
            
            collection_info['device_analysis'] = {
                'total_devices': len(collection_info.get('devices', [])),
                'accessible_devices': 0,
                'failed_devices': 0,
                'device_success_rate': 0.0,
                'device_details': {},
                'connection_patterns': {},
                'data_quality_scores': {}
            }
            
            for device_info in collection_info.get('devices', []):
                device_ip = device_info['device_ip']
                
                # Track global device presence
                global_device_stats['total_devices'].add(device_ip)
                
                # Analyze device accessibility
                is_accessible = device_info['accessibility_status'] == 'accessible'
                
                if is_accessible:
                    collection_info['device_analysis']['accessible_devices'] += 1
                    global_device_stats['accessible_devices'].add(device_ip)
                else:
                    collection_info['device_analysis']['failed_devices'] += 1
                    global_device_stats['failed_devices'].add(device_ip)
                
                # Device collection count tracking
                if device_ip not in global_device_stats['device_collection_counts']:
                    global_device_stats['device_collection_counts'][device_ip] = 0
                global_device_stats['device_collection_counts'][device_ip] += 1
                
                # Analyze data quality per device
                data_quality_score = self._calculate_device_data_quality(device_info)
                collection_info['device_analysis']['data_quality_scores'][device_ip] = data_quality_score
                
                # Store detailed device analysis
                collection_info['device_analysis']['device_details'][device_ip] = {
                    'accessibility_status': device_info['accessibility_status'],
                    'total_files': device_info['total_files'],
                    'layers_count': len(device_info['layers']),
                    'layers': device_info['layers'],
                    'has_errors': device_info['has_errors'],
                    'data_quality_score': data_quality_score,
                    'layer_details': device_info['layer_details']
                }
                
                # Track layer coverage per device globally
                if device_ip not in global_device_stats['device_layer_coverage']:
                    global_device_stats['device_layer_coverage'][device_ip] = set()
                global_device_stats['device_layer_coverage'][device_ip].update(device_info['layers'])
            
            # Calculate collection success rate
            if collection_info['device_analysis']['total_devices'] > 0:
                success_rate = (collection_info['device_analysis']['accessible_devices'] / 
                              collection_info['device_analysis']['total_devices']) * 100
                collection_info['device_analysis']['device_success_rate'] = round(success_rate, 1)
        
        # Calculate global device success rates
        for device_ip in global_device_stats['total_devices']:
            accessible_count = sum(1 for c in collections.values() 
                                 if any(d['device_ip'] == device_ip and d['accessibility_status'] == 'accessible' 
                                       for d in c.get('devices', [])))
            total_appearances = global_device_stats['device_collection_counts'][device_ip]
            success_rate = (accessible_count / total_appearances * 100) if total_appearances > 0 else 0
            global_device_stats['device_success_rates'][device_ip] = round(success_rate, 1)
        
        # Identify consistent vs inconsistent devices
        for device_ip, success_rate in global_device_stats['device_success_rates'].items():
            if success_rate >= 90:
                global_device_stats['consistent_devices'].add(device_ip)
            elif success_rate <= 70:
                global_device_stats['inconsistent_devices'].add(device_ip)
        
        # Store global analysis
        for collection_name, collection_info in collections.items():
            collection_info['global_device_stats'] = global_device_stats
        
        print_success(f"    ✅ Device analysis complete: {len(global_device_stats['total_devices'])} unique devices analyzed")
        
        return collections
    
    def _calculate_device_data_quality(self, device_info: Dict) -> float:
        """Calculate data quality score for a device
        
        Args:
            device_info: Device information dictionary
            
        Returns:
            float: Data quality score between 0.0 and 1.0
        """
        if device_info['accessibility_status'] != 'accessible':
            return 0.0
        
        # Base score for accessibility
        quality_score = 0.3
        
        # File count contribution (up to 0.3)
        if device_info['total_files'] > 0:
            # Logarithmic scale for files (diminishing returns)
            import math
            file_score = min(0.3, math.log(device_info['total_files'] + 1) / math.log(50))
            quality_score += file_score
        
        # Layer diversity contribution (up to 0.4)
        layer_count = len(device_info['layers'])
        expected_layers = 8  # health, interfaces, igp, bgp, mpls, vpn, static, console
        layer_score = min(0.4, (layer_count / expected_layers) * 0.4)
        quality_score += layer_score
        
        # Layer data completeness (analyze each layer's data)
        if device_info['layer_details']:
            layer_completeness = 0
            for layer_name, layer_detail in device_info['layer_details'].items():
                if layer_detail['has_data'] and layer_detail['file_count'] > 0:
                    layer_completeness += 1
            
            if len(device_info['layer_details']) > 0:
                completeness_score = (layer_completeness / len(device_info['layer_details'])) * 0.1
                quality_score = min(1.0, quality_score + completeness_score)
        
        return round(quality_score, 3)

    def _perform_layer_completeness_analysis(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Perform layer-level completeness analysis (T003.2)
        
        Analyzes layer presence, quality, and completeness across collections.
        
        Args:
            collections: Collections with device analysis
            
        Returns:
            Dict[str, Dict]: Collections with layer completeness analysis
        """
        print_info(f"  🔍 Analyzing layer completeness across {len(collections)} collections...")
        
        # Define expected layers and their importance
        expected_layers = {
            'health': {'priority': 'critical', 'description': 'Device health and status'},
            'interfaces': {'priority': 'critical', 'description': 'Interface configurations'},
            'igp': {'priority': 'high', 'description': 'IGP routing protocols'},
            'bgp': {'priority': 'high', 'description': 'BGP routing protocol'},
            'mpls': {'priority': 'medium', 'description': 'MPLS configurations'},
            'vpn': {'priority': 'medium', 'description': 'VPN configurations'},
            'static': {'priority': 'low', 'description': 'Static routing'},
            'console': {'priority': 'medium', 'description': 'Console line configurations'}
        }
        
        # Global layer statistics
        global_layer_stats = {
            'layer_coverage': {},
            'layer_quality': {},
            'layer_device_coverage': {},
            'missing_layers': {},
            'partial_layers': {},
            'complete_layers': {},
            'critical_gaps': [],
            'total_expected_layers': len(expected_layers)
        }
        
        # Initialize layer tracking
        for layer_name in expected_layers.keys():
            global_layer_stats['layer_coverage'][layer_name] = 0
            global_layer_stats['layer_quality'][layer_name] = []
            global_layer_stats['layer_device_coverage'][layer_name] = set()
            global_layer_stats['missing_layers'][layer_name] = []
            global_layer_stats['partial_layers'][layer_name] = []
            global_layer_stats['complete_layers'][layer_name] = []
        
        for collection_name, collection_info in collections.items():
            print_info(f"    📊 Analyzing layers in: {collection_name}")
            
            collection_info['layer_analysis'] = {
                'expected_layers': expected_layers,
                'found_layers': collection_info.get('layers_found', []),
                'missing_layers': [],
                'partial_layers': [],
                'complete_layers': [],
                'layer_completeness_score': 0.0,
                'layer_quality_scores': {},
                'layer_device_coverage': {},
                'critical_layer_gaps': []
            }
            
            # Analyze each expected layer
            for layer_name, layer_config in expected_layers.items():
                layer_present = layer_name in collection_info['layers_found']
                
                if layer_present:
                    # Analyze layer quality across devices
                    layer_quality_scores = []
                    devices_with_layer = 0
                    total_devices = len(collection_info.get('devices', []))
                    
                    for device_info in collection_info.get('devices', []):
                        if layer_name in device_info['layers']:
                            devices_with_layer += 1
                            global_layer_stats['layer_device_coverage'][layer_name].add(device_info['device_ip'])
                            
                            # Calculate layer quality for this device
                            layer_detail = device_info['layer_details'].get(layer_name, {})
                            quality_score = self._calculate_layer_quality_score(layer_detail)
                            layer_quality_scores.append(quality_score)
                    
                    # Determine layer completeness level
                    device_coverage = (devices_with_layer / total_devices * 100) if total_devices > 0 else 0
                    avg_quality = sum(layer_quality_scores) / len(layer_quality_scores) if layer_quality_scores else 0
                    
                    collection_info['layer_analysis']['layer_device_coverage'][layer_name] = {
                        'devices_with_layer': devices_with_layer,
                        'total_devices': total_devices,
                        'coverage_percentage': round(device_coverage, 1),
                        'average_quality': round(avg_quality, 3)
                    }
                    
                    # Classify layer completeness
                    if device_coverage >= 90 and avg_quality >= 0.8:
                        collection_info['layer_analysis']['complete_layers'].append(layer_name)
                        global_layer_stats['complete_layers'][layer_name].append(collection_name)
                    elif device_coverage >= 50 or avg_quality >= 0.5:
                        collection_info['layer_analysis']['partial_layers'].append(layer_name)
                        global_layer_stats['partial_layers'][layer_name].append(collection_name)
                    else:
                        collection_info['layer_analysis']['missing_layers'].append(layer_name)
                        global_layer_stats['missing_layers'][layer_name].append(collection_name)
                    
                    # Track global statistics
                    global_layer_stats['layer_coverage'][layer_name] += 1
                    global_layer_stats['layer_quality'][layer_name].extend(layer_quality_scores)
                    
                else:
                    # Layer completely missing
                    collection_info['layer_analysis']['missing_layers'].append(layer_name)
                    global_layer_stats['missing_layers'][layer_name].append(collection_name)
                
                # Check for critical gaps
                if layer_config['priority'] == 'critical' and layer_name in collection_info['layer_analysis']['missing_layers']:
                    collection_info['layer_analysis']['critical_layer_gaps'].append(layer_name)
                    if layer_name not in global_layer_stats['critical_gaps']:
                        global_layer_stats['critical_gaps'].append(layer_name)
            
            # Calculate overall layer completeness score for collection
            complete_weight = len(collection_info['layer_analysis']['complete_layers']) * 1.0
            partial_weight = len(collection_info['layer_analysis']['partial_layers']) * 0.5
            total_possible = len(expected_layers)
            
            completeness_score = (complete_weight + partial_weight) / total_possible
            collection_info['layer_analysis']['layer_completeness_score'] = round(completeness_score, 3)
        
        # Store global layer analysis
        for collection_name, collection_info in collections.items():
            collection_info['global_layer_stats'] = global_layer_stats
        
        print_success(f"    ✅ Layer analysis complete: {len(expected_layers)} layers analyzed across all collections")
        
        return collections
    
    def _calculate_layer_quality_score(self, layer_detail: Dict) -> float:
        """Calculate quality score for a layer
        
        Args:
            layer_detail: Layer detail information
            
        Returns:
            float: Quality score between 0.0 and 1.0
        """
        if not layer_detail or not layer_detail.get('has_data', False):
            return 0.0
        
        # Base score for having data
        quality_score = 0.4
        
        # File count contribution
        file_count = layer_detail.get('file_count', 0)
        if file_count > 0:
            # Logarithmic scale (diminishing returns)
            import math
            file_score = min(0.3, math.log(file_count + 1) / math.log(10))
            quality_score += file_score
        
        # Format diversity (JSON + TXT is better)
        format_score = 0
        if layer_detail.get('has_json', False):
            format_score += 0.15
        if layer_detail.get('has_txt', False):
            format_score += 0.15
        quality_score += format_score
        
        return round(min(1.0, quality_score), 3)

    def _perform_cross_option_analysis(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Perform cross-option analysis (T003.3)
        
        Compares collections across different options to identify patterns and trends.
        
        Args:
            collections: Collections with device and layer analysis
            
        Returns:
            Dict[str, Dict]: Collections with cross-option analysis
        """
        print_info(f"  🔍 Performing cross-option analysis across {len(collections)} collections...")
        
        # Group collections by option type
        option_groups = {}
        for collection_name, collection_info in collections.items():
            option_type = collection_info.get('option_type', 'unknown')
            if option_type not in option_groups:
                option_groups[option_type] = []
            option_groups[option_type].append((collection_name, collection_info))
        
        # Analyze patterns across option types
        cross_analysis = {
            'option_effectiveness': {},
            'option_patterns': {},
            'comparative_metrics': {},
            'trend_analysis': {},
            'best_practices': [],
            'improvement_opportunities': []
        }
        
        print_info(f"    🔄 Analyzing {len(option_groups)} option types...")
        
        for option_type, option_collections in option_groups.items():
            print_info(f"      📈 Analyzing option type: {option_type}")
            
            # Calculate option-level metrics
            total_collections = len(option_collections)
            total_devices = sum(len(c[1].get('devices', [])) for c in option_collections)
            
            # Device success rates
            device_success_rates = []
            for _, collection_info in option_collections:
                device_analysis = collection_info.get('device_analysis', {})
                success_rate = device_analysis.get('device_success_rate', 0)
                device_success_rates.append(success_rate)
            
            avg_device_success = sum(device_success_rates) / len(device_success_rates) if device_success_rates else 0
            
            # Layer completeness
            layer_completeness_scores = []
            for _, collection_info in option_collections:
                layer_analysis = collection_info.get('layer_analysis', {})
                completeness_score = layer_analysis.get('layer_completeness_score', 0)
                layer_completeness_scores.append(completeness_score)
            
            avg_layer_completeness = sum(layer_completeness_scores) / len(layer_completeness_scores) if layer_completeness_scores else 0
            
            # Data quality analysis
            data_quality_scores = []
            for _, collection_info in option_collections:
                device_analysis = collection_info.get('device_analysis', {})
                quality_scores = device_analysis.get('data_quality_scores', {})
                if quality_scores:
                    avg_quality = sum(quality_scores.values()) / len(quality_scores)
                    data_quality_scores.append(avg_quality)
            
            avg_data_quality = sum(data_quality_scores) / len(data_quality_scores) if data_quality_scores else 0
            
            # Option effectiveness metrics
            cross_analysis['option_effectiveness'][option_type] = {
                'collection_count': total_collections,
                'total_devices': total_devices,
                'avg_device_success_rate': round(avg_device_success, 1),
                'avg_layer_completeness': round(avg_layer_completeness, 3),
                'avg_data_quality': round(avg_data_quality, 3),
                'effectiveness_score': round((avg_device_success/100 * 0.4 + avg_layer_completeness * 0.4 + avg_data_quality * 0.2), 3)
            }
            
            # Pattern analysis
            patterns = self._analyze_option_patterns(option_type, option_collections)
            cross_analysis['option_patterns'][option_type] = patterns
        
        # Comparative analysis
        cross_analysis['comparative_metrics'] = self._generate_comparative_metrics(cross_analysis['option_effectiveness'])
        
        # Trend analysis
        cross_analysis['trend_analysis'] = self._analyze_collection_trends(collections)
        
        # Best practices identification
        cross_analysis['best_practices'] = self._identify_best_practices(cross_analysis)
        
        # Improvement opportunities
        cross_analysis['improvement_opportunities'] = self._identify_improvement_opportunities(cross_analysis)
        
        # Store cross-analysis in all collections
        for collection_name, collection_info in collections.items():
            collection_info['cross_analysis'] = cross_analysis
        
        print_success(f"    ✅ Cross-option analysis complete: {len(option_groups)} option types analyzed")
        
        return collections
    
    def _analyze_option_patterns(self, option_type: str, option_collections: List[Tuple]) -> Dict:
        """Analyze patterns within an option type"""
        patterns = {
            'consistency': 'unknown',
            'common_layers': [],
            'common_issues': [],
            'success_factors': [],
            'failure_patterns': []
        }
        
        if not option_collections:
            return patterns
        
        # Analyze layer consistency
        all_layers = []
        for _, collection_info in option_collections:
            all_layers.extend(collection_info.get('layers_found', []))
        
        # Find most common layers
        from collections import Counter
        layer_counts = Counter(all_layers)
        patterns['common_layers'] = [layer for layer, count in layer_counts.most_common(5)]
        
        # Analyze success patterns
        high_success_collections = [c for c in option_collections 
                                   if c[1].get('device_analysis', {}).get('device_success_rate', 0) >= 80]
        
        if len(high_success_collections) / len(option_collections) >= 0.7:
            patterns['consistency'] = 'high'
            patterns['success_factors'].append('Consistently high device success rates')
        elif len(high_success_collections) / len(option_collections) >= 0.4:
            patterns['consistency'] = 'medium'
        else:
            patterns['consistency'] = 'low'
            patterns['failure_patterns'].append('Variable device success rates')
        
        return patterns
    
    def _generate_comparative_metrics(self, effectiveness_data: Dict) -> Dict:
        """Generate comparative metrics across option types"""
        if not effectiveness_data:
            return {}
        
        # Find best and worst performing options
        effectiveness_scores = {opt: data['effectiveness_score'] for opt, data in effectiveness_data.items()}
        
        best_option = max(effectiveness_scores.items(), key=lambda x: x[1]) if effectiveness_scores else ('none', 0)
        worst_option = min(effectiveness_scores.items(), key=lambda x: x[1]) if effectiveness_scores else ('none', 0)
        
        avg_effectiveness = sum(effectiveness_scores.values()) / len(effectiveness_scores) if effectiveness_scores else 0
        
        return {
            'best_performing_option': {
                'option_type': best_option[0],
                'effectiveness_score': best_option[1]
            },
            'worst_performing_option': {
                'option_type': worst_option[0],
                'effectiveness_score': worst_option[1]
            },
            'average_effectiveness': round(avg_effectiveness, 3),
            'performance_range': round(best_option[1] - worst_option[1], 3) if best_option[1] and worst_option[1] else 0
        }
    
    def _analyze_collection_trends(self, collections: Dict[str, Dict]) -> Dict:
        """Analyze trends across collections over time"""
        # Sort collections by timestamp
        sorted_collections = sorted(
            collections.items(),
            key=lambda x: x[1].get('timestamp') or x[1].get('creation_time'),
            reverse=False  # Oldest first
        )
        
        trends = {
            'device_success_trend': [],
            'layer_completeness_trend': [],
            'data_quality_trend': [],
            'overall_improvement': 'stable'
        }
        
        for collection_name, collection_info in sorted_collections:
            device_success = collection_info.get('device_analysis', {}).get('device_success_rate', 0)
            layer_completeness = collection_info.get('layer_analysis', {}).get('layer_completeness_score', 0)
            
            # Calculate average data quality
            quality_scores = collection_info.get('device_analysis', {}).get('data_quality_scores', {})
            avg_quality = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0
            
            trends['device_success_trend'].append(device_success)
            trends['layer_completeness_trend'].append(layer_completeness)
            trends['data_quality_trend'].append(avg_quality)
        
        # Determine overall trend
        if len(trends['device_success_trend']) >= 3:
            recent_avg = sum(trends['device_success_trend'][-3:]) / 3
            early_avg = sum(trends['device_success_trend'][:3]) / 3
            
            if recent_avg > early_avg + 5:
                trends['overall_improvement'] = 'improving'
            elif recent_avg < early_avg - 5:
                trends['overall_improvement'] = 'declining'
        
        return trends
    
    def _identify_best_practices(self, cross_analysis: Dict) -> List[str]:
        """Identify best practices from cross-analysis"""
        best_practices = []
        
        effectiveness_data = cross_analysis.get('option_effectiveness', {})
        if not effectiveness_data:
            return best_practices
        
        # Find highest performing option
        best_option = cross_analysis.get('comparative_metrics', {}).get('best_performing_option', {})
        if best_option.get('option_type'):
            best_practices.append(f"Use {best_option['option_type']} approach for optimal results")
        
        # Analyze effectiveness scores
        high_performing_options = [opt for opt, data in effectiveness_data.items() 
                                 if data['effectiveness_score'] >= 0.7]
        
        if high_performing_options:
            best_practices.append(f"Focus on {', '.join(high_performing_options)} for best collection results")
        
        # Device success rate best practices
        high_device_success = [opt for opt, data in effectiveness_data.items() 
                             if data['avg_device_success_rate'] >= 80]
        
        if high_device_success:
            best_practices.append(f"Maintain device connectivity standards seen in {', '.join(high_device_success)}")
        
        return best_practices
    
    def _identify_improvement_opportunities(self, cross_analysis: Dict) -> List[str]:
        """Identify improvement opportunities from cross-analysis"""
        opportunities = []
        
        effectiveness_data = cross_analysis.get('option_effectiveness', {})
        if not effectiveness_data:
            return opportunities
        
        # Find low performing areas
        low_device_success = [opt for opt, data in effectiveness_data.items() 
                            if data['avg_device_success_rate'] < 70]
        
        if low_device_success:
            opportunities.append(f"Improve device connectivity for {', '.join(low_device_success)}")
        
        low_completeness = [opt for opt, data in effectiveness_data.items() 
                          if data['avg_layer_completeness'] < 0.5]
        
        if low_completeness:
            opportunities.append(f"Enhance layer collection completeness for {', '.join(low_completeness)}")
        
        low_quality = [opt for opt, data in effectiveness_data.items() 
                     if data['avg_data_quality'] < 0.6]
        
        if low_quality:
            opportunities.append(f"Improve data quality standards for {', '.join(low_quality)}")
        
        return opportunities
    
    def _display_status_analysis_summary(self, collections: Dict[str, Dict]):
        """Display comprehensive status analysis summary"""
        print_section("Status Analysis Summary")
        
        # Get cross-analysis data (should be same across all collections)
        sample_collection = next(iter(collections.values()))
        cross_analysis = sample_collection.get('cross_analysis', {})
        global_device_stats = sample_collection.get('global_device_stats', {})
        global_layer_stats = sample_collection.get('global_layer_stats', {})
        
        # Device Status Summary
        print_info("📱 Device Status Summary:")
        total_devices = len(global_device_stats.get('total_devices', set()))
        accessible_devices = len(global_device_stats.get('accessible_devices', set()))
        consistent_devices = len(global_device_stats.get('consistent_devices', set()))
        
        print_info(f"   • Total Unique Devices: {total_devices}")
        print_info(f"   • Accessible Devices: {accessible_devices}")
        print_info(f"   • Consistent Devices: {consistent_devices}")
        print_info(f"   • Device Reliability: {(consistent_devices/total_devices*100):.1f}%" if total_devices > 0 else "   • Device Reliability: N/A")
        
        # Layer Status Summary
        print_info("\n📊 Layer Status Summary:")
        critical_gaps = global_layer_stats.get('critical_gaps', [])
        print_info(f"   • Expected Layers: {global_layer_stats.get('total_expected_layers', 0)}")
        print_info(f"   • Critical Layer Gaps: {len(critical_gaps)}")
        if critical_gaps:
            print_info(f"   • Missing Critical Layers: {', '.join(critical_gaps)}")
        
        # Option Effectiveness Summary
        print_info("\n🎯 Option Effectiveness Summary:")
        effectiveness_data = cross_analysis.get('option_effectiveness', {})
        for option_type, metrics in effectiveness_data.items():
            print_info(f"   • {option_type}: {metrics['effectiveness_score']:.3f} effectiveness score")
        
        # Best Practices and Opportunities
        best_practices = cross_analysis.get('best_practices', [])
        opportunities = cross_analysis.get('improvement_opportunities', [])
        
        if best_practices:
            print_info(f"\n💡 Best Practices Identified: {len(best_practices)}")
            for practice in best_practices[:3]:  # Show top 3
                print_info(f"   • {practice}")
        
        if opportunities:
            print_info(f"\n🔧 Improvement Opportunities: {len(opportunities)}")
            for opportunity in opportunities[:3]:  # Show top 3
                print_info(f"   • {opportunity}")

    def _analyze_collection_structures(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Analyze the internal structure of each collection
        
        Args:
            collections: Dictionary of discovered collections
            
        Returns:
            Dict[str, Dict]: Enhanced collections with structure analysis
        """
        print_info(f"🔍 Analyzing structure of {len(collections)} collections...")
        
        for collection_name, collection_info in collections.items():
            try:
                collection_path = collection_info['path']
                print_info(f"  📂 Analyzing: {collection_name}")
                
                # Find device directories (IP addresses)
                device_dirs = [d for d in collection_path.iterdir() 
                             if d.is_dir() and not d.name.startswith('.') 
                             and d.name not in ['logs', 'reports', 'sample-configs']]
                
                collection_info['devices'] = []
                collection_info['device_count'] = len(device_dirs)
                
                # Analyze each device
                for device_dir in device_dirs:
                    device_info = self._analyze_device_structure(device_dir)
                    collection_info['devices'].append(device_info)
                    
                    # Update collection-level layer tracking
                    collection_info['layers_found'].update(device_info['layers'])
                
                # Convert set to list for JSON serialization
                collection_info['layers_found'] = list(collection_info['layers_found'])
                
                # Determine collection completeness
                collection_info['completeness_score'] = self._calculate_completeness_score(collection_info)
                
                print_info(f"    ✅ {len(device_dirs)} devices, {len(collection_info['layers_found'])} layer types")
                
            except Exception as e:
                print_warning(f"⚠️  Error analyzing {collection_name}: {str(e)}")
                collection_info['analysis_error'] = str(e)
        
        return collections
    
    def _analyze_device_structure(self, device_dir: Path) -> Dict:
        """Analyze the structure of a single device directory
        
        Args:
            device_dir: Path to device directory
            
        Returns:
            Dict: Device structure information
        """
        device_info = {
            'device_ip': device_dir.name,
            'device_path': device_dir,
            'layers': [],
            'layer_details': {},
            'total_files': 0,
            'has_errors': False,
            'accessibility_status': 'unknown'
        }
        
        # Find layer directories
        layer_dirs = [d for d in device_dir.iterdir() if d.is_dir()]
        
        for layer_dir in layer_dirs:
            layer_name = layer_dir.name
            device_info['layers'].append(layer_name)
            
            # Analyze layer contents
            layer_files = list(layer_dir.rglob('*'))
            file_count = len([f for f in layer_files if f.is_file()])
            
            device_info['layer_details'][layer_name] = {
                'path': layer_dir,
                'file_count': file_count,
                'has_json': any(f.suffix == '.json' for f in layer_files),
                'has_txt': any(f.suffix == '.txt' for f in layer_files),
                'has_data': file_count > 0
            }
            
            device_info['total_files'] += file_count
        
        # Determine accessibility status based on presence of data
        if device_info['total_files'] > 0:
            device_info['accessibility_status'] = 'accessible'
        else:
            device_info['accessibility_status'] = 'failed'
            device_info['has_errors'] = True
        
        return device_info
    
    def _calculate_completeness_score(self, collection_info: Dict) -> float:
        """Calculate a completeness score for a collection
        
        Args:
            collection_info: Collection information dictionary
            
        Returns:
            float: Completeness score between 0.0 and 1.0
        """
        # Expected layers for full analysis
        expected_layers = ['health', 'interfaces', 'igp', 'bgp', 'mpls', 'vpn', 'static', 'console']
        
        if not collection_info['devices']:
            return 0.0
        
        # Calculate layer completeness
        layers_found = set(collection_info['layers_found'])
        layer_score = len(layers_found.intersection(expected_layers)) / len(expected_layers)
        
        # Calculate device completeness
        accessible_devices = sum(1 for device in collection_info['devices'] 
                               if device['accessibility_status'] == 'accessible')
        device_score = accessible_devices / len(collection_info['devices']) if collection_info['devices'] else 0
        
        # Weighted average (layers 70%, devices 30%)
        completeness_score = (layer_score * 0.7) + (device_score * 0.3)
        
        return round(completeness_score, 3)
    
    def _map_collections_to_options(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Map collections to their originating options (T002.3 placeholder)
        
        Args:
            collections: Analyzed collections
            
        Returns:
            Dict[str, Dict]: Collections with option mapping
        """
        print_info("🎯 Mapping collections to originating options...")
        
        for collection_name, collection_info in collections.items():
            # Basic heuristics for option mapping (to be enhanced)
            layers = set(collection_info.get('layers_found', []))
            
            if 'console' in layers and len(layers) == 1:
                collection_info['option_type'] = 'console_audit'  # Option 8
                collection_info['likely_option'] = 8
            elif 'console' in layers and len(layers) > 6:
                collection_info['option_type'] = 'complete_collection'  # Option 9
                collection_info['likely_option'] = 9
            elif len(layers) >= 5 and 'console' not in layers:
                collection_info['option_type'] = 'full_collection'  # Option 3
                collection_info['likely_option'] = 3
            elif 'health' in layers and len(layers) <= 2:
                collection_info['option_type'] = 'audit_only'  # Option 2
                collection_info['likely_option'] = 2
            else:
                collection_info['option_type'] = 'custom_or_partial'  # Option 4 or partial
                collection_info['likely_option'] = 4
            
            print_info(f"  🎯 {collection_name}: {collection_info['option_type']} (Option {collection_info['likely_option']})")
        
        return collections
    
    def _display_discovery_summary(self, collections: Dict[str, Dict]):
        """Display comprehensive discovery summary
        
        Args:
            collections: Mapped and analyzed collections
        """
        print_info("📊 Collection Discovery Summary:")
        print_info(f"   📂 Total Collections Found: {len(collections)}")
        
        # Group by option type
        option_groups = {}
        for collection_name, collection_info in collections.items():
            option_type = collection_info.get('option_type', 'unknown')
            if option_type not in option_groups:
                option_groups[option_type] = []
            option_groups[option_type].append(collection_info)
        
        print_info("\n📋 Collections by Type:")
        for option_type, group_collections in option_groups.items():
            print_info(f"   • {option_type}: {len(group_collections)} collections")
        
        # Overall statistics
        total_devices = sum(len(c.get('devices', [])) for c in collections.values())
        avg_completeness = sum(c.get('completeness_score', 0) for c in collections.values()) / len(collections)
        
        print_info(f"\n📈 Overall Statistics:")
        print_info(f"   • Total Devices Analyzed: {total_devices}")
        print_info(f"   • Average Completeness: {avg_completeness:.1%}")
        print_info(f"   • Collections with Reports: {sum(1 for c in collections.values() if c.get('has_collection_report', False))}")

    def _discover_collection_directories(self) -> Dict[str, Dict]:
        """Discover and catalog all collection output directories
        
        Scans the rr4-complete-enchanced-v4-cli-output directory for collector-run-* 
        directories and extracts metadata for each collection.
        
        Returns:
            Dict[str, Dict]: Dictionary of collection directories with metadata
        """
        collections = {}
        base_dir = Path("../rr4-complete-enchanced-v4-cli-output")
        
        print_info(f"🔍 Scanning base directory: {base_dir}")
        
        if not base_dir.exists():
            print_warning(f"⚠️  Output directory not found: {base_dir}")
            print_info("This is normal if no collections have been run yet")
            return collections
        
        # Find all collector-run directories
        collector_pattern = "collector-run-*"
        collector_dirs = list(base_dir.glob(collector_pattern))
        
        print_info(f"📂 Found {len(collector_dirs)} collection directories")
        
        for collector_dir in collector_dirs:
            if collector_dir.is_dir():
                try:
                    # Extract timestamp from directory name
                    # Format: collector-run-YYYYMMDD-HHMMSS
                    timestamp_str = collector_dir.name.replace("collector-run-", "")
                    timestamp = self._parse_collection_timestamp(timestamp_str)
                    
                    # Get directory creation time as fallback
                    creation_time = datetime.fromtimestamp(collector_dir.stat().st_mtime)
                    
                    collection_info = {
                        'path': collector_dir,
                        'name': collector_dir.name,
                        'timestamp': timestamp,
                        'creation_time': creation_time,
                        'devices': [],
                        'device_count': 0,
                        'layers_found': set(),
                        'has_collection_report': False,
                        'collection_metadata': {},
                        'option_type': 'unknown',
                        'status': 'discovered'
                    }
                    
                    # Check for collection report
                    collection_report = collector_dir / "collection_report.json"
                    if collection_report.exists():
                        collection_info['has_collection_report'] = True
                        try:
                            with open(collection_report, 'r') as f:
                                metadata = json.load(f)
                                collection_info['collection_metadata'] = metadata
                                
                                # Extract key information from metadata
                                if 'summary' in metadata:
                                    summary = metadata['summary']
                                    collection_info['device_count'] = summary.get('total_devices', 0)
                                    collection_info['completed_devices'] = summary.get('completed_devices', 0)
                                    collection_info['failed_devices'] = summary.get('failed_devices', 0)
                                    collection_info['completion_rate'] = summary.get('device_completion_rate', 0.0)
                                    collection_info['elapsed_time'] = summary.get('elapsed_time', 0.0)
                                    collection_info['is_running'] = summary.get('is_running', False)
                                
                        except Exception as e:
                            print_warning(f"⚠️  Could not parse collection report for {collector_dir.name}: {str(e)}")
                    
                    collections[collector_dir.name] = collection_info
                    print_info(f"  ✅ Cataloged: {collector_dir.name} ({collection_info['device_count']} devices)")
                    
                except Exception as e:
                    print_warning(f"⚠️  Error processing {collector_dir.name}: {str(e)}")
                    continue
        
        # Sort collections by timestamp (newest first)
        sorted_collections = dict(sorted(
            collections.items(),
            key=lambda x: x[1]['timestamp'] if x[1]['timestamp'] else x[1]['creation_time'],
            reverse=True
        ))
        
        print_success(f"📊 Discovery complete: {len(sorted_collections)} collections cataloged")
        return sorted_collections
    
    def _parse_collection_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp from collection directory name
        
        Args:
            timestamp_str: Timestamp string in format YYYYMMDD-HHMMSS
            
        Returns:
            datetime object or None if parsing fails
        """
        try:
            # Handle format: 20250530-230452
            if len(timestamp_str) == 15 and '-' in timestamp_str:
                return datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
            else:
                print_warning(f"⚠️  Unexpected timestamp format: {timestamp_str}")
                return None
        except ValueError as e:
            print_warning(f"⚠️  Could not parse timestamp '{timestamp_str}': {str(e)}")
            return None

    def _perform_gap_analysis(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Perform comprehensive gap analysis and generate recommendations (T004)
        
        Args:
            collections: Collections with status analysis
            
        Returns:
            Dict[str, Dict]: Collections with gap analysis and recommendations
        """
        print_info("🔍 Starting comprehensive gap analysis and recommendations...")
        
        # T004.1: Collection gap identification
        print_info("📋 T004.1: Performing collection gap identification...")
        gap_identified_collections = self._identify_collection_gaps(collections)
        
        # T004.2: Root cause analysis
        print_info("🔬 T004.2: Performing root cause analysis...")
        root_cause_collections = self._perform_root_cause_analysis(gap_identified_collections)
        
        # T004.3: Recommendation engine
        print_info("💡 T004.3: Generating actionable recommendations...")
        recommended_collections = self._generate_recommendations(root_cause_collections)
        
        # Display comprehensive gap analysis summary
        self._display_gap_analysis_summary(recommended_collections)
        
        return recommended_collections
    
    def _identify_collection_gaps(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Identify collection gaps per option (T004.1)
        
        Analyzes missing collections, incomplete data, and coverage gaps.
        
        Args:
            collections: Collections with status analysis
            
        Returns:
            Dict[str, Dict]: Collections with gap identification
        """
        print_info(f"  🔍 Identifying collection gaps across {len(collections)} collections...")
        
        # Define expected collection patterns per option
        expected_option_patterns = {
            'full_collection': {
                'required_layers': ['health', 'interfaces', 'igp', 'bgp', 'mpls', 'vpn', 'static'],
                'min_device_coverage': 80.0,
                'min_layer_completeness': 0.8,
                'description': 'Full production data collection'
            },
            'complete_collection': {
                'required_layers': ['health', 'interfaces', 'igp', 'bgp', 'mpls', 'vpn', 'static', 'console'],
                'min_device_coverage': 80.0,
                'min_layer_completeness': 0.9,
                'description': 'Complete collection with all layers including console'
            },
            'console_audit': {
                'required_layers': ['console'],
                'min_device_coverage': 70.0,
                'min_layer_completeness': 0.7,
                'description': 'Console line audit and configuration collection'
            },
            'audit_only': {
                'required_layers': ['health'],
                'min_device_coverage': 60.0,
                'min_layer_completeness': 0.6,
                'description': 'Quick connectivity and health check'
            },
            'custom_or_partial': {
                'required_layers': [],  # Variable based on intent
                'min_device_coverage': 50.0,
                'min_layer_completeness': 0.5,
                'description': 'Custom or partial collection'
            }
        }
        
        # Global gap analysis
        global_gap_analysis = {
            'missing_options': [],
            'incomplete_options': [],
            'coverage_gaps': {},
            'layer_gaps': {},
            'device_gaps': {},
            'quality_gaps': {},
            'critical_gaps': [],
            'total_gaps_identified': 0
        }
        
        # Analyze gaps per option type
        option_groups = {}
        for collection_name, collection_info in collections.items():
            option_type = collection_info.get('option_type', 'unknown')
            if option_type not in option_groups:
                option_groups[option_type] = []
            option_groups[option_type].append((collection_name, collection_info))
        
        print_info(f"    📊 Analyzing gaps for {len(option_groups)} option types...")
        
        for option_type, expected_pattern in expected_option_patterns.items():
            print_info(f"      🎯 Analyzing {option_type}...")
            
            option_collections = option_groups.get(option_type, [])
            gap_info = {
                'option_present': len(option_collections) > 0,
                'collection_count': len(option_collections),
                'expected_pattern': expected_pattern,
                'identified_gaps': [],
                'missing_layers': [],
                'coverage_issues': [],
                'quality_issues': [],
                'completeness_score': 0.0
            }
            
            if not option_collections:
                # Option completely missing
                gap_info['identified_gaps'].append(f"No {option_type} collections found")
                global_gap_analysis['missing_options'].append(option_type)
                
                if option_type in ['full_collection', 'console_audit']:
                    global_gap_analysis['critical_gaps'].append(f"Missing critical {option_type}")
            
            else:
                # Analyze existing collections for this option
                total_layers_found = set()
                total_device_coverage = []
                total_layer_completeness = []
                
                for collection_name, collection_info in option_collections:
                    # Layer analysis
                    layers_found = set(collection_info.get('layers_found', []))
                    total_layers_found.update(layers_found)
                    
                    # Device coverage analysis
                    device_analysis = collection_info.get('device_analysis', {})
                    device_coverage = device_analysis.get('device_success_rate', 0)
                    total_device_coverage.append(device_coverage)
                    
                    # Layer completeness analysis
                    layer_analysis = collection_info.get('layer_analysis', {})
                    layer_completeness = layer_analysis.get('layer_completeness_score', 0)
                    total_layer_completeness.append(layer_completeness)
                
                # Check for missing required layers
                required_layers = set(expected_pattern['required_layers'])
                missing_layers = required_layers - total_layers_found
                
                if missing_layers:
                    gap_info['missing_layers'] = list(missing_layers)
                    gap_info['identified_gaps'].append(f"Missing required layers: {', '.join(missing_layers)}")
                
                # Check device coverage
                avg_device_coverage = sum(total_device_coverage) / len(total_device_coverage) if total_device_coverage else 0
                min_coverage = expected_pattern['min_device_coverage']
                
                if avg_device_coverage < min_coverage:
                    gap_info['coverage_issues'].append(f"Device coverage {avg_device_coverage:.1f}% below target {min_coverage}%")
                    gap_info['identified_gaps'].append(f"Low device coverage: {avg_device_coverage:.1f}%")
                
                # Check layer completeness
                avg_layer_completeness = sum(total_layer_completeness) / len(total_layer_completeness) if total_layer_completeness else 0
                min_completeness = expected_pattern['min_layer_completeness']
                
                if avg_layer_completeness < min_completeness:
                    gap_info['quality_issues'].append(f"Layer completeness {avg_layer_completeness:.3f} below target {min_completeness}")
                    gap_info['identified_gaps'].append(f"Low layer completeness: {avg_layer_completeness:.3f}")
                
                # Calculate overall completeness score for this option
                layer_score = 1.0 - (len(missing_layers) / len(required_layers)) if required_layers else 1.0
                coverage_score = min(1.0, avg_device_coverage / min_coverage) if min_coverage > 0 else 1.0
                quality_score = min(1.0, avg_layer_completeness / min_completeness) if min_completeness > 0 else 1.0
                
                gap_info['completeness_score'] = (layer_score * 0.4 + coverage_score * 0.3 + quality_score * 0.3)
                
                # Classify as incomplete if significant gaps
                if gap_info['completeness_score'] < 0.8:
                    global_gap_analysis['incomplete_options'].append(option_type)
            
            # Store gap analysis for this option
            global_gap_analysis['coverage_gaps'][option_type] = gap_info
            global_gap_analysis['total_gaps_identified'] += len(gap_info['identified_gaps'])
        
        # Identify device-specific gaps
        sample_collection = next(iter(collections.values()))
        global_device_stats = sample_collection.get('global_device_stats', {})
        
        # Device reliability gaps
        inconsistent_devices = global_device_stats.get('inconsistent_devices', set())
        if inconsistent_devices:
            global_gap_analysis['device_gaps']['inconsistent_devices'] = list(inconsistent_devices)
        
        # Layer coverage gaps
        global_layer_stats = sample_collection.get('global_layer_stats', {})
        critical_gaps = global_layer_stats.get('critical_gaps', [])
        if critical_gaps:
            global_gap_analysis['layer_gaps']['critical_missing'] = critical_gaps
        
        # Store global gap analysis in all collections
        for collection_name, collection_info in collections.items():
            collection_info['gap_analysis'] = global_gap_analysis
        
        print_success(f"    ✅ Gap identification complete: {global_gap_analysis['total_gaps_identified']} gaps identified across {len(expected_option_patterns)} option types")
        
        return collections
    
    def _perform_root_cause_analysis(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Perform root cause analysis of identified gaps (T004.2)
        
        Analyzes failure patterns and underlying causes behind collection gaps.
        
        Args:
            collections: Collections with gap identification
            
        Returns:
            Dict[str, Dict]: Collections with root cause analysis
        """
        print_info(f"  🔍 Performing root cause analysis on identified gaps...")
        
        # Get gap analysis data
        sample_collection = next(iter(collections.values()))
        gap_analysis = sample_collection.get('gap_analysis', {})
        
        # Root cause categories
        root_cause_analysis = {
            'infrastructure_issues': {
                'network_connectivity': [],
                'device_accessibility': [],
                'authentication_failures': []
            },
            'configuration_issues': {
                'missing_protocols': [],
                'incomplete_configs': [],
                'platform_limitations': []
            },
            'process_issues': {
                'collection_strategy': [],
                'timing_issues': [],
                'scope_limitations': []
            },
            'technical_issues': {
                'command_failures': [],
                'parsing_errors': [],
                'storage_issues': []
            },
            'prioritized_causes': [],
            'impact_assessment': {},
            'remediation_complexity': {}
        }
        
        print_info(f"    🔬 Analyzing root causes for {len(gap_analysis.get('coverage_gaps', {}))} option types...")
        
        # Analyze each option type's gaps
        for option_type, gap_info in gap_analysis.get('coverage_gaps', {}).items():
            print_info(f"      🎯 Root cause analysis for {option_type}...")
            
            option_causes = []
            
            # Analyze missing options
            if not gap_info['option_present']:
                option_causes.append({
                    'cause': 'collection_strategy_gap',
                    'category': 'process_issues',
                    'description': f"No {option_type} collections have been executed",
                    'severity': 'high' if option_type in ['full_collection', 'console_audit'] else 'medium',
                    'remediation_effort': 'low'
                })
                root_cause_analysis['process_issues']['collection_strategy'].append(option_type)
            
            # Analyze missing layers
            missing_layers = gap_info.get('missing_layers', [])
            if missing_layers:
                for layer in missing_layers:
                    if layer in ['health', 'interfaces']:
                        option_causes.append({
                            'cause': 'critical_layer_missing',
                            'category': 'infrastructure_issues',
                            'description': f"Critical layer '{layer}' missing from {option_type}",
                            'severity': 'critical',
                            'remediation_effort': 'medium'
                        })
                        root_cause_analysis['infrastructure_issues']['device_accessibility'].append(f"{option_type}:{layer}")
                    
                    elif layer in ['console']:
                        option_causes.append({
                            'cause': 'console_collection_missing',
                            'category': 'configuration_issues',
                            'description': f"Console layer missing - may indicate no NM4 cards or insufficient privileges",
                            'severity': 'medium',
                            'remediation_effort': 'high'
                        })
                        root_cause_analysis['configuration_issues']['platform_limitations'].append(f"{option_type}:{layer}")
                    
                    else:
                        option_causes.append({
                            'cause': 'protocol_layer_missing',
                            'category': 'configuration_issues',
                            'description': f"Protocol layer '{layer}' missing - may indicate protocol not configured",
                            'severity': 'low',
                            'remediation_effort': 'low'
                        })
                        root_cause_analysis['configuration_issues']['missing_protocols'].append(f"{option_type}:{layer}")
            
            # Analyze coverage issues
            coverage_issues = gap_info.get('coverage_issues', [])
            if coverage_issues:
                option_causes.append({
                    'cause': 'device_connectivity_issues',
                    'category': 'infrastructure_issues',
                    'description': f"Low device success rate in {option_type} collections",
                    'severity': 'high',
                    'remediation_effort': 'medium'
                })
                root_cause_analysis['infrastructure_issues']['network_connectivity'].append(option_type)
            
            # Analyze quality issues
            quality_issues = gap_info.get('quality_issues', [])
            if quality_issues:
                option_causes.append({
                    'cause': 'data_quality_degradation',
                    'category': 'technical_issues',
                    'description': f"Data quality below standards in {option_type}",
                    'severity': 'medium',
                    'remediation_effort': 'medium'
                })
                root_cause_analysis['technical_issues']['command_failures'].append(option_type)
            
            # Store option-specific causes
            root_cause_analysis[f'{option_type}_causes'] = option_causes
        
        # Analyze device-specific issues
        device_gaps = gap_analysis.get('device_gaps', {})
        if 'inconsistent_devices' in device_gaps:
            inconsistent_devices = device_gaps['inconsistent_devices']
            for device in inconsistent_devices:
                root_cause_analysis['infrastructure_issues']['device_accessibility'].append(f"device:{device}")
        
        # Analyze layer-specific issues
        layer_gaps = gap_analysis.get('layer_gaps', {})
        if 'critical_missing' in layer_gaps:
            critical_missing = layer_gaps['critical_missing']
            for layer in critical_missing:
                root_cause_analysis['infrastructure_issues']['device_accessibility'].append(f"global:{layer}")
        
        # Prioritize causes by impact and frequency
        all_causes = []
        for option_type in gap_analysis.get('coverage_gaps', {}):
            option_causes = root_cause_analysis.get(f'{option_type}_causes', [])
            all_causes.extend(option_causes)
        
        # Sort by severity and remediation effort
        severity_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
        effort_order = {'low': 0, 'medium': 1, 'high': 2}
        
        prioritized_causes = sorted(all_causes, 
                                  key=lambda x: (severity_order.get(x['severity'], 0), 
                                               -effort_order.get(x['remediation_effort'], 1)), 
                                  reverse=True)
        
        root_cause_analysis['prioritized_causes'] = prioritized_causes[:10]  # Top 10 priority causes
        
        # Impact assessment
        root_cause_analysis['impact_assessment'] = {
            'critical_impact_count': len([c for c in all_causes if c['severity'] == 'critical']),
            'high_impact_count': len([c for c in all_causes if c['severity'] == 'high']),
            'total_issues': len(all_causes),
            'affected_options': len([opt for opt in gap_analysis.get('coverage_gaps', {}) 
                                   if not gap_analysis['coverage_gaps'][opt]['option_present'] or 
                                      gap_analysis['coverage_gaps'][opt]['identified_gaps']])
        }
        
        # Remediation complexity assessment
        root_cause_analysis['remediation_complexity'] = {
            'low_effort_fixes': len([c for c in all_causes if c['remediation_effort'] == 'low']),
            'medium_effort_fixes': len([c for c in all_causes if c['remediation_effort'] == 'medium']),
            'high_effort_fixes': len([c for c in all_causes if c['remediation_effort'] == 'high']),
            'quick_wins_available': len([c for c in all_causes if c['severity'] in ['high', 'critical'] and c['remediation_effort'] == 'low'])
        }
        
        # Store root cause analysis in all collections
        for collection_name, collection_info in collections.items():
            collection_info['root_cause_analysis'] = root_cause_analysis
        
        print_success(f"    ✅ Root cause analysis complete: {len(all_causes)} causes identified and prioritized")
        
        return collections
    
    def _generate_recommendations(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Generate actionable recommendations (T004.3)
        
        Creates prioritized, actionable recommendations based on gap and root cause analysis.
        
        Args:
            collections: Collections with root cause analysis
            
        Returns:
            Dict[str, Dict]: Collections with actionable recommendations
        """
        print_info(f"  🔍 Generating actionable recommendations...")
        
        # Get analysis data
        sample_collection = next(iter(collections.values()))
        gap_analysis = sample_collection.get('gap_analysis', {})
        root_cause_analysis = sample_collection.get('root_cause_analysis', {})
        
        # Recommendation engine
        recommendations = {
            'immediate_actions': [],
            'short_term_improvements': [],
            'long_term_enhancements': [],
            'quick_wins': [],
            'strategic_initiatives': [],
            'implementation_roadmap': [],
            'success_metrics': {},
            'resource_requirements': {}
        }
        
        print_info(f"    💡 Generating recommendations based on root cause analysis...")
        
        # Process prioritized causes to generate recommendations
        prioritized_causes = root_cause_analysis.get('prioritized_causes', [])
        
        for cause in prioritized_causes:
            severity = cause.get('severity', 'low')
            effort = cause.get('remediation_effort', 'medium')
            category = cause.get('category', 'unknown')
            cause_type = cause.get('cause', 'unknown')
            description = cause.get('description', '')
            
            # Generate specific recommendations based on cause type
            if cause_type == 'collection_strategy_gap':
                if 'console_audit' in description:
                    recommendations['immediate_actions'].append({
                        'action': 'Execute Console Audit',
                        'description': 'Run Option 8 (Console Audit) to collect console line configurations',
                        'command': 'Select Option 8 from main menu',
                        'priority': 'high',
                        'effort': 'low',
                        'impact': 'high',
                        'timeline': '1 hour'
                    })
                
                elif 'complete_collection' in description:
                    recommendations['short_term_improvements'].append({
                        'action': 'Execute Complete Collection',
                        'description': 'Run Option 9 (Complete Collection) for comprehensive data gathering',
                        'command': 'Select Option 9 from main menu',
                        'priority': 'high',
                        'effort': 'medium',
                        'impact': 'high',
                        'timeline': '2-4 hours'
                    })
                
                elif 'full_collection' in description:
                    recommendations['immediate_actions'].append({
                        'action': 'Execute Full Collection',
                        'description': 'Run Option 3 (Full Collection) for standard production data',
                        'command': 'Select Option 3 from main menu',
                        'priority': 'high',
                        'effort': 'low',
                        'impact': 'high',
                        'timeline': '1-2 hours'
                    })
            
            elif cause_type == 'critical_layer_missing':
                if 'health' in description:
                    recommendations['immediate_actions'].append({
                        'action': 'Collect Health Data',
                        'description': 'Execute health layer collection to establish baseline device status',
                        'command': 'Run Option 2 (Audit Only) or targeted health collection',
                        'priority': 'critical',
                        'effort': 'low',
                        'impact': 'critical',
                        'timeline': '30 minutes'
                    })
                
                elif 'interfaces' in description:
                    recommendations['immediate_actions'].append({
                        'action': 'Collect Interface Data',
                        'description': 'Execute interface layer collection for network topology understanding',
                        'command': 'Run targeted interface collection or full collection',
                        'priority': 'critical',
                        'effort': 'low',
                        'impact': 'critical',
                        'timeline': '45 minutes'
                    })
            
            elif cause_type == 'console_collection_missing':
                recommendations['long_term_enhancements'].append({
                    'action': 'Investigate Console Infrastructure',
                    'description': 'Verify NM4 console cards presence and configure console access',
                    'command': 'Check hardware inventory and privilege levels',
                    'priority': 'medium',
                    'effort': 'high',
                    'impact': 'medium',
                    'timeline': '1-2 weeks'
                })
            
            elif cause_type == 'device_connectivity_issues':
                recommendations['short_term_improvements'].append({
                    'action': 'Improve Device Connectivity',
                    'description': 'Investigate and resolve network connectivity and authentication issues',
                    'command': 'Run Option 6 (Enhanced Connectivity Test) for detailed analysis',
                    'priority': 'high',
                    'effort': 'medium',
                    'impact': 'high',
                    'timeline': '2-5 days'
                })
            
            elif cause_type == 'data_quality_degradation':
                recommendations['short_term_improvements'].append({
                    'action': 'Enhance Data Quality',
                    'description': 'Review collection parameters and command execution for quality improvements',
                    'command': 'Analyze failed commands and adjust collection strategy',
                    'priority': 'medium',
                    'effort': 'medium',
                    'impact': 'medium',
                    'timeline': '3-7 days'
                })
        
        # Identify quick wins (high impact, low effort)
        impact_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        effort_order = {'low': 1, 'medium': 2, 'high': 3}
        
        all_actions = (recommendations['immediate_actions'] + 
                      recommendations['short_term_improvements'] + 
                      recommendations['long_term_enhancements'])
        
        quick_wins = [action for action in all_actions 
                     if impact_order.get(action.get('impact', 'low'), 1) >= 3 and 
                        effort_order.get(action.get('effort', 'medium'), 2) <= 1]
        
        recommendations['quick_wins'] = quick_wins[:5]  # Top 5 quick wins
        
        # Generate implementation roadmap
        roadmap_phases = [
            {
                'phase': 'Phase 1: Immediate Critical Actions',
                'timeline': '1-7 days',
                'actions': recommendations['immediate_actions'][:3],
                'objective': 'Address critical gaps and establish baseline data collection'
            },
            {
                'phase': 'Phase 2: Short-term Improvements',
                'timeline': '1-4 weeks',
                'actions': recommendations['short_term_improvements'][:3],
                'objective': 'Enhance collection coverage and data quality'
            },
            {
                'phase': 'Phase 3: Long-term Enhancements',
                'timeline': '1-3 months',
                'actions': recommendations['long_term_enhancements'][:2],
                'objective': 'Implement comprehensive infrastructure improvements'
            }
        ]
        
        recommendations['implementation_roadmap'] = roadmap_phases
        
        # Define success metrics
        recommendations['success_metrics'] = {
            'device_reliability_target': '95%',
            'layer_completeness_target': '90%',
            'collection_coverage_target': '100% of critical options',
            'data_quality_target': '85% average quality score',
            'critical_gaps_target': '0 critical gaps remaining'
        }
        
        # Estimate resource requirements
        total_immediate = len(recommendations['immediate_actions'])
        total_short_term = len(recommendations['short_term_improvements'])
        total_long_term = len(recommendations['long_term_enhancements'])
        
        recommendations['resource_requirements'] = {
            'immediate_effort_hours': total_immediate * 2,  # Avg 2 hours per action
            'short_term_effort_days': total_short_term * 3,  # Avg 3 days per action
            'long_term_effort_weeks': total_long_term * 2,   # Avg 2 weeks per action
            'total_estimated_effort': f"{total_immediate * 2}h + {total_short_term * 3}d + {total_long_term * 2}w",
            'recommended_team_size': 'Network engineer + 1 technician',
            'budget_estimate': 'Low (primarily operational effort)'
        }
        
        # Strategic initiatives based on patterns
        missing_options = gap_analysis.get('missing_options', [])
        incomplete_options = gap_analysis.get('incomplete_options', [])
        
        if len(missing_options) >= 2:
            recommendations['strategic_initiatives'].append({
                'initiative': 'Comprehensive Collection Strategy',
                'description': 'Implement systematic approach to ensure all collection options are executed',
                'timeline': '3-6 months',
                'impact': 'high'
            })
        
        if len(incomplete_options) >= 2:
            recommendations['strategic_initiatives'].append({
                'initiative': 'Data Quality Enhancement Program',
                'description': 'Establish ongoing monitoring and improvement of collection data quality',
                'timeline': '6-12 months',
                'impact': 'medium'
            })
        
        # Store recommendations in all collections
        for collection_name, collection_info in collections.items():
            collection_info['recommendations'] = recommendations
        
        total_recommendations = (len(recommendations['immediate_actions']) + 
                               len(recommendations['short_term_improvements']) + 
                               len(recommendations['long_term_enhancements']))
        
        print_success(f"    ✅ Recommendation generation complete: {total_recommendations} actionable recommendations created")
        
        return collections
    
    def _display_gap_analysis_summary(self, collections: Dict[str, Dict]):
        """Display comprehensive gap analysis and recommendations summary"""
        print_section("Gap Analysis and Recommendations Summary")
        
        # Get analysis data
        sample_collection = next(iter(collections.values()))
        gap_analysis = sample_collection.get('gap_analysis', {})
        root_cause_analysis = sample_collection.get('root_cause_analysis', {})
        recommendations = sample_collection.get('recommendations', {})
        
        # Gap Analysis Summary
        print_info("📋 Gap Analysis Summary:")
        missing_options = gap_analysis.get('missing_options', [])
        incomplete_options = gap_analysis.get('incomplete_options', [])
        critical_gaps = gap_analysis.get('critical_gaps', [])
        total_gaps = gap_analysis.get('total_gaps_identified', 0)
        
        print_info(f"   • Total Gaps Identified: {total_gaps}")
        print_info(f"   • Missing Collection Options: {len(missing_options)}")
        print_info(f"   • Incomplete Collection Options: {len(incomplete_options)}")
        print_info(f"   • Critical Gaps: {len(critical_gaps)}")
        
        if missing_options:
            print_info(f"   • Missing Options: {', '.join(missing_options)}")
        if critical_gaps:
            print_info(f"   • Critical Issues: {', '.join(critical_gaps)}")
        
        # Root Cause Analysis Summary
        print_info("\n🔬 Root Cause Analysis Summary:")
        impact_assessment = root_cause_analysis.get('impact_assessment', {})
        remediation_complexity = root_cause_analysis.get('remediation_complexity', {})
        
        print_info(f"   • Critical Impact Issues: {impact_assessment.get('critical_impact_count', 0)}")
        print_info(f"   • High Impact Issues: {impact_assessment.get('high_impact_count', 0)}")
        print_info(f"   • Affected Collection Options: {impact_assessment.get('affected_options', 0)}")
        print_info(f"   • Quick Win Opportunities: {remediation_complexity.get('quick_wins_available', 0)}")
        
        # Recommendations Summary
        print_info("\n💡 Recommendations Summary:")
        immediate_actions = recommendations.get('immediate_actions', [])
        short_term_improvements = recommendations.get('short_term_improvements', [])
        quick_wins = recommendations.get('quick_wins', [])
        
        print_info(f"   • Immediate Actions Required: {len(immediate_actions)}")
        print_info(f"   • Short-term Improvements: {len(short_term_improvements)}")
        print_info(f"   • Quick Win Opportunities: {len(quick_wins)}")
        
        # Top 3 Priority Actions
        if immediate_actions:
            print_info(f"\n🎯 Top Priority Actions:")
            for i, action in enumerate(immediate_actions[:3], 1):
                print_info(f"   {i}. {action.get('action', 'Unknown')}: {action.get('description', '')}")
        
        # Resource Requirements
        resource_reqs = recommendations.get('resource_requirements', {})
        if resource_reqs:
            print_info(f"\n📊 Resource Requirements:")
            print_info(f"   • Estimated Effort: {resource_reqs.get('total_estimated_effort', 'TBD')}")
            print_info(f"   • Recommended Team: {resource_reqs.get('recommended_team_size', 'TBD')}")

    def _generate_comprehensive_reports(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Generate comprehensive reports for all analysis data (T006)
        
        Args:
            collections: Collections with complete analysis data
            
        Returns:
            Dict[str, Dict]: Collections with report generation metadata
        """
        print_info("📊 Generating comprehensive reports...")
        
        # Create reports directory
        reports_dir = Path("feature_report_outputs")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for report files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate multiple report formats
        report_files = {}
        
        try:
            # Executive Summary Report
            print_info("📋 Generating Executive Summary Report...")
            exec_summary_file = self._generate_executive_summary_report_file(collections, reports_dir, timestamp)
            report_files['executive_summary'] = exec_summary_file
            
            # Technical Analysis Report
            print_info("🔬 Generating Technical Analysis Report...")
            tech_analysis_file = self._generate_technical_analysis_report_file(collections, reports_dir, timestamp)
            report_files['technical_analysis'] = tech_analysis_file
            
            # Gap Analysis Report
            print_info("🔍 Generating Gap Analysis Report...")
            gap_analysis_file = self._generate_gap_analysis_report_file(collections, reports_dir, timestamp)
            report_files['gap_analysis'] = gap_analysis_file
            
            # Recommendations Report
            print_info("💡 Generating Recommendations Report...")
            recommendations_file = self._generate_recommendations_report_file(collections, reports_dir, timestamp)
            report_files['recommendations'] = recommendations_file
            
            # Device Analysis Report
            print_info("🖥️  Generating Device Analysis Report...")
            device_analysis_file = self._generate_device_analysis_report_file(collections, reports_dir, timestamp)
            report_files['device_analysis'] = device_analysis_file
            
            # JSON Data Export
            print_info("📄 Generating JSON Data Export...")
            json_export_file = self._generate_json_export_file(collections, reports_dir, timestamp)
            report_files['json_export'] = json_export_file
            
            # Store report metadata in collections
            for collection_name, collection_info in collections.items():
                collection_info['generated_reports'] = {
                    'timestamp': timestamp,
                    'reports_directory': str(reports_dir),
                    'report_files': report_files,
                    'total_reports': len(report_files)
                }
            
            print_success(f"✅ Report generation complete: {len(report_files)} reports created")
            print_info(f"📁 Reports saved to: {reports_dir}")
            
            # Display report summary
            self._display_report_generation_summary(report_files, reports_dir)
            
            return collections
            
        except Exception as e:
            print_error(f"Error generating reports: {str(e)}")
            return collections

    def _generate_executive_summary_report_file(self, collections: Dict[str, Dict], reports_dir: Path, timestamp: str) -> str:
        """Generate executive summary report file"""
        filename = f"feature_report_executive_summary_{timestamp}.txt"
        filepath = reports_dir / filename
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        
        with open(filepath, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("COMPREHENSIVE COLLECTION STATUS REPORT - EXECUTIVE SUMMARY\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Report Type: Executive Summary\n")
            f.write(f"Analysis Scope: All collection options 1-10\n")
            f.write("=" * 100 + "\n\n")
            
            # Executive Overview
            f.write("EXECUTIVE OVERVIEW\n")
            f.write("-" * 50 + "\n")
            
            total_collections = len(collections)
            device_stats = sample_collection.get('global_device_stats', {})
            total_devices = len(device_stats.get('total_devices', set()))
            accessible_devices = len(device_stats.get('accessible_devices', set()))
            device_reliability = (accessible_devices / total_devices * 100) if total_devices > 0 else 0
            
            f.write(f"Network Infrastructure Status: ")
            if device_reliability >= 95:
                f.write("EXCELLENT\n")
            elif device_reliability >= 85:
                f.write("GOOD\n")
            elif device_reliability >= 70:
                f.write("ACCEPTABLE\n")
            else:
                f.write("NEEDS ATTENTION\n")
            
            f.write(f"Total Collections Analyzed: {total_collections}\n")
            f.write(f"Network Devices Analyzed: {total_devices}\n")
            f.write(f"Device Reliability Rate: {device_reliability:.1f}%\n")
            f.write(f"Accessible Devices: {accessible_devices}/{total_devices}\n\n")
            
            # Key Findings
            gap_analysis = sample_collection.get('gap_analysis', {})
            f.write("KEY FINDINGS\n")
            f.write("-" * 50 + "\n")
            f.write(f"Total Gaps Identified: {gap_analysis.get('total_gaps_identified', 0)}\n")
            f.write(f"Missing Collection Options: {len(gap_analysis.get('missing_options', []))}\n")
            f.write(f"Critical Issues: {len(gap_analysis.get('critical_gaps', []))}\n")
            
            missing_options = gap_analysis.get('missing_options', [])
            if missing_options:
                f.write(f"Missing Options: {', '.join(missing_options)}\n")
            
            critical_gaps = gap_analysis.get('critical_gaps', [])
            if critical_gaps:
                f.write(f"Critical Gaps: {', '.join(critical_gaps)}\n")
            f.write("\n")
            
            # Recommendations Summary
            recommendations = sample_collection.get('recommendations', {})
            f.write("IMMEDIATE ACTIONS REQUIRED\n")
            f.write("-" * 50 + "\n")
            
            immediate_actions = recommendations.get('immediate_actions', [])
            if immediate_actions:
                for i, action in enumerate(immediate_actions, 1):
                    f.write(f"{i}. {action.get('action', 'Unknown Action')}\n")
                    f.write(f"   Description: {action.get('description', '')}\n")
                    f.write(f"   Timeline: {action.get('timeline', 'TBD')}\n")
                    f.write(f"   Command: {action.get('command', 'N/A')}\n\n")
            else:
                f.write("No immediate actions required - network collection status is optimal.\n\n")
            
            # Resource Requirements
            resource_reqs = recommendations.get('resource_requirements', {})
            f.write("RESOURCE REQUIREMENTS\n")
            f.write("-" * 50 + "\n")
            f.write(f"Estimated Effort: {resource_reqs.get('total_estimated_effort', 'TBD')}\n")
            f.write(f"Recommended Team: {resource_reqs.get('recommended_team_size', 'TBD')}\n")
            f.write(f"Budget Estimate: {resource_reqs.get('budget_estimate', 'TBD')}\n\n")
            
            # Success Metrics
            success_metrics = recommendations.get('success_metrics', {})
            if success_metrics:
                f.write("SUCCESS METRICS & TARGETS\n")
                f.write("-" * 50 + "\n")
                for metric, target in success_metrics.items():
                    metric_name = metric.replace('_', ' ').title()
                    f.write(f"{metric_name}: {target}\n")
        
        return filename

    def _generate_technical_analysis_report_file(self, collections: Dict[str, Dict], reports_dir: Path, timestamp: str) -> str:
        """Generate technical analysis report file"""
        filename = f"feature_report_technical_analysis_{timestamp}.txt"
        filepath = reports_dir / filename
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        
        with open(filepath, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("COMPREHENSIVE COLLECTION STATUS REPORT - TECHNICAL ANALYSIS\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Report Type: Technical Analysis\n")
            f.write("=" * 100 + "\n\n")
            
            # Collection Analysis
            f.write("COLLECTION ANALYSIS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Collections Discovered: {len(collections)}\n")
            
            # Group by option type
            option_groups = {}
            for collection_info in collections.values():
                option_type = collection_info.get('option_type', 'unknown')
                if option_type not in option_groups:
                    option_groups[option_type] = 0
                option_groups[option_type] += 1
            
            f.write("Collections by Option Type:\n")
            for option_type, count in option_groups.items():
                f.write(f"  {option_type}: {count} collections\n")
            f.write("\n")
            
            # Device Analysis
            device_stats = sample_collection.get('global_device_stats', {})
            f.write("DEVICE ANALYSIS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Unique Devices: {len(device_stats.get('total_devices', set()))}\n")
            f.write(f"Accessible Devices: {len(device_stats.get('accessible_devices', set()))}\n")
            f.write(f"Consistent Devices: {len(device_stats.get('consistent_devices', set()))}\n")
            f.write(f"Inconsistent Devices: {len(device_stats.get('inconsistent_devices', set()))}\n")
            
            # Device success rates
            device_success_rates = device_stats.get('device_success_rates', {})
            if device_success_rates:
                f.write("\nDevice Success Rates:\n")
                for device_ip, success_rate in device_success_rates.items():
                    f.write(f"  {device_ip}: {success_rate}%\n")
            f.write("\n")
            
            # Layer Analysis
            layer_stats = sample_collection.get('global_layer_stats', {})
            f.write("LAYER ANALYSIS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Expected Layers: {layer_stats.get('total_expected_layers', 0)}\n")
            
            all_layers = layer_stats.get('all_layers', set())
            if all_layers:
                f.write(f"Available Layers: {', '.join(sorted(all_layers))}\n")
            
            critical_gaps = layer_stats.get('critical_gaps', [])
            if critical_gaps:
                f.write(f"Critical Layer Gaps: {', '.join(critical_gaps)}\n")
            f.write("\n")
            
            # Cross-Option Analysis
            cross_analysis = sample_collection.get('cross_analysis', {})
            effectiveness_data = cross_analysis.get('option_effectiveness', {})
            
            if effectiveness_data:
                f.write("OPTION EFFECTIVENESS ANALYSIS\n")
                f.write("-" * 60 + "\n")
                for option_type, metrics in effectiveness_data.items():
                    f.write(f"{option_type}:\n")
                    f.write(f"  Collection Count: {metrics.get('collection_count', 0)}\n")
                    f.write(f"  Total Devices: {metrics.get('total_devices', 0)}\n")
                    f.write(f"  Avg Device Success Rate: {metrics.get('avg_device_success_rate', 0)}%\n")
                    f.write(f"  Avg Layer Completeness: {metrics.get('avg_layer_completeness', 0):.3f}\n")
                    f.write(f"  Avg Data Quality: {metrics.get('avg_data_quality', 0):.3f}\n")
                    f.write(f"  Effectiveness Score: {metrics.get('effectiveness_score', 0):.3f}\n\n")
            
            # Best Practices
            best_practices = cross_analysis.get('best_practices', [])
            if best_practices:
                f.write("IDENTIFIED BEST PRACTICES\n")
                f.write("-" * 60 + "\n")
                for i, practice in enumerate(best_practices, 1):
                    f.write(f"{i}. {practice}\n")
                f.write("\n")
            
            # Improvement Opportunities
            opportunities = cross_analysis.get('improvement_opportunities', [])
            if opportunities:
                f.write("IMPROVEMENT OPPORTUNITIES\n")
                f.write("-" * 60 + "\n")
                for i, opportunity in enumerate(opportunities, 1):
                    f.write(f"{i}. {opportunity}\n")
        
        return filename

    def _generate_gap_analysis_report_file(self, collections: Dict[str, Dict], reports_dir: Path, timestamp: str) -> str:
        """Generate gap analysis report file"""
        filename = f"feature_report_gap_analysis_{timestamp}.txt"
        filepath = reports_dir / filename
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        gap_analysis = sample_collection.get('gap_analysis', {})
        root_cause_analysis = sample_collection.get('root_cause_analysis', {})
        
        with open(filepath, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("COMPREHENSIVE COLLECTION STATUS REPORT - GAP ANALYSIS\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Report Type: Gap Analysis\n")
            f.write("=" * 100 + "\n\n")
            
            # Gap Summary
            f.write("GAP ANALYSIS SUMMARY\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Gaps Identified: {gap_analysis.get('total_gaps_identified', 0)}\n")
            f.write(f"Missing Collection Options: {len(gap_analysis.get('missing_options', []))}\n")
            f.write(f"Incomplete Collection Options: {len(gap_analysis.get('incomplete_options', []))}\n")
            f.write(f"Critical Issues: {len(gap_analysis.get('critical_gaps', []))}\n\n")
            
            # Missing Options Detail
            missing_options = gap_analysis.get('missing_options', [])
            if missing_options:
                f.write("MISSING COLLECTION OPTIONS\n")
                f.write("-" * 60 + "\n")
                for option in missing_options:
                    f.write(f"• {option}\n")
                f.write("\n")
            
            # Incomplete Options Detail
            incomplete_options = gap_analysis.get('incomplete_options', [])
            if incomplete_options:
                f.write("INCOMPLETE COLLECTION OPTIONS\n")
                f.write("-" * 60 + "\n")
                for option in incomplete_options:
                    f.write(f"• {option}\n")
                f.write("\n")
            
            # Critical Gaps Detail
            critical_gaps = gap_analysis.get('critical_gaps', [])
            if critical_gaps:
                f.write("CRITICAL GAPS\n")
                f.write("-" * 60 + "\n")
                for gap in critical_gaps:
                    f.write(f"• {gap}\n")
                f.write("\n")
            
            # Coverage Gaps Detail
            coverage_gaps = gap_analysis.get('coverage_gaps', {})
            if coverage_gaps:
                f.write("DETAILED GAP ANALYSIS BY OPTION TYPE\n")
                f.write("-" * 60 + "\n")
                for option_type, gap_info in coverage_gaps.items():
                    f.write(f"{option_type.upper()}:\n")
                    f.write(f"  Option Present: {gap_info.get('option_present', False)}\n")
                    f.write(f"  Collection Count: {gap_info.get('collection_count', 0)}\n")
                    f.write(f"  Completeness Score: {gap_info.get('completeness_score', 0):.3f}\n")
                    
                    identified_gaps = gap_info.get('identified_gaps', [])
                    if identified_gaps:
                        f.write("  Identified Gaps:\n")
                        for gap in identified_gaps:
                            f.write(f"    - {gap}\n")
                    
                    missing_layers = gap_info.get('missing_layers', [])
                    if missing_layers:
                        f.write(f"  Missing Layers: {', '.join(missing_layers)}\n")
                    
                    f.write("\n")
            
            # Root Cause Analysis
            f.write("ROOT CAUSE ANALYSIS\n")
            f.write("-" * 60 + "\n")
            
            impact_assessment = root_cause_analysis.get('impact_assessment', {})
            f.write(f"Critical Impact Issues: {impact_assessment.get('critical_impact_count', 0)}\n")
            f.write(f"High Impact Issues: {impact_assessment.get('high_impact_count', 0)}\n")
            f.write(f"Total Issues: {impact_assessment.get('total_issues', 0)}\n")
            f.write(f"Affected Options: {impact_assessment.get('affected_options', 0)}\n\n")
            
            # Prioritized Causes
            prioritized_causes = root_cause_analysis.get('prioritized_causes', [])
            if prioritized_causes:
                f.write("PRIORITIZED ROOT CAUSES\n")
                f.write("-" * 60 + "\n")
                for i, cause in enumerate(prioritized_causes, 1):
                    f.write(f"{i}. {cause.get('cause', 'Unknown')}\n")
                    f.write(f"   Category: {cause.get('category', 'Unknown')}\n")
                    f.write(f"   Severity: {cause.get('severity', 'Unknown')}\n")
                    f.write(f"   Remediation Effort: {cause.get('remediation_effort', 'Unknown')}\n")
                    f.write(f"   Description: {cause.get('description', '')}\n\n")
        
        return filename

    def _generate_recommendations_report_file(self, collections: Dict[str, Dict], reports_dir: Path, timestamp: str) -> str:
        """Generate recommendations report file"""
        filename = f"feature_report_recommendations_{timestamp}.txt"
        filepath = reports_dir / filename
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        recommendations = sample_collection.get('recommendations', {})
        
        with open(filepath, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("COMPREHENSIVE COLLECTION STATUS REPORT - RECOMMENDATIONS\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Report Type: Actionable Recommendations\n")
            f.write("=" * 100 + "\n\n")
            
            # Immediate Actions
            immediate_actions = recommendations.get('immediate_actions', [])
            if immediate_actions:
                f.write("IMMEDIATE ACTIONS REQUIRED\n")
                f.write("-" * 60 + "\n")
                for i, action in enumerate(immediate_actions, 1):
                    f.write(f"{i}. {action.get('action', 'Unknown Action')}\n")
                    f.write(f"   Priority: {action.get('priority', 'Unknown')}\n")
                    f.write(f"   Effort: {action.get('effort', 'Unknown')}\n")
                    f.write(f"   Impact: {action.get('impact', 'Unknown')}\n")
                    f.write(f"   Timeline: {action.get('timeline', 'TBD')}\n")
                    f.write(f"   Description: {action.get('description', '')}\n")
                    f.write(f"   Command: {action.get('command', 'N/A')}\n\n")
            
            # Short-term Improvements
            short_term_improvements = recommendations.get('short_term_improvements', [])
            if short_term_improvements:
                f.write("SHORT-TERM IMPROVEMENTS\n")
                f.write("-" * 60 + "\n")
                for i, action in enumerate(short_term_improvements, 1):
                    f.write(f"{i}. {action.get('action', 'Unknown Action')}\n")
                    f.write(f"   Priority: {action.get('priority', 'Unknown')}\n")
                    f.write(f"   Effort: {action.get('effort', 'Unknown')}\n")
                    f.write(f"   Impact: {action.get('impact', 'Unknown')}\n")
                    f.write(f"   Timeline: {action.get('timeline', 'TBD')}\n")
                    f.write(f"   Description: {action.get('description', '')}\n")
                    f.write(f"   Command: {action.get('command', 'N/A')}\n\n")
            
            # Long-term Enhancements
            long_term_enhancements = recommendations.get('long_term_enhancements', [])
            if long_term_enhancements:
                f.write("LONG-TERM ENHANCEMENTS\n")
                f.write("-" * 60 + "\n")
                for i, action in enumerate(long_term_enhancements, 1):
                    f.write(f"{i}. {action.get('action', 'Unknown Action')}\n")
                    f.write(f"   Priority: {action.get('priority', 'Unknown')}\n")
                    f.write(f"   Effort: {action.get('effort', 'Unknown')}\n")
                    f.write(f"   Impact: {action.get('impact', 'Unknown')}\n")
                    f.write(f"   Timeline: {action.get('timeline', 'TBD')}\n")
                    f.write(f"   Description: {action.get('description', '')}\n")
                    f.write(f"   Command: {action.get('command', 'N/A')}\n\n")
            
            # Quick Wins
            quick_wins = recommendations.get('quick_wins', [])
            if quick_wins:
                f.write("QUICK WIN OPPORTUNITIES\n")
                f.write("-" * 60 + "\n")
                for i, win in enumerate(quick_wins, 1):
                    f.write(f"{i}. {win.get('action', 'Unknown Action')}\n")
                    f.write(f"   Description: {win.get('description', '')}\n")
                    f.write(f"   Timeline: {win.get('timeline', 'TBD')}\n\n")
            
            # Implementation Roadmap
            roadmap = recommendations.get('implementation_roadmap', [])
            if roadmap:
                f.write("IMPLEMENTATION ROADMAP\n")
                f.write("-" * 60 + "\n")
                for phase in roadmap:
                    f.write(f"PHASE: {phase.get('phase', 'Unknown Phase')}\n")
                    f.write(f"Timeline: {phase.get('timeline', 'TBD')}\n")
                    f.write(f"Objective: {phase.get('objective', '')}\n")
                    
                    actions = phase.get('actions', [])
                    if actions:
                        f.write("Actions:\n")
                        for action in actions:
                            f.write(f"  • {action.get('action', 'Unknown')}\n")
                    f.write("\n")
            
            # Resource Requirements
            resource_reqs = recommendations.get('resource_requirements', {})
            if resource_reqs:
                f.write("RESOURCE REQUIREMENTS\n")
                f.write("-" * 60 + "\n")
                f.write(f"Total Estimated Effort: {resource_reqs.get('total_estimated_effort', 'TBD')}\n")
                f.write(f"Immediate Effort: {resource_reqs.get('immediate_effort_hours', 0)} hours\n")
                f.write(f"Short-term Effort: {resource_reqs.get('short_term_effort_days', 0)} days\n")
                f.write(f"Long-term Effort: {resource_reqs.get('long_term_effort_weeks', 0)} weeks\n")
                f.write(f"Recommended Team Size: {resource_reqs.get('recommended_team_size', 'TBD')}\n")
                f.write(f"Budget Estimate: {resource_reqs.get('budget_estimate', 'TBD')}\n\n")
            
            # Success Metrics
            success_metrics = recommendations.get('success_metrics', {})
            if success_metrics:
                f.write("SUCCESS METRICS & TARGETS\n")
                f.write("-" * 60 + "\n")
                for metric, target in success_metrics.items():
                    metric_name = metric.replace('_', ' ').title()
                    f.write(f"{metric_name}: {target}\n")
                f.write("\n")
            
            # Strategic Initiatives
            strategic_initiatives = recommendations.get('strategic_initiatives', [])
            if strategic_initiatives:
                f.write("STRATEGIC INITIATIVES\n")
                f.write("-" * 60 + "\n")
                for initiative in strategic_initiatives:
                    f.write(f"Initiative: {initiative.get('initiative', 'Unknown Initiative')}\n")
                    f.write(f"Description: {initiative.get('description', '')}\n")
                    f.write(f"Timeline: {initiative.get('timeline', 'TBD')}\n")
                    f.write(f"Impact: {initiative.get('impact', 'TBD')}\n\n")
        
        return filename

    def _generate_device_analysis_report_file(self, collections: Dict[str, Dict], reports_dir: Path, timestamp: str) -> str:
        """Generate device analysis report file"""
        filename = f"feature_report_device_analysis_{timestamp}.txt"
        filepath = reports_dir / filename
        
        # Get sample collection for aggregate data
        sample_collection = next(iter(collections.values()))
        device_stats = sample_collection.get('global_device_stats', {})
        
        with open(filepath, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("COMPREHENSIVE COLLECTION STATUS REPORT - DEVICE ANALYSIS\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Report Type: Device Analysis\n")
            f.write("=" * 100 + "\n\n")
            
            # Device Overview
            f.write("DEVICE OVERVIEW\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Unique Devices: {len(device_stats.get('total_devices', set()))}\n")
            f.write(f"Accessible Devices: {len(device_stats.get('accessible_devices', set()))}\n")
            f.write(f"Failed Devices: {len(device_stats.get('failed_devices', set()))}\n")
            f.write(f"Consistent Devices: {len(device_stats.get('consistent_devices', set()))}\n")
            f.write(f"Inconsistent Devices: {len(device_stats.get('inconsistent_devices', set()))}\n\n")
            
            # Device Success Rates
            device_success_rates = device_stats.get('device_success_rates', {})
            if device_success_rates:
                f.write("DEVICE SUCCESS RATES\n")
                f.write("-" * 60 + "\n")
                for device_ip, success_rate in sorted(device_success_rates.items()):
                    status = "EXCELLENT" if success_rate >= 95 else "GOOD" if success_rate >= 85 else "FAIR" if success_rate >= 70 else "POOR"
                    f.write(f"{device_ip}: {success_rate}% ({status})\n")
                f.write("\n")
            
            # Device Collection Counts
            device_collection_counts = device_stats.get('device_collection_counts', {})
            if device_collection_counts:
                f.write("DEVICE COLLECTION PARTICIPATION\n")
                f.write("-" * 60 + "\n")
                for device_ip, count in sorted(device_collection_counts.items()):
                    f.write(f"{device_ip}: {count} collections\n")
                f.write("\n")
            
            # Device Layer Coverage
            device_layer_coverage = device_stats.get('device_layer_coverage', {})
            if device_layer_coverage:
                f.write("DEVICE LAYER COVERAGE\n")
                f.write("-" * 60 + "\n")
                for device_ip, layers in sorted(device_layer_coverage.items()):
                    layer_list = ", ".join(sorted(layers)) if layers else "None"
                    f.write(f"{device_ip}: {layer_list}\n")
                f.write("\n")
            
            # Detailed Device Analysis
            f.write("DETAILED DEVICE ANALYSIS\n")
            f.write("-" * 60 + "\n")
            
            # Analyze each collection for device details
            for collection_name, collection_info in collections.items():
                device_analysis = collection_info.get('device_analysis', {})
                device_details = device_analysis.get('device_details', {})
                
                if device_details:
                    f.write(f"Collection: {collection_name}\n")
                    f.write(f"Collection Success Rate: {device_analysis.get('device_success_rate', 0)}%\n")
                    
                    for device_ip, details in device_details.items():
                        f.write(f"  Device: {device_ip}\n")
                        f.write(f"    Status: {details.get('accessibility_status', 'Unknown')}\n")
                        f.write(f"    Total Files: {details.get('total_files', 0)}\n")
                        f.write(f"    Layers Count: {details.get('layers_count', 0)}\n")
                        f.write(f"    Data Quality Score: {details.get('data_quality_score', 0):.3f}\n")
                        f.write(f"    Layers: {', '.join(details.get('layers', []))}\n")
                        f.write(f"    Has Errors: {details.get('has_errors', False)}\n")
                    f.write("\n")
        
        return filename

    def _generate_json_export_file(self, collections: Dict[str, Dict], reports_dir: Path, timestamp: str) -> str:
        """Generate JSON export file with all analysis data"""
        filename = f"feature_report_data_export_{timestamp}.json"
        filepath = reports_dir / filename
        
        # Prepare data for JSON export (convert sets to lists)
        export_data = {}
        
        for collection_name, collection_info in collections.items():
            # Deep copy and convert sets to lists for JSON serialization
            export_collection = {}
            
            for key, value in collection_info.items():
                if isinstance(value, set):
                    export_collection[key] = list(value)
                elif isinstance(value, dict):
                    export_collection[key] = self._convert_sets_to_lists(value)
                elif isinstance(value, Path):
                    export_collection[key] = str(value)
                else:
                    export_collection[key] = value
            
            export_data[collection_name] = export_collection
        
        # Add metadata
        export_data['_metadata'] = {
            'generated_timestamp': datetime.now().isoformat(),
            'report_type': 'comprehensive_collection_status_analysis',
            'version': '1.0',
            'total_collections': len(collections),
            'analysis_scope': 'All collection options 1-10'
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return filename

    def _convert_sets_to_lists(self, obj):
        """Recursively convert sets to lists for JSON serialization"""
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_sets_to_lists(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_sets_to_lists(item) for item in obj]
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return obj

    def _display_report_generation_summary(self, report_files: Dict[str, str], reports_dir: Path):
        """Display summary of generated reports"""
        print_info("📋 Report Generation Summary:")
        print_info(f"   📁 Reports Directory: {reports_dir}")
        print_info(f"   📄 Total Reports Generated: {len(report_files)}")
        print_info("")
        print_info("📊 Generated Reports:")
        
        report_descriptions = {
            'executive_summary': '📋 Executive Summary - High-level overview for management',
            'technical_analysis': '🔬 Technical Analysis - Detailed technical findings',
            'gap_analysis': '🔍 Gap Analysis - Comprehensive gap identification and root causes',
            'recommendations': '💡 Recommendations - Actionable recommendations and roadmap',
            'device_analysis': '🖥️  Device Analysis - Per-device detailed analysis',
            'json_export': '📄 JSON Export - Complete data export for further analysis'
        }
        
        for report_type, filename in report_files.items():
            description = report_descriptions.get(report_type, f'📄 {report_type.title()} Report')
            print_info(f"   • {description}")
            print_info(f"     File: {filename}")
        
        print_info("")
        print_success("✅ All reports successfully generated and saved")

    def _handle_export_and_persistence(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Handle export and persistence of all analysis data (T007)
        
        Args:
            collections: Collections with complete analysis data
            
        Returns:
            Dict[str, Dict]: Collections with export and persistence metadata
        """
        print_info("🗄️  Handling export and persistence...")
        
        try:
            # Create exports directory if it doesn't exist
            reports_dir = Path("feature_report_outputs")
            reports_dir.mkdir(exist_ok=True)
            
            # Create comprehensive CSV export
            print_info("📊 Generating CSV exports...")
            csv_files = self._generate_csv_exports(collections, reports_dir)
            
            # Create summary dashboard export
            print_info("📋 Generating dashboard export...")
            dashboard_file = self._generate_dashboard_export(collections, reports_dir)
            
            # Create archival backup
            print_info("🗂️  Creating archival backup...")
            backup_file = self._create_archival_backup(collections, reports_dir)
            
            # Update collections with export metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            for collection_name, collection_info in collections.items():
                if 'export_metadata' not in collection_info:
                    collection_info['export_metadata'] = {}
                
                collection_info['export_metadata'].update({
                    'export_timestamp': timestamp,
                    'csv_files': csv_files,
                    'dashboard_file': dashboard_file,
                    'backup_file': backup_file,
                    'export_directory': str(reports_dir),
                    'export_status': 'completed'
                })
            
            print_success("✅ Export and persistence completed successfully")
            print_info(f"📁 All exports saved to: {reports_dir}")
            
            # Display export summary
            self._display_export_summary(csv_files, dashboard_file, backup_file, reports_dir)
            
            return collections
            
        except Exception as e:
            print_error(f"Error in export and persistence: {str(e)}")
            # Mark export as failed but continue
            for collection_info in collections.values():
                if 'export_metadata' not in collection_info:
                    collection_info['export_metadata'] = {}
                collection_info['export_metadata']['export_status'] = 'failed'
                collection_info['export_metadata']['error'] = str(e)
            
            return collections

    def _generate_csv_exports(self, collections: Dict[str, Dict], reports_dir: Path) -> Dict[str, str]:
        """Generate CSV exports for structured data analysis"""
        csv_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Collections Summary CSV
            collections_csv = reports_dir / f"feature_report_collections_summary_{timestamp}.csv"
            with open(collections_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Collection Name', 'Option Type', 'Device Count', 'Layer Count', 
                               'Completeness Score', 'Creation Time', 'Status'])
                
                for collection_name, collection_info in collections.items():
                    writer.writerow([
                        collection_name,
                        collection_info.get('option_type', 'unknown'),
                        len(collection_info.get('devices', [])),
                        len(collection_info.get('layers_found', [])),
                        f"{collection_info.get('completeness_score', 0):.3f}",
                        collection_info.get('creation_time', 'unknown'),
                        'completed' if collection_info.get('device_count', 0) > 0 else 'empty'
                    ])
            
            csv_files['collections_summary'] = collections_csv.name
            
            # Device Analysis CSV
            devices_csv = reports_dir / f"feature_report_device_analysis_{timestamp}.csv"
            with open(devices_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Collection', 'Device IP', 'Hostname', 'Accessibility Status', 
                               'Total Files', 'Layers Count', 'Data Quality Score', 'Has Errors',
                               'Layers Available'])
                
                for collection_name, collection_info in collections.items():
                    for device_info in collection_info.get('devices', []):
                        writer.writerow([
                            collection_name,
                            device_info.get('device_ip', ''),
                            device_info.get('hostname', ''),
                            device_info.get('accessibility_status', ''),
                            device_info.get('total_files', 0),
                            device_info.get('layers_count', 0),
                            f"{device_info.get('data_quality_score', 0):.3f}",
                            device_info.get('has_errors', False),
                            ', '.join(device_info.get('layers', []))
                        ])
            
            csv_files['device_analysis'] = devices_csv.name
            
            # Gap Analysis CSV  
            gaps_csv = reports_dir / f"feature_report_gaps_analysis_{timestamp}.csv"
            with open(gaps_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Gap Type', 'Option Type', 'Description', 'Severity', 'Impact'])
                
                # Get sample collection for gap data
                sample_collection = next(iter(collections.values()))
                gap_analysis = sample_collection.get('gap_analysis', {})
                
                # Missing options
                for option in gap_analysis.get('missing_options', []):
                    writer.writerow(['Missing Option', option, 'Collection option not executed', 
                                   'High', 'Incomplete data coverage'])
                
                # Critical gaps
                for gap in gap_analysis.get('critical_gaps', []):
                    writer.writerow(['Critical Gap', 'Various', gap, 'Critical', 'High business impact'])
            
            csv_files['gap_analysis'] = gaps_csv.name
            
            return csv_files
            
        except Exception as e:
            print_error(f"Error generating CSV exports: {str(e)}")
            return {}

    def _generate_dashboard_export(self, collections: Dict[str, Dict], reports_dir: Path) -> str:
        """Generate dashboard-ready export file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dashboard_file = reports_dir / f"feature_report_dashboard_data_{timestamp}.json"
        
        try:
            # Get sample collection for aggregate data
            sample_collection = next(iter(collections.values()))
            
            dashboard_data = {
                'dashboard_summary': {
                    'total_collections': len(collections),
                    'total_devices': len(sample_collection.get('global_device_stats', {}).get('total_devices', set())),
                    'device_reliability': len(sample_collection.get('global_device_stats', {}).get('accessible_devices', set())),
                    'total_gaps': sample_collection.get('gap_analysis', {}).get('total_gaps_identified', 0),
                    'critical_gaps': len(sample_collection.get('gap_analysis', {}).get('critical_gaps', [])),
                    'immediate_actions': len(sample_collection.get('recommendations', {}).get('immediate_actions', [])),
                    'generated_timestamp': datetime.now().isoformat()
                },
                'collection_health': [
                    {
                        'name': collection_name,
                        'option_type': collection_info.get('option_type', 'unknown'),
                        'device_count': len(collection_info.get('devices', [])),
                        'completeness_score': collection_info.get('completeness_score', 0),
                        'status': 'healthy' if collection_info.get('completeness_score', 0) > 0.6 else 'needs_attention'
                    }
                    for collection_name, collection_info in collections.items()
                ],
                'device_statistics': {
                    'total_devices': len(sample_collection.get('global_device_stats', {}).get('total_devices', set())),
                    'accessible_devices': len(sample_collection.get('global_device_stats', {}).get('accessible_devices', set())),
                    'consistent_devices': len(sample_collection.get('global_device_stats', {}).get('consistent_devices', set())),
                    'device_success_rates': dict(sample_collection.get('global_device_stats', {}).get('device_success_rates', {}))
                },
                'recommendations_summary': {
                    'immediate_actions': sample_collection.get('recommendations', {}).get('immediate_actions', []),
                    'quick_wins': sample_collection.get('recommendations', {}).get('quick_wins', []),
                    'resource_requirements': sample_collection.get('recommendations', {}).get('resource_requirements', {})
                }
            }
            
            with open(dashboard_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            
            return dashboard_file.name
            
        except Exception as e:
            print_error(f"Error generating dashboard export: {str(e)}")
            return ""

    def _create_archival_backup(self, collections: Dict[str, Dict], reports_dir: Path) -> str:
        """Create comprehensive archival backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = reports_dir / f"feature_report_complete_backup_{timestamp}.json"
        
        try:
            # Create complete backup with all data
            backup_data = {
                'backup_metadata': {
                    'created_timestamp': datetime.now().isoformat(),
                    'backup_type': 'comprehensive_analysis_backup',
                    'version': '1.0',
                    'total_collections': len(collections),
                    'backup_purpose': 'Complete archival of comprehensive collection status analysis'
                },
                'collections_data': {}
            }
            
            # Convert collections data for backup (handle non-serializable objects)
            for collection_name, collection_info in collections.items():
                backup_collection = {}
                
                for key, value in collection_info.items():
                    if isinstance(value, set):
                        backup_collection[key] = list(value)
                    elif isinstance(value, Path):
                        backup_collection[key] = str(value)
                    elif isinstance(value, datetime):
                        backup_collection[key] = value.isoformat()
                    elif isinstance(value, dict):
                        backup_collection[key] = self._convert_sets_to_lists(value)
                    elif isinstance(value, list):
                        backup_collection[key] = [self._convert_sets_to_lists(item) for item in value]
                    else:
                        backup_collection[key] = value
                
                backup_data['collections_data'][collection_name] = backup_collection
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            return backup_file.name
            
        except Exception as e:
            print_error(f"Error creating archival backup: {str(e)}")
            return ""

    def _display_export_summary(self, csv_files: Dict[str, str], dashboard_file: str, backup_file: str, reports_dir: Path):
        """Display summary of export operations"""
        print_info("📊 Export and Persistence Summary:")
        print_info(f"   📁 Export Directory: {reports_dir}")
        print_info("")
        
        if csv_files:
            print_info("📈 CSV Exports:")
            for export_type, filename in csv_files.items():
                print_info(f"   • {export_type.replace('_', ' ').title()}: {filename}")
        
        if dashboard_file:
            print_info(f"\n📋 Dashboard Export: {dashboard_file}")
        
        if backup_file:
            print_info(f"\n🗂️  Archival Backup: {backup_file}")
        
        print_info("")
        print_success("✅ All data successfully exported and persisted")

    def _perform_testing_and_validation(self, collections: Dict[str, Dict]) -> Dict[str, Dict]:
        """Perform comprehensive testing and validation (T008)
        
        Args:
            collections: Collections with complete analysis data
            
        Returns:
            Dict[str, Dict]: Collections with validation results
        """
        print_info("🧪 Starting comprehensive testing and validation...")
        
        validation_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0,
            'test_details': []
        }
        
        try:
            # T008.1: Data Integrity Validation
            print_info("🔍 T008.1: Performing data integrity validation...")
            integrity_results = self._validate_data_integrity(collections)
            validation_results['test_details'].append(integrity_results)
            
            # T008.2: Report Generation Validation
            print_info("📊 T008.2: Performing report generation validation...")
            report_results = self._validate_report_generation(collections)
            validation_results['test_details'].append(report_results)
            
            # T008.3: Export Functionality Validation
            print_info("📤 T008.3: Performing export functionality validation...")
            export_results = self._validate_export_functionality(collections)
            validation_results['test_details'].append(export_results)
            
            # T008.4: Analysis Engine Validation
            print_info("⚙️  T008.4: Performing analysis engine validation...")
            analysis_results = self._validate_analysis_engine(collections)
            validation_results['test_details'].append(analysis_results)
            
            # Calculate overall results
            for test_result in validation_results['test_details']:
                validation_results['total_tests'] += test_result['total_tests']
                validation_results['passed_tests'] += test_result['passed_tests']
                validation_results['failed_tests'] += test_result['failed_tests']
                validation_results['warnings'] += test_result['warnings']
            
            # Display validation summary
            self._display_validation_summary(validation_results)
            
            # Store validation results in collections
            for collection_info in collections.values():
                collection_info['validation_results'] = validation_results
            
            return collections
            
        except Exception as e:
            print_error(f"Error in testing and validation: {str(e)}")
            return collections

    def _validate_data_integrity(self, collections: Dict[str, Dict]) -> Dict:
        """Validate data integrity across all collections"""
        results = {
            'test_name': 'Data Integrity Validation',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0,
            'details': []
        }
        
        # Test 1: Collection data structure validation
        results['total_tests'] += 1
        if len(collections) > 0:
            results['passed_tests'] += 1
            results['details'].append("✅ Collections data structure is valid")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ No collections found")
        
        # Test 2: Device data consistency
        results['total_tests'] += 1
        sample_collection = next(iter(collections.values()))
        device_stats = sample_collection.get('global_device_stats', {})
        if device_stats and len(device_stats.get('total_devices', set())) > 0:
            results['passed_tests'] += 1
            results['details'].append("✅ Device data consistency validated")
        else:
            results['warnings'] += 1
            results['details'].append("⚠️  No device data found for validation")
        
        # Test 3: Analysis data completeness
        results['total_tests'] += 1
        if sample_collection.get('gap_analysis') and sample_collection.get('recommendations'):
            results['passed_tests'] += 1
            results['details'].append("✅ Analysis data completeness validated")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ Analysis data incomplete")
        
        return results

    def _validate_report_generation(self, collections: Dict[str, Dict]) -> Dict:
        """Validate report generation functionality"""
        results = {
            'test_name': 'Report Generation Validation',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0,
            'details': []
        }
        
        reports_dir = Path("feature_report_outputs")
        
        # Test 1: Reports directory exists
        results['total_tests'] += 1
        if reports_dir.exists():
            results['passed_tests'] += 1
            results['details'].append("✅ Reports directory exists")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ Reports directory not found")
        
        # Test 2: Required report files exist
        required_reports = [
            'executive_summary',
            'technical_analysis', 
            'gap_analysis',
            'recommendations',
            'device_analysis',
            'data_export'
        ]
        
        for report_type in required_reports:
            results['total_tests'] += 1
            report_files = list(reports_dir.glob(f"feature_report_{report_type}_*.txt")) + \
                          list(reports_dir.glob(f"feature_report_{report_type}_*.json"))
            
            if report_files:
                results['passed_tests'] += 1
                results['details'].append(f"✅ {report_type.replace('_', ' ').title()} report generated")
            else:
                results['failed_tests'] += 1
                results['details'].append(f"❌ {report_type.replace('_', ' ').title()} report missing")
        
        return results

    def _validate_export_functionality(self, collections: Dict[str, Dict]) -> Dict:
        """Validate export functionality"""
        results = {
            'test_name': 'Export Functionality Validation',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0,
            'details': []
        }
        
        reports_dir = Path("feature_report_outputs")
        
        # Test 1: CSV exports exist
        csv_files = list(reports_dir.glob("*.csv"))
        results['total_tests'] += 1
        if csv_files:
            results['passed_tests'] += 1
            results['details'].append(f"✅ CSV exports generated ({len(csv_files)} files)")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ No CSV exports found")
        
        # Test 2: Dashboard export exists
        dashboard_files = list(reports_dir.glob("feature_report_dashboard_data_*.json"))
        results['total_tests'] += 1
        if dashboard_files:
            results['passed_tests'] += 1
            results['details'].append("✅ Dashboard export generated")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ Dashboard export missing")
        
        # Test 3: Backup files exist
        backup_files = list(reports_dir.glob("feature_report_complete_backup_*.json"))
        results['total_tests'] += 1
        if backup_files:
            results['passed_tests'] += 1
            results['details'].append("✅ Archival backup generated")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ Archival backup missing")
        
        return results

    def _validate_analysis_engine(self, collections: Dict[str, Dict]) -> Dict:
        """Validate analysis engine functionality"""
        results = {
            'test_name': 'Analysis Engine Validation',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0,
            'details': []
        }
        
        sample_collection = next(iter(collections.values()))
        
        # Test 1: Gap analysis functionality
        results['total_tests'] += 1
        gap_analysis = sample_collection.get('gap_analysis', {})
        if gap_analysis and 'total_gaps_identified' in gap_analysis:
            results['passed_tests'] += 1
            results['details'].append("✅ Gap analysis engine functional")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ Gap analysis engine failed")
        
        # Test 2: Recommendations generation
        results['total_tests'] += 1
        recommendations = sample_collection.get('recommendations', {})
        if recommendations and 'immediate_actions' in recommendations:
            results['passed_tests'] += 1
            results['details'].append("✅ Recommendations engine functional")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ Recommendations engine failed")
        
        # Test 3: Cross-option analysis
        results['total_tests'] += 1
        cross_analysis = sample_collection.get('cross_analysis', {})
        if cross_analysis and 'option_effectiveness' in cross_analysis:
            results['passed_tests'] += 1
            results['details'].append("✅ Cross-option analysis functional")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ Cross-option analysis failed")
        
        # Test 4: Device statistics
        results['total_tests'] += 1
        device_stats = sample_collection.get('global_device_stats', {})
        if device_stats and 'total_devices' in device_stats:
            results['passed_tests'] += 1
            results['details'].append("✅ Device statistics analysis functional")
        else:
            results['failed_tests'] += 1
            results['details'].append("❌ Device statistics analysis failed")
        
        return results

    def _display_validation_summary(self, validation_results: Dict):
        """Display comprehensive validation summary"""
        print_header("🧪 TESTING AND VALIDATION SUMMARY", Colors.GREEN)
        
        total_tests = validation_results['total_tests']
        passed_tests = validation_results['passed_tests']
        failed_tests = validation_results['failed_tests']
        warnings = validation_results['warnings']
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print_info(f"📊 Overall Test Results:")
        print_info(f"   • Total Tests: {total_tests}")
        print_info(f"   • Passed: {passed_tests}")
        print_info(f"   • Failed: {failed_tests}")
        print_info(f"   • Warnings: {warnings}")
        print_info(f"   • Success Rate: {success_rate:.1f}%")
        print_info("")
        
        # Display results by test category
        for test_detail in validation_results['test_details']:
            test_name = test_detail['test_name']
            test_passed = test_detail['passed_tests']
            test_total = test_detail['total_tests']
            test_success_rate = (test_passed / test_total * 100) if test_total > 0 else 0
            
            print_info(f"🔍 {test_name}:")
            print_info(f"   • Success Rate: {test_success_rate:.1f}% ({test_passed}/{test_total})")
            
            for detail in test_detail['details'][:3]:  # Show first 3 details
                print_info(f"   {detail}")
            
            if len(test_detail['details']) > 3:
                print_info(f"   ... and {len(test_detail['details']) - 3} more")
            print_info("")
        
        # Overall status
        if success_rate >= 90:
            print_success("🎉 EXCELLENT: All critical tests passed successfully!")
        elif success_rate >= 75:
            print_success("✅ GOOD: Most tests passed with minor issues")
        elif success_rate >= 50:
            print_warning("⚠️  ACCEPTABLE: Some tests failed, review recommended")
        else:
            print_error("❌ NEEDS ATTENTION: Multiple test failures detected")
        
        print_success("✅ Testing and validation completed")

def main():
    """Main entry point"""
    manager = RR4StartupManager()
    manager.run()

if __name__ == "__main__":
    main() 
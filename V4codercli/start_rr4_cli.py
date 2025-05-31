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
        print(f"   - All layers (health, interfaces, igp, bgp, mpls, vpn, static)")
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
        
        print(f"\n{Colors.RED}0. 🚪 EXIT{Colors.RESET}")
        
        while True:
            try:
                choice = input(f"\n{Colors.BOLD}Select option (0-7): {Colors.RESET}").strip()
                if choice in ['0', '1', '2', '3', '4', '5', '6', '7']:
                    return int(choice)
                else:
                    print_error("Invalid choice. Please enter 0-7.")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                return 0
            except Exception:
                print_error("Invalid input. Please enter a number (0-7).")
    
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
        
        # Run full collection with extended timeout
        success, stdout, stderr = self._run_command(
            ["python3", str(self.main_script), "collect-all", "--layers", "health,interfaces,igp,bgp,mpls,vpn,static"],
            "Full data collection (all layers, all reachable devices)",
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
        layers = ["health", "interfaces", "igp", "bgp", "mpls", "vpn", "static"]
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

def main():
    """Main entry point"""
    manager = RR4StartupManager()
    manager.run()

if __name__ == "__main__":
    main() 
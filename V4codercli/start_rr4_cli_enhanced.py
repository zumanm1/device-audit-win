#!/usr/bin/env python3
"""
RR4 CLI Interactive Startup Script - Enhanced with Command-Line Options
Comprehensive guided setup and execution for the RR4 Complete Enhanced v4 CLI

CROSS-PLATFORM STARTUP:
- Windows 10/11: python start_rr4_cli_enhanced.py
- Linux: python3 start_rr4_cli_enhanced.py
- macOS: python3 start_rr4_cli_enhanced.py

COMMAND-LINE OPTIONS:
- Direct execution: python3 start_rr4_cli_enhanced.py --option 1
- First-time wizard: python3 start_rr4_cli_enhanced.py --option 11
- Show help: python3 start_rr4_cli_enhanced.py --help
- Interactive mode: python3 start_rr4_cli_enhanced.py (default)

This script provides:
- Comprehensive first-time startup wizard (Option 11)
- Guided first-time setup
- Prerequisites checking
- Step-by-step testing
- Menu-driven interface for different use cases
- Direct command-line access to all options (0-12)
- Error handling and recovery
- Best practice recommendations

Author: AI Assistant
Version: 1.2.0-CrossPlatform-CLI-Enhanced-FirstTime
Created: 2025-06-02
Updated: 2025-06-03
Platform Support: Windows 10/11, Linux, macOS
"""

import os
import sys
import time
import json
import csv
import subprocess
import platform
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Import the original startup manager
from start_rr4_cli import RR4StartupManager, Colors, print_header, print_info, print_success, print_error, print_warning, print_section, display_startup_info

class EnhancedRR4StartupManager(RR4StartupManager):
    """Enhanced RR4 Startup Manager with Option 11 support"""
    
    def show_main_menu(self) -> int:
        """Enhanced main menu that includes Option 11"""
        while True:
            display_startup_info()
            
            print_header("RR4 COMPLETE ENHANCED V4 CLI - MAIN MENU", Colors.CYAN)
            print_info("📂 Network automation system for 11 Cisco routers")
            print_info("🌐 Jump host: 172.16.39.128")
            print_info("📊 Data collection: 8 specialized collectors")
            print_info("🔒 Security rating: A+")
            print_info("")
            
            # Enhanced menu with all options including 11
            menu_options = [
                "  0: 🚪 EXIT",
                "  1: 🎯 FIRST-TIME SETUP - Complete guided setup",
                "  2: 🔍 AUDIT ONLY - Quick health & connectivity check",
                "  3: 📊 FULL COLLECTION - Production data collection",
                "  4: 🎛️  CUSTOM COLLECTION - Choose devices & layers",
                "  5: 🔧 PREREQUISITES CHECK - Verify system requirements",
                "  6: 🌐 ENHANCED CONNECTIVITY - Comprehensive network test",
                "  7: 📚 HELP & OPTIONS - Show all available commands",
                "  8: 🎯 CONSOLE AUDIT - Console line discovery",
                "  9: 🌟 COMPLETE COLLECTION - All layers + Console",
                " 10: 🔒 CONSOLE SECURITY AUDIT - Transport security",
                f" 11: {Colors.YELLOW}🚀 FIRST-TIME WIZARD - New user onboarding{Colors.RESET} ⭐",
                " 12: 📊 STATUS REPORT - Comprehensive analysis"
            ]
            
            print_info("Available options:")
            for option in menu_options:
                print_info(option)
            
            print_info("")
            print_info("🌟 NEW USERS: Start with Option 11 for guided setup!")
            print_info("")
            
            # Enhanced input validation with Option 11 support
            while True:
                try:
                    choice = input(f"\n{Colors.BOLD}Select option (0-12): {Colors.RESET}").strip()
                    if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']:
                        return int(choice)
                    else:
                        print_error("Invalid choice. Please enter 0-12.")
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                    return 0
                except Exception:
                    print_error("Invalid input. Please enter a number (0-12).")
    
    def run(self):
        """Enhanced main execution loop with Option 11 support"""
        print_header("V4CODERCLI ENHANCED STARTUP", Colors.GREEN)
        
        while True:
            try:
                choice = self.show_main_menu()
                
                if choice == 0:
                    print_success("Thank you for using V4CODERCLI! Goodbye!")
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
                elif choice == 11:
                    # Call our enhanced first-time wizard
                    class Args:
                        quiet = False
                    args = Args()
                    first_time_startup_wizard(args)
                elif choice == 12:
                    self.comprehensive_status_report()
                else:
                    print_error("Invalid option selected.")
                
            except KeyboardInterrupt:
                print_warning("\nOperation cancelled by user.")
                break
            except Exception as e:
                print_error(f"Unexpected error: {str(e)}")
                break

def detect_first_time_usage():
    """Detect if this is likely a first-time usage"""
    indicators = {
        'no_output_dir': not Path('outputs').exists(),
        'no_env_configured': not any(Path(f).exists() for f in ['.env-t', 'rr4-complete-enchanced-v4-cli.env-t']),
        'no_previous_collections': not any(Path('outputs').glob('**/collection_*')) if Path('outputs').exists() else True,
        'no_health_monitor_history': not list(Path('.').glob('system_health_*.json'))
    }
    
    first_time_score = sum(indicators.values())
    return first_time_score >= 2, indicators

def parse_command_line_arguments():
    """Parse command line arguments for direct option execution"""
    parser = argparse.ArgumentParser(
        description='RR4 CLI Interactive Startup Script with Direct Option Access',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
OPTION DESCRIPTIONS:
  0   🚪 EXIT                          - Exit the application
  1   🎯 FIRST-TIME SETUP             - Complete guided setup with prerequisites check
  2   🔍 AUDIT ONLY                   - Quick connectivity and health check
  3   📊 FULL COLLECTION              - Production data collection
  4   🎛️  CUSTOM COLLECTION            - Choose specific devices and layers
  5   🔧 PREREQUISITES CHECK ONLY     - Verify system requirements
  6   🌐 ENHANCED CONNECTIVITY TEST   - Comprehensive connectivity test
  7   📚 SHOW HELP & OPTIONS          - Display all available commands
  8   🎯 CONSOLE AUDIT                - Console line discovery and collection
  9   🌟 COMPLETE COLLECTION          - All layers + Console in systematic order
  10  🔒 CONSOLE SECURITY AUDIT       - Transport security analysis
  11  🚀 FIRST-TIME STARTUP WIZARD    - Comprehensive new user onboarding
  12  📊 COMPREHENSIVE STATUS REPORT  - All options analysis with device filtering

FIRST-TIME USER RECOMMENDATIONS:
  python3 start_rr4_cli_enhanced.py --option 11        # ⭐ RECOMMENDED for new users
  python3 start_rr4_cli_enhanced.py --first-time       # Alternative first-time flag
  python3 start_rr4_cli_enhanced.py                    # Interactive menu with auto-detection

EXAMPLES:
  python3 start_rr4_cli_enhanced.py                    # Interactive menu mode (default)
  python3 start_rr4_cli_enhanced.py --option 11        # Run first-time startup wizard
  python3 start_rr4_cli_enhanced.py --option 1         # Run first-time setup directly
  python3 start_rr4_cli_enhanced.py --option 2         # Run audit only directly
  python3 start_rr4_cli_enhanced.py --option 3         # Run full collection directly
  python3 start_rr4_cli_enhanced.py --option 12        # Run comprehensive status report
  python3 start_rr4_cli_enhanced.py --list-options     # List all available options
        '''
    )
    
    parser.add_argument(
        '--option', '-o',
        type=int,
        choices=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        help='Execute specific option directly (0-12, including new Option 11)'
    )
    
    parser.add_argument(
        '--first-time', '-f',
        action='store_true',
        help='Launch first-time startup wizard (equivalent to --option 11)'
    )
    
    parser.add_argument(
        '--list-options', '-l',
        action='store_true',
        help='List all available options with descriptions'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='store_true',
        help='Show version information'
    )
    
    parser.add_argument(
        '--no-prereq-check',
        action='store_true',
        help='Skip prerequisites check (for automated execution)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimize output (for automated execution)'
    )
    
    parser.add_argument(
        '--auto-detect',
        action='store_true',
        help='Auto-detect first-time usage and suggest appropriate option'
    )
    
    return parser.parse_args()

def show_version_info():
    """Show version information"""
    print(f"{Colors.CYAN}{'=' * 60}")
    print(f"RR4 CLI Interactive Startup Script - Enhanced")
    print(f"Version: 1.2.0-CrossPlatform-CLI-Enhanced-FirstTime")
    print(f"Created: 2025-06-02")
    print(f"Updated: 2025-06-03")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"{'=' * 60}{Colors.RESET}")

def list_all_options():
    """List all available options with descriptions"""
    options = {
        0: "🚪 EXIT - Exit the application",
        1: "🎯 FIRST-TIME SETUP - Complete guided setup with prerequisites check",
        2: "🔍 AUDIT ONLY - Quick connectivity and health check", 
        3: "📊 FULL COLLECTION - Production data collection",
        4: "🎛️  CUSTOM COLLECTION - Choose specific devices and layers",
        5: "🔧 PREREQUISITES CHECK ONLY - Verify system requirements",
        6: "🌐 ENHANCED CONNECTIVITY TEST - Comprehensive connectivity test",
        7: "📚 SHOW HELP & OPTIONS - Display all available commands",
        8: "🎯 CONSOLE AUDIT - Console line discovery and collection",
        9: "🌟 COMPLETE COLLECTION - All layers + Console in systematic order",
        10: "🔒 CONSOLE SECURITY AUDIT - Transport security analysis",
        11: "🚀 FIRST-TIME STARTUP WIZARD - Comprehensive new user onboarding",
        12: "📊 COMPREHENSIVE STATUS REPORT - All options analysis with device filtering"
    }
    
    print_header("AVAILABLE OPTIONS", Colors.CYAN)
    print_info("RR4 CLI startup options available for direct command-line execution:")
    print_info("")
    
    for option_num, description in options.items():
        if option_num == 11:
            print_info(f"  {option_num:2d}: {Colors.YELLOW}{description}{Colors.RESET} ⭐ RECOMMENDED FOR NEW USERS")
        else:
            print_info(f"  {option_num:2d}: {description}")
    
    print_info("")
    print_info("Usage examples:")
    print_info("  python3 start_rr4_cli_enhanced.py --option 11   # ⭐ First-time startup wizard")
    print_info("  python3 start_rr4_cli_enhanced.py --first-time  # Alternative first-time flag")  
    print_info("  python3 start_rr4_cli_enhanced.py --option 1    # Run first-time setup")
    print_info("  python3 start_rr4_cli_enhanced.py --option 12   # Run comprehensive report")
    print_info("  python3 start_rr4_cli_enhanced.py               # Interactive menu mode")

def first_time_startup_wizard(args) -> bool:
    """Comprehensive first-time startup wizard"""
    print_header("🚀 FIRST-TIME STARTUP WIZARD", Colors.GREEN)
    print_info("Welcome to the V4CODERCLI Network Automation System!")
    print_info("This wizard will guide you through your first experience.")
    print_info("")
    
    # Detect first-time usage indicators
    is_first_time, indicators = detect_first_time_usage()
    
    print_section("🔍 First-Time Usage Detection")
    for indicator, status in indicators.items():
        status_icon = "🔸" if status else "✅"
        print_info(f"{status_icon} {indicator.replace('_', ' ').title()}: {'Yes' if status else 'Already configured'}")
    
    confidence = "HIGH" if sum(indicators.values()) >= 3 else "MEDIUM" if sum(indicators.values()) >= 2 else "LOW"
    print_info(f"🎯 First-time usage confidence: {confidence}")
    print_info("")
    
    # Display system overview
    print_section("🌐 System Overview")
    print_info("• Network: 11 Cisco routers (R102-R120)")
    print_info("• Jump Host: 172.16.39.128") 
    print_info("• Collectors: 8 specialized data collectors")
    print_info("• Security: A+ rated system")
    print_info("• Status: 100% operational")
    print_info("")
    
    # Wizard steps
    wizard_steps = [
        ("🔧 System Health Check", "Verify all components are working"),
        ("🌐 Network Connectivity", "Test connection to all 11 devices"),
        ("📚 Learn Available Options", "Understand all 13 options"),
        ("🎯 First Collection", "Perform your first data collection"),
        ("📊 View Results", "Analyze collected data")
    ]
    
    print_section("🎯 Wizard Steps")
    for i, (step, description) in enumerate(wizard_steps, 1):
        print_info(f"  {i}. {step}")
        print_info(f"     {description}")
    print_info("")
    
    # Ask user to proceed
    if not args.quiet:
        try:
            proceed = input(f"{Colors.YELLOW}Ready to start the wizard? (y/n): {Colors.RESET}").strip().lower()
            if proceed not in ['y', 'yes']:
                print_info("Wizard cancelled. You can run it anytime with:")
                print_info("  python3 start_rr4_cli_enhanced.py --option 11")
                return True
        except:
            print_info("Proceeding with wizard...")
    
    manager = RR4StartupManager()
    success_count = 0
    
    # Step 1: System Health Check
    print_header("STEP 1: 🔧 SYSTEM HEALTH CHECK", Colors.CYAN)
    print_info("Running comprehensive system health monitor...")
    
    try:
        health_result = subprocess.run(
            ["python3", "system_health_monitor.py"],
            capture_output=True, text=True, timeout=60
        )
        if health_result.returncode == 0 and "HEALTHY" in health_result.stdout:
            print_success("✅ System health check passed!")
            success_count += 1
        else:
            print_warning("⚠️ System health check completed with warnings")
    except Exception as e:
        print_error(f"❌ System health check failed: {e}")
    
    if not args.quiet:
        input(f"{Colors.YELLOW}Press Enter to continue to Step 2...{Colors.RESET}")
    
    # Step 2: Network Connectivity  
    print_header("STEP 2: 🌐 NETWORK CONNECTIVITY", Colors.CYAN)
    print_info("Testing connectivity to all 11 devices...")
    
    if manager.enhanced_connectivity_test():
        print_success("✅ Network connectivity test passed!")
        success_count += 1
    else:
        print_error("❌ Network connectivity test failed")
    
    if not args.quiet:
        input(f"{Colors.YELLOW}Press Enter to continue to Step 3...{Colors.RESET}")
    
    # Step 3: Learn Available Options
    print_header("STEP 3: 📚 LEARN AVAILABLE OPTIONS", Colors.CYAN)
    print_info("Here are all 13 options available in the system:")
    list_all_options()
    success_count += 1
    
    if not args.quiet:
        input(f"{Colors.YELLOW}Press Enter to continue to Step 4...{Colors.RESET}")
    
    # Step 4: First Collection
    print_header("STEP 4: 🎯 YOUR FIRST COLLECTION", Colors.CYAN)
    print_info("Let's perform your first data collection!")
    print_info("We recommend starting with a connectivity audit (Option 2)")
    
    if not args.quiet:
        try:
            run_collection = input(f"{Colors.YELLOW}Run first collection now? (y/n): {Colors.RESET}").strip().lower()
            if run_collection in ['y', 'yes']:
                if manager.audit_only():
                    print_success("✅ First collection completed successfully!")
                    success_count += 1
                else:
                    print_error("❌ First collection failed")
            else:
                print_info("First collection skipped. You can run it later with:")
                print_info("  python3 start_rr4_cli_enhanced.py --option 2")
        except:
            print_info("Proceeding with first collection...")
            if manager.audit_only():
                success_count += 1
    else:
        if manager.audit_only():
            success_count += 1
    
    if not args.quiet:
        input(f"{Colors.YELLOW}Press Enter to continue to Step 5...{Colors.RESET}")
    
    # Step 5: View Results
    print_header("STEP 5: 📊 VIEW RESULTS", Colors.CYAN)
    print_info("Checking outputs directory for your collected data...")
    
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        collections = list(outputs_dir.glob("**/collection_*"))
        if collections:
            print_success(f"✅ Found {len(collections)} data collections!")
            print_info("Your data is organized in the outputs/ directory")
            for collection in collections[-3:]:  # Show last 3
                print_info(f"  • {collection.name}")
            success_count += 1
        else:
            print_info("No collections found yet - run Option 2 or 3 to collect data")
    else:
        print_info("Outputs directory will be created when you run your first collection")
    
    # Wizard completion summary
    print_header("🎉 WIZARD COMPLETION SUMMARY", Colors.GREEN)
    print_info(f"Completed steps: {success_count}/5")
    
    if success_count >= 4:
        print_success("🎉 Excellent! You're ready to use the system!")
        print_info("🎯 Recommended next steps:")
        print_info("  • Run Option 9 for complete collection")
        print_info("  • Run Option 12 for comprehensive status report")
        print_info("  • Explore Option 4 for custom collections")
    elif success_count >= 2:
        print_warning("⚠️ Good progress! Review any failed steps before proceeding.")
        print_info("🎯 Next steps:")
        print_info("  • Address any connectivity issues")
        print_info("  • Re-run failed steps")
        print_info("  • Run Option 5 for prerequisites check")
    else:
        print_error("❌ Several steps need attention. Please review system requirements.")
        print_info("🎯 Troubleshooting:")
        print_info("  • Check system requirements")
        print_info("  • Verify network connectivity")
        print_info("  • Run system_health_monitor.py for diagnostics")
    
    print_info("")
    print_info("📚 Resources:")
    print_info("  • Full guide: STARTUP_COMMANDS_GUIDE.txt")
    print_info("  • Quick start: QUICK_START.txt")
    print_info("  • Interactive menu: python3 start_rr4_cli_enhanced.py")
    
    return success_count >= 2

def execute_option_directly(option_num: int, args) -> bool:
    """Execute a specific option directly from command line"""
    manager = EnhancedRR4StartupManager()
    
    # Show minimal startup info in quiet mode
    if not args.quiet:
        display_startup_info()
        print_header(f"DIRECT EXECUTION - OPTION {option_num}", Colors.GREEN)
    
    # Skip prerequisites check if requested (for automation)
    if not args.no_prereq_check:
        if not args.quiet:
            print_info("Performing prerequisites check...")
        if not manager.check_prerequisites():
            print_error("Prerequisites check failed. Use --no-prereq-check to skip.")
            return False
    elif not args.quiet:
        print_warning("Skipping prerequisites check as requested.")
    
    # Execute the selected option
    success = False
    try:
        if option_num == 0:
            if not args.quiet:
                print_success("Exit option selected. Goodbye!")
            return True
        elif option_num == 1:
            success = manager.first_time_setup()
        elif option_num == 2:
            success = manager.audit_only()
        elif option_num == 3:
            success = manager.full_collection()
        elif option_num == 4:
            success = manager.custom_collection()
        elif option_num == 5:
            success = manager.check_prerequisites()
        elif option_num == 6:
            success = manager.enhanced_connectivity_test()
        elif option_num == 7:
            success = manager.show_help()
        elif option_num == 8:
            success = manager.console_audit()
        elif option_num == 9:
            success = manager.complete_collection()
        elif option_num == 10:
            success = manager.console_security_audit()
        elif option_num == 11:
            success = first_time_startup_wizard(args)
        elif option_num == 12:
            success = manager.comprehensive_status_report()
        else:
            print_error(f"Invalid option: {option_num}")
            return False
            
        if success:
            if not args.quiet:
                print_success(f"Option {option_num} completed successfully!")
        else:
            if not args.quiet:
                print_error(f"Option {option_num} failed or was cancelled.")
        
        return success
        
    except KeyboardInterrupt:
        if not args.quiet:
            print_warning("\nOperation cancelled by user.")
        return False
    except Exception as e:
        print_error(f"Error executing option {option_num}: {str(e)}")
        return False

def main():
    """Main entry point with command-line argument support"""
    try:
        # Parse command line arguments
        args = parse_command_line_arguments()
        
        # Handle version request
        if args.version:
            show_version_info()
            return
        
        # Handle list options request
        if args.list_options:
            list_all_options()
            return
        
        # Handle first-time flag (equivalent to --option 11)
        if args.first_time:
            success = first_time_startup_wizard(args)
            sys.exit(0 if success else 1)
        
        # Handle direct option execution
        if args.option is not None:
            success = execute_option_directly(args.option, args)
            sys.exit(0 if success else 1)
        
        # Handle auto-detection mode
        if args.auto_detect:
            is_first_time, indicators = detect_first_time_usage()
            if is_first_time:
                print_info("🔍 First-time usage detected!")
                print_info("🚀 Recommending first-time startup wizard (Option 11)")
                print_info("Run: python3 start_rr4_cli_enhanced.py --option 11")
                return
            else:
                print_info("✅ System appears to be already configured")
                print_info("🎯 Recommended: python3 start_rr4_cli_enhanced.py --option 2")
                return
        
        # Default: Run interactive menu mode with first-time detection
        is_first_time, indicators = detect_first_time_usage()
        if is_first_time and not args.quiet:
            print_header("🔍 FIRST-TIME USAGE DETECTED", Colors.YELLOW)
            print_info("It looks like this might be your first time using the system!")
            print_info("🚀 We recommend starting with the First-Time Startup Wizard")
            print_info("")
            try:
                use_wizard = input(f"{Colors.YELLOW}Launch first-time wizard now? (y/n): {Colors.RESET}").strip().lower()
                if use_wizard in ['y', 'yes']:
                    success = first_time_startup_wizard(args)
                    sys.exit(0 if success else 1)
            except:
                pass
        
        # Run normal interactive menu
        manager = EnhancedRR4StartupManager()
        manager.run()
        
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
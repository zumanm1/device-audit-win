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
- Show help: python3 start_rr4_cli_enhanced.py --help
- Interactive mode: python3 start_rr4_cli_enhanced.py (default)

This script provides:
- Guided first-time setup
- Prerequisites checking
- Step-by-step testing
- Menu-driven interface for different use cases
- Direct command-line access to all options (0-12)
- Error handling and recovery
- Best practice recommendations

Author: AI Assistant
Version: 1.1.0-CrossPlatform-CLI-Enhanced
Created: 2025-06-02
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
from start_rr4_cli import RR4StartupManager, Colors, print_header, print_info, print_success, print_error, print_warning, display_startup_info

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
  12  📊 COMPREHENSIVE STATUS REPORT  - All options analysis with device filtering

EXAMPLES:
  python3 start_rr4_cli_enhanced.py                    # Interactive menu mode (default)
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
        choices=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12],
        help='Execute specific option directly (0-12, excluding 11)'
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
    
    return parser.parse_args()

def show_version_info():
    """Show version information"""
    print(f"{Colors.CYAN}{'=' * 60}")
    print(f"RR4 CLI Interactive Startup Script - Enhanced")
    print(f"Version: 1.1.0-CrossPlatform-CLI-Enhanced")
    print(f"Created: 2025-06-02")
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
        12: "📊 COMPREHENSIVE STATUS REPORT - All options analysis with device filtering"
    }
    
    print_header("AVAILABLE OPTIONS", Colors.CYAN)
    print_info("RR4 CLI startup options available for direct command-line execution:")
    print_info("")
    
    for option_num, description in options.items():
        print_info(f"  {option_num:2d}: {description}")
    
    print_info("")
    print_info("Usage examples:")
    print_info("  python3 start_rr4_cli_enhanced.py --option 1    # Run first-time setup")
    print_info("  python3 start_rr4_cli_enhanced.py --option 12   # Run comprehensive report")
    print_info("  python3 start_rr4_cli_enhanced.py               # Interactive menu mode")

def execute_option_directly(option_num: int, args) -> bool:
    """Execute a specific option directly from command line"""
    manager = RR4StartupManager()
    
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
        
        # Handle direct option execution
        if args.option is not None:
            success = execute_option_directly(args.option, args)
            sys.exit(0 if success else 1)
        
        # Default: Run interactive menu mode
        manager = RR4StartupManager()
        manager.run()
        
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 